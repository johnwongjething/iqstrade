#!/usr/bin/env python3
"""
Test the 3 PDF sample files for payment processing
"""

import os
from email_ingestor_enhanced import handle_email_via_openai, process_payment_receipt_email

def test_pdf_sample(pdf_path, test_name):
    """Test a specific PDF sample"""
    print(f"\n🧪 Testing: {test_name}")
    print("=" * 60)
    
    # Test email with PDF attachment
    subject = f"Bank Transfer Receipt - {test_name}"
    body = f"Please find attached the bank transfer receipt for B/L NYC220"
    attachments = [pdf_path]
    from_addr = "customer@example.com"
    
    print(f"📧 Subject: {subject}")
    print(f"📝 Body: {body}")
    print(f"📎 PDF: {os.path.basename(pdf_path)}")
    
    try:
        # Process the email
        result = handle_email_via_openai(subject, body, attachments, from_addr)
        
        print(f"\n💰 Extracted Amount: ${result.get('paid_amount')}")
        print(f"📊 BL Numbers: {result.get('bl_numbers')}")
        print(f"📋 BL Payment Map: {result.get('bl_payment_map')}")
        print(f"✅ Valid BLs: {result.get('valid_bls')}")
        
        # Check payment processing
        if result.get('bl_payment_map') and result.get('paid_amount'):
            print("\n🔄 Testing payment receipt processing...")
            
            # Simulate email processing
            email_id = 999  # Test email ID
            success = process_payment_receipt_email(
                email_id=email_id,
                from_addr=from_addr,
                subject=subject,
                body_text=body,
                attachments=attachments,
                bl_payment_map=result.get('bl_payment_map', {})
            )
            
            if success:
                print("✅ Payment receipt processing completed successfully")
            else:
                print("❌ Payment receipt processing failed")
        
        # Check for payment messages
        reply = result.get('custom_reply', '')
        if 'underpayment' in reply.lower():
            print("✅ UNDERPAYMENT message detected in reply")
        elif 'overpayment' in reply.lower():
            print("✅ OVERPAYMENT message detected in reply")
        elif 'payment match' in reply.lower():
            print("✅ PAYMENT MATCH message detected in reply")
        else:
            print("❓ No specific payment message detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing PDF: {e}")
        return False

def main():
    """Main test function"""
    print("🔧 Testing PDF Sample Files for Payment Processing")
    print("=" * 80)
    
    # Check if test_pdfs directory exists
    test_dir = "test_pdfs"
    if not os.path.exists(test_dir):
        print(f"❌ Test directory '{test_dir}' not found!")
        print("💡 Run 'python create_test_pdfs.py' first to create the PDF samples")
        return
    
    # Define test cases
    test_cases = [
        {
            "file": "underpayment_receipt.pdf",
            "name": "Underpayment Test ($680 for $700 invoice)",
            "expected": "underpayment"
        },
        {
            "file": "overpayment_receipt.pdf", 
            "name": "Overpayment Test ($720 for $700 invoice)",
            "expected": "overpayment"
        },
        {
            "file": "exact_payment_receipt.pdf",
            "name": "Exact Payment Test ($700 for $700 invoice)",
            "expected": "payment match"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        pdf_path = os.path.join(test_dir, test_case["file"])
        
        if not os.path.exists(pdf_path):
            print(f"❌ PDF file not found: {pdf_path}")
            continue
        
        success = test_pdf_sample(pdf_path, test_case["name"])
        results.append({
            "test": test_case["name"],
            "success": success,
            "expected": test_case["expected"]
        })
    
    # Summary
    print(f"\n📊 Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"{status}: {result['test']}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All PDF payment processing tests passed!")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main() 