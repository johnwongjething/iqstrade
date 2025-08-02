#!/usr/bin/env python3
"""
Simple database connection test
"""
import os
import psycopg2

# Set the database credentials directly for testing
os.environ['DB_NAME'] = 'railway'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'UsfqjqgxiNTHLACQPVTQMbvXAXnWgcLj'
os.environ['DB_HOST'] = 'trolley.proxy.rlwy.net'
os.environ['DB_PORT'] = '22790'

def test_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    
    try:
        conn = psycopg2.connect(
            dbname=os.environ['DB_NAME'],
            user=os.environ['DB_USER'],
            password=os.environ['DB_PASSWORD'],
            host=os.environ['DB_HOST'],
            port=os.environ['DB_PORT']
        )
        
        print("✅ Database connection successful!")
        
        cursor = conn.cursor()
        
        # Check if customer_emails table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'customer_emails'
            );
        """)
        
        if cursor.fetchone()[0]:
            print("✅ customer_emails table exists")
            
            # Check attachments column
            cursor.execute("""
                SELECT column_name, data_type, udt_name
                FROM information_schema.columns 
                WHERE table_name = 'customer_emails' 
                AND column_name = 'attachments'
            """)
            
            result = cursor.fetchone()
            if result:
                column_name, data_type, udt_name = result
                print(f"✅ Attachments column: {column_name} ({data_type})")
                
                # Check existing emails with attachments
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM customer_emails 
                    WHERE attachments IS NOT NULL AND attachments != '[]' AND attachments != 'null'
                """)
                
                count = cursor.fetchone()[0]
                print(f"📧 Emails with attachments: {count}")
                
                if count > 0:
                    # Get a sample email
                    cursor.execute("""
                        SELECT id, sender, subject, attachments, pg_typeof(attachments)
                        FROM customer_emails 
                        WHERE attachments IS NOT NULL AND attachments != '[]' AND attachments != 'null'
                        ORDER BY id DESC 
                        LIMIT 1
                    """)
                    
                    email = cursor.fetchone()
                    if email:
                        email_id, sender, subject, attachments, attachment_type = email
                        print(f"\n📋 Sample email:")
                        print(f"  ID: {email_id}")
                        print(f"  Sender: {sender}")
                        print(f"  Subject: {subject}")
                        print(f"  Attachment Type: {attachment_type}")
                        print(f"  Raw Attachments: {attachments}")
                        
                        # Test parsing
                        if attachments:
                            if isinstance(attachments, list):
                                print(f"  Parsed as list: {attachments}")
                            elif isinstance(attachments, str):
                                try:
                                    import json
                                    parsed = json.loads(attachments)
                                    print(f"  Parsed as JSON: {parsed}")
                                except:
                                    print(f"  Failed to parse as JSON")
                            else:
                                print(f"  Unknown type: {type(attachments)}")
            else:
                print("❌ Attachments column not found")
        else:
            print("❌ customer_emails table does not exist")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection() 