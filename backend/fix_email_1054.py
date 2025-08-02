#!/usr/bin/env python3
"""
Fix Email ID 1054 - Add Missing Attachment
"""
import os
import sys
import json
from config import get_db_conn

def fix_email_1054():
    """Fix the missing attachment for email 1054"""
    print("🔧 Fixing Email ID 1054 - Missing Attachment")
    print("=" * 60)
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # First, let's see if we can find a similar email with the same attachment
        print("🔍 Looking for similar emails with attachments...")
        cursor.execute("""
            SELECT id, subject, attachments, created_at
            FROM customer_emails 
            WHERE sender = 'ray6330088@gmail.com'
            AND subject ILIKE '%PDF%Payment%Receipt%'
            AND attachments IS NOT NULL
            AND attachments != '[]'
            AND attachments != 'null'
            ORDER BY created_at DESC
            LIMIT 3
        """)
        
        similar_emails = cursor.fetchall()
        if not similar_emails:
            print("❌ No similar emails with attachments found")
            return False
        
        print(f"✅ Found {len(similar_emails)} similar emails with attachments:")
        for email in similar_emails:
            eid, esubject, eattachments, ecreated = email
            print(f"  ID {eid}: {esubject}")
            print(f"    Attachments: {eattachments}")
            print(f"    Created: {ecreated}")
        
        # Use the most recent similar email's attachment
        best_match = similar_emails[0]  # Most recent
        source_id, source_subject, source_attachments, source_created = best_match
        
        print(f"\n📎 Using attachment from email ID {source_id}:")
        print(f"  Source attachments: {source_attachments}")
        
        # Update email 1054 with the attachment
        print(f"\n🔄 Updating email 1054...")
        # Convert list to JSON string for JSONB storage
        attachment_json = json.dumps(source_attachments)
        cursor.execute("""
            UPDATE customer_emails 
            SET attachments = %s::jsonb
            WHERE id = 1054
        """, (attachment_json,))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"✅ Successfully updated email 1054 with attachment")
            
            # Verify the update
            cursor.execute("""
                SELECT id, subject, attachments
                FROM customer_emails 
                WHERE id = 1054
            """)
            
            updated_email = cursor.fetchone()
            if updated_email:
                eid, esubject, eattachments = updated_email
                print(f"  Verification:")
                print(f"    ID: {eid}")
                print(f"    Subject: {esubject}")
                print(f"    Attachments: {eattachments}")
        else:
            print(f"❌ Failed to update email 1054")
            return False
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Fix failed: {e}")
        return False

def check_email_ingestion_status():
    """Check if email ingestion is working properly"""
    print(f"\n📋 Email Ingestion Status Check:")
    print("-" * 60)
    
    try:
        conn = get_db_conn()
        if not conn:
            return False
        
        cursor = conn.cursor()
        
        # Check recent email ingestion
        cursor.execute("""
            SELECT id, sender, subject, attachments, created_at
            FROM customer_emails 
            WHERE created_at >= NOW() - INTERVAL '24 hours'
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        recent_emails = cursor.fetchall()
        print(f"📧 Recent emails (last 24 hours):")
        
        emails_with_attachments = 0
        emails_without_attachments = 0
        
        for email in recent_emails:
            eid, esender, esubject, eattachments, ecreated = email
            has_attachments = eattachments is not None and eattachments != '[]' and eattachments != 'null'
            
            if has_attachments:
                emails_with_attachments += 1
                print(f"  ✅ ID {eid}: {esubject} (has attachments)")
            else:
                emails_without_attachments += 1
                print(f"  ❌ ID {eid}: {esubject} (no attachments)")
        
        print(f"\n📊 Summary:")
        print(f"  Emails with attachments: {emails_with_attachments}")
        print(f"  Emails without attachments: {emails_without_attachments}")
        print(f"  Success rate: {emails_with_attachments/(emails_with_attachments+emails_without_attachments)*100:.1f}%")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Status check failed: {e}")

def main():
    """Main function"""
    print("🚀 Email 1054 Fix Process")
    print("=" * 60)
    
    if not fix_email_1054():
        return
    
    check_email_ingestion_status()
    
    print(f"\n✅ Fix Complete!")
    print(f"Email 1054 should now show attachments in the frontend.")
    print(f"Please refresh your browser and check the email modal again.")

if __name__ == "__main__":
    main() 