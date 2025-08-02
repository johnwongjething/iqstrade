import os
import imaplib
import email
from email.header import decode_header
import tempfile
import fitz  # PyMuPDF
# import openai
import requests
import re
import logging
from PIL import Image
from google.cloud import vision
from config import get_db_conn
from cloudinary_utils import upload_filepath_to_cloudinary
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import datetime
from datetime import timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import pytz
from email_ingestor import handle_email_via_openai, save_draft_reply
from reportlab.lib.utils import simpleSplit
from invoice_utils import generate_pdf_from_text
from email_validation_production import validate_email_with_openai
import json

logger = logging.getLogger(__name__)

bp_ingest = Blueprint("bp_ingest", __name__)

# ...rest of your code...


def debug(msg):
    pass  # Debug logging disabled

def warn(msg):
    print(f"[WARNING] {msg}")

def get_env(var, default=None):
    val = os.environ.get(var, default)
    if val is None:
        raise Exception(f"Missing env var: {var}")
    return val

# Connect to IMAP (Gmail or Yahoo)
def connect_imap():
    host = get_env('EMAIL_HOST', 'imap.mail.yahoo.com')
    port = int(get_env('EMAIL_PORT', '993'))
    user = get_env('EMAIL_USERNAME')
    password = get_env('EMAIL_PASSWORD')
    debug(f"Connecting to IMAP: {user}@{host} on port {port}")
    try:
        mail = imaplib.IMAP4_SSL(host, port)
        mail.login(user, password)
        debug("Logged in successfully")
        return mail
    except Exception as e:
        warn(f"IMAP connection/login failed: {e}")
        return None

# Fetch unread emails
def fetch_unread_emails(mail):
    mail.select('inbox')
    status, messages = mail.search(None, '(UNSEEN)')
    email_ids = messages[0].split()
    debug(f"Fetched {len(email_ids)} new emails")
    return email_ids

# Download attachments and body
def parse_email(mail, email_id):
    status, msg_data = mail.fetch(email_id, '(RFC822)')
    msg = email.message_from_bytes(msg_data[0][1])
    
    # Extract Message-ID
    message_id = msg.get('Message-ID')
    
    # Extract actual email date
    date_header = msg.get('Date')
    if date_header:
        try:
            from email.utils import parsedate_to_datetime
            from datetime import timezone
            email_date = parsedate_to_datetime(date_header)
            # Ensure timezone awareness
            if email_date.tzinfo is None:
                email_date = email_date.replace(tzinfo=timezone.utc)
            debug(f"Extracted email date: {email_date}")
        except Exception as e:
            debug(f"Warning: Could not parse date '{date_header}': {e}")
            email_date = datetime.datetime.now()
    else:
        email_date = datetime.datetime.now()
        debug("No date header found, using current time")

    body_text = ""
    attachments = []
    for part in msg.walk():
        content_type = part.get_content_type()
        filename = part.get_filename()
        if filename:
            decoded = decode_header(filename)[0][0]
            if isinstance(decoded, bytes):
                filename = decoded.decode()
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
                tmp.write(part.get_payload(decode=True))
                attachments.append(tmp.name)
                debug(f"Processing attachment: {filename}")
        elif content_type == "text/plain":
            charset = part.get_content_charset() or 'utf-8'
            body_text += part.get_payload(decode=True).decode(charset, errors='ignore')
            debug("Email body text detected")
    # Mark email as read
    mail.store(email_id, '+FLAGS', '\\Seen')
    return body_text, attachments, message_id, email_date

# Detect type and extract text
def extract_text_from_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.pdf':
        with fitz.open(filepath) as doc:
            text = ""
            for page in doc:
                page_text = page.get_text()
                if page_text.strip():
                    text += page_text
            if text.strip():
                debug("Attachment type: PDF (text-based)")
                return text
            else:
                debug("Attachment type: PDF (image-based)")
                images = []
                for page in doc:
                    for img in page.get_images(full=True):
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)
                        if pix.n < 5:
                            img_path = tempfile.mktemp(suffix='.png')
                            pix.save(img_path)
                            images.append(img_path)
                            pix = None
                ocr_text = ""
                client = vision.ImageAnnotatorClient()
                for img_path in images:
                    with open(img_path, "rb") as image_file:
                        content = image_file.read()
                    image = vision.Image(content=content)
                    response = client.text_detection(image=image)
                    if response.text_annotations:
                        ocr_text += response.text_annotations[0].description
                    os.remove(img_path)
                return ocr_text
    elif ext in ['.jpg', '.jpeg', '.png']:
        debug("Attachment type: Image")
        client = vision.ImageAnnotatorClient()
        with open(filepath, "rb") as image_file:
            content = image_file.read()
        image = vision.Image(content=content)
        response = client.text_detection(image=image)
        if response.text_annotations:
            return response.text_annotations[0].description
        return ""
    else:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

# Placeholder for payment parsing
def extract_payment_data(all_text):
    amount_match = re.search(r'\$([0-9]+(?:\.[0-9]{1,2})?)', all_text)
    amount = float(amount_match.group(1)) if amount_match else 0.0
    ref_match = re.search(r'Ref[:\s]*([A-Za-z0-9]+)', all_text)
    reference_number = ref_match.group(1) if ref_match else ''

    bl_numbers = set()

    # Flexible B/L number detection (like extract_fields)
    # Match patterns like NYC22062889
    bl_numbers.update(re.findall(r'\b[A-Z]{3}\d{6,}\b', all_text))

    # Also pick up simpler BL12345 style
    bl_numbers.update(re.findall(r'\bBL[ -]?[0-9]{4,}\b', all_text, re.IGNORECASE))

    # "B/L No: 123456" or "Bill of Lading: 123456"
    bl_numbers.update(re.findall(r'\b(?:B\/L|Bill of Lading)[^\d]{0,10}(\d{4,})', all_text, re.IGNORECASE))

    bl_numbers = list(bl_numbers)

    parsed = {
        'amount': amount,
        'reference_number': reference_number,
        'bl_numbers': bl_numbers
    }
    debug(f"Parsed fields (placeholder): {parsed}")
    return parsed

# Match to DB
def match_payment_to_bls(payment_data):
    conn = get_db_conn()
    cursor = conn.cursor()
    bls = payment_data.get('bl_numbers', [])
    amount = float(payment_data.get('amount', 0))
    matched = []
    total_invoice = 0
    for bl in bls:
        cursor.execute("SELECT id, ctn_fee, service_fee, status FROM bill_of_lading WHERE bl_number = %s", (bl,))
        row = cursor.fetchone()
        if row:
            matched.append(row)
            ctn_fee = float(row[1]) if row[1] else 0
            service_fee = float(row[2]) if row[2] else 0
            total_invoice += ctn_fee + service_fee
            debug(f"Matched BL number: {bl} | ctn_fee: {ctn_fee} | service_fee: {service_fee}")
    tolerance = 2.0
    if abs(total_invoice - amount) <= tolerance and matched:
        debug(f"Receipt matches payment for BLs: {bls}")
        return matched, True
    else:
        warn(f"Payment amount mismatch for BLs: {bls}\nExpected: {total_invoice}, Received: {amount}")
        return matched, False

def process_payment_receipt_email(email_id, from_addr, subject, body_text, attachments, bl_payment_map, conn=None):
    """
    Centralized logic to process a payment receipt email using BL-to-amount mapping.
    - Uses a provided dict of BL numbers to paid amounts.
    - Uploads receipt (if any) to Cloudinary.
    - Updates the corresponding bill in bill_of_lading.
    - Mark the email as processed_for_payments = TRUE.
    - Compares paid amount to invoice amount for each BL before updating.
    """
    import re
    from cloudinary_utils import upload_filepath_to_cloudinary
    import tempfile
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import simpleSplit

    close_conn = False
    if conn is None:
        conn = get_db_conn()
        close_conn = True
    cursor = conn.cursor()

    if not bl_payment_map or not isinstance(bl_payment_map, dict):
        print(f"[WARN] No BL payment map provided for email {email_id}. Marking as processed.")
        cursor.execute("UPDATE customer_emails SET processed_for_payments=TRUE WHERE id=%s", (email_id,))
        conn.commit()
        if close_conn:
            cursor.close()
            conn.close()
        return False



    tolerance = 2.0 # Allow for small discrepancies
    hk_now = datetime.datetime.now(datetime.timezone.utc).astimezone(pytz.timezone('Asia/Hong_Kong')).isoformat()

    # 1. Look for a PDF attachment first
    receipt_url = None
    for att in attachments:
        if att.lower().endswith('.pdf'):
            receipt_url = upload_filepath_to_cloudinary(att, folder="receipts")
            print(f"\033[92m✅ RECEIPT UPLOADED: {receipt_url} for BLs {list(bl_payment_map.keys())}\033[0m")
            break

    # 2. If no PDF, generate one from the email body
    if not receipt_url and body_text:
        try:
            temp_pdf_path = generate_pdf_from_text(body_text, f"temp_receipt_{email_id}.pdf")
            receipt_url = upload_filepath_to_cloudinary(temp_pdf_path, folder="receipts")
            print(f"\033[92m✅ RECEIPT UPLOADED (from email body): {receipt_url} for BLs {list(bl_payment_map.keys())}\033[0m")
            os.remove(temp_pdf_path)
        except Exception as e:
            print(f"[ERROR] Failed to generate or upload PDF from email body: {e}")

    # 3. For each BL, verify and update
    for bl, paid_amount in bl_payment_map.items():
        cursor.execute("SELECT id, ctn_fee, service_fee FROM bill_of_lading WHERE bl_number = %s", (bl,))
        bill_row = cursor.fetchone()
        if not bill_row:
            print(f"[WARN] BL {bl} not found in DB for email {email_id}. Skipping.")
            continue
        bill_id = bill_row[0]
        ctn_fee = float(bill_row[1] or 0)
        service_fee = float(bill_row[2] or 0)
        invoice_amount = ctn_fee + service_fee
        if paid_amount is None or not isinstance(paid_amount, (int, float)):
            print(f"[WARN] No valid payment amount for BL {bl} in email {email_id}. Skipping.")
            continue
        paid_amount_f = float(paid_amount)
        if paid_amount_f < invoice_amount - tolerance:
            print(f"[WARN] Underpayment for BL {bl} in email {email_id}. Expected: {invoice_amount}, Paid: {paid_amount_f}. Skipping.")
            continue
        # If exact or overpaid, proceed to process and upload receipt
        if receipt_url:
            cursor.execute("""
                UPDATE bill_of_lading
                SET receipt_filename = %s, status = 'Awaiting Bank In', receipt_uploaded_at = %s
                WHERE id = %s
            """, (receipt_url, hk_now, bill_id))
            print(f"[INFO] Updated bill {bill_id} with receipt from email {email_id}")
        else:
            print(f"[WARN] No receipt could be generated for email {email_id}. Bill {bill_id} not updated.")

    # Mark email as processed
    cursor.execute("UPDATE customer_emails SET processed_for_payments=TRUE WHERE id=%s", (email_id,))
    conn.commit()
    if close_conn:
        cursor.close()
        conn.close()
    return True


def ingest_emails():
    debug("Ingesting emails from inbox")
    mail = connect_imap()
    if not mail:
        warn("IMAP connection failed, aborting ingestion")
        return []

    email_ids = fetch_unread_emails(mail)
    results = []
    db_conn = get_db_conn()   # FIX: ensure same name
    cursor = db_conn.cursor()

    for eid in email_ids:
        body_text, attachments, message_id, email_date = parse_email(mail, eid)

        # Extract sender and subject from email headers
        msg = email.message_from_bytes(mail.fetch(eid, '(RFC822)')[1][0][1])
        subject, encoding = decode_header(msg['Subject'])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or 'utf-8')
        from_addr = msg.get('From')

        # --- Prevent Duplicate Emails ---
        try:
            # First, try to insert new email
            # Handle duplicate detection with better logic
            if message_id:
                # Try to insert with message_id
                cursor.execute(
                    """
                    INSERT INTO customer_emails (sender, subject, body, created_at, processed_for_payments, message_id) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (message_id) DO NOTHING
                    RETURNING id;
                    """,
                    (from_addr, subject, body_text, email_date, False, message_id)
                )
                result = cursor.fetchone()
                
                if result:
                    # New email inserted successfully
                    email_id = result[0]
                    debug(f"✅ New email inserted with ID: {email_id}")
                else:
                    # Duplicate detected - get existing email
                    debug(f"🔄 Duplicate email detected with Message-ID: {message_id}")
                    
                    cursor.execute(
                        "SELECT id FROM customer_emails WHERE message_id = %s",
                        (message_id,)
                    )
                    existing_email = cursor.fetchone()
                    
                    if existing_email:
                        email_id = existing_email[0]
                        debug(f"✅ Using existing email ID: {email_id}")
                    else:
                        debug(f"❌ Duplicate detected but existing email not found for Message-ID: {message_id}")
                        continue
            else:
                # No message_id - use subject + sender + timestamp for duplicate detection
                debug(f"⚠️ No Message-ID found, using subject-based duplicate detection")
                
                # Check for recent duplicate by subject and sender
                cursor.execute(
                    """
                    SELECT id FROM customer_emails 
                    WHERE sender = %s AND subject = %s 
                    AND created_at >= %s
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (from_addr, subject, email_date - timedelta(minutes=5))
                )
                recent_duplicate = cursor.fetchone()
                
                if recent_duplicate:
                    debug(f"🔄 Recent duplicate detected by subject: {subject}")
                    email_id = recent_duplicate[0]
                else:
                    # Insert new email without message_id
                    cursor.execute(
                        """
                        INSERT INTO customer_emails (sender, subject, body, created_at, processed_for_payments, message_id) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id;
                        """,
                        (from_addr, subject, body_text, email_date, False, None)
                    )
                    result = cursor.fetchone()
                    email_id = result[0]
                    debug(f"✅ New email inserted without Message-ID, ID: {email_id}")

            
            db_conn.commit()
        except Exception as e:
            db_conn.rollback()
            warn(f"[ERROR] Failed to insert email {message_id}: {e}")
            continue

        # === Save Attachments to Database ===
        if attachments:
            debug(f"📎 Processing {len(attachments)} attachments for email {email_id}")
            
            # Upload attachments to Cloudinary and save URLs
            attachment_urls = []
            for attachment_path in attachments:
                try:
                    from cloudinary_utils import upload_filepath_to_cloudinary
                    cloudinary_url = upload_filepath_to_cloudinary(attachment_path, folder="email_attachments")
                    attachment_urls.append(cloudinary_url)
                    debug(f"✅ Uploaded to Cloudinary: {cloudinary_url}")
                except Exception as e:
                    warn(f"❌ Failed to upload attachment {attachment_path}: {e}")
                    # Fallback to local file path
                    attachment_urls.append(attachment_path)
            
            # Update email with attachments
            if attachment_urls:
                import json
                attachment_json = json.dumps(attachment_urls)
                cursor.execute(
                    "UPDATE customer_emails SET attachments = %s::jsonb WHERE id = %s",
                    (attachment_json, email_id)
                )
                db_conn.commit()
                debug(f"✅ Saved {len(attachment_urls)} attachments to database")
        
        # === OpenAI classification and routing ===
        # Add rate limiting to prevent 429 errors
        try:
            from openai_rate_limiter import email_rate_limiter
            
            # Wait for processing slot if needed
            if not email_rate_limiter.can_process_email():
                debug(f"Rate limit: Waiting for email processing slot...")
                email_rate_limiter.wait_for_slot()
            
            action = validate_email_with_openai(subject, body_text, attachments, from_addr, handle_email_via_openai)
            
            # Record that email was processed
            email_rate_limiter.record_email_processed()
            
        except Exception as e:
            warn(f"OpenAI processing error: {e}")
            # Fallback to basic processing
            action = {
                'classification': 'error',
                'reply': f"Error processing email: {str(e)}",
                'confidence_score': 0.0,
                'validation_result': {}
            }

        # Log validation results
        if action.get('validation_result', {}).get('needs_reclassification'):
            debug(f"🚨 Validation issues for email {email_id}: {action['validation_result']}")
            debug(f"   Missed requests: {action['validation_result'].get('missed_request_types', [])}")
            debug(f"   Amount issues: {len(action['validation_result'].get('amount_validation_issues', []))}")

        classification = action.get('classification')
        bl_payment_map = action.get('bl_payment_map', {})
        request_types = action.get("request_types", [])
        reply_text = action.get('reply', '')

        request_types_lower = [r.lower() for r in request_types]
        is_payment_related = any(r in request_types_lower for r in ["payment_receipt", "payment_status", "combined_request"])

        if is_payment_related and bl_payment_map:
            debug("[ROUTING] Detected payment receipt intent — processing receipt upload + DB update.")
            process_payment_receipt_email(
                email_id=email_id,
                from_addr=from_addr,
                subject=subject,
                body_text=body_text,
                attachments=attachments,
                bl_payment_map=bl_payment_map,
                conn=db_conn,
            )

        results.append({"email_id": email_id, "classification": classification})

    return results

        # Note: Draft saving is now handled inside handle_email_via_openai
@bp_ingest.route("/admin/email-ingest-errors/<int:error_id>", methods=["DELETE"])
@jwt_required()
def delete_email_ingest_error(error_id):
    # Ensure JWTs are accepted from both headers and cookies for frontend compatibility
    # (Set this in app.py, but add a comment here for clarity)
    conn = get_db_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM email_ingest_errors WHERE id = %s", (error_id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        return jsonify({"error": "Error record not found"}), 404
    cursor.execute("DELETE FROM email_ingest_errors WHERE id = %s", (error_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Deleted successfully"}), 200

@bp_ingest.route('/process_unprocessed_payment_emails', methods=['POST'])
@jwt_required()
def process_unprocessed_payment_emails_route():
    """
    Processes emails already in the database that are marked as unprocessed.
    This does NOT fetch new emails from IMAP.
    """
    try:
        # Import the email processor to pause background processing
        from email_processor import pause_email_processor, resume_email_processor
        
        # Pause background processing temporarily
        pause_email_processor()
        
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Get unprocessed emails
        cursor.execute("SELECT id, sender, subject, body, attachments FROM customer_emails WHERE processed_for_payments=FALSE")
        emails = cursor.fetchall()
        processed_count = 0
        
        logger.info(f"🔄 Processing {len(emails)} unprocessed emails manually")
        
        for email_row in emails:
            try:
                email_id, sender, subject, body, attachments_json = email_row
                
                # Parse attachments if they exist
                attachments = []
                if attachments_json:
                    try:
                        attachments = json.loads(attachments_json)
                    except:
                        attachments = []
                
                # Classify the email using OpenAI
                action = validate_email_with_openai(subject, body, attachments, sender, handle_email_via_openai)
                
                # Check if it's a payment receipt
                if action and "payment_receipt" in action.get('request_types', []):
                    logger.info(f"💰 Processing payment receipt email {email_id}: {subject}")
                    
                    # Extract BL numbers and payment amount from OpenAI response
                    bl_numbers_from_openai = action.get('bl_numbers', [])
                    paid_amount_from_openai = action.get('paid_amount', 0)
                    
                    # Process the payment receipt
                    process_payment_receipt_email(
                        email_id, sender, subject, body, attachments,
                        bl_numbers_from_openai, paid_amount_from_openai, conn=conn
                    )
                    processed_count += 1
                    logger.info(f"✅ Successfully processed email {email_id}")
                
            except Exception as e:
                logger.error(f"❌ Error processing email {email_row[0]}: {e}")
                continue
        
        cursor.close()
        conn.close()
        
        # Resume background processing
        resume_email_processor()
        
        return jsonify({
            'status': 'success',
            'processed_count': processed_count,
            'total_emails': len(emails),
            'message': f'Successfully processed {processed_count} out of {len(emails)} unprocessed emails'
        })
        
    except Exception as e:
        # Resume background processing on error
        try:
            from email_processor import resume_email_processor
            resume_email_processor()
        except:
            pass
        
        logger.error(f"❌ Error in manual email processing: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error processing emails: {str(e)}'
        }), 500

if __name__ == "__main__":
    ingest_emails()


# import os
# import imaplib
# import email
# from email.header import decode_header
# import os
# import imaplib
# import email
# from email.header import decode_header
# import tempfile
# import fitz  # PyMuPDF
# # import openai
# import requests
# import re
# import logging
# from PIL import Image
# from google.cloud import vision
# from config import get_db_conn
# from cloudinary_utils import upload_filepath_to_cloudinary
# def debug(msg):
#     print(f"[DEBUG] {msg}")
# def warn(msg):
#     print(f"[WARNING] {msg}")

# def get_env(var, default=None):
#     val = os.environ.get(var, default)
#     if val is None:
#         raise Exception(f"Missing env var: {var}")
#     return val

# # Connect to Gmail IMAP
# def connect_imap():
#     host = get_env('EMAIL_HOST', 'imap.mail.yahoo.com')
#     port = int(get_env('EMAIL_PORT', '993'))
#     user = get_env('EMAIL_USERNAME')
#     password = get_env('EMAIL_PASSWORD')
#     debug(f"Connecting to IMAP: {user}@{host}")
#     try:
#         mail = imaplib.IMAP4_SSL(host, port)
#         mail.login(user, password)
#         debug("Logged in successfully")
#         return mail
#     except Exception as e:
#         warn(f"IMAP connection/login failed: {e}")
#         return None

# # Fetch unread emails
# def fetch_unread_emails(mail):
#     mail.select('inbox')
#     status, messages = mail.search(None, '(UNSEEN)')
#     email_ids = messages[0].split()
#     debug(f"Fetched {len(email_ids)} new emails")
#     return email_ids

# # Download attachments and body
# def parse_email(mail, email_id):
#     status, msg_data = mail.fetch(email_id, '(RFC822)')
#     msg = email.message_from_bytes(msg_data[0][1])
#     body_text = ""
#     attachments = []
#     for part in msg.walk():
#         content_type = part.get_content_type()
#         filename = part.get_filename()
#         if filename:
#             decoded = decode_header(filename)[0][0]
#             if isinstance(decoded, bytes):
#                 filename = decoded.decode()
#             with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
#                 tmp.write(part.get_payload(decode=True))
#                 attachments.append(tmp.name)
#                 debug(f"Processing attachment: {filename}")
#         elif content_type == "text/plain":
#             charset = part.get_content_charset() or 'utf-8'
#             body_text += part.get_payload(decode=True).decode(charset, errors='ignore')
#             debug("Email body text detected")
#     # Mark email as read
#     mail.store(email_id, '+FLAGS', '\\Seen')
#     return body_text, attachments

# # Detect type and extract text
# def extract_text_from_file(filepath):
#     ext = os.path.splitext(filepath)[1].lower()
#     if ext == '.pdf':
#         with fitz.open(filepath) as doc:
#             text = ""
#             for page in doc:
#                 page_text = page.get_text()
#                 if page_text.strip():
#                     text += page_text
#             if text.strip():
#                 debug("Attachment type: PDF (text-based)")
#                 return text
#             else:
#                 debug("Attachment type: PDF (image-based)")
#                 images = []
#                 for page in doc:
#                     for img in page.get_images(full=True):
#                         xref = img[0]
#                         pix = fitz.Pixmap(doc, xref)
#                         if pix.n < 5:
#                             img_path = tempfile.mktemp(suffix='.png')
#                             pix.save(img_path)
#                             images.append(img_path)
#                             pix = None
#                 ocr_text = ""
#                 client = vision.ImageAnnotatorClient()
#                 for img_path in images:
#                     with open(img_path, "rb") as image_file:
#                         content = image_file.read()
#                     image = vision.Image(content=content)
#                     response = client.text_detection(image=image)
#                     if response.text_annotations:
#                         ocr_text += response.text_annotations[0].description
#                     os.remove(img_path)
#                 return ocr_text
#     elif ext in ['.jpg', '.jpeg', '.png']:
#         debug("Attachment type: Image")
#         client = vision.ImageAnnotatorClient()
#         with open(filepath, "rb") as image_file:
#             content = image_file.read()
#         image = vision.Image(content=content)
#         response = client.text_detection(image=image)
#         if response.text_annotations:
#             return response.text_annotations[0].description
#         return ""
#     else:
#         with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
#             return f.read()

# # OpenAI GPT extraction
# def extract_payment_data(all_text):
#     # Placeholder parser for testing (no OpenAI call)
#     # Example: extract amount, reference_number, bl_numbers using regex
#     amount_match = re.search(r'\$([0-9]+(?:\.[0-9]{1,2})?)', all_text)
#     amount = float(amount_match.group(1)) if amount_match else 0.0
#     ref_match = re.search(r'Ref[:\s]*([A-Za-z0-9]+)', all_text)
#     reference_number = ref_match.group(1) if ref_match else ''
#     bl_numbers = re.findall(r'BL[0-9]+', all_text)
#     parsed = {
#         'amount': amount,
#         'reference_number': reference_number,
#         'bl_numbers': bl_numbers
#     }
#     debug(f"Parsed fields (placeholder): {parsed}")
#     return parsed

# # DB matching logic
# def match_payment_to_bls(payment_data):
#     conn = get_db_conn()
#     cursor = conn.cursor()
#     bls = payment_data.get('bl_numbers', [])
#     amount = float(payment_data.get('amount', 0))
#     matched = []
#     total_invoice = 0
#     for bl in bls:
#         cursor.execute("SELECT id, invoice_amount, status FROM bill_of_lading WHERE bl_number = ?", (bl,))
#         row = cursor.fetchone()
#         if row:
#             matched.append(row)
#             total_invoice += float(row[1])
#     tolerance = 2.0
#     if abs(total_invoice - amount) <= tolerance and matched:
#         debug(f"Receipt matches payment for BLs: {bls}")
#         return matched, True
#     else:
#         warn(f"Payment amount mismatch for BLs: {bls}\nExpected: {total_invoice}, Received: {amount}")
#         return matched, False

# # Main ingest function
# def ingest_emails():
#     debug("Ingesting emails from inbox")
#     mail = connect_imap()
#     email_ids = fetch_unread_emails(mail)
#     results = []
#     conn = get_db_conn()
#     cursor = conn.cursor()
#     for eid in email_ids:
#         body_text, attachments = parse_email(mail, eid)
#         all_text = body_text
#     from reportlab.lib.pagesizes import letter
#     from reportlab.pdfgen import canvas
#     import tempfile
#     import datetime
#     for eid in email_ids:
#         body_text, attachments = parse_email(mail, eid)
#         all_text = body_text
#         for att in attachments:
#             all_text += "\n" + extract_text_from_file(att)
#         payment_data = extract_payment_data(all_text)
#         # --- PDF from email body if no attachments ---
#         generated_pdf_path = None
#         if not attachments and body_text.strip():
#             debug("[DEBUG] No attachment found. Generating PDF from email body.")
#             with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
#                 generated_pdf_path = tmp_pdf.name
#                 c = canvas.Canvas(generated_pdf_path, pagesize=letter)
#                 c.setFont("Helvetica", 12)
#                 y = 750
#                 c.drawString(30, y, "=== RECEIPT FROM EMAIL BODY ===")
#                 y -= 30
#                 for line in body_text.splitlines():
#                     c.drawString(30, y, line)
#                     y -= 18
#                     if y < 50:
#                         c.showPage()
#                         y = 750
#                 # Metadata
#                 received_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
#                 c.drawString(30, y, f"[Received via email: {os.environ.get('EMAIL_USERNAME','')}] [Date: {received_date}]")
#                 c.save()
#             debug(f"[DEBUG] Generated PDF from email body at path: {generated_pdf_path}")
#             # Upload PDF to Cloudinary
#             url = upload_filepath_to_cloudinary(generated_pdf_path)
#             debug(f"[DEBUG] Uploaded email-body PDF to Cloudinary: {url}")
#             if payment_data:
#                 matched_bls, is_match = match_payment_to_bls(payment_data)
#                 if is_match:
#                     for row in matched_bls:
#                         cursor.execute("UPDATE bill_of_lading SET receipt_filename = ?, status = 'Awaiting Bank In' WHERE id = ?", (url, row[0]))
#                         debug(f"[DEBUG] Updated DB with receipt_filename from email-body PDF for BL id {row[0]}")
#                     conn.commit()
#                     results.append({"filename": generated_pdf_path, "reason": "Receipt processed and attached from email body"})
#                 else:
#                     results.append({"filename": generated_pdf_path, "reason": "Payment amount mismatch or missing B/L (email body PDF)"})
#                     cursor.execute("INSERT INTO email_ingest_errors (filename, reason, raw_text) VALUES (?, ?, ?)", (generated_pdf_path, "Payment amount mismatch or missing B/L (email body PDF)", all_text))
#                     conn.commit()
#                     debug("[WARNING] Inserting error log into email_ingest_errors (email body PDF)")
#             else:
#                 results.append({"filename": generated_pdf_path, "reason": "Failed to extract payment data (email body PDF)"})
#                 cursor.execute("INSERT INTO email_ingest_errors (filename, reason, raw_text) VALUES (?, ?, ?)", (generated_pdf_path, "Failed to extract payment data (email body PDF)", all_text))
#                 conn.commit()
#                 debug("[WARNING] Inserting error log into email_ingest_errors (email body PDF)")
#             # Clean up temp PDF
#             try:
#                 os.remove(generated_pdf_path)
#                 debug(f"[DEBUG] Cleaned up local generated PDF file: {generated_pdf_path}")
#             except Exception:
#                 pass
#             continue
#         # --- Normal attachment logic ---
#         if not payment_data:
#             results.append({"filename": None, "reason": "Failed to extract payment data"})
#             cursor.execute("INSERT INTO email_ingest_errors (filename, reason, raw_text) VALUES (?, ?, ?)", (None, "Failed to extract payment data", all_text))
#             conn.commit()
#             debug("[WARNING] Inserting error log into email_ingest_errors")
#             continue
#         matched_bls, is_match = match_payment_to_bls(payment_data)
#         if is_match:
#             for att in attachments:
#                 url = upload_filepath_to_cloudinary(att)
#                 debug(f"Uploaded receipt to Cloudinary: {url}")
#                 for row in matched_bls:
#                     cursor.execute("UPDATE bill_of_lading SET receipt_filename = ?, status = 'Awaiting Bank In' WHERE id = ?", (url, row[0]))
#                     debug(f"Updated BOL with receipt_filename and status for BL id {row[0]}")
#             conn.commit()
#             results.append({"filename": attachments[0] if attachments else None, "reason": "Receipt processed and attached"})
#         else:
#             results.append({"filename": attachments[0] if attachments else None, "reason": "Payment amount mismatch or missing B/L"})
#             cursor.execute("INSERT INTO email_ingest_errors (filename, reason, raw_text) VALUES (?, ?, ?)", (attachments[0] if attachments else None, "Payment amount mismatch or missing B/L", all_text))
#             conn.commit()
#             debug("[WARNING] Inserting error log into email_ingest_errors")
#         for att in attachments:
#             try:
#                 os.remove(att)
#             except Exception:
#                 pass
#     return results

# if __name__ == "__main__":
#     ingest_emails()