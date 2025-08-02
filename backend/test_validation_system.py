#!/usr/bin/env python3
"""
Test Validation System
Demonstrates how the validation system catches missed information
"""
import sys
import os
from email_classification_validator import validate_email_classification, email_validator

def test_validation_system():
    """Test the validation system with the specific cases you mentioned"""
    
    print("🧪 TESTING EMAIL CLASSIFICATION VALIDATION SYSTEM")
    print("=" * 80)
    
    # Test cases based on your feedback
    test_cases = [
        {
            "name": "Case 7 - CTN Processing Time (Missed)",
            "subject": "Complex Test 7 - CTN Processing Time",
            "body": """Dear Team,

How long does it take to process CTN for BL NAM20, BL 001-123, and BL NYC220?

Also, what are the total fees for each shipment?

Best regards,
John Doe""",
            "request_types": ["fee_inquiry"],  # Original classification missed ctn_process
            "ai_reply": "Thank you for your inquiry regarding the fees for your shipments. Here are the details for each Bill of Lading (BL): - BL NAM20: The total fees amount to $1,000...",
            "bl_numbers": ["NAM20", "001-123", "NYC220"]
        },
        {
            "name": "Case 6 - Wrong Amount for NAM20 (Missed)",
            "subject": "Complex Test 6 - Business Hours + Payment Methods",
            "body": """Hi IQS Trade,

What are your business hours? Also, what payment methods do you accept?

I need to pay for BL NAM20 ($250), BL 001-123 ($200), and BL NYC220 ($200).

Please provide payment instructions.

Thanks,
John""",
            "request_types": ["business_hours", "payment_methods"],  # Original classification
            "ai_reply": "Our business hours are: Monday to Friday, 9:00 AM to 5:00 PM (Hong Kong time)...",
            "bl_numbers": ["NAM20", "001-123", "NYC220"]
        },
        {
            "name": "Case 4 - Underpayment Calculation (Wrong)",
            "subject": "Complex Test 4 - Underpayment Scenario",
            "body": """Hi Team,

I'm sending payment for:
- BL NAM20: $100 (should be $250 total)
- BL 001-123: $150 (should be $200 total)
- BL NYC220: $50 (should be $200 total)

Total sent: $300. Please confirm what's still due.

Thanks,
John""",
            "request_types": ["payment_status"],  # Original classification
            "ai_reply": "Thank you for your payment update. Here is the current payment status for the specified BLs: - BL NAM20: The total amount due is $1,000...",
            "bl_numbers": ["NAM20", "001-123", "NYC220"]
        },
        {
            "name": "Case 1 - Mixed Payment Types (Good)",
            "subject": "Complex Test 1 - Mixed Payment Types",
            "body": """Dear IQS Trade Team,

I need to make payments for multiple shipments:

1. BL NAM20: USD 250 (partial payment)
2. BL 001-123: USD 200 (full payment) 
3. BL NYC220: USD 180 (overpayment)

Also, please provide CTN numbers for all three shipments and send invoices.

Best regards,
John Doe""",
            "request_types": ["payment_status", "ctn_request", "invoice_request"],  # Good classification
            "ai_reply": "Thank you for reaching out to us regarding your shipments. Here are the details you requested: 1. BL NAM20: CTN Number: MYS306581...",
            "bl_numbers": ["NAM20", "001-123", "NYC220"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📧 TEST CASE {i}: {test_case['name']}")
        print("-" * 60)
        
        # Run validation
        validation_result = validate_email_classification(
            email_body=test_case['body'],
            subject=test_case['subject'],
            request_types=test_case['request_types'],
            ai_reply=test_case['ai_reply'],
            bl_numbers=test_case['bl_numbers']
        )
        
        # Display results
        print(f"📋 Original Request Types: {validation_result['original_request_types']}")
        print(f"🚨 Missed Request Types: {validation_result['missed_request_types']}")
        print(f"💰 Amount Validation Issues: {len(validation_result['amount_validation_issues'])}")
        print(f"🔧 Recommendations: {len(validation_result['recommendations'])}")
        print(f"🔄 Needs Reclassification: {'✅ YES' if validation_result['needs_reclassification'] else '❌ NO'}")
        
        # Show specific issues
        if validation_result['missed_request_types']:
            print(f"   ❌ MISSED: {', '.join(validation_result['missed_request_types'])}")
        
        if validation_result['amount_validation_issues']:
            print(f"   💰 AMOUNT ISSUES:")
            for issue in validation_result['amount_validation_issues']:
                print(f"      - {issue['issue']}")
        
        if validation_result['recommendations']:
            print(f"   🔧 RECOMMENDATIONS:")
            for rec in validation_result['recommendations']:
                print(f"      - {rec}")
        
        # Show enhanced prompt if needed
        if validation_result['needs_reclassification']:
            print(f"\n📝 ENHANCED PROMPT:")
            enhanced_prompt = email_validator.generate_enhanced_prompt(
                f"Subject: {test_case['subject']}\n\nBody: {test_case['body']}",
                validation_result
            )
            print(f"   {enhanced_prompt[:200]}...")
    
    print(f"\n{'='*80}")
    print("📊 VALIDATION SYSTEM SUMMARY")
    print(f"{'='*80}")
    
    # Summary statistics
    total_cases = len(test_cases)
    cases_needing_reclassification = sum(1 for case in test_cases if 
        validate_email_classification(
            case['body'], case['subject'], case['request_types'], 
            case['ai_reply'], case['bl_numbers']
        )['needs_reclassification']
    )
    
    print(f"📧 Total Test Cases: {total_cases}")
    print(f"🚨 Cases Needing Reclassification: {cases_needing_reclassification}")
    print(f"✅ Cases Working Correctly: {total_cases - cases_needing_reclassification}")
    print(f"📈 Success Rate: {((total_cases - cases_needing_reclassification) / total_cases) * 100:.1f}%")
    
    print(f"\n🎯 VALIDATION SYSTEM BENEFITS:")
    print(f"   ✅ Catches missed CTN processing time questions")
    print(f"   ✅ Identifies wrong amounts mentioned by customers")
    print(f"   ✅ Ensures all customer questions are addressed")
    print(f"   ✅ Non-disruptive to existing system")
    print(f"   ✅ Provides detailed recommendations for improvement")

if __name__ == '__main__':
    test_validation_system() 