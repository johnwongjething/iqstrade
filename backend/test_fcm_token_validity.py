#!/usr/bin/env python3
"""
Test FCM token validity and message delivery
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_fcm_token():
    """Test if FCM token is valid and can receive messages"""
    
    print("🔍 Testing FCM Token Validity")
    print("=" * 50)
    
    # Your actual FCM token
    test_token = "fTp9k8GIumfk5o827m3Jnz:APA91bEA_0LrD5S0ZmdBcnRgwPORLd9uT6nLpfs_HcvHK-qs8GXT5baE_w5DApYOzDQCIsNAKW0A4XHIL24yCHEM70A3hzsD9PC62tZKaCkxVdXnwx1qSYU"
    
    print(f"📱 Testing token: {test_token[:50]}...")
    
    # Test different notification types
    test_cases = [
        {
            "name": "Simple Notification",
            "data": {
                "token": test_token,
                "title": "🔔 Simple Test",
                "body": "This is a simple test notification"
            }
        },
        {
            "name": "Data Notification",
            "data": {
                "token": test_token,
                "title": "📊 Data Test",
                "body": "This notification has custom data",
                "data": {
                    "type": "test",
                    "message": "Hello from backend!",
                    "timestamp": "2025-07-31T10:20:00Z"
                }
            }
        },
        {
            "name": "High Priority Notification",
            "data": {
                "token": test_token,
                "title": "🚨 High Priority Test",
                "body": "This is a high priority notification",
                "data": {
                    "type": "urgent",
                    "priority": "high"
                }
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            response = requests.post(
                'http://localhost:5000/api/fcm/send/direct',
                json=test_case['data'],
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            print(f"📡 Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                fcm_result = result.get('result', {})
                
                if fcm_result.get('success'):
                    print("✅ FCM reports success")
                    print(f"📱 Message ID: {fcm_result.get('results', [{}])[0].get('response', {}).get('name', 'Unknown')}")
                    print("📱 Check your device for the notification!")
                else:
                    print("❌ FCM reports failure")
                    print(f"📱 Error: {fcm_result.get('error', 'Unknown error')}")
            else:
                print(f"❌ HTTP Error: {response.status_code}")
                print(f"📱 Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")
        
        # Wait a bit between tests
        import time
        time.sleep(2)
    
    print("\n" + "=" * 50)
    print("🎯 Summary:")
    print("If you received notifications, your FCM setup is working!")
    print("If you didn't receive notifications, check:")
    print("1. Browser notification permissions")
    print("2. Service worker registration")
    print("3. FCM token validity")
    print("4. Network connectivity")

if __name__ == '__main__':
    test_fcm_token() 