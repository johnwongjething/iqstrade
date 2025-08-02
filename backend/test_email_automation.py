#!/usr/bin/env python3
"""
Automated test script for email ingestor
Simulates processing of test emails without requiring actual IMAP connection
"""

import sys
import os
import json
import datetime
from unittest.mock import Mock, patch

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def simulate_email_processing():
    """Simulate email processing for test emails"""
    
    # Test emails from the user
    test_emails = [
        {
            "subject": "Fwd: 1", 
            "body": "Hello IQS Trade,:\n\n\n请问BL 001-123和BL 654321的CTN号码是多少？另外，请告知客户的营业时间。谢谢！\n\nBest,\nClient", 
            "attachments": [], 
            "from_addr": "johnwongjething@gmail.com"
        },
        {
            "subject": "Fwd: 2", 
            "body": "Hi Team,\nCan you provide the total fees for BL 445566? Also, I need to track the shipment status. Is there any payment due? Please advise.\nThanks,\nAlice", 
            "attachments": [], 
            "from_addr": "johnwongjething@gmail.com"
        },
        {
            "subject": "Fwd: 3", 
            "body": "I have paid $500 for BL 777888, but the invoice total is $400. Please confirm the excess payment and send me the invoice. See attached payment receipt.\nRegards,\nMichael", 
            "attachments": [], 
            "from_addr": "johnwongjething@gmail.com"
        },
        {
            "subject": "Fwd: 4", 
            "body": "Hi Team,\nCan you provide the total fees for BL 001-123 NYC220? Also, I need to track the payment status? Is there any payment due?\nThanks,\nAlice", 
            "attachments": [], 
            "from_addr": "johnwongjething@gmail.com"
        },
        {
            "subject": "Fwd: 5", 
            "body": "Payment for B/L 001-123, NYC220 Amount: $420 Ref: TEST987", 
            "attachments": [], 
            "from_addr": "johnwongjething@gmail.com"
        },
        {
            "subject": "Fwd: 6", 
            "body": "", 
            "attachments": ["3.pdf"], 
            "from_addr": "johnwongjething@gmail.com"
        },
        {
            "subject": "Fwd: 7", 
            "body": "Dear IQS Trade Team,\nWe have just transferred USD 320 for BL NYC220 and USD 200 for BL 001-123. Please confirm receipt and send us the invoices for both shipments. Also, let us know if there are any outstanding fees.\nBest regards,\nJohn Doe", 
            "attachments": ["path/to/payment_receipt.pdf"], 
            "from_addr": "johnwongjething@gmail.com"
        },
        {
            "subject": "Fwd: 8", 
            "body": "can i have invoice and ctn number for bl number 001-123, NYC220, 445566", 
            "attachments": [], 
            "from_addr": "johnwongjething@gmail.com"
        }
    ]

    print("🤖 Automated Email Ingestor Test")
    print("=" * 60)
    print(f"Testing {len(test_emails)} emails...\n")

    # Mock database responses for testing
    mock_db_data = {
        "001-123": {
            "ctn": "CTN001123",
            "invoice_link": "https://cloudinary.com/invoice_001123.pdf",
            "ctn_fee": 200.0,
            "service_fee": 50.0,
            "paid_amount": 0.0
        },
        "NYC220": {
            "ctn": "CTNNYC220", 
            "invoice_link": "https://cloudinary.com/invoice_NYC220.pdf",
            "ctn_fee": 250.0,
            "service_fee": 60.0,
            "paid_amount": 0.0
        }
    }

    # Set up environment variables for testing
    os.environ['OPENAI_API_KEY'] = 'test-key-for-mocking'
    
    # Mock functions
    def mock_find_ctn_info(bl_numbers):
        return [{"bl_number": bl, "ctn_number": mock_db_data[bl]["ctn"]} 
                for bl in bl_numbers if bl in mock_db_data]
    
    def mock_find_invoice_info(bl_numbers):
        return [{"bl_number": bl, **mock_db_data[bl]} 
                for bl in bl_numbers if bl in mock_db_data]
    
    def mock_process_pdf(filepath):
        # Simulate PDF processing for test emails 5 and 6
        if "3.pdf" in filepath or "bank_test.pdf" in filepath:
            return {
                "bl_number": "001-123, NYC220",
                "paid_amount": 420.0,
                "raw_text": "Payment for B/L 001-123, NYC220 Amount: $420 Ref: TEST987"
            }
        elif "payment_receipt.pdf" in filepath:
            return {
                "bl_number": "NYC220, 001-123", 
                "paid_amount": 520.0,
                "raw_text": "USD 320 for BL NYC220 and USD 200 for BL 001-123"
            }
        return {"raw_text": ""}

    def mock_openai_chat_completions_create(**kwargs):
        # Simulate OpenAI responses based on request types
        messages = kwargs.get('messages', [])
        user_content = ""
        for msg in messages:
            if msg['role'] == 'user':
                user_content = msg['content']
                break
        
        # Generate appropriate response based on content
        if "CTN号码" in user_content or "ctn number" in user_content.lower():
            reply = "Hello,\n\nCTN numbers:\n- BL 001-123: CTN number is CTN001123\n- BL 654321: This BL number was not found in our system, please verify and query again\n\nBusiness hours: Monday to Friday, 9:00 AM to 5:00 PM (Hong Kong time)\n\nBest regards,\nIQS Trade Team"
        elif "total fees" in user_content.lower() or "payment status" in user_content.lower():
            reply = "Hello,\n\nFee details:\n- BL 445566: CTN fee $300.00, service fee $75.00, total $375.00\n\nPayment status:\n- BL 445566: Total fee $375.00, paid $0.00, status: Due $375.00\n\nBest regards,\nIQS Trade Team"
        elif "payment" in user_content.lower() and "receipt" in user_content.lower():
            reply = "Hello,\n\nPayment confirmation:\n- BL 777888: Payment record received\n\nNote: We have received your payment of $500.00, but the invoice amount is $400.00. We will contact you regarding the excess payment of $100.00.\n\nBest regards,\nIQS Trade Team"
        else:
            reply = "Hello,\n\nThank you for your email. We have processed your request.\n\nBest regards,\nIQS Trade Team"
        
        return Mock(
            choices=[Mock(message=Mock(content=reply))]
        )

    # Patch the necessary functions
    with patch('email_ingestor.find_ctn_info', side_effect=mock_find_ctn_info), \
         patch('email_ingestor.find_invoice_info', side_effect=mock_find_invoice_info), \
         patch('email_ingestor.process_pdf', side_effect=mock_process_pdf), \
         patch('openai.chat.completions.create', side_effect=mock_openai_chat_completions_create), \
         patch('email_ingestor.save_draft_reply'), \
         patch('email_ingestor.process_payment_receipt_email'):
        
        try:
            from email_ingestor import handle_email_via_openai
            
            results = []
            for i, email in enumerate(test_emails, 1):
                print(f"📧 Processing Email {i}: {email['subject']}")
                print(f"   From: {email['from_addr']}")
                print(f"   Body: {email['body'][:100]}...")
                print(f"   Attachments: {len(email['attachments'])}")
                
                try:
                    # Process the email
                    result = handle_email_via_openai(
                        email['subject'], 
                        email['body'], 
                        email['attachments'], 
                        email['from_addr']
                    )
                    
                    print(f"   ✅ Classification: {result.get('classification', 'N/A')}")
                    print(f"   ✅ Request Types: {result.get('request_types', [])}")
                    print(f"   ✅ Extracted BLs: {result.get('bl_numbers', [])}")
                    print(f"   ✅ Valid BLs: {list(result.get('bl_payment_map', {}).keys())}")
                    print(f"   ✅ Paid Amount: {result.get('paid_amount', 'N/A')}")
                    print(f"   ✅ Reply Preview: {result.get('reply', '')[:100]}...")
                    
                    results.append({
                        'email_id': i,
                        'subject': email['subject'],
                        'result': result
                    })
                    
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    results.append({
                        'email_id': i,
                        'subject': email['subject'],
                        'error': str(e)
                    })
                
                print("-" * 60)
            
            # Generate summary report
            print("\n📊 SUMMARY REPORT")
            print("=" * 60)
            
            successful = len([r for r in results if 'result' in r])
            failed = len([r for r in results if 'error' in r])
            
            print(f"✅ Successful: {successful}")
            print(f"❌ Failed: {failed}")
            print(f"📈 Success Rate: {(successful/len(results)*100):.1f}%")
            
            # Save detailed results to file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_results_{timestamp}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n📄 Detailed results saved to: {output_file}")
            print("\n🎉 Automated testing completed!")
            
        except ImportError as e:
            print(f"❌ Import error: {e}")
            print("Make sure you're running this from the backend directory")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    simulate_email_processing() 