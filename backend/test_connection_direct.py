#!/usr/bin/env python3
"""
Direct database connection test
"""
import os
import psycopg2
from dotenv import load_dotenv

def test_direct_connection():
    """Test database connection directly"""
    print("🔍 Testing direct database connection...")
    
    # Load environment variables
    load_dotenv('.env.local')
    
    # Get database credentials
    db_host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_port = os.getenv('DB_PORT', '5432')
    
    print(f"📊 Connecting to: {db_host}:{db_port}/{db_name}")
    
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            connect_timeout=10
        )
        
        print("✅ Database connection successful!")
        
        cursor = conn.cursor()
        
        # Test a simple query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"📊 PostgreSQL version: {version}")
        
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
                
                # Check for emails with attachments
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM customer_emails 
                    WHERE attachments IS NOT NULL AND attachments != '[]' AND attachments != 'null'
                """)
                
                count = cursor.fetchone()[0]
                print(f"📧 Emails with attachments: {count}")
                
                if count > 0:
                    # Get a sample
                    cursor.execute("""
                        SELECT id, sender, subject, attachments
                        FROM customer_emails 
                        WHERE attachments IS NOT NULL AND attachments != '[]' AND attachments != 'null'
                        ORDER BY id DESC 
                        LIMIT 1
                    """)
                    
                    sample = cursor.fetchone()
                    if sample:
                        email_id, sender, subject, attachments = sample
                        print(f"\n📋 Sample email:")
                        print(f"   ID: {email_id}")
                        print(f"   Sender: {sender}")
                        print(f"   Subject: {subject}")
                        print(f"   Attachments: {attachments}")
                        print(f"   Type: {type(attachments)}")
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
    test_direct_connection() 