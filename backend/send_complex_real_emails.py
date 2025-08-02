#!/usr/bin/env python3
"""
Send Complex Real Email Tests
Sends the complex test scenarios as real emails to test the system
"""

import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

# Load environment variables from .env.local (fallback to .env)
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
if not os.path.exists(env_file):
    env_file = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_file)

def send_complex_test_emails():
    """Send complex test emails automatically"""
    
    # Email configuration
    sender_email = os.getenv('EMAIL_USERNAME')
    sender_password = os.getenv('EMAIL_PASSWORD')
    smtp_server = os.getenv('EMAIL_HOST')
    smtp_port = 587  # Standard TLS port
    
    # Target email (where the ingestor monitors)
    target_email = os.getenv('EMAIL_USERNAME')  # Same as sender for testing
    
    if not all([sender_email, sender_password, smtp_server]):
        print("❌ Missing email configuration. Please set EMAIL_USERNAME, EMAIL_PASSWORD, and EMAIL_HOST in .env file")
        return
    
    # Complex test emails to send
    complex_test_emails = [
        {
            "subject": "Complex Test 1 - Mixed Payment Types",
            "body": """Dear IQS Trade Team,

I need to make payments for multiple shipments:

1. BL NAM20: USD 250 (partial payment)
2. BL 001-123: USD 200 (full payment) 
3. BL NYC220: USD 180 (overpayment)

Also, please provide CTN numbers for all three shipments and send invoices.

Best regards,
John Doe"""
        },
        {
            "subject": "Complex Test 2 - Chinese + English Mixed",
            "body": """Hello IQS Trade,

请问BL NAM20和BL 001-123的CTN号码是多少？

Also, I have paid $500 for BL NYC220. Please confirm receipt.

另外，请告知营业时间和付款方式。

Thanks,
John"""
        },
        {
            "subject": "Complex Test 3 - PDF with Multiple BLs",
            "body": "Please process the attached payment receipt for multiple shipments.",
            "attachments": ["3.pdf"]
        },
        {
            "subject": "Complex Test 4 - Underpayment Scenario",
            "body": """Hi Team,

I'm sending payment for:
- BL NAM20: $100 (should be $250 total)
- BL 001-123: $150 (should be $200 total)
- BL NYC220: $50 (should be $200 total)

Total sent: $300. Please confirm what's still due.

Thanks,
John"""
        },
        {
            "subject": "Complex Test 5 - Invalid BL Mixed with Valid",
            "body": """Hello,

I need information for:
- BL NAM20 (valid)
- BL 001-123 (valid) 
- BL NYC220 (valid)
- BL INVALID999 (invalid)
- BL TEST123 (invalid)

Please provide CTN numbers and payment status for all shipments.

Regards,
John"""
        },
        {
            "subject": "Complex Test 6 - Business Hours + Payment Methods",
            "body": """Hi IQS Trade,

What are your business hours? Also, what payment methods do you accept?

I need to pay for BL NAM20 ($250), BL 001-123 ($200), and BL NYC220 ($200).

Please provide payment instructions.

Thanks,
John"""
        },
        {
            "subject": "Complex Test 7 - CTN Processing Time",
            "body": """Dear Team,

How long does it take to process CTN for BL NAM20, BL 001-123, and BL NYC220?

Also, what are the total fees for each shipment?

Best regards,
John Doe"""
        },
        {
            "subject": "Complex Test 8 - Empty Body with PDF",
            "body": "",
            "attachments": ["3.pdf"]
        }
    ]
    
    print("🚀 SENDING COMPLEX REAL EMAIL TESTS")
    print(f"From: {sender_email}")
    print(f"To: {target_email}")
    print(f"SMTP: {smtp_server}:{smtp_port}")
    print("=" * 60)
    
    # Connect to SMTP server
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        print("✅ Connected to SMTP server successfully")
    except Exception as e:
        print(f"❌ Failed to connect to SMTP server: {e}")
        return
    
    # Send each test email
    for i, email_data in enumerate(complex_test_emails, 1):
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = target_email
            msg['Subject'] = email_data['subject']
            
            # Add body
            body = email_data['body']
            msg.attach(MIMEText(body, 'plain'))
            
            # Add attachments if any
            if 'attachments' in email_data:
                for attachment_path in email_data['attachments']:
                    if os.path.exists(attachment_path):
                        with open(attachment_path, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                        
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {os.path.basename(attachment_path)}'
                        )
                        msg.attach(part)
                        print(f"📎 Attached: {attachment_path}")
                    else:
                        print(f"⚠️ Attachment not found: {attachment_path}")
            
            # Send email
            server.send_message(msg)
            print(f"✅ Email {i} sent: {email_data['subject']}")
            
            # Wait between emails to avoid rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Failed to send email {i}: {e}")
    
    server.quit()
    print("\n🎉 All complex test emails sent!")
    print("\n📋 Next Steps:")
    print("1. Wait 1-2 minutes for emails to arrive")
    print("2. Run the email ingestion process")
    print("3. Check the results in your application")

if __name__ == "__main__":
    send_complex_test_emails() 