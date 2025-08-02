#!/usr/bin/env python3
"""
Check current database schema and attachment storage
"""
import os
import sys
import json
from config import get_db_conn

def check_database_schema():
    """Check the current database schema"""
    print("🔍 Checking current database schema...")
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Check if customer_emails table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'customer_emails'
            );
        """)
        
        if not cursor.fetchone()[0]:
            print("❌ customer_emails table does not exist")
            cursor.close()
            conn.close()
            return False
        
        print("✅ customer_emails table exists")
        
        # Check all columns in customer_emails table
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'customer_emails' 
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print(f"\n📋 customer_emails table schema:")
        print("-" * 80)
        for col in columns:
            column_name, data_type, is_nullable, column_default = col
            nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
            default = f" DEFAULT {column_default}" if column_default else ""
            print(f"  {column_name:<20} {data_type:<15} {nullable:<10}{default}")
        
        # Specifically check attachments column
        cursor.execute("""
            SELECT column_name, data_type, udt_name, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'customer_emails' 
            AND column_name = 'attachments'
        """)
        
        result = cursor.fetchone()
        if result:
            column_name, data_type, udt_name, is_nullable = result
            print(f"\n📎 Attachments column details:")
            print(f"  Column: {column_name}")
            print(f"  Data Type: {data_type}")
            print(f"  UDT Name: {udt_name}")
            print(f"  Nullable: {is_nullable}")
        else:
            print("\n❌ Attachments column not found!")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Schema check failed: {e}")
        return False

def check_existing_emails():
    """Check existing emails and their attachments"""
    print("\n📧 Checking existing emails...")
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM customer_emails")
        total_count = cursor.fetchone()[0]
        print(f"📊 Total emails in database: {total_count}")
        
        # Get emails with attachments
        cursor.execute("""
            SELECT COUNT(*) 
            FROM customer_emails 
            WHERE attachments IS NOT NULL AND attachments != '[]' AND attachments != 'null'
        """)
        with_attachments = cursor.fetchone()[0]
        print(f"📎 Emails with attachments: {with_attachments}")
        
        # Get sample emails with attachments
        cursor.execute("""
            SELECT id, sender, subject, attachments, pg_typeof(attachments) as attachment_type
            FROM customer_emails 
            WHERE attachments IS NOT NULL AND attachments != '[]' AND attachments != 'null'
            ORDER BY id DESC 
            LIMIT 5
        """)
        
        emails = cursor.fetchall()
        if emails:
            print(f"\n📋 Sample emails with attachments:")
            print("-" * 80)
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
                        print(f"  List length: {len(attachments)}")
                    elif isinstance(attachments, str):
                        try:
                            parsed = json.loads(attachments)
                            print(f"  Parsed as JSON: {parsed}")
                            print(f"  JSON type: {type(parsed)}")
                            if isinstance(parsed, list):
                                print(f"  JSON list length: {len(parsed)}")
                        except json.JSONDecodeError as e:
                            print(f"  Failed to parse as JSON: {e}")
                            print(f"  Raw string: {attachments}")
                    else:
                        print(f"  Unknown type: {type(attachments)}")
        else:
            print("\n❌ No emails with attachments found")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Email check failed: {e}")
        return False

def test_api_response():
    """Test what the API would return for an email with attachments"""
    print("\n🌐 Testing API response simulation...")
    
    try:
        conn = get_db_conn()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        
        # Get the latest email with attachments
        cursor.execute("""
            SELECT id, sender, subject, body, attachments, bl_numbers, created_at
            FROM customer_emails 
            WHERE attachments IS NOT NULL AND attachments != '[]' AND attachments != 'null'
            ORDER BY id DESC 
            LIMIT 1
        """)
        
        email_row = cursor.fetchone()
        if not email_row:
            print("❌ No emails with attachments found for API testing")
            cursor.close()
            conn.close()
            return False
        
        email_id, sender, subject, body, attachments_raw, bl_numbers, created_at = email_row
        
        print(f"✅ Testing API for email ID: {email_id}")
        print(f"   Sender: {sender}")
        print(f"   Subject: {subject}")
        print(f"   Raw attachments from DB: {attachments_raw}")
        print(f"   Attachments type: {type(attachments_raw)}")
        
        # Simulate the API processing (like email_routes.py does)
        attachments = []
        if attachments_raw:
            if isinstance(attachments_raw, list):
                attachments = attachments_raw
            elif isinstance(attachments_raw, str):
                try:
                    parsed = json.loads(attachments_raw)
                    if isinstance(parsed, list):
                        attachments = parsed
                    else:
                        attachments = [parsed]
                except:
                    attachments = [attachments_raw]
            else:
                attachments = [str(attachments_raw)]
        
        print(f"   Processed attachments: {attachments}")
        print(f"   Processed type: {type(attachments)}")
        print(f"   Processed length: {len(attachments)}")
        
        # Simulate API response
        api_response = {
            'id': email_id,
            'sender': sender,
            'subject': subject,
            'body': body,
            'attachments': attachments,
            'bl_numbers': bl_numbers,
            'created_at': created_at.isoformat() if created_at else None
        }
        
        print(f"\n📤 API would return:")
        print(json.dumps(api_response, indent=2))
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Main function"""
    print("🔍 Database Schema and Attachment Analysis")
    print("=" * 60)
    
    # Check schema
    if not check_database_schema():
        return
    
    # Check existing emails
    if not check_existing_emails():
        return
    
    # Test API response
    if not test_api_response():
        return
    
    print("\n✅ Analysis completed!")
    print("\n💡 This will help identify why attachments aren't showing in the frontend.")

if __name__ == "__main__":
    main() 