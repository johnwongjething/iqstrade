#!/usr/bin/env python3
"""
Fix customer name for ray40 if it's empty
"""

from config import get_db_conn

def fix_customer_name():
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # First check current data
        cur.execute('SELECT username, customer_name, customer_email, customer_phone FROM users WHERE username = %s', ('ray40',))
        row = cur.fetchone()
        
        if row:
            username, customer_name, customer_email, customer_phone = row
            print(f"Current data:")
            print(f"Username: {username}")
            print(f"Customer Name: {customer_name}")
            print(f"Customer Email: {customer_email}")
            print(f"Customer Phone: {customer_phone}")
            
            # If customer_name is empty, set it to username
            if customer_name is None or customer_name == '':
                print("❌ Customer name is empty! Fixing...")
                cur.execute('UPDATE users SET customer_name = %s WHERE username = %s', ('ray40', 'ray40'))
                conn.commit()
                print("✅ Updated customer_name to 'ray40'")
                
                # Verify the update
                cur.execute('SELECT customer_name FROM users WHERE username = %s', ('ray40',))
                new_name = cur.fetchone()[0]
                print(f"✅ Verified: customer_name is now '{new_name}'")
            else:
                print("✅ Customer name is already set")
        else:
            print("❌ User ray40 not found in database")
            
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    fix_customer_name() 