#!/usr/bin/env python3
"""
Test script for email_ingestor_working.py scenarios
Tests all the different email types to ensure AI content extraction works correctly
"""

import sys
import os
import json
import logging
from unittest.mock import Mock, patch, MagicMock

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_scenario_1_new_email_plain_text():
    """Test: New email from customer - plain text enquiry"""
    print("\n" + "="*60)
    print("SCENARIO 1: New email from customer - plain text enquiry")
    print("="*60)
    
    subject = "CTN Number Request"
    body = """
    Hello,
    
    I need the CTN number for BL-001-123. Can you please provide it?
    
    Best regards,
    Customer
    """
    attachments = []
    from_addr = "customer@example.com"
    
    # Mock the AI function to return the same content (no quoted content to remove)
    with patch('email_ingestor_working.extract_new_content_from_reply') as mock_extract:
        mock_extract.return_value = body.strip()
        
        # Import and test
        from email_ingestor_working import handle_email_via_openai
        
        try:
            result = handle_email_via_openai(subject, body, attachments, from_addr)
            print(f"✅ SUCCESS: New email processed")
            print(f"   Classification: {result.get('classification')}")
            print(f"   BL Numbers: {result.get('bl_numbers')}")
            print(f"   Request Types: {result.get('request_types')}")
            print(f"   Reply Length: {len(result.get('reply', ''))}")
            
            # Verify no old content was processed
            assert 'BL-001-123' in result.get('bl_numbers', []), "BL number should be extracted"
            assert 'ctn_request' in result.get('request_types', []), "Should be classified as CTN request"
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    return True

def test_scenario_2_new_email_text_bank_transfer():
    """Test: New email from customer - text based bank transfer"""
    print("\n" + "="*60)
    print("SCENARIO 2: New email from customer - text based bank transfer")
    print("="*60)
    
    subject = "Payment Confirmation"
    body = """
    Hi,
    
    I have made a payment of $420 for BL-001-123.
    Transaction ID: TXN123456
    Bank: ABC Bank
    
    Please confirm receipt.
    """
    attachments = []
    from_addr = "customer@example.com"
    
    with patch('email_ingestor_working.extract_new_content_from_reply') as mock_extract:
        mock_extract.return_value = body.strip()
        
        from email_ingestor_working import handle_email_via_openai
        
        try:
            result = handle_email_via_openai(subject, body, attachments, from_addr)
            print(f"✅ SUCCESS: Text-based payment processed")
            print(f"   Classification: {result.get('classification')}")
            print(f"   BL Numbers: {result.get('bl_numbers')}")
            print(f"   Paid Amount: {result.get('paid_amount')}")
            print(f"   Request Types: {result.get('request_types')}")
            
            # Verify payment information was extracted
            assert 'BL-001-123' in result.get('bl_numbers', []), "BL number should be extracted"
            assert result.get('paid_amount') == 420.0, "Payment amount should be extracted"
            assert 'payment_receipt' in result.get('request_types', []), "Should be classified as payment receipt"
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    return True

def test_scenario_3_new_email_pdf_bank_transfer():
    """Test: New email from customer - pdf based bank transfer"""
    print("\n" + "="*60)
    print("SCENARIO 3: New email from customer - pdf based bank transfer")
    print("="*60)
    
    subject = "Payment Receipt"
    body = "Please find attached payment receipt."  # Minimal body text
    attachments = ["payment_receipt.pdf"]
    from_addr = "customer@example.com"
    
    # Mock PDF processing to return BL and payment info
    with patch('email_ingestor_working.extract_new_content_from_reply') as mock_extract:
        with patch('email_ingestor_working.extract_bl_specific_payments') as mock_bl_payments:
            with patch('email_ingestor_working.extract_all_payment_amounts') as mock_payment:
                
                mock_extract.return_value = body.strip()
                mock_bl_payments.return_value = {'BL-001-123': 420.0}
                mock_payment.return_value = 420.0
                
                from email_ingestor_working import handle_email_via_openai
                
                try:
                    result = handle_email_via_openai(subject, body, attachments, from_addr)
                    print(f"✅ SUCCESS: PDF-based payment processed")
                    print(f"   Classification: {result.get('classification')}")
                    print(f"   BL Numbers: {result.get('bl_numbers')}")
                    print(f"   Paid Amount: {result.get('paid_amount')}")
                    print(f"   Request Types: {result.get('request_types')}")
                    
                    # Verify attachment processing worked
                    assert 'BL-001-123' in result.get('bl_numbers', []), "BL number should be extracted from PDF"
                    assert result.get('paid_amount') == 420.0, "Payment amount should be extracted from PDF"
                    assert 'payment_receipt' in result.get('request_types', []), "Should be classified as payment receipt"
                    
                except Exception as e:
                    print(f"❌ ERROR: {e}")
                    return False
    
    return True

def test_scenario_4_customer_reply_plain_text():
    """Test: New email from customer reply from our last email - plain text enquiry"""
    print("\n" + "="*60)
    print("SCENARIO 4: Customer reply from our last email - plain text enquiry")
    print("="*60)
    
    subject = "Re: CTN Number Request"
    body = """
    On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:
    > Hello,
    > 
    > We have received your request for CTN number for BL-001-123.
    > 
    > Best regards,
    > Support Team
    
    Thank you for the quick response. I also need the CTN for BL-001-124.
    """
    attachments = []
    from_addr = "customer@example.com"
    
    # Mock AI to extract only the new content
    with patch('email_ingestor_working.extract_new_content_from_reply') as mock_extract:
        mock_extract.return_value = "Thank you for the quick response. I also need the CTN for BL-001-124."
        
        from email_ingestor_working import handle_email_via_openai
        
        try:
            result = handle_email_via_openai(subject, body, attachments, from_addr)
            print(f"✅ SUCCESS: Customer reply processed")
            print(f"   Classification: {result.get('classification')}")
            print(f"   BL Numbers: {result.get('bl_numbers')}")
            print(f"   Request Types: {result.get('request_types')}")
            print(f"   Reply Length: {len(result.get('reply', ''))}")
            
            # Verify only new BL was extracted, not old quoted BL
            assert 'BL-001-124' in result.get('bl_numbers', []), "New BL number should be extracted"
            assert 'BL-001-123' not in result.get('bl_numbers', []), "Old quoted BL should NOT be extracted"
            assert 'ctn_request' in result.get('request_types', []), "Should be classified as CTN request"
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    return True

def test_scenario_5_customer_reply_text_bank_transfer():
    """Test: New email from customer reply from our last email - text based bank transfer"""
    print("\n" + "="*60)
    print("SCENARIO 5: Customer reply from our last email - text based bank transfer")
    print("="*60)
    
    subject = "Re: Payment Request"
    body = """
    On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:
    > Hello,
    > 
    > Please find attached invoice for BL-001-123.
    > Amount: $420
    > 
    > Best regards,
    > Support Team
    
    I have made the payment of $420 for BL-001-123.
    Transaction ID: TXN789012
    """
    attachments = []
    from_addr = "customer@example.com"
    
    with patch('email_ingestor_working.extract_new_content_from_reply') as mock_extract:
        mock_extract.return_value = "I have made the payment of $420 for BL-001-123.\nTransaction ID: TXN789012"
        
        from email_ingestor_working import handle_email_via_openai
        
        try:
            result = handle_email_via_openai(subject, body, attachments, from_addr)
            print(f"✅ SUCCESS: Customer reply with payment processed")
            print(f"   Classification: {result.get('classification')}")
            print(f"   BL Numbers: {result.get('bl_numbers')}")
            print(f"   Paid Amount: {result.get('paid_amount')}")
            print(f"   Request Types: {result.get('request_types')}")
            
            # Verify only new payment info was extracted
            assert 'BL-001-123' in result.get('bl_numbers', []), "BL number should be extracted"
            assert result.get('paid_amount') == 420.0, "Payment amount should be extracted"
            assert 'payment_receipt' in result.get('request_types', []), "Should be classified as payment receipt"
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    return True

def test_scenario_6_customer_reply_pdf_bank_transfer():
    """Test: New email from customer reply from our last email - pdf based bank transfer"""
    print("\n" + "="*60)
    print("SCENARIO 6: Customer reply from our last email - pdf based bank transfer")
    print("="*60)
    
    subject = "Re: Payment Request"
    body = """
    On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:
    > Hello,
    > 
    > Please find attached invoice for BL-001-123.
    > Amount: $420
    > 
    > Best regards,
    > Support Team
    
    Please find attached payment receipt.
    """
    attachments = ["payment_receipt.pdf"]
    from_addr = "customer@example.com"
    
    # Mock AI to return minimal content (just the new text)
    with patch('email_ingestor_working.extract_new_content_from_reply') as mock_extract:
        with patch('email_ingestor_working.extract_bl_specific_payments') as mock_bl_payments:
            with patch('email_ingestor_working.extract_all_payment_amounts') as mock_payment:
                
                mock_extract.return_value = "Please find attached payment receipt."
                mock_bl_payments.return_value = {'BL-001-123': 420.0}
                mock_payment.return_value = 420.0
                
                from email_ingestor_working import handle_email_via_openai
                
                try:
                    result = handle_email_via_openai(subject, body, attachments, from_addr)
                    print(f"✅ SUCCESS: Customer reply with PDF attachment processed")
                    print(f"   Classification: {result.get('classification')}")
                    print(f"   BL Numbers: {result.get('bl_numbers')}")
                    print(f"   Paid Amount: {result.get('paid_amount')}")
                    print(f"   Request Types: {result.get('request_types')}")
                    
                    # Verify PDF processing worked and old quoted content wasn't processed
                    assert 'BL-001-123' in result.get('bl_numbers', []), "BL number should be extracted from PDF"
                    assert result.get('paid_amount') == 420.0, "Payment amount should be extracted from PDF"
                    assert 'payment_receipt' in result.get('request_types', []), "Should be classified as payment receipt"
                    
                except Exception as e:
                    print(f"❌ ERROR: {e}")
                    return False
    
    return True

def test_scenario_7_no_text_with_attachment():
    """Test: Email with no text but attachment (NYC239 scenario)"""
    print("\n" + "="*60)
    print("SCENARIO 7: Email with no text but attachment (NYC239 scenario)")
    print("="*60)
    
    subject = "Payment for NYC239"
    body = """
    On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:
    > Hello,
    > 
    > Please find attached invoice for NYC239.
    > Amount: $420
    > 
    > Best regards,
    > Support Team
    
    On Sun, Aug 9, 2025 at 1:30 PM, Customer <customer@example.com> wrote:
    > Hello,
    > 
    > I need CTN numbers for NYC238, NYC239, NYC240.
    > 
    > Best regards,
    > Customer
    """
    attachments = ["payment_receipt.pdf"]
    from_addr = "customer@example.com"
    
    # Mock AI to return empty string (no new content)
    with patch('email_ingestor_working.extract_new_content_from_reply') as mock_extract:
        with patch('email_ingestor_working.extract_bl_specific_payments') as mock_bl_payments:
            with patch('email_ingestor_working.extract_all_payment_amounts') as mock_payment:
                
                mock_extract.return_value = ""  # AI should return empty for no new content
                mock_bl_payments.return_value = {'NYC239': 420.0}
                mock_payment.return_value = 420.0
                
                from email_ingestor_working import handle_email_via_openai
                
                try:
                    result = handle_email_via_openai(subject, body, attachments, from_addr)
                    print(f"✅ SUCCESS: No-text-with-attachment email processed")
                    print(f"   Classification: {result.get('classification')}")
                    print(f"   BL Numbers: {result.get('bl_numbers')}")
                    print(f"   Paid Amount: {result.get('paid_amount')}")
                    print(f"   Request Types: {result.get('request_types')}")
                    
                    # Verify only NYC239 was processed, not old quoted BLs
                    assert 'NYC239' in result.get('bl_numbers', []), "NYC239 should be extracted from PDF"
                    assert 'NYC238' not in result.get('bl_numbers', []), "Old quoted NYC238 should NOT be extracted"
                    assert 'NYC240' not in result.get('bl_numbers', []), "Old quoted NYC240 should NOT be extracted"
                    assert result.get('paid_amount') == 420.0, "Payment amount should be extracted from PDF"
                    assert 'payment_receipt' in result.get('request_types', []), "Should be classified as payment receipt"
                    
                except Exception as e:
                    print(f"❌ ERROR: {e}")
                    return False
    
    return True

def test_scenario_8_short_meaningful_reply():
    """Test: Customer reply with short but meaningful content (e.g., 'No')"""
    print("\n" + "="*60)
    print("SCENARIO 8: Customer reply with short but meaningful content (e.g., 'No')")
    print("="*60)
    
    subject = "Re: Have you made the payment?"
    body = """
    On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:
    > Hello,
    > 
    > Have you made the payment for BL-001-123?
    > 
    > Best regards,
    > Support Team
    
    No
    """
    attachments = []
    from_addr = "customer@example.com"
    
    with patch('email_ingestor_working.extract_new_content_from_reply') as mock_extract:
        mock_extract.return_value = "No"  # AI should keep short meaningful content
        
        from email_ingestor_working import handle_email_via_openai
        
        try:
            result = handle_email_via_openai(subject, body, attachments, from_addr)
            print(f"✅ SUCCESS: Short meaningful reply processed")
            print(f"   Classification: {result.get('classification')}")
            print(f"   BL Numbers: {result.get('bl_numbers')}")
            print(f"   Request Types: {result.get('request_types')}")
            print(f"   Reply Length: {len(result.get('reply', ''))}")
            
            # Verify short content was kept and processed
            assert len(result.get('reply', '')) > 0, "Reply should not be empty"
            assert 'No' in result.get('reply', ''), "Short reply content should be preserved"
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            return False
    
    return True

def test_ai_content_extraction():
    """Test the AI content extraction function directly"""
    print("\n" + "="*60)
    print("TESTING: AI Content Extraction Function")
    print("="*60)
    
    from email_ingestor_working import extract_new_content_from_reply
    
    test_cases = [
        {
            "name": "Simple reply with quoted content",
            "input": """Thank you for the information.
            
            On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:
            > Hello,
            > 
            > Here is your CTN number: ABC123
            > 
            > Best regards,
            > Support Team""",
            "expected_contains": "Thank you for the information",
            "expected_not_contains": "Here is your CTN number: ABC123"
        },
        {
            "name": "Empty reply (only quoted content)",
            "input": """On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:
            > Hello,
            > 
            > Here is your CTN number: ABC123
            > 
            > Best regards,
            > Support Team""",
            "expected_contains": "",
            "expected_not_contains": "Here is your CTN number: ABC123"
        },
        {
            "name": "Reply with multiple quoted levels",
            "input": """I need the CTN for BL-001-124.
            
            On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:
            > On Sun, Aug 9, 2025 at 1:30 PM, Customer <customer@example.com> wrote:
            > > Hello,
            > > 
            > > I need CTN numbers for NYC238, NYC239, NYC240.
            > > 
            > > Best regards,
            > > Customer""",
            "expected_contains": "I need the CTN for BL-001-124",
            "expected_not_contains": "NYC238, NYC239, NYC240"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        try:
            result = extract_new_content_from_reply(test_case['input'])
            print(f"Input length: {len(test_case['input'])}")
            print(f"Output length: {len(result)}")
            print(f"Output: '{result}'")
            
            # Check if expected content is present
            if test_case['expected_contains']:
                if test_case['expected_contains'] in result:
                    print(f"✅ Expected content found: '{test_case['expected_contains']}'")
                else:
                    print(f"❌ Expected content NOT found: '{test_case['expected_contains']}'")
            
            # Check if unwanted content is absent
            if test_case['expected_not_contains']:
                if test_case['expected_not_contains'] not in result:
                    print(f"✅ Unwanted content correctly removed: '{test_case['expected_not_contains']}'")
                else:
                    print(f"❌ Unwanted content still present: '{test_case['expected_not_contains']}'")
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")

def run_all_tests():
    """Run all test scenarios"""
    print("🚀 Starting Email Ingestion Test Suite")
    print("="*80)
    
    test_results = []
    
    # Test all scenarios
    test_results.append(("Scenario 1: New email - plain text", test_scenario_1_new_email_plain_text()))
    test_results.append(("Scenario 2: New email - text bank transfer", test_scenario_2_new_email_text_bank_transfer()))
    test_results.append(("Scenario 3: New email - PDF bank transfer", test_scenario_3_new_email_pdf_bank_transfer()))
    test_results.append(("Scenario 4: Customer reply - plain text", test_scenario_4_customer_reply_plain_text()))
    test_results.append(("Scenario 5: Customer reply - text bank transfer", test_scenario_5_customer_reply_text_bank_transfer()))
    test_results.append(("Scenario 6: Customer reply - PDF bank transfer", test_scenario_6_customer_reply_pdf_bank_transfer()))
    test_results.append(("Scenario 7: No text with attachment", test_scenario_7_no_text_with_attachment()))
    test_results.append(("Scenario 8: Short meaningful reply", test_scenario_8_short_meaningful_reply()))
    
    # Test AI content extraction directly
    test_ai_content_extraction()
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST RESULTS SUMMARY")
    print("="*80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The email ingestion system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(1)
