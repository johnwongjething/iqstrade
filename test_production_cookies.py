#!/usr/bin/env python3
"""
Local test script to simulate production cookie behavior
This helps test the JWT cookie fixes before deploying to Render
"""

import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:5000"  # Your local Flask app
TEST_USERNAME = "ray40"
TEST_PASSWORD = "Raysan11!!"

def test_cookie_behavior():
    """Test the complete login flow with cookie handling"""
    
    session = requests.Session()
    
    print("🔍 Testing Production Cookie Behavior Locally")
    print("=" * 50)
    
    # Step 1: Clear cookies first
    print("\n1️⃣ Clearing existing cookies...")
    try:
        clear_response = session.post(f"{BASE_URL}/api/clear-cookies")
        print(f"   Clear cookies response: {clear_response.status_code}")
        print(f"   Cookies after clearing: {dict(session.cookies)}")
    except Exception as e:
        print(f"   Error clearing cookies: {e}")
    
    # Step 2: Get Geetest registration
    print("\n2️⃣ Getting Geetest registration...")
    try:
        geetest_response = session.get(f"{BASE_URL}/api/geetest/register")
        geetest_data = geetest_response.json()
        print(f"   Geetest response: {geetest_data}")
    except Exception as e:
        print(f"   Error getting Geetest: {e}")
        return
    
    # Step 3: Simulate login with mock Geetest data
    print("\n3️⃣ Attempting login...")
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD,
        "captcha_id": geetest_data.get("gt"),
        "lot_number": "test_lot_number",
        "pass_token": "test_pass_token", 
        "captcha_output": "test_captcha_output"
    }
    
    try:
        login_response = session.post(f"{BASE_URL}/api/login", json=login_data)
        print(f"   Login response status: {login_response.status_code}")
        print(f"   Login response: {login_response.json()}")
        print(f"   Cookies after login: {dict(session.cookies)}")
        
        if login_response.status_code == 200:
            print("   ✅ Login successful!")
        else:
            print("   ❌ Login failed!")
            return
            
    except Exception as e:
        print(f"   Error during login: {e}")
        return
    
    # Step 4: Test /api/me endpoint
    print("\n4️⃣ Testing /api/me endpoint...")
    try:
        me_response = session.get(f"{BASE_URL}/api/me")
        print(f"   /api/me status: {me_response.status_code}")
        
        if me_response.status_code == 200:
            me_data = me_response.json()
            print(f"   ✅ /api/me successful: {me_data}")
        else:
            print(f"   ❌ /api/me failed: {me_response.text}")
            
    except Exception as e:
        print(f"   Error testing /api/me: {e}")
    
    # Step 5: Test FCM token saving
    print("\n5️⃣ Testing FCM token saving...")
    try:
        fcm_data = {"token": "test_fcm_token_12345"}
        fcm_response = session.post(f"{BASE_URL}/api/fcm/token", json=fcm_data)
        print(f"   FCM token save status: {fcm_response.status_code}")
        
        if fcm_response.status_code == 200:
            print("   ✅ FCM token saved successfully!")
        else:
            print(f"   ❌ FCM token save failed: {fcm_response.text}")
            
    except Exception as e:
        print(f"   Error testing FCM: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_cookie_behavior() 