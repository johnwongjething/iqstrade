#!/usr/bin/env python3
"""
Test sending notifications directly to FCM tokens
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_direct_notification():
    """Test sending notification directly to a token"""
    
    print("🧪 Testing Direct FCM Notification")
    print("=" * 50)
    
    # Test token (you can replace this with a real token)
    test_token = "test_token_for_testing"
    
    # Send notification directly to token
    notification_data = {
        "token": test_token,
        "title": "Direct Test Notification",
        "body": "This is a direct notification test"
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/api/fcm/send/direct',
            json=notification_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Direct notification endpoint working")
        else:
            print("❌ Direct notification endpoint failed")
            
    except Exception as e:
        print(f"❌ Error testing direct notification: {e}")

if __name__ == '__main__':
    test_direct_notification() 