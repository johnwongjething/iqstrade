#!/usr/bin/env python3
"""
Test FCM Endpoints
"""

import requests
import json

def test_fcm_endpoints():
    """Test the FCM endpoints directly"""
    
    print("🧪 Testing FCM Endpoints")
    print("=" * 50)
    
    # Test the subscription endpoint
    print("\n1️⃣ Testing FCM Subscription Endpoint")
    print("-" * 40)
    
    subscription_data = {
        "token": "test_token_for_testing",
        "topic": "test"
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/api/fcm/subscribe',
            json=subscription_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Subscription endpoint working")
        else:
            print("❌ Subscription endpoint failed")
            
    except Exception as e:
        print(f"❌ Error testing subscription: {e}")
    
    # Test the test notification endpoint
    print("\n2️⃣ Testing FCM Test Notification Endpoint")
    print("-" * 40)
    
    try:
        response = requests.post(
            'http://localhost:5000/api/fcm/test/public',
            json={},
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Test notification endpoint working")
        else:
            print("❌ Test notification endpoint failed")
            
    except Exception as e:
        print(f"❌ Error testing notification: {e}")
    
    # Test the token save endpoint
    print("\n3️⃣ Testing FCM Token Save Endpoint")
    print("-" * 40)
    
    token_data = {
        "token": "test_token_for_testing"
    }
    
    try:
        response = requests.post(
            'http://localhost:5000/api/fcm/token/public',
            json=token_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Token save endpoint working")
        else:
            print("❌ Token save endpoint failed")
            
    except Exception as e:
        print(f"❌ Error testing token save: {e}")

if __name__ == '__main__':
    test_fcm_endpoints() 