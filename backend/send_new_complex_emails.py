#!/usr/bin/env python3
"""
Send New Complex Email Templates Automatically
Uses real BL numbers from the database
"""

import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
load_dotenv(env_file)

def get_new_complex_emails():
    """Get the new complex email templates with real BL numbers"""
    
    # Real BL numbers from your database
    bl_numbers = [f"BL-2024-{i:03d}" for i in range(1, 21)]  # BL-2024-001 to BL-2024-020
    
    # Generate dummy Cloudinary links
    dummy_links = {}
    for bl in bl_numbers:
        dummy_links[bl] = {
            'invoice': f"http://dummy-invoice-{bl}.pdf",
            'receipt': f"http://dummy-receipt-{bl}.pdf", 
            'ctn': f"http://dummy-ctn-{bl}.pdf"
        }
    
    # Complex email templates using real BL numbers
    complex_emails = [
        {
            "subject": "Complex Test 1 - Mixed Payment Types (Real BLs)",
            "body": f"""Dear IQS Trade Team,

I need to make payments for multiple shipments:

1. {bl_numbers[0]}: USD 200 (full payment)
2. {bl_numbers[1]}: USD 170 (85% Allinpay)
3. {bl_numbers[2]}: USD 30 (15% reserve)

Please confirm receipt and send invoices. Also, what's the status of {bl_numbers[3]}?

Best regards,
Client""",
            "dummy_links": [dummy_links[bl_numbers[0]]['invoice'], dummy_links[bl_numbers[1]]['receipt'], dummy_links[bl_numbers[2]]['ctn']]
        },
        {
            "subject": "Complex Test 2 - Chinese + English Mixed (Real BLs)",
            "body": f"""Hello IQS Trade,

请问{bl_numbers[3]}和{bl_numbers[4]}的CTN号码是多少？

Also, I have paid $400 for {bl_numbers[5]}. Please confirm receipt and send invoice.

Thanks,
Client""",
            "dummy_links": [dummy_links[bl_numbers[3]]['ctn']]
        },
        {
            "subject": "Complex Test 3 - PDF with Multiple BLs (Real BLs)",
            "body": f"""Please process the attached payment receipt for multiple shipments:

- {bl_numbers[6]}: $200
- {bl_numbers[7]}: $170 (85%)
- {bl_numbers[8]}: $30 (reserve)

Please confirm and send updated invoices.

Regards,
Client""",
            "attachments": ["payment_receipt.pdf"],
            "dummy_links": [dummy_links[bl_numbers[6]]['receipt']]
        },
        {
            "subject": "Complex Test 4 - Underpayment Scenario (Real BLs)",
            "body": f"""Hi Team,

I'm sending payment for:
- {bl_numbers[8]}: $100 (should be $200 total)
- {bl_numbers[9]}: $150 (should be $200 total)

Please confirm receipt and let me know the outstanding amounts.

Thanks,
Client""",
            "dummy_links": [dummy_links[bl_numbers[8]]['invoice'], dummy_links[bl_numbers[9]]['receipt'], dummy_links[bl_numbers[10]]['ctn']]
        },
        {
            "subject": "Complex Test 5 - Allinpay Reserve Settlement (Real BLs)",
            "body": f"""Dear IQS Trade,

I need to settle the reserve for the following Allinpay shipments:

1. {bl_numbers[10]} - Reserve amount: $30
2. {bl_numbers[11]} - Reserve amount: $30
3. {bl_numbers[12]} - Reserve amount: $30

Please confirm the total reserve settlement amount and send confirmation.

Best regards,
Client"""
        },
        {
            "subject": "Complex Test 6 - Business Hours + Payment Methods (Real BLs)",
            "body": f"""Hi IQS Trade,

What are your business hours? Also, what payment methods do you accept?

I need to pay for {bl_numbers[13]} and {bl_numbers[14]}. Can you provide the total amounts?

Thanks,
Client"""
        },
        {
            "subject": "Complex Test 7 - CTN Processing Time (Real BLs)",
            "body": f"""Dear Team,

How long does it take to process CTN for {bl_numbers[15]}, {bl_numbers[16]}, and {bl_numbers[17]}?

Also, what's the status of {bl_numbers[18]}? I need to track the shipment.

Regards,
Client"""
        },
        {
            "subject": "Complex Test 8 - Invalid BL Mixed with Valid (Real BLs)",
            "body": f"""Hello,

I need information for:
- {bl_numbers[19]} (valid)
- BL-INVALID999 (invalid)
- BL-TEST123 (invalid)

Please provide status for the valid BL and ignore the invalid ones.

Thanks,
Client"""
        }
    ]
    
    return complex_emails, dummy_links

def send_complex_emails():
    """Send the new complex email templates"""
    
    # Email configuration
    sender_email = os.getenv('EMAIL_USERNAME')
    sender_password = os.getenv('EMAIL_PASSWORD')
    smtp_server = os.getenv('EMAIL_HOST')
    smtp_port = int(os.getenv('EMAIL_PORT', '587'))
    
    # Target email (where the ingestor monitors)
    target_email = os.getenv('EMAIL_USERNAME')  # Same email for testing
    
    if not all([sender_email, sender_password, smtp_server]):
        print("❌ Missing email configuration.")
        print("Please check your .env.local file has:")
        print("EMAIL_USERNAME=your-email@gmail.com")
        print("EMAIL_PASSWORD=your-app-password")
        print("EMAIL_HOST=smtp.gmail.com")
        return
    
    # Get complex emails
    complex_emails, dummy_links = get_new_complex_emails()
    
    print("🚀 Sending New Complex Email Templates")
    print("=" * 50)
    print(f"📧 From: {sender_email}")
    print(f"📧 To: {target_email}")
    print(f"📧 SMTP: {smtp_server}:{smtp_port}")
    print("=" * 50)
    
    # Send each email
    for i, email_data in enumerate(complex_emails, 1):
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = target_email
            msg['Subject'] = email_data['subject']
            
            # Add body
            body = email_data['body']
            msg.attach(MIMEText(body, 'plain'))
            
            # Add dummy links as text
            if 'dummy_links' in email_data:
                links_text = "\n\nDummy Links:\n"
                for link in email_data['dummy_links']:
                    links_text += f"- {link}\n"
                msg.attach(MIMEText(links_text, 'plain'))
            
            # Send email
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(sender_email, sender_password)
            
            text = msg.as_string()
            server.sendmail(sender_email, target_email, text)
            server.quit()
            
            print(f"✅ Email {i} sent: {email_data['subject']}")
            
            # Wait between emails to avoid rate limiting
            time.sleep(2)
            
        except Exception as e:
            print(f"❌ Failed to send email {i}: {e}")
    
    print("\n🎉 Complex email sending completed!")
    print(f"📊 Sent {len(complex_emails)} complex emails")
    print(f"📊 Used {len(dummy_links)} BL numbers")
    
    print("\n📋 Next Steps:")
    print("1. Check your email inbox")
    print("2. Monitor email_scheduler.log for processing")
    print("3. Check the customer_emails table in database")

def main():
    """Main function"""
    print("📧 New Complex Email Sender")
    print("=" * 30)
    
    # Confirm before sending
    response = input("Do you want to send 8 complex emails? (y/n): ")
    if response.lower() == 'y':
        send_complex_emails()
    else:
        print("Cancelled.")

if __name__ == "__main__":
    main() 