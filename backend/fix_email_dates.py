#!/usr/bin/env python3
"""
Fix email date issues by extracting actual email dates instead of using processing time
"""

import email
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from config import get_db_conn

def fix_email_dates():
    """Fix email dates by extracting actual email dates"""
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        print("🔧 Fixing Email Date Issues...")
        
        # 1. Check current state
        cursor.execute("""
            SELECT id, sender, subject, created_at, message_id
            FROM customer_emails 
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        current_emails = cursor.fetchall()
        print("Current emails (using processing time):")
        for email in current_emails:
            email_id, sender, subject, created_at, message_id = email
            print(f"  ID {email_id}: {created_at} - {subject[:40]}...")
        
        # 2. Check if we have the original email data to extract dates
        print(f"\nChecking if we can extract actual email dates...")
        
        # For now, we'll need to re-process emails to get their actual dates
        # This would require accessing the original email data from IMAP
        
        print(f"\n⚠️  To fix this properly, we need to:")
        print(f"   1. Extract the actual email date from email headers")
        print(f"   2. Use that date instead of datetime.now()")
        print(f"   3. Re-process existing emails or update their dates")
        
        # 3. Show the fix approach
        print(f"\n🔧 Fix approach:")
        print(f"   - Modify parse_email() to extract Date header")
        print(f"   - Use parsedate_to_datetime() to convert to datetime")
        print(f"   - Use email date instead of datetime.now()")
        
        # 4. Create the fix code
        fix_code = '''
def parse_email_with_date(mail, email_id):
    """Parse email and extract actual email date"""
    status, msg_data = mail.fetch(email_id, '(RFC822)')
    msg = email.message_from_bytes(msg_data[0][1])
    
    # Extract Message-ID
    message_id = msg.get('Message-ID')
    
    # Extract actual email date
    date_header = msg.get('Date')
    if date_header:
        try:
            email_date = parsedate_to_datetime(date_header)
            # Ensure timezone awareness
            if email_date.tzinfo is None:
                email_date = email_date.replace(tzinfo=timezone.utc)
        except Exception as e:
            print(f"Warning: Could not parse date '{date_header}': {e}")
            email_date = datetime.now(timezone.utc)
    else:
        email_date = datetime.now(timezone.utc)
    
    # Rest of parsing logic...
    body_text = ""
    attachments = []
    for part in msg.walk():
        # ... existing attachment processing ...
        pass
    
    return body_text, attachments, message_id, email_date
'''
        
        print(f"\n📝 Fix code:")
        print(fix_code)
        
        print(f"\n🎯 Next steps:")
        print(f"   1. Update parse_email() to extract actual email dates")
        print(f"   2. Update ingest_emails() to use email_date instead of datetime.now()")
        print(f"   3. Test with a few emails to verify correct ordering")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_email_dates() 