#!/usr/bin/env python3
"""
Check email status issue - why has_sent_replies is defaulting to true
"""

from db_utils import get_db_conn

def check_email_status_issue():
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Check the customer_emails table structure
        cur.execute("SELECT column_name, data_type, column_default, is_nullable FROM information_schema.columns WHERE table_name = 'customer_emails' ORDER BY ordinal_position")
        columns = cur.fetchall()
        print("customer_emails table structure:")
        for col in columns:
            print(f"  {col[0]}: {col[1]} (default: {col[2]}, nullable: {col[3]})")
        
        # Check the latest emails with actual columns
        cur.execute("""
            SELECT ce.id, ce.sender, ce.subject, ce.created_at, ce.openai_processed,
                   (SELECT COUNT(*) FROM customer_email_replies WHERE customer_email_id = ce.id) as reply_count,
                   (SELECT COUNT(*) FROM customer_email_replies WHERE customer_email_id = ce.id AND auto_send_recommended = true) as auto_send_count
            FROM customer_emails ce 
            ORDER BY ce.created_at DESC 
            LIMIT 5
        """)
        emails = cur.fetchall()
        print(f"\nLatest 5 emails:")
        for email in emails:
            print(f"  ID {email[0]}: {email[1]} - '{email[2]}' - openai_processed={email[4]}, reply_count={email[5]}, auto_send_count={email[6]}")
        
        # Check customer_email_replies table structure
        cur.execute("SELECT column_name, data_type, column_default, is_nullable FROM information_schema.columns WHERE table_name = 'customer_email_replies' ORDER BY ordinal_position")
        reply_columns = cur.fetchall()
        print(f"\ncustomer_email_replies table structure:")
        for col in reply_columns:
            print(f"  {col[0]}: {col[1]} (default: {col[2]}, nullable: {col[3]})")
        
        # Check if there are any emails with replies but openai_processed=false
        cur.execute("""
            SELECT ce.id, ce.sender, ce.subject, ce.openai_processed,
                   (SELECT COUNT(*) FROM customer_email_replies WHERE customer_email_id = ce.id) as reply_count
            FROM customer_emails ce 
            WHERE ce.openai_processed = false 
            AND (SELECT COUNT(*) FROM customer_email_replies WHERE customer_email_id = ce.id) > 0
            ORDER BY ce.created_at DESC 
            LIMIT 5
        """)
        problematic_emails = cur.fetchall()
        print(f"\nProblematic emails (openai_processed=false but has replies):")
        for email in problematic_emails:
            print(f"  ID {email[0]}: {email[1]} - '{email[2]}' - openai_processed={email[3]}, reply_count={email[4]}")
            
        # Check the email_status_view if it exists
        cur.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_name = 'email_status_view' AND table_schema = 'public'
        """)
        view_exists = cur.fetchone()
        if view_exists:
            print(f"\nemail_status_view exists - checking its structure:")
            cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'email_status_view' ORDER BY ordinal_position")
            view_columns = cur.fetchall()
            for col in view_columns:
                print(f"  {col[0]}: {col[1]}")
        else:
            print(f"\nemail_status_view does not exist")
            
    except Exception as e:
        print(f"Error checking email status: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_email_status_issue() 