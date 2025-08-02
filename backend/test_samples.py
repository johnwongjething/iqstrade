#!/usr/bin/env python3
"""
Test Samples for Email Receipt Processing System
Based on user's requirements for testing valid BL numbers (NYC220, NYC221, NYC223) 
and invalid ones (NYC224, NYC225) with mixed text-based and PDF-based scenarios.
"""

import os
import tempfile
from datetime import datetime
from test_db_receipt_update import create_test_pdf
from email_ingestor_enhanced import process_payment_receipt_email

def create_test_samples():
    """Create various test samples for the receipt processing system"""
    
    print("🧪 Creating Test Samples for Receipt Processing System")
    print("=" * 70)
    
    # Test Case 1: Valid BL - Text-based receipt (NYC220)
    print("\n📧 Test Sample 1: Valid BL - Text-based Receipt")
    print("-" * 50)
    print("BL Number: NYC220")
    print("Payment Amount: $700")
    print("Type: Text-based (will generate PDF)")
    print("Expected: Should update database with receipt URL")
    
    test_case_1 = {
        "email_id": 2001,
        "from_addr": "customer@bank.com",
        "subject": "Payment Receipt - NYC220",
        "body_text": """
Dear Sir/Madam,

Please find attached our payment receipt for Bill of Lading NYC220.

Payment Details:
- BL Number: NYC220
- Amount Paid: $700.00
- Payment Date: August 1, 2025
- Payment Method: Bank Transfer

Best regards,
Customer Service
        """,
        "attachments": [],
        "bl_payment_map": {'NYC220': 700.0}
    }
    
    # Test Case 2: Valid BL - PDF-based receipt (NYC221)
    print("\n📧 Test Sample 2: Valid BL - PDF-based Receipt")
    print("-" * 50)
    print("BL Number: NYC221")
    print("Payment Amount: $675")
    print("Type: PDF attachment")
    print("Expected: Should update database with receipt URL")
    
    pdf_path_1 = create_test_pdf("NYC221 Payment Receipt - $675", "receipt_nyc221.pdf")
    test_case_2 = {
        "email_id": 2002,
        "from_addr": "payments@company.com",
        "subject": "Payment Confirmation - NYC221",
        "body_text": "Please find attached the payment receipt for BL NYC221.",
        "attachments": [pdf_path_1],
        "bl_payment_map": {'NYC221': 675.0}
    }
    
    # Test Case 3: Valid BL - Mixed content (NYC223)
    print("\n📧 Test Sample 3: Valid BL - Mixed Content")
    print("-" * 50)
    print("BL Number: NYC223")
    print("Payment Amount: $675")
    print("Type: PDF attachment + text body")
    print("Expected: Should use PDF attachment, update database")
    
    pdf_path_2 = create_test_pdf("NYC223 Payment Receipt - $675", "receipt_nyc223.pdf")
    test_case_3 = {
        "email_id": 2003,
        "from_addr": "finance@client.com",
        "subject": "Payment for NYC223",
        "body_text": """
Payment confirmation for Bill of Lading NYC223.

Amount: $675.00
Date: August 1, 2025
Reference: NYC223-001

Receipt attached.
        """,
        "attachments": [pdf_path_2],
        "bl_payment_map": {'NYC223': 675.0}
    }
    
    # Test Case 4: Invalid BL - Text-based (NYC224)
    print("\n📧 Test Sample 4: Invalid BL - Text-based Receipt")
    print("-" * 50)
    print("BL Number: NYC224 (does not exist in DB)")
    print("Payment Amount: $500")
    print("Type: Text-based")
    print("Expected: Should NOT update database (BL not found)")
    
    test_case_4 = {
        "email_id": 2004,
        "from_addr": "unknown@bank.com",
        "subject": "Payment for NYC224",
        "body_text": "Payment of $500 for BL NYC224",
        "attachments": [],
        "bl_payment_map": {'NYC224': 500.0}
    }
    
    # Test Case 5: Invalid BL - PDF-based (NYC225)
    print("\n📧 Test Sample 5: Invalid BL - PDF-based Receipt")
    print("-" * 50)
    print("BL Number: NYC225 (does not exist in DB)")
    print("Payment Amount: $600")
    print("Type: PDF attachment")
    print("Expected: Should NOT update database (BL not found)")
    
    pdf_path_3 = create_test_pdf("NYC225 Payment Receipt - $600", "receipt_nyc225.pdf")
    test_case_5 = {
        "email_id": 2005,
        "from_addr": "payments@unknown.com",
        "subject": "Payment Receipt - NYC225",
        "body_text": "Payment receipt for BL NYC225 attached.",
        "attachments": [pdf_path_3],
        "bl_payment_map": {'NYC225': 600.0}
    }
    
    # Test Case 6: Underpayment - Valid BL (NYC220)
    print("\n📧 Test Sample 6: Underpayment - Valid BL")
    print("-" * 50)
    print("BL Number: NYC220")
    print("Payment Amount: $650 (less than required $700)")
    print("Type: Text-based")
    print("Expected: Should NOT update database (underpayment)")
    
    test_case_6 = {
        "email_id": 2006,
        "from_addr": "customer@bank.com",
        "subject": "Partial Payment - NYC220",
        "body_text": "Partial payment of $650 for BL NYC220",
        "attachments": [],
        "bl_payment_map": {'NYC220': 650.0}
    }
    
    # Test Case 7: Overpayment - Valid BL (NYC221)
    print("\n📧 Test Sample 7: Overpayment - Valid BL")
    print("-" * 50)
    print("BL Number: NYC221")
    print("Payment Amount: $700 (more than required $675)")
    print("Type: PDF attachment")
    print("Expected: Should update database (overpayment accepted)")
    
    pdf_path_4 = create_test_pdf("NYC221 Payment Receipt - $700", "receipt_nyc221_overpayment.pdf")
    test_case_7 = {
        "email_id": 2007,
        "from_addr": "payments@company.com",
        "subject": "Overpayment - NYC221",
        "body_text": "Payment of $700 for BL NYC221 (includes extra amount)",
        "attachments": [pdf_path_4],
        "bl_payment_map": {'NYC221': 700.0}
    }
    
    # Test Case 8: Multiple BLs in one email
    print("\n📧 Test Sample 8: Multiple BLs in One Email")
    print("-" * 50)
    print("BL Numbers: NYC220, NYC221")
    print("Payment Amounts: $700, $675")
    print("Type: Text-based")
    print("Expected: Should update both BLs in database")
    
    test_case_8 = {
        "email_id": 2008,
        "from_addr": "bulk@payments.com",
        "subject": "Bulk Payment - Multiple BLs",
        "body_text": """
Bulk payment for multiple bills:

BL NYC220: $700
BL NYC221: $675

Total: $1,375
        """,
        "attachments": [],
        "bl_payment_map": {'NYC220': 700.0, 'NYC221': 675.0}
    }
    
    # Store all test cases
    test_cases = [
        ("Valid BL - Text-based (NYC220)", test_case_1),
        ("Valid BL - PDF-based (NYC221)", test_case_2),
        ("Valid BL - Mixed content (NYC223)", test_case_3),
        ("Invalid BL - Text-based (NYC224)", test_case_4),
        ("Invalid BL - PDF-based (NYC225)", test_case_5),
        ("Underpayment - Valid BL (NYC220)", test_case_6),
        ("Overpayment - Valid BL (NYC221)", test_case_7),
        ("Multiple BLs in one email", test_case_8)
    ]
    
    return test_cases

def run_test_samples():
    """Run all test samples and show results"""
    
    test_cases = create_test_samples()
    
    print("\n🚀 Running Test Samples")
    print("=" * 70)
    
    results = []
    
    for i, (test_name, test_case) in enumerate(test_cases, 1):
        print(f"\n🔄 Running Test {i}: {test_name}")
        print(f"   Email ID: {test_case['email_id']}")
        print(f"   BL Payment Map: {test_case['bl_payment_map']}")
        print(f"   Has PDF: {len(test_case['attachments']) > 0}")
        
        try:
            # Process the payment receipt
            success = process_payment_receipt_email(
                email_id=test_case['email_id'],
                from_addr=test_case['from_addr'],
                subject=test_case['subject'],
                body_text=test_case['body_text'],
                attachments=test_case['attachments'],
                bl_payment_map=test_case['bl_payment_map']
            )
            
            # Determine expected result
            expected_success = True
            if "Invalid BL" in test_name:
                expected_success = False
            elif "Underpayment" in test_name:
                expected_success = False
            
            # Check result
            if success == expected_success:
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
            
            results.append({
                "test": test_name,
                "success": success,
                "expected": expected_success,
                "status": status
            })
            
            print(f"   Result: {status}")
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
            results.append({
                "test": test_name,
                "success": False,
                "expected": "ERROR",
                "status": f"❌ ERROR: {str(e)}"
            })
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 70)
    
    passed = sum(1 for r in results if "PASS" in r["status"])
    failed = sum(1 for r in results if "FAIL" in r["status"])
    errors = sum(1 for r in results if "ERROR" in r["status"])
    
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"💥 Errors: {errors}")
    print(f"📈 Success Rate: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
    
    print("\n📋 Detailed Results:")
    for result in results:
        print(f"   {result['status']} - {result['test']}")

def create_email_templates():
    """Create email templates for manual testing"""
    
    print("\n📧 Email Templates for Manual Testing")
    print("=" * 70)
    
    templates = {
        "valid_text_nyc220": {
            "subject": "Payment Receipt - NYC220",
            "body": """
Dear Sir/Madam,

Please find our payment receipt for Bill of Lading NYC220.

Payment Details:
- BL Number: NYC220
- Amount Paid: $700.00
- Payment Date: August 1, 2025
- Payment Method: Bank Transfer

Best regards,
Customer Service
            """,
            "bl_payment_map": {'NYC220': 700.0}
        },
        
        "valid_pdf_nyc221": {
            "subject": "Payment Confirmation - NYC221",
            "body": "Please find attached the payment receipt for BL NYC221.",
            "bl_payment_map": {'NYC221': 675.0}
        },
        
        "invalid_nyc224": {
            "subject": "Payment for NYC224",
            "body": "Payment of $500 for BL NYC224",
            "bl_payment_map": {'NYC224': 500.0}
        },
        
        "underpayment_nyc220": {
            "subject": "Partial Payment - NYC220",
            "body": "Partial payment of $650 for BL NYC220",
            "bl_payment_map": {'NYC220': 650.0}
        },
        
        "multiple_bls": {
            "subject": "Bulk Payment - Multiple BLs",
            "body": """
Bulk payment for multiple bills:

BL NYC220: $700
BL NYC221: $675

Total: $1,375
            """,
            "bl_payment_map": {'NYC220': 700.0, 'NYC221': 675.0}
        }
    }
    
    for name, template in templates.items():
        print(f"\n📧 Template: {name}")
        print(f"Subject: {template['subject']}")
        print(f"BL Payment Map: {template['bl_payment_map']}")
        print(f"Body:\n{template['body']}")
        print("-" * 50)

if __name__ == "__main__":
    print("🧪 Test Samples for Email Receipt Processing System")
    print("=" * 70)
    
    # Show test samples
    create_test_samples()
    
    # Show email templates
    create_email_templates()
    
    # Ask user if they want to run tests
    print("\n" + "=" * 70)
    print("To run the tests, call: run_test_samples()")
    print("Or run individual tests by importing the functions.")
    print("=" * 70) 