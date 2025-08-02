#!/usr/bin/env python3
"""
Test script to insert a sample email with attachments for testing CustomerEmails.js
"""
import os
import sys
import json
import datetime
from config import get_db_conn

def insert_test_email_with_attachments():
    """Insert a test email with attachments to test the frontend display"""
    print("📧 Inserting test email with attachments...")
    
    # Try to connect to database
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Failed to connect to database - make sure your .env.local is set up")
            return False
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("💡 Make sure you have:")
        print("  1. PostgreSQL running")
        print("  2. .env.local file with database credentials")
        print("  3. Database created and schema applied")
        return False
    
    cursor = conn.cursor()
    
    # Test data
    test_email = {
        'sender': 'test@example.com',
        'subject': 'Test Email with Attachments',
        'body': 'This is a test email with multiple attachments for testing the CustomerEmails.js display.',
        'attachments': [
            'https://res.cloudinary.com/demo/image/upload/sample.pdf',
            'https://res.cloudinary.com/demo/image/upload/sample.jpg',
            'https://res.cloudinary.com/demo/image/upload/receipt.pdf'
        ],
        'bl_numbers': ['TEST123', 'TEST456'],
        'message_id': f'test-message-{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}'
    }
    
    try:
        # Insert the test email
        cursor.execute("""
            INSERT INTO customer_emails (sender, subject, body, attachments, bl_numbers, message_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            test_email['sender'],
            test_email['subject'],
            test_email['body'],
            json.dumps(test_email['attachments']),
            test_email['bl_numbers'],
            test_email['message_id'],
            datetime.datetime.now()
        ))
        
        email_id = cursor.fetchone()[0]
        conn.commit()
        
        print(f"✅ Test email inserted with ID: {email_id}")
        print(f"📎 Attachments: {test_email['attachments']}")
        
        # Verify the insertion
        cursor.execute("""
            SELECT id, sender, subject, attachments, pg_typeof(attachments)
            FROM customer_emails 
            WHERE id = %s
        """, (email_id,))
        
        result = cursor.fetchone()
        if result:
            db_id, db_sender, db_subject, db_attachments, db_type = result
            print(f"✅ Verified in database:")
            print(f"   ID: {db_id}")
            print(f"   Sender: {db_sender}")
            print(f"   Subject: {db_subject}")
            print(f"   Attachments: {db_attachments}")
            print(f"   Type: {db_type}")
            
            # Test retrieval like the frontend would
            if db_attachments:
                if isinstance(db_attachments, list):
                    retrieved_attachments = db_attachments
                elif isinstance(db_attachments, str):
                    try:
                        retrieved_attachments = json.loads(db_attachments)
                    except:
                        retrieved_attachments = [db_attachments]
                else:
                    retrieved_attachments = [str(db_attachments)]
                
                print(f"✅ Frontend would receive attachments: {retrieved_attachments}")
            else:
                print("❌ No attachments found in database")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error inserting test email: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        return False

def check_existing_emails():
    """Check existing emails in the database"""
    print("\n📋 Checking existing emails...")
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Failed to connect to database")
            return
        
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, sender, subject, attachments IS NOT NULL as has_attachments
            FROM customer_emails 
            ORDER BY id DESC 
            LIMIT 10
        """)
        
        emails = cursor.fetchall()
        if emails:
            print(f"Found {len(emails)} emails:")
            for email in emails:
                email_id, sender, subject, has_attachments = email
                attachment_status = "📎" if has_attachments else "📭"
                print(f"  {attachment_status} ID: {email_id}, From: {sender}, Subject: {subject}")
        else:
            print("No emails found in database")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking emails: {e}")

if __name__ == "__main__":
    print("🧪 Testing Email Attachments Display")
    print("=" * 50)
    
    check_existing_emails()
    
    success = insert_test_email_with_attachments()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("💡 Now you can:")
        print("  1. Start your backend server: python run_local.py")
        print("  2. Start your frontend: npm start (in frontend directory)")
        print("  3. Go to CustomerEmails page to see the test email with attachments")
    else:
        print("\n❌ Test failed. Please check your database setup.") 