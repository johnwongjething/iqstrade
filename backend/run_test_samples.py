#!/usr/bin/env python3
"""
Simple Test Runner for Email Receipt Processing System
"""

from test_samples import create_test_samples
from email_ingestor_enhanced import process_payment_receipt_email

def main():
    print("🧪 Running All Test Samples")
    print("=" * 70)
    
    test_cases = create_test_samples()
    results = []
    
    for i, (test_name, test_case) in enumerate(test_cases, 1):
        print(f"\n🔄 Test {i}: {test_name}")
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

if __name__ == "__main__":
    main() 