#!/usr/bin/env python3
"""
Enhanced Email Ingestor - Full version with AI capabilities
"""

import os
import logging
import imaplib
import email
from email.header import decode_header
import json
import tempfile
import re
import openai
from datetime import datetime
from dotenv import load_dotenv
from db_utils import get_db_conn
from utils.timezone_utils import get_hk_now, get_hk_now_iso
from ocr_processor import process_pdf
import threading
import time
from decimal import Decimal
from cloudinary_utils import upload_filepath_to_cloudinary
from invoice_utils import find_invoice_info, find_ctn_info, generate_pdf_from_text
from config import CloudinaryConfig
from utils.unified_response_handler import get_response_handler
from utils.confidence_scorer import confidence_scorer

# Load environment variables
load_dotenv('.env.local')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PDF_SAVE_DIR = os.path.join(os.path.dirname(__file__), 'pdf_attachments')

# OpenAI configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

# Global processing lock to prevent race conditions
email_processing_lock = threading.Lock()
email_processing_status = {
    'is_processing': False,
    'started_by': None,
    'started_at': None,
    'processed_count': 0
}

def acquire_db_processing_lock(user_id, timeout_seconds=30):
    """Acquire database-based processing lock"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Clean up stale locks (older than 10 minutes)
        cursor.execute("""
            DELETE FROM email_processing_locks 
            WHERE created_at < NOW() - INTERVAL '10 minutes'
        """)
        
        # Try to insert a new lock (will fail if another lock exists due to our constraint)
        cursor.execute("""
            INSERT INTO email_processing_locks (user_id, created_at, expires_at)
            VALUES (%s, NOW(), NOW() + INTERVAL '%s seconds')
            RETURNING id
        """, (user_id, timeout_seconds))
        
        result = cursor.fetchone()
        if result:
            conn.commit()
            logger.info(f"🔒 Database lock acquired by: {user_id}")
            return True
        else:
            return False
            
    except Exception as e:
        # Check if the error is due to existing lock (our constraint)
        if "already exists" in str(e):
            # Check if there's an existing lock
            cursor.execute("""
                SELECT user_id, created_at FROM email_processing_locks 
                WHERE expires_at > NOW()
                ORDER BY created_at DESC LIMIT 1
            """)
            existing = cursor.fetchone()
            if existing:
                logger.warning(f"⏰ Database lock already held by: {existing[0]} since {existing[1]}")
            return False
        else:
            logger.error(f"❌ Failed to acquire database lock: {e}")
            return False
    finally:
        cursor.close()
        conn.close()

def release_db_processing_lock(user_id):
    """Release database-based processing lock"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            DELETE FROM email_processing_locks 
            WHERE user_id = %s
        """, (user_id,))
        conn.commit()
        logger.info(f"🔓 Database lock released by: {user_id}")
    except Exception as e:
        logger.error(f"❌ Failed to release database lock: {e}")
    finally:
        cursor.close()
        conn.close()

def get_db_processing_status():
    """Get current database processing status"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT user_id, created_at, expires_at 
            FROM email_processing_locks 
            WHERE expires_at > NOW()
            ORDER BY created_at DESC LIMIT 1
        """)
        
        result = cursor.fetchone()
        if result:
            user_id, created_at, expires_at = result
            return {
                'is_processing': True,
                'started_by': user_id,
                'started_at': created_at.isoformat() if created_at else None,
                'expires_at': expires_at.isoformat() if expires_at else None
            }
        else:
            return {
                'is_processing': False,
                'started_by': None,
                'started_at': None,
                'expires_at': None
            }
    except Exception as e:
        logger.error(f"❌ Failed to get database processing status: {e}")
        return {
            'is_processing': False,
            'started_by': None,
            'started_at': None,
            'expires_at': None,
            'error': str(e)
        }
    finally:
        cursor.close()
        conn.close()

def connect_imap():
    """Connect to Gmail IMAP"""
    try:
        # Get email credentials from environment
        email_host = os.getenv('EMAIL_HOST')
        email_user = os.getenv('EMAIL_USERNAME')
        email_pass = os.getenv('EMAIL_PASSWORD')
        
        if not email_host or not email_user or not email_pass:
            logger.error("❌ Email credentials not found in environment variables")
            logger.error(f"EMAIL_HOST: {email_host}")
            logger.error(f"EMAIL_USERNAME: {email_user}")
            logger.error(f"EMAIL_PASSWORD: {'***' if email_pass else 'NOT SET'}")
            return None
        
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(email_host)
        mail.login(email_user, email_pass)
        logger.info("✅ Connected to IMAP server")
        return mail
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to IMAP: {e}")
        return None

def openai_call_with_fallback(messages, temperature=0, max_retries=2):
    """
    Make OpenAI API call with production fallback strategy
    Email: GPT-3.5-turbo → GPT-4o (fast, cheap for text processing)
    """
    logger.info(f"[OpenAI Call] Starting OpenAI API call with {len(messages)} messages")
    logger.info(f"[OpenAI Call] Temperature: {temperature}")
    
    if not OPENAI_API_KEY:
        logger.error("❌ OpenAI API key not configured")
        return None
    
    models = ['gpt-3.5-turbo', 'gpt-4o-mini']
    
    for i, model in enumerate(models):
        try:
            logger.info(f"[OpenAI Email] Attempting call with {model}")
            response = openai.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature
            )
            content = response.choices[0].message.content
            logger.info(f"[OpenAI Email] Successfully used {model} for email processing")
            return content
        except Exception as e:
            error_msg = str(e).lower()
            if "quota" in error_msg or "rate limit" in error_msg or "billing" in error_msg:
                if i < len(models) - 1:
                    logger.warning(f"[OpenAI Email] {model} quota/rate limit exceeded, falling back to {models[i+1]}")
                    continue
                else:
                    logger.error(f"[OpenAI Email] All models exhausted: {e}")
                    return None
            else:
                logger.error(f"[OpenAI Email] Error with {model}: {e}")
                return None
    
    return None

def handle_email_via_openai(subject, body, attachments, from_addr):
    """AI-powered email classification and reply generation"""
    logger.info(f"[AI Processing] Starting AI processing for email from: {from_addr}")
    logger.info(f"[AI Processing] Subject: {subject}")
    logger.info(f"[AI Processing] Body length: {len(body)} characters")
    logger.info(f"[AI Processing] Attachments: {len(attachments) if attachments else 0}")
    
    # Initialize variables
    paid_amount = None
    custom_reply = "Hello,\n\nThank you for your email. Please provide more details or contact us for assistance."
    confidence_score = 0.0
    auto_send = False
    classification = "general"

    # --- Pre-Processing: Extract payment and BLs from PDFs ---
    def extract_payment_amount(text):
        if not text:
            return None
        patterns = [
            r'\$\s?([0-9]+(?:\.[0-9]{1,2})?)',
            r'USD\s*([0-9]+(?:\.[0-9]{1,2})?)',
            r'Amount[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)',
            r'Paid[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)',
            r'Payment[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)',
            r'Total[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)',
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except Exception:
                    continue
        return None

    def extract_all_payment_amounts(text):
        """Extract all payment amounts from text and return total"""
        if not text:
            return None
        patterns = [
            r'\$\s?([0-9]+(?:\.[0-9]{1,2})?)',
            r'USD\s*([0-9]+(?:\.[0-9]{1,2})?)',
            r'Amount[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)',
            r'Paid[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)',
            r'Payment[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)',
            r'Total[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)',
        ]
        amounts = set()  # Use set to avoid duplicates
        for pat in patterns:
            matches = re.findall(pat, text, re.IGNORECASE)
            for match in matches:
                try:
                    amount = float(match)
                    # Filter out amounts that are likely BL numbers (too small or too large)
                    if amount >= 10 and amount <= 10000:  # Reasonable payment range
                        amounts.add(amount)  # Use add() instead of append() to avoid duplicates
                        logger.info(f"\033[92m[Payment Extraction] Found amount: {amount} from pattern match: {match}\033[0m")
                    else:
                        logger.info(f"\033[93m[Payment Extraction] Skipping amount: {amount} (likely BL number)\033[0m")
                except Exception:
                    continue
        total = sum(amounts) if amounts else None
        logger.info(f"\033[92m[Payment Extraction] Total extracted amount: {total}\033[0m")
        return total

    def extract_bl_specific_payments(text, bl_numbers):
        """Extract payment amounts specific to each BL number"""
        if not text or not bl_numbers:
            return {}
        
        bl_payments = {}
        
        # Pattern to match "USD X for BL Y" or "BL Y USD X" or similar
        patterns = [
            r'USD\s*([0-9]+(?:\.[0-9]{1,2})?)\s+(?:for\s+)?(?:BL\s*)?([A-Z0-9\-]+)',
            r'(?:BL\s*)?([A-Z0-9\-]+)\s+USD\s*([0-9]+(?:\.[0-9]{1,2})?)',
            r'\$\s*([0-9]+(?:\.[0-9]{1,2})?)\s+(?:for\s+)?(?:BL\s*)?([A-Z0-9\-]+)',
            r'(?:BL\s*)?([A-Z0-9\-]+)\s+\$\s*([0-9]+(?:\.[0-9]{1,2})?)',
        ]
        
        # First try to find BL-specific payments
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for amount_str, bl_match in matches:
                try:
                    amount = float(amount_str)
                    # Find the closest matching BL number
                    for bl in bl_numbers:
                        if bl.upper() in bl_match.upper() or bl_match.upper() in bl.upper():
                            bl_payments[bl] = amount
                            break
                except ValueError:
                    continue
        
        return bl_payments

    # Process PDF attachments for payment and BL information
    bls_from_pdfs = set()
    fallback_paid_amount = None
    
    if attachments:
        for att_path in attachments:
            if att_path.lower().endswith('.pdf'):
                try:
                    logger.info(f"[PDF Processing] Processing attachment: {att_path}")
                    pdf_fields = process_pdf(att_path)
                    if pdf_fields and isinstance(pdf_fields, dict):
                        # Extract payment amount
                        paid_amt_struct = pdf_fields.get('paid_amount')
                        if paid_amt_struct is not None:
                            try:
                                fallback_paid_amount = float(re.sub(r'[^0-9.]+', '', str(paid_amt_struct)))
                                logger.info(f"[PDF Processing] Parsed paid_amount from PDF: {fallback_paid_amount}")
                            except Exception as ex:
                                logger.error(f"[PDF Processing] Error parsing paid_amount from PDF: {ex}")
                        
                        # Fallback to raw_text extraction
                        if fallback_paid_amount is None:
                            raw_text = pdf_fields.get('raw_text')
                            if raw_text:
                                amt = extract_payment_amount(raw_text)
                                if amt is not None:
                                    fallback_paid_amount = amt
                        
                        # Extract BLs
                        bl_val = pdf_fields.get('bl_number')
                        if bl_val and isinstance(bl_val, str):
                            bls = [b.strip() for b in re.split(r'[\s,;/]+', bl_val) if b.strip()]
                            bls_from_pdfs.update(bls)
                            logger.info(f"[PDF Processing] BLs from structured field: {bls}")
                        
                        # Extract from raw text
                        raw_text = pdf_fields.get('raw_text')
                        if raw_text:
                            bl_pattern = re.compile(r'(?:提单号[:：]?\s*)?(BL-\d{4,}|\d{3,}-\d{3,}|\d{6,}|[A-Z]{2,4}\d{2,})', re.IGNORECASE)
                            raw_bls = bl_pattern.findall(raw_text)
                            bls_from_pdfs.update(raw_bls)
                            logger.info(f"[PDF Processing] BLs from raw text: {raw_bls}")
                            
                except Exception as e:
                    logger.error(f"[PDF Processing] Failed for {att_path}: {e}")
    
    # Fallback to email body extraction
    if fallback_paid_amount is None:
        fallback_paid_amount = extract_all_payment_amounts(body)
    paid_amount = fallback_paid_amount

    # --- Translation for Chinese emails ---
    def is_chinese(text):
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        return chinese_chars > 0 and chinese_chars / max(1, len(text)) > 0.2

    def openai_translate(text, source_lang, target_lang):
        try:
            translation_prompt = f"Translate the following {source_lang} text to {target_lang}. Only return the translated text, no explanation.\n\n{text}"
            messages = [
                {"role": "system", "content": "You are a professional translator."},
                {"role": "user", "content": translation_prompt},
            ]
            translated_text = openai_call_with_fallback(messages, temperature=0)
            if translated_text:
                logger.info(f"[Translation] Original: {text[:50]}... -> Translated: {translated_text[:50]}...")
                return translated_text.strip()
            return text
        except Exception as e:
            logger.error(f"[OpenAI Translate] Failed: {e}")
            return text

    incoming_is_chinese = is_chinese(body)
    translation_used = False
    translated_body = body
    if incoming_is_chinese:
        translated_body = openai_translate(body, 'Chinese', 'English')
        translation_used = True
        logger.info(f"[OpenAI Email] Translated body: {translated_body[:100]}...")

    # --- Pre-Parse Request Types with more flexible patterns ---
    patterns = [
        ('payment_receipt', r'\b(payment\s+receipt|paid\s+receipt|payment\s+confirmation|付款确认|收据|payment|paid|amount[:：]?\s*\$?[0-9]+)\b'),
        ('payment_status', r'\b(payment\s+status|due|outstanding|balance|payment\s+for|amount[:：]?\s*\$?[0-9]+)\b'),
        ('invoice_request', r'\b(invoice|bill|billing|发票|账单)\b'),
        ('ctn_request', r'\b(ctn|container)\s+number(s)?\b|CTN号码|集装箱号|container'),
        ('fee_inquiry', r'\b(fee|fees|cost|charge|charges|total\s+fee|total\s+cost|费用|收费)\b'),
        ('business_hours', r'\b(business\s+hours|operating\s+hours|office\s+hours|working\s+hours|营业时间|工作时间)\b'),
        ('payment_methods', r'\b(payment\s+method|payment\s+option|how\s+to\s+pay|settle|支付方式|付款方式)\b'),
        ('ctn_process', r'\b(ctn\s+process|ctn\s+time|ctn\s+duration|集装箱处理时间)\b'),
    ]
    
    request_types = []
    text_to_parse = [translated_body] if translation_used else [body]
    if incoming_is_chinese:
        text_to_parse.append(body)  # Parse original Chinese body for Chinese terms
    
    for text in text_to_parse:
        for req_type, pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE) and req_type not in request_types:
                request_types.append(req_type)
    
    # Prioritize payment_receipt and payment_status over fee_inquiry
    if 'payment_receipt' in request_types or 'payment_status' in request_types:
        request_types = [rt for rt in request_types if rt not in ['fee_inquiry']] + [rt for rt in request_types if rt == 'fee_inquiry']
    
    if not request_types:
        request_types.append('general_enquiry')
    
    logger.info(f"\033[92m[Pre-Parsing] Request types: {request_types} | Email body: {body}\033[0m")

    # --- Extract and Merge BLs from all sources ---
    # Refined BL pattern that excludes common bank reference formats
    bl_pattern = re.compile(r'(?:提单号[:：]?\s*)?(BL-\d{4,}|\d{3,}-\d{3,}|\d{6,}|[A-Z]{2,4}\d{2,})', re.IGNORECASE)
    bls_from_body = set()
    
    for text in text_to_parse:
        found_bls = bl_pattern.findall(text)
        logger.debug(f"[DEBUG] BLs found in body text '{text[:50]}...': {found_bls}")
        bls_from_body.update(found_bls)
    
    # Merge BLs from body, PDF, and OpenAI reply
    merged_bls = bls_from_body | bls_from_pdfs
    logger.info(f"\033[92m[BL Processing] BLs from body: {bls_from_body}, BLs from PDFs: {bls_from_pdfs}, Merged: {merged_bls}\033[0m")
    logger.info(f"\033[92m[BL Processing] Body text for BL extraction: '{body[:200]}...' if body else 'Empty'\033[0m")
    
    # Filter out common bank reference patterns
    bank_ref_patterns = ['TEST', 'REF', 'BANK', 'PAY', 'TRANS', 'TXN']
    filtered_bls = set()
    logger.info(f"\033[92m[BL Processing] Filtering BLs: {merged_bls}\033[0m")
    logger.info(f"\033[92m[BL Processing] Bank reference patterns: {bank_ref_patterns}\033[0m")
    for bl in merged_bls:
        # Skip if BL starts with common bank reference prefixes
        bl_upper = bl.upper()
        excluded = False
        for prefix in bank_ref_patterns:
            if bl_upper.startswith(prefix):
                logger.info(f"\033[93m[BL Processing] Excluding bank reference: {bl} (matches prefix: {prefix})\033[0m")
                excluded = True
                break
        if excluded:
            continue
        filtered_bls.add(bl)
        logger.info(f"\033[92m[BL Processing] Keeping BL: {bl}\033[0m")
    
    bl_numbers = list(filtered_bls)
    logger.info(f"\033[92m[BL Processing] Final BL numbers: {bl_numbers}\033[0m")
    logger.info(f"\033[92m[Pre-Parsing] Extracted BLs (filtered): {bl_numbers}\033[0m")

    # --- Override classification if payment info found ---
    if 'payment_receipt' not in request_types:
        if paid_amount and bl_numbers:
            logger.warning("[Heuristic Override] Found paid amount and BLs — forcing payment_receipt.")
            request_types.insert(0, 'payment_receipt')
        elif paid_amount and not bl_numbers:
            # Stronger fallback: use BLs from PDF OCR if available
            if bls_from_pdfs:
                bl_numbers = list(bls_from_pdfs)
                logger.warning("[Heuristic Override] Found payment amount but no BLs — using BLs from PDF OCR and forcing payment_receipt.")
            else:
                logger.warning("[Heuristic Override] Found payment amount but no BLs — still forcing payment_receipt.")
            request_types.insert(0, 'payment_receipt')
        elif not body.strip() and attachments:
            logger.warning("[Heuristic Override] No body text but has attachment — treating as payment_receipt.")
            request_types.insert(0, 'payment_receipt')
        elif attachments and bls_from_pdfs:
            # If we have attachments with BLs but no payment amount, still treat as payment_receipt
            logger.warning("[Heuristic Override] Found attachments with BLs — treating as payment_receipt.")
            request_types.insert(0, 'payment_receipt')

    # --- Query database for BL information ---

    valid_bls = {}
    invalid_bls = []
    if bl_numbers:
        ctn_infos = find_ctn_info(bl_numbers) or []
        invoice_infos = find_invoice_info(bl_numbers) or []
        
        for bl in bl_numbers:
            ctn_info = next((info for info in ctn_infos if info.get('bl_number') == bl), {})
            invoice_info = next((info for info in invoice_infos if info.get('bl_number') == bl), {})
            
            if ctn_info or invoice_info:
                valid_bls[bl] = {
                    'ctn': ctn_info.get('ctn_number'),
                    'invoice_link': invoice_info.get('invoice_filename'),
                    'ctn_fee': float(invoice_info.get('ctn_fee', 0)) if invoice_info.get('ctn_fee') else 0.0,
                    'service_fee': float(invoice_info.get('service_fee', 0)) if invoice_info.get('service_fee') else 0.0,
                    'paid_amount': float(invoice_info.get('paid_amount', 0)) if invoice_info.get('paid_amount') else 0.0,
                    'status': invoice_info.get('status', 'Unknown')
                }
            else:
                invalid_bls.append(bl)
    
    logger.info(f"\033[92m[DB Query] Valid BLs: {valid_bls}, Invalid BLs: {invalid_bls}\033[0m")

    # --- Validate Paid Amount ---
    if paid_amount is not None and 'payment_receipt' in request_types and not valid_bls:
        logger.warning(f"[Validation] Paid amount {paid_amount} ignored: No valid BLs found for payment_receipt")
        paid_amount = None

    # --- Detect Missing Attachments ---
    missing_attachment_flag = False
    if not attachments:
        attachment_phrases = [
            r"see (the )?attached", r"find (the )?attached", r"attached( is| are|:)?",
            r"attachment(s)?( is| are|:)?", r"enclosed (file|document|pdf|invoice|receipt)?",
            r"as per (the )?attachment", r"please refer to (the )?attachment",
            r"please see (the )?attachment", r"please find (the )?attachment",
            r"I've attached", r"I have attached", r"see attached", r"see the attached",
            r"see the attachment", r"see attachments", r"see the attachments",
            r"find attached", r"find the attached", r"find the attachment",
            r"find attachments", r"find the attachments", r"attachment is",
            r"attachment are", r"attachment:",
            r"已?附上|附件|请查收附件|请见附件|请参见附件|请参考附件|请见附档|请查收附档|请见附加文件|请查收附加文件|附件见下|请查附件|请见下方附件|请见随信附件"
        ]
        pattern = re.compile(r"|".join(attachment_phrases), re.IGNORECASE)
        if pattern.search(body):
            missing_attachment_flag = True

    # --- Load Canned Responses ---
    try:
        with open('canned_responses.json', 'r') as f:
            canned_responses = json.load(f)
        canned_responses_text = "\n\n".join([f"Q: {r['title']}\nA: {r['body']}" for r in canned_responses])
    except Exception as e:
        logger.error(f"[OpenAI Email] Could not load canned_responses.json: {e}")
        canned_responses_text = "No canned responses available."

    # Business constants
    BUSINESS_HOURS = "Monday to Friday: 9:00 AM - 6:00 PM (Hong Kong Time)"
    PAYMENT_METHODS = ["Bank Transfer", "PayPal", "Credit Card"]
    CTN_PROCESSING_TIME = "3-5 business days"

    # --- OpenAI Prompt ---
    full_text = f"Subject: {subject}\n\n{translated_body}"
    attachment_info = f"\n\nThe customer has attached {len(attachments)} file(s) to this email." if attachments else ""
    
    # Build prompt sections only for detected request types
    prompt_sections = []
    if 'invoice_request' in request_types and valid_bls:
        prompt_sections.append(f"Valid BLs: {json.dumps(valid_bls)}")
    if 'ctn_request' in request_types and valid_bls:
        prompt_sections.append(f"Valid BLs: {json.dumps(valid_bls)}")
    if 'fee_inquiry' in request_types and valid_bls:
        prompt_sections.append(f"Valid BLs: {json.dumps(valid_bls)}")
    if 'payment_status' in request_types or 'payment_receipt' in request_types:
        prompt_sections.append(f"Paid amount: {paid_amount if paid_amount is not None else 'None'}")
        if valid_bls:
            prompt_sections.append(f"Valid BLs: {json.dumps(valid_bls)}")
    if 'business_hours' in request_types:
        prompt_sections.append(f"Business hours: {BUSINESS_HOURS}")
    if 'payment_methods' in request_types:
        prompt_sections.append(f"Payment methods: {', '.join(PAYMENT_METHODS)}")
    if 'ctn_process' in request_types:
        prompt_sections.append(f"CTN processing time: {CTN_PROCESSING_TIME}")
    if invalid_bls:
        prompt_sections.append(f"Invalid BLs: {json.dumps(invalid_bls)}")
    
    prompt = f"""
You are a logistics assistant for IQS Trade. Draft a reply in English for the email below, addressing ONLY the specified request types using the provided data. Do NOT include information unrelated to the request types. Only include payment details for valid BLs. Do not mention payments for invalid BLs.

Request types: {json.dumps(request_types)}
{chr(10).join(prompt_sections)}

Email: {full_text}{attachment_info}

Canned responses: {canned_responses_text}

Return a JSON object:
{{
  "classification": "{"combined_request" if len(request_types) > 1 else request_types[0] if request_types else "general_enquiry"}",
  "reply": "Reply addressing ONLY the detected requests."
}}
"""
    logger.debug(f"[OpenAI Email] Sending prompt to OpenAI:\n{prompt}")

    # --- OpenAI Call ---
    try:
        messages = [
            {"role": "system", "content": "You're a shipping email agent."},
            {"role": "user", "content": prompt}
        ]
        content = openai_call_with_fallback(messages, temperature=0)
        logger.debug(f"[OpenAI Email] Received response from OpenAI:\n{content}")
        
        try:
            action = json.loads(content)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    action = json.loads(match.group(0))
                except json.JSONDecodeError:
                    logger.error(f"[OpenAI Email] Failed to parse JSON from response.\nPrompt: {prompt}\nResponse: {content}")
                    action = None
            else:
                logger.error(f"[OpenAI Email] No JSON found in response.\nPrompt: {prompt}\nResponse: {content}")
                action = None
        
        if not action or not isinstance(action, dict):
            logger.error(f"[OpenAI Email] Invalid response format.\nPrompt: {prompt}\nResponse: {content}")
            action = {
                'classification': 'general_enquiry',
                'reply': 'Could not process email.'
            }
    except Exception as e:
        logger.error(f"[OpenAI Email] Exception during OpenAI call: {e}\nPrompt: {prompt}")
        action = {
            'classification': 'general_enquiry',
            'reply': 'Could not process email.'
        }

    # --- Validate and Process Reply ---
    classification = action.get('classification', 'general_enquiry')
    custom_reply = action.get('reply', 'We could not process your request. Please provide more details or contact us for assistance.')
    logger.info(f"[OpenAI Email] Classification: {classification}, Reply: {custom_reply[:100]}...")

    # Validate reply includes all request types and BLs
    reply_lower = custom_reply.lower()
    missing_requests = []
    
    # Check if all BLs are mentioned in the reply
    missing_bls = []
    for bl in bl_numbers:
        if bl.lower() not in reply_lower:
            missing_bls.append(bl)
    
    if missing_bls:
        logger.warning(f"[Validation] Missing BLs in reply: {missing_bls}")
        # Add missing BLs to reply
        bl_info = []
        for bl in missing_bls:
            if bl in valid_bls:
                bl_info.append(f"BL {bl}: CTN {valid_bls[bl]['ctn']}, Invoice: {valid_bls[bl]['invoice_link']}")
            else:
                bl_info.append(f"BL {bl}: Not found in our system")
        
        if bl_info:
            custom_reply += f"\n\nAdditional BL Information:\n" + "\n".join(bl_info)

    # --- Build BL-to-paid_amount mapping ---
    bl_payment_map = {}
    
    # First try to extract BL-specific payments
    bl_specific_payments = extract_bl_specific_payments(body, bl_numbers)
    logger.info(f"\033[92m[Payment Mapping] BL-specific payments: {bl_specific_payments}\033[0m")
    
    # If no BL-specific payments found but we have multiple BLs and a total paid amount, distribute evenly
    if not bl_specific_payments and len(bl_numbers) > 1 and paid_amount is not None:
        amount_per_bl = paid_amount / len(bl_numbers)
        for bl in bl_numbers:
            bl_specific_payments[bl] = amount_per_bl
        logger.info(f"\033[92m[Payment Mapping] Distributed total amount {paid_amount} among {bl_numbers} = {amount_per_bl} each\033[0m")
    
    # If valid_bls has paid_amount per BL, use that; else use BL-specific payments or fallback to total paid_amount
    for bl in bl_numbers:
        if bl in valid_bls and valid_bls[bl].get('paid_amount', 0) > 0:
            bl_payment_map[bl] = valid_bls[bl]['paid_amount']
            logger.info(f"\033[92m[Payment Mapping] Using DB paid_amount for {bl}: {valid_bls[bl]['paid_amount']}\033[0m")
        elif bl in bl_specific_payments:
            bl_payment_map[bl] = bl_specific_payments[bl]
            logger.info(f"\033[92m[Payment Mapping] Using extracted payment for {bl}: {bl_specific_payments[bl]}\033[0m")
        elif paid_amount is not None:
            bl_payment_map[bl] = paid_amount
            logger.info(f"\033[92m[Payment Mapping] Using total paid_amount for {bl}: {paid_amount}\033[0m")
    
    # If no BLs but paid_amount exists, create a dummy mapping
    if not bl_payment_map and paid_amount is not None:
        bl_payment_map['UNKNOWN'] = paid_amount
        logger.info(f"\033[92m[Payment Mapping] Created dummy mapping for UNKNOWN: {paid_amount}\033[0m")
    
    logger.info(f"\033[92m[Payment Mapping] Final BL payment map: {bl_payment_map}\033[0m")

    # --- Add Payment Summary for Payment Receipts ---
    if 'payment_receipt' in request_types and valid_bls and paid_amount is not None:
        total_invoice = sum(info.get('ctn_fee', 0.0) + info.get('service_fee', 0.0) for info in valid_bls.values())
        
        # Only add summary if it's not already in the reply
        if 'underpayment' not in custom_reply.lower() and 'overpayment' not in custom_reply.lower() and 'payment match' not in custom_reply.lower():
            if paid_amount < total_invoice - 0.01:
                diff = total_invoice - paid_amount
                custom_reply += f"\n\n⚠️ UNDERPAYMENT: We have received your payment of ${paid_amount:.2f}, but the invoice amount is ${total_invoice:.2f}. There is an outstanding balance of ${diff:.2f}."
                logger.warning(f"\033[93m[Payment Check] Underpayment detected: ${diff:.2f}\033[0m")
            elif paid_amount > total_invoice + 0.01:
                diff = paid_amount - total_invoice
                custom_reply += f"\n\n💰 OVERPAYMENT: We have received your payment of ${paid_amount:.2f}, but the invoice amount is ${total_invoice:.2f}. We will contact you regarding the excess payment of ${diff:.2f}."
                logger.info(f"\033[92m[Payment Check] Overpayment detected: ${diff:.2f}\033[0m")
            else:
                custom_reply += f"\n\n✅ PAYMENT MATCH: Your payment of ${paid_amount:.2f} matches the invoice amount of ${total_invoice:.2f}."
                logger.info(f"\033[92m[Payment Check] Payment matches invoice amount\033[0m")
    
    # Set confidence score based on validation
    if missing_requests or missing_bls:
        confidence_score = 0.7
    else:
        confidence_score = 0.95

    result = {
        'classification': classification,
        'confidence_score': confidence_score,
        'custom_reply': custom_reply,
        'auto_send': auto_send,
        'paid_amount': paid_amount,
        'bl_numbers': bl_numbers,
        'bl_payment_map': bl_payment_map,
        'translated_body': translated_body if incoming_is_chinese else None,
        'request_types': request_types,
        'valid_bls': valid_bls,
        'invalid_bls': invalid_bls
    }
    
    logger.info(f"[AI Processing] AI processing completed successfully")
    logger.info(f"[AI Processing] Final result: {result}")
    
    return result

def save_draft_reply(to_addr, subject, reply, confidence_result=None, email_id=None):
    """Save draft reply to database"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO customer_email_replies (customer_email_id, sender, body, confidence_score, auto_send_recommended, is_draft, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            email_id,
            'openai_draft',
            reply,
            confidence_result.get('confidence_score', 0.0) if confidence_result else 0.0,
            confidence_result.get('auto_send', False) if confidence_result else False,
            True,  # Always save as draft for manual review
            get_hk_now()
        ))
        
        reply_id = cursor.fetchone()[0]
        conn.commit()
        logger.info(f"✅ Draft reply saved with ID: {reply_id}")
        return reply_id
        
    except Exception as e:
        logger.error(f"❌ Failed to save draft reply: {e}")
        return None
    finally:
        cursor.close()
        conn.close()

def send_fcm_notification(title, body, data=None):
    """Send FCM notification using real FCM service"""
    try:
        from fcm_service_fallback import fcm_service_fallback
        
        # Get all FCM tokens for notifications
        conn = get_db_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT token FROM fcm_tokens WHERE is_active = TRUE')
        tokens = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        if tokens:
            # Send notification to all active tokens
            fcm_service_fallback.send_notification(
                tokens=tokens,
                title=title,
                body=body,
                data=data or {}
            )
            logger.info(f"✅ FCM notification sent: {title} - {body}")
            return True
        else:
            logger.info("ℹ️ No FCM tokens found for notifications")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to send FCM notification: {e}")
        return False

def process_payment_receipt_email(email_id, from_addr, subject, body_text, attachments, bl_payment_map, conn=None):
    """
    Centralized logic to process a payment receipt email using BL-to-amount mapping.
    - Uses a provided dict of BL numbers to paid amounts.
    - Uploads receipt (if any) to Cloudinary.
    - Updates the corresponding bill in bill_of_lading.
    - Mark the email as processed_for_payments = TRUE.
    - Compares paid amount to invoice amount for each BL before updating.
    """
    close_conn = False
    if conn is None:
        conn = get_db_conn()
        close_conn = True
    cursor = conn.cursor()

    if not bl_payment_map or not isinstance(bl_payment_map, dict):
        logger.warning(f"No BL payment map provided for email {email_id}. Marking as processed.")
        cursor.execute("UPDATE customer_emails SET processed_for_payments=TRUE WHERE id=%s", (email_id,))
        conn.commit()
        if close_conn:
            cursor.close()
            conn.close()
        return False

    logger.info(f"Processing payment for email {email_id} with BL payment map: {bl_payment_map}")

    tolerance = 2.0 # Allow for small discrepancies
    hk_now = get_hk_now_iso()

    # 1. Look for a PDF attachment first
    receipt_url = None
    for att in attachments:
        if att.lower().endswith('.pdf'):
            receipt_url = upload_filepath_to_cloudinary(att, folder="receipts")
            logger.info(f"\033[92m🎉 SUCCESS! RECEIPT UPLOADED: {receipt_url} for BLs {list(bl_payment_map.keys())} 🎉\033[0m")
            break

    # 2. If no PDF, generate one from the email body
    if not receipt_url and body_text:
        try:
            temp_pdf_path = generate_pdf_from_text(body_text, f"temp_receipt_{email_id}.pdf")
            receipt_url = upload_filepath_to_cloudinary(temp_pdf_path, folder="receipts")
            logger.info(f"\033[92m🎉 SUCCESS! RECEIPT UPLOADED (from email body): {receipt_url} for BLs {list(bl_payment_map.keys())} 🎉\033[0m")
            os.remove(temp_pdf_path)
        except Exception as e:
            logger.error(f"Failed to generate or upload PDF from email body: {e}")

    # 3. For each BL, verify and update
    for bl, paid_amount in bl_payment_map.items():
        cursor.execute("SELECT id, ctn_fee, service_fee FROM bill_of_lading WHERE bl_number = %s", (bl,))
        bill_row = cursor.fetchone()
        if not bill_row:
            logger.warning(f"BL {bl} not found in DB for email {email_id}. Skipping.")
            continue
        bill_id = bill_row[0]
        ctn_fee = float(bill_row[1] or 0)
        service_fee = float(bill_row[2] or 0)
        invoice_amount = ctn_fee + service_fee
        if paid_amount is None or not isinstance(paid_amount, (int, float)):
            logger.warning(f"No valid payment amount for BL {bl} in email {email_id}. Skipping.")
            continue
        paid_amount_f = float(paid_amount)
        if paid_amount_f < invoice_amount - tolerance:
            logger.warning(f"Underpayment for BL {bl} in email {email_id}. Expected: {invoice_amount}, Paid: {paid_amount_f}. Skipping.")
            continue
        # If exact or overpaid, proceed to process and upload receipt
        if receipt_url:
            cursor.execute("""
                UPDATE bill_of_lading
                SET receipt_filename = %s, status = 'Awaiting Bank In', receipt_uploaded_at = %s
                WHERE id = %s
            """, (receipt_url, hk_now, bill_id))
            logger.info(f"Updated bill {bill_id} with receipt from email {email_id}")
        else:
            logger.warning(f"No receipt could be generated for email {email_id}. Bill {bill_id} not updated.")

    # Mark email as processed
    cursor.execute("UPDATE customer_emails SET processed_for_payments=TRUE WHERE id=%s", (email_id,))
    conn.commit()
    
    # Send FCM push notification for payment receipt processing
    try:
        from fcm_service_fallback import fcm_service_fallback
        # Get all FCM tokens for notifications
        cursor.execute('SELECT token FROM fcm_tokens')
        tokens = [row[0] for row in cursor.fetchall()]
        
        if tokens and bl_payment_map:
            bl_list = list(bl_payment_map.keys())
            total_paid = sum(bl_payment_map.values())
            fcm_service_fallback.send_notification(
                tokens=tokens,
                title='💰 Payment Receipt Processed',
                body=f'Payment processed for BL(s): {", ".join(bl_list)} - Total: ${total_paid}',
                data={
                    'type': 'payment_receipt',
                    'sender': from_addr,
                    'bl_numbers': ','.join(bl_list),  # Convert list to string
                    'total_amount': str(total_paid),  # Convert to string
                    'email_id': str(email_id),  # Convert to string
                    'receipt_url': receipt_url or '',
                    'timestamp': datetime.now().isoformat()
                }
            )
            logger.info(f"✅ FCM notification sent for payment receipt: {bl_list} from {from_addr}")
        else:
            logger.info("ℹ️ No FCM tokens found for payment notifications")
    except Exception as e:
        logger.error(f"Failed to send FCM notification for payment: {str(e)}")
    
    if close_conn:
        cursor.close()
        conn.close()
    return True

def get_email_processing_status():
    """Get current email processing status"""
    return {
        'is_processing': email_processing_status['is_processing'],
        'started_by': email_processing_status['started_by'],
        'started_at': email_processing_status['started_at'],
        'processed_count': email_processing_status['processed_count']
    }

def acquire_email_processing_lock(user_id=None, timeout=30):
    """Acquire email processing lock"""
    if email_processing_lock.acquire(timeout=timeout):
        email_processing_status['is_processing'] = True
        email_processing_status['started_by'] = user_id or 'unknown'
        email_processing_status['started_at'] = time.time()
        email_processing_status['processed_count'] = 0
        logger.info(f"🔒 Email processing lock acquired by: {user_id or 'unknown'}")
        return True
    else:
        logger.warning(f"⏰ Email processing lock already held")
        return False

def release_email_processing_lock():
    """Release email processing lock"""
    try:
        email_processing_status['is_processing'] = False
        email_processing_status['started_by'] = None
        email_processing_status['started_at'] = None
        email_processing_lock.release()
        logger.info("🔓 Email processing lock released")
    except Exception as e:
        logger.error(f"❌ Failed to release email processing lock: {e}")

def extract_contact_info(text):
    """Extract contact information from text"""
    if not text:
        return {}
    
    contact_info = {}
    
    # Extract email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        contact_info['emails'] = emails
    
    # Extract phone numbers
    phone_pattern = r'(\+?[\d\s\-\(\)]{7,})'
    phones = re.findall(phone_pattern, text)
    if phones:
        contact_info['phones'] = phones
    
    # Extract names (basic pattern)
    name_pattern = r'([A-Z][a-z]+ [A-Z][a-z]+)'
    names = re.findall(name_pattern, text)
    if names:
        contact_info['names'] = names
    
    return contact_info

def process_inbox(user_id=None):
    """Process inbox emails with AI capabilities"""
    logger.info(f"🔄 Starting email processing for user: {user_id}")
    
    # Try to acquire the database lock
    if not acquire_db_processing_lock(user_id or 'unknown_user'):
        logger.warning("⏰ Email processing already in progress by another user")
        return []
    
    try:
        # Connect to Gmail
        mail = connect_imap()
        if not mail:
            logger.error("❌ Failed to connect to Gmail")
            return []
        
        # Select inbox
        mail.select('inbox')
        
        # Search for unread emails only
        status, messages = mail.search(None, 'UNSEEN')
        if status != 'OK':
            logger.error('Failed to search inbox')
            return []
        
        email_ids = messages[0].split()
        logger.info(f"Found {len(email_ids)} unread emails to process")
        
        results = []
        conn = get_db_conn()
        cursor = conn.cursor()
        
        for num in email_ids:
            try:
                status, msg_data = mail.fetch(num, '(RFC822)')
                if status != 'OK':
                    continue
                    
                msg = email.message_from_bytes(msg_data[0][1])
                message_id = msg.get('Message-ID')
                
                subject, encoding = decode_header(msg['Subject'])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or 'utf-8')
                from_addr = msg.get('From')
                
                body = ""
                attachments = []
                attachment_urls = []
                
                # Ensure PDF_SAVE_DIR exists
                os.makedirs(PDF_SAVE_DIR, exist_ok=True)
                
                logger.info(f"[Email Processing] Processing email: {subject}")
                logger.info(f"[Email Processing] From: {from_addr}")
                
                # Extract body and attachments
                for part in msg.walk():
                    if part.get_content_maintype() == 'multipart':
                        continue
                        
                    # Handle text content
                    if part.get('Content-Disposition') is None:
                        if part.get_content_type() == 'text/plain':
                            charset = part.get_content_charset() or 'utf-8'
                            body += part.get_payload(decode=True).decode(charset, errors='ignore')
                        continue
                    
                    # Handle attachments
                    filename = part.get_filename()
                    if filename:
                        if isinstance(filename, bytes):
                            filename = filename.decode('utf-8', errors='ignore')
                        
                        logger.info(f"[Email Processing] Found attachment: {filename}")
                        
                        # Save file locally
                        filepath = os.path.join(PDF_SAVE_DIR, filename)
                        try:
                            with open(filepath, 'wb') as f:
                                f.write(part.get_payload(decode=True))
                            logger.info(f"✅ Saved attachment: {filepath}")
                            attachments.append(filepath)
                            attachment_urls.append(filepath)
                                
                        except Exception as e:
                            logger.error(f"❌ Failed to save attachment {filename}: {e}")
                
                # Store attachment_urls as JSONB array
                attachment_json = json.dumps(attachment_urls) if attachment_urls else None
                
                # Extract CC, BCC, and Reply-To headers
                cc_header = msg.get('Cc', '')
                bcc_header = msg.get('Bcc', '')
                reply_to_header = msg.get('Reply-To', '')
                
                # Parse email addresses from headers
                def parse_email_list(header_value):
                    if not header_value:
                        return []
                    # Split by comma and clean up each email
                    emails = []
                    for email in header_value.split(','):
                        email = email.strip()
                        if email and '@' in email:
                            # Extract just the email part if it's in "Name <email>" format
                            if '<' in email and '>' in email:
                                email = email.split('<')[1].split('>')[0]
                            emails.append(email)
                    return emails
                
                cc_emails = parse_email_list(cc_header)
                bcc_emails = parse_email_list(bcc_header)
                reply_to_emails = parse_email_list(reply_to_header)
                
                # AI Processing
                ai_result = handle_email_via_openai(subject, body, attachments, from_addr)
                
                # Store email with CC, BCC, Reply-To
                cursor.execute(
                    """
                    INSERT INTO customer_emails (sender, subject, body, created_at, processed_for_payments, message_id, attachments, bl_numbers, classification, openai_processed, cc, bcc, reply_to) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (message_id) DO NOTHING
                    RETURNING id;
                    """,
                    (from_addr, subject, body, get_hk_now(), False, message_id, attachment_json, ai_result.get('bl_numbers', []), ai_result.get('classification', 'general_enquiry'), True, cc_emails, bcc_emails, reply_to_emails)
                )
                
                result = cursor.fetchone()
                if result:
                    email_id = result[0]
                    conn.commit()
                    logger.info(f"✅ Email saved to database with ID: {email_id}")
                    logger.info(f"✅ AI Classification: {ai_result.get('classification')}")
                    logger.info(f"✅ AI Confidence: {ai_result.get('confidence_score')}")
                    
                    # Save draft reply if confidence is high enough
                    if ai_result.get('confidence_score', 0.0) >= 0.7 and ai_result.get('custom_reply'):
                        try:
                            save_draft_reply(from_addr, f"Re: {subject}", ai_result.get('custom_reply'), {
                                'confidence_score': ai_result.get('confidence_score', 0.0),
                                'classification': ai_result.get('classification', 'general'),
                                'auto_send': ai_result.get('auto_send', False)
                            }, email_id)
                            logger.info(f"[AI Reply] Draft reply saved with confidence {ai_result.get('confidence_score')}")
                        except Exception as e:
                            logger.error(f"[AI Reply] Failed to save draft: {e}")
                    
                    # Process payment receipt if this is a payment-related email
                    request_types = ai_result.get('request_types', [])
                    bl_payment_map = ai_result.get('bl_payment_map', {})
                    
                    request_types_lower = [r.lower() for r in request_types]
                    is_payment_related = any(r in request_types_lower for r in ["payment_receipt", "payment_status", "combined_request"])
                    
                    # Only process as payment if we have both payment intent AND payment data
                    is_actual_payment = is_payment_related and bl_payment_map
                    
                    # Log classification for debugging
                    logger.info(f"[CLASSIFICATION] Email: {subject}")
                    logger.info(f"[CLASSIFICATION] Request types: {request_types}")
                    logger.info(f"[CLASSIFICATION] Is payment related: {is_payment_related}")
                    logger.info(f"[CLASSIFICATION] Has payment data: {bool(bl_payment_map)}")
                    logger.info(f"[CLASSIFICATION] Is actual payment: {is_actual_payment}")
                    logger.info(f"[CLASSIFICATION] BL payment map: {bl_payment_map}")
                    
                    if is_actual_payment:
                        logger.info("[ROUTING] Detected payment receipt intent — processing receipt upload + DB update.")
                        process_payment_receipt_email(
                            email_id=email_id,
                            from_addr=from_addr,
                            subject=subject,
                            body_text=body,
                            attachments=attachments,
                            bl_payment_map=bl_payment_map,
                            conn=conn,
                        )
                    else:
                        if not is_payment_related:
                            logger.warning(f"[ROUTING] Email NOT processed as payment: Not payment-related (request_types: {request_types})")
                        if not bl_payment_map:
                            logger.warning(f"[ROUTING] Email NOT processed as payment: No payment data (bl_payment_map: {bl_payment_map})")
                    
                    # Mark email as read
                    mail.store(num, '+FLAGS', '\\Seen')
                    logger.info(f"Marked email as read: {subject}")
                    
                    # Send FCM push notification for new email
                    try:
                        from fcm_service_fallback import fcm_service_fallback
                        import datetime as dt
                        
                        # Get all FCM tokens for notifications
                        cursor.execute('SELECT token FROM fcm_tokens WHERE is_active = TRUE')
                        tokens = [row[0] for row in cursor.fetchall()]
                        
                        if tokens:
                            # Simple notification - all emails show as "new email"
                            title = "📧 You have new email"
                            body = "New customer email received"
                            
                            fcm_service_fallback.send_notification(
                                tokens=tokens,
                                title=title,
                                body=body,
                                data={
                                    'type': 'new_email',
                                    'email_id': str(email_id),
                                    'timestamp': dt.datetime.now().isoformat()
                                }
                            )
                            logger.info(f"✅ FCM notification sent for new email: {subject} from {from_addr}")
                        else:
                            logger.info("ℹ️ No FCM tokens found for notifications")
                    except Exception as e:
                        logger.error(f"Failed to send FCM notification: {str(e)}")
                        logger.error(f"FCM Error details: {e}")
                    
                    results.append({"email_id": email_id, "classification": ai_result.get('classification', 'general')})
                else:
                    logger.info(f"📧 Email already exists in database: {message_id}")
                
            except Exception as e:
                logger.error(f"❌ Error processing email {num}: {e}")
                continue
        
        cursor.close()
        conn.close()
        mail.logout()
        
        # Update final count and release lock
        email_processing_status['processed_count'] = len(results)
        logger.info(f"✅ Email processing completed: {len(results)} emails processed")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Email processing failed: {e}")
        return []
    finally:
        # Always release the lock
        release_db_processing_lock(user_id or 'unknown_user')

def ingest_emails():
    """Alias for process_inbox to maintain compatibility"""
    return process_inbox() 