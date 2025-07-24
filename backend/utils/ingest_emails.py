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
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import pytz
from email_ingestor import handle_email_via_openai, save_draft_reply
from reportlab.lib.utils import simpleSplit
from invoice_utils import generate_pdf_from_text

bp_ingest = Blueprint("bp_ingest", __name__)

# ...rest of your code...


def debug(msg):
    print(f"[DEBUG] {msg}")

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
    return body_text, attachments, message_id

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

def process_payment_receipt_email(email_id, from_addr, subject, body_text, attachments, bl_numbers, paid_amount, conn=None):
    """
    Centralized logic to process a payment receipt email.
    - Uses a provided list of BL numbers.
    - Uploads receipt (if any) to Cloudinary.
    - Updates the corresponding bill in bill_of_lading.
    - Mark the email as processed_for_payments = TRUE.
    - Compares paid amount to total invoice amount before updating.
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
    
    if not bl_numbers:
        print(f"[WARN] No BL number was provided for email {email_id}. Marking as processed.")
        cursor.execute("UPDATE customer_emails SET processed_for_payments=TRUE WHERE id=%s", (email_id,))
        conn.commit()
        if close_conn:
            cursor.close()
            conn.close()
        return False

    print(f"[DEBUG] Processing payment for email {email_id} with BLs: {bl_numbers} and amount: {paid_amount}")

    # --- Amount Verification ---
    total_expected_amount = 0
    bill_ids_to_update = []
    for bl in bl_numbers:
        cursor.execute("SELECT id, ctn_fee, service_fee FROM bill_of_lading WHERE bl_number = %s", (bl,))
        bill_row = cursor.fetchone()
        if bill_row:
            bill_ids_to_update.append(bill_row[0])
            ctn_fee = float(bill_row[1] or 0)
            service_fee = float(bill_row[2] or 0)
            total_expected_amount += ctn_fee + service_fee
    
    if paid_amount is None or not isinstance(paid_amount, (int, float)):
        print(f"[WARN] No valid payment amount found in email {email_id}. Cannot verify payment. Flagging for manual review.")
        # Mark as processed to avoid re-running, but don't update bills
        cursor.execute("UPDATE customer_emails SET processed_for_payments=TRUE WHERE id=%s", (email_id,))
        conn.commit()
        if close_conn:
            cursor.close()
            conn.close()
        return False
        
    tolerance = 2.0 # Allow for small discrepancies
    paid_amount_f = float(paid_amount)
    # If underpaid, flag for manual review. If overpaid, process as normal.
    if paid_amount_f < total_expected_amount - tolerance:
        print(f"[WARN] Underpayment for email {email_id}. Expected: {total_expected_amount}, Paid: {paid_amount_f}. Flagging for manual review.")
        cursor.execute("UPDATE customer_emails SET processed_for_payments=TRUE WHERE id=%s", (email_id,))
        conn.commit()
        if close_conn:
            cursor.close()
            conn.close()
        return False
    # If exact or overpaid, proceed to process and upload receipt
    print(f"[INFO] Payment amount verified (or overpaid) for email {email_id}. Proceeding to update bills.")

    # --- Proceed with updating bills since amount is verified ---
    # 1. Look for a PDF attachment first
    receipt_url = None
    for att in attachments:
        if att.lower().endswith('.pdf'):
            receipt_url = upload_filepath_to_cloudinary(att, folder="receipts")
            print(f"[INFO] Uploaded attached PDF as receipt for bills {bill_ids_to_update}")
            break
    
    # 2. If no PDF, generate one from the email body
    if not receipt_url and body_text:
        try:
            # Generate a PDF from the email body text.
            temp_pdf_path = generate_pdf_from_text(body_text, f"temp_receipt_{email_id}.pdf")
            receipt_url = upload_filepath_to_cloudinary(temp_pdf_path, folder="receipts") # Use upload_filepath_to_cloudinary
            os.remove(temp_pdf_path) # Clean up the temporary file
        except Exception as e:
            print(f"[ERROR] Failed to generate or upload PDF from email body: {e}")

    hk_now = datetime.datetime.now(datetime.timezone.utc).astimezone(pytz.timezone('Asia/Hong_Kong')).isoformat()
    if receipt_url:
        for bill_id in bill_ids_to_update:
            cursor.execute("""
                UPDATE bill_of_lading
                SET receipt_filename = %s, status = 'Awaiting Bank In', receipt_uploaded_at = %s
                WHERE id = %s
            """, (receipt_url, hk_now, bill_id))
            print(f"[INFO] Updated bill {bill_id} with receipt from email {email_id}")
    else:
        print(f"[WARN] No receipt could be generated for email {email_id}. Bills not updated.")

    # Mark email as processed
    cursor.execute("UPDATE customer_emails SET processed_for_payments=TRUE WHERE id=%s", (email_id,))
    conn.commit()
    if close_conn:
        cursor.close()
        conn.close()
    return True

# Main
def ingest_emails():
    debug("Ingesting emails from inbox")
    mail = connect_imap()
    if not mail:
        warn("IMAP connection failed, aborting ingestion")
        return []
    email_ids = fetch_unread_emails(mail)
    results = []
    conn = get_db_conn()
    cursor = conn.cursor()
    for eid in email_ids:
        body_text, attachments, message_id = parse_email(mail, eid)
        
        # Extract sender and subject from email headers
        msg = email.message_from_bytes(mail.fetch(eid, '(RFC822)')[1][0][1])
        subject, encoding = decode_header(msg['Subject'])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or 'utf-8')
        from_addr = msg.get('From')

        # --- Prevent Duplicate Emails using an Atomic Insert ---
        try:
            cursor.execute(
                """
                INSERT INTO customer_emails (sender, subject, body, created_at, processed_for_payments, message_id) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (message_id) DO NOTHING
                RETURNING id;
                """,
                (from_addr, subject, body_text, datetime.datetime.now(), False, message_id)
            )
            result = cursor.fetchone()
            if not result:
                debug(f"Skipping duplicate email with Message-ID: {message_id}")
                continue # Skip if the email already existed
            email_id = result[0]
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Failed to insert new email, skipping. Message-ID: {message_id}, Error: {e}")
            continue

        # === OpenAI classification and draft ===
        action = handle_email_via_openai(subject, body_text, attachments, from_addr)
        classification = action.get('classification')
        bl_numbers_from_openai = action.get('bl_numbers', []) # Get list of BLs
        paid_amount_from_openai = action.get('paid_amount') # Get paid amount
        
        # === Centralized payment receipt processing ===
        if classification == "payment_receipt":
            # Pass the BL numbers and paid amount from OpenAI to the processing function
            process_payment_receipt_email(
                email_id, from_addr, subject, body_text, attachments, 
                bl_numbers_from_openai, paid_amount_from_openai, conn=conn
            )
        
        # Note: Draft saving is now handled inside handle_email_via_openai
    mail.logout()
    return results

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
    conn = get_db_conn()
    cursor = conn.cursor()
    # Note: We are now fetching attachments from the stored email, not live from IMAP
    cursor.execute("SELECT id, sender, subject, body, attachments FROM customer_emails WHERE processed_for_payments=FALSE")
    emails = cursor.fetchall()
    processed_count = 0
    for email_row in emails:
        email_id, sender, subject, body, attachments_json = email_row
        
        # We need to simulate the OpenAI classification again or use a stored classification
        # For simplicity, we will re-classify. For optimization, store the classification.
        action = handle_email_via_openai(subject, body, [], from_addr=sender) # attachments are not easily available here
        
        if action.get('classification') == 'payment_receipt':
            bl_list = action.get('bl_numbers', [])
            process_payment_receipt_email(email_id, sender, subject, body, [], bl_list, 0.0, conn=conn) # Pass 0.0 for paid_amount
            processed_count += 1

    cursor.close()
    conn.close()
    return jsonify({'processed_count': processed_count})

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
