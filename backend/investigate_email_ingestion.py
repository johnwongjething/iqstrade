#!/usr/bin/env python3
"""
Investigate Email Ingestion Issues
Find out why attachments are not being saved properly
"""
import os
import sys
import json
from datetime import datetime, timedelta
from config import get_db_conn

def investigate_recent_emails():
    """Investigate recent emails to understand the pattern"""
    print("🔍 Investigating Recent Email Ingestion Issues")
    print("=" * 80)
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Get recent emails with detailed analysis
        cursor.execute("""
            SELECT 
                id, sender, subject, body, created_at, message_id, 
                attachments, processed_for_payments,
                LENGTH(body) as body_length
            FROM customer_emails 
            WHERE created_at >= NOW() - INTERVAL '48 hours'
            ORDER BY created_at DESC
            LIMIT 20
        """)
        
        recent_emails = cursor.fetchall()
        print(f"📧 Analyzing {len(recent_emails)} recent emails...")
        print("-" * 80)
        
        emails_with_attachments = 0
        emails_without_attachments = 0
        emails_with_empty_body = 0
        
        for email in recent_emails:
            eid, sender, subject, body, created_at, message_id, attachments, processed, body_length = email
            
            has_attachments = attachments is not None and attachments != '[]' and attachments != 'null'
            has_body = body and body_length > 0
            
            status = []
            if has_attachments:
                status.append("✅ Has attachments")
                emails_with_attachments += 1
            else:
                status.append("❌ No attachments")
                emails_without_attachments += 1
            
            if has_body:
                status.append("✅ Has body")
            else:
                status.append("❌ Empty body")
                emails_with_empty_body += 1
            
            print(f"ID {eid:4d}: {subject[:50]:<50} | {' | '.join(status)}")
            print(f"      Sender: {sender}")
            print(f"      Created: {created_at}")
            print(f"      Message ID: {message_id}")
            if has_attachments:
                print(f"      Attachments: {attachments}")
            print()
        
        print("=" * 80)
        print(f"📊 Summary (Last 48 hours):")
        print(f"  Total emails: {len(recent_emails)}")
        print(f"  With attachments: {emails_with_attachments}")
        print(f"  Without attachments: {emails_without_attachments}")
        print(f"  Empty bodies: {emails_with_empty_body}")
        print(f"  Success rate: {emails_with_attachments/len(recent_emails)*100:.1f}%")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Investigation failed: {e}")
        return False

def check_email_ingestion_logs():
    """Check email ingestion logs for errors"""
    print(f"\n📋 Email Ingestion Log Analysis:")
    print("-" * 80)
    
    log_files = [
        'email_scheduler.log',
        'email_ingestor.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"📄 Analyzing: {log_file}")
            
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                
                # Look for error patterns
                error_keywords = ['ERROR', 'FAILED', 'Exception', 'Traceback', 'attachment']
                error_lines = []
                
                for line in lines[-100:]:  # Last 100 lines
                    if any(keyword.lower() in line.lower() for keyword in error_keywords):
                        error_lines.append(line.strip())
                
                if error_lines:
                    print(f"  Found {len(error_lines)} potential error lines:")
                    for line in error_lines[-10:]:  # Show last 10 errors
                        print(f"    {line}")
                else:
                    print(f"  No obvious errors found in recent logs")
                    
            except Exception as e:
                print(f"  ❌ Error reading log: {e}")
        else:
            print(f"📄 Log file not found: {log_file}")

def check_cloudinary_config():
    """Check if Cloudinary is properly configured"""
    print(f"\n☁️ Cloudinary Configuration Check:")
    print("-" * 80)
    
    try:
        from config import CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET
        
        print(f"Cloud Name: {'✅ Set' if CLOUDINARY_CLOUD_NAME else '❌ Missing'}")
        print(f"API Key: {'✅ Set' if CLOUDINARY_API_KEY else '❌ Missing'}")
        print(f"API Secret: {'✅ Set' if CLOUDINARY_API_SECRET else '❌ Missing'}")
        
        if CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET:
            print(f"✅ Cloudinary appears to be configured")
        else:
            print(f"❌ Cloudinary configuration incomplete")
            
    except Exception as e:
        print(f"❌ Error checking Cloudinary config: {e}")

def test_email_ingestion_process():
    """Test the email ingestion process"""
    print(f"\n🧪 Testing Email Ingestion Process:")
    print("-" * 80)
    
    try:
        # Check if email_ingestor.py exists and can be imported
        if os.path.exists('email_ingestor.py'):
            print(f"✅ email_ingestor.py found")
            
            # Try to import and check basic functionality
            try:
                import email_ingestor
                print(f"✅ email_ingestor module can be imported")
                
                # Check if key functions exist
                if hasattr(email_ingestor, 'process_email'):
                    print(f"✅ process_email function exists")
                else:
                    print(f"❌ process_email function not found")
                    
            except ImportError as e:
                print(f"❌ Cannot import email_ingestor: {e}")
        else:
            print(f"❌ email_ingestor.py not found")
            
    except Exception as e:
        print(f"❌ Error testing ingestion: {e}")

def suggest_fixes():
    """Suggest potential fixes based on findings"""
    print(f"\n💡 Suggested Fixes:")
    print("-" * 80)
    
    print(f"1. 🔧 Check Email Ingestion Process:")
    print(f"   - Verify email_ingestor.py is working correctly")
    print(f"   - Check if IMAP connection is stable")
    print(f"   - Ensure attachment download is working")
    
    print(f"\n2. ☁️ Verify Cloudinary Upload:")
    print(f"   - Test Cloudinary credentials")
    print(f"   - Check if upload permissions are correct")
    print(f"   - Verify upload folder exists")
    
    print(f"\n3. 🗄️ Database Issues:")
    print(f"   - Check if JSONB conversion is working")
    print(f"   - Verify transaction handling")
    print(f"   - Look for constraint violations")
    
    print(f"\n4. 📧 Email Content Issues:")
    print(f"   - Some emails have empty bodies (forwarded emails?)")
    print(f"   - Check if attachments are being stripped by email provider")
    print(f"   - Verify email parsing logic")

def main():
    """Main function"""
    print("🚀 Email Ingestion Investigation")
    print("=" * 80)
    
    if not investigate_recent_emails():
        return
    
    check_email_ingestion_logs()
    check_cloudinary_config()
    test_email_ingestion_process()
    suggest_fixes()
    
    print(f"\n✅ Investigation Complete!")
    print(f"Based on the findings, you should:")
    print(f"1. Check if your backend server is running")
    print(f"2. Verify email ingestion is working")
    print(f"3. Test Cloudinary upload functionality")

if __name__ == "__main__":
    main() 