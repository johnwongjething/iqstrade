"""
Complex Email Test Scenarios
Testing edge cases with multiple BL numbers: NAM20, 001-123, NYC220
"""
import os
import json
from unittest.mock import patch, MagicMock
import sys

# Add the backend directory to the path
sys.path.append(os.path.dirname(__file__))

def create_test_pdf_content():
    """Create mock PDF content for testing"""
    return {
        'document_type': 'BOL',
        'bl_number': 'NAM20, 001-123',
        'shipper': 'Test Shipper',
        'consignee': 'Test Consignee',
        'port_of_loading': 'Shanghai',
        'port_of_discharge': 'Los Angeles',
        'container_numbers': 'ABCD1234567',
        'flight_or_vessel': 'MSC FANTASIA',
        'product_description': 'Electronics',
        'paid_amount': '$750',
        'raw_text': 'Payment for B/L NAM20, 001-123\nAmount: $750\nRef: PAY123'
    }

def mock_db_connection():
    """Mock database connection"""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    def mock_execute(query, params=None):
        if 'INSERT INTO customer_emails' in query:
            mock_cursor.fetchone.return_value = (999,)
        elif 'SELECT id FROM customer_emails' in query:
            mock_cursor.fetchone.return_value = (999,)
        elif 'INSERT INTO customer_email_replies' in query:
            mock_cursor.fetchone.return_value = None
        return mock_cursor
    
    mock_cursor.execute = mock_execute
    return mock_conn

def mock_find_invoice_info(bl_numbers):
    """Mock invoice info lookup"""
    invoice_data = {
        'NAM20': {
            'bl_number': 'NAM20',
            'invoice_filename': 'https://res.cloudinary.com/dtm46mski/image/upload/v1753088057/invoices/nam20_invoice.pdf',
            'ctn_fee': 150.0,
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
        },
        'NYC220': {
            'bl_number': 'NYC220',
            'invoice_filename': 'https://res.cloudinary.com/dtm46mski/image/upload/v1753088057/invoices/k4ddwncnctmprmcl1pl3.pdf',
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
        'NAM20': {
            'bl_number': 'NAM20',
            'ctn_number': 'NAM000020'
        },
        '001-123': {
            'bl_number': '001-123',
            'ctn_number': 'ray010101'
        },
        'NYC220': {
            'bl_number': 'NYC220',
            'ctn_number': 'Ray000006'
        }
    }
    return [ctn_data.get(bl, {}) for bl in bl_numbers]

def mock_process_pdf(filepath):
    """Mock PDF processing"""
    if "complex_test.pdf" in filepath:
        return create_test_pdf_content()
    return None

def mock_openai_call(messages, temperature=0):
    """Mock OpenAI API calls"""
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

def run_complex_email_test(email_num, email_data):
    """Run a single complex email test"""
    print(f"\n{'='*70}")
    print(f"🧪 COMPLEX TEST EMAIL {email_num}")
    print(f"{'='*70}")
    print(f"Subject: {email_data['subject']}")
    print(f"Body: {email_data['body'][:150]}...")
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
            print(f"\n✅ COMPLEX EMAIL {email_num} PROCESSED SUCCESSFULLY")
            print(f"Classification: {result['classification']}")
            print(f"BL Numbers: {result['bl_numbers']}")
            print(f"Paid Amount: {result['paid_amount']}")
            print(f"BL Payment Map: {result['bl_payment_map']}")
            print(f"Request Types: {result['request_types']}")
            print(f"Confidence Score: {result['confidence_score']}")
            print(f"Auto Send: {result['auto_send']}")
            print(f"\nReply Preview:")
            print(f"{result['reply'][:300]}...")
            
            return result
            
        except Exception as e:
            print(f"❌ ERROR PROCESSING COMPLEX EMAIL {email_num}: {e}")
            import traceback
            traceback.print_exc()
            return None

def main():
    """Main complex test function"""
    print("🚀 STARTING COMPLEX EMAIL TESTS")
    print("Testing edge cases with multiple BL numbers: NAM20, 001-123, NYC220")
    
    # Complex test emails
    complex_test_emails = {
        1: {
            "subject": "Complex Test 1 - Mixed Payment Types",
            "body": """Dear IQS Trade Team,

I need to make payments for multiple shipments:

1. BL NAM20: USD 250 (partial payment)
2. BL 001-123: USD 200 (full payment) 
3. BL NYC220: USD 180 (overpayment)

Also, please provide CTN numbers for all three shipments and send invoices.

Best regards,
John Doe""",
            "attachments": [],
            "from_addr": "johnwongjething@gmail.com"
        },
        2: {
            "subject": "Complex Test 2 - Chinese + English Mixed",
            "body": """Hello IQS Trade,

请问BL NAM20和BL 001-123的CTN号码是多少？

Also, I have paid $500 for BL NYC220. Please confirm receipt.

另外，请告知营业时间和付款方式。

Thanks,
John""",
            "attachments": [],
            "from_addr": "johnwongjething@gmail.com"
        },
        3: {
            "subject": "Complex Test 3 - PDF with Multiple BLs",
            "body": "Please process the attached payment receipt for multiple shipments.",
            "attachments": ["complex_test.pdf"],
            "from_addr": "johnwongjething@gmail.com"
        },
        4: {
            "subject": "Complex Test 4 - Underpayment Scenario",
            "body": """Hi Team,

I'm sending payment for:
- BL NAM20: $100 (should be $250 total)
- BL 001-123: $150 (should be $200 total)
- BL NYC220: $50 (should be $200 total)

Total sent: $300. Please confirm what's still due.

Thanks,
John""",
            "attachments": [],
            "from_addr": "johnwongjething@gmail.com"
        },
        5: {
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
            "attachments": [],
            "from_addr": "johnwongjething@gmail.com"
        },
        6: {
            "subject": "Complex Test 6 - Business Hours + Payment Methods",
            "body": """Hi IQS Trade,

What are your business hours? Also, what payment methods do you accept?

I need to pay for BL NAM20 ($250), BL 001-123 ($200), and BL NYC220 ($200).

Please provide payment instructions.

Thanks,
John""",
            "attachments": [],
            "from_addr": "johnwongjething@gmail.com"
        },
        7: {
            "subject": "Complex Test 7 - CTN Processing Time",
            "body": """Dear Team,

How long does it take to process CTN for BL NAM20, BL 001-123, and BL NYC220?

Also, what are the total fees for each shipment?

Best regards,
John Doe""",
            "attachments": [],
            "from_addr": "johnwongjething@gmail.com"
        },
        8: {
            "subject": "Complex Test 8 - Empty Body with PDF",
            "body": "",
            "attachments": ["complex_test.pdf"],
            "from_addr": "johnwongjething@gmail.com"
        }
    }
    
    results = {}
    
    # Run complex tests
    for email_num in range(1, 9):
        results[email_num] = run_complex_email_test(email_num, complex_test_emails[email_num])
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 COMPLEX TEST SUMMARY")
    print(f"{'='*70}")
    
    for email_num, result in results.items():
        if result:
            print(f"Complex Email {email_num}: ✅ PASSED")
            print(f"  - BLs: {result['bl_numbers']}")
            print(f"  - Payment Map: {result['bl_payment_map']}")
            print(f"  - Classification: {result['classification']}")
            print(f"  - Request Types: {result['request_types']}")
        else:
            print(f"Complex Email {email_num}: ❌ FAILED")
    
    print(f"\n🎯 COMPLEX TEST SCENARIOS:")
    print(f"Email 1: Mixed payment types (partial, full, overpayment)")
    print(f"Email 2: Chinese + English mixed language")
    print(f"Email 3: PDF with multiple BLs")
    print(f"Email 4: Underpayment scenario")
    print(f"Email 5: Invalid BLs mixed with valid")
    print(f"Email 6: Business hours + payment methods")
    print(f"Email 7: CTN processing time inquiry")
    print(f"Email 8: Empty body with PDF attachment")
    
    return results

if __name__ == "__main__":
    main() 