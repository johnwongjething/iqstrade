#!/usr/bin/env python3
"""
Test database connection and FCM tokens
"""
import sys
import os

# Add backend to path
sys.path.append('backend')

def test_db_connection():
    """Test database connection"""
    try:
        print("🗄️ Testing database connection...")
        
        # Import database connection
        from config import get_db_conn
        print("✅ Database config imported")
        
        # Test connection
        conn = get_db_conn()
        print("✅ Database connection established")
        
        cursor = conn.cursor()
        
        # Test FCM tokens table
        cursor.execute('SELECT COUNT(*) FROM fcm_tokens')
        count = cursor.fetchone()[0]
        print(f"📱 FCM tokens in database: {count}")
        
        # Get active tokens
        cursor.execute('SELECT token FROM fcm_tokens WHERE is_active = TRUE')
        tokens = [row[0] for row in cursor.fetchall()]
        print(f"📱 Active FCM tokens: {len(tokens)}")
        
        if tokens:
            print(f"📱 First token: {tokens[0][:20]}...")
        
        cursor.close()
        conn.close()
        print("✅ Database test completed")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_db_connection() 