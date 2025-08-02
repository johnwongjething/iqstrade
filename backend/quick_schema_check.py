#!/usr/bin/env python3
"""
Quick Database Schema Check
Fast schema analysis that won't hang in PowerShell
"""

import os
import sys
from config import get_db_conn

def quick_schema_check():
    """Quick schema check without hanging"""
    
    print("🗄️ QUICK SCHEMA CHECK")
    print("=" * 40)
    
    try:
        db_conn = get_db_conn()
        cursor = db_conn.cursor()
        
        # Get all tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📊 Tables ({len(tables)}):")
        for table in tables:
            print(f"   - {table}")
        
        print(f"\n📋 Detailed Table Info:")
        for table in tables:
            print(f"\n📋 {table.upper()}:")
            
            # Get columns
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table,))
            
            columns = cursor.fetchall()
            for col_name, data_type, nullable in columns:
                nullable_str = "NULL" if nullable == "YES" else "NOT NULL"
                print(f"   {col_name:<20} {data_type:<15} {nullable_str}")
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            print(f"   Rows: {row_count:,}")
        
        cursor.close()
        db_conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_schema_check()
    print("\n✅ Done!") 