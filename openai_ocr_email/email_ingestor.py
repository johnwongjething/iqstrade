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
from utils.log import logger
from ocr_processor import process_pdf
from dotenv import load_dotenv
import openai
import json

# Load env from ../iqstrade/.env
load_dotenv(os.path.join(os.path.dirname(__file__), '../iqstrade/.env'))

IMAP_SERVER = os.getenv('EMAIL_HOST')
EMAIL_USER = os.getenv('EMAIL_USERNAME')
EMAIL_PASS = os.getenv('EMAIL_PASSWORD')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
openai.api_key = OPENAI_API_KEY

PDF_SAVE_DIR = 'downloads'
os.makedirs(PDF_SAVE_DIR, exist_ok=True)

def connect_imap():
    return imaplib.IMAP4_SSL(IMAP_SERVER)

def handle_email_via_openai(subject, body, attachments, from_addr):
    print(f"[DEBUG] [OpenAI] handle_email_via_openai called with subject: {subject}, from: {from_addr}")
    full_text = f"Subject: {subject}\n\n{body}"
    prompt = f"""
You are a logistics assistant. Based on this email, classify its intent:
1. Is the customer asking about invoice/CTN/documents?
2. Is this a payment receipt (bank transfer screenshot)?
3. Is it a general enquiry?

Provide:
- classification: one of ["invoice_request", "payment_receipt", "general_enquiry"]
- any info you need from DB (like BL number or receipt filename)
- reply message to customer (leave as draft)
EMAIL:
{full_text}

Return your answer as a valid JSON object with keys: classification, info_needed, reply.
"""
    print("[DEBUG] [OpenAI] Calling openai.ChatCompletion.create for email classification...")
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You're a shipping email agent."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    print("[DEBUG] [OpenAI] openai.ChatCompletion.create response received.")
    content = response.choices[0].message.content
    try:
        action = json.loads(content)
    except Exception:
        import re
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            try:
                action = json.loads(match.group(0))
            except Exception:
                logger.error(f"[OpenAI Email] Could not parse JSON from response: {content}")
                action = {"classification": "unknown", "reply": "", "bl_number": ""}
        else:
            logger.error(f"[OpenAI Email] Could not parse JSON from response: {content}")
            action = {"classification": "unknown", "reply": "", "bl_number": ""}
    logger.info(f"[OpenAI Email] Classification: {action.get('classification')}")
    logger.info(f"[OpenAI Email] Draft reply: {action.get('reply')}")
    # Save draft reply (implement as needed, e.g., DB or file)
    save_draft_reply(from_addr, subject, action.get('reply', ''))
    print(f"[DEBUG] [OpenAI] handle_email_via_openai returning action: {action}")
    return action

def save_draft_reply(to_addr, subject, reply):
    # Placeholder: save to DB, file, or print
    logger.info(f"[Draft Reply] To: {to_addr}, Subject: {subject}, Reply: {reply}")
    # Implement DB save as needed

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