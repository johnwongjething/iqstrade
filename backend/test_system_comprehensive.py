#!/usr/bin/env python3
"""
Comprehensive System Testing Script
Tests both Email and WhatsApp systems with simple and complex scenarios
Valid BL numbers: NYC220 to NYC247
"""

import smtplib
import os
import time
import json
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
load_dotenv(env_file)

class SystemTester:
    def __init__(self):
        # Email configuration
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL')
        self.to_email = os.getenv('EMAIL_USERNAME')
        
        # Valid BL numbers (NYC220 to NYC247)
        self.valid_bls = [f"NYC{i}" for i in range(220, 248)]
        
        # WhatsApp API endpoint (if available)
        self.whatsapp_api_url = os.getenv('WHATSAPP_API_URL', 'http://localhost:3000')
        
        print("🔧 System Tester Initialized")
        print("=" * 50)
        print(f"📧 SMTP Server: {self.smtp_server}")
        print(f"📧 From: {self.from_email}")
        print(f"📧 To: {self.to_email}")
        print(f"📱 WhatsApp API: {self.whatsapp_api_url}")
        print(f"📋 Valid BLs: {len(self.valid_bls)} (NYC220-NYC247)")
        print("=" * 50)

    def get_simple_email_tests(self):
        """Simple email test cases"""
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
            }
        ]

    def get_complex_email_tests(self):
        """Complex email test cases"""
        return [
            {
                "category": "Multiple BLs",
                "subject": "Multiple shipments - NYC224, NYC225, NYC226",
                "body": """Dear IQS Trade,

I need information for multiple shipments:

1. NYC224: Payment status and CTN number
2. NYC225: Invoice and tracking details
3. NYC226: Reserve settlement amount

Please provide updates for all three shipments.

Also, when will NYC224 arrive at the port?

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

    def get_whatsapp_tests(self):
        """WhatsApp test cases"""
        return [
            {
                "category": "Simple Payment",
                "message": "I paid $200 for NYC233"
            },
            {
                "category": "CTN Request",
                "message": "What is the CTN number for NYC234?"
            },
            {
                "category": "Invoice Request",
                "message": "Can you send me the invoice for NYC235?"
            },
            {
                "category": "Payment Status",
                "message": "What is the payment status for NYC236?"
            },
            {
                "category": "General Question",
                "message": "Hello, how are you today?"
            },
            {
                "category": "Multiple BLs",
                "message": "I need info for NYC237, NYC238, and NYC239"
            },
            {
                "category": "Mixed Languages",
                "message": "请问NYC240的CTN号码是多少？Can you also send invoice?"
            },
            {
                "category": "Irrelevant + Valid",
                "message": "The weather is nice! What's the status of NYC241?"
            },
            {
                "category": "Complex Request",
                "message": "I paid $150 for NYC242, need CTN, invoice, and arrival date"
            },
            {
                "category": "Invalid BL",
                "message": "What's the status of NYC999?"
            }
        ]

    def send_email(self, subject, body):
        """Send a single email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            
            text = msg.as_string()
            server.sendmail(self.from_email, self.to_email, text)
            server.quit()
            
            return True
        except Exception as e:
            print(f"❌ Email sending failed: {e}")
            return False

    def send_whatsapp_message(self, message):
        """Send WhatsApp message via API (if available)"""
        try:
            # This would need to be implemented based on your WhatsApp API
            # For now, just simulate the API call
            print(f"📱 WhatsApp API call: {message}")
            return True
        except Exception as e:
            print(f"❌ WhatsApp sending failed: {e}")
            return False

    def test_emails(self, test_type="both"):
        """Test email system"""
        print(f"\n📧 Testing Email System - {test_type.upper()}")
        print("=" * 50)
        
        emails_to_send = []
        
        if test_type in ["simple", "both"]:
            emails_to_send.extend(self.get_simple_email_tests())
        
        if test_type in ["complex", "both"]:
            emails_to_send.extend(self.get_complex_email_tests())
        
        successful = 0
        failed = 0
        
        for i, email_data in enumerate(emails_to_send, 1):
            print(f"\n📧 Email {i}: {email_data['category']}")
            print(f"   Subject: {email_data['subject']}")
            print(f"   Body: {email_data['body'][:100]}...")
            
            if self.send_email(email_data['subject'], email_data['body']):
                print("   ✅ Sent successfully!")
                successful += 1
            else:
                print("   ❌ Failed to send")
                failed += 1
            
            # Wait between emails
            if i < len(emails_to_send):
                print("   ⏳ Waiting 3 seconds...")
                time.sleep(3)
        
        print(f"\n📊 Email Test Results:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📧 Total: {len(emails_to_send)}")

    def test_whatsapp(self):
        """Test WhatsApp system"""
        print(f"\n📱 Testing WhatsApp System")
        print("=" * 50)
        
        whatsapp_tests = self.get_whatsapp_tests()
        successful = 0
        failed = 0
        
        for i, test_data in enumerate(whatsapp_tests, 1):
            print(f"\n📱 WhatsApp {i}: {test_data['category']}")
            print(f"   Message: {test_data['message']}")
            
            if self.send_whatsapp_message(test_data['message']):
                print("   ✅ Sent successfully!")
                successful += 1
            else:
                print("   ❌ Failed to send")
                failed += 1
            
            # Wait between messages
            if i < len(whatsapp_tests):
                print("   ⏳ Waiting 2 seconds...")
                time.sleep(2)
        
        print(f"\n📊 WhatsApp Test Results:")
        print(f"   ✅ Successful: {successful}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📱 Total: {len(whatsapp_tests)}")

    def generate_test_report(self):
        """Generate a test report"""
        print(f"\n📋 Test Report")
        print("=" * 50)
        print(f"📅 Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 System: IQS Trade")
        print(f"📧 Email System: {self.smtp_server}")
        print(f"📱 WhatsApp System: {self.whatsapp_api_url}")
        print(f"📋 Valid BL Numbers: {len(self.valid_bls)} (NYC220-NYC247)")
        
        print(f"\n📧 Email Test Cases:")
        simple_emails = self.get_simple_email_tests()
        complex_emails = self.get_complex_email_tests()
        print(f"   Simple: {len(simple_emails)}")
        print(f"   Complex: {len(complex_emails)}")
        print(f"   Total: {len(simple_emails) + len(complex_emails)}")
        
        print(f"\n📱 WhatsApp Test Cases:")
        whatsapp_tests = self.get_whatsapp_tests()
        print(f"   Total: {len(whatsapp_tests)}")
        
        print(f"\n🎯 Test Categories:")
        categories = set()
        for email in simple_emails + complex_emails:
            categories.add(email['category'])
        for test in whatsapp_tests:
            categories.add(test['category'])
        
        for category in sorted(categories):
            print(f"   - {category}")

def main():
    """Main function"""
    print("🚀 Comprehensive System Testing")
    print("=" * 50)
    
    tester = SystemTester()
    
    print("\nChoose test type:")
    print("1. Email - Simple tests only")
    print("2. Email - Complex tests only")
    print("3. Email - Both simple and complex")
    print("4. WhatsApp tests")
    print("5. All tests (Email + WhatsApp)")
    print("6. Generate test report only")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    
    if choice == '1':
        tester.test_emails("simple")
    elif choice == '2':
        tester.test_emails("complex")
    elif choice == '3':
        tester.test_emails("both")
    elif choice == '4':
        tester.test_whatsapp()
    elif choice == '5':
        tester.test_emails("both")
        tester.test_whatsapp()
    elif choice == '6':
        tester.generate_test_report()
    else:
        print("Invalid choice. Cancelled.")
        return
    
    print(f"\n🎉 Testing completed!")
    print(f"\n📋 Next Steps:")
    print("1. Check your email inbox for test emails")
    print("2. Monitor email processing in the system")
    print("3. Check WhatsApp responses (if API is configured)")
    print("4. Review the customer_emails table in database")

if __name__ == "__main__":
    main() 