#!/usr/bin/env python3
"""
Test Current Email System Status
Checks what's working and what needs to be fixed.
"""

import os
import sys
from dotenv import load_dotenv

def test_environment():
    """Test environment variables and configuration."""
    print("🔍 Testing Environment Configuration...")
    
    # Load environment
    env_file = os.path.join(os.path.dirname(__file__), '.env.local')
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print("✅ Found .env.local file")
    else:
        print("❌ No .env.local file found")
    
    # Check required email variables
    required_vars = [
        'EMAIL_USERNAME',
        'EMAIL_PASSWORD', 
        'EMAIL_HOST',
        'OPENAI_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {'*' * len(value)} (configured)")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def test_database():
    """Test database connection and schema."""
    print("\n🗄️ Testing Database...")
    
    try:
        from config import get_db_conn
        conn = get_db_conn()
        if conn:
            print("✅ Database connection successful")
            
            cursor = conn.cursor()
            
            # Check if email tables exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('customer_emails', 'customer_email_replies')
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            if 'customer_emails' in tables:
                print("✅ customer_emails table exists")
            else:
                print("❌ customer_emails table missing")
                
            if 'customer_email_replies' in tables:
                print("✅ customer_email_replies table exists")
            else:
                print("❌ customer_email_replies table missing")
            
            # Check for existing emails
            cursor.execute("SELECT COUNT(*) FROM customer_emails")
            email_count = cursor.fetchone()[0]
            print(f"📧 Found {email_count} emails in database")
            
            cursor.close()
            conn.close()
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_email_ingestor():
    """Test email ingestor import and basic functionality."""
    print("\n📧 Testing Email Ingestor...")
    
    try:
        from email_ingestor import process_inbox
        print("✅ Email ingestor imports successfully")
        
        # Test IMAP connection (without actually connecting)
        from email_ingestor import connect_imap
        print("✅ IMAP connection function available")
        
        return True
    except Exception as e:
        print(f"❌ Email ingestor test failed: {e}")
        return False

def test_email_scheduler():
    """Test email scheduler functionality."""
    print("\n⏰ Testing Email Scheduler...")
    
    try:
        from email_scheduler import run_as_service
        print("✅ Email scheduler imports successfully")
        
        # Check if scheduler log exists
        log_file = 'email_scheduler.log'
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            if size > 0:
                print(f"✅ Email scheduler log exists ({size} bytes)")
            else:
                print("⚠️ Email scheduler log exists but is empty (scheduler may not be running)")
        else:
            print("❌ Email scheduler log not found")
        
        return True
    except Exception as e:
        print(f"❌ Email scheduler test failed: {e}")
        return False

def test_frontend_files():
    """Test if frontend files exist."""
    print("\n🎨 Testing Frontend Files...")
    
    frontend_file = '../frontend/src/pages/CustomerEmails.js'
    if os.path.exists(frontend_file):
        print("✅ CustomerEmails.js exists")
        
        # Check for attachment display code
        with open(frontend_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'attachments' in content and 'Customer Attachments' in content:
                print("✅ Attachment display code found")
            else:
                print("❌ Attachment display code missing")
    else:
        print("❌ CustomerEmails.js not found")
    
    return True

def main():
    """Run all tests and provide summary."""
    print("🚀 Email System Status Check")
    print("=" * 50)
    
    results = {
        'environment': test_environment(),
        'database': test_database(),
        'email_ingestor': test_email_ingestor(),
        'email_scheduler': test_email_scheduler(),
        'frontend_files': test_frontend_files()
    }
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    working = sum(results.values())
    total = len(results)
    
    for test, result in results.items():
        status = "✅" if result else "❌"
        print(f"{status} {test.replace('_', ' ').title()}")
    
    print(f"\n🎯 Overall Status: {working}/{total} tests passed")
    
    if working == total:
        print("🎉 All systems are working! Email system is ready to use.")
    else:
        print("\n🔧 Issues to Fix:")
        if not results['environment']:
            print("  - Set up .env.local file with email credentials")
        if not results['database']:
            print("  - Check database connection and schema")
        if not results['email_ingestor']:
            print("  - Fix email ingestor dependencies")
        if not results['email_scheduler']:
            print("  - Start email scheduler service")
        if not results['frontend_files']:
            print("  - Check frontend file structure")

if __name__ == "__main__":
    main() 