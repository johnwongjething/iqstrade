#!/usr/bin/env python3
"""
Auto Send 16 Test Emails
Sends all 8 complex test emails + 8 simple test emails to test the email ingestion system
"""
import smtplib
import os
import time
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
if not os.path.exists(env_file):
    env_file = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_file)

def send_test_emails():
    """Send all 16 test emails automatically"""
    
    # Email configuration
    sender_email = os.getenv('EMAIL_USERNAME')
    sender_password = os.getenv('EMAIL_PASSWORD')
    smtp_server = os.getenv('EMAIL_HOST')
    smtp_port = 587  # Standard TLS port
    
    # Target email (where the ingestor monitors)
    target_email = os.getenv('EMAIL_USERNAME')  # Same as sender for testing
    
    if not all([sender_email, sender_password, smtp_server]):
        print("❌ Missing email configuration. Please set EMAIL_USERNAME, EMAIL_PASSWORD, and EMAIL_HOST in .env file")
        return False
    
    print("🚀 Starting Auto-Send of 16 Test Emails")
    print("=" * 60)
    print(f"📧 From: {sender_email}")
    print(f"📧 To: {target_email}")
    print(f"📧 SMTP: {smtp_server}:{smtp_port}")
    print("=" * 60)
    
    # Complex test emails (from complex_email_tests.py)
    complex_test_emails = [
        {
            "type": "Complex",
            "number": 1,
            "subject": "Complex Test 1 - Mixed Payment Types",
            "body": """Dear IQS Trade Team,

I need to make payments for multiple shipments:

1. BL NAM20: USD 250 (partial payment)
2. BL 001-123: USD 200 (full payment) 
3. BL NYC220: USD 180 (overpayment)

Also, please provide CTN numbers for all three shipments and send invoices.

Best regards,
John Doe""",
            "attachments": []
        },
        {
            "type": "Complex",
            "number": 2,
            "subject": "Complex Test 2 - Chinese + English Mixed",
            "body": """Hello IQS Trade,

请问BL NAM20和BL 001-123的CTN号码是多少？

Also, I have paid $500 for BL NYC220. Please confirm receipt.

另外，请告知营业时间和付款方式。

Thanks,
John""",
            "attachments": []
        },
        {
            "type": "Complex",
            "number": 3,
            "subject": "Complex Test 3 - PDF with Multiple BLs",
            "body": "Please process the attached payment receipt for multiple shipments.",
            "attachments": ["3.pdf"]
        },
        {
            "type": "Complex",
            "number": 4,
            "subject": "Complex Test 4 - Underpayment Scenario",
            "body": """Hi Team,

I'm sending payment for:
- BL NAM20: $100 (should be $250 total)
- BL 001-123: $150 (should be $200 total)
- BL NYC220: $50 (should be $200 total)

Total sent: $300. Please confirm what's still due.

Thanks,
John""",
            "attachments": []
        },
        {
            "type": "Complex",
            "number": 5,
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
John""",
            "attachments": []
        },
        {
            "type": "Complex",
            "number": 6,
            "subject": "Complex Test 6 - Business Hours + Payment Methods",
            "body": """Hi IQS Trade,

What are your business hours? Also, what payment methods do you accept?

I need to pay for BL NAM20 ($250), BL 001-123 ($200), and BL NYC220 ($200).

Please provide payment instructions.

Thanks,
John""",
            "attachments": []
        },
        {
            "type": "Complex",
            "number": 7,
            "subject": "Complex Test 7 - CTN Processing Time",
            "body": """Dear Team,

How long does it take to process CTN for BL NAM20, BL 001-123, and BL NYC220?

Also, what are the total fees for each shipment?

Best regards,
John Doe""",
            "attachments": []
        },
        {
            "type": "Complex",
            "number": 8,
            "subject": "Complex Test 8 - Empty Body with PDF",
            "body": "",
            "attachments": ["3.pdf"]
        }
    ]
    
    # Simple test emails (from simple_email_sender.py)
    simple_test_emails = [
        {
            "type": "Simple",
            "number": 1,
            "subject": "Fwd: 1 - CTN Request + Business Hours",
            "body": """Hello IQS Trade,

请问BL 001-123和BL 654321的CTN号码是多少？另外，请告知客户的营业时间。谢谢！

Best,
Client""",
            "attachments": []
        },
        {
            "type": "Simple",
            "number": 2,
            "subject": "Fwd: 2 - Fee Inquiry + Payment Status", 
            "body": """Hi Team,

Can you provide the total fees for BL 445566? Also, I need to track the shipment status. Is there any payment due? Please advise.

Thanks,
Alice""",
            "attachments": []
        },
        {
            "type": "Simple",
            "number": 3,
            "subject": "Fwd: 3 - Payment Receipt (Overpayment)",
            "body": """I have paid $500 for BL 777888, but the invoice total is $400. Please confirm the excess payment and send me the invoice. See attached payment receipt.

Regards,
Michael""",
            "attachments": []
        },
        {
            "type": "Simple",
            "number": 4,
            "subject": "Fwd: 4 - Multiple BL Fee Inquiry",
            "body": """Hi Team,

Can you provide the total fees for BL 001-123 NYC220? Also, I need to track the payment status? Is there any payment due?

Thanks,
Alice""",
            "attachments": []
        },
        {
            "type": "Simple",
            "number": 5,
            "subject": "Fwd: 5 - Payment Receipt (Bank Reference Test)",
            "body": """Payment for B/L 001-123, NYC220 Amount: $420 Ref: TEST987""",
            "attachments": []
        },
        {
            "type": "Simple",
            "number": 6,
            "subject": "Fwd: 6 - PDF Payment Receipt",
            "body": "",
            "attachments": ["3.pdf"]
        },
        {
            "type": "Simple",
            "number": 7,
            "subject": "Fwd: 7 - Complex Payment with Multiple BLs",
            "body": """Dear IQS Trade Team,

We have just transferred USD 320 for BL NYC220 and USD 200 for BL 001-123. Please confirm receipt and send us the invoices for both shipments. Also, let us know if there are any outstanding fees.

Best regards,
John Doe""",
            "attachments": []
        },
        {
            "type": "Simple",
            "number": 8,
            "subject": "Fwd: 8 - Invoice + CTN Request (Invalid BL Test)",
            "body": """can i have invoice and ctn number for bl number 001-123, NYC220, 445566""",
            "attachments": []
        }
    ]
    
    # Combine all test emails
    all_test_emails = complex_test_emails + simple_test_emails
    
    # Connect to SMTP server
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        print("✅ Connected to SMTP server successfully")
    except Exception as e:
        print(f"❌ Failed to connect to SMTP server: {e}")
        return False
    
    # Send emails
    sent_count = 0
    failed_count = 0
    
    for i, email_data in enumerate(all_test_emails, 1):
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = target_email
            msg['Subject'] = f"[TEST {i:02d}] {email_data['subject']}"
            
            # Add body
            if email_data['body']:
                msg.attach(MIMEText(email_data['body'], 'plain'))
            
            # Add attachments if any
            for attachment in email_data['attachments']:
                attachment_path = os.path.join(os.path.dirname(__file__), attachment)
                if os.path.exists(attachment_path):
                    with open(attachment_path, "rb") as attachment_file:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(attachment_file.read())
                    
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename= {attachment}'
                    )
                    msg.attach(part)
                    print(f"   📎 Attached: {attachment}")
                else:
                    print(f"   ⚠️  Attachment not found: {attachment}")
            
            # Send email
            server.send_message(msg)
            sent_count += 1
            
            print(f"✅ [{i:02d}/16] {email_data['type']} Test {email_data['number']}: {email_data['subject']}")
            
            # Wait 2 seconds between emails to avoid rate limiting
            if i < len(all_test_emails):
                time.sleep(2)
                
        except Exception as e:
            failed_count += 1
            print(f"❌ [{i:02d}/16] Failed to send {email_data['type']} Test {email_data['number']}: {e}")
    
    # Close connection
    server.quit()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 EMAIL SENDING SUMMARY")
    print("=" * 60)
    print(f"📧 Total Emails: 16")
    print(f"✅ Successfully Sent: {sent_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📈 Success Rate: {(sent_count/16)*100:.1f}%")
    print(f"⏰ Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if sent_count > 0:
        print(f"\n🎯 Next Steps:")
        print(f"   1. Wait 1-2 minutes for emails to be processed")
        print(f"   2. Run: python retrieve_16_email_results.py")
        print(f"   3. Check the results in the database")
    
    return sent_count > 0

if __name__ == '__main__':
    success = send_test_emails()
    if success:
        print("\n🎉 Email sending completed successfully!")
    else:
        print("\n💥 Email sending failed!") 