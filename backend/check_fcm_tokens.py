#!/usr/bin/env python3
"""
Check FCM tokens in database
"""

from config import get_db_conn

def check_fcm_tokens():
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Check if fcm_tokens table exists and has data
        cur.execute("SELECT COUNT(*) FROM fcm_tokens")
        count = cur.fetchone()[0]
        print(f"📊 Total FCM tokens in database: {count}")
        
        if count > 0:
            # Show active tokens
            cur.execute("SELECT id, user_id, token, created_at, is_active FROM fcm_tokens WHERE is_active = TRUE")
            active_tokens = cur.fetchall()
            print(f"✅ Active FCM tokens: {len(active_tokens)}")
            
            for token in active_tokens:
                token_id, user_id, token_value, created_at, is_active = token
                print(f"  Token ID: {token_id}")
                print(f"  User ID: {user_id}")
                print(f"  Token: {token_value[:20]}...")
                print(f"  Created: {created_at}")
                print(f"  Active: {is_active}")
                print()
        else:
            print("❌ No FCM tokens found in database")
            print("💡 You need to set up FCM on your devices first")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_fcm_tokens() 