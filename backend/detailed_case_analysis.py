#!/usr/bin/env python3
"""
Detailed Case Analysis for AI Reply Issues
Compare original test emails with actual AI replies
"""
import os
import sys
import json
from config import get_db_conn

# Original test emails from complex_email_tests.py
ORIGINAL_TEST_EMAILS = {
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
        "expected_issues": "Should detect partial payment ($250 vs $1000), full payment ($200 vs $200), overpayment ($180 vs $200)"
    },
    2: {
        "subject": "Complex Test 2 - Chinese + English Mixed",
        "body": """Hello IQS Trade,

请问BL NAM20和BL 001-123的CTN号码是多少？

Also, I have paid $500 for BL NYC220. Please confirm receipt.

另外，请告知营业时间和付款方式。

Thanks,
John""",
        "expected_issues": "Should provide CTN numbers and confirm $500 payment for NYC220"
    },
    3: {
        "subject": "Complex Test 3 - PDF with Multiple BLs",
        "body": "Please process the attached payment receipt for multiple shipments.",
        "attachments": ["complex_test.pdf"],
        "expected_issues": "Should extract BL numbers and payment info from PDF"
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
        "expected_issues": "Customer sent $300, total invoice cost is $1400 (NAM20:$1000 + 001-123:$200 + NYC220:$200), outstanding is $1100"
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
        "expected_issues": "Should identify valid vs invalid BLs and provide info only for valid ones"
    },
    6: {
        "subject": "Complex Test 6 - Business Hours + Payment Methods",
        "body": """Hi IQS Trade,

What are your business hours? Also, what payment methods do you accept?

I need to pay for BL NAM20 ($250), BL 001-123 ($200), and BL NYC220 ($200).

Please provide payment instructions.

Thanks,
John""",
        "expected_issues": "Customer is asking how to pay and deliberately indicating wrong amount for NAM20 ($250 instead of $1000) - AI should catch this"
    },
    7: {
        "subject": "Complex Test 7 - CTN Processing Time",
        "body": """Dear Team,

How long does it take to process CTN for BL NAM20, BL 001-123, and BL NYC220?

Also, what are the total fees for each shipment?

Best regards,
John Doe""",
        "expected_issues": "AI doesn't answer the CTN processing time question"
    },
    8: {
        "subject": "Complex Test 8 - Empty Body with PDF",
        "body": "",
        "attachments": ["complex_test.pdf"],
        "expected_issues": "Should extract info from PDF attachment"
    }
}

# Valid BL costs as specified by user
VALID_BL_COSTS = {
    '001-123': {'ctn_cost': 100, 'service_cost': 100, 'total': 200},
    'NYC220': {'ctn_cost': 100, 'service_cost': 100, 'total': 200},
    'NAM20': {'ctn_cost': 500, 'service_cost': 500, 'total': 1000}
}

def analyze_specific_cases():
    """Analyze the specific cases mentioned by the user"""
    
    print("🔍 DETAILED CASE ANALYSIS")
    print("=" * 80)
    print("📋 Valid BL Numbers and Costs:")
    for bl, costs in VALID_BL_COSTS.items():
        print(f"  {bl}: CTN=${costs['ctn_cost']}, Service=${costs['service_cost']}, Total=${costs['total']}")
    print("=" * 80)
    
    try:
        db_conn = get_db_conn()
        cursor = db_conn.cursor()
        
        # Get emails 810-824 (corresponding to test cases 1-8)
        cursor.execute("""
            SELECT id, sender, subject, body, created_at, processed_for_payments, attachments
            FROM customer_emails 
            WHERE id BETWEEN 810 AND 824
            ORDER BY id DESC
        """)
        
        emails = cursor.fetchall()
        
        # Map email IDs to test cases (reverse order)
        email_to_case = {
            824: 8, 822: 7, 820: 6, 818: 5, 816: 4, 814: 3, 812: 2, 810: 1
        }
        
        for email in emails:
            email_id, sender, subject, body, created_at, processed_for_payments, attachments = email
            
            if email_id not in email_to_case:
                continue
                
            case_num = email_to_case[email_id]
            original_email = ORIGINAL_TEST_EMAILS[case_num]
            
            print(f"\n📧 CASE {case_num}: {subject}")
            print(f"   Email ID: {email_id}")
            print(f"   From: {sender}")
            print(f"   Created: {created_at}")
            print(f"   Processed: {'✅' if processed_for_payments else '❌'}")
            
            # Get AI replies for this email
            cursor.execute("""
                SELECT id, body, confidence_score, created_at
                FROM customer_email_replies 
                WHERE customer_email_id = %s
                ORDER BY created_at DESC
            """, (email_id,))
            
            replies = cursor.fetchall()
            
            if replies:
                for reply in replies:
                    reply_id, reply_body, confidence, reply_created = reply
                    
                    print(f"\n   🤖 AI Reply ID {reply_id} (Confidence: {confidence})")
                    print(f"   Created: {reply_created}")
                    print(f"   Reply: {reply_body}")
                    
                    # Analyze specific issues for each case
                    analyze_case_specific_issues(case_num, original_email, reply_body, email_id)
            else:
                print("   ❌ No AI reply found")
            
            print("-" * 80)
        
        cursor.close()
        db_conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing cases: {e}")
        import traceback
        traceback.print_exc()

def analyze_case_specific_issues(case_num, original_email, ai_reply, email_id):
    """Analyze specific issues for each case"""
    
    print(f"\n   🔍 CASE {case_num} ANALYSIS:")
    
    if case_num == 1:
        # Mixed Payment Types
        print(f"   📋 Original: Mixed payments - NAM20:$250(partial), 001-123:$200(full), NYC220:$180(overpayment)")
        print(f"   🎯 Expected: Detect partial payment ($250 vs $1000), full payment ($200 vs $200), overpayment ($180 vs $200)")
        
        # Check for payment amounts
        import re
        amounts = re.findall(r'\$(\d+)', ai_reply)
        if amounts:
            print(f"   💰 AI mentioned amounts: ${', $'.join(amounts)}")
        else:
            print(f"   ❌ AI didn't mention any payment amounts")
        
        # Check for cost accuracy
        for bl, costs in VALID_BL_COSTS.items():
            if str(costs['total']) in ai_reply:
                print(f"   ✅ {bl}: ${costs['total']} (correct)")
            else:
                print(f"   ❌ {bl}: ${costs['total']} (not found)")
    
    elif case_num == 2:
        # Chinese + English Mixed
        print(f"   📋 Original: Chinese + English, $500 payment for NYC220")
        print(f"   🎯 Expected: Provide CTN numbers and confirm $500 payment")
        
        if 'CTN' in ai_reply or 'ctn' in ai_reply:
            print(f"   ✅ Mentioned CTN information")
        else:
            print(f"   ❌ Didn't mention CTN information")
        
        if '$500' in ai_reply:
            print(f"   ✅ Confirmed $500 payment")
        else:
            print(f"   ❌ Didn't confirm $500 payment")
    
    elif case_num == 3:
        # PDF with Multiple BLs
        print(f"   📋 Original: PDF attachment with multiple BLs")
        print(f"   🎯 Expected: Extract BL numbers and payment info from PDF")
        
        bls_found = []
        for bl in VALID_BL_COSTS.keys():
            if bl in ai_reply:
                bls_found.append(bl)
        
        if bls_found:
            print(f"   ✅ Found BLs: {', '.join(bls_found)}")
        else:
            print(f"   ❌ No BLs extracted from PDF")
    
    elif case_num == 4:
        # Underpayment Scenario
        print(f"   📋 Original: Customer sent $300 total")
        print(f"   🎯 Expected: Total cost $1400 (NAM20:$1000 + 001-123:$200 + NYC220:$200), outstanding $1100")
        
        total_cost = 1000 + 200 + 200  # $1400
        customer_paid = 300
        outstanding = total_cost - customer_paid  # $1100
        
        if str(outstanding) in ai_reply or '1100' in ai_reply:
            print(f"   ✅ Correctly identified outstanding amount: ${outstanding}")
        else:
            print(f"   ❌ Didn't calculate outstanding amount correctly")
        
        if str(total_cost) in ai_reply or '1400' in ai_reply:
            print(f"   ✅ Mentioned total cost: ${total_cost}")
        else:
            print(f"   ❌ Didn't mention total cost")
    
    elif case_num == 5:
        # Invalid BL Mixed with Valid
        print(f"   📋 Original: Mix of valid and invalid BLs")
        print(f"   🎯 Expected: Identify valid vs invalid BLs")
        
        if 'invalid' in ai_reply.lower():
            print(f"   ✅ Mentioned invalid BLs")
        else:
            print(f"   ❌ Didn't mention invalid BLs")
        
        valid_bls_found = []
        for bl in VALID_BL_COSTS.keys():
            if bl in ai_reply:
                valid_bls_found.append(bl)
        
        if valid_bls_found:
            print(f"   ✅ Found valid BLs: {', '.join(valid_bls_found)}")
        else:
            print(f"   ❌ No valid BLs mentioned")
    
    elif case_num == 6:
        # Business Hours + Payment Methods + Wrong Amount
        print(f"   📋 Original: Customer asking how to pay, mentions NAM20:$250 (wrong amount)")
        print(f"   🎯 Expected: Provide payment instructions and correct NAM20 amount ($1000)")
        
        if 'business hours' in ai_reply.lower() or 'payment method' in ai_reply.lower():
            print(f"   ✅ Answered business hours/payment methods question")
        else:
            print(f"   ❌ Didn't answer business hours/payment methods question")
        
        if '$1000' in ai_reply and 'NAM20' in ai_reply:
            print(f"   ✅ Corrected NAM20 amount to $1000")
        elif '$250' in ai_reply and 'NAM20' in ai_reply:
            print(f"   ❌ Didn't correct wrong NAM20 amount ($250)")
        else:
            print(f"   ⚠️  Didn't mention NAM20 amount")
    
    elif case_num == 7:
        # CTN Processing Time
        print(f"   📋 Original: Customer asking about CTN processing time")
        print(f"   🎯 Expected: Answer CTN processing time question")
        
        if 'time' in ai_reply.lower() and ('CTN' in ai_reply or 'ctn' in ai_reply):
            print(f"   ✅ Answered CTN processing time question")
        else:
            print(f"   ❌ Didn't answer CTN processing time question")
        
        # Check for fee information
        fees_mentioned = 0
        for bl, costs in VALID_BL_COSTS.items():
            if str(costs['total']) in ai_reply and bl in ai_reply:
                fees_mentioned += 1
        
        if fees_mentioned > 0:
            print(f"   ✅ Mentioned fees for {fees_mentioned} BLs")
        else:
            print(f"   ❌ Didn't mention fees")
    
    elif case_num == 8:
        # Empty Body with PDF
        print(f"   📋 Original: Empty body with PDF attachment")
        print(f"   🎯 Expected: Extract info from PDF")
        
        bls_found = []
        for bl in VALID_BL_COSTS.keys():
            if bl in ai_reply:
                bls_found.append(bl)
        
        if bls_found:
            print(f"   ✅ Extracted BLs from PDF: {', '.join(bls_found)}")
        else:
            print(f"   ❌ No BLs extracted from PDF")

if __name__ == '__main__':
    analyze_specific_cases() 