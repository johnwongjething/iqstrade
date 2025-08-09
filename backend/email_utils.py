
import smtplib
from email.message import EmailMessage
from email.utils import formataddr, parseaddr
import os

from config import EmailConfig
from invoice_utils import send_invoice_email

# Loaded email_utils.py

# Send invoice email with PDF attachment using SMTP
# def send_invoice_email(to_email, subject, body, pdf_path):
#     try:
#         # Check if SMTP configuration is available
#         if not all([EmailConfig.SMTP_SERVER, EmailConfig.SMTP_USERNAME, EmailConfig.SMTP_PASSWORD]):
#             print("SMTP configuration not available, skipping email sending")
#             return True  # Return True to indicate success since we're skipping
#
#         print(f"Attempting to send email to: {to_email}")
#         print(f"SMTP server: {EmailConfig.SMTP_SERVER}:{EmailConfig.SMTP_PORT}")
#         print(f"From email: {EmailConfig.FROM_EMAIL}")
#         
#         msg = EmailMessage()
#         msg['Subject'] = subject
#         msg['From'] = formataddr(('Logistics Company', EmailConfig.FROM_EMAIL))
#         msg['To'] = to_email
#         msg.set_content(body)
#
#         # Attach PDF
#         print(f"Attaching PDF from: {pdf_path}")
#         with open(pdf_path, 'rb') as f:
#             pdf_data = f.read()
#             msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename='invoice.pdf')
#
#         with smtplib.SMTP(EmailConfig.SMTP_SERVER, EmailConfig.SMTP_PORT) as server:
#             print("Starting TLS...")
#             server.starttls()
#             print("Logging in...")
#             server.login(EmailConfig.SMTP_USERNAME, EmailConfig.SMTP_PASSWORD)
#             print("Sending message...")
#             server.send_message(msg)
#         print("Email sent successfully")
#         return True
#     except Exception as e:
#         print(f"Failed to send invoice email: {str(e)}")
#         print(f"Email config: {EmailConfig.SMTP_SERVER}, {EmailConfig.SMTP_PORT}, {EmailConfig.SMTP_USERNAME}, {EmailConfig.SMTP_PASSWORD}")
#         return False

def send_email(to, subject, body):
    from email.utils import formataddr
    # Ensure all required config values are present
    if not all([
        EmailConfig.SMTP_SERVER,
        EmailConfig.SMTP_PORT,
        EmailConfig.SMTP_USERNAME,
        EmailConfig.SMTP_PASSWORD,
        EmailConfig.FROM_EMAIL
    ]):
        raise ValueError("SMTP server, port, username, password, and FROM_EMAIL must all be set in EmailConfig.")
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = formataddr(('Logistics Company', EmailConfig.FROM_EMAIL))  # Use verified sender
    msg['To'] = to
    msg.set_content(body)

    with smtplib.SMTP(str(EmailConfig.SMTP_SERVER), int(EmailConfig.SMTP_PORT)) as server:
        server.starttls()
        server.login(str(EmailConfig.SMTP_USERNAME), str(EmailConfig.SMTP_PASSWORD))
        server.send_message(msg)

def send_email_with_attachment(to, subject, body, attachments, cc=None, bcc=None, reply_to=None):
    """
    Send email with attachments and support for CC, BCC, and Reply-To
    
    Args:
        to: Primary recipient email address
        subject: Email subject
        body: Email body text
        attachments: List of file paths to attach
        cc: List of CC email addresses (optional)
        bcc: List of BCC email addresses (optional)
        reply_to: List of Reply-To email addresses (optional)
    """
    if not all([
        EmailConfig.SMTP_SERVER,
        EmailConfig.SMTP_PORT,
        EmailConfig.SMTP_USERNAME,
        EmailConfig.SMTP_PASSWORD,
        EmailConfig.FROM_EMAIL
    ]):
        raise ValueError("SMTP server, port, username, password, and FROM_EMAIL must all be set in EmailConfig.")
    
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = formataddr(('Logistics Company', EmailConfig.FROM_EMAIL))
        msg['To'] = to
        msg.set_content(body)
        
        # Add CC if provided
        if cc and isinstance(cc, list) and len(cc) > 0:
            cc_emails = [email.strip() for email in cc if email.strip()]
            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)
        
        # Add Reply-To if provided
        if reply_to and isinstance(reply_to, list) and len(reply_to) > 0:
            reply_to_emails = [email.strip() for email in reply_to if email.strip()]
            if reply_to_emails:
                msg['Reply-To'] = ', '.join(reply_to_emails)
        
        # Add attachments
        for file_path in attachments:
            with open(file_path, 'rb') as f:
                file_data = f.read()
                file_name = os.path.basename(file_path)
            maintype = 'application'
            subtype = 'octet-stream'
            if file_name.lower().endswith('.pdf'):
                subtype = 'pdf'
            msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=file_name)
        
        # Prepare recipients list (To + CC + BCC)
        recipients = [to]
        if cc and isinstance(cc, list):
            recipients.extend([email.strip() for email in cc if email.strip()])
        if bcc and isinstance(bcc, list):
            recipients.extend([email.strip() for email in bcc if email.strip()])
        
        # Remove duplicates while preserving order
        unique_recipients = []
        for recipient in recipients:
            if recipient not in unique_recipients:
                unique_recipients.append(recipient)
        
        with smtplib.SMTP(str(EmailConfig.SMTP_SERVER), int(EmailConfig.SMTP_PORT)) as server:
            server.starttls()
            server.login(str(EmailConfig.SMTP_USERNAME), str(EmailConfig.SMTP_PASSWORD))
            server.send_message(msg, to_addrs=unique_recipients)
        return True
    except Exception as e:
        print(f"Failed to send email with attachment: {str(e)}")
        return False

# Send unique number email using SMTP (plain text)
def send_unique_number_email(to_email, subject, body):
    # Ensure all required config values are present
    if not all([
        EmailConfig.SMTP_SERVER,
        EmailConfig.SMTP_PORT,
        EmailConfig.SMTP_USERNAME,
        EmailConfig.SMTP_PASSWORD,
        EmailConfig.FROM_EMAIL
    ]):
        raise ValueError("SMTP server, port, username, password, and FROM_EMAIL must all be set in EmailConfig.")
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = formataddr(('Logistics Company', EmailConfig.FROM_EMAIL))
        msg['To'] = to_email
        msg.set_content(body)

        with smtplib.SMTP(str(EmailConfig.SMTP_SERVER), int(EmailConfig.SMTP_PORT)) as server:
            server.starttls()
            server.login(str(EmailConfig.SMTP_USERNAME), str(EmailConfig.SMTP_PASSWORD))
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send unique number email: {str(e)}")
        return False

def send_contact_email(name, from_email, message):
    # Ensure all required config values are present
    if not all([
        EmailConfig.SMTP_SERVER,
        EmailConfig.SMTP_PORT,
        EmailConfig.SMTP_USERNAME,
        EmailConfig.SMTP_PASSWORD,
        EmailConfig.FROM_EMAIL
    ]):
        raise ValueError("SMTP server, port, username, password, and FROM_EMAIL must all be set in EmailConfig.")
    to_email = "johnwongjething@gmail.com"  # Your receiving email
    subject = "New Contact Form Submission"
    body = f"Name: {name}\nEmail: {from_email}\n\nMessage:\n{message}"

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = formataddr(('Website Contact', EmailConfig.FROM_EMAIL))
    msg['To'] = to_email
    msg['Reply-To'] = from_email
    msg.set_content(body)

    try:
        print(f"Attempting to send contact email to: {to_email}")
        with smtplib.SMTP(str(EmailConfig.SMTP_SERVER), int(EmailConfig.SMTP_PORT)) as server:
            server.starttls()
            server.login(str(EmailConfig.SMTP_USERNAME), str(EmailConfig.SMTP_PASSWORD))
            server.send_message(msg)
        print("Contact email sent successfully.")
        return True
    except Exception as e:
        print(f"Failed to send contact email: {str(e)}")
        return False

# Send a simple plain text email to a customer (for registration approval, upload confirmation, etc.)
def send_simple_email(to_email, subject, body):
    # Ensure all required config values are present
    if not all([
        EmailConfig.SMTP_SERVER,
        EmailConfig.SMTP_PORT,
        EmailConfig.SMTP_USERNAME,
        EmailConfig.SMTP_PASSWORD,
        EmailConfig.FROM_EMAIL
    ]):
        raise ValueError("SMTP server, port, username, password, and FROM_EMAIL must all be set in EmailConfig.")
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = formataddr(('Logistics Company', EmailConfig.FROM_EMAIL))
        msg['To'] = to_email
        msg.set_content(body)
        
        with smtplib.SMTP(str(EmailConfig.SMTP_SERVER), int(EmailConfig.SMTP_PORT)) as server:
            server.starttls()
            server.login(str(EmailConfig.SMTP_USERNAME), str(EmailConfig.SMTP_PASSWORD))
            server.send_message(msg)
        # Simple email sent successfully
        return True
    except Exception as e:
        print("Failed to send simple email:", e)
        return False

def send_payment_confirmation_email(to_email, customer_name, bl_number):
    subject = "Payment Received - Thank You!"
    body = f"Dear {customer_name},\n\nWe have received your payment for Bill of Lading {bl_number}. Your CTN Number is now valid.\n\nThank you for your business!"
    send_simple_email(to_email, subject, body)
