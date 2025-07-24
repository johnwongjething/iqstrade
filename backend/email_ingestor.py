"""
Email Ingestor for IQSTrade
- Connects to IMAP inbox
- Filters unread emails with PDF attachments
- Downloads PDFs and passes to ocr_processor
- Uses OpenAI to classify email and draft reply
- Marks emails as read
- Logs all actions
"""
import os
import imaplib
import email
from email.header import decode_header
import logging
from ocr_processor import process_pdf
from dotenv import load_dotenv
import openai
from config import CloudinaryConfig
import json
import re
from db_utils import get_db_conn
import datetime
from utils.unified_response_handler import get_response_handler
from utils.confidence_scorer import confidence_scorer
from invoice_utils import find_invoice_info, find_ctn_info

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env from .env
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

IMAP_SERVER = os.getenv('EMAIL_HOST')
EMAIL_USER = os.getenv('EMAIL_USERNAME')
EMAIL_PASS = os.getenv('EMAIL_PASSWORD')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

PDF_SAVE_DIR = 'downloads'
os.makedirs(PDF_SAVE_DIR, exist_ok=True)

# Initialize unified response handler
response_handler = get_response_handler(get_db_conn)

def connect_imap():
    return imaplib.IMAP4_SSL(IMAP_SERVER)

def handle_email_via_openai(subject, body, attachments, from_addr):
    # --- Extract payment amount from PDF raw_text and email body as fallback ---
    def extract_payment_amount(text):
        if not text:
            return None
        # Look for patterns like $380, USD 380, Amount: 380, Amount: $380, etc.
        patterns = [
            r'\$\s?([0-9]+(?:\.[0-9]{1,2})?)',
            r'USD\s*([0-9]+(?:\.[0-9]{1,2})?)',
            r'Amount[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)',
            r'Paid[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)',
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except Exception:
                    continue
        return None

    fallback_paid_amount = None
    # Try to extract from PDF paid_amount field first, then raw_text, then email body
    if attachments:
        for att_path in attachments:
            if att_path.lower().endswith('.pdf'):
                try:
                    pdf_fields = process_pdf(att_path)
                    if pdf_fields and isinstance(pdf_fields, dict):
                        # 1. Prefer structured paid_amount from OpenAI Vision/text
                        paid_amt_struct = pdf_fields.get('paid_amount')
                        amt_val = None
                        if paid_amt_struct is not None:
                            try:
                                amt_val = float(re.sub(r'[^0-9.]+', '', str(paid_amt_struct)))
                                fallback_paid_amount = amt_val
                                break
                            except Exception:
                                pass
                        # 2. Fallback: extract from raw_text using regex
                        raw_text = pdf_fields.get('raw_text')
                        amt = extract_payment_amount(raw_text)
                        if amt is not None:
                            fallback_paid_amount = amt
                            break
                except Exception:
                    pass
    # If not found, try to extract from email body
    if fallback_paid_amount is None:
        fallback_paid_amount = extract_payment_amount(body)
    # --- Translation helpers using OpenAI ---
    # --- Extract BL numbers from PDF attachments (if any) ---
    bls_from_pdfs = set()
    if attachments:
        for att_path in attachments:
            if att_path.lower().endswith('.pdf'):
                try:
                    pdf_fields = process_pdf(att_path)
                    # Try to extract BL from known fields and raw text
                    if pdf_fields:
                        # Add BL from structured field
                        bl_val = pdf_fields.get('bl_number') if isinstance(pdf_fields, dict) else None
                        if bl_val:
                            # If multiple BLs in one field, split by comma/space
                            if isinstance(bl_val, str):
                                bls_from_pdfs.update([b.strip() for b in re.split(r'[\s,;/]+', bl_val) if b.strip()])
                        # Fallback: extract BLs from raw_text if present
                        raw_text = pdf_fields.get('raw_text') if isinstance(pdf_fields, dict) else None
                        if raw_text:
                            bl_pattern = re.compile(r'(?:提单号[:：]?\s*)?([A-Z]{2,4}\d{2,}|BL-\d{4,}|\d{3,}-\d{3,}|\d{6,})', re.IGNORECASE)
                            bls_from_pdfs.update(bl_pattern.findall(raw_text))
                except Exception as e:
                    logger.error(f"[PDF BL Extraction] Failed to extract BL from {att_path}: {e}")
    def openai_translate(text, source_lang, target_lang):
        """
        Translate text using OpenAI GPT-4o. source_lang/target_lang: 'Chinese', 'English'.
        """
        try:
            translation_prompt = f"Translate the following {source_lang} text to {target_lang}. Only return the translated text, no explanation.\n\n{text}"
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": translation_prompt},
                ],
                temperature=0,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"[OpenAI Translate] Failed: {e}")
            return text  # fallback: return original

    # Detect if incoming email is Chinese
    def is_chinese(text):
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        return chinese_chars > 0 and chinese_chars / max(1, len(text)) > 0.2

    incoming_is_chinese = is_chinese(body)
    translated_body = body
    translation_used = False
    if incoming_is_chinese:
        # Translate Chinese email to English for processing
        translated_body = openai_translate(body, 'Chinese', 'English')
        translation_used = True

    # Detect if sender claims an attachment but none is present
    missing_attachment_flag = False
    if not attachments:
        # Expanded: Look for more variations in the email body that suggest an attachment should be present
        attachment_phrases = [
            r"see (the )?attached",
            r"find (the )?attached",
            r"attached( is| are|:)?",
            r"attachment(s)?( is| are|:)?",
            r"enclosed (file|document|pdf|invoice|receipt)?",
            r"as per (the )?attachment",
            r"please refer to (the )?attachment",
            r"please see (the )?attachment",
            r"please find (the )?attachment",
            r"I've attached",
            r"I have attached",
            r"see attached",
            r"see the attached",
            r"see the attachment",
            r"see attachments",
            r"see the attachments",
            r"find attached",
            r"find the attached",
            r"find the attachment",
            r"find attachments",
            r"find the attachments",
            r"attachment is",
            r"attachment are",
            r"attachment:"
        ]
        pattern = re.compile(r"|".join(attachment_phrases), re.IGNORECASE)
        if pattern.search(body):
            missing_attachment_flag = True

    """
    Single source of truth for handling an email via OpenAI.
    1. Gets classification and a detailed draft reply from OpenAI.
    2. Customizes the reply with real data (invoice links, fees).
    3. Saves the final, customized draft reply ONCE.
    """
    # Load canned responses to provide as context to OpenAI
    try:
        with open('canned_responses.json', 'r') as f:
            canned_responses = json.load(f)
        canned_responses_text = "\n\n".join([f"Q: {r['title']}\nA: {r['body']}" for r in canned_responses])
    except Exception as e:
        logger.error(f"[OpenAI Email] Could not load canned_responses.json: {e}")
        canned_responses_text = "No canned responses available."

    full_text = f"Subject: {subject}\n\n{translated_body}"
    # Add attachment info to the prompt only if attachments exist
    if attachments:
        attachment_info = f"\n\nThe customer has attached {len(attachments)} file(s) to this email. Please mention the receipt of attachments in your reply."
    else:
        attachment_info = ""
    prompt = f"""
You are a logistics assistant. Based on the email below, provide a helpful reply.
First, check if the question can be answered from the 'CANNED RESPONSES' knowledge base. If it matches, use that template. If not, generate a reply.

CANNED RESPONSES:
{canned_responses_text}

EMAIL:
{full_text}{attachment_info}

Return a valid JSON object with keys: "classification", "info_needed", and "reply".
- "classification" must be one of ["invoice_request", "payment_receipt", "general_enquiry", "ctn_request"].
- "info_needed" must be a dictionary containing a list of all BL numbers under the key "BL_numbers" and the numeric payment amount under "paid_amount".
- For example, for an email about "payment for 001-123 and NYC220", the "BL_numbers" key must be ["001-123", "NYC220"].
"""
    
    # 1. Get base reply from OpenAI
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You're a shipping email agent."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    content = response.choices[0].message.content
    try:
        action = json.loads(content)
    except Exception:
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            action = json.loads(match.group(0))
        else:
            logger.error(f"[OpenAI Email] Could not parse JSON from response.\nPrompt: {prompt}\nResponse: {content}")
            action = {"classification": "unknown", "reply": "Could not process email.", "info_needed": {}}
    
    if not action:
        return {"classification": "error", "reply": "Could not process email."}


    # 2. Customize the reply based on classification
    classification = action.get('classification')
    bl_numbers = action.get('info_needed', {}).get('BL_numbers', [])
    custom_reply = action.get('reply', '') # Start with OpenAI's base reply

    # Log BLs from OpenAI only (original logic)
    logger.info(f"[OpenAI Email] BLs from OpenAI only: {bl_numbers}")

    # Always run fallback BL extraction on both processed email text, AI reply, and PDF attachments, merge with OpenAI's BL_numbers, and deduplicate
    bl_pattern = re.compile(r'(?:提单号[:：]?\s*)?([A-Z]{2,4}\d{2,}|BL-\d{4,}|\d{3,}-\d{3,}|\d{6,})', re.IGNORECASE)
    bl_source = translated_body if translation_used else body
    fallback_bls_email = set(bl_pattern.findall(bl_source))
    fallback_bls_reply = set(bl_pattern.findall(action.get('reply', '')))
    bl_numbers_set = set(bl_numbers) if bl_numbers else set()
    merged_bls = bl_numbers_set | fallback_bls_email | fallback_bls_reply | bls_from_pdfs
    # Lookup all merged BLs in the database and only keep those that exist
    invoice_infos = find_invoice_info(list(merged_bls))
    found_bls = [info['bl_number'] for info in invoice_infos] if invoice_infos else []
    bl_numbers = found_bls
    logger.info(f"[OpenAI Email] BLs after merging and DB filter: {bl_numbers}")

    # For critical tasks, IGNORE the AI's generic reply and build a specific one.
    if classification == 'invoice_request' and bl_numbers:
        invoice_infos = find_invoice_info(bl_numbers)
        found_bls = [info['bl_number'] for info in invoice_infos] if invoice_infos else []
        missing_bls = [bl for bl in bl_numbers if bl not in found_bls]
        reply_lines = []
        if found_bls:
            reply_lines.append("Invoice(s) found:")
            for info in invoice_infos:
                invoice_filename = info.get('invoice_filename')
                if invoice_filename:
                    invoice_link = invoice_filename
                    reply_lines.append(f"  - For BL {info['bl_number']}: You can download your invoice here: {invoice_link}")
                else:
                    reply_lines.append(f"  - For BL {info['bl_number']}: An invoice has not been generated yet.")
        if missing_bls:
            reply_lines.append("\nThe following BL numbers could not be found in our system: " + ", ".join(missing_bls) + ". Please double-check or contact us for assistance.")
        if reply_lines:
            custom_reply = "Hello,\n\n" + "\n".join(reply_lines)
        else:
            custom_reply = (
                "Hello,\n\nWe could not find any invoice records for the provided BL numbers in our system. "
                "Please double-check the BL numbers or contact us for further assistance."
            )

    # Improved: Partial BL handling for ctn_request
    elif classification == 'ctn_request' and bl_numbers:
        ctn_infos = find_ctn_info(bl_numbers)
        found_bls = [info['bl_number'] for info in ctn_infos] if ctn_infos else []
        missing_bls = [bl for bl in bl_numbers if bl not in found_bls]
        reply_lines = []
        if found_bls:
            reply_lines.append("CTN(s) found:")
            for info in ctn_infos:
                ctn_number = info.get('ctn_number', 'Not available yet')
                reply_lines.append(f"  - For BL {info['bl_number']}: The CTN number is {ctn_number}.")
        if missing_bls:
            reply_lines.append("\nThe following BL numbers could not be found in our system: " + ", ".join(missing_bls) + ". Please double-check or contact us for assistance.")
        if reply_lines:
            custom_reply = "Hello,\n\n" + "\n".join(reply_lines)
        else:
            custom_reply = (
                "Hello,\n\nWe could not find any CTN records for the provided BL numbers in our system. "
                "Please double-check the BL numbers or contact us for further assistance."
            )

    # Improved: Partial BL handling for payment_receipt
    elif classification == 'payment_receipt' and bl_numbers:
        invoice_infos = find_invoice_info(bl_numbers)
        found_bls = [info['bl_number'] for info in invoice_infos] if invoice_infos else []
        missing_bls = [bl for bl in bl_numbers if bl not in found_bls]
        paid_amount = action.get('info_needed', {}).get('paid_amount')
        # Try to convert paid_amount to float if it's a string (e.g., "$400")
        paid_amount_val = None
        if paid_amount not in (None, "", []):
            try:
                paid_amount_val = float(re.sub(r'[^0-9.]+', '', str(paid_amount)))
            except Exception:
                paid_amount_val = None
        # If still not valid, use fallback_paid_amount
        if paid_amount_val is None:
            paid_amount_val = fallback_paid_amount
        paid_amount = paid_amount_val
        reply_lines = []
        if found_bls:
            reply_lines.append("Payment(s) found:")
            for info in invoice_infos:
                invoice_filename = info.get('invoice_filename')
                reply_lines.append(f"  - For BL {info['bl_number']}: Payment record found.")
        if missing_bls:
            reply_lines.append("\nThe following BL numbers could not be found in our system: " + ", ".join(missing_bls) + ". Please double-check or contact us for assistance.")
        if reply_lines:
            custom_reply = "Hello,\n\n" + "\n".join(reply_lines)
        else:
            custom_reply = (
                "Hello,\n\nWe could not find any invoice records for the provided BL numbers in our system. "
                "If you believe this is an error, please double-check the BL numbers or contact us for further assistance."
            )


    # 3. For general enquiries, add fee and payment info to the AI's reply if placeholders are present.
    if "[insert CTN fee amount]" in custom_reply or "[insert service fee amount]" in custom_reply:
        invoice_infos = find_invoice_info(bl_numbers)
        if invoice_infos:
            # Use first invoice for general fee info in the reply body
            info = invoice_infos[0]
            ctn_fee = info.get('ctn_fee', 'N/A')
            service_fee = info.get('service_fee', 'N/A')
            custom_reply = custom_reply.replace("[insert CTN fee amount]", str(ctn_fee))
            custom_reply = custom_reply.replace("[insert service fee amount]", str(service_fee))

    # 4. Add underpaid/overpaid notice if payment_receipt and invoice/paid amounts are available
    if classification == 'payment_receipt' and bl_numbers:
        invoice_infos = find_invoice_info(bl_numbers)
        # Use the paid_amount determined above (OpenAI or fallback)
        if invoice_infos and paid_amount is not None:
            total_invoice = sum(float(info.get('ctn_fee', 0) or 0) + float(info.get('service_fee', 0) or 0) for info in invoice_infos)
            try:
                paid_amount = float(paid_amount)
            except Exception:
                paid_amount = None
            if paid_amount is not None:
                if paid_amount < total_invoice - 0.01:
                    diff = total_invoice - paid_amount
                    notice = f"\n\nNote: We have received your payment of ${paid_amount:.2f}, but the invoice amount is ${total_invoice:.2f}. There is an outstanding balance of ${diff:.2f}."
                    custom_reply += notice
                elif paid_amount > total_invoice + 0.01:
                    diff = paid_amount - total_invoice
                    notice = f"\n\nNote: We have received your payment of ${paid_amount:.2f}, but the invoice amount is ${total_invoice:.2f}. We will contact you regarding the excess payment of ${diff:.2f}."
                    custom_reply += notice
        # Always add a standard friendly closing and signature for payment confirmation
        if not any(phrase in custom_reply for phrase in ["Best regards", "IQS Trade Team", "IQSTrade客服团队", "祝商祺"]):
            custom_reply += "\n\nIf you have any questions, please let us know.\n\nBest regards,\nIQS Trade Team"

    # 5. Remove attachment references if there are no attachments
    if not attachments:
        import re as _re
        # Remove any line mentioning attachments, attached, or similar (English)
        custom_reply = _re.sub(r'^.*\b(attach|attachment|attached|attachments)\b.*$', '', custom_reply, flags=_re.MULTILINE | _re.IGNORECASE)
        # Remove any line mentioning attachments in Chinese (expanded)
        custom_reply = _re.sub(r'^.*(已?附上|附件|请查收附件|请见附件|请参见附件|请参考附件|请见附档|请查收附档|请见附加文件|请查收附加文件|附件见下|请查附件|请见下方附件|请见随信附件).*$','', custom_reply, flags=_re.MULTILINE)
        # Remove any leftover empty lines
        custom_reply = '\n'.join([line for line in custom_reply.splitlines() if line.strip()])
        # If sender mentioned an attachment but none is present, add a warning to the reply (English/Chinese)
        if missing_attachment_flag:
            custom_reply += ("\n\nNote: You mentioned an attachment in your email, but no files were attached. "
                             "If you intended to send a file, please resend your email with the attachment included."
                             "\n\n注意：您在邮件中提到有附件，但未检测到任何文件。如需补发，请重新发送带附件的邮件。")

    # --- Translate reply back to Chinese if original email was Chinese ---
    reply_is_chinese = False
    if translation_used:
        # Translate the reply to Chinese
        custom_reply = openai_translate(custom_reply, 'English', 'Chinese')
        reply_is_chinese = True
    else:
        # Detect reply language (simple heuristic: if >20% of chars are Chinese, treat as Chinese)
        reply_is_chinese = is_chinese(custom_reply)

    # Canned responses: warn if only English available for Chinese email
    if reply_is_chinese and 'No canned responses available.' in canned_responses_text:
        logger.warning('[OpenAI Email] No Chinese canned responses available for Chinese email.')

    # Add standard polite closing for Chinese replies if missing
    if reply_is_chinese and not any(phrase in custom_reply for phrase in ['祝商祺', '此致敬礼', '顺祝商祺', '敬请回复']):
        custom_reply += '\n\n祝商祺！\nIQSTrade客服团队'

    # Log original Chinese text for debugging if fallback BL or attachment detection triggers
    if reply_is_chinese and (not bl_numbers or missing_attachment_flag):
        logger.info(f"[OpenAI Email] Original Chinese email body: {body}")

    # 6. Get confidence score (using the final reply)
    confidence_result = confidence_scorer.get_auto_send_recommendation(
        full_text, custom_reply, classification, bl_numbers
    )
    # Enhanced logging for found/missing BLs and missing attachment
    # Always log lists for found_bls and missing_bls, even if empty
    found_bls_log = found_bls if 'found_bls' in locals() else []
    missing_bls_log = missing_bls if 'missing_bls' in locals() else []
    logger.info(f"[OpenAI Email] BLs found: {found_bls_log}, BLs missing: {missing_bls_log}")
    if missing_attachment_flag:
        logger.info(f"[OpenAI Email] Missing attachment detected for email from {from_addr} (subject: {subject})")
    # 7. Save the final draft ONCE
    save_draft_reply(from_addr, subject, custom_reply, confidence_result)
    logger.info(f"[OpenAI Email] Final customized reply saved for email from {from_addr}")

    return {
        'classification': classification, 
        'reply': custom_reply,
        'bl_numbers': bl_numbers, # Return the list
        'paid_amount': paid_amount,  # Always return the final float value used in logic
        'confidence_score': confidence_result['confidence_score'],
        'auto_send': confidence_result['auto_send']
    }

def save_draft_reply(to_addr, subject, reply, confidence_result=None):
    """
    Save a draft reply to the customer_email_replies table.
    Now includes confidence scoring information.
    """
    logger.info(f"[Draft Reply] To: {to_addr}, Subject: {subject}, Reply: {reply}")
    
    # Determine if this should be auto-sent or kept as draft
    is_draft = True
    if confidence_result and confidence_result['auto_send']:
        is_draft = False
        logger.info(f"[Auto-Send] High confidence ({confidence_result['confidence_score']:.2f}) - marking for auto-send")
    
    conn = get_db_conn()
    cur = conn.cursor()
    
    # Find the customer_email_id by sender and subject (latest match)
    cur.execute("SELECT id FROM customer_emails WHERE sender = %s AND subject = %s ORDER BY created_at DESC LIMIT 1", (to_addr, subject))
    row = cur.fetchone()
    if row:
        customer_email_id = row[0]
    else:
        # If not found, create a new customer_email entry
        cur.execute("INSERT INTO customer_emails (sender, subject, body, created_at) VALUES (%s, %s, %s, %s) RETURNING id", (to_addr, subject, '', datetime.datetime.now()))
        customer_email_id = cur.fetchone()[0]
        conn.commit()
    
    # Insert draft reply with confidence information
    try:
        confidence_score = confidence_result['confidence_score'] if confidence_result else None
        confidence_reasoning = json.dumps(confidence_result['reasoning']) if confidence_result else None
        
        cur.execute("""
            INSERT INTO customer_email_replies (
                customer_email_id, sender, body, created_at, is_draft, 
                confidence_score, confidence_reasoning, auto_send_recommended
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            customer_email_id, 
            'openai_draft', 
            reply, 
            datetime.datetime.now(), 
            is_draft,
            confidence_score,
            confidence_reasoning,
            confidence_result['auto_send'] if confidence_result else False
        ))
        conn.commit()
        
        if is_draft:
            logger.info(f"[Draft Reply] Saved to DB for customer_email_id={customer_email_id} (DRAFT)")
        else:
            logger.info(f"[Auto-Send] Saved to DB for customer_email_id={customer_email_id} (AUTO-SEND)")
            
    except Exception as e:
        logger.error(f"[Draft Reply] Failed to save draft: {e}")
        # If new columns don't exist, try without them
        try:
            cur.execute("""
                INSERT INTO customer_email_replies (customer_email_id, sender, body, created_at, is_draft)
                VALUES (%s, %s, %s, %s, %s)
            """, (customer_email_id, 'openai_draft', reply, datetime.datetime.now(), is_draft))
            conn.commit()
            logger.info(f"[Draft Reply] Saved with basic columns for customer_email_id={customer_email_id}")
        except Exception as e2:
            logger.error(f"[Draft Reply] Failed to save even with basic columns: {e2}")
    
    cur.close()
    conn.close()

def process_inbox():
    logger.info("Connecting to IMAP server...")
    mail = connect_imap()
    mail.login(EMAIL_USER, EMAIL_PASS)
    mail.select('inbox')
    status, messages = mail.search(None, '(UNSEEN)')
    if status != 'OK':
        logger.error('Failed to search inbox')
        return
    for num in messages[0].split():
        status, msg_data = mail.fetch(num, '(RFC822)')
        if status != 'OK':
            continue
        msg = email.message_from_bytes(msg_data[0][1])
        subject, encoding = decode_header(msg['Subject'])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or 'utf-8')
        from_addr = msg.get('From')
        body = ""
        attachments = []
        for part in msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                if part.get_content_type() == 'text/plain':
                    charset = part.get_content_charset() or 'utf-8'
                    body += part.get_payload(decode=True).decode(charset, errors='ignore')
                continue
            filename = part.get_filename()
            if filename and filename.lower().endswith('.pdf'):
                filepath = os.path.join(PDF_SAVE_DIR, filename)
                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                logger.info(f"Saved PDF: {filepath}")
                attachments.append(filepath)
        # Use OpenAI to classify and draft reply
        handle_email_via_openai(subject, body, attachments, from_addr)
        # Optionally process PDFs
        for pdf_path in attachments:
            process_pdf(pdf_path)
        mail.store(num, '+FLAGS', '\\Seen')
        logger.info(f"Marked email as read: {subject}")
    mail.logout()

if __name__ == "__main__":
    process_inbox() 