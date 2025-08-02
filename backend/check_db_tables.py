#!/usr/bin/env python3
"""
Check what database tables exist
"""

from db_utils import get_db_conn

def check_tables():
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        tables = [row[0] for row in cur.fetchall()]
        print("Existing tables:", tables)
        
        # Check if specific tables exist
        important_tables = ['ctn_info', 'invoices', 'customer_emails', 'email_processing_locks']
        for table in important_tables:
            if table in tables:
                print(f"✅ {table} - EXISTS")
            else:
                print(f"❌ {table} - MISSING")
                
    except Exception as e:
        print(f"Error checking tables: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_tables() 