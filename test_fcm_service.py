#!/usr/bin/env python3
"""
Test script to directly test FCM service
"""
import sys
import os

# Add backend to path
sys.path.append('backend')

def test_fcm_service():
    """Test FCM service directly"""
    try:
        print("🧪 Testing FCM service directly...")
        
        # Import FCM service
        from fcm_service_modern import fcm_service
        print("✅ FCM service imported successfully")
        
        # Test getting tokens from database
        from config import get_db_conn
        conn = get_db_conn()
        cursor = conn.cursor()
        
        cursor.execute('SELECT token FROM fcm_tokens WHERE is_active = TRUE')
        tokens = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        print(f"📱 Found {len(tokens)} FCM tokens")
        
        if tokens:
            # Test sending a simple notification
            print("📤 Sending test notification...")
            result = fcm_service.send_notification(
                tokens=tokens,
                title='🧪 Test Notification',
                body='This is a direct FCM test',
                data={'type': 'test', 'timestamp': '2024-01-01T00:00:00'}
            )
            
            print(f"📱 FCM Result: {result}")
            
            if result.get('success'):
                print("✅ FCM notification sent successfully!")
            else:
                print(f"❌ FCM notification failed: {result}")
        else:
            print("ℹ️ No FCM tokens found")
            
    except Exception as e:
        print(f"❌ Error testing FCM service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fcm_service() 