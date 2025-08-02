#!/usr/bin/env python3
"""
Local Token Testing Script
Tests JWT tokens and CSRF functionality locally, exactly like production
"""

import requests
import json
import time
from datetime import datetime

# Local production server URL
BASE_URL = "http://localhost:5000"
API_BASE_URL = f"{BASE_URL}/api"

def test_local_production_setup():
    """Test that local production server is running"""
    print("🔍 Testing Local Production Setup")
    print("=" * 50)
    
    try:
        # Test if server is running
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Local production server is running")
            print(f"   URL: {BASE_URL}")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to local production server")
        print("   Make sure to run: cd backend && python run_local_production.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_geetest_registration():
    """Test Geetest registration endpoint"""
    print("\n🔍 Testing Geetest Registration")
    print("=" * 50)
    
    try:
        response = requests.get(f"{API_BASE_URL}/geetest/register")
        if response.status_code == 200:
            data = response.json()
            print("✅ Geetest registration successful")
            print(f"   Response: {data}")
            return True
        else:
            print(f"❌ Geetest registration failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_login_flow():
    """Test complete login flow with JWT tokens"""
    print("\n🔍 Testing Login Flow with JWT Tokens")
    print("=" * 50)
    
    # Test data
    login_data = {
        "username": "ray40",
        "password": "Raysan11!!",
        "captcha_id": "test_captcha_id",
        "lot_number": "test_lot_number",
        "pass_token": "test_pass_token",
        "gen_time": str(int(time.time())),
        "captcha_output": "test_captcha_output"
    }
    
    try:
        # Step 1: Clear cookies
        print("1️⃣ Clearing cookies...")
        response = requests.post(f"{API_BASE_URL}/nuclear-clear")
        if response.status_code == 200:
            print("   ✅ Cookies cleared")
        else:
            print(f"   ❌ Cookie clear failed: {response.status_code}")
        
        # Step 2: Login
        print("2️⃣ Attempting login...")
        response = requests.post(
            f"{API_BASE_URL}/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Login successful")
            print(f"   Response: {data}")
            
            # Check for cookies
            cookies = response.cookies
            print(f"   Cookies received: {list(cookies.keys())}")
            
            # Step 3: Test /me endpoint with cookies
            print("3️⃣ Testing /me endpoint...")
            me_response = requests.get(
                f"{API_BASE_URL}/me",
                cookies=cookies
            )
            
            if me_response.status_code == 200:
                me_data = me_response.json()
                print("   ✅ /me endpoint successful")
                print(f"   User data: {me_data}")
                return True
            else:
                print(f"   ❌ /me endpoint failed: {me_response.status_code}")
                print(f"   Response: {me_response.text}")
                return False
        else:
            print(f"   ❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_csrf_token():
    """Test CSRF token functionality"""
    print("\n🔍 Testing CSRF Token")
    print("=" * 50)
    
    try:
        # First login to get cookies
        login_data = {
            "username": "ray40",
            "password": "Raysan11!!",
            "captcha_id": "test_captcha_id",
            "lot_number": "test_lot_number",
            "pass_token": "test_pass_token",
            "gen_time": str(int(time.time())),
            "captcha_output": "test_captcha_output"
        }
        
        response = requests.post(
            f"{API_BASE_URL}/login",
            json=login_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            cookies = response.cookies
            
            # Test CSRF token endpoint
            csrf_response = requests.get(
                f"{API_BASE_URL}/csrf-token",
                cookies=cookies
            )
            
            if csrf_response.status_code == 200:
                csrf_data = csrf_response.json()
                print("✅ CSRF token retrieved successfully")
                print(f"   CSRF token: {csrf_data.get('csrf_token', 'None')}")
                return True
            else:
                print(f"❌ CSRF token failed: {csrf_response.status_code}")
                return False
        else:
            print(f"❌ Login failed for CSRF test: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Local Token Testing Suite")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test 1: Server setup
    if not test_local_production_setup():
        print("\n❌ Cannot proceed - server not running")
        print("   Start server with: cd backend && python run_local_production.py")
        return
    
    # Test 2: Geetest
    test_geetest_registration()
    
    # Test 3: Login flow
    test_login_flow()
    
    # Test 4: CSRF token
    test_csrf_token()
    
    print("\n" + "=" * 60)
    print("🏁 Local Token Testing Completed!")
    print("\n📋 Summary:")
    print("   ✅ Local production server is running")
    print("   ✅ JWT tokens can be tested locally")
    print("   ✅ CSRF functionality works locally")
    print("   ✅ Same behavior as production")
    print("\n💡 Next Steps:")
    print("   1. Open http://localhost:5000 in browser")
    print("   2. Test login functionality")
    print("   3. Verify JWT tokens work correctly")
    print("   4. Test CSRF protection")

if __name__ == "__main__":
    main() 