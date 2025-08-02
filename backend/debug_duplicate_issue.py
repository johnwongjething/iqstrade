#!/usr/bin/env python3
"""
Debug Duplicate Detection Issue
Investigate why odd-numbered emails are being skipped
"""

import os
import sys
from datetime import datetime, timedelta
from config import get_db_conn

def investigate_duplicate_issue():
    """Investigate the duplicate detection issue"""
    
    print("🔍 INVESTIGATING DUPLICATE DETECTION ISSUE")
    print("=" * 50)
    
    try:
        db_conn = get_db_conn()
        cursor = db_conn.cursor()
        
        # Check recent emails for missing IDs
        print("\n📧 Checking recent email IDs...")
        cursor.execute("""
            SELECT id, sender, subject, created_at, message_id
            FROM customer_emails 
            WHERE created_at >= %s
            ORDER BY id ASC
        """, (datetime.now() - timedelta(hours=2),))
        
        emails = cursor.fetchall()
        
        if not emails:
            print("❌ No recent emails found")
            return
        
        print(f"📊 Found {len(emails)} recent emails")
        
        # Check for gaps in ID sequence
        ids = [email[0] for email in emails]
        print(f"📋 Email IDs: {ids}")
        
        # Find gaps
        gaps = []
        for i in range(len(ids) - 1):
            if ids[i+1] - ids[i] > 1:
                gaps.append((ids[i], ids[i+1]))
        
        if gaps:
            print(f"🚨 Found {len(gaps)} gaps in ID sequence:")
            for start, end in gaps:
                print(f"   Gap: {start} -> {end} (missing {end - start - 1} emails)")
        else:
            print("✅ No gaps found in recent emails")
        
        # Check message_id duplicates
        print("\n🔍 Checking for message_id duplicates...")
        cursor.execute("""
            SELECT message_id, COUNT(*) as count, MIN(id) as first_id, MAX(id) as last_id
            FROM customer_emails 
            WHERE message_id IS NOT NULL AND created_at >= %s
            GROUP BY message_id
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """, (datetime.now() - timedelta(hours=2),))
        
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"🚨 Found {len(duplicates)} duplicate message_ids:")
            for msg_id, count, first_id, last_id in duplicates:
                print(f"   Message-ID: {msg_id}")
                print(f"   Count: {count}, IDs: {first_id} -> {last_id}")
        else:
            print("✅ No duplicate message_ids found")
        
        # Check the duplicate handling logic
        print("\n🔧 Checking duplicate handling logic...")
        
        # Look at recent emails with same subject
        cursor.execute("""
            SELECT subject, COUNT(*) as count, MIN(id) as first_id, MAX(id) as last_id
            FROM customer_emails 
            WHERE created_at >= %s AND subject LIKE '%TEST%'
            GROUP BY subject
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """, (datetime.now() - timedelta(hours=2),))
        
        subject_duplicates = cursor.fetchall()
        
        if subject_duplicates:
            print(f"🚨 Found {len(subject_duplicates)} duplicate subjects:")
            for subject, count, first_id, last_id in subject_duplicates:
                print(f"   Subject: {subject}")
                print(f"   Count: {count}, IDs: {first_id} -> {last_id}")
                
                # Check if these have different message_ids
                cursor.execute("""
                    SELECT id, message_id, created_at
                    FROM customer_emails 
                    WHERE subject = %s AND created_at >= %s
                    ORDER BY id
                """, (subject, datetime.now() - timedelta(hours=2)))
                
                details = cursor.fetchall()
                for detail in details:
                    print(f"      ID {detail[0]}: Message-ID = {detail[1]}, Created = {detail[2]}")
        else:
            print("✅ No duplicate subjects found")
        
        # Check the ON CONFLICT logic
        print("\n🔍 Analyzing ON CONFLICT behavior...")
        
        # Look at emails that might have been skipped
        cursor.execute("""
            SELECT id, sender, subject, message_id, created_at
            FROM customer_emails 
            WHERE created_at >= %s AND subject LIKE '%TEST%'
            ORDER BY id
        """, (datetime.now() - timedelta(hours=2),))
        
        test_emails = cursor.fetchall()
        
        print(f"📧 Test emails found: {len(test_emails)}")
        for email in test_emails:
            print(f"   ID {email[0]}: {email[2]} (Message-ID: {email[3]})")
        
        # Check if there are emails with NULL message_id
        cursor.execute("""
            SELECT COUNT(*) 
            FROM customer_emails 
            WHERE message_id IS NULL AND created_at >= %s
        """, (datetime.now() - timedelta(hours=2),))
        
        null_message_ids = cursor.fetchone()[0]
        print(f"\n📊 Emails with NULL message_id: {null_message_ids}")
        
        if null_message_ids > 0:
            print("🚨 This could cause duplicate detection issues!")
            print("   Emails without message_id might be treated as duplicates")
        
    except Exception as e:
        print(f"❌ Error investigating: {e}")
        import traceback
        traceback.print_exc()

def check_duplicate_logic():
    """Check the duplicate handling logic in the code"""
    
    print("\n🔍 CHECKING DUPLICATE LOGIC IN CODE")
    print("=" * 40)
    
    # Check utils/ingest_emails.py
    try:
        with open("utils/ingest_emails.py", "r", encoding="utf-8") as f:
            content = f.read()
        
        # Look for ON CONFLICT logic
        if "ON CONFLICT" in content:
            print("✅ Found ON CONFLICT logic in utils/ingest_emails.py")
            
            # Find the specific lines
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if "ON CONFLICT" in line:
                    print(f"   Line {i+1}: {line.strip()}")
                    # Show context
                    for j in range(max(0, i-2), min(len(lines), i+3)):
                        if j == i:
                            print(f"   >>> {j+1}: {lines[j].strip()}")
                        else:
                            print(f"      {j+1}: {lines[j].strip()}")
        else:
            print("❌ No ON CONFLICT logic found")
        
        # Look for duplicate handling
        if "duplicate" in content.lower():
            print("✅ Found duplicate handling logic")
        else:
            print("❌ No explicit duplicate handling found")
            
    except Exception as e:
        print(f"❌ Error reading file: {e}")

if __name__ == "__main__":
    investigate_duplicate_issue()
    check_duplicate_logic() 