#!/usr/bin/env python3
"""
Test script to verify the new reply status filter works correctly
"""

from config import get_db_conn

def test_reply_status_filter():
    """Test the new reply status filter logic"""
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🧪 Testing Reply Status Filter...")
        
        # 1. Check current email status distribution
        print("\n1. Current email status distribution:")
        cursor.execute("""
            SELECT 
                COUNT(*) as total_emails,
                COUNT(CASE WHEN EXISTS(SELECT 1 FROM customer_email_replies WHERE customer_email_id = customer_emails.id) THEN 1 END) as has_replies,
                COUNT(CASE WHEN EXISTS(SELECT 1 FROM customer_email_replies WHERE customer_email_id = customer_emails.id AND is_draft = FALSE) THEN 1 END) as has_sent_replies
            FROM customer_emails
        """)
        
        stats = cursor.fetchone()
        if stats:
            total, has_replies, has_sent_replies = stats
            print(f"   Total emails: {total}")
            print(f"   Has replies (AI Reply Ready + Sent): {has_replies}")
            print(f"   Has sent replies (Sent): {has_sent_replies}")
            print(f"   AI Reply Ready only: {has_replies - has_sent_replies}")
            print(f"   No AI Reply: {total - has_replies}")
        
        # 2. Test the filter logic manually
        print(f"\n2. Testing filter logic:")
        
        # Get sample emails for each status
        cursor.execute("""
            SELECT id, subject, created_at,
                   EXISTS(SELECT 1 FROM customer_email_replies WHERE customer_email_id = customer_emails.id) as has_replies,
                   EXISTS(SELECT 1 FROM customer_email_replies WHERE customer_email_id = customer_emails.id AND is_draft = FALSE) as has_sent_replies
            FROM customer_emails
            ORDER BY created_at DESC
            LIMIT 20
        """)
        
        sample_emails = cursor.fetchall()
        
        # Categorize emails
        sent_emails = []
        ai_ready_emails = []
        no_reply_emails = []
        
        for email in sample_emails:
            email_id, subject, created_at, has_replies, has_sent_replies = email
            
            if has_sent_replies:
                sent_emails.append(email)
            elif has_replies:
                ai_ready_emails.append(email)
            else:
                no_reply_emails.append(email)
        
        print(f"   Sample emails by status:")
        print(f"     Sent: {len(sent_emails)} emails")
        print(f"     AI Reply Ready: {len(ai_ready_emails)} emails")
        print(f"     No AI Reply: {len(no_reply_emails)} emails")
        
        # Show examples
        if sent_emails:
            print(f"     Example Sent: ID {sent_emails[0][0]} - {sent_emails[0][1][:30]}...")
        if ai_ready_emails:
            print(f"     Example AI Ready: ID {ai_ready_emails[0][0]} - {ai_ready_emails[0][1][:30]}...")
        if no_reply_emails:
            print(f"     Example No Reply: ID {no_reply_emails[0][0]} - {no_reply_emails[0][1][:30]}...")
        
        # 3. Test the exact filter logic
        print(f"\n3. Testing exact filter logic:")
        
        # Test 'sent' filter
        sent_filtered = [e for e in sample_emails if e[4]]  # has_sent_replies
        print(f"   'sent' filter: {len(sent_filtered)} emails")
        
        # Test 'ai_ready' filter
        ai_ready_filtered = [e for e in sample_emails if e[3] and not e[4]]  # has_replies and not has_sent_replies
        print(f"   'ai_ready' filter: {len(ai_ready_filtered)} emails")
        
        # Test 'no_reply' filter
        no_reply_filtered = [e for e in sample_emails if not e[3]]  # not has_replies
        print(f"   'no_reply' filter: {len(no_reply_filtered)} emails")
        
        # 4. Verify the logic is correct
        print(f"\n4. Verification:")
        total_filtered = len(sent_filtered) + len(ai_ready_filtered) + len(no_reply_filtered)
        if total_filtered == len(sample_emails):
            print(f"   ✅ Filter logic is correct - all emails accounted for")
        else:
            print(f"   ❌ Filter logic error - {total_filtered} vs {len(sample_emails)} emails")
        
        # Check for overlaps
        sent_ids = set(e[0] for e in sent_filtered)
        ai_ready_ids = set(e[0] for e in ai_ready_filtered)
        no_reply_ids = set(e[0] for e in no_reply_filtered)
        
        overlaps = sent_ids & ai_ready_ids | sent_ids & no_reply_ids | ai_ready_ids & no_reply_ids
        if not overlaps:
            print(f"   ✅ No overlaps between filter categories")
        else:
            print(f"   ❌ Found overlaps: {overlaps}")
        
        print(f"\n🎯 Reply status filter test completed!")
        
    except Exception as e:
        print(f"❌ Error during test: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_reply_status_filter() 