#!/usr/bin/env python3
"""
Analyze AI Replies for Emails ID 810-824
Check accuracy against valid BL numbers and costs
"""
import os
import sys
import json
from datetime import datetime
from config import get_db_conn

# Valid BL numbers and costs as specified by user
VALID_BL_COSTS = {
    '001-123': {'ctn_cost': 100, 'service_cost': 100, 'total': 200},
    'NYC220': {'ctn_cost': 100, 'service_cost': 100, 'total': 200},
    'NAM20': {'ctn_cost': 500, 'service_cost': 500, 'total': 1000}
}

def analyze_ai_replies_810_824():
    """Analyze AI replies for emails ID 810-824"""
    
    print("🔍 AI Reply Analysis for Emails ID 810-824")
    print("=" * 80)
    print("📋 Valid BL Numbers and Costs:")
    for bl, costs in VALID_BL_COSTS.items():
        print(f"  {bl}: CTN=${costs['ctn_cost']}, Service=${costs['service_cost']}, Total=${costs['total']}")
    print("=" * 80)
    
    try:
        db_conn = get_db_conn()
        cursor = db_conn.cursor()
        
        # Get emails 810-824
        cursor.execute("""
            SELECT id, sender, subject, body, created_at, processed_for_payments, attachments
            FROM customer_emails 
            WHERE id BETWEEN 810 AND 824
            ORDER BY id DESC
        """)
        
        emails = cursor.fetchall()
        
        if not emails:
            print("❌ No emails found in range 810-824")
            return
        
        print(f"📧 Found {len(emails)} emails in range 810-824")
        print("-" * 80)
        
        for email in emails:
            email_id, sender, subject, body, created_at, processed_for_payments, attachments = email
            
            print(f"\n📧 Email ID {email_id}: {subject}")
            print(f"   From: {sender}")
            print(f"   Created: {created_at}")
            print(f"   Processed: {'✅' if processed_for_payments else '❌'}")
            print(f"   Attachments: {'✅' if attachments else '❌'}")
            
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
                    reply_id, reply_text, confidence, reply_created = reply
                    
                    print(f"\n   🤖 AI Reply ID {reply_id} (Confidence: {confidence})")
                    print(f"   Created: {reply_created}")
                    print(f"   Reply Preview: {body[:200]}...")
                    
                    # Analyze the reply for accuracy
                    analyze_reply_accuracy(body, email_id, subject)
            else:
                print("   ❌ No AI reply found")
            
            print("-" * 60)
        
        # Summary statistics
        print("\n" + "=" * 80)
        print("📊 SUMMARY STATISTICS")
        print("=" * 80)
        
        # Count emails with replies
        cursor.execute("""
            SELECT COUNT(DISTINCT customer_email_id) 
            FROM customer_email_replies 
            WHERE customer_email_id BETWEEN 810 AND 824
        """)
        emails_with_replies = cursor.fetchone()[0]
        
        print(f"📧 Emails with AI replies: {emails_with_replies}/{len(emails)}")
        
        # Count total replies
        cursor.execute("""
            SELECT COUNT(*) 
            FROM customer_email_replies 
            WHERE customer_email_id BETWEEN 810 AND 824
        """)
        total_replies = cursor.fetchone()[0]
        print(f"🤖 Total AI replies: {total_replies}")
        
        # Average confidence
        cursor.execute("""
            SELECT AVG(confidence_score) 
            FROM customer_email_replies 
            WHERE customer_email_id BETWEEN 810 AND 824
        """)
        avg_confidence = cursor.fetchone()[0]
        if avg_confidence:
            print(f"📈 Average confidence: {avg_confidence:.2f}")
        
        cursor.close()
        db_conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing emails: {e}")
        import traceback
        traceback.print_exc()

def analyze_reply_accuracy(reply_text, email_id, subject):
    """Analyze the accuracy of an AI reply"""
    
    print(f"\n   🔍 ACCURACY ANALYSIS:")
    
    # Check for valid BL numbers mentioned
    found_valid_bls = []
    found_invalid_bls = []
    
    for bl in VALID_BL_COSTS.keys():
        if bl.lower() in reply_text.lower():
            found_valid_bls.append(bl)
    
    # Check for common invalid patterns
    invalid_patterns = ['invalid', 'not found', 'does not exist', 'unknown']
    has_invalid_mentions = any(pattern in reply_text.lower() for pattern in invalid_patterns)
    
    # Check for payment amounts
    import re
    payment_matches = re.findall(r'\$(\d+)', reply_text)
    payment_amounts = [int(amount) for amount in payment_matches]
    
    # Check for cost calculations
    cost_accuracy = []
    for bl in found_valid_bls:
        expected_total = VALID_BL_COSTS[bl]['total']
        if str(expected_total) in reply_text:
            cost_accuracy.append(f"✅ {bl}: ${expected_total} (correct)")
        else:
            cost_accuracy.append(f"❌ {bl}: ${expected_total} (not found)")
    
    # Print analysis results
    if found_valid_bls:
        print(f"   ✅ Valid BLs found: {', '.join(found_valid_bls)}")
    else:
        print(f"   ❌ No valid BLs found")
    
    if has_invalid_mentions:
        print(f"   ⚠️  Invalid BL mentions detected")
    
    if payment_amounts:
        print(f"   💰 Payment amounts mentioned: ${', $'.join(map(str, payment_amounts))}")
    else:
        print(f"   ❌ No payment amounts found")
    
    if cost_accuracy:
        print(f"   📊 Cost accuracy:")
        for accuracy in cost_accuracy:
            print(f"      {accuracy}")
    
    # Overall assessment based on subject
    if 'invalid' in subject.lower():
        if has_invalid_mentions:
            print(f"   ✅ CORRECT: Properly identified invalid BL")
        else:
            print(f"   ❌ INCORRECT: Should have identified invalid BL")
    elif 'underpayment' in subject.lower():
        if any(amount < 200 for amount in payment_amounts):  # Assuming underpayment scenario
            print(f"   ✅ CORRECT: Detected underpayment")
        else:
            print(f"   ❌ INCORRECT: Should have detected underpayment")
    elif 'overpayment' in subject.lower():
        if any(amount > 200 for amount in payment_amounts):  # Assuming overpayment scenario
            print(f"   ✅ CORRECT: Detected overpayment")
        else:
            print(f"   ❌ INCORRECT: Should have detected overpayment")
    else:
        if found_valid_bls and payment_amounts:
            print(f"   ✅ CORRECT: Found valid BLs and payment amounts")
        else:
            print(f"   ⚠️  PARTIAL: Missing some expected information")

if __name__ == '__main__':
    analyze_ai_replies_810_824() 