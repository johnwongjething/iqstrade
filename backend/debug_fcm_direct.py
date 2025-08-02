#!/usr/bin/env python3
"""
Debug FCM direct notification
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def debug_fcm_direct():
    """Debug FCM direct notification with detailed logging"""
    
    print("🔍 Debugging FCM Direct Notification")
    print("=" * 50)
    
    # Test with a real FCM token (you can replace this)
    test_token = "fTp9k8GIumfk5o827m3Jnz:APA91bEA_0LrD5S0ZmdBcnRgwPORLd9uT6nLpfs_HcvHK-qs8GXT5baE_w5DApYOzDQCIsNAKW0A4XHIL24yCHEM70A3hzsD9PC62tZKaCkxVdXnwx1qSYU"
    
    print(f"📱 Using test token: {test_token[:50]}...")
    
    # Test the direct notification endpoint
    notification_data = {
        "token": test_token,
        "title": "Debug Test Notification",
        "body": "This is a debug test notification"
    }
    
    try:
        print("📡 Making request to /api/fcm/send/direct...")
        response = requests.post(
            'http://localhost:5000/api/fcm/send/direct',
            json=notification_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        print(f"📡 Response Status: {response.status_code}")
        print(f"📡 Response Headers: {dict(response.headers)}")
        print(f"📡 Response Text: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Direct notification endpoint responded successfully")
            print(f"📱 Backend message: {result.get('message', 'No message')}")
            
            # Check the FCM result
            fcm_result = result.get('result', {})
            print(f"📱 FCM Success: {fcm_result.get('success', 'Unknown')}")
            print(f"📱 FCM Response: {fcm_result.get('response', 'No response')}")
            print(f"📱 FCM Error: {fcm_result.get('error', 'No error')}")
            
            if fcm_result.get('success'):
                print("✅ FCM service reports success")
            else:
                print("❌ FCM service reports failure")
                print(f"📱 Error details: {fcm_result.get('error', 'No error details')}")
                
        else:
            print("❌ Direct notification endpoint failed")
            print(f"📱 Error: {response.status_code} - {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out")
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - is the backend running?")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == '__main__':
    debug_fcm_direct() 