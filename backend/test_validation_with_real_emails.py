#!/usr/bin/env python3
"""
Test Validation System with Real Email Data
Demonstrates validation system with actual email content
"""
import sys
import os
from email_classification_validator import validate_email_classification, email_validator

def test_validation_with_real_emails():
    """Test validation system with real email scenarios"""
    
    print("🧪 TESTING VALIDATION SYSTEM WITH REAL EMAIL DATA")
    print("=" * 80)
    
    # Real email scenarios based on your feedback
    real_email_scenarios = [
        {
            "name": "Real Case 7 - CTN Processing Time (Missed by System)",
            "subject": "Complex Test 7 - CTN Processing Time",
            "body": """Dear Team,

How long does it take to process CTN for BL NAM20, BL 001-123, and BL NYC220?

Also, what are the total fees for each shipment?

Best regards,
John Doe""",
            "original_request_types": ["fee_inquiry"],  # What the system detected
            "ai_reply": "Thank you for your inquiry regarding the fees for your shipments. Here are the details for each Bill of Lading (BL): - BL NAM20: The total fees amount to $1,000, which includes a CTN Fee of $500 and a Service Fee of $500. You can view the invoice here: [Invoice Link]. - BL 001-123: The total fees amount to $200, which includes a CTN Fee of $100 and a Service Fee of $100. You can view the invoice here: [Invoice Link]. - BL NYC220: The total fees amount to $200, which includes a CTN Fee of $100 and a Service Fee of $100. You can view the invoice here: [Invoice Link]. If you have any further questions, please feel free to reach out. Thank you! IQSTrade Support Team Best regards, IQS Trade Team",
            "expected_issues": ["ctn_process"]
        },
        {
            "name": "Real Case 6 - Wrong Amount for NAM20 (Missed by System)",
            "subject": "Complex Test 6 - Business Hours + Payment Methods",
            "body": """Hi IQS Trade,

What are your business hours? Also, what payment methods do you accept?

I need to pay for BL NAM20 ($250), BL 001-123 ($200), and BL NYC220 ($200).

Please provide payment instructions.

Thanks,
John""",
            "original_request_types": ["business_hours", "payment_methods"],
            "ai_reply": "Hello, Payment(s) found: - For BL 001-123: Payment record found. - For BL NAM20: Payment record found. - For BL NYC220: Payment record found. ⚠️ UNDERPAYMENT: We have received your payment of $450.00, but the invoice amount is $1400.00. There is an outstanding balance of $950.00. Our business hours are: Monday to Friday, 9:00 AM to 5:00 PM (Hong Kong time) Best regards, IQS Trade Team",
            "expected_issues": ["amount_validation"]
        },
        {
            "name": "Real Case 4 - Underpayment Calculation (Wrong Math)",
            "subject": "Complex Test 4 - Underpayment Scenario",
            "body": """Hi Team,

I'm sending payment for:
- BL NAM20: $100 (should be $250 total)
- BL 001-123: $150 (should be $200 total)
- BL NYC220: $50 (should be $200 total)

Total sent: $300. Please confirm what's still due.

Thanks,
John""",
            "original_request_types": ["payment_status"],
            "ai_reply": "Hi John, Thank you for your payment update. Here is the current payment status for the specified BLs: - BL NAM20: The total amount due is $1,000. You have sent $100, leaving a balance of $900. - BL 001-123: The total amount due is $200. You have sent $150, leaving a balance of $50. - BL NYC220: The total amount due is $200. You have sent $50, leaving a balance of $150. Please let us know if you need further assistance. Thank you! IQSTrade Support Team ⚠️ UNDERPAYMENT: We have received your payment of $1050.00, but the invoice amount is $1400.00. There is an outstanding balance of $350.00. Best regards, IQS Trade Team",
            "expected_issues": ["amount_validation"]
        },
        {
            "name": "Real Case 1 - Mixed Payment Types (Good)",
            "subject": "Complex Test 1 - Mixed Payment Types",
            "body": """Dear IQS Trade Team,

I need to make payments for multiple shipments:

1. BL NAM20: USD 250 (partial payment)
2. BL 001-123: USD 200 (full payment) 
3. BL NYC220: USD 180 (overpayment)

Also, please provide CTN numbers for all three shipments and send invoices.

Best regards,
John Doe""",
            "original_request_types": ["payment_status", "ctn_request", "invoice_request"],
            "ai_reply": "Dear John Doe, Thank you for reaching out to us regarding your shipments. Here are the details you requested: 1. BL NAM20: - CTN Number: MYS306581 - Invoice: [Download Invoice](https://res.cloudinary.com/dtm46mski/image/upload/v1753164521/invoices/b40frniluowxpc48pw6g.pdf) 2. BL 001-123: - CTN Number: ray010101 - Invoice: [Download Invoice](https://res.cloudinary.com/dtm46mski/image/upload/v1753070621/invoices/nogajjvsrgp6kkubnthl.pdf) 3. BL NYC220: - CTN Number: Ray000006 - Invoice: [Download Invoice](https://res.cloudinary.com/dtm46mski/image/upload/v1753088057/invoices/k4ddwncnctmprmcl1pl3.pdf) Please note that the processing time for a Cargo Tracking Note (CTN) is typically between 24 to 48 hours after your payment has been confirmed. If you have any further questions or need assistance, feel free to reach out. Best regards, IQSTrade Support Team ⚠️ UNDERPAYMENT: We have received your payment of $630.00, but the invoice amount is $1400.00. There is an outstanding balance of $770.00. Best regards, IQS Trade Team",
            "expected_issues": []
        }
    ]
    
    total_tests = len(real_email_scenarios)
    validation_caught_issues = 0
    
    for i, scenario in enumerate(real_email_scenarios, 1):
        print(f"\n📧 TEST {i}: {scenario['name']}")
        print("-" * 60)
        
        # Run validation
        validation_result = validate_email_classification(
            email_body=scenario['body'],
            subject=scenario['subject'],
            request_types=scenario['original_request_types'],
            ai_reply=scenario['ai_reply'],
            bl_numbers=extract_bl_numbers(scenario['body'])
        )
        
        # Display results
        print(f"📋 Original Request Types: {scenario['original_request_types']}")
        print(f"🚨 Missed Request Types: {validation_result['missed_request_types']}")
        print(f"💰 Amount Validation Issues: {len(validation_result['amount_validation_issues'])}")
        print(f"🔄 Needs Reclassification: {'✅ YES' if validation_result['needs_reclassification'] else '❌ NO'}")
        
        # Check if validation caught expected issues
        expected_issues = scenario['expected_issues']
        actual_issues = validation_result['missed_request_types'] + ['amount_validation'] if validation_result['amount_validation_issues'] else []
        
        if set(expected_issues).issubset(set(actual_issues)):
            print(f"✅ VALIDATION SUCCESS: Caught expected issues")
            validation_caught_issues += 1
        else:
            print(f"❌ VALIDATION FAILED: Expected {expected_issues}, got {actual_issues}")
        
        # Show specific issues
        if validation_result['missed_request_types']:
            print(f"   ❌ MISSED: {', '.join(validation_result['missed_request_types'])}")
        
        if validation_result['amount_validation_issues']:
            print(f"   💰 AMOUNT ISSUES:")
            for issue in validation_result['amount_validation_issues']:
                print(f"      - {issue['issue']}")
        
        # Show enhanced prompt if needed
        if validation_result['needs_reclassification']:
            print(f"\n📝 ENHANCED PROMPT:")
            enhanced_prompt = email_validator.generate_enhanced_prompt(
                f"Subject: {scenario['subject']}\n\nBody: {scenario['body']}",
                validation_result
            )
            print(f"   {enhanced_prompt[:200]}...")
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 VALIDATION SYSTEM PERFORMANCE")
    print(f"{'='*80}")
    print(f"📧 Total Test Cases: {total_tests}")
    print(f"✅ Validation Caught Expected Issues: {validation_caught_issues}")
    print(f"❌ Validation Missed Issues: {total_tests - validation_caught_issues}")
    print(f"📈 Success Rate: {(validation_caught_issues/total_tests)*100:.1f}%")
    
    print(f"\n🎯 VALIDATION SYSTEM EFFECTIVENESS:")
    if validation_caught_issues == total_tests:
        print(f"   🎉 PERFECT: Validation system caught ALL expected issues!")
        print(f"   ✅ Ready for production use")
    elif validation_caught_issues >= total_tests * 0.75:
        print(f"   ✅ GOOD: Validation system caught most issues")
        print(f"   🔧 Minor improvements needed")
    else:
        print(f"   ⚠️  NEEDS WORK: Validation system missed many issues")
        print(f"   🔧 Significant improvements needed")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Run: python auto_send_16_test_emails.py")
    print(f"   2. Wait 2-3 minutes for processing")
    print(f"   3. Run: python retrieve_16_email_results.py")
    print(f"   4. Analyze real-world performance")

def extract_bl_numbers(text):
    """Extract BL numbers from text"""
    import re
    bl_pattern = re.compile(r'(?:提单号[:：]?\s*)?(BL-\d{4,}|\d{3,}-\d{3,}|\d{6,}|[A-Z]{2,4}\d{2,})', re.IGNORECASE)
    return list(set(bl_pattern.findall(text)))

if __name__ == '__main__':
    test_validation_with_real_emails() 