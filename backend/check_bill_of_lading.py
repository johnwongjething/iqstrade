#!/usr/bin/env python3
"""
Check bill_of_lading table structure and data
"""

from db_utils import get_db_conn

def check_bill_of_lading():
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Check table structure
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'bill_of_lading'")
        columns = cur.fetchall()
        print("bill_of_lading table columns:")
        for col in columns:
            print(f"  {col[0]}: {col[1]}")
        
        # Check sample data
        cur.execute("SELECT * FROM bill_of_lading LIMIT 3")
        rows = cur.fetchall()
        print(f"\nSample data ({len(rows)} rows):")
        for i, row in enumerate(rows):
            print(f"  Row {i+1}: {row}")
            
        # Check if BL NYC2201666 exists
        cur.execute("SELECT * FROM bill_of_lading WHERE bl_number LIKE '%NYC2201666%'")
        bl_rows = cur.fetchall()
        print(f"\nBL NYC2201666 search results ({len(bl_rows)} rows):")
        for row in bl_rows:
            print(f"  {row}")
            
    except Exception as e:
        print(f"Error checking bill_of_lading: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_bill_of_lading() 