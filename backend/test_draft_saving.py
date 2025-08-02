#!/usr/bin/env python3
"""
Test draft saving with the exact scenario from the user's log
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from email_ingestor_enhanced import save_draft_reply, handle_email_via_openai
from db_utils import get_db_conn

def test_draft_saving():
    """Test with the exact email from the user's log"""
    
    # Email details from the log
    subject = "aaahh"
    body = "Payment for B/L 001-123, NYC220 Amount: $420 Ref: TEST987"
    from_addr = "Jething John <johnwongjething@gmail.com>"
    attachments = []
    
    print("🧪 Testing AI function with exact email from log...")
    print(f"Subject: {subject}")
    print(f"From: {from_addr}")
    print(f"Body: {body}")
    print("-" * 50)
    
    try:
        # Test AI processing
        result = handle_email_via_openai(subject, body, attachments, from_addr)
        
        print("✅ AI function completed successfully!")
        print(f"Classification: {result.get('classification')}")
        print(f"Confidence Score: {result.get('confidence_score')}")
        print(f"Auto Send: {result.get('auto_send')}")
        print(f"Has Custom Reply: {bool(result.get('custom_reply'))}")
        
        # Check if confidence score meets the threshold
        confidence = result.get('confidence_score', 0.0)
        threshold = 0.7
        print(f"\n📊 Confidence Check:")
        print(f"  Confidence: {confidence}")
        print(f"  Threshold: {threshold}")
        print(f"  Meets threshold (>=): {confidence >= threshold}")
        
        if confidence >= threshold and result.get('custom_reply'):
            print("✅ Should save draft reply")
            
            # Test saving draft reply
            print("\n💾 Testing draft reply saving...")
            
            # First, create a test email in the database
            conn = get_db_conn()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO customer_emails (sender, subject, body, created_at, openai_processed, classification)
                VALUES (%s, %s, %s, NOW(), TRUE, %s)
                RETURNING id
            """, (from_addr, subject, body, result.get('classification')))
            
            email_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"✅ Test email created with ID: {email_id}")
            
            # Now test saving the draft reply
            reply_id = save_draft_reply(
                from_addr, 
                f"Re: {subject}", 
                result.get('custom_reply'), 
                {
                    'confidence_score': result.get('confidence_score', 0.0),
                    'classification': result.get('classification', 'general'),
                    'auto_send': result.get('auto_send', False)
                }, 
                email_id
            )
            
            if reply_id:
                print(f"✅ Draft reply saved successfully with ID: {reply_id}")
                
                # Verify it was saved correctly
                conn = get_db_conn()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, customer_email_id, sender, body, is_draft, auto_send_recommended, confidence_score
                    FROM customer_email_replies WHERE id = %s
                """, (reply_id,))
                
                reply_data = cursor.fetchone()
                if reply_data:
                    print(f"✅ Draft reply verified in database:")
                    print(f"  ID: {reply_data[0]}")
                    print(f"  Email ID: {reply_data[1]}")
                    print(f"  Sender: {reply_data[2]}")
                    print(f"  Is Draft: {reply_data[4]}")
                    print(f"  Auto Send Recommended: {reply_data[5]}")
                    print(f"  Confidence Score: {reply_data[6]}")
                else:
                    print("❌ Draft reply not found in database")
                
                cursor.close()
                conn.close()
            else:
                print("❌ Failed to save draft reply")
        else:
            print("❌ Should NOT save draft reply (confidence too low or no custom reply)")
            
    except Exception as e:
        print(f"❌ Error testing draft saving: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_draft_saving() 