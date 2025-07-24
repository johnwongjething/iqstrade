#!/usr/bin/env python3
"""
Database Schema Checker
Checks what columns are missing for OpenAI integration
"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_conn():
    """Get database connection"""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    else:
        return psycopg2.connect(
            dbname=os.getenv('DB_NAME', 'railway'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432')
        )

def check_table_columns(table_name, expected_columns):
    """Check if table has all expected columns"""
    conn = get_db_conn()
    cur = conn.cursor()
    
    # Get current columns
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position
    """, (table_name,))
    
    current_columns = {row[0]: row[1] for row in cur.fetchall()}
    
    print(f"\n📋 Table: {table_name}")
    print("=" * 50)
    
    missing_columns = []
    existing_columns = []
    
    for col_name, col_type in expected_columns.items():
        if col_name in current_columns:
            existing_columns.append(f"✅ {col_name} ({current_columns[col_name]})")
        else:
            missing_columns.append(f"❌ {col_name} ({col_type})")
    
    # Show existing columns
    for col in existing_columns:
        print(col)
    
    # Show missing columns
    if missing_columns:
        print("\n🚨 MISSING COLUMNS:")
        for col in missing_columns:
            print(col)
    else:
        print("\n✅ All expected columns are present!")
    
    cur.close()
    conn.close()
    
    return len(missing_columns) == 0

def check_indexes(table_name, expected_indexes):
    """Check if table has all expected indexes"""
    conn = get_db_conn()
    cur = conn.cursor()
    
    # Get current indexes
    cur.execute("""
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename = %s
    """, (table_name,))
    
    current_indexes = {row[0] for row in cur.fetchall()}
    
    print(f"\n🔍 Indexes for: {table_name}")
    print("-" * 30)
    
    missing_indexes = []
    existing_indexes = []
    
    for index_name in expected_indexes:
        if index_name in current_indexes:
            existing_indexes.append(f"✅ {index_name}")
        else:
            missing_indexes.append(f"❌ {index_name}")
    
    # Show existing indexes
    for idx in existing_indexes:
        print(idx)
    
    # Show missing indexes
    if missing_indexes:
        print("\n🚨 MISSING INDEXES:")
        for idx in missing_indexes:
            print(idx)
    else:
        print("\n✅ All expected indexes are present!")
    
    cur.close()
    conn.close()
    
    return len(missing_indexes) == 0

def main():
    """Main function to check database schema"""
    print("🔍 DATABASE SCHEMA CHECK FOR OPENAI INTEGRATION")
    print("=" * 60)
    
    # Expected columns for customer_emails
    customer_emails_columns = {
        'id': 'integer',
        'sender': 'text',
        'subject': 'text',
        'body': 'text',
        'attachments': 'jsonb',
        'bl_numbers': 'text[]',
        'created_at': 'timestamp',
        'processed_at': 'timestamp',
        'classification': 'varchar(50)',
        'openai_processed': 'boolean'
    }
    
    # Expected columns for customer_email_replies
    customer_email_replies_columns = {
        'id': 'integer',
        'customer_email_id': 'integer',
        'sender': 'text',
        'body': 'text',
        'created_at': 'timestamp',
        'is_draft': 'boolean',
        'sent_at': 'timestamp',
        'sent_via': 'varchar(50)',
        'confidence_score': 'float',
        'confidence_reasoning': 'jsonb',
        'auto_send_recommended': 'boolean',
        'auto_sent': 'boolean',
        'auto_sent_at': 'timestamp'
    }
    
    # Expected indexes
    customer_emails_indexes = [
        'customer_emails_pkey',
        'idx_customer_emails_sender',
        'idx_customer_emails_created_at',
        'idx_customer_emails_classification'
    ]
    
    customer_email_replies_indexes = [
        'customer_email_replies_pkey',
        'idx_customer_email_replies_email_id',
        'idx_customer_email_replies_is_draft',
        'idx_customer_email_replies_confidence',
        'idx_customer_email_replies_auto_send'
    ]
    
    # Check tables
    emails_ok = check_table_columns('customer_emails', customer_emails_columns)
    replies_ok = check_table_columns('customer_email_replies', customer_email_replies_columns)
    
    # Check indexes
    emails_indexes_ok = check_indexes('customer_emails', customer_emails_indexes)
    replies_indexes_ok = check_indexes('customer_email_replies', customer_email_replies_indexes)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    
    if emails_ok and replies_ok and emails_indexes_ok and replies_indexes_ok:
        print("🎉 All schema requirements are met!")
        print("✅ Your database is ready for OpenAI integration")
    else:
        print("⚠️  Some schema requirements are missing")
        print("\n🔧 To fix, run the migration script:")
        print("   backend/migrations/20250716_safe_openai_update.sql")
        print("\n📋 This will safely add missing columns without affecting existing data")
    
    print("=" * 60)

if __name__ == '__main__':
    main() 