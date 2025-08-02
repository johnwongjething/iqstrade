#!/usr/bin/env python3
"""
Check users table schema
"""

from db_utils import get_db_conn

def check_users_schema():
    """Check the current users table schema"""
    conn = get_db_conn()
    cur = conn.cursor()
    
    print("🔍 Checking users table schema...")
    print("=" * 50)
    
    # Get table schema
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """)
    
    columns = cur.fetchall()
    
    print("📋 users table schema:")
    print("-" * 50)
    for col in columns:
        column_name, data_type, is_nullable, column_default = col
        nullable = "NULL" if is_nullable == "YES" else "NOT NULL"
        default = f"DEFAULT {column_default}" if column_default else ""
        print(f"  {column_name:<20} {data_type:<15} {nullable:<10} {default}")
    
    print()
    
    # Get sample user data
    cur.execute("SELECT * FROM users LIMIT 3")
    sample_users = cur.fetchall()
    
    if sample_users:
        print("👥 Sample user data:")
        print("-" * 50)
        for user in sample_users:
            print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Role: {user[4]}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_users_schema() 