#!/usr/bin/env python3
"""
Check user data for ray40
"""

from config import get_db_conn

def check_user_data():
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        cur.execute('SELECT username, customer_name, customer_email, customer_phone FROM users WHERE username = %s', ('ray40',))
        row = cur.fetchone()
        
        if row:
            username, customer_name, customer_email, customer_phone = row
            print(f"Username: {username}")
            print(f"Customer Name: {customer_name}")
            print(f"Customer Email: {customer_email}")
            print(f"Customer Phone: {customer_phone}")
            
            if customer_name is None or customer_name == '':
                print("❌ Customer name is empty!")
            else:
                print("✅ Customer name is set")
        else:
            print("❌ User ray40 not found in database")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_user_data() 