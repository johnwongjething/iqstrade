#!/usr/bin/env python3
"""
Retrieve 16 Email Results
Analyzes the results of the 16 test emails sent by auto_send_16_test_emails.py
"""
import os
import sys
import json
from datetime import datetime, timedelta
from config import get_db_conn
from email_classification_validator import validate_email_classification, email_validator

def retrieve_email_results():
    """Retrieve and analyze results of the 16 test emails"""
    
    print("🔍 RETRIEVING 16 EMAIL RESULTS")
    print("=" * 80)
    
    try:
        db_conn = get_db_conn()
        cursor = db_conn.cursor()
        
        # Get emails from the last 30 minutes (assuming emails were sent recently)
        cutoff_time = datetime.now() - timedelta(minutes=30)
        
        print(f"🔍 Looking for emails after: {cutoff_time}")
        
        # First, let's see what emails exist
        cursor.execute("""
            SELECT id, sender, subject, created_at
            FROM customer_emails 
            WHERE created_at >= %s
            ORDER BY created_at DESC
            LIMIT 10
        """, (cutoff_time,))
        
        recent_emails = cursor.fetchall()
        print(f"📧 Found {len(recent_emails)} recent emails:")
        for email in recent_emails:
            print(f"   - ID {email[0]}: {email[2]} (from {email[1]})")
        
        # Now look for test emails specifically
        cursor.execute("""
            SELECT id, sender, subject, body, created_at, processed_for_payments, attachments
            FROM customer_emails 
            WHERE created_at >= %s AND subject LIKE '%%TEST%%'
            ORDER BY created_at DESC
        """, (cutoff_time,))
        
        emails = cursor.fetchall()
        
        if not emails:
            print("❌ No test emails found in the last 30 minutes")
            print("   Make sure you've run: python auto_send_16_test_emails.py")
            return
        
        print(f"📧 Found {len(emails)} test emails")
        print("-" * 80)
        
        # Expected test emails
        expected_emails = [
            "Complex Test 1 - Mixed Payment Types",
            "Complex Test 2 - Chinese + English Mixed", 
            "Complex Test 3 - PDF with Multiple BLs",
            "Complex Test 4 - Underpayment Scenario",
            "Complex Test 5 - Invalid BL Mixed with Valid",
            "Complex Test 6 - Business Hours + Payment Methods",
            "Complex Test 7 - CTN Processing Time",
            "Complex Test 8 - Empty Body with PDF",
            "Fwd: 1 - CTN Request + Business Hours",
            "Fwd: 2 - Fee Inquiry + Payment Status",
            "Fwd: 3 - Payment Receipt (Overpayment)",
            "Fwd: 4 - Multiple BL Fee Inquiry",
            "Fwd: 5 - Payment Receipt (Bank Reference Test)",
            "Fwd: 6 - PDF Payment Receipt",
            "Fwd: 7 - Complex Payment with Multiple BLs",
            "Fwd: 8 - Invoice + CTN Request (Invalid BL Test)"
        ]
        
        # Analyze each email
        analysis_results = []
        
        for email in emails:
            email_id, sender, subject, body, created_at, processed_for_payments, attachments = email
            
            # Extract test number and type from subject
            test_info = extract_test_info(subject)
            
            print(f"\n📧 Email ID {email_id}: {test_info['clean_subject']}")
            print(f"   Type: {test_info['type']}")
            print(f"   Number: {test_info['number']}")
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
                    reply_id, reply_body, confidence, reply_created = reply
                    
                    print(f"\n   🤖 AI Reply ID {reply_id} (Confidence: {confidence})")
                    print(f"   Created: {reply_created}")
                    print(f"   Reply Preview: {reply_body[:150]}...")
                    
                    # Validate the reply
                    validation_result = validate_email_classification(
                        email_body=body,
                        subject=test_info['clean_subject'],
                        request_types=[],  # We'll extract from the reply
                        ai_reply=reply_body,
                        bl_numbers=extract_bl_numbers(body)
                    )
                    
                    # Store analysis result
                    analysis_result = {
                        'email_id': email_id,
                        'test_type': test_info['type'],
                        'test_number': test_info['number'],
                        'subject': test_info['clean_subject'],
                        'body': body,
                        'reply': reply_body,
                        'confidence': confidence,
                        'validation_result': validation_result,
                        'created_at': created_at,
                        'reply_created_at': reply_created
                    }
                    analysis_results.append(analysis_result)
                    
                    # Display validation issues
                    if validation_result['needs_reclassification']:
                        print(f"   🚨 VALIDATION ISSUES:")
                        if validation_result['missed_request_types']:
                            print(f"      ❌ Missed: {', '.join(validation_result['missed_request_types'])}")
                        if validation_result['amount_validation_issues']:
                            print(f"      💰 Amount Issues: {len(validation_result['amount_validation_issues'])}")
                        if validation_result['recommendations']:
                            print(f"      🔧 Recommendations: {len(validation_result['recommendations'])}")
                    else:
                        print(f"   ✅ Validation: No issues detected")
            else:
                print("   ❌ No AI reply found")
            
            print("-" * 60)
        
        # Generate comprehensive analysis
        generate_analysis_report(analysis_results)
        
        # Save detailed results to file
        save_detailed_results(analysis_results)
        
        cursor.close()
        db_conn.close()
        
    except Exception as e:
        print(f"❌ Error retrieving results: {e}")
        import traceback
        traceback.print_exc()

def extract_test_info(subject):
    """Extract test type and number from subject"""
    # Remove [TEST XX] prefix
    clean_subject = subject.replace('[TEST', '').replace(']', '').strip()
    clean_subject = ' '.join(clean_subject.split()[1:])  # Remove test number
    
    # Determine type and number
    if clean_subject.startswith('Complex Test'):
        test_type = 'Complex'
        number = int(clean_subject.split()[2])
    elif clean_subject.startswith('Fwd:'):
        test_type = 'Simple'
        number = int(clean_subject.split()[1])
    else:
        test_type = 'Unknown'
        number = 0
    
    return {
        'type': test_type,
        'number': number,
        'clean_subject': clean_subject
    }

def extract_bl_numbers(text):
    """Extract BL numbers from text"""
    import re
    bl_pattern = re.compile(r'(?:提单号[:：]?\s*)?(BL-\d{4,}|\d{3,}-\d{3,}|\d{6,}|[A-Z]{2,4}\d{2,})', re.IGNORECASE)
    return list(set(bl_pattern.findall(text)))

def generate_analysis_report(analysis_results):
    """Generate comprehensive analysis report"""
    
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE ANALYSIS REPORT")
    print(f"{'='*80}")
    
    # Statistics
    total_emails = len(analysis_results)
    complex_emails = [r for r in analysis_results if r['test_type'] == 'Complex']
    simple_emails = [r for r in analysis_results if r['test_type'] == 'Simple']
    
    emails_with_validation_issues = [r for r in analysis_results if r['validation_result']['needs_reclassification']]
    emails_with_amount_issues = [r for r in analysis_results if r['validation_result']['amount_validation_issues']]
    
    avg_confidence = sum(r['confidence'] for r in analysis_results if r['confidence']) / len(analysis_results)
    
    print(f"📧 Total Emails Analyzed: {total_emails}")
    print(f"🔷 Complex Test Emails: {len(complex_emails)}")
    print(f"🔶 Simple Test Emails: {len(simple_emails)}")
    print(f"🚨 Emails with Validation Issues: {len(emails_with_validation_issues)}")
    print(f"💰 Emails with Amount Issues: {len(emails_with_amount_issues)}")
    print(f"📈 Average Confidence Score: {avg_confidence:.2f}")
    
    # Specific issue analysis
    print(f"\n🎯 SPECIFIC ISSUE ANALYSIS:")
    
    # CTN Processing Time (Case 7)
    ctn_time_emails = [r for r in analysis_results if 'CTN Processing Time' in r['subject']]
    if ctn_time_emails:
        ctn_email = ctn_time_emails[0]
        if ctn_email['validation_result']['needs_reclassification']:
            print(f"   ❌ Case 7 (CTN Processing Time): Issues detected")
        else:
            print(f"   ✅ Case 7 (CTN Processing Time): No issues")
    
    # Wrong Amount (Case 6)
    wrong_amount_emails = [r for r in analysis_results if 'Business Hours + Payment Methods' in r['subject']]
    if wrong_amount_emails:
        amount_email = wrong_amount_emails[0]
        if amount_email['validation_result']['amount_validation_issues']:
            print(f"   ❌ Case 6 (Wrong Amount): Amount issues detected")
        else:
            print(f"   ✅ Case 6 (Wrong Amount): No amount issues")
    
    # Underpayment (Case 4)
    underpayment_emails = [r for r in analysis_results if 'Underpayment Scenario' in r['subject']]
    if underpayment_emails:
        underpayment_email = underpayment_emails[0]
        if underpayment_email['validation_result']['amount_validation_issues']:
            print(f"   ❌ Case 4 (Underpayment): Amount calculation issues")
        else:
            print(f"   ✅ Case 4 (Underpayment): No calculation issues")
    
    # Success rate by type
    complex_success = len([r for r in complex_emails if not r['validation_result']['needs_reclassification']])
    simple_success = len([r for r in simple_emails if not r['validation_result']['needs_reclassification']])
    
    print(f"\n📊 SUCCESS RATES:")
    print(f"   Complex Tests: {complex_success}/{len(complex_emails)} ({complex_success/len(complex_emails)*100:.1f}%)")
    print(f"   Simple Tests: {simple_success}/{len(simple_emails)} ({simple_success/len(simple_emails)*100:.1f}%)")
    print(f"   Overall: {(complex_success + simple_success)}/{total_emails} ({(complex_success + simple_success)/total_emails*100:.1f}%)")
    
    # Recommendations
    print(f"\n🔧 RECOMMENDATIONS:")
    if len(emails_with_validation_issues) > 0:
        print(f"   🚨 {len(emails_with_validation_issues)} emails need reclassification")
        print(f"   💡 Consider implementing the validation system")
    
    if len(emails_with_amount_issues) > 0:
        print(f"   💰 {len(emails_with_amount_issues)} emails have amount validation issues")
        print(f"   💡 Add amount validation to catch customer errors")
    
    if avg_confidence < 0.8:
        print(f"   📉 Low average confidence ({avg_confidence:.2f}) - consider improving classification")
    else:
        print(f"   📈 Good average confidence ({avg_confidence:.2f})")

def save_detailed_results(analysis_results):
    """Save detailed results to JSON file"""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"email_analysis_results_{timestamp}.json"
    
    # Prepare data for JSON serialization
    serializable_results = []
    for result in analysis_results:
        serializable_result = {
            'email_id': result['email_id'],
            'test_type': result['test_type'],
            'test_number': result['test_number'],
            'subject': result['subject'],
            'body': result['body'],
            'reply': result['reply'],
            'confidence': result['confidence'],
            'validation_result': result['validation_result'],
            'created_at': result['created_at'].isoformat() if result['created_at'] else None,
            'reply_created_at': result['reply_created_at'].isoformat() if result['reply_created_at'] else None
        }
        serializable_results.append(serializable_result)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed results saved to: {filename}")

if __name__ == '__main__':
    retrieve_email_results() 