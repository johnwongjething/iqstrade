#!/usr/bin/env python3
"""
Fix Duplicate Detection Issue
Resolve the problem causing odd-numbered emails to be skipped
"""

import os
import sys
from datetime import datetime, timedelta
from config import get_db_conn

def analyze_duplicate_issue():
    """Analyze the duplicate detection issue"""
    
    print("🔍 ANALYZING DUPLICATE DETECTION ISSUE")
    print("=" * 50)
    
    try:
        db_conn = get_db_conn()
        cursor = db_conn.cursor()
        
        # Check recent emails for message_id patterns
        print("\n📧 Checking recent email message_ids...")
        cursor.execute("""
            SELECT id, sender, subject, message_id, created_at
            FROM customer_emails 
            WHERE created_at >= %s AND subject LIKE '%%TEST%%'
            ORDER BY id ASC
        """, (datetime.now() - timedelta(hours=2),))
        
        emails = cursor.fetchall()
        
        if not emails:
            print("❌ No recent test emails found")
            return
        
        print(f"📊 Found {len(emails)} recent test emails")
        
        # Analyze message_id patterns
        message_ids = {}
        for email in emails:
            msg_id = email[3]  # message_id
            if msg_id:
                if msg_id in message_ids:
                    message_ids[msg_id].append(email[0])  # email ID
                else:
                    message_ids[msg_id] = [email[0]]
        
        print(f"\n📋 Message-ID Analysis:")
        print(f"   Unique message_ids: {len(message_ids)}")
        print(f"   Total emails: {len(emails)}")
        
        # Check for duplicates
        duplicates = {msg_id: ids for msg_id, ids in message_ids.items() if len(ids) > 1}
        if duplicates:
            print(f"🚨 Found {len(duplicates)} duplicate message_ids:")
            for msg_id, ids in duplicates.items():
                print(f"   Message-ID: {msg_id}")
                print(f"   Email IDs: {ids}")
        else:
            print("✅ No duplicate message_ids found")
        
        # Check for NULL message_ids
        null_count = sum(1 for email in emails if email[3] is None)
        print(f"\n📊 Emails with NULL message_id: {null_count}")
        
        if null_count > 0:
            print("🚨 This is likely the cause of the issue!")
            print("   Emails with NULL message_id might be treated as duplicates")
        
        # Show the actual email sequence
        print(f"\n📧 Email ID Sequence:")
        for email in emails:
            print(f"   ID {email[0]}: {email[2]} (Message-ID: {email[3]})")
        
    except Exception as e:
        print(f"❌ Error analyzing: {e}")
        import traceback
        traceback.print_exc()

def fix_duplicate_logic():
    """Fix the duplicate detection logic"""
    
    print("\n🔧 FIXING DUPLICATE DETECTION LOGIC")
    print("=" * 40)
    
    # Read the current file
    try:
        with open("utils/ingest_emails.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Find the problematic ON CONFLICT logic
        old_logic = '''            cursor.execute(
                """
                INSERT INTO customer_emails (sender, subject, body, created_at, processed_for_payments, message_id) 
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (message_id) DO NOTHING
                RETURNING id;
                """,
                (from_addr, subject, body_text, datetime.datetime.now(), False, message_id)
            )'''
        
        # Create improved logic that handles NULL message_ids
        new_logic = '''            # Handle duplicate detection with better logic
            if message_id:
                # Try to insert with message_id
                cursor.execute(
                    """
                    INSERT INTO customer_emails (sender, subject, body, created_at, processed_for_payments, message_id) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (message_id) DO NOTHING
                    RETURNING id;
                    """,
                    (from_addr, subject, body_text, datetime.datetime.now(), False, message_id)
                )
                result = cursor.fetchone()
                
                if result:
                    # New email inserted successfully
                    email_id = result[0]
                    debug(f"✅ New email inserted with ID: {email_id}")
                else:
                    # Duplicate detected - get existing email
                    debug(f"🔄 Duplicate email detected with Message-ID: {message_id}")
                    
                    cursor.execute(
                        "SELECT id FROM customer_emails WHERE message_id = %s",
                        (message_id,)
                    )
                    existing_email = cursor.fetchone()
                    
                    if existing_email:
                        email_id = existing_email[0]
                        debug(f"✅ Using existing email ID: {email_id}")
                    else:
                        debug(f"❌ Duplicate detected but existing email not found for Message-ID: {message_id}")
                        continue
            else:
                # No message_id - use subject + sender + timestamp for duplicate detection
                debug(f"⚠️ No Message-ID found, using subject-based duplicate detection")
                
                # Check for recent duplicate by subject and sender
                cursor.execute(
                    """
                    SELECT id FROM customer_emails 
                    WHERE sender = %s AND subject = %s 
                    AND created_at >= %s
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    (from_addr, subject, datetime.datetime.now() - timedelta(minutes=5))
                )
                recent_duplicate = cursor.fetchone()
                
                if recent_duplicate:
                    debug(f"🔄 Recent duplicate detected by subject: {subject}")
                    email_id = recent_duplicate[0]
                else:
                    # Insert new email without message_id
                    cursor.execute(
                        """
                        INSERT INTO customer_emails (sender, subject, body, created_at, processed_for_payments, message_id) 
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id;
                        """,
                        (from_addr, subject, body_text, datetime.datetime.now(), False, None)
                    )
                    result = cursor.fetchone()
                    email_id = result[0]
                    debug(f"✅ New email inserted without Message-ID, ID: {email_id}")'''
        
        # Replace the old logic
        if old_logic in content:
            content = content.replace(old_logic, new_logic)
            
            # Write the fixed file
            with open("utils/ingest_emails.py", "w", encoding="utf-8") as f:
                f.write(content)
            
            print("✅ Fixed duplicate detection logic")
            print("   - Added handling for NULL message_ids")
            print("   - Added subject-based duplicate detection")
            print("   - Improved logging for debugging")
        else:
            print("❌ Could not find the exact logic to replace")
            print("   Manual fix required")
        
    except Exception as e:
        print(f"❌ Error fixing logic: {e}")
        import traceback
        traceback.print_exc()

def test_fix():
    """Test the fix with a simple email"""
    
    print("\n🧪 TESTING THE FIX")
    print("=" * 30)
    
    print("📧 To test the fix:")
    print("   1. Send a test email without Message-ID")
    print("   2. Check if it gets processed correctly")
    print("   3. Send another email with same subject")
    print("   4. Verify duplicate detection works")
    
    print("\n📋 Test email content:")
    print("   Subject: [FIX TEST] Duplicate Detection Test")
    print("   Body: This is a test email to verify duplicate detection fix")
    print("   From: test@example.com")

if __name__ == "__main__":
    analyze_duplicate_issue()
    fix_duplicate_logic()
    test_fix() 