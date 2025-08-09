"""
Email Ingestor for IQSTrade
- Connects to IMAP inbox
- Filters unread emails with PDF attachments
- Downloads PDFs and passes to ocr_processor
- Uses OpenAI to draft reply based on pre-classified requests
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
from utils.timezone_utils import get_hk_now, get_hk_now_iso, get_hk_timestamp
from utils.confidence_scorer import confidence_scorer
from invoice_utils import find_invoice_info, find_ctn_info, generate_pdf_from_text
from utils.balance_utils import process_payment_balance, check_payment_processed, mark_payment_processed
from utils.duplicate_payment_notifications import send_duplicate_payment_notifications
from decimal import Decimal
import tempfile
import pytz
from cloudinary_utils import upload_filepath_to_cloudinary
import threading
import time
import httpx

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
        
        # Try to insert a new lock
        cursor.execute("""
            INSERT INTO email_processing_locks (user_id, created_at, expires_at)
            VALUES (%s, NOW(), NOW() + INTERVAL '%s seconds')
            ON CONFLICT DO NOTHING
            RETURNING id
        """, (user_id, timeout_seconds))
        
        result = cursor.fetchone()
        if result:
            conn.commit()
            logger.info(f"🔒 Database lock acquired by: {user_id}")
            return True
        else:
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
            
    except Exception as e:
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
            return {
                'is_processing': True,
                'started_by': result[0],
                'started_at': result[1].isoformat() if result[1] else None,
                'expires_at': result[2].isoformat() if result[2] else None
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
            'expires_at': None
        }
    finally:
        cursor.close()
        conn.close()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load env from .env.local (or .env as fallback)
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
if not os.path.exists(env_file):
    env_file = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_file)

IMAP_SERVER = os.getenv('EMAIL_HOST')
EMAIL_USER = os.getenv('EMAIL_USERNAME')
EMAIL_PASS = os.getenv('EMAIL_PASSWORD')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

PDF_SAVE_DIR = 'downloads'
os.makedirs(PDF_SAVE_DIR, exist_ok=True)

# Initialize unified response handler
response_handler = get_response_handler(get_db_conn)

# Static configurations
BUSINESS_HOURS = "Monday to Friday, 9:00 AM to 5:00 PM (Hong Kong time)"
PAYMENT_METHODS = ["Bank Transfer", "Allinpay", "Stripe"]
CTN_PROCESSING_TIME = "24 to 48 hours after payment confirmation"

def get_email_processing_status():
    """Get current email processing status"""
    return {
        'is_processing': email_processing_status['is_processing'],
        'started_by': email_processing_status['started_by'],
        'started_at': email_processing_status['started_at'],
        'processed_count': email_processing_status['processed_count'],
        'lock_acquired': email_processing_lock.locked()
    }

def acquire_email_processing_lock(user_id=None, timeout=30):
    """Try to acquire email processing lock with timeout"""
    try:
        # Try to acquire lock with timeout
        if email_processing_lock.acquire(blocking=True, timeout=timeout):
            email_processing_status['is_processing'] = True
            email_processing_status['started_by'] = user_id or 'background'
            email_processing_status['started_at'] = get_hk_now_iso()
            email_processing_status['processed_count'] = 0
            logger.info(f"🔒 Email processing lock acquired by: {user_id or 'background'}")
            return True
        else:
            logger.warning(f"⏰ Email processing lock acquisition timeout after {timeout}s")
            return False
    except Exception as e:
        logger.error(f"❌ Failed to acquire email processing lock: {e}")
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

def connect_imap():
    return imaplib.IMAP4_SSL(IMAP_SERVER)

def generate_duplicate_payment_reply(duplicate_bls, bl_payment_map):
    """Generate a duplicate payment response without calling AI"""
    total_amount = sum(bl_payment_map.values()) if bl_payment_map else 0
    
    reply_lines = [
        "Hello,",
        "",
        "⚠️ DUPLICATE PAYMENT DETECTED:",
    ]
    
    for bl in duplicate_bls:
        reply_lines.append(f"  - For BL {bl}: This payment has already been processed previously.")
    
    reply_lines.extend([
        "",
        f"💰 DUPLICATE PAYMENT: We detected that your payment of ${total_amount:.2f} for BL(s) {', '.join(duplicate_bls)} has already been processed. No action is required from you.",
        "",
        "Best regards,",
        "IQS Trade Team"
    ])
    
    return "\n".join(reply_lines)

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
        cursor.execute("SELECT id, ctn_fee, service_fee, customer_username, balance_applied FROM bill_of_lading WHERE bl_number = %s", (bl,))
        bill_row = cursor.fetchone()
        if not bill_row:
            logger.warning(f"BL {bl} not found in DB for email {email_id}. Skipping.")
            continue
        bill_id = bill_row[0]
        ctn_fee = float(bill_row[1] or 0)
        service_fee = float(bill_row[2] or 0)
        customer_username = bill_row[3]
        balance_applied = float(bill_row[4] or 0)
        # Calculate adjusted invoice amount (original fees minus balance applied)
        invoice_amount = (ctn_fee + service_fee) - balance_applied
        
        if paid_amount is None or not isinstance(paid_amount, (int, float)):
            logger.warning(f"No valid payment amount for BL {bl} in email {email_id}. Skipping.")
            continue
            
        paid_amount_f = float(paid_amount)
        
        # Check if payment already processed to prevent duplicates
        if check_payment_processed(bill_id, 'email'):
            logger.warning(f"Payment already processed for BL {bl} (ID: {bill_id}). Skipping.")
            
            # Send duplicate payment notifications
            try:
                # Get customer email for notifications
                cursor.execute("SELECT customer_email FROM bill_of_lading WHERE id = %s", (bill_id,))
                customer_email_result = cursor.fetchone()
                customer_email = customer_email_result[0] if customer_email_result else None
                
                # Get original payment date
                cursor.execute("""
                    SELECT created_at FROM customer_balance_transactions 
                    WHERE reference_id = %s AND payment_source = 'email' 
                    ORDER BY created_at DESC LIMIT 1
                """, (bill_id,))
                original_payment = cursor.fetchone()
                original_payment_date = original_payment[0] if original_payment else None
                
                send_duplicate_payment_notifications(
                    bl_id=bill_id,
                    bl_number=bl,
                    customer_username=customer_username,
                    customer_email=customer_email,
                    payment_amount=paid_amount_f,
                    payment_source='email',
                    original_payment_date=original_payment_date
                )
            except Exception as e:
                logger.error(f"Error sending duplicate payment notifications: {e}")
            
            continue
        
        # Process payment and calculate balance adjustments
        balance_adjustment = 0.0
        if customer_username:
            try:
                balance_adjustment = process_payment_balance(
                    username=customer_username,
                    payment_amount=paid_amount_f,
                    invoice_amount=invoice_amount,
                    bl_id=bill_id,
                    payment_source='email',
                    created_by='email_ingestor'
                )
                logger.info(f"Balance adjustment for {customer_username}: {balance_adjustment}")
            except Exception as e:
                logger.error(f"Error processing balance for {customer_username}: {e}")
        
        # Mark payment as processed
        mark_payment_processed(bill_id, 'email', 'email_ingestor')
        
        # Update bill status based on payment
        if paid_amount_f >= invoice_amount - tolerance:
            # Payment is sufficient (exact or overpayment)
            if receipt_url:
                cursor.execute("""
                    UPDATE bill_of_lading
                    SET receipt_filename = %s, status = 'Awaiting Bank In', receipt_uploaded_at = %s
                    WHERE id = %s
                """, (receipt_url, hk_now, bill_id))
                logger.info(f"Updated bill {bill_id} with receipt from email {email_id}")
            else:
                logger.warning(f"No receipt could be generated for email {email_id}. Bill {bill_id} not updated.")
        else:
            # Underpayment - store in unmatched_receipts
            try:
                cursor.execute("""
                    INSERT INTO unmatched_receipts (date, description, amount, reason, raw_text)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    datetime.datetime.now().date(),
                    f"Email payment for BL {bl}",
                    paid_amount_f,
                    f"Underpayment: Expected ${invoice_amount}, Paid ${paid_amount_f}",
                    f"Email from {from_addr}: {subject}"
                ))
                logger.info(f"Stored underpayment in unmatched_receipts for BL {bl}")
            except Exception as e:
                logger.error(f"Error storing underpayment: {e}")

    # Mark email as processed
    cursor.execute("UPDATE customer_emails SET processed_for_payments=TRUE WHERE id=%s", (email_id,))
    conn.commit()
    
    # Send FCM push notification for payment receipt processing
    try:
        from fcm_service_fallback import fcm_service_fallback
        # Get all FCM tokens for notifications
        cursor.execute('SELECT token FROM fcm_tokens WHERE is_active = TRUE')
        tokens = [row[0] for row in cursor.fetchall()]
        
        if tokens and bl_payment_map:
            bl_list = list(bl_payment_map.keys())
            total_paid = sum(bl_payment_map.values())
            result = fcm_service_fallback.send_notification(
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
                    'timestamp': datetime.datetime.now().isoformat()
                }
            )
            if result.get('success'):
                logger.info(f"✅ FCM notification sent for payment receipt: {bl_list} from {from_addr}")
            else:
                logger.error(f"❌ FCM notification failed: {result.get('error', 'Unknown error')}")
        else:
            logger.info("ℹ️ No FCM tokens found for payment notifications")
    except Exception as e:
        logger.error(f"Failed to send FCM notification for payment: {str(e)}")
    
    if close_conn:
        cursor.close()
        conn.close()
    return True

def openai_call_with_fallback(messages, temperature=0, max_retries=2):
    """Make OpenAI API call with fallback to different models"""
    models_to_try = ['gpt-3.5-turbo', 'gpt-4o-mini', 'gpt-4o']
    
    for attempt in range(max_retries):
        for model in models_to_try:
            try:
                logger.info(f"[OpenAI Email] Attempting call with {model}")
                
                # Add timeout to prevent hanging
                with httpx.Client(timeout=30.0) as client:
                    response = client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {OPENAI_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": model,
                            "messages": messages,
                            "temperature": temperature,
                            "max_tokens": 1000
                        }
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        logger.info(f"[OpenAI Email] Successfully used {model} for email processing")
                        return result['choices'][0]['message']['content']
                    else:
                        logger.warning(f"[OpenAI Email] {model} failed with status {response.status_code}")
                        
            except Exception as e:
                logger.error(f"[OpenAI Email] Error with {model}: {e}")
                continue
    
    # If all models fail, return a default response
    logger.error("[OpenAI Email] All models failed, using default response")
    return """Thank you for your enquiry.

To provide you with the most accurate information, please include:
• Your BL number (if you have one)
• Specific details about what you need help with

This will help me give you a more detailed and helpful response.

Alternatively, you can contact our customer service team directly for immediate assistance."""

def handle_email_via_openai(subject, body, attachments, from_addr):
    # Initialize variables
    paid_amount = None
    custom_reply = "Hello,\n\nThank you for your email. Please provide more details or contact us for assistance."
    confidence_score = 0.0
    auto_send = False

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
        
        # Handle case where amount is for multiple BLs (e.g., "Payment for B/L 001-123, NYC220 Amount: $420")
        # Also handle case where we have a paid amount from PDF but no body text
        if not bl_payments and len(bl_numbers) > 1:
            # Look for pattern like "Payment for B/L X, Y Amount: $Z"
            combined_pattern = r'(?:payment|paid|amount)[^0-9]*\$?([0-9]+(?:\.[0-9]{1,2})?)[^0-9]*(?:for\s+)?(?:b/l\s*)?([A-Z0-9\-\s,]+)'
            
            # Also try a simpler pattern for "Amount: $X"
            simple_pattern = r'amount[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)'
            logger.info(f"\033[92m[Payment Distribution] Testing pattern: {combined_pattern}\033[0m")
            logger.info(f"\033[92m[Payment Distribution] Text to match: {text}\033[0m")
            matches = re.findall(combined_pattern, text, re.IGNORECASE)
            logger.info(f"\033[92m[Payment Distribution] Pattern matches: {matches}\033[0m")
            
            for amount_str, bls_text in matches:
                try:
                    total_amount = float(amount_str)
                    # Extract BL numbers from the text
                    found_bls = []
                    for bl in bl_numbers:
                        if bl.upper() in bls_text.upper():
                            found_bls.append(bl)
                    
                    logger.info(f"\033[92m[Payment Distribution] Found BLs in text '{bls_text}': {found_bls}\033[0m")
                    
                    # Only use this match if we found at least 2 BLs (indicating it's a real multi-BL payment)
                    if len(found_bls) >= 2:
                        # Distribute amount evenly among found BLs
                        amount_per_bl = total_amount / len(found_bls)
                        for bl in found_bls:
                            bl_payments[bl] = amount_per_bl
                        logger.info(f"\033[92m[Payment Distribution] Distributed payment: {total_amount} among {found_bls} = {amount_per_bl} each\033[0m")
                        break
                    else:
                        logger.info(f"\033[93m[Payment Distribution] Skipping match - only found {len(found_bls)} BLs, need at least 2\033[0m")
                except ValueError:
                    continue
            
            # Try simple pattern if complex pattern didn't work
            if not bl_payments:
                simple_matches = re.findall(simple_pattern, text, re.IGNORECASE)
                logger.info(f"\033[92m[Payment Distribution] Simple pattern matches: {simple_matches}\033[0m")
                
                if simple_matches:
                    try:
                        total_amount = float(simple_matches[0])
                        # If we have a total amount and multiple BLs, distribute evenly
                        amount_per_bl = total_amount / len(bl_numbers)
                        for bl in bl_numbers:
                            bl_payments[bl] = amount_per_bl
                        logger.info(f"\033[92m[Payment Distribution] Simple pattern: distributed {total_amount} among {bl_numbers} = {amount_per_bl} each\033[0m")
                    except ValueError:
                        pass
            
            # If still no BL-specific payments found, try to extract from text with BL numbers
            if not bl_payments:
                # Look for patterns like "B/L 001-123, NYC220 Amount: $420"
                bl_amount_pattern = r'(?:b/l\s*|bl\s*)([a-z0-9\-\s,]+)[^0-9]*\$?([0-9]+(?:\.[0-9]{1,2})?)'
                matches = re.findall(bl_amount_pattern, text, re.IGNORECASE)
                for bls_text, amount_str in matches:
                    try:
                        total_amount = float(amount_str)
                        # Extract BL numbers from the text
                        found_bls = []
                        for bl in bl_numbers:
                            if bl.upper() in bls_text.upper():
                                found_bls.append(bl)
                        
                        if found_bls:
                            # Distribute amount evenly among found BLs
                            amount_per_bl = total_amount / len(found_bls)
                            for bl in found_bls:
                                bl_payments[bl] = amount_per_bl
                            logger.info(f"\033[92m[Payment Distribution] Distributed payment from BL pattern: {total_amount} among {found_bls} = {amount_per_bl} each\033[0m")
                            break
                    except ValueError:
                        continue
            
            # Final fallback: if we have a total amount and multiple BLs, distribute evenly
            # Note: BL validation will be done later in the main processing loop
            if not bl_payments and paid_amount is not None and len(bl_numbers) > 1:
                amount_per_bl = paid_amount / len(bl_numbers)
                for bl in bl_numbers:
                    bl_payments[bl] = amount_per_bl
                logger.info(f"\033[92m[Payment Distribution] Final fallback: distributed {paid_amount} among {bl_numbers} = {amount_per_bl} each\033[0m")
            
            # Super fallback: if still no BL-specific payments, use the total amount for all BLs
            if not bl_payments and paid_amount is not None:
                for bl in bl_numbers:
                    bl_payments[bl] = paid_amount
                logger.info(f"\033[92m[Payment Distribution] Super fallback: using total amount {paid_amount} for all BLs {bl_numbers}\033[0m")
            
            # If still no BL-specific payments found, try to extract from text with BL numbers
            if not bl_payments:
                # Look for patterns like "B/L 001-123, NYC220 Amount: $420"
                bl_amount_pattern = r'(?:b/l\s*|bl\s*)([a-z0-9\-\s,]+)[^0-9]*\$?([0-9]+(?:\.[0-9]{1,2})?)'
                matches = re.findall(bl_amount_pattern, text, re.IGNORECASE)
                for bls_text, amount_str in matches:
                    try:
                        total_amount = float(amount_str)
                        # Extract BL numbers from the text
                        found_bls = []
                        for bl in bl_numbers:
                            if bl.upper() in bls_text.upper():
                                found_bls.append(bl)
                        
                        if found_bls:
                            # Distribute amount evenly among found BLs
                            amount_per_bl = total_amount / len(found_bls)
                            for bl in found_bls:
                                bl_payments[bl] = amount_per_bl
                            logger.debug(f"[DEBUG] Distributed payment from BL pattern: {total_amount} among {found_bls} = {amount_per_bl} each")
                            break
                    except ValueError:
                        continue
        
        return bl_payments

    # More flexible BL regex: matches various BL formats but excludes bank references
    # Excludes patterns like TEST987, REF123, RAY6330088, etc. that are common bank reference formats
    # Bank reference patterns to exclude: RAY, TEST, REF, BANK, PAY, TRANS, TXN followed by numbers
    # Also exclude EST, which is commonly found in reference numbers like TEST987
    bank_ref_patterns = ['RAY', 'TEST', 'REF', 'BANK', 'PAY', 'TRANS', 'TXN', 'EST']
    bank_ref_regex = '|'.join(bank_ref_patterns)
    expanded_bl_pattern = re.compile(r'(?:提单号[:：]?\s*)?(BL-\d{4,}|\d{3,}-\d{3,}|\d{6,}|(?!' + bank_ref_regex + r')[A-Z]{2,4}\d{2,})', re.IGNORECASE)
    logger.info(f"\033[92m[BL Processing] BL regex pattern: {expanded_bl_pattern.pattern}\033[0m")
    bls_from_pdfs = set()
    fallback_paid_amount = None
    
    logger.info(f"\033[92m[PDF Processing] Starting with {len(attachments) if attachments else 0} attachments\033[0m")
    
    if attachments:
        for att_path in attachments:
            if att_path.lower().endswith('.pdf'):
                try:
                    logger.info(f"[PDF Processing] Processing attachment: {att_path}")
                    pdf_fields = process_pdf(att_path)
                    logger.info(f"[PDF Processing] PDF fields: {pdf_fields}")
                    if pdf_fields and isinstance(pdf_fields, dict):
                        # Try structured paid_amount first
                        paid_amt_struct = pdf_fields.get('paid_amount')
                        if paid_amt_struct is not None:
                            try:
                                fallback_paid_amount = float(re.sub(r'[^0-9.]+', '', str(paid_amt_struct)))
                                logger.info(f"[PDF Processing] Parsed paid_amount from PDF: {fallback_paid_amount}")
                            except Exception as ex:
                                logger.error(f"[PDF Processing] Error parsing paid_amount from PDF: {ex}")
                        
                        # Fallback to raw_text extraction for payment amount
                        if fallback_paid_amount is None:
                            raw_text = pdf_fields.get('raw_text')
                            if raw_text:
                                amt = extract_payment_amount(raw_text)
                                if amt is not None:
                                    fallback_paid_amount = amt
                        
                        # Extract BLs from both structured field and raw text
                        bl_val = pdf_fields.get('bl_number')
                        logger.info(f"[PDF Processing] PDF bl_number field: '{bl_val}'")
                        if bl_val and isinstance(bl_val, str):
                            bls = [b.strip() for b in re.split(r'[\s,;/]+', bl_val) if b.strip()]
                            bls_from_pdfs.update(bls)
                            logger.info(f"[PDF Processing] BLs from structured field '{bl_val}': {bls}")
                            # Also run expanded regex on bl_val
                            regex_bls = expanded_bl_pattern.findall(bl_val)
                            bls_from_pdfs.update(regex_bls)
                            logger.info(f"[PDF Processing] BLs from structured field regex: {regex_bls}")
                        
                        # Always extract from raw text as fallback
                        raw_text = pdf_fields.get('raw_text')
                        logger.info(f"[PDF Processing] PDF raw_text: '{raw_text[:100]}...' if raw_text else 'None'")
                        if raw_text:
                            # Extract BLs from raw text using regex
                            raw_bls = expanded_bl_pattern.findall(raw_text)
                            bls_from_pdfs.update(raw_bls)
                            logger.info(f"[PDF Processing] BLs from raw text regex: {raw_bls}")
                            
                            # Test the regex with the actual text
                            logger.info(f"[PDF Processing] Testing regex on text: '{raw_text}'")
                            test_matches = expanded_bl_pattern.findall(raw_text)
                            logger.info(f"[PDF Processing] Regex test matches: {test_matches}")
                            
                            # Also try simple text search for common BL patterns
                            text_lower = raw_text.lower()
                            if 'b/l' in text_lower or 'bl' in text_lower:
                                # Look for patterns like "B/L 001-123, NYC220"
                                bl_matches = re.findall(r'(?:b/l\s*|bl\s*)([a-z0-9\-]+)', text_lower)
                                for match in bl_matches:
                                    if match and len(match) >= 3:  # Minimum BL length
                                        bls_from_pdfs.add(match.upper())
                                logger.info(f"[PDF Processing] BLs from text search: {bl_matches}")
                        
                            # Also try to extract BLs from the structured bl_number field if it contains multiple BLs
                            if bl_val and ',' in bl_val:
                                # Split by comma and extract individual BLs
                                bl_parts = [part.strip() for part in bl_val.split(',')]
                                for part in bl_parts:
                                    # Extract BL numbers from each part
                                    part_bls = expanded_bl_pattern.findall(part)
                                    bls_from_pdfs.update(part_bls)
                                    logger.info(f"[PDF Processing] BLs from structured field parts '{part}': {part_bls}")
                            
                except Exception as e:
                    logger.error(f"[PDF Processing] Failed for {att_path}: {e}")
    
    logger.info(f"\033[92m[PDF Processing] Final BLs from PDFs: {bls_from_pdfs}\033[0m")
    logger.info(f"\033[92m[PDF Processing] Number of BLs from PDFs: {len(bls_from_pdfs)}\033[0m")
    
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
            translated_text = openai_call_with_fallback(messages, temperature=0).strip()
            logger.info(f"[Translation] Original: {text[:50]}... -> Translated: {translated_text[:50]}...")
            return translated_text
        except Exception as e:
            logger.error(f"[OpenAI Translate] Failed: {e}")
            return text

    incoming_is_chinese = is_chinese(body)
    translated_body = body
    translation_used = False
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
    
    print(f"\033[94m[DEBUG] Text to parse: {text_to_parse}\033[0m")
    
    for text in text_to_parse:
        print(f"\033[94m[DEBUG] Analyzing text: '{text[:200]}...'\033[0m")
        for req_type, pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                print(f"\033[94m[DEBUG] Pattern '{pattern}' matched '{match.group()}' for request type '{req_type}'\033[0m")
                if req_type not in request_types:
                    request_types.append(req_type)
                    print(f"\033[94m[DEBUG] Added request type: {req_type}\033[0m")
            else:
                print(f"\033[94m[DEBUG] Pattern '{pattern}' did NOT match for request type '{req_type}'\033[0m")
    
    # Prioritize payment_receipt and payment_status over fee_inquiry
    if 'payment_receipt' in request_types or 'payment_status' in request_types:
        request_types = [rt for rt in request_types if rt not in ['fee_inquiry']] + [rt for rt in request_types if rt == 'fee_inquiry']
    
    if not request_types:
        request_types.append('general_enquiry')
    
    print(f"\033[94m[DEBUG] Final request types: {request_types}\033[0m")
    logger.info(f"\033[92m[Pre-Parsing] Request types: {request_types} | Email body: {body}\033[0m")

    # --- Extract and Merge BLs from all sources ---
    # Refined BL pattern that excludes common bank reference formats
    bl_pattern = re.compile(r'(?:提单号[:：]?\s*)?(BL-\d{4,}|\d{3,}-\d{3,}|\d{6,}|[A-Z]{2,4}\d{2,})', re.IGNORECASE)
    bls_from_body = set()
    
    print(f"\033[94m[DEBUG] BL extraction pattern: {bl_pattern.pattern}\033[0m")
    
    for text in text_to_parse:
        found_bls = bl_pattern.findall(text)
        print(f"\033[94m[DEBUG] BLs found in text '{text[:100]}...': {found_bls}\033[0m")
        logger.debug(f"[DEBUG] BLs found in body text '{text[:50]}...': {found_bls}")
        bls_from_body.update(found_bls)
    
    # Merge BLs from body, PDF, and OpenAI reply
    merged_bls = bls_from_body | bls_from_pdfs
    print(f"\033[94m[DEBUG] BLs from body: {bls_from_body}\033[0m")
    print(f"\033[94m[DEBUG] BLs from PDFs: {bls_from_pdfs}\033[0m")
    print(f"\033[94m[DEBUG] Merged BLs: {merged_bls}\033[0m")
    logger.info(f"\033[92m[BL Processing] BLs from body: {bls_from_body}, BLs from PDFs: {bls_from_pdfs}, Merged: {merged_bls}\033[0m")
    logger.info(f"\033[92m[BL Processing] Body text for BL extraction: '{body[:200]}...' if body else 'Empty'\033[0m")
    
    # Filter out common bank reference patterns
    bank_ref_patterns = ['TEST', 'REF', 'BANK', 'PAY', 'TRANS', 'TXN', 'RAY', 'EST']
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
        # Also check if BL contains bank reference patterns anywhere in the string
        if not excluded:
            for pattern in bank_ref_patterns:
                if pattern in bl_upper:
                    logger.info(f"\033[93m[BL Processing] Excluding bank reference: {bl} (contains pattern: {pattern})\033[0m")
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
        print(f"\033[94m[DEBUG] Querying database for BLs: {bl_numbers}\033[0m")
        ctn_infos = find_ctn_info(bl_numbers) or []
        invoice_infos = find_invoice_info(bl_numbers) or []
        
        print(f"\033[94m[DEBUG] CTN infos from DB: {ctn_infos}\033[0m")
        print(f"\033[94m[DEBUG] Invoice infos from DB: {invoice_infos}\033[0m")
        
        for bl in bl_numbers:
            print(f"\033[94m[DEBUG] Processing BL: {bl}\033[0m")
            ctn_info = next((info for info in ctn_infos if info.get('bl_number') == bl), {})
            invoice_info = next((info for info in invoice_infos if info.get('bl_number') == bl), {})
            
            print(f"\033[94m[DEBUG] CTN info for {bl}: {ctn_info}\033[0m")
            print(f"\033[94m[DEBUG] Invoice info for {bl}: {invoice_info}\033[0m")
            
            if ctn_info or invoice_info:
                valid_bls[bl] = {
                    'ctn': ctn_info.get('ctn_number'),
                    'invoice_link': invoice_info.get('invoice_filename'),
                    'ctn_fee': float(invoice_info.get('ctn_fee', 0)) if invoice_info.get('ctn_fee') else 0.0,
                    'service_fee': float(invoice_info.get('service_fee', 0)) if invoice_info.get('service_fee') else 0.0,
                    'paid_amount': float(invoice_info.get('paid_amount', 0)) if invoice_info.get('paid_amount') else 0.0,
                    'status': invoice_info.get('status', 'Unknown')
                }
                print(f"\033[94m[DEBUG] Added {bl} to valid_bls: {valid_bls[bl]}\033[0m")
            else:
                invalid_bls.append(bl)
                print(f"\033[94m[DEBUG] Added {bl} to invalid_bls (no CTN or invoice info)\033[0m")
    
    print(f"\033[94m[DEBUG] Final valid_bls: {valid_bls}\033[0m")
    print(f"\033[94m[DEBUG] Final invalid_bls: {invalid_bls}\033[0m")
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

    # --- OpenAI Prompt ---
    full_text = f"Subject: {subject}\n\n{translated_body}"
    attachment_info = f"\n\nThe customer has attached {len(attachments)} file(s) to this email." if attachments else ""
    
    # Build prompt sections only for detected request types
    prompt_sections = []
    print(f"\033[94m[DEBUG] Building prompt sections for request types: {request_types}\033[0m")
    print(f"\033[94m[DEBUG] Available valid_bls: {valid_bls}\033[0m")
    
    if 'invoice_request' in request_types and valid_bls:
        prompt_sections.append(f"Valid BLs: {json.dumps(valid_bls)}")
        print(f"\033[94m[DEBUG] Added invoice_request section with Valid BLs\033[0m")
    if 'ctn_request' in request_types and valid_bls:
        prompt_sections.append(f"Valid BLs: {json.dumps(valid_bls)}")
        print(f"\033[94m[DEBUG] Added ctn_request section with Valid BLs\033[0m")
    if 'fee_inquiry' in request_types and valid_bls:
        prompt_sections.append(f"Valid BLs: {json.dumps(valid_bls)}")
        print(f"\033[94m[DEBUG] Added fee_inquiry section with Valid BLs\033[0m")
    if 'payment_status' in request_types or 'payment_receipt' in request_types:
        prompt_sections.append(f"Paid amount: {paid_amount if paid_amount is not None else 'None'}")
        if valid_bls:
            prompt_sections.append(f"Valid BLs: {json.dumps(valid_bls)}")
            print(f"\033[94m[DEBUG] Added payment_status/payment_receipt section with Valid BLs\033[0m")
    if 'business_hours' in request_types:
        prompt_sections.append(f"Business hours: {BUSINESS_HOURS}")
        print(f"\033[94m[DEBUG] Added business_hours section\033[0m")
    if 'payment_methods' in request_types:
        prompt_sections.append(f"Payment methods: {', '.join(PAYMENT_METHODS)}")
        print(f"\033[94m[DEBUG] Added payment_methods section\033[0m")
    if 'ctn_process' in request_types:
        prompt_sections.append(f"CTN processing time: {CTN_PROCESSING_TIME}")
        print(f"\033[94m[DEBUG] Added ctn_process section\033[0m")
    if invalid_bls:
        prompt_sections.append(f"Invalid BLs: {json.dumps(invalid_bls)}")
        print(f"\033[94m[DEBUG] Added invalid_bls section: {invalid_bls}\033[0m")
    
    print(f"\033[94m[DEBUG] Final prompt sections: {prompt_sections}\033[0m")
    
    prompt = f"""
You are a logistics assistant for IQS Trade. Draft a reply in English for the email below.

CRITICAL REQUIREMENTS:
1. You MUST address ALL Bill of Lading (BL) numbers mentioned in the customer's email
2. For each BL number, provide complete information for ALL requested request types
3. Do NOT skip any BL numbers or request types
4. If multiple BLs are mentioned, address each one individually and completely
5. Use ONLY the provided data - do not make up information

Request types: {json.dumps(request_types)}
{chr(10).join(prompt_sections)}

Email: {full_text}{attachment_info}

Canned responses: {canned_responses_text}

Return a JSON object:
{{
  "classification": "{"combined_request" if len(request_types) > 1 else request_types[0] if request_types else "general_enquiry"}",
  "reply": "Reply addressing ALL BLs and ALL detected requests completely."
}}
"""
    print(f"\033[94m[DEBUG] Final prompt sent to OpenAI:\033[0m")
    print(f"\033[94m[DEBUG] Request types: {json.dumps(request_types)}\033[0m")
    print(f"\033[94m[DEBUG] Prompt sections: {chr(10).join(prompt_sections)}\033[0m")
    print(f"\033[94m[DEBUG] Email text: {full_text}{attachment_info}\033[0m")
    logger.debug(f"[OpenAI Email] Sending prompt to OpenAI:\n{prompt}")

    # --- OpenAI Call ---
    try:
        messages = [
            {"role": "system", "content": "You're a shipping email agent. You MUST address ALL Bill of Lading (BL) numbers mentioned in customer emails. Never skip or ignore any BL numbers. Provide complete information for each BL and each request type."},
            {"role": "user", "content": prompt}
        ]
        print(f"\033[94m[DEBUG] ===== OPENAI CALL =====\033[0m")
        print(f"\033[94m[DEBUG] System message: You're a shipping email agent. You MUST address ALL Bill of Lading (BL) numbers mentioned in customer emails. Never skip or ignore any BL numbers. Provide complete information for each BL and each request type.\033[0m")
        print(f"\033[94m[DEBUG] User message length: {len(prompt)} characters\033[0m")
        print(f"\033[94m[DEBUG] Complete prompt sent to OpenAI:\033[0m")
        print(f"\033[94m{prompt}\033[0m")
        print(f"\033[94m[DEBUG] ===== END PROMPT =====\033[0m")
        
        content = openai_call_with_fallback(messages, temperature=0)
        
        print(f"\033[94m[DEBUG] ===== OPENAI RESPONSE =====\033[0m")
        print(f"\033[94m[DEBUG] Response length: {len(content)} characters\033[0m")
        print(f"\033[94m[DEBUG] Complete response from OpenAI:\033[0m")
        print(f"\033[94m{content}\033[0m")
        print(f"\033[94m[DEBUG] ===== END RESPONSE =====\033[0m")
        
        logger.debug(f"[OpenAI Email] Received response from OpenAI:\n{content}")
        
        print(f"\033[94m[DEBUG] ===== JSON PARSING =====\033[0m")
        try:
            action = json.loads(content)
            print(f"\033[94m[DEBUG] Successfully parsed JSON: {action}\033[0m")
        except json.JSONDecodeError as e:
            print(f"\033[94m[DEBUG] JSON decode error: {e}\033[0m")
            match = re.search(r'\{.*\}', content, re.DOTALL)
            if match:
                try:
                    action = json.loads(match.group(0))
                    print(f"\033[94m[DEBUG] Successfully parsed JSON from regex match: {action}\033[0m")
                except json.JSONDecodeError as e2:
                    print(f"\033[94m[DEBUG] Failed to parse JSON from regex match: {e2}\033[0m")
                    logger.error(f"[OpenAI Email] Failed to parse JSON from response.\nPrompt: {prompt}\nResponse: {content}")
                    action = None
            else:
                print(f"\033[94m[DEBUG] No JSON pattern found in response\033[0m")
                logger.error(f"[OpenAI Email] No JSON found in response.\nPrompt: {prompt}\nResponse: {content}")
                action = None
        
        if not action or not isinstance(action, dict):
            print(f"\033[94m[DEBUG] Invalid action format, using fallback\033[0m")
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
    print(f"\033[94m[DEBUG] ===== FINAL RESULT =====\033[0m")
    classification = action.get('classification', 'general_enquiry')
    custom_reply = action.get('reply', 'We could not process your request. Please provide more details or contact us for assistance.')
    print(f"\033[94m[DEBUG] Final classification: {classification}\033[0m")
    print(f"\033[94m[DEBUG] Final reply: {custom_reply}\033[0m")
    print(f"\033[94m[DEBUG] ===== END PROCESSING =====\033[0m")
    logger.info(f"[OpenAI Email] Classification: {classification}, Reply: {custom_reply[:100]}...")

    # Validate reply includes all request types and BLs
    reply_lower = custom_reply.lower()
    missing_requests = []
    
    # Check if all BLs are mentioned in the reply
    missing_bls = []
    for bl in bl_numbers:
        if bl not in custom_reply:
            missing_bls.append(bl)
    
    for req_type in request_types:
        if req_type == 'invoice_request' and not ('invoice' in reply_lower or 'bill' in reply_lower):
            missing_requests.append(req_type)
        elif req_type == 'ctn_request' and not ('ctn' in reply_lower or 'container number' in reply_lower):
            missing_requests.append(req_type)
        elif req_type == 'fee_inquiry' and not ('fee' in reply_lower or 'cost' in reply_lower or 'charge' in reply_lower):
            missing_requests.append(req_type)
        elif req_type == 'payment_status' and not ('status' in reply_lower or 'due' in reply_lower or 'balance' in reply_lower):
            missing_requests.append(req_type)
        elif req_type == 'payment_receipt' and not ('payment' in reply_lower or 'receipt' in reply_lower or 'received' in reply_lower):
            missing_requests.append(req_type)
        elif req_type == 'business_hours' and 'hours' not in reply_lower:
            missing_requests.append(req_type)
        elif req_type == 'payment_methods' and not ('payment method' in reply_lower or 'bank transfer' in reply_lower):
            missing_requests.append(req_type)
        elif req_type == 'ctn_process' and not ('process' in reply_lower or 'time' in reply_lower):
            missing_requests.append(req_type)
    
    # Force fallback if BLs are missing
    if missing_bls:
        logger.warning(f"[OpenAI Email] Missing BLs in reply: {missing_bls}")
        missing_requests.append('missing_bls')
    
    # Force fallback if payment receipt but reply mentions "Awaiting Bank In" status
    if 'payment_receipt' in request_types and paid_amount is not None and 'awaiting bank in' in reply_lower:
        logger.warning(f"[OpenAI Email] Payment receipt with 'Awaiting Bank In' status - forcing fallback for proper acknowledgment")
        missing_requests.append('payment_receipt')
    
    if missing_requests:
        logger.warning(f"[OpenAI Email] Missing request types in reply: {missing_requests}")
        # Fallback reply generation
        reply_lines = ["Hello,"]
        for req_type in request_types:
            if req_type == 'invoice_request' and valid_bls:
                reply_lines.append("Invoice(s) found:")
                for bl, info in valid_bls.items():
                    if info['invoice_link']:
                        reply_lines.append(f"  - For BL {bl}: You can download your invoice here: {info['invoice_link']}")
                    else:
                        reply_lines.append(f"  - For BL {bl}: An invoice has not been generated yet.")
            elif req_type == 'ctn_request' and valid_bls:
                reply_lines.append("CTN(s) found:")
                for bl, info in valid_bls.items():
                    if info['ctn']:
                        reply_lines.append(f"  - For BL {bl}: The CTN number is {info['ctn']}.")
            elif req_type == 'fee_inquiry' and valid_bls:
                reply_lines.append("Fee details:")
                for bl, info in valid_bls.items():
                    ctn_fee = info.get('ctn_fee', 0.0)
                    service_fee = info.get('service_fee', 0.0)
                    total_fee = ctn_fee + service_fee
                    reply_lines.append(f"  - BL {bl}: CTN Fee: ${ctn_fee:.2f}, Service Fee: ${service_fee:.2f}, Total: ${total_fee:.2f}")
            elif req_type == 'payment_status' and valid_bls:
                reply_lines.append("Payment status:")
                for bl, info in valid_bls.items():
                    ctn_fee = info.get('ctn_fee', 0.0)
                    service_fee = info.get('service_fee', 0.0)
                    total_fee = ctn_fee + service_fee
                    paid = info.get('paid_amount', 0.0)
                    due = total_fee - paid
                    # Use actual status from database, fallback to calculated status
                    db_status = info.get('status', 'Unknown')
                    if db_status == 'Unknown' or db_status == 'Unknown':
                        status = "Paid and CTN Valid" if due <= 0 else f"Due: ${due:.2f}"
                    else:
                        status = db_status
                    reply_lines.append(f"  - BL {bl}: Total Fee: ${total_fee:.2f}, Paid: ${paid:.2f}, Status: {status}")
            elif req_type == 'payment_receipt' and valid_bls and paid_amount is not None:
                # Check for duplicate payments first
                duplicate_bls = []
                non_duplicate_bls = []
                
                for bl, info in valid_bls.items():
                    try:
                        from utils.balance_utils import check_payment_processed
                        if check_payment_processed(info.get('id'), 'email'):
                            duplicate_bls.append(bl)
                        else:
                            non_duplicate_bls.append(bl)
                    except Exception as e:
                        logger.error(f"Error checking duplicate payment for BL {bl}: {e}")
                        non_duplicate_bls.append(bl)  # Assume not duplicate if check fails
                
                if duplicate_bls:
                    reply_lines.append("⚠️ DUPLICATE PAYMENT DETECTED:")
                    for bl in duplicate_bls:
                        reply_lines.append(f"  - For BL {bl}: This payment has already been processed previously.")
                    reply_lines.append(f"\n💰 DUPLICATE PAYMENT: We detected that your payment of ${paid_amount:.2f} for BL(s) {', '.join(duplicate_bls)} has already been processed. No action is required from you.")
                    logger.warning(f"\033[93m[Payment Check] Duplicate payment detected for BLs: {duplicate_bls}\033[0m")
                
                # Only process non-duplicate BLs for payment analysis
                if non_duplicate_bls:
                    reply_lines.append("Payment(s) found:")
                    for bl in non_duplicate_bls:
                        reply_lines.append(f"  - For BL {bl}: Payment record found.")
                    
                    # Check for underpayment/overpayment only for non-duplicate BLs
                    non_duplicate_info = {bl: valid_bls[bl] for bl in non_duplicate_bls}
                    total_invoice = sum(info.get('ctn_fee', 0.0) + info.get('service_fee', 0.0) for info in non_duplicate_info.values())
                    logger.info(f"\033[92m[Payment Check] Total invoice: ${total_invoice:.2f}, Paid amount: ${paid_amount:.2f}\033[0m")
                    
                    if paid_amount < total_invoice - 0.01:
                        diff = total_invoice - paid_amount
                        reply_lines.append(f"\n⚠️ UNDERPAYMENT: We have received your payment of ${paid_amount:.2f}, but the invoice amount is ${total_invoice:.2f}. There is an outstanding balance of ${diff:.2f}.")
                        logger.warning(f"\033[93m[Payment Check] Underpayment detected: ${diff:.2f}\033[0m")
                    elif paid_amount > total_invoice + 0.01:
                        diff = paid_amount - total_invoice
                        reply_lines.append(f"\n💰 OVERPAYMENT: We have received your payment of ${paid_amount:.2f}, but the invoice amount is ${total_invoice:.2f}. We will contact you regarding the excess payment of ${diff:.2f}.")
                        logger.info(f"\033[92m[Payment Check] Overpayment detected: ${diff:.2f}\033[0m")
                    else:
                        reply_lines.append(f"\n✅ PAYMENT MATCH: Your payment of ${paid_amount:.2f} matches the invoice amount of ${total_invoice:.2f}.")
                        logger.info(f"\033[92m[Payment Check] Payment matches invoice amount\033[0m")
            elif req_type == 'business_hours':
                reply_lines.append(f"Our business hours are: {BUSINESS_HOURS}")
            elif req_type == 'payment_methods':
                reply_lines.append("We accept the following payment methods:")
                for method in PAYMENT_METHODS:
                    reply_lines.append(f"  - {method}")
                reply_lines.append("Please choose the one that is most convenient for you. Instructions are provided when you generate a payment link.")
            elif req_type == 'ctn_process':
                reply_lines.append(f"The processing time for a Cargo Tracking Note (CTN) is {CTN_PROCESSING_TIME}.")
        
        if invalid_bls:
            reply_lines.append("\nThe following BL numbers could not be found in our system: " + ", ".join(invalid_bls) + ". Please double-check or contact us for assistance.")
        
        if reply_lines != ["Hello,"]:
            custom_reply = "\n".join(reply_lines)
        else:
            custom_reply = "Hello,\n\nWe could not process your request. Please provide more details or contact us for assistance."

    # --- Post-Processing: Add Missing BL Information ---
    print(f"\033[94m[DEBUG] ===== POST-PROCESSING =====\033[0m")
    if missing_bls and valid_bls:
        print(f"\033[94m[DEBUG] Missing BLs detected: {missing_bls}\033[0m")
        print(f"\033[94m[DEBUG] Valid BLs available: {list(valid_bls.keys())}\033[0m")
        
        # Only add information for BLs that are both missing AND valid
        bls_to_add = [bl for bl in missing_bls if bl in valid_bls]
        
        if bls_to_add:
            print(f"\033[94m[DEBUG] Adding missing BL information for: {bls_to_add}\033[0m")
            
            # Add missing BL information to the reply
            missing_bl_info = []
            for bl in bls_to_add:
                bl_data = valid_bls[bl]
                bl_info_lines = [f"\n{bl}:"]
                
                # Add information based on request types
                for req_type in request_types:
                    if req_type == 'ctn_request' and bl_data.get('ctn'):
                        bl_info_lines.append(f"  - CTN Number: {bl_data['ctn']}")
                    if req_type == 'invoice_request' and bl_data.get('invoice_link'):
                        bl_info_lines.append(f"  - Invoice: {bl_data['invoice_link']}")
                    if req_type == 'fee_inquiry':
                        ctn_fee = bl_data.get('ctn_fee', 0.0)
                        service_fee = bl_data.get('service_fee', 0.0)
                        total_fee = ctn_fee + service_fee
                        bl_info_lines.append(f"  - CTN Fee: ${ctn_fee:.2f}, Service Fee: ${service_fee:.2f}, Total: ${total_fee:.2f}")
                    if req_type == 'payment_status':
                        ctn_fee = bl_data.get('ctn_fee', 0.0)
                        service_fee = bl_data.get('service_fee', 0.0)
                        total_fee = ctn_fee + service_fee
                        paid = bl_data.get('paid_amount', 0.0)
                        due = total_fee - paid
                        db_status = bl_data.get('status', 'Unknown')
                        if db_status == 'Unknown':
                            status = "Paid and CTN Valid" if due <= 0 else f"Due: ${due:.2f}"
                        else:
                            status = db_status
                        bl_info_lines.append(f"  - Total Fee: ${total_fee:.2f}, Paid: ${paid:.2f}, Status: {status}")
                
                missing_bl_info.append(" ".join(bl_info_lines))
            
            if missing_bl_info:
                custom_reply += "\n\n" + "\n".join(missing_bl_info)
                print(f"\033[94m[DEBUG] Added missing BL information to reply\033[0m")
                logger.info(f"[Post-Processing] Added missing BL information for: {bls_to_add}")
        else:
            print(f"\033[94m[DEBUG] No valid BLs to add (missing BLs are invalid)\033[0m")
    else:
        print(f"\033[94m[DEBUG] No missing BLs or no valid BLs available\033[0m")
    print(f"\033[94m[DEBUG] ===== END POST-PROCESSING =====\033[0m")

    # --- Translate Reply for Chinese Emails ---
    reply_is_chinese = False
    if translation_used:
        custom_reply = openai_translate(custom_reply, 'English', 'Chinese')
        reply_is_chinese = True
    else:
        reply_is_chinese = is_chinese(custom_reply)

    # --- Add Payment Summary for Payment Receipts ---
    if 'payment_receipt' in request_types and valid_bls and paid_amount is not None:
        # Check for duplicate payments first
        duplicate_bls = []
        non_duplicate_bls = []
        
        for bl, info in valid_bls.items():
            try:
                from utils.balance_utils import check_payment_processed
                if check_payment_processed(info.get('id'), 'email'):
                    duplicate_bls.append(bl)
                else:
                    non_duplicate_bls.append(bl)
            except Exception as e:
                logger.error(f"Error checking duplicate payment for BL {bl}: {e}")
                non_duplicate_bls.append(bl)
        
        # Only add summary if it's not already in the reply and no duplicate payments
        if ('underpayment' not in custom_reply.lower() and 'overpayment' not in custom_reply.lower() and 
            'payment match' not in custom_reply.lower() and 'duplicate payment' not in custom_reply.lower()):
            
            if duplicate_bls:
                # Don't add payment summary for duplicate payments
                pass
            elif non_duplicate_bls:
                # Only calculate for non-duplicate BLs
                non_duplicate_info = {bl: valid_bls[bl] for bl in non_duplicate_bls}
                total_invoice = sum(info.get('ctn_fee', 0.0) + info.get('service_fee', 0.0) for info in non_duplicate_info.values())
                
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

    # --- Finalize Reply ---
    custom_reply = custom_reply.strip()
    if reply_is_chinese:
        custom_reply += '\n\n祝商祺！\nIQS Trade Team'
    else:
        custom_reply += '\n\nBest regards,\nIQS Trade Team'

    # Remove attachment references if none exist
    if not attachments:
        custom_reply = re.sub(r'^.*\b(attach|attachment|attached|attachments)\b.*$', '', custom_reply, flags=re.MULTILINE | re.IGNORECASE)
        custom_reply = re.sub(r'^.*(已?附上|附件|请查收附件|请见附件|请参见附件|请参考附件|请见附档|请查收附档|请见附加文件|请查收附加文件|附件见下|请查附件|请见下方附件|请见随信附件).*$', '', custom_reply, flags=re.MULTILINE)
        custom_reply = '\n'.join([line for line in custom_reply.splitlines() if line.strip()])
        if missing_attachment_flag:
            custom_reply += ("\n\nNote: You mentioned an attachment in your email, but no files were attached. "
                             "If you intended to send a file, please resend your email with the attachment included."
                             "\n\n注意：您在邮件中提到有附件，但未检测到任何文件。如需补发，请重新发送带附件的邮件。")

    # --- Confidence Scoring ---
    confidence_result = confidence_scorer.get_auto_send_recommendation(
        full_text, custom_reply, classification, bl_numbers
    )
    confidence_score = confidence_result['confidence_score']
    auto_send = confidence_result['auto_send']
    logger.info(f"[OpenAI Email] Confidence score: {confidence_score}, Auto-send: {auto_send}")

    # --- Log BLs and Missing Attachments ---
    logger.info(f"[OpenAI Email] BLs found: {list(valid_bls.keys())}, BLs missing: {invalid_bls}")
    if missing_attachment_flag:
        logger.info(f"[OpenAI Email] Missing attachment detected for email from {from_addr} (subject: {subject})")

    # --- Save Draft ---
    save_draft_reply(from_addr, subject, custom_reply, confidence_result)
    logger.info(f"[OpenAI Email] Final customized reply saved for email from {from_addr}")

    # --- Build BL-to-paid_amount mapping ---
    bl_payment_map = {}
    
    # First try to extract BL-specific payments
    valid_bl_numbers = list(valid_bls.keys())  # Only use valid BLs for payment processing
    bl_specific_payments = extract_bl_specific_payments(body, valid_bl_numbers)
    logger.info(f"\033[92m[Payment Mapping] BL-specific payments: {bl_specific_payments}\033[0m")
    
    # If no BL-specific payments found but we have multiple valid BLs and a total paid amount, distribute proportionally
    if not bl_specific_payments and len(valid_bl_numbers) > 1 and paid_amount is not None:
        # Get invoice amounts for valid BLs to calculate proportional distribution
        total_invoice_amount = 0
        bl_invoice_amounts = {}
        
        for bl in valid_bl_numbers:
            if bl in valid_bls:
                ctn_fee = float(valid_bls[bl].get('ctn_fee', 0) or 0)
                service_fee = float(valid_bls[bl].get('service_fee', 0) or 0)
                balance_applied = float(valid_bls[bl].get('balance_applied', 0) or 0)
                invoice_amount = (ctn_fee + service_fee) - balance_applied
                bl_invoice_amounts[bl] = invoice_amount
                total_invoice_amount += invoice_amount
        
        # Only distribute if we have valid BLs with invoice amounts
        if total_invoice_amount > 0:
            for bl in valid_bl_numbers:
                if bl in bl_invoice_amounts:
                    # Calculate proportional amount based on invoice amount
                    proportional_amount = (paid_amount * bl_invoice_amounts[bl]) / total_invoice_amount
                    bl_specific_payments[bl] = proportional_amount
            logger.info(f"\033[92m[Payment Mapping] Distributed total amount {paid_amount} proportionally among valid BLs {valid_bl_numbers} based on invoice amounts\033[0m")
        else:
            # Fallback to even distribution if no valid invoice amounts
            amount_per_bl = paid_amount / len(valid_bl_numbers)
            for bl in valid_bl_numbers:
                bl_specific_payments[bl] = amount_per_bl
            logger.info(f"\033[92m[Payment Mapping] Fallback: distributed total amount {paid_amount} evenly among valid BLs {valid_bl_numbers} = {amount_per_bl} each\033[0m")
    
    # Only process valid BLs for payment mapping
    for bl in valid_bl_numbers:
        if bl in valid_bls and valid_bls[bl].get('paid_amount', 0) > 0:
            bl_payment_map[bl] = valid_bls[bl]['paid_amount']
            logger.info(f"\033[92m[Payment Mapping] Using DB paid_amount for {bl}: {valid_bls[bl]['paid_amount']}\033[0m")
        elif bl in bl_specific_payments:
            bl_payment_map[bl] = bl_specific_payments[bl]
            logger.info(f"\033[92m[Payment Mapping] Using extracted payment for {bl}: {bl_specific_payments[bl]}\033[0m")
        elif paid_amount is not None:
            bl_payment_map[bl] = paid_amount
            logger.info(f"\033[92m[Payment Mapping] Using total paid_amount for {bl}: {paid_amount}\033[0m")
    
    # If no valid BLs but paid_amount exists, create a dummy mapping
    if not bl_payment_map and paid_amount is not None:
        bl_payment_map['UNKNOWN'] = paid_amount
        logger.info(f"\033[92m[Payment Mapping] Created dummy mapping for UNKNOWN: {paid_amount}\033[0m")
    
    logger.info(f"\033[92m[Payment Mapping] Final BL payment map (valid BLs only): {bl_payment_map}\033[0m")

    return {
        'classification': classification,
        'reply': custom_reply,
        'bl_numbers': bl_numbers,
        'paid_amount': paid_amount,
        'bl_payment_map': bl_payment_map,
        'confidence_score': confidence_score,
        'auto_send': auto_send,
        "request_types": request_types,
    }

def extract_contact_info(text):
    """Extract phone and email from text."""
    phone_pattern = r'(\+?\d{1,3}[-\s]?\d{3,}[-\s]?\d{3,})'
    email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
    phone = re.search(phone_pattern, text)
    email_addr = re.search(email_pattern, text)
    return {
        'phone': phone.group(1) if phone else None,
        'email': email_addr.group(1) if email_addr else None
    }

def save_draft_reply(to_addr, subject, reply, confidence_result=None):
    """
    Save a draft reply to the customer_email_replies table.
    Now includes confidence scoring information.
    """
    logger.info(f"[Draft Reply] To: {to_addr}, Subject: {subject}, Reply: {reply}")
    
    # Always save AI-generated replies as drafts - let users review and send manually
    is_draft = True
    if confidence_result and confidence_result['auto_send']:
        logger.info(f"[Auto-Send] High confidence ({confidence_result['confidence_score']:.2f}) - but keeping as draft for manual review")
    
    conn = get_db_conn()
    cur = conn.cursor()
    
    cur.execute("SELECT id FROM customer_emails WHERE sender = %s AND subject = %s ORDER BY created_at DESC LIMIT 1", (to_addr, subject))
    row = cur.fetchone()
    if row:
        customer_email_id = row[0]
    else:
        cur.execute("INSERT INTO customer_emails (sender, subject, body, created_at, cc, bcc, reply_to) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id", (to_addr, subject, '', get_hk_now(), [], [], []))
        customer_email_id = cur.fetchone()[0]
        conn.commit()
    
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
            get_hk_now(), 
            is_draft,
            confidence_score,
            confidence_reasoning,
            confidence_result['auto_send'] if confidence_result else False
        ))
        conn.commit()
        logger.info(f"[Draft Reply] Saved to DB for customer_email_id={customer_email_id} ({'DRAFT' if is_draft else 'AUTO-SEND'})")
    except Exception as e:
        logger.error(f"[Draft Reply] Failed to save draft: {e}")
        try:
            cur.execute("""
                INSERT INTO customer_email_replies (customer_email_id, sender, body, created_at, is_draft)
                VALUES (%s, %s, %s, %s, %s)
            """, (customer_email_id, 'openai_draft', reply, get_hk_now(), is_draft))
            conn.commit()
            logger.info(f"[Draft Reply] Saved with basic columns for customer_email_id={customer_email_id}")
        except Exception as e2:
            logger.error(f"[Draft Reply] Failed to save even with basic columns: {e2}")
    
    cur.close()
    conn.close()

def process_inbox(user_id=None):
    """Process unread emails from inbox - compatible with original ingest_emails function"""
    
    # Try to acquire processing lock
    if not acquire_db_processing_lock(user_id, timeout_seconds=30):
        logger.warning("Email processing already in progress, skipping this request")
        return []
    
    try:
        logger.info("Connecting to IMAP server...")
        mail = connect_imap()
        if not mail:
            logger.error("IMAP connection failed, aborting ingestion")
            return []
        
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select('inbox')
        
        # Process only unread emails to avoid reprocessing
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
                
                logger.info(f"[Email Processing] CC: {cc_emails}")
                logger.info(f"[Email Processing] BCC: {bcc_emails}")
                logger.info(f"[Email Processing] Reply-To: {reply_to_emails}")
                
                body = ""
                attachments = []
                attachment_urls = []  # Store Cloudinary URLs for frontend display
                
                # Ensure PDF_SAVE_DIR exists
                os.makedirs(PDF_SAVE_DIR, exist_ok=True)
                
                logger.info(f"[Email Processing] Processing email: {subject}")
                logger.info(f"[Email Processing] From: {from_addr}")
                
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
                        # Decode filename if needed
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
                            
                            # Upload to Cloudinary for frontend display
                            try:
                                cloudinary_url = upload_filepath_to_cloudinary(filepath, folder="email_attachments")
                                attachment_urls.append(cloudinary_url)
                                logger.info(f"📎 Uploaded to Cloudinary: {cloudinary_url}")
                            except Exception as e:
                                logger.error(f"❌ Failed to upload to Cloudinary: {e}")
                                # Fallback to local file path
                                attachment_urls.append(filepath)
                                
                        except Exception as e:
                            logger.error(f"❌ Failed to save attachment {filename}: {e}")
                
                logger.info(f"[Email Processing] Final attachments: {attachment_urls}")
                logger.info(f"[Email Processing] Body length: {len(body)}")
                
                # --- Prevent Duplicate Emails using Message-ID ---
                try:
                    # Store attachment_urls as JSONB array
                    attachment_json = json.dumps(attachment_urls) if attachment_urls else None
                    
                    # First, try to insert new email with CC, BCC, Reply-To
                    cursor.execute(
                        """
                        INSERT INTO customer_emails (sender, subject, body, created_at, processed_for_payments, message_id, attachments, bl_numbers, cc, bcc, reply_to) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (message_id) DO NOTHING
                        RETURNING id;
                        """,
                        (from_addr, subject, body, get_hk_now(), False, message_id, attachment_json, [], cc_emails, bcc_emails, reply_to_emails)
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        # New email inserted successfully
                        email_id = result[0]
                        logger.info(f"✅ New email inserted with ID: {email_id}")
                    else:
                        # Duplicate detected - update existing email with attachments if it has none
                        logger.info(f"🔄 Duplicate email detected with Message-ID: {message_id}")
                        
                        # Get existing email
                        cursor.execute(
                            "SELECT id, attachments FROM customer_emails WHERE message_id = %s",
                            (message_id,)
                        )
                        existing_email = cursor.fetchone()
                        
                        if existing_email:
                            existing_id, existing_attachments = existing_email
                            
                            # If existing email has no attachments but we have new ones, update it
                            if (not existing_attachments or existing_attachments == '[]' or existing_attachments == 'null') and attachment_urls:
                                cursor.execute(
                                    "UPDATE customer_emails SET attachments = %s::jsonb WHERE id = %s",
                                    (attachment_json, existing_id)
                                )
                                logger.info(f"✅ Updated existing email {existing_id} with new attachments")
                                email_id = existing_id
                            else:
                                logger.info(f"⏭️ Skipping duplicate email {existing_id} (already has attachments)")
                                continue
                        else:
                            logger.error(f"❌ Duplicate detected but existing email not found for Message-ID: {message_id}")
                            continue
                    
                    conn.commit()
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Failed to insert email {message_id}: {e}")
                    continue
                
                # === OpenAI classification and routing ===
                action = handle_email_via_openai(subject, body, attachments, from_addr)
                
                classification = action.get('classification')
                bl_payment_map = action.get('bl_payment_map', {})
                request_types = action.get("request_types", [])
                reply_text = action.get('reply', '')
                bl_numbers = action.get('bl_numbers', [])
                
                # === Check for duplicate payments AFTER AI processing ===
                duplicate_payment_detected = False
                duplicate_bls = []
                
                if bl_numbers and bl_payment_map:
                    # Check each BL for duplicate payments
                    for bl in bl_numbers:
                        cursor.execute("SELECT id FROM bill_of_lading WHERE bl_number = %s", (bl,))
                        bl_result = cursor.fetchone()
                        if bl_result:
                            bl_id = bl_result[0]
                            from utils.balance_utils import check_payment_processed
                            if check_payment_processed(bl_id, 'email'):
                                duplicate_bls.append(bl)
                                duplicate_payment_detected = True
                                logger.warning(f"Duplicate payment detected for BL {bl}")
                    
                    # If duplicates detected, override the AI reply
                    if duplicate_payment_detected:
                        duplicate_reply = generate_duplicate_payment_reply(duplicate_bls, bl_payment_map)
                        action['reply'] = duplicate_reply
                        action['duplicate_payment'] = True
                        reply_text = duplicate_reply
                        logger.info("Generated duplicate payment reply instead of AI reply")
                
                # Validate and filter BL numbers before saving
                if bl_numbers:
                    # Get valid BL numbers from database
                    valid_bls = []
                    invalid_bls = []
                    
                    for bl in bl_numbers:
                        cursor.execute("SELECT id FROM bill_of_lading WHERE bl_number = %s", (bl,))
                        if cursor.fetchone():
                            valid_bls.append(bl)
                        else:
                            invalid_bls.append(bl)
                    
                    # Only save valid BL numbers
                    if valid_bls:
                        cursor.execute(
                            "UPDATE customer_emails SET bl_numbers = %s WHERE id = %s",
                            (valid_bls, email_id)
                        )
                        conn.commit()
                        logger.info(f"✅ Updated email {email_id} with valid BL numbers: {valid_bls}")
                        if invalid_bls:
                            logger.info(f"⚠️ Filtered out invalid BL numbers: {invalid_bls}")
                    else:
                        logger.info(f"⚠️ No valid BL numbers found for email {email_id}. Invalid BLs: {invalid_bls}")
                
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
                
                if is_actual_payment and not action.get('duplicate_payment', False):
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
                elif action.get('duplicate_payment', False):
                    logger.info("[ROUTING] Duplicate payment detected — skipping payment processing, sending notifications only.")
                    # Send duplicate payment notifications without processing
                    for bl in duplicate_bls:
                        cursor.execute("SELECT id FROM bill_of_lading WHERE bl_number = %s", (bl,))
                        bl_result = cursor.fetchone()
                        if bl_result:
                            bl_id = bl_result[0]
                            cursor.execute("SELECT customer_email, customer_username FROM bill_of_lading WHERE id = %s", (bl_id,))
                            customer_result = cursor.fetchone()
                            if customer_result:
                                customer_email, customer_username = customer_result
                                payment_amount = bl_payment_map.get(bl, 0)
                                
                                # Get original payment date
                                cursor.execute("""
                                    SELECT created_at FROM customer_balance_transactions 
                                    WHERE reference_id = %s AND payment_source = 'email' 
                                    ORDER BY created_at DESC LIMIT 1
                                """, (bl_id,))
                                original_payment = cursor.fetchone()
                                original_payment_date = original_payment[0] if original_payment else None
                                
                                send_duplicate_payment_notifications(
                                    bl_id=bl_id,
                                    bl_number=bl,
                                    customer_username=customer_username,
                                    customer_email=customer_email,
                                    payment_amount=payment_amount,
                                    payment_source='email',
                                    original_payment_date=original_payment_date
                                )
                    
                    # Save the duplicate payment reply
                    save_draft_reply(from_addr, subject, reply_text, {'confidence_score': 1.0, 'auto_send': True})
                
                # Mark email as read
                mail.store(num, '+FLAGS', '\\Seen')
                logger.info(f"Marked email as read: {subject}")
                
                # Send FCM notification with duplicate prevention
                send_fcm_notification_for_new_email(email_id, subject, from_addr)
                
                results.append({"email_id": email_id, "classification": classification})
                
            except Exception as e:
                logger.error(f"Failed to process email {num}: {e}")
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
        release_db_processing_lock(user_id)

def ingest_emails():
    """Alias for process_inbox to maintain compatibility with original code"""
    return process_inbox()

def process_existing_email_without_reply(email_id):
    """Manually process an existing email that doesn't have a reply"""
    try:
        logger.info(f"[Manual Processing] Processing email ID {email_id} without reply")
        
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Get email details
        cursor.execute("""
            SELECT sender, subject, body, created_at 
            FROM customer_emails 
            WHERE id = %s
        """, (email_id,))
        
        email_data = cursor.fetchone()
        if not email_data:
            logger.error(f"[Manual Processing] Email ID {email_id} not found")
            return False
            
        sender, subject, body, created_at = email_data
        
        # Check if reply already exists
        cursor.execute("""
            SELECT COUNT(*) 
            FROM customer_email_replies 
            WHERE customer_email_id = %s
        """, (email_id,))
        
        reply_count = cursor.fetchone()[0]
        if reply_count > 0:
            logger.info(f"[Manual Processing] Email ID {email_id} already has {reply_count} replies")
            return True
        
        # Process the email
        logger.info(f"[Manual Processing] Processing email: {subject} from {sender}")
        result = handle_email_via_openai(subject, body, [], sender)
        
        logger.info(f"[Manual Processing] Email ID {email_id} processed successfully")
        return True
        
    except Exception as e:
        logger.error(f"[Manual Processing] Error processing email ID {email_id}: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

def process_all_emails_without_replies():
    """Process all emails that don't have replies"""
    try:
        logger.info("[Manual Processing] Finding emails without replies...")
        
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Find emails without replies
        cursor.execute("""
            SELECT ce.id, ce.sender, ce.subject, ce.body
            FROM customer_emails ce
            LEFT JOIN customer_email_replies cer ON ce.id = cer.customer_email_id
            WHERE cer.id IS NULL
            ORDER BY ce.created_at DESC
        """)
        
        emails_without_replies = cursor.fetchall()
        logger.info(f"[Manual Processing] Found {len(emails_without_replies)} emails without replies")
        
        processed_count = 0
        for email_id, sender, subject, body in emails_without_replies:
            try:
                logger.info(f"[Manual Processing] Processing email ID {email_id}: {subject}")
                result = handle_email_via_openai(subject, body, [], sender)
                processed_count += 1
                logger.info(f"[Manual Processing] Successfully processed email ID {email_id}")
            except Exception as e:
                logger.error(f"[Manual Processing] Failed to process email ID {email_id}: {e}")
        
        logger.info(f"[Manual Processing] Completed processing {processed_count}/{len(emails_without_replies)} emails")
        return processed_count
        
    except Exception as e:
        logger.error(f"[Manual Processing] Error in batch processing: {e}")
        return 0
    finally:
        if 'conn' in locals():
            conn.close()

def send_fcm_notification_for_new_email(email_id, subject, from_addr):
    """Send FCM notification for new email with duplicate prevention"""
    try:
        # Check if notification was already sent for this email
        conn = get_db_conn()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM fcm_notifications 
            WHERE email_id = %s AND notification_type = 'new_email'
        """, (email_id,))
        
        notification_count = cursor.fetchone()[0]
        
        if notification_count > 0:
            logger.info(f"FCM notification already sent for email {email_id}, skipping")
            cursor.close()
            conn.close()
            return True
        
        # Send the notification
        from fcm_service_fallback import fcm_service_fallback
        
        # Get all FCM tokens for notifications
        cursor.execute('SELECT token FROM fcm_tokens WHERE is_active = TRUE')
        tokens = [row[0] for row in cursor.fetchall()]
        
        if tokens:
            notification_data = {
                'type': 'new_email',
                'email_id': str(email_id),
                'timestamp': datetime.datetime.now().isoformat()
            }
            
            result = fcm_service_fallback.send_notification(
                tokens=tokens,
                title="📧 You have new email",
                body="New customer email received",
                data=notification_data
            )
            
            if result.get('success'):
                success = True
                logger.info(f"✅ FCM notification sent for new email: {subject} from {from_addr}")
            else:
                success = False
                logger.error(f"❌ FCM notification failed: {result.get('error', 'Unknown error')}")
        else:
            success = False
            logger.info("ℹ️ No FCM tokens found for new email notifications")
        
        if success:
            # Record that notification was sent
            cursor.execute("""
                INSERT INTO fcm_notifications (email_id, notification_type, sent_at)
                VALUES (%s, %s, %s)
            """, (email_id, 'new_email', datetime.datetime.now()))
            conn.commit()
            logger.info(f"✅ FCM notification sent for new email: {subject} from {from_addr}")
        else:
            logger.error(f"❌ Failed to send FCM notification for new email: {subject}")
        
        cursor.close()
        conn.close()
        return success
        
    except Exception as e:
        logger.error(f"❌ Failed to send FCM notification for new email: {e}")
        return False

if __name__ == "__main__":
    process_inbox()
