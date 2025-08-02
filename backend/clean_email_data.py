#!/usr/bin/env python3
"""
Clean up all email-related data to start fresh
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def clean_email_data():
    """Clean up all email-related data from database"""
    try:
        print("🧹 Cleaning up email data from database...")
        
        from db_utils import get_db_conn
        
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # 1. Clear email processing locks
        print("1. Clearing email processing locks...")
        cursor.execute("DELETE FROM email_processing_locks")
        print(f"   ✅ Deleted {cursor.rowcount} processing locks")
        
        # 2. Clear customer emails
        print("2. Clearing customer emails...")
        cursor.execute("DELETE FROM customer_emails")
        print(f"   ✅ Deleted {cursor.rowcount} customer emails")
        
        # 3. Reset auto-increment sequences
        print("3. Resetting auto-increment sequences...")
        cursor.execute("SELECT setval(pg_get_serial_sequence('customer_emails', 'id'), 1, false)")
        print("   ✅ Reset customer_emails sequence")
        
        # 4. Commit changes
        conn.commit()
        print("   ✅ Changes committed to database")
        
        # 5. Verify cleanup
        print("4. Verifying cleanup...")
        cursor.execute("SELECT COUNT(*) FROM email_processing_locks")
        locks_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM customer_emails")
        emails_count = cursor.fetchone()[0]
        
        print(f"   📊 email_processing_locks: {locks_count} records")
        print(f"   📊 customer_emails: {emails_count} records")
        
        if locks_count == 0 and emails_count == 0:
            print("✅ Database cleanup completed successfully!")
            print("🎯 Ready for fresh email processing test")
        else:
            print("⚠️ Some data may still exist")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = clean_email_data()
    sys.exit(0 if success else 1) 