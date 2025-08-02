#!/usr/bin/env python3
"""
Debug script to check Example 6 attachments
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
if not os.path.exists(env_file):
    env_file = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_file)

from db_utils import get_db_conn

def debug_email6_attachments():
    """Check Example 6 attachments in database"""
    print("🔍 DEBUGGING EMAIL 6 ATTACHMENTS")
    print("=" * 50)
    
    conn = get_db_conn()
    cursor = conn.cursor()
    
    # Find Example 6 email
    cursor.execute("""
        SELECT id, sender, subject, body, attachments, created_at 
        FROM customer_emails 
        WHERE subject LIKE '%6%' OR subject LIKE '%PDF%' OR subject LIKE '%attachment%'
        ORDER BY id DESC
        LIMIT 10
    """)
    
    emails = cursor.fetchall()
    print(f"Found {len(emails)} emails that might be Example 6:")
    
    for email in emails:
        email_id, sender, subject, body, attachments, created_at = email
        print(f"\n📧 Email ID: {email_id}")
        print(f"   Subject: {subject}")
        print(f"   Sender: {sender}")
        print(f"   Created: {created_at}")
        print(f"   Body length: {len(body) if body else 0}")
        print(f"   Attachments: {attachments}")
        print(f"   Attachments type: {type(attachments)}")
        
        if attachments:
            if isinstance(attachments, list):
                print(f"   Attachments count: {len(attachments)}")
                for i, att in enumerate(attachments):
                    print(f"     {i+1}. {att}")
            else:
                print(f"   Single attachment: {attachments}")
    
    # Also check for emails with PDF attachments
    cursor.execute("""
        SELECT id, sender, subject, attachments 
        FROM customer_emails 
        WHERE attachments IS NOT NULL AND attachments != '{}' AND attachments != '[]' AND attachments != 'null'
        ORDER BY id DESC
        LIMIT 5
    """)
    
    pdf_emails = cursor.fetchall()
    print(f"\n📎 Emails with PDF attachments:")
    for email in pdf_emails:
        email_id, sender, subject, attachments = email
        print(f"   ID {email_id}: {subject} - {attachments}")
    
    # Check the database schema for attachments column
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns 
        WHERE table_name = 'customer_emails' AND column_name = 'attachments'
    """)
    
    schema_info = cursor.fetchone()
    if schema_info:
        print(f"\n📊 Attachments column schema:")
        print(f"   Column: {schema_info[0]}")
        print(f"   Type: {schema_info[1]}")
        print(f"   Nullable: {schema_info[2]}")
    else:
        print(f"\n❌ Attachments column not found in schema")
    
    # Test a specific Example 6 email
    cursor.execute("""
        SELECT id, sender, subject, body, attachments, created_at
        FROM customer_emails
        WHERE subject LIKE '%6%' AND subject LIKE '%PDF%'
        ORDER BY id DESC
        LIMIT 1
    """)
    
    test_email = cursor.fetchone()
    if test_email:
        email_id, sender, subject, body, attachments, created_at = test_email
        print(f"\n🧪 Testing specific Example 6 email:")
        print(f"   ID: {email_id}")
        print(f"   Subject: {subject}")
        print(f"   Sender: {sender}")
        print(f"   Body length: {len(body) if body else 0}")
        print(f"   Attachments raw: {attachments}")
        print(f"   Attachments type: {type(attachments)}")
        
        # Try to parse attachments if it's a JSON string
        if attachments and isinstance(attachments, str):
            try:
                import json
                parsed_attachments = json.loads(attachments)
                print(f"   Parsed attachments: {parsed_attachments}")
                print(f"   Parsed type: {type(parsed_attachments)}")
            except json.JSONDecodeError as e:
                print(f"   Failed to parse JSON: {e}")
    else:
        print(f"\n❌ No Example 6 PDF emails found for testing")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    debug_email6_attachments() 