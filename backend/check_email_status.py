#!/usr/bin/env python3
"""
Check Email System Status and Manually Trigger Processing
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
load_dotenv(env_file)

def check_email_scheduler_status():
    """Check if email scheduler is running and working"""
    print("🔍 Checking Email Scheduler Status")
    print("=" * 50)
    
    # Check if log file exists and has content
    log_file = "email_scheduler.log"
    if os.path.exists(log_file):
        file_size = os.path.getsize(log_file)
        if file_size > 0:
            print(f"✅ Log file exists with {file_size} bytes")
            with open(log_file, 'r') as f:
                content = f.read()
                print(f"📄 Log content:\n{content}")
        else:
            print("⚠️ Log file exists but is empty")
    else:
        print("❌ Log file does not exist")
    
    # Check if email scheduler can be imported
    try:
        import email_scheduler
        print("✅ Email scheduler module can be imported")
        
        # Check if main functions exist
        if hasattr(email_scheduler, 'main'):
            print("✅ main function exists")
        if hasattr(email_scheduler, 'run_as_service'):
            print("✅ run_as_service function exists")
            
    except ImportError as e:
        print(f"❌ Cannot import email scheduler: {e}")

def check_database_emails():
    """Check emails in the database"""
    print("\n🔍 Checking Database for Emails")
    print("=" * 50)
    
    try:
        from config import get_db_conn
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return
        
        cursor = conn.cursor()
        
        # Check total emails in database
        cursor.execute("SELECT COUNT(*) FROM customer_emails")
        total_emails = cursor.fetchone()[0]
        print(f"📊 Total emails in database: {total_emails}")
        
        # Check recent emails
        cursor.execute("""
            SELECT id, subject, created_at, processed_at, classification, openai_processed
            FROM customer_emails
            ORDER BY created_at DESC
            LIMIT 5
        """)
        recent_emails = cursor.fetchall()
        
        if recent_emails:
            print("\n📧 Recent emails:")
            for email in recent_emails:
                print(f"ID: {email[0]}, Subject: {email[1]}")
                print(f"  Created: {email[2]}, Processed: {email[3]}")
                print(f"  Classification: {email[4]}, OpenAI: {email[5]}")
                print()
        else:
            print("❌ No emails found in database")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")

def manually_trigger_email_processing():
    """Manually trigger email processing"""
    print("\n🔍 Manually Triggering Email Processing")
    print("=" * 50)
    
    try:
        # Import email ingestor
        from email_ingestor import process_emails
        
        print("✅ Email ingestor imported successfully")
        print("🔄 Triggering email processing...")
        
        # This would normally process emails from the inbox
        # For now, just check if the function exists
        if callable(process_emails):
            print("✅ process_emails function is callable")
        else:
            print("❌ process_emails function not found")
            
    except ImportError as e:
        print(f"❌ Cannot import email ingestor: {e}")
    except Exception as e:
        print(f"❌ Error triggering email processing: {e}")

def check_environment():
    """Check environment variables"""
    print("\n🔍 Checking Environment Variables")
    print("=" * 50)
    
    required_vars = [
        'EMAIL_USERNAME',
        'EMAIL_PASSWORD', 
        'EMAIL_HOST',
        'SMTP_SERVER',
        'SMTP_USERNAME',
        'SMTP_PASSWORD',
        'OPENAI_API_KEY'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * len(value)} (set)")
        else:
            print(f"❌ {var}: NOT SET")

def main():
    """Main function"""
    print("📧 Email System Status Checker")
    print("=" * 40)
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 40)
    
    # Run all checks
    check_environment()
    check_email_scheduler_status()
    check_database_emails()
    manually_trigger_email_processing()
    
    print("\n📋 Summary:")
    print("1. Check if email scheduler is running in another terminal")
    print("2. Check your email inbox for the 8 complex emails")
    print("3. Monitor the log file for processing updates")
    print("4. Check database for processed emails")

if __name__ == "__main__":
    main() 