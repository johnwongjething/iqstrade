#!/usr/bin/env python3
"""
Simple check for email ID sequence issues
"""

from config import get_db_conn

def check_email_ids():
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🔍 Checking Email ID Sequence...")
        
        # Get recent emails
        cursor.execute("""
            SELECT id, subject, created_at, message_id
            FROM customer_emails 
            ORDER BY created_at DESC
            LIMIT 20
        """)
        
        emails = cursor.fetchall()
        
        print("Recent emails (newest first):")
        print("ID     | Created At | Subject")
        print("-------|------------|------------------")
        
        for email in emails:
            email_id, subject, created_at, message_id = email
            print(f"{email_id:6d} | {created_at.strftime('%H:%M:%S')} | {subject[:30]}...")
        
        # Check for gaps
        print("\nChecking for ID gaps...")
        ids = [email[0] for email in emails]
        ids.sort()
        
        gaps = []
        for i in range(1, len(ids)):
            if ids[i] - ids[i-1] > 1:
                gaps.append((ids[i-1], ids[i], ids[i] - ids[i-1] - 1))
        
        if gaps:
            print(f"Found {len(gaps)} gaps:")
            for prev_id, current_id, gap_size in gaps:
                print(f"  Gap: {prev_id} → {current_id} (missing {gap_size} IDs)")
        else:
            print("No gaps found in recent emails")
        
        # Check message_id duplicates
        cursor.execute("""
            SELECT message_id, COUNT(*) 
            FROM customer_emails 
            WHERE message_id IS NOT NULL
            GROUP BY message_id 
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"\nFound {len(duplicates)} duplicate message_ids!")
        else:
            print("\nNo duplicate message_ids found")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    check_email_ids() 