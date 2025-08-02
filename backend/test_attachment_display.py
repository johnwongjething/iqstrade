#!/usr/bin/env python3
"""
Test script to debug attachment display issues in CustomerEmails.js
"""
import os
import sys
import json
from config import get_db_conn

def test_attachment_storage():
    """Test how attachments are being stored and retrieved"""
    print("🔍 Testing attachment storage and retrieval...")
    
    conn = get_db_conn()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    cursor = conn.cursor()
    
    # Check the current schema
    print("\n📋 Current customer_emails table schema:")
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'customer_emails' 
        ORDER BY ordinal_position
    """)
    columns = cursor.fetchall()
    for col in columns:
        print(f"  {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
    
    # Check existing emails with attachments
    print("\n📧 Checking existing emails with attachments:")
    cursor.execute("""
        SELECT id, sender, subject, attachments, 
               pg_typeof(attachments) as attachment_type
        FROM customer_emails 
        WHERE attachments IS NOT NULL 
        ORDER BY id DESC 
        LIMIT 5
    """)
    emails = cursor.fetchall()
    
    if not emails:
        print("  No emails with attachments found")
    else:
        for email in emails:
            email_id, sender, subject, attachments, attachment_type = email
            print(f"\n  Email ID: {email_id}")
            print(f"  Sender: {sender}")
            print(f"  Subject: {subject}")
            print(f"  Attachment Type: {attachment_type}")
            print(f"  Raw Attachments: {attachments}")
            
            # Try to parse attachments
            if attachments:
                if isinstance(attachments, list):
                    print(f"  Parsed as list: {attachments}")
                elif isinstance(attachments, str):
                    try:
                        parsed = json.loads(attachments)
                        print(f"  Parsed as JSON: {parsed}")
                    except json.JSONDecodeError:
                        print(f"  Failed to parse as JSON: {attachments}")
                else:
                    print(f"  Unknown type: {type(attachments)}")
    
    # Test inserting a sample email with attachments
    print("\n🧪 Testing attachment insertion...")
    test_attachments = [
        "https://res.cloudinary.com/test/image/upload/test1.pdf",
        "https://res.cloudinary.com/test/image/upload/test2.jpg"
    ]
    
    # Try different storage methods
    test_methods = [
        ("JSON string", json.dumps(test_attachments)),
        ("Array format", test_attachments),
        ("Single string", test_attachments[0])
    ]
    
    for method_name, test_data in test_methods:
        print(f"\n  Testing {method_name}: {test_data}")
        try:
            cursor.execute("""
                INSERT INTO customer_emails (sender, subject, body, attachments, message_id)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (
                "test@example.com", 
                f"Test Email - {method_name}", 
                "Test body", 
                test_data,
                f"test-message-{method_name}"
            ))
            test_id = cursor.fetchone()[0]
            conn.commit()
            print(f"    ✅ Inserted with ID: {test_id}")
            
            # Retrieve and check
            cursor.execute("SELECT attachments, pg_typeof(attachments) FROM customer_emails WHERE id = %s", (test_id,))
            result = cursor.fetchone()
            if result:
                stored_attachments, stored_type = result
                print(f"    Retrieved: {stored_attachments} (type: {stored_type})")
            
        except Exception as e:
            print(f"    ❌ Failed: {e}")
            conn.rollback()
    
    cursor.close()
    conn.close()
    
    print("\n✅ Test completed!")

def test_frontend_retrieval():
    """Test how the frontend would retrieve attachments"""
    print("\n🌐 Testing frontend retrieval simulation...")
    
    conn = get_db_conn()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    cursor = conn.cursor()
    
    # Get a sample email with attachments
    cursor.execute("""
        SELECT id, sender, subject, body, attachments, bl_numbers, created_at
        FROM customer_emails 
        WHERE attachments IS NOT NULL 
        ORDER BY id DESC 
        LIMIT 1
    """)
    
    email_row = cursor.fetchone()
    if not email_row:
        print("  No emails with attachments found for testing")
        cursor.close()
        conn.close()
        return
    
    email_id, sender, subject, body, attachments_raw, bl_numbers, created_at = email_row
    
    print(f"  Testing email ID: {email_id}")
    print(f"  Raw attachments from DB: {attachments_raw}")
    print(f"  Attachments type: {type(attachments_raw)}")
    
    # Process attachments like the backend does
    attachments = []
    if attachments_raw:
        if isinstance(attachments_raw, list):
            attachments = attachments_raw
        elif isinstance(attachments_raw, str):
            try:
                attachments = json.loads(attachments_raw)
            except:
                attachments = [attachments_raw]
    
    print(f"  Processed attachments: {attachments}")
    
    # Simulate what the frontend would receive
    email_detail = {
        'id': email_id,
        'sender': sender,
        'subject': subject,
        'body': body,
        'attachments': attachments,
        'bl_numbers': bl_numbers,
        'created_at': created_at.isoformat() if created_at else None
    }
    
    print(f"  Frontend would receive: {json.dumps(email_detail, indent=2)}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    test_attachment_storage()
    test_frontend_retrieval() 