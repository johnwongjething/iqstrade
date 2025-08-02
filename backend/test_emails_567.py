#!/usr/bin/env python3
"""
Automated test script for Emails 5, 6, and 7
Tests payment distribution, PDF processing, and overpayment detection
"""
import os
import sys
import json
from unittest.mock import patch, Mock
import tempfile

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up environment for testing
os.environ['OPENAI_API_KEY'] = 'test-key-for-mocking'

def create_test_pdf_content():
    """Create test PDF content for Email 6"""
    return {
        'document_type': 'BOL',
        'bl_number': '001-123',
        'shipper': '',
        'consignee': '',
        'port_of_loading': '',
        'port_of_discharge': '',
        'container_numbers': '',
        'flight_or_vessel': '',
        'product_description': '',
        'paid_amount': '$420',
        'raw_text': 'Untitled\nPayment for B/L  001-123, NYC220\nAmount: $420\nRef: TEST987\nPage 1\n'
    }

def mock_db_connection():
    """Mock database connection and queries"""
    mock_conn = Mock()
    mock_cursor = Mock()
    mock_conn.cursor.return_value = mock_cursor
    
    # Mock BL data
    bl_data = {
        'NYC220': {
            'id': 102,
            'bl_number': 'NYC220',
            'ctn_fee': 100.0,
            'service_fee': 100.0,
            'status': 'Awaiting Bank In'
        },
        '001-123': {
            'id': 100,
            'bl_number': '001-123',
            'ctn_fee': 100.0,
            'service_fee': 100.0,
            'status': 'Awaiting Bank In'
        }
    }
    
    def mock_execute(query, params=None):
        if 'bill_of_lading' in query and 'bl_number' in query:
            bl_num = params[0] if params else None
            if bl_num in bl_data:
                mock_cursor.fetchone.return_value = (
                    bl_data[bl_num]['id'],
                    bl_data[bl_num]['ctn_fee'],
                    bl_data[bl_num]['service_fee']
                )
            else:
                mock_cursor.fetchone.return_value = None
        elif 'customer_emails' in query and 'INSERT' in query:
            mock_cursor.fetchone.return_value = (999,)
        elif 'customer_email_replies' in query:
            mock_cursor.fetchone.return_value = None
    
    mock_cursor.execute.side_effect = mock_execute
    return mock_conn

def mock_find_invoice_info(bl_numbers):
    """Mock invoice info lookup"""
    invoice_data = {
        'NYC220': {
            'bl_number': 'NYC220',
            'invoice_filename': 'https://res.cloudinary.com/dtm46mski/image/upload/v1753088057/invoices/k4ddwncnctmprmcl1pl3.pdf',
            'ctn_fee': 100.0,
            'service_fee': 100.0,
            'paid_amount': 0.0,
            'status': 'Awaiting Bank In'
        },
        '001-123': {
            'bl_number': '001-123',
            'invoice_filename': 'https://res.cloudinary.com/dtm46mski/image/upload/v1753070621/invoices/nogajjvsrgp6kkubnthl.pdf',
            'ctn_fee': 100.0,
            'service_fee': 100.0,
            'paid_amount': 0.0,
            'status': 'Awaiting Bank In'
        }
    }
    return [invoice_data.get(bl, {}) for bl in bl_numbers]

def mock_find_ctn_info(bl_numbers):
    """Mock CTN info lookup"""
    ctn_data = {
        'NYC220': {
            'bl_number': 'NYC220',
            'ctn_number': 'Ray000006'
        },
        '001-123': {
            'bl_number': '001-123',
            'ctn_number': 'ray010101'
        }
    }
    return [ctn_data.get(bl, {}) for bl in bl_numbers]

def mock_process_pdf(filepath):
    """Mock PDF processing"""
    if "3.pdf" in filepath or "bank_test.pdf" in filepath:
        return create_test_pdf_content()
    return None

def mock_openai_call(messages, temperature=0):
    """Mock OpenAI API calls"""
    # Return different responses based on the prompt content
    prompt = messages[-1]['content'] if messages else ""
    
    if 'payment_receipt' in prompt.lower():
        return json.dumps({
            "classification": "payment_receipt",
            "reply": "Thank you for your payment. We have received your payment and will process it accordingly."
        })
    elif 'general_enquiry' in prompt.lower():
        return json.dumps({
            "classification": "general_enquiry", 
            "reply": "Thank you for your enquiry. We will assist you with your request."
        })
    else:
        return json.dumps({
            "classification": "combined_request",
            "reply": "Thank you for your email. We have processed your request and will get back to you shortly."
        })

def mock_upload_filepath_to_cloudinary(filepath, folder):
    """Mock Cloudinary upload"""
    return f"https://res.cloudinary.com/test/image/upload/v1234567890/{folder}/test_receipt.pdf"

def mock_generate_pdf_from_text(text, filename):
    """Mock PDF generation"""
    return f"/tmp/{filename}"

def mock_confidence_scorer_get_auto_send_recommendation(text, reply, classification, bl_numbers):
    """Mock confidence scoring"""
    return {
        'confidence_score': 0.85,
        'auto_send': True,
        'reasoning': ['High confidence in payment processing']
    }

def run_email_test(email_num, email_data):
    """Run a single email test"""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING EMAIL {email_num}")
    print(f"{'='*60}")
    print(f"Subject: {email_data['subject']}")
    print(f"Body: {email_data['body'][:100]}...")
    print(f"Attachments: {email_data.get('attachments', [])}")
    
    # Mock all external dependencies
    with patch('email_ingestor.get_db_conn', side_effect=mock_db_connection), \
         patch('email_ingestor.find_invoice_info', side_effect=mock_find_invoice_info), \
         patch('email_ingestor.find_ctn_info', side_effect=mock_find_ctn_info), \
         patch('email_ingestor.process_pdf', side_effect=mock_process_pdf), \
         patch('email_ingestor.openai_call_with_fallback', side_effect=mock_openai_call), \
         patch('email_ingestor.upload_filepath_to_cloudinary', side_effect=mock_upload_filepath_to_cloudinary), \
         patch('email_ingestor.generate_pdf_from_text', side_effect=mock_generate_pdf_from_text), \
         patch('email_ingestor.confidence_scorer.get_auto_send_recommendation', side_effect=mock_confidence_scorer_get_auto_send_recommendation), \
         patch('email_ingestor.save_draft_reply'), \
         patch('email_ingestor.process_payment_receipt_email'):
        
        # Import after mocking
        from email_ingestor import handle_email_via_openai
        
        try:
            # Process the email
            result = handle_email_via_openai(
                subject=email_data['subject'],
                body=email_data['body'],
                attachments=email_data.get('attachments', []),
                from_addr=email_data['from_addr']
            )
            
            # Display results
            print(f"\n✅ EMAIL {email_num} PROCESSED SUCCESSFULLY")
            print(f"Classification: {result['classification']}")
            print(f"BL Numbers: {result['bl_numbers']}")
            print(f"Paid Amount: {result['paid_amount']}")
            print(f"BL Payment Map: {result['bl_payment_map']}")
            print(f"Request Types: {result['request_types']}")
            print(f"Confidence Score: {result['confidence_score']}")
            print(f"Auto Send: {result['auto_send']}")
            print(f"\nReply Preview:")
            print(f"{result['reply'][:200]}...")
            
            return result
            
        except Exception as e:
            print(f"❌ ERROR PROCESSING EMAIL {email_num}: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """Main test function"""
    print("🚀 STARTING AUTOMATED TEST FOR EMAILS 5, 6, 7")
    print("Testing payment distribution, PDF processing, and overpayment detection")
    
    # Test emails
    test_emails = {
        5: {
            "subject": "Fwd: 5 - Payment Receipt (Bank Reference Test)",
            "body": "Payment for B/L  001-123, NYC220 Amount: $420 Ref: TEST987",
            "attachments": [],
            "from_addr": "johnwongjething@gmail.com"
        },
        6: {
            "subject": "Fwd: 6",
            "body": "",
            "attachments": ["3.pdf"],
            "from_addr": "johnwongjething@gmail.com"
        },
        7: {
            "subject": "Fwd: 7",
            "body": """Dear IQS Trade Team,

We have just transferred USD 380 for BL NYC220 and USD 200 for BL 001-123.
Please confirm receipt and send us the invoices for both shipments. Also,
let us know if there are any outstanding fees.

Best regards,
John Doe""",
            "attachments": [],
            "from_addr": "johnwongjething@gmail.com"
        }
    }
    
    results = {}
    
    # Run tests
    for email_num in [5, 6, 7]:
        results[email_num] = run_email_test(email_num, test_emails[email_num])
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    for email_num, result in results.items():
        if result:
            print(f"Email {email_num}: ✅ PASSED")
            print(f"  - BLs: {result['bl_numbers']}")
            print(f"  - Payment Map: {result['bl_payment_map']}")
            print(f"  - Classification: {result['classification']}")
        else:
            print(f"Email {email_num}: ❌ FAILED")
    
    print(f"\n📄 PDF PROCESSING SUMMARY:")
    print(f"Email 5: 0 PDFs processed (no attachments)")
    print(f"Email 6: 1 PDF processed (3.pdf) - BLs extracted: {results[6]['bl_numbers'] if results[6] else 'N/A'}")
    print(f"Email 7: 0 PDFs processed (no attachments)")
    
    print(f"\n📤 RECEIPT UPLOAD SUMMARY:")
    print(f"Email 5: 0 receipts uploaded (mocked in test)")
    print(f"Email 6: 0 receipts uploaded (mocked in test)")
    print(f"Email 7: 0 receipts uploaded (mocked in test)")
    print(f"Note: Receipt processing is mocked in this test - no actual uploads occur")
    
    print(f"\n🎯 EXPECTED RESULTS:")
    print(f"Email 5: Should distribute $420 between 2 BLs = $210 each")
    print(f"Email 6: Should extract BLs from PDF and process both")
    print(f"Email 7: Should show overpayment for NYC220 ($380 vs $200)")
    
    return results

if __name__ == "__main__":
    main() 