#!/usr/bin/env python3
"""
FCM Token Cleanup Script
Removes invalid/expired FCM tokens to prevent crashes
"""
import os
import sys
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env.local')

def get_db_conn():
    """Get database connection"""
    import psycopg2
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', '5432')
    )

def cleanup_fcm_tokens():
    """Clean up invalid FCM tokens"""
    print("🧹 Starting FCM token cleanup...")
    
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Get all FCM tokens
        cur.execute("SELECT id, token, created_at, updated_at FROM fcm_tokens WHERE is_active = TRUE")
        tokens = cur.fetchall()
        
        print(f"📱 Found {len(tokens)} active FCM tokens")
        
        invalid_tokens = []
        valid_tokens = []
        
        # Test each token with a simple FCM call
        for token_id, token, created_at, updated_at in tokens:
            print(f"🔍 Testing token {token_id}: {token[:20]}...")
            
            # Skip tokens older than 30 days (likely expired)
            if updated_at and (datetime.now() - updated_at).days > 30:
                print(f"   ⏰ Token {token_id} is older than 30 days, marking as invalid")
                invalid_tokens.append(token_id)
                continue
            
            # Test token validity by attempting to send a test message
            try:
                from fcm_service_fallback import fcm_service_fallback
                
                result = fcm_service_fallback.send_notification(
                    tokens=[token],
                    title="Token Test",
                    body="Testing token validity",
                    data={'type': 'token_test'}
                )
                
                if result.get('success') and result.get('success_count', 0) > 0:
                    print(f"   ✅ Token {token_id} is valid")
                    valid_tokens.append(token_id)
                else:
                    print(f"   ❌ Token {token_id} failed: {result.get('error', 'Unknown error')}")
                    invalid_tokens.append(token_id)
                    
            except Exception as e:
                print(f"   ❌ Token {token_id} error: {str(e)}")
                invalid_tokens.append(token_id)
        
        # Mark invalid tokens as inactive
        if invalid_tokens:
            print(f"🗑️ Marking {len(invalid_tokens)} invalid tokens as inactive...")
            cur.execute(
                "UPDATE fcm_tokens SET is_active = FALSE WHERE id = ANY(%s)",
                (invalid_tokens,)
            )
            conn.commit()
            print(f"✅ Marked {len(invalid_tokens)} tokens as inactive")
        else:
            print("✅ No invalid tokens found")
        
        print(f"📊 Summary:")
        print(f"   Valid tokens: {len(valid_tokens)}")
        print(f"   Invalid tokens: {len(invalid_tokens)}")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    cleanup_fcm_tokens() 