#!/usr/bin/env python3
"""
Check for new complex emails in database
"""

from config import get_db_conn

def check_new_emails():
    """Check for new complex emails"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    # Check for complex test emails
    cursor.execute("""
        SELECT id, subject, created_at, processed_at, classification, openai_processed
        FROM customer_emails 
        WHERE subject LIKE '%Complex Test%'
        ORDER BY created_at DESC
        LIMIT 10
    """)
    
    emails = cursor.fetchall()
    
    if emails:
        print("📧 Found Complex Test Emails:")
        print("=" * 50)
        for email in emails:
            print(f"ID: {email[0]}")
            print(f"Subject: {email[1]}")
            print(f"Created: {email[2]}")
            print(f"Processed: {email[3]}")
            print(f"Classification: {email[4]}")
            print(f"OpenAI Processed: {email[5]}")
            print("-" * 30)
    else:
        print("❌ No Complex Test emails found in database")
    
    # Check total recent emails
    cursor.execute("""
        SELECT COUNT(*) 
        FROM customer_emails 
        WHERE created_at > NOW() - INTERVAL '1 hour'
    """)
    
    recent_count = cursor.fetchone()[0]
    print(f"\n📊 Recent emails (last hour): {recent_count}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_new_emails() 