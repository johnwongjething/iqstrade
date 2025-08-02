#!/usr/bin/env python3
"""
Automated Email Sender for Testing Email Ingestor
Sends all 8 test emails to Gmail automatically
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
    sender_email = os.getenv('EMAIL_USERNAME')
    sender_password = os.getenv('EMAIL_PASSWORD')
    smtp_server = os.getenv('EMAIL_HOST')
    smtp_port = 587  # Standard TLS port
    
    if not all([sender_email, sender_password, smtp_server]):
        print("❌ Missing email configuration. Please set EMAIL_USERNAME, EMAIL_PASSWORD, and EMAIL_HOST in .env file")
        return
    
    # Test emails to send
    test_emails = [
        {
            "subject": "Fwd: 1 - CTN Request + Business Hours",
            "body": """Hello IQS Trade,

请问BL 001-123和BL 654321的CTN号码是多少？另外，请告知客户的营业时间。谢谢！

Best,
Client""",
            "attachments": []
        },
        {
            "subject": "Fwd: 2 - Fee Inquiry + Payment Status", 
            "body": """Hi Team,

Can you provide the total fees for BL 445566? Also, I need to track the shipment status. Is there any payment due? Please advise.

Thanks,
Alice""",
            "attachments": []
        },
        {
            "subject": "Fwd: 3 - Payment Receipt (Overpayment)",
            "body": """I have paid $500 for BL 777888, but the invoice total is $400. Please confirm the excess payment and send me the invoice. See attached payment receipt.

Regards,
Michael""",
            "attachments": []
        },
        {
            "subject": "Fwd: 4 - Multiple BL Fee Inquiry",
            "body": """Hi Team,

Can you provide the total fees for BL 001-123 NYC220? Also, I need to track the payment status? Is there any payment due?

Thanks,
Alice""",
            "attachments": []
        },
        {
            "subject": "Fwd: 5 - Payment Receipt (Bank Reference Test)",
            "body": """Payment for B/L 001-123, NYC220 Amount: $420 Ref: TEST987""",
            "attachments": []
        },
        {
            "subject": "Fwd: 6 - PDF Payment Receipt",
            "body": "",
            "attachments": ["3.pdf"]
        },
        {
            "subject": "Fwd: 7 - Complex Payment with Multiple BLs",
            "body": """Dear IQS Trade Team,

We have just transferred USD 320 for BL NYC220 and USD 200 for BL 001-123. Please confirm receipt and send us the invoices for both shipments. Also, let us know if there are any outstanding fees.

Best regards,
John Doe""",
            "attachments": []
        },
        {
            "subject": "Fwd: 8 - Invoice + CTN Request (Invalid BL Test)",
            "body": """can i have invoice and ctn number for bl number 001-123, NYC220, 445566""",
            "attachments": []
        }
    ]
    
    print("📧 Automated Email Sender for Testing")
    print("=" * 50)
    print(f"SMTP Server: {smtp_server}")
    print(f"Sender Email: {sender_email}")
    print(f"Target Email: {sender_email} (sending to self)")
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
            msg['To'] = sender_email  # Send to self for testing
            msg['Subject'] = email_data['subject']
            
            # Add body
            if email_data['body']:
                msg.attach(MIMEText(email_data['body'], 'plain'))
            
            # Add attachments if any
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
            
            # Send email
            text = msg.as_string()
            server.sendmail(sender_email, sender_email, text)
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
    except smtplib.SMTPException as e:
        print(f"❌ SMTP error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def create_test_pdf():
    """Create a simple test PDF for email 6"""
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        
        pdf_path = "test_payment_receipt.pdf"
        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(100, 750, "Test Payment Receipt")
        c.drawString(100, 730, "Payment for B/L 001-123, NYC220")
        c.drawString(100, 710, "Amount: $420")
        c.drawString(100, 690, "Reference: TEST987")
        c.save()
        print(f"✅ Created test PDF: {pdf_path}")
        return pdf_path
    except ImportError:
        print("⚠️  reportlab not installed. Skipping PDF creation.")
        return None
    except Exception as e:
        print(f"❌ Error creating PDF: {e}")
        return None

if __name__ == "__main__":
    # Create test PDF if needed
    pdf_path = create_test_pdf()
    
    # Update email 6 with PDF attachment if created
    if pdf_path:
        # This would be handled in the actual email sending
        pass
    
    # Send test emails
    send_test_emails() 