#!/usr/bin/env python3
"""
Email System Diagnostic Tool - Final Version
Checks for actual variable names used in .env.local
"""

import os
import sys
import json
from datetime import datetime

def check_environment_variables():
    """Check if all required environment variables are set"""
    print("🔍 Checking Environment Variables")
    print("-" * 50)
    
    # Check variables that actually exist in .env.local
    config_vars = [
        ('EMAIL_USERNAME', 'Email Username'),
        ('EMAIL_PASSWORD', 'Email Password'), 
        ('EMAIL_HOST', 'Email Host'),
        ('OPENAI_API_KEY', 'OpenAI API Key'),
        ('DB_NAME', 'Database Name'),
        ('DB_USER', 'Database User'),
        ('DB_PASSWORD', 'Database Password'),
        ('DB_HOST', 'Database Host'),
        ('CLOUDINARY_CLOUD_NAME', 'Cloudinary Cloud Name'),
        ('CLOUDINARY_API_KEY', 'Cloudinary API Key'),
        ('CLOUDINARY_API_SECRET', 'Cloudinary API Secret'),
        ('SMTP_SERVER', 'SMTP Server'),
        ('SMTP_USERNAME', 'SMTP Username'),
        ('SMTP_PASSWORD', 'SMTP Password')
    ]
    
    missing_vars = []
    for var, display_name in config_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {display_name}: {'*' * len(value)} (set)")
        else:
            print(f"❌ {display_name}: NOT SET")
            missing_vars.append(var)
    
    # Check for Railway-specific variables
    railway_vars = ['RAILWAY_ENVIRONMENT', 'PORT']
    print("\n🔍 Railway Environment Variables:")
    for var in railway_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️ {var}: NOT SET (optional)")
    
    if missing_vars:
        print(f"\n⚠️ Missing environment variables: {missing_vars}")
        return False
    else:
        print("\n✅ All required environment variables are set")
        return True

def check_database_connection():
    """Check database connection and email-related tables"""
    print("\n🔍 Checking Database Connection")
    print("-" * 50)
    
    try:
        from config import get_db_conn
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Check if customer_emails table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'customer_emails'
            );
        """)
        emails_table_exists = cursor.fetchone()[0]
        
        if emails_table_exists:
            print("✅ customer_emails table exists")
            
            # Check table structure
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'customer_emails'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            print(f"📋 Table has {len(columns)} columns")
            
            # Check for required columns
            required_columns = ['id', 'subject', 'body', 'from_addr', 'attachments', 'processed_for_payments']
            existing_columns = [col[0] for col in columns]
            
            for col in required_columns:
                if col in existing_columns:
                    print(f"✅ Column '{col}' exists")
                else:
                    print(f"❌ Column '{col}' missing")
            
        else:
            print("❌ customer_emails table does not exist")
        
        # Check bill_of_lading table
        cursor.execute("SELECT COUNT(*) FROM bill_of_lading")
        bl_count = cursor.fetchone()[0]
        print(f"✅ bill_of_lading table has {bl_count} records")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

def check_email_files():
    """Check if email-related files exist"""
    print("\n🔍 Checking Email System Files")
    print("-" * 50)
    
    required_files = [
        'email_ingestor.py',
        'email_scheduler.py',
        'utils/ingest_emails.py',
        'utils/unified_response_handler.py',
        'utils/confidence_scorer.py',
        'invoice_utils.py',
        'cloudinary_utils.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️ Missing files: {missing_files}")
        return False
    else:
        print("\n✅ All required email files exist")
        return True

def check_email_scheduler():
    """Check email scheduler status"""
    print("\n🔍 Checking Email Scheduler")
    print("-" * 50)
    
    try:
        import email_scheduler
        print("✅ email_scheduler.py can be imported")
        
        if hasattr(email_scheduler, 'main'):
            print("✅ main function exists")
        else:
            print("❌ main function missing")
        
        if hasattr(email_scheduler, 'run_as_service'):
            print("✅ run_as_service function exists")
        else:
            print("❌ run_as_service function missing")
        
        return True
        
    except ImportError as e:
        print(f"❌ Cannot import email_scheduler: {e}")
        return False

def check_openai_integration():
    """Check OpenAI integration"""
    print("\n🔍 Checking OpenAI Integration")
    print("-" * 50)
    
    try:
        import openai
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            print("✅ OpenAI API key is set")
            # Test with a simple call using the old API (v0.28)
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                print("✅ OpenAI API call successful")
                return True
            except Exception as e:
                print(f"❌ OpenAI API call failed: {e}")
                return False
        else:
            print("❌ OpenAI API key not set")
            return False
    except ImportError:
        print("❌ OpenAI library not installed")
        return False

def check_cloudinary_integration():
    """Check Cloudinary integration"""
    print("\n🔍 Checking Cloudinary Integration")
    print("-" * 50)
    
    try:
        from cloudinary_utils import upload_filepath_to_cloudinary
        print("✅ cloudinary_utils can be imported")
        
        # Check if Cloudinary config exists
        from config import CloudinaryConfig
        print("✅ CloudinaryConfig exists")
        
        return True
        
    except ImportError as e:
        print(f"❌ Cloudinary integration failed: {e}")
        return False

def test_email_system():
    """Test the email system with new templates"""
    print("\n🔍 Testing Email System")
    print("-" * 50)
    
    try:
        # Test new complex email templates
        from new_complex_emails_v2 import create_new_complex_emails
        emails = create_new_complex_emails()
        print(f"✅ Generated {len(emails)} complex email templates")
        
        # Test dummy Cloudinary links
        from generate_dummy_cloudinary_links import generate_dummy_cloudinary_links
        dummy_links = generate_dummy_cloudinary_links()
        print(f"✅ Generated {len(dummy_links)} dummy Cloudinary links")
        
        return True
        
    except Exception as e:
        print(f"❌ Email system test failed: {e}")
        return False

def main():
    """Main diagnostic function"""
    print("🚀 Email System Diagnostic Tool - Final Version")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run all checks
    env_ok = check_environment_variables()
    db_ok = check_database_connection()
    files_ok = check_email_files()
    scheduler_ok = check_email_scheduler()
    openai_ok = check_openai_integration()
    cloudinary_ok = check_cloudinary_integration()
    email_test_ok = test_email_system()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    checks = [
        ("Environment Variables", env_ok),
        ("Database Connection", db_ok),
        ("Email Files", files_ok),
        ("Email Scheduler", scheduler_ok),
        ("OpenAI Integration", openai_ok),
        ("Cloudinary Integration", cloudinary_ok),
        ("Email System Test", email_test_ok)
    ]
    
    passed = 0
    for name, status in checks:
        status_text = "✅ PASS" if status else "❌ FAIL"
        print(f"{name:25} {status_text}")
        if status:
            passed += 1
    
    print(f"\n📈 Overall Status: {passed}/{len(checks)} checks passed")
    
    if passed == len(checks):
        print("\n🎉 All checks passed! Email system is ready!")
        print("\n📋 Next Steps:")
        print("1. Start email scheduler: python email_scheduler.py")
        print("2. Test with real emails")
        print("3. Monitor email_scheduler.log")
        print("4. Deploy to Railway when ready")
    else:
        print(f"\n⚠️ {len(checks) - passed} issues found.")
        if not env_ok:
            print("\n🔧 Environment Variables Issue:")
            print("Check that your .env.local file has all required variables")
        if not db_ok:
            print("\n🔧 Database Issue:")
            print("Run the database migration scripts")
        if not email_test_ok:
            print("\n🔧 Email System Issue:")
            print("Check the email templates and Cloudinary links")

if __name__ == "__main__":
    main() 