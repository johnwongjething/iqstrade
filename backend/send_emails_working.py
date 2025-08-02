#!/usr/bin/env python3
"""
Working Email Sender - Uses correct SMTP settings
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

def send_test_emails():
    """Send test emails using correct SMTP settings"""
    
    # Get SMTP settings from .env.local
    smtp_server = os.getenv('SMTP_SERVER')  # smtp-relay.brevo.com
    smtp_port = int(os.getenv('SMTP_PORT', '587'))  # 587
    smtp_username = os.getenv('SMTP_USERNAME')  # 8ff19f001@smtp-brevo.com
    smtp_password = os.getenv('SMTP_PASSWORD')  # 01smLzJnjcr4BDxM
    from_email = os.getenv('FROM_EMAIL')  # ray6330099@gmail.com
    to_email = os.getenv('EMAIL_USERNAME')  # ray6330088@gmail.com
    
    print("🚀 Working Email Sender")
    print("=" * 50)
    print(f"📧 SMTP Server: {smtp_server}")
    print(f"📧 SMTP Port: {smtp_port}")
    print(f"📧 SMTP Username: {smtp_username}")
    print(f"📧 From: {from_email}")
    print(f"📧 To: {to_email}")
    print("=" * 50)
    
    # Test emails
    test_emails = [
        {
            "subject": "Test 1 - Simple Payment (BL-2024-001)",
            "body": """Dear IQS Trade,

I have paid $200 for BL-2024-001. Please confirm receipt and send invoice.

Thanks,
Client"""
        },
        {
            "subject": "Test 2 - Allinpay 85% (BL-2024-002)",
            "body": """Hello IQS Trade,

I have paid $170 (85%) for BL-2024-002 via Allinpay. When can I settle the remaining $30?

Best regards,
Client"""
        },
        {
            "subject": "Test 3 - Chinese + English (BL-2024-003)",
            "body": """Hi IQS Trade,

请问BL-2024-003的CTN号码是多少？

Also, I need to track the shipment status.

Thanks,
Client"""
        },
        {
            "subject": "Test 4 - Multiple BLs (BL-2024-004, BL-2024-005)",
            "body": """Dear Team,

I need information for:
- BL-2024-004: Payment status
- BL-2024-005: CTN number

Please provide updates for both shipments.

Regards,
Client"""
        },
        {
            "subject": "Test 5 - Reserve Settlement (BL-2024-006)",
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
            
            # Wait between emails
            time.sleep(3)
            
        except Exception as e:
            print(f"❌ Failed to send email {i}: {e}")
            print(f"   Error details: {type(e).__name__}")
    
    print(f"\n🎉 Email sending completed!")
    print(f"📊 Attempted to send {len(test_emails)} emails")
    
    print("\n📋 Next Steps:")
    print("1. Check your email inbox for the test emails")
    print("2. Start email scheduler: python email_scheduler.py")
    print("3. Monitor email processing")

def main():
    """Main function"""
    print("📧 Working Email Sender")
    print("=" * 30)
    
    # Confirm before sending
    response = input("Do you want to send 5 test emails? (y/n): ")
    if response.lower() == 'y':
        send_test_emails()
    else:
        print("Cancelled.")

if __name__ == "__main__":
    main() 