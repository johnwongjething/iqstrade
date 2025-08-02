#!/usr/bin/env python3
"""
Fix email status by updating sent_at field for replies that should be marked as sent
"""

from db_utils import get_db_conn

def fix_email_status():
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Check current state
        print("Checking current email reply status...")
        cur.execute("""
            SELECT 
                customer_email_id,
                COUNT(*) as total_replies,
                COUNT(CASE WHEN is_draft = FALSE THEN 1 END) as non_draft_count,
                COUNT(CASE WHEN sent_at IS NOT NULL THEN 1 END) as sent_count
            FROM customer_email_replies 
            GROUP BY customer_email_id
            ORDER BY customer_email_id DESC
            LIMIT 10
        """)
        results = cur.fetchall()
        
        print("Current state:")
        for row in results:
            print(f"  Email {row[0]}: total={row[1]}, non_draft={row[2]}, sent={row[3]}")
        
        # Find replies that are marked as non-draft but don't have sent_at set
        cur.execute("""
            SELECT id, customer_email_id, is_draft, sent_at, created_at
            FROM customer_email_replies 
            WHERE is_draft = FALSE AND sent_at IS NULL
            ORDER BY created_at DESC
            LIMIT 10
        """)
        problematic_replies = cur.fetchall()
        
        print(f"\nFound {len(problematic_replies)} replies that need sent_at to be set:")
        for reply in problematic_replies:
            print(f"  Reply {reply[0]} for email {reply[1]}: is_draft={reply[2]}, sent_at={reply[3]}, created_at={reply[4]}")
        
        # Update these replies to have sent_at set to created_at
        if problematic_replies:
            reply_ids = [str(reply[0]) for reply in problematic_replies]
            placeholders = ','.join(['%s'] * len(reply_ids))
            
            cur.execute(f"""
                UPDATE customer_email_replies 
                SET sent_at = created_at 
                WHERE id IN ({placeholders}) AND is_draft = FALSE AND sent_at IS NULL
            """, reply_ids)
            
            updated_count = cur.rowcount
            conn.commit()
            print(f"\n✅ Updated {updated_count} replies with sent_at = created_at")
        else:
            print("\n✅ No problematic replies found")
            
        # Verify the fix
        print("\nVerifying fix...")
        cur.execute("""
            SELECT 
                customer_email_id,
                COUNT(*) as total_replies,
                COUNT(CASE WHEN sent_at IS NOT NULL THEN 1 END) as sent_count
            FROM customer_email_replies 
            GROUP BY customer_email_id
            ORDER BY customer_email_id DESC
            LIMIT 5
        """)
        verify_results = cur.fetchall()
        
        print("After fix:")
        for row in verify_results:
            print(f"  Email {row[0]}: total={row[1]}, sent={row[2]}")
            
    except Exception as e:
        print(f"Error fixing email status: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    fix_email_status() 