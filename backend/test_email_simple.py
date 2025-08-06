#!/usr/bin/env python3
"""
Simple Email Testing Script
Uses existing email sending functionality to test the email system
Valid BL numbers: NYC220 to NYC247
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

def get_test_emails():
    """Get test emails with valid BL numbers (NYC220 to NYC247)"""
    return [
        {
            "category": "Simple Payment",
            "subject": "Payment for NYC220",
            "body": """Dear IQS Trade,

I have paid $200 for NYC220. Please confirm receipt.

Thanks,
Client"""
        },
        {
            "category": "CTN Request",
            "subject": "CTN number for NYC221",
            "body": """Hello IQS Trade,

请问NYC221的CTN号码是多少？

Thanks,
Client"""
        },
        {
            "category": "Invoice Request",
            "subject": "Invoice for NYC222",
            "body": """Hi IQS Trade,

Can you send me the invoice for NYC222?

Best regards,
Client"""
        },
        {
            "category": "Payment Status",
            "subject": "Payment status NYC223",
            "body": """Dear Team,

What is the payment status for NYC223?

Regards,
Client"""
        },
        {
            "category": "General Enquiry",
            "subject": "General question",
            "body": """Hello IQS Trade,

I have a general question about shipping procedures.

Thanks,
Client"""
        },
        {
            "category": "Multiple BLs",
            "subject": "Multiple shipments - NYC224, NYC225, NYC226",
            "body": """Dear IQS Trade,

I need information for multiple shipments:

1. NYC224: Payment status and CTN number
2. NYC225: Invoice and tracking details
3. NYC226: Reserve settlement amount

Please provide updates for all three shipments.

Best regards,
Client"""
        },
        {
            "category": "Mixed Languages",
            "subject": "Mixed language request - NYC227",
            "body": """Hello IQS Trade,

请问NYC227的CTN号码是多少？
Can you also send me the invoice for this shipment?

另外，什么时候可以安排提货？
When will the container be available for pickup?

Thanks,
谢谢,
Client"""
        },
        {
            "category": "Irrelevant + Valid",
            "subject": "Weather and shipment - NYC228",
            "body": """Hi IQS Trade,

The weather is really nice today! 
I hope you're having a good day.

By the way, I need the CTN number for NYC228.
Also, what's the current status of this shipment?

Have a great day!
Client"""
        },
        {
            "category": "Complex Payment",
            "subject": "Partial payment and reserve - NYC229",
            "body": """Dear IQS Trade,

I have made a partial payment of $150 for NYC229.
The total amount is $200, so I still owe $50.

Can you confirm the payment receipt?
Also, what is the reserve amount for this shipment?

I will settle the remaining amount next week.

Thanks,
Client"""
        },
        {
            "category": "Multiple Requests",
            "subject": "Various requests - NYC230",
            "body": """Hello IQS Trade,

I have several questions about NYC230:

1. What is the CTN number?
2. Can you send the invoice?
3. What is the payment status?
4. When will it arrive at the port?
5. How much is the reserve amount?

Please provide all this information.

Also, I need to know about NYC231 and NYC232 as well.

Thanks,
Client"""
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
    
    print("🚀 Simple Email Testing")
    print("=" * 50)
    print(f"📧 SMTP Server: {smtp_server}")
    print(f"📧 SMTP Port: {smtp_port}")
    print(f"📧 From: {from_email}")
    print(f"📧 To: {to_email}")
    print("=" * 50)
    
    if not all([smtp_server, smtp_username, smtp_password, from_email, to_email]):
        print("❌ Missing email configuration. Please check your .env.local file")
        return
    
    # Send each email
    successful = 0
    failed = 0
    
    for i, email_data in enumerate(emails_to_send, 1):
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
            print(f"\n📧 Sending email {i}: {email_data['category']}")
            print(f"   Subject: {email_data['subject']}")
            print(f"   Body: {email_data['body'][:100]}...")
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_username, smtp_password)
            
            text = msg.as_string()
            server.sendmail(from_email, to_email, text)
            server.quit()
            
            print(f"   ✅ Email {i} sent successfully!")
            successful += 1
            
            # Wait between emails to avoid rate limiting
            if i < len(emails_to_send):
                print("   ⏳ Waiting 3 seconds...")
                time.sleep(3)
            
        except Exception as e:
            print(f"   ❌ Failed to send email {i}: {e}")
            failed += 1
    
    print(f"\n📊 Email Test Results:")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📧 Total: {len(emails_to_send)}")
    
    print(f"\n🎉 Email testing completed!")
    print(f"\n📋 Next Steps:")
    print("1. Check your email inbox for the test emails")
    print("2. Start email scheduler: python email_scheduler.py")
    print("3. Monitor email processing in database")
    print("4. Check the customer_emails table for processed emails")

def main():
    """Main function"""
    print("📧 Simple Email Testing")
    print("=" * 50)
    
    # Get test emails
    test_emails = get_test_emails()
    
    print(f"📋 Test Emails: {len(test_emails)}")
    print("Categories:")
    for email in test_emails:
        print(f"   - {email['category']}")
    
    print(f"\nValid BL Numbers: NYC220 to NYC247")
    
    # Ask for confirmation
    response = input(f"\nSend {len(test_emails)} test emails? (y/n): ").strip().lower()
    
    if response in ['y', 'yes']:
        send_emails(test_emails)
    else:
        print("Cancelled.")

if __name__ == "__main__":
    main() 