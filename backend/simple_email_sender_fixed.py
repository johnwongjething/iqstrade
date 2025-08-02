#!/usr/bin/env python3
"""
Simple Email Sender - Fixed for BL Number Format
Uses BL numbers that work with the current regex pattern
"""

import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
load_dotenv(env_file)

def send_fixed_test_emails():
    """Send test emails with BL numbers that work with the regex pattern"""
    
    # Get SMTP settings from .env.local
    smtp_server = os.getenv('SMTP_SERVER')  # smtp-relay.brevo.com
    smtp_port = int(os.getenv('SMTP_PORT', '587'))  # 587
    smtp_username = os.getenv('SMTP_USERNAME')  # 8ff19f001@smtp-brevo.com
    smtp_password = os.getenv('SMTP_PASSWORD')  # 01smLzJnjcr4BDxM
    from_email = os.getenv('FROM_EMAIL')  # ray6330099@gmail.com
    to_email = os.getenv('EMAIL_USERNAME')  # ray6330088@gmail.com
    
    print("🚀 Fixed Email Sender - BL Number Compatible")
    print("=" * 50)
    print(f"📧 SMTP Server: {smtp_server}")
    print(f"📧 SMTP Port: {smtp_port}")
    print(f"📧 From: {from_email}")
    print(f"📧 To: {to_email}")
    print("=" * 50)
    
    # Test emails with BL numbers that work with the regex pattern
    # Using format: BL-2024-001 (which should match BL-\d{4,})
    test_emails = [
        {
            "subject": "Fixed Test 1 - Payment for BL-2024-001",
            "body": """Dear IQS Trade,

I have paid $200 for BL-2024-001. Please confirm receipt and send invoice.

Thanks,
Client"""
        },
        {
            "subject": "Fixed Test 2 - Allinpay 85% for BL-2024-002",
            "body": """Hello IQS Trade,

I have paid $170 (85%) for BL-2024-002 via Allinpay. When can I settle the remaining $30?

Best regards,
Client"""
        },
        {
            "subject": "Fixed Test 3 - CTN Request for BL-2024-003",
            "body": """Hi IQS Trade,

请问BL-2024-003的CTN号码是多少？

Also, I need to track the shipment status.

Thanks,
Client"""
        },
        {
            "subject": "Fixed Test 4 - Multiple BLs (BL-2024-004, BL-2024-005)",
            "body": """Dear Team,

I need information for:
- BL-2024-004: Payment status
- BL-2024-005: CTN number

Please provide updates for both shipments.

Regards,
Client"""
        },
        {
            "subject": "Fixed Test 5 - Reserve Settlement for BL-2024-006",
            "body": """Hello IQS Trade,

I want to settle the reserve for BL-2024-006. The reserve amount is $30.

Please confirm the settlement process.

Thanks,
Client"""
        }
    ]
    
    # Send each email
    for i, email_data in enumerate(test_emails, 1):
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = email_data['subject']
            
            # Add body
            body = email_data['body']
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            print(f"\n📧 Sending email {i}: {email_data['subject']}")
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            print(f"✅ Email {i} sent successfully!")
            
            # Wait between emails to avoid rate limiting
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ Failed to send email {i}: {e}")
            print(f"   Error details: {type(e).__name__}")
    
    print(f"\n🎉 Email sending completed!")
    print(f"📊 Successfully sent {len(test_emails)} emails")
    
    print("\n📋 Next Steps:")
    print("1. Check your email inbox for the test emails")
    print("2. Start email scheduler: python email_scheduler.py")
    print("3. Monitor email processing in database")

def send_alternative_format_emails():
    """Send emails with alternative BL number formats that might work better"""
    
    # Get SMTP settings
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL')
    to_email = os.getenv('EMAIL_USERNAME')
    
    print("🚀 Alternative Format Email Sender")
    print("=" * 50)
    
    # Test emails with different BL number formats
    alternative_emails = [
        {
            "subject": "Alt Test 1 - BL Number with Space (BL 2024-001)",
            "body": """Dear IQS Trade,

I have paid $200 for BL 2024-001. Please confirm receipt and send invoice.

Thanks,
Client"""
        },
        {
            "subject": "Alt Test 2 - BL Number with Colon (BL: 2024-002)",
            "body": """Hello IQS Trade,

I have paid $170 for BL: 2024-002. Please process the payment.

Best regards,
Client"""
        },
        {
            "subject": "Alt Test 3 - Bill of Lading Number (Bill of Lading: 2024-003)",
            "body": """Hi IQS Trade,

What's the status of Bill of Lading: 2024-003?

Thanks,
Client"""
        },
        {
            "subject": "Alt Test 4 - B/L Format (B/L 2024-004)",
            "body": """Dear Team,

I need information for B/L 2024-004. Please provide status update.

Regards,
Client"""
        },
        {
            "subject": "Alt Test 5 - Multiple Formats (BL-2024-005, B/L 2024-006)",
            "body": """Hello IQS Trade,

I need updates for:
- BL-2024-005: Payment status
- B/L 2024-006: CTN number

Please provide information for both.

Thanks,
Client"""
        }
    ]
    
    # Send alternative format emails
    for i, email_data in enumerate(alternative_emails, 1):
        try:
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = email_data['subject']
            msg.attach(MIMEText(email_data['body'], 'plain'))
            
            print(f"\n📧 Sending alternative email {i}: {email_data['subject']}")
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            print(f"✅ Alternative email {i} sent successfully!")
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ Failed to send alternative email {i}: {e}")
    
    print(f"\n🎉 Alternative format email sending completed!")

def main():
    """Main function"""
    print("📧 Fixed Email Sender - BL Number Compatible")
    print("=" * 40)
    
    print("\nChoose email type:")
    print("1. Fixed format emails (5 emails)")
    print("2. Alternative format emails (5 emails)")
    print("3. Both (10 emails total)")
    
    choice = input("\nEnter your choice (1/2/3): ")
    
    if choice == '1':
        send_fixed_test_emails()
    elif choice == '2':
        send_alternative_format_emails()
    elif choice == '3':
        send_fixed_test_emails()
        print("\n" + "="*50)
        send_alternative_format_emails()
    else:
        print("Invalid choice. Cancelled.")

if __name__ == "__main__":
    main() 