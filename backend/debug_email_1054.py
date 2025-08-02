#!/usr/bin/env python3
"""
Debug Email ID 1054 - Attachment Issue
"""
import os
import sys
import json
from config import get_db_conn

def debug_email_1054():
    """Debug the specific email that's showing no attachments"""
    print("🔍 Debugging Email ID 1054 - Attachment Issue")
    print("=" * 60)
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Get the specific email
        cursor.execute("""
            SELECT id, sender, subject, body, created_at, message_id, attachments, processed_for_payments
            FROM customer_emails 
            WHERE id = 1054
        """)
        
        email = cursor.fetchone()
        if not email:
            print("❌ Email ID 1054 not found")
            return False
        
        id, sender, subject, body, created_at, message_id, attachments, processed = email
        
        print(f"📧 Email Details:")
        print(f"  ID: {id}")
        print(f"  Sender: {sender}")
        print(f"  Subject: {subject}")
        print(f"  Created: {created_at}")
        print(f"  Message ID: {message_id}")
        print(f"  Processed: {processed}")
        print(f"  Body length: {len(body) if body else 0} characters")
        
        print(f"\n📎 Attachments Analysis:")
        print(f"  Raw attachments: {attachments}")
        print(f"  Type: {type(attachments)}")
        
        if attachments:
            print(f"  JSON representation: {json.dumps(attachments, indent=2)}")
            
            # Try to parse as JSON if it's a string
            if isinstance(attachments, str):
                try:
                    parsed = json.loads(attachments)
                    print(f"  Parsed JSON: {parsed}")
                    print(f"  Parsed type: {type(parsed)}")
                    if isinstance(parsed, list):
                        print(f"  Number of attachments: {len(parsed)}")
                        for i, att in enumerate(parsed):
                            print(f"    Attachment {i+1}: {att}")
                except json.JSONDecodeError as e:
                    print(f"  ❌ Failed to parse as JSON: {e}")
        else:
            print("  ❌ Attachments is NULL or empty")
        
        # Check if there are other emails with similar subjects
        print(f"\n🔍 Similar Emails (same sender, similar subject):")
        cursor.execute("""
            SELECT id, subject, attachments, created_at
            FROM customer_emails 
            WHERE sender = %s 
            AND subject ILIKE %s
            ORDER BY created_at DESC
            LIMIT 5
        """, (sender, '%PDF%Payment%Receipt%'))
        
        similar_emails = cursor.fetchall()
        for email in similar_emails:
            eid, esubject, eattachments, ecreated = email
            print(f"  ID {eid}: {esubject}")
            print(f"    Attachments: {eattachments}")
            print(f"    Created: {ecreated}")
        
        # Check recent emails with attachments
        print(f"\n📎 Recent Emails with Attachments:")
        cursor.execute("""
            SELECT id, sender, subject, attachments, created_at
            FROM customer_emails 
            WHERE attachments IS NOT NULL 
            AND attachments != '[]' 
            AND attachments != 'null'
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        emails_with_attachments = cursor.fetchall()
        for email in emails_with_attachments:
            eid, esender, esubject, eattachments, ecreated = email
            print(f"  ID {eid}: {esubject}")
            print(f"    Sender: {esender}")
            print(f"    Attachments: {eattachments}")
            print(f"    Created: {ecreated}")
        
        # Check the schema of attachments column
        print(f"\n🗄️ Database Schema Check:")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'customer_emails' 
            AND column_name = 'attachments'
        """)
        
        schema = cursor.fetchone()
        if schema:
            column_name, data_type, is_nullable = schema
            print(f"  Column: {column_name}")
            print(f"  Type: {data_type}")
            print(f"  Nullable: {is_nullable}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        return False

def check_email_ingestion_logs():
    """Check if there are any logs about this email's ingestion"""
    print(f"\n📋 Email Ingestion Check:")
    print("-" * 60)
    
    try:
        # Check if there are any log files
        log_files = [
            'email_scheduler.log',
            'email_ingestor.log'
        ]
        
        for log_file in log_files:
            if os.path.exists(log_file):
                print(f"📄 Found log file: {log_file}")
                # Look for lines containing the email ID or sender
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    relevant_lines = [line for line in lines if '1054' in line or 'ray6330088@gmail.com' in line]
                    if relevant_lines:
                        print(f"  Relevant entries:")
                        for line in relevant_lines[-5:]:  # Last 5 relevant lines
                            print(f"    {line.strip()}")
                    else:
                        print(f"  No relevant entries found")
            else:
                print(f"📄 Log file not found: {log_file}")
                
    except Exception as e:
        print(f"❌ Log check failed: {e}")

def main():
    """Main function"""
    print("🚀 Email 1054 Debug Analysis")
    print("=" * 60)
    
    if not debug_email_1054():
        return
    
    check_email_ingestion_logs()
    
    print(f"\n💡 Analysis Complete!")
    print(f"Based on the API response showing empty attachments array,")
    print(f"the issue is likely one of these:")
    print(f"  1. The email was ingested without attachments")
    print(f"  2. Attachments were not properly saved to Cloudinary")
    print(f"  3. The attachments field was not properly populated")
    print(f"  4. There's a data type mismatch in storage/retrieval")

if __name__ == "__main__":
    main() 