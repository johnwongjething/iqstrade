#!/usr/bin/env python3
"""
Test email status fix - verify that emails now show correct status
"""

from db_utils import get_db_conn

def test_email_status():
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Test the same logic as the backend
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
        
        results = cur.fetchall()
        
        print("Email Status Test Results:")
        print("-" * 80)
        print(f"{'ID':<4} {'Status':<15} {'Reply Count':<12} {'Sent Count':<12} {'Subject':<30}")
        print("-" * 80)
        
        for row in results:
            email_id, sender, subject, created_at, reply_count, sent_count = row
            
            # Calculate status using the same logic as frontend
            has_replies = reply_count > 0
            has_sent_replies = sent_count > 0
            
            if has_replies and not has_sent_replies:
                status = "AI Reply Ready"
            elif has_replies and has_sent_replies:
                status = "Sent"
            else:
                status = "No AI Reply"
            
            print(f"{email_id:<4} {status:<15} {reply_count:<12} {sent_count:<12} {subject[:30]:<30}")
        
        print("-" * 80)
        
        # Test specific emails from the screenshot
        print("\nTesting specific emails from screenshot:")
        test_emails = [11, 10, 9, 8, 7]  # Email IDs from the screenshot
        
        for email_id in test_emails:
            cur.execute("""
                SELECT 
                    ce.id, 
                    ce.subject,
                    COUNT(cer.id) as reply_count,
                    COUNT(CASE WHEN cer.sent_at IS NOT NULL THEN 1 END) as sent_count
                FROM customer_emails ce
                LEFT JOIN customer_email_replies cer ON ce.id = cer.customer_email_id
                WHERE ce.id = %s
                GROUP BY ce.id, ce.subject
            """, (email_id,))
            
            result = cur.fetchone()
            if result:
                email_id, subject, reply_count, sent_count = result
                has_replies = reply_count > 0
                has_sent_replies = sent_count > 0
                
                if has_replies and not has_sent_replies:
                    status = "AI Reply Ready"
                elif has_replies and has_sent_replies:
                    status = "Sent"
                else:
                    status = "No AI Reply"
                
                print(f"  Email {email_id} ('{subject}'): {status} (replies={reply_count}, sent={sent_count})")
            else:
                print(f"  Email {email_id}: Not found")
                
    except Exception as e:
        print(f"Error testing email status: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    test_email_status() 