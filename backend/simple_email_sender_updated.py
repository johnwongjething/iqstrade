#!/usr/bin/env python3
"""
Simple Email Sender - Updated with New BL Number Format
Uses BL2024XXX format (without dashes) to work with current regex
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

def get_simple_emails():
    """Get simple test emails with new BL number format"""
    return [
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
            "subject": "Simple Test 6 - Status Check for BL2024007",
            "body": """Dear IQS Trade,

What's the current status of BL2024007? I need to know if the payment has been processed.

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

def get_complex_emails():
    """Get complex test emails with new BL number format and dummy links"""
    return [
        {
            "subject": "Complex Test 1 - Mixed Payment Types (BL2024010, BL2024011)",
            "body": """Dear IQS Trade,

I need to make payments for multiple shipments:

1. BL2024010: USD 200 (full payment via bank transfer)
2. BL2024011: USD 170 (85% Allinpay payment)

Please confirm receipt and send invoices for both.

Best regards,
Client""",
            "attachments": ["http://dummy-invoice-BL2024010.pdf", "http://dummy-receipt-BL2024010.pdf"]
        },
        {
            "subject": "Complex Test 2 - Chinese + English (BL2024012)",
            "body": """Dear IQS Trade,

您好！我需要查询BL2024012的状态。

Hello! I need to check the status of BL2024012.

请问：
1. 付款是否已收到？
2. CTN号码是什么？
3. 何时可以提货？

Please provide:
1. Payment confirmation
2. CTN number
3. Pickup date

谢谢！
Thanks!
Client""",
            "attachments": ["http://dummy-invoice-BL2024012.pdf"]
        },
        {
            "subject": "Complex Test 3 - Underpayment Issue (BL2024013)",
            "body": """Hello IQS Trade,

I sent a payment of $150 for BL2024013, but the total amount should be $200.

I understand there's a $50 shortfall. Please let me know how to pay the remaining amount.

Thanks,
Client""",
            "attachments": ["http://dummy-receipt-BL2024013.pdf"]
        },
        {
            "subject": "Complex Test 4 - Allinpay Reserve Settlement (BL2024014)",
            "body": """Dear IQS Trade,

I want to settle the reserve amount for BL2024014. 

Current status: 85% paid ($170), 15% reserve ($30) remaining.

Please provide the settlement instructions and confirm the total amount.

Best regards,
Client""",
            "attachments": ["http://dummy-invoice-BL2024014.pdf", "http://dummy-ctn-BL2024014.pdf"]
        },
        {
            "subject": "Complex Test 5 - Business Hours Query (BL2024015)",
            "body": """Hi IQS Trade,

I need to arrange pickup for BL2024015. 

What are your business hours? Can I pick up the CTN after 6 PM?

Also, please confirm the pickup location and required documents.

Thanks,
Client""",
            "attachments": ["http://dummy-invoice-BL2024015.pdf"]
        }
    ]

def send_emails(emails_to_send):
    """Send emails using SMTP"""
    
    # Get SMTP settings from .env.local
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = os.getenv('FROM_EMAIL')
    to_email = os.getenv('EMAIL_USERNAME')
    
    print("🚀 Email Sender - New BL Number Format")
    print("=" * 50)
    print(f"📧 SMTP Server: {smtp_server}")
    print(f"📧 SMTP Port: {smtp_port}")
    print(f"📧 From: {from_email}")
    print(f"📧 To: {to_email}")
    print("=" * 50)
    
    # Send each email
    for i, email_data in enumerate(emails_to_send, 1):
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = email_data['subject']
            
            # Add body
            body = email_data['body']
            if 'attachments' in email_data:
                body += f"\n\nAttachments:\n"
                for attachment in email_data['attachments']:
                    body += f"- {attachment}\n"
            
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
    print(f"📊 Successfully sent {len(emails_to_send)} emails")
    
    print("\n📋 Next Steps:")
    print("1. Check your email inbox for the test emails")
    print("2. Start email scheduler: python email_scheduler.py")
    print("3. Monitor email processing in database")

def main():
    """Main function"""
    print("📧 Simple Email Sender - Updated with New BL Format")
    print("=" * 50)
    
    print("\nChoose email type:")
    print("1. Simple emails (8 emails)")
    print("2. Complex emails (5 emails)")
    print("3. Both (13 emails total)")
    
    choice = input("\nEnter your choice (1/2/3): ")
    
    if choice == '1':
        emails = get_simple_emails()
        send_emails(emails)
    elif choice == '2':
        emails = get_complex_emails()
        send_emails(emails)
    elif choice == '3':
        simple_emails = get_simple_emails()
        complex_emails = get_complex_emails()
        all_emails = simple_emails + complex_emails
        send_emails(all_emails)
    else:
        print("Invalid choice. Cancelled.")

if __name__ == "__main__":
    main() 