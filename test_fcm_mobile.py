#!/usr/bin/env python3
"""
Comprehensive FCM Mobile Setup Test Script
Tests all aspects of FCM setup for mobile devices
"""

import requests
import json
import time

# Configuration
BASE_URL = "https://iqstrade.onrender.com"  # Change to localhost:5000 for local testing
TEST_TOKEN = "test_token_12345"  # This will be replaced with real token

def test_fcm_service_status():
    """Test if FCM service is working"""
    print("🔍 Testing FCM service status...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/fcm/test-service")
        print(f"Status: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print("✅ FCM Service Status:")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            print(f"   Credentials Available: {data.get('credentials_available')}")
            print(f"   Access Token Available: {data.get('access_token_available')}")
            print(f"   Project ID: {data.get('project_id')}")
            return True
        else:
            print(f"❌ FCM Service Test Failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing FCM service: {e}")
        return False

def test_simple_endpoint():
    """Test basic FCM endpoint"""
    print("\n🔍 Testing simple FCM endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/api/fcm/test-simple")
        print(f"Status: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print(f"✅ Simple test: {data.get('message')}")
            return True
        else:
            print(f"❌ Simple test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error in simple test: {e}")
        return False

def test_token_save():
    """Test saving FCM token"""
    print("\n🔍 Testing FCM token save...")
    
    try:
        # First, we need to get a valid JWT token by logging in
        login_data = {
            "username": "admin",  # Replace with actual test credentials
            "password": "admin123"
        }
        
        login_response = requests.post(f"{BASE_URL}/api/login", json=login_data)
        print(f"Login status: {login_response.status_code}")
        
        if not login_response.ok:
            print("❌ Login failed - cannot test token save")
            return False
        
        # Get cookies from login response
        cookies = login_response.cookies
        
        # Test token save
        token_data = {
            "token": TEST_TOKEN
        }
        
        response = requests.post(
            f"{BASE_URL}/api/fcm/token", 
            json=token_data,
            cookies=cookies
        )
        
        print(f"Token save status: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print(f"✅ Token save: {data.get('message')}")
            return True
        else:
            print(f"❌ Token save failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in token save test: {e}")
        return False

def test_direct_notification():
    """Test sending direct notification"""
    print("\n🔍 Testing direct notification...")
    
    try:
        notification_data = {
            "token": TEST_TOKEN,
            "title": "🔔 Mobile Test",
            "body": "This is a test notification for mobile debugging"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/fcm/send/direct",
            json=notification_data
        )
        
        print(f"Direct notification status: {response.status_code}")
        
        if response.ok:
            data = response.json()
            print(f"✅ Direct notification: {data.get('message')}")
            if 'result' in data:
                result = data['result']
                print(f"   Success: {result.get('success')}")
                print(f"   API Used: {result.get('api_used')}")
                print(f"   Success Count: {result.get('success_count')}")
                print(f"   Failure Count: {result.get('failure_count')}")
            return True
        else:
            print(f"❌ Direct notification failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in direct notification test: {e}")
        return False

def main():
    """Run all FCM tests"""
    print("🚀 Starting Comprehensive FCM Mobile Setup Test")
    print("=" * 50)
    
    tests = [
        ("Simple Endpoint", test_simple_endpoint),
        ("FCM Service Status", test_fcm_service_status),
        ("Token Save", test_token_save),
        ("Direct Notification", test_direct_notification),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! FCM should work on mobile.")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if Firebase service account is properly configured")
        print("2. Verify FIREBASE_SERVICE_ACCOUNT_PATH environment variable")
        print("3. Check Google Cloud Console for proper permissions")
        print("4. Ensure the service account file is not corrupted")

if __name__ == "__main__":
    main() 