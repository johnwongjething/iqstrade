#!/usr/bin/env python3
"""
Fix Example 6 attachments by manually adding 3.pdf to existing emails
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
if not os.path.exists(env_file):
    env_file = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_file)

from db_utils import get_db_conn
from cloudinary_utils import upload_filepath_to_cloudinary

def fix_example6_attachments():
    """Fix Example 6 emails by adding 3.pdf attachment"""
    print("🔧 FIXING EXAMPLE 6 ATTACHMENTS")
    print("=" * 50)
    
    # Check if 3.pdf exists
    pdf_path = "3.pdf"
    if not os.path.exists(pdf_path):
        print(f"❌ {pdf_path} not found in current directory")
        return
    
    print(f"✅ Found {pdf_path}")
    print(f"   Size: {os.path.getsize(pdf_path)} bytes")
    
    # Upload to Cloudinary
    try:
        cloudinary_url = upload_filepath_to_cloudinary(pdf_path, folder="email_attachments")
        print(f"📎 Uploaded to Cloudinary: {cloudinary_url}")
    except Exception as e:
        print(f"❌ Failed to upload to Cloudinary: {e}")
        return
    
    # Find Example 6 emails in database
    conn = get_db_conn()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, subject, sender, attachments 
        FROM customer_emails 
        WHERE subject LIKE '%6%' AND (attachments IS NULL OR attachments = '{}' OR attachments = '[]')
        ORDER BY id DESC
        LIMIT 10
    """)
    
    emails = cursor.fetchall()
    print(f"\n📧 Found {len(emails)} Example 6 emails without attachments:")
    
    for email in emails:
        email_id, subject, sender, attachments = email
        print(f"   ID {email_id}: {subject} - {sender}")
    
    # Update the emails with the attachment
    if emails:
        print(f"\n🔄 Updating emails with attachment...")
        updated_count = 0
        
        # Convert list to JSON string for jsonb column
        attachment_json = json.dumps([cloudinary_url])
        print(f"   Using JSON: {attachment_json}")
        
        for email in emails:
            email_id = email[0]
            try:
                cursor.execute("""
                    UPDATE customer_emails 
                    SET attachments = %s 
                    WHERE id = %s
                """, (attachment_json, email_id))
                updated_count += 1
                print(f"   ✅ Updated email ID {email_id}")
            except Exception as e:
                print(f"   ❌ Failed to update email ID {email_id}: {e}")
                # Rollback and continue with next email
                conn.rollback()
        
        conn.commit()
        print(f"\n✅ Successfully updated {updated_count} emails")
    else:
        print(f"\nℹ️ No Example 6 emails found to update")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    fix_example6_attachments() 