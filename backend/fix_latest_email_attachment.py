#!/usr/bin/env python3
"""
Fix Latest Email Attachment - Email ID 1060
"""
import os
import sys
import json
from config import get_db_conn

def fix_latest_email_attachment():
    """Fix the latest email by adding the missing attachment"""
    print("🔧 Fixing Latest Email Attachment - Email ID 1060")
    print("=" * 60)
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Get the latest email
        cursor.execute("""
            SELECT id, sender, subject, body, created_at, message_id, attachments
            FROM customer_emails 
            WHERE id = 1060
        """)
        
        email = cursor.fetchone()
        if not email:
            print("❌ Email ID 1060 not found")
            return False
        
        id, sender, subject, body, created_at, message_id, attachments = email
        
        print(f"📧 Email Details:")
        print(f"  ID: {id}")
        print(f"  Sender: {sender}")
        print(f"  Subject: {subject}")
        print(f"  Created: {created_at}")
        print(f"  Message ID: {message_id}")
        print(f"  Current attachments: {attachments}")
        
        # Based on the logs, the Cloudinary URL should be:
        cloudinary_url = "https://res.cloudinary.com/dtm46mski/raw/upload/v1753667125/receipts/zlrckk2moodmvpwhhs2n.pdf"
        
        print(f"\n📎 Adding attachment:")
        print(f"  Cloudinary URL: {cloudinary_url}")
        
        # Convert to JSONB format
        attachment_json = json.dumps([cloudinary_url])
        
        # Update the email with the attachment
        cursor.execute("""
            UPDATE customer_emails 
            SET attachments = %s::jsonb
            WHERE id = 1060
        """, (attachment_json,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ Successfully updated email 1060 with attachment")
            
            # Verify the update
            cursor.execute("""
                SELECT id, subject, attachments
                FROM customer_emails 
                WHERE id = 1060
            """)
            
            updated_email = cursor.fetchone()
            if updated_email:
                eid, esubject, eattachments = updated_email
                print(f"  Verification:")
                print(f"    ID: {eid}")
                print(f"    Subject: {esubject}")
                print(f"    Attachments: {eattachments}")
        else:
            print(f"❌ Failed to update email 1060")
            return False
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        return False

def check_duplicate_emails():
    """Check for duplicate emails with the same Message-ID"""
    print(f"\n🔍 Checking for Duplicate Emails:")
    print("-" * 60)
    
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Find emails with duplicate Message-IDs
        cursor.execute("""
            SELECT message_id, COUNT(*) as count, 
                   STRING_AGG(CAST(id AS TEXT), ', ') as email_ids,
                   STRING_AGG(subject, ' | ') as subjects
            FROM customer_emails 
            WHERE message_id IS NOT NULL
            GROUP BY message_id 
            HAVING COUNT(*) > 1
            ORDER BY count DESC
        """)
        
        duplicates = cursor.fetchall()
        if duplicates:
            print(f"Found {len(duplicates)} duplicate Message-IDs:")
            for dup in duplicates:
                message_id, count, email_ids, subjects = dup
                print(f"  Message-ID: {message_id}")
                print(f"    Count: {count}")
                print(f"    Email IDs: {email_ids}")
                print(f"    Subjects: {subjects}")
                print()
        else:
            print("✅ No duplicate Message-IDs found")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking duplicates: {e}")

def main():
    """Main function"""
    print("🚀 Latest Email Attachment Fix")
    print("=" * 60)
    
    if not fix_latest_email_attachment():
        return
    
    check_duplicate_emails()
    
    print(f"\n✅ Fix Complete!")
    print(f"Email 1060 should now show the PDF attachment in the frontend.")
    print(f"Please refresh your browser and check the email modal again.")

if __name__ == "__main__":
    main() 