#!/usr/bin/env python3
"""
Debug script to test the reply status filter issue
"""

from config import get_db_conn

def debug_filter_issue():
    """Debug the filter issue by checking the database directly"""
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🔍 Debugging Filter Issue...")
        
        # Get some sample emails with their reply status
        cursor.execute("""
            SELECT 
                ce.id, 
                ce.subject, 
                ce.created_at,
                EXISTS(SELECT 1 FROM customer_email_replies WHERE customer_email_id = ce.id) as has_replies,
                EXISTS(SELECT 1 FROM customer_email_replies WHERE customer_email_id = ce.id AND is_draft = FALSE) as has_sent_replies
            FROM customer_emails ce
            ORDER BY ce.created_at DESC
            LIMIT 10
        """)
        
        emails = cursor.fetchall()
        
        print(f"\n📧 Sample Emails from Database:")
        print("ID    | Subject                    | has_replies | has_sent_replies | Status")
        print("-" * 70)
        
        for email in emails:
            email_id, subject, created_at, has_replies, has_sent_replies = email
            
            if has_sent_replies:
                status = "Sent"
            elif has_replies:
                status = "AI Reply Ready"
            else:
                status = "No AI Reply"
            
            print(f"{email_id:5d} | {subject[:25]:<25} | {has_replies:11} | {has_sent_replies:16} | {status}")
        
        # Test the filter logic
        print(f"\n🧪 Testing Filter Logic:")
        
        # Test 'ai_ready' filter
        ai_ready_emails = [e for e in emails if e[3] and not e[4]]  # has_replies and not has_sent_replies
        print(f"   'ai_ready' filter should return {len(ai_ready_emails)} emails")
        for email in ai_ready_emails:
            print(f"     - ID {email[0]}: {email[1][:30]}...")
        
        # Test 'no_reply' filter  
        no_reply_emails = [e for e in emails if not e[3]]  # not has_replies
        print(f"   'no_reply' filter should return {len(no_reply_emails)} emails")
        for email in no_reply_emails:
            print(f"     - ID {email[0]}: {email[1][:30]}...")
        
        print(f"\n✅ Debug completed!")
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    debug_filter_issue() 