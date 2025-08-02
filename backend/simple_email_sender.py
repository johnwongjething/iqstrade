#!/usr/bin/env python3
"""
Simple Automated Email Sender for Testing Email Ingestor
Sends all 8 test emails to Gmail automatically (no PDF dependencies)
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

def send_test_emails():
    """Send all 8 test emails automatically"""
    
    # Email configuration
    sender_email = os.getenv('SMTP_USERNAME')
    sender_password = os.getenv('SMTP_PASSWORD')
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    # Target email (where the ingestor monitors)
    target_email = os.getenv('EMAIL_USERNAME')  # Same as sender for testing
    
    if not all([sender_email, sender_password, smtp_server]):
        print("❌ Missing email configuration. Please set EMAIL_USERNAME, EMAIL_PASSWORD, and EMAIL_HOST in .env file")
        print("\nExample .env file:")
        print("EMAIL_USERNAME=your-email@gmail.com")
        print("EMAIL_PASSWORD=your-app-password")
        print("EMAIL_HOST=smtp.gmail.com")
        return
    
    # Test emails to send
    test_emails = [
        {
            "subject": "Simple Test 1 - Payment for BL2024001",
            "body": """Dear IQS Trade,

I have paid $200 for BL2024001. Please confirm receipt and send invoice.

Thanks,
Client"""
        },
        {
            "subject": "Simple Test 2 - Allinpay 85% for BL2024002",
            "body": """Hello IQS Trade,

I have paid $170 (85%) for BL2024002 via Allinpay. When can I settle the remaining $30?

Best regards,
Client"""
        },
        {
            "subject": "Simple Test 3 - CTN Request for BL2024003",
            "body": """Hi IQS Trade,

请问BL2024003的CTN号码是多少？

Also, I need to track the shipment status.

Thanks,
Client"""
        },
        {
            "subject": "Simple Test 4 - Multiple BLs (BL2024004, BL2024005)",
            "body": """Dear Team,

I need information for:
- BL2024004: Payment status
- BL2024005: CTN number

Please provide updates for both shipments.

Regards,
Client"""
        },
        {
            "subject": "Simple Test 5 - Reserve Settlement for BL2024006",
            "body": """Hello IQS Trade,

I want to settle the reserve for BL2024006. The reserve amount is $30.

Please confirm the settlement process.

Thanks,
Client"""
        },
        {
            "subject": "Simple Test 6 - Payment Status for BL2024007",
            "body": """Dear IQS Trade,

I made a payment of $200 for BL2024007 yesterday. Please confirm if you have received the payment and what the current status is.

Thanks,
Client"""
        },
        {
            "subject": "Simple Test 7 - Invoice Request for BL2024008",
            "body": """Hello IQS Trade,

Please send me the invoice for BL2024008. I need it for my records.

Best regards,
Client"""
        },
        {
            "subject": "Simple Test 8 - Payment Confirmation for BL2024009",
            "body": """Hi IQS Trade,

I have made the payment for BL2024009. Please confirm receipt and update the status.

Thanks,
Client"""
        }
    ]
    
    print("📧 Simple Automated Email Sender for Testing")
    print("=" * 60)
    print(f"SMTP Server: {smtp_server}")
    print(f"Sender Email: {sender_email}")
    print(f"Target Email: {target_email} (where ingestor monitors)")
    print(f"Total Emails to Send: {len(test_emails)}")
    print()
    
    try:
        # Connect to SMTP server
        print("🔌 Connecting to SMTP server...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        print("✅ Connected and authenticated successfully!")
        
        # Send each test email
        for i, email_data in enumerate(test_emails, 1):
            print(f"\n📤 Sending Email {i}: {email_data['subject']}")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = target_email  # Send to monitored email address
            msg['Subject'] = email_data['subject']
            
            # Add body
            if email_data['body']:
                msg.attach(MIMEText(email_data['body'], 'plain'))
            
            # Add attachments if any
            if 'attachments' in email_data and email_data['attachments']:
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
                        print(f"   📎 Attached: {attachment_path}")
                    else:
                        print(f"   ⚠️  Attachment not found: {attachment_path}")
            
            # Send email
            text = msg.as_string()
            server.sendmail(sender_email, target_email, text)
            print(f"   ✅ Sent successfully!")
            
            # Wait 2 seconds between emails to avoid rate limiting
            if i < len(test_emails):
                print("   ⏳ Waiting 2 seconds...")
                time.sleep(2)
        
        # Close connection
        server.quit()
        print(f"\n🎉 All {len(test_emails)} test emails sent successfully!")
        print("\n📋 Next Steps:")
        print("1. Check your Gmail inbox for the test emails")
        print("2. Run the email ingestor to process them:")
        print("   python email_ingestor.py")
        print("3. Or run the automated test:")
        print("   python test_email_automation.py")
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed. Please check your email credentials.")
        print("\n💡 For Gmail, you need to:")
        print("1. Enable 2-factor authentication")
        print("2. Generate an App Password")
        print("3. Use the App Password instead of your regular password")
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    send_test_emails() 