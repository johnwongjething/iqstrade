#!/usr/bin/env python3
"""
Quick check for email status issues
"""

from config import get_db_conn

def quick_check():
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🔍 Quick Email Status Check...")
        
        # Check the most recent email
        cursor.execute("""
            SELECT id, sender, subject, created_at 
            FROM customer_emails 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        latest_email = cursor.fetchone()
        if latest_email:
            email_id, sender, subject, created_at = latest_email
            print(f"Latest email: ID {email_id}, Subject: {subject[:50]}...")
            
            # Check if it has any replies
            cursor.execute("""
                SELECT COUNT(*) as total, 
                       COUNT(CASE WHEN is_draft = FALSE THEN 1 END) as sent
                FROM customer_email_replies 
                WHERE customer_email_id = %s
            """, (email_id,))
            
            result = cursor.fetchone()
            if result:
                total, sent = result
                print(f"Replies: {total} total, {sent} sent")
                
                if sent > 0:
                    print("❌ This email will show as 'Sent' because it has sent replies!")
                    
                    # Show the sent replies
                    cursor.execute("""
                        SELECT id, content, created_at 
                        FROM customer_email_replies 
                        WHERE customer_email_id = %s AND is_draft = FALSE
                    """, (email_id,))
                    
                    replies = cursor.fetchall()
                    for reply in replies:
                        print(f"  Reply {reply[0]}: {reply[1][:50]}... ({reply[2]})")
                else:
                    print("✅ This email should show correct status")
        
        # Check total counts
        cursor.execute("SELECT COUNT(*) FROM customer_emails")
        total_emails = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM customer_email_replies WHERE is_draft = FALSE")
        total_sent_replies = cursor.fetchone()[0]
        
        print(f"\nTotal emails: {total_emails}")
        print(f"Total sent replies: {total_sent_replies}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    quick_check() 