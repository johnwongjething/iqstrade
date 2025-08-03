#!/usr/bin/env python3
"""
Test script to verify FCM backend functionality
"""

import requests
import json
import os

# Configuration
BASE_URL = "https://iqstrade.onrender.com"  # Production URL
# BASE_URL = "http://localhost:5000"  # Local URL

def test_fcm_service():
    """Test FCM service status"""
    print("🔍 Testing FCM service status...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/fcm/test-service")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ FCM service is working!")
            print(f"   Project ID: {data.get('project_id')}")
            print(f"   API URL: {data.get('api_url')}")
            return True
        else:
            print("❌ FCM service test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing FCM service: {e}")
        return False

def test_fcm_token_save():
    """Test FCM token saving (public endpoint)"""
    print("\n🔍 Testing FCM token save (public endpoint)...")
    
    # Mock FCM token
    test_token = "test_token_" + "x" * 100
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/fcm/token/public",
            json={"token": test_token},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ FCM token save test passed!")
            return True
        else:
            print("❌ FCM token save test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing FCM token save: {e}")
        return False

def test_fcm_notification():
    """Test FCM notification sending"""
    print("\n🔍 Testing FCM notification sending...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/fcm/test/public",
            json={
                "title": "Test Notification",
                "body": "This is a test notification from backend",
                "token": "test_token_" + "x" * 100
            },
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ FCM notification test passed!")
            return True
        else:
            print("❌ FCM notification test failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing FCM notification: {e}")
        return False

def main():
    print("🚀 FCM Backend Test Suite")
    print("=" * 50)
    
    # Test 1: FCM Service Status
    service_ok = test_fcm_service()
    
    # Test 2: Token Save
    token_ok = test_fcm_token_save()
    
    # Test 3: Notification Sending
    notification_ok = test_fcm_notification()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   FCM Service: {'✅ PASS' if service_ok else '❌ FAIL'}")
    print(f"   Token Save: {'✅ PASS' if token_ok else '❌ FAIL'}")
    print(f"   Notification: {'✅ PASS' if notification_ok else '❌ FAIL'}")
    
    if all([service_ok, token_ok, notification_ok]):
        print("\n🎉 All tests passed! FCM backend is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    main() 