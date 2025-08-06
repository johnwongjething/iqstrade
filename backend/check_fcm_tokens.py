#!/usr/bin/env python3
"""
FCM Token Status Checker
Check the age and status of FCM tokens in the database
"""
import os
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env.local')

def get_db_conn():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT', '5432')
    )

def check_fcm_tokens():
    """Check FCM token status and age"""
    print("🔍 Checking FCM token status...")
    
    conn = get_db_conn()
    cur = conn.cursor()
    
    try:
        # Get all FCM tokens with their age
        cur.execute("""
            SELECT 
                id, 
                token, 
                user_id,
                is_active,
                created_at, 
                updated_at,
                EXTRACT(EPOCH FROM (NOW() - updated_at))/86400 as days_old
            FROM fcm_tokens 
            ORDER BY updated_at DESC
        """)
        tokens = cur.fetchall()
        
        print(f"📱 Found {len(tokens)} total FCM tokens")
        
        active_tokens = []
        inactive_tokens = []
        old_tokens = []
        
        for token_id, token, user_id, is_active, created_at, updated_at, days_old in tokens:
            token_info = {
                'id': token_id,
                'token_preview': token[:20] + '...' if token else 'None',
                'user_id': user_id,
                'is_active': is_active,
                'created_at': created_at,
                'updated_at': updated_at,
                'days_old': days_old
            }
            
            if is_active:
                active_tokens.append(token_info)
                if days_old and days_old > 30:
                    old_tokens.append(token_info)
            else:
                inactive_tokens.append(token_info)
        
        print(f"\n📊 Token Summary:")
        print(f"   Active tokens: {len(active_tokens)}")
        print(f"   Inactive tokens: {len(inactive_tokens)}")
        print(f"   Old tokens (>30 days): {len(old_tokens)}")
        
        if active_tokens:
            print(f"\n✅ Active Tokens:")
            for token in active_tokens[:5]:  # Show first 5
                age_status = "🟢 Recent" if token['days_old'] < 7 else "🟡 Old" if token['days_old'] < 30 else "🔴 Very Old"
                print(f"   ID {token['id']}: {token['token_preview']} (User: {token['user_id']}, Age: {token['days_old']:.1f} days) {age_status}")
            
            if len(active_tokens) > 5:
                print(f"   ... and {len(active_tokens) - 5} more active tokens")
        
        if old_tokens:
            print(f"\n⚠️ Old Tokens (>30 days):")
            for token in old_tokens[:3]:  # Show first 3
                print(f"   ID {token['id']}: {token['token_preview']} (Age: {token['days_old']:.1f} days)")
        
        if inactive_tokens:
            print(f"\n❌ Inactive Tokens:")
            print(f"   {len(inactive_tokens)} inactive tokens found")
        
        # Check for potential issues
        print(f"\n🔍 Potential Issues:")
        if len(old_tokens) > 0:
            print(f"   ⚠️ {len(old_tokens)} tokens are older than 30 days (may be expired)")
        if len(active_tokens) == 0:
            print(f"   ❌ No active FCM tokens found")
        if len(active_tokens) > 0:
            print(f"   ✅ {len(active_tokens)} active tokens available for notifications")
        
    except Exception as e:
        print(f"❌ Error checking FCM tokens: {str(e)}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    check_fcm_tokens() 