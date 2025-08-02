#!/usr/bin/env python3
import os
import sys
from config import get_db_conn

def main():
    print("SCHEMA CHECK")
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        
        # Get tables
        cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Tables: {len(tables)}")
        for table in tables:
            print(f"  {table}")
            
            # Get columns
            cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name=%s ORDER BY ordinal_position", (table,))
            cols = cursor.fetchall()
            for col in cols:
                print(f"    {col[0]}: {col[1]}")
            
            # Get count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"    Rows: {count}")
        
        cursor.close()
        conn.close()
        print("DONE")
        
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    main() 