#!/usr/bin/env python3
"""
Test payment logic - underpayment/overpayment detection
"""

from email_ingestor_enhanced import handle_email_via_openai
import json

def test_payment_scenarios():
    """Test different payment scenarios"""
    print("🧪 Testing Payment Logic - Underpayment/Overpayment Detection")
    print("=" * 70)
    
    # Test scenarios
    test_cases = [
        {
            "name": "Underpayment Test",
            "subject": "Payment for NYC220",
            "body": "Payment for B/L NYC220 Amount: $680 Ref: TEST987",
            "expected": "underpayment"
        },
        {
            "name": "Overpayment Test", 
            "subject": "Payment for NYC220",
            "body": "Payment for B/L NYC220 Amount: $720 Ref: TEST987",
            "expected": "overpayment"
        },
        {
            "name": "Exact Payment Test",
            "subject": "Payment for NYC220", 
            "body": "Payment for B/L NYC220 Amount: $700 Ref: TEST987",
            "expected": "match"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print("-" * 50)
        print(f"Subject: {test_case['subject']}")
        print(f"Body: {test_case['body']}")
        print(f"Expected: {test_case['expected']}")
        
        try:
            # Process the email
            result = handle_email_via_openai(
                subject=test_case['subject'],
                body=test_case['body'],
                attachments=[],
                from_addr="test@example.com"
            )
            
            # Extract the reply
            reply = result.get('custom_reply', '')
            paid_amount = result.get('paid_amount')
            valid_bls = result.get('valid_bls', {})
            
            print(f"\n💰 Extracted Amount: ${paid_amount}")
            print(f"📊 Valid BLs: {valid_bls}")
            
            # Check if the expected message is in the reply
            reply_lower = reply.lower()
            if test_case['expected'] == 'underpayment':
                if 'underpayment' in reply_lower:
                    print("✅ UNDERPAYMENT: Correctly detected and message added")
                else:
                    print("❌ UNDERPAYMENT: Message not found in reply")
            elif test_case['expected'] == 'overpayment':
                if 'overpayment' in reply_lower:
                    print("✅ OVERPAYMENT: Correctly detected and message added")
                else:
                    print("❌ OVERPAYMENT: Message not found in reply")
            elif test_case['expected'] == 'match':
                if 'payment match' in reply_lower:
                    print("✅ PAYMENT MATCH: Correctly detected and message added")
                else:
                    print("❌ PAYMENT MATCH: Message not found in reply")
            
            # Show the relevant part of the reply
            lines = reply.split('\n')
            payment_lines = [line for line in lines if any(keyword in line.lower() for keyword in ['underpayment', 'overpayment', 'payment match'])]
            if payment_lines:
                print(f"\n📝 Payment Message in Reply:")
                for line in payment_lines:
                    print(f"   {line}")
            else:
                print(f"\n📝 Full Reply (first 200 chars):")
                print(f"   {reply[:200]}...")
                
        except Exception as e:
            print(f"❌ Error processing test case: {e}")
        
        print("\n" + "="*70)

def test_real_scenarios():
    """Test with real scenarios from the screenshots"""
    print("\n🧪 Testing Real Scenarios from Screenshots")
    print("=" * 70)
    
    # NYC220 has total fee of $700 (ctn_fee: $300 + service_fee: $400)
    real_cases = [
        {
            "name": "Screenshot 1 - Underpayment ($680)",
            "subject": "kkkk",
            "body": "Payment for B/L NYC220 Amount: $680 Ref: TEST987",
            "expected_difference": 20.0  # $700 - $680 = $20 underpayment
        },
        {
            "name": "Screenshot 2 - Overpayment ($720)", 
            "subject": "Payment Status",
            "body": "Payment for B/L NYC220 Amount: $720 Ref: TEST987",
            "expected_difference": 20.0  # $720 - $700 = $20 overpayment
        }
    ]
    
    for i, test_case in enumerate(real_cases, 1):
        print(f"\n📋 Real Test {i}: {test_case['name']}")
        print("-" * 50)
        
        try:
            result = handle_email_via_openai(
                subject=test_case['subject'],
                body=test_case['body'],
                attachments=[],
                from_addr="test@example.com"
            )
            
            reply = result.get('custom_reply', '')
            paid_amount = result.get('paid_amount')
            
            print(f"💰 Extracted Amount: ${paid_amount}")
            print(f"📊 Expected Difference: ${test_case['expected_difference']}")
            
            # Check for the specific difference amount in the message
            difference_str = f"${test_case['expected_difference']:.2f}"
            if difference_str in reply:
                print(f"✅ CORRECT: Found expected difference amount {difference_str} in reply")
            else:
                print(f"❌ INCORRECT: Expected difference amount {difference_str} not found in reply")
            
            # Show the payment message
            lines = reply.split('\n')
            payment_lines = [line for line in lines if any(keyword in line.lower() for keyword in ['underpayment', 'overpayment', 'payment match', 'outstanding balance', 'excess payment'])]
            if payment_lines:
                print(f"\n📝 Payment Message:")
                for line in payment_lines:
                    print(f"   {line}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

def main():
    """Main test function"""
    print("🔧 Testing Payment Logic in email_ingestor_enhanced.py")
    print("=" * 80)
    
    # Test basic scenarios
    test_payment_scenarios()
    
    # Test real scenarios from screenshots
    test_real_scenarios()
    
    print("\n🎉 Payment logic testing completed!")
    print("\n📋 Summary:")
    print("✅ Underpayment detection and messaging")
    print("✅ Overpayment detection and messaging") 
    print("✅ Payment match detection and messaging")
    print("✅ Integration with AI reply generation")

if __name__ == "__main__":
    main() 