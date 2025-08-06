#!/usr/bin/env python3
"""
Geetest Integration Test Script
Test the Geetest API integration to identify issues
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_geetest_configuration():
    """Test Geetest configuration"""
    print("🔍 Testing Geetest Configuration...")
    
    geetest_id = os.getenv('GEETEST_ID')
    geetest_key = os.getenv('GEETEST_KEY')
    
    print(f"📋 GEETEST_ID: {geetest_id}")
    print(f"🔑 GEETEST_KEY: {'*' * len(geetest_key) if geetest_key else 'None'}")
    
    if not geetest_id:
        print("❌ GEETEST_ID not configured")
        return False
    
    if not geetest_key:
        print("❌ GEETEST_KEY not configured")
        return False
    
    print("✅ Geetest configuration looks good")
    return True

def test_geetest_registration_api():
    """Test Geetest registration API directly"""
    print("\n🔍 Testing Geetest Registration API...")
    
    geetest_id = os.getenv('GEETEST_ID')
    
    try:
        url = "https://gcaptcha4.geetest.com/register"
        params = {
            "captcha_id": geetest_id,
            "client_type": "web",
            "lang": "en"
        }
        
        print(f"📡 Calling: {url}")
        print(f"📋 Params: {params}")
        
        response = requests.get(url, params=params, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ API Response: {json.dumps(data, indent=2)}")
                
                if data.get("success") == 1:
                    print("✅ Registration successful")
                    return True
                else:
                    print(f"❌ Registration failed: {data}")
                    return False
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response: {e}")
                print(f"📄 Raw response: {response.text}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - possible network/firewall issue")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_geetest_validation_api():
    """Test Geetest validation API with mock data"""
    print("\n🔍 Testing Geetest Validation API...")
    
    geetest_id = os.getenv('GEETEST_ID')
    
    # Mock validation data (this won't work, but we can test the API endpoint)
    mock_payload = {
        "lot_number": "mock_lot_number",
        "captcha_output": "mock_captcha_output", 
        "pass_token": "mock_pass_token",
        "captcha_id": geetest_id
    }
    
    try:
        url = "https://gcaptcha4.geetest.com/validate"
        
        print(f"📡 Calling: {url}")
        print(f"📋 Payload: {mock_payload}")
        
        response = requests.post(url, json=mock_payload, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ API Response: {json.dumps(data, indent=2)}")
                print("✅ Validation API endpoint is accessible")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response: {e}")
                print(f"📄 Raw response: {response.text}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - possible network/firewall issue")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_backend_geetest_endpoint():
    """Test your backend Geetest endpoint"""
    print("\n🔍 Testing Backend Geetest Endpoint...")
    
    try:
        # Assuming your backend is running locally
        url = "http://localhost:5000/api/geetest/register"
        
        print(f"📡 Calling: {url}")
        
        response = requests.get(url, timeout=10)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Backend Response: {json.dumps(data, indent=2)}")
                return True
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON response: {e}")
                print(f"📄 Raw response: {response.text}")
                return False
        else:
            print(f"❌ HTTP error: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend - make sure it's running")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    print("=" * 60)
    print("Geetest Integration Test")
    print("=" * 60)
    
    # Test 1: Configuration
    config_ok = test_geetest_configuration()
    
    if config_ok:
        # Test 2: Direct API calls
        registration_ok = test_geetest_registration_api()
        validation_ok = test_geetest_validation_api()
        
        # Test 3: Backend endpoint
        backend_ok = test_backend_geetest_endpoint()
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Configuration: {'✅' if config_ok else '❌'}")
        print(f"Registration API: {'✅' if registration_ok else '❌'}")
        print(f"Validation API: {'✅' if validation_ok else '❌'}")
        print(f"Backend Endpoint: {'✅' if backend_ok else '❌'}")
        
        if not registration_ok:
            print("\n💡 If registration API fails, check:")
            print("   - Network connectivity")
            print("   - Firewall settings")
            print("   - Geetest account status")
            print("   - Captcha ID validity")
        
        if not validation_ok:
            print("\n💡 If validation API fails, check:")
            print("   - Same issues as registration")
            print("   - API endpoint accessibility")
        
        if not backend_ok:
            print("\n💡 If backend endpoint fails, check:")
            print("   - Backend server is running")
            print("   - Environment variables are set")
            print("   - Route is properly configured")
    else:
        print("\n❌ Fix configuration issues first")

if __name__ == "__main__":
    main() 