#!/usr/bin/env python3
"""
Test script to check BL number search functionality
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_db_conn

def test_bl_search():
    """Test BL number search functionality"""
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        # Check if bl_numbers column exists
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'customer_emails' AND column_name = 'bl_numbers'
        """)
        result = cursor.fetchone()
        
        if result:
            print(f"✅ bl_numbers column exists: {result[1]}")
        else:
            print("❌ bl_numbers column does not exist")
            return
        
        # Check for emails with BL numbers
        cursor.execute("""
            SELECT id, sender, subject, bl_numbers 
            FROM customer_emails 
            WHERE bl_numbers IS NOT NULL AND array_length(bl_numbers, 1) > 0
            LIMIT 5
        """)
        
        emails_with_bl = cursor.fetchall()
        print(f"\n📧 Found {len(emails_with_bl)} emails with BL numbers:")
        
        for email in emails_with_bl:
            print(f"  ID: {email[0]}, Sender: {email[1]}")
            print(f"  Subject: {email[2]}")
            print(f"  BL Numbers: {email[3]}")
            print()
        
        # Test the search query
        if emails_with_bl:
            test_bl = emails_with_bl[0][3][0] if emails_with_bl[0][3] else "TEST123"
            print(f"🔍 Testing search for BL number: {test_bl}")
            
            # Test the exact query we're using
            query = """
                SELECT id, sender, subject, bl_numbers
                FROM customer_emails 
                WHERE (EXISTS(SELECT 1 FROM unnest(bl_numbers) AS bl WHERE bl ILIKE %s) 
                       OR subject ILIKE %s 
                       OR body ILIKE %s)
                LIMIT 5
            """
            
            cursor.execute(query, [f'%{test_bl}%', f'%{test_bl}%', f'%{test_bl}%'])
            results = cursor.fetchall()
            
            print(f"✅ Search found {len(results)} results:")
            for result in results:
                print(f"  ID: {result[0]}, Sender: {result[1]}")
                print(f"  Subject: {result[2]}")
                print(f"  BL Numbers: {result[3]}")
                print()
        
        # Check total email count
        cursor.execute("SELECT COUNT(*) FROM customer_emails")
        total_emails = cursor.fetchone()[0]
        print(f"📊 Total emails in database: {total_emails}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_bl_search() 