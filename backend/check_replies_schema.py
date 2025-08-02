#!/usr/bin/env python3
"""
Check customer_email_replies table schema
"""
import os
import sys
from config import get_db_conn

def check_replies_schema():
    """Check the schema of customer_email_replies table"""
    
    try:
        db_conn = get_db_conn()
        cursor = db_conn.cursor()
        
        # Get table structure
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'customer_email_replies'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        
        print("📋 customer_email_replies table structure:")
        print("-" * 50)
        for col_name, data_type, nullable in columns:
            print(f"  {col_name}: {data_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
        
        # Check if table has any data
        cursor.execute("SELECT COUNT(*) FROM customer_email_replies")
        count = cursor.fetchone()[0]
        print(f"\n📊 Total replies: {count}")
        
        # Show sample data
        if count > 0:
            cursor.execute("SELECT * FROM customer_email_replies LIMIT 3")
            samples = cursor.fetchall()
            print(f"\n📝 Sample replies:")
            for i, sample in enumerate(samples, 1):
                print(f"  Reply {i}: {sample}")
        
        cursor.close()
        db_conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    check_replies_schema() 