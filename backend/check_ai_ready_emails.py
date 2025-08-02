#!/usr/bin/env python3
"""
Check for emails that should show as "AI Reply Ready"
"""

from db_utils import get_db_conn

def check_ai_ready_emails():
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Find emails that have replies but haven't been sent
        cur.execute("""
            SELECT 
                ce.id, 
                ce.sender, 
                ce.subject, 
                ce.created_at,
                COUNT(cer.id) as reply_count,
                COUNT(CASE WHEN cer.sent_at IS NOT NULL THEN 1 END) as sent_count,
                COUNT(CASE WHEN cer.sent_at IS NULL THEN 1 END) as unsent_count
            FROM customer_emails ce
            LEFT JOIN customer_email_replies cer ON ce.id = cer.customer_email_id
            GROUP BY ce.id, ce.sender, ce.subject, ce.created_at
            HAVING COUNT(cer.id) > 0 AND COUNT(CASE WHEN cer.sent_at IS NOT NULL THEN 1 END) = 0
            ORDER BY ce.created_at DESC
        """)
        
        results = cur.fetchall()
        
        if results:
            print("Emails that should show as 'AI Reply Ready':")
            print("-" * 80)
            print(f"{'ID':<4} {'Sender':<30} {'Subject':<30} {'Replies':<8} {'Unsent':<8}")
            print("-" * 80)
            
            for row in results:
                email_id, sender, subject, created_at, reply_count, sent_count, unsent_count = row
                print(f"{email_id:<4} {sender[:30]:<30} {subject[:30]:<30} {reply_count:<8} {unsent_count:<8}")
        else:
            print("✅ No emails found that should show as 'AI Reply Ready'")
            print("All emails with replies have been sent.")
        
        print("\n" + "-" * 80)
        
        # Show all emails with their current status
        cur.execute("""
            SELECT 
                ce.id, 
                ce.sender, 
                ce.subject, 
                ce.created_at,
                COUNT(cer.id) as reply_count,
                COUNT(CASE WHEN cer.sent_at IS NOT NULL THEN 1 END) as sent_count
            FROM customer_emails ce
            LEFT JOIN customer_email_replies cer ON ce.id = cer.customer_email_id
            GROUP BY ce.id, ce.sender, ce.subject, ce.created_at
            ORDER BY ce.created_at DESC
            LIMIT 10
        """)
        
        all_results = cur.fetchall()
        
        print("All emails with their current status:")
        print("-" * 80)
        print(f"{'ID':<4} {'Status':<15} {'Replies':<8} {'Sent':<8} {'Subject':<30}")
        print("-" * 80)
        
        for row in all_results:
            email_id, sender, subject, created_at, reply_count, sent_count = row
            
            if reply_count > 0 and sent_count == 0:
                status = "AI Reply Ready"
            elif reply_count > 0 and sent_count > 0:
                status = "Sent"
            else:
                status = "No AI Reply"
            
            print(f"{email_id:<4} {status:<15} {reply_count:<8} {sent_count:<8} {subject[:30]:<30}")
        
        print("-" * 80)
        
    except Exception as e:
        print(f"Error checking AI ready emails: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_ai_ready_emails() 