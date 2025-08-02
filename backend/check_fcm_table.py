#!/usr/bin/env python3
"""
Check the structure of fcm_tokens table
"""

from config import get_db_conn

def check_fcm_table():
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Check table structure
        cur.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'fcm_tokens'
            ORDER BY ordinal_position;
        """)
        
        columns = cur.fetchall()
        print("📋 FCM Tokens Table Structure:")
        print("=" * 50)
        for col in columns:
            col_name, data_type, nullable, default = col
            print(f"Column: {col_name}")
            print(f"  Type: {data_type}")
            print(f"  Nullable: {nullable}")
            print(f"  Default: {default}")
            print()
        
        # Check if table has any data
        cur.execute("SELECT COUNT(*) FROM fcm_tokens")
        count = cur.fetchone()[0]
        print(f"📊 Total records in fcm_tokens: {count}")
        
        if count > 0:
            # Show sample data
            cur.execute("SELECT * FROM fcm_tokens LIMIT 3")
            rows = cur.fetchall()
            print("\n📄 Sample data:")
            for row in rows:
                print(f"  {row}")
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_fcm_table() 