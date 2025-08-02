#!/usr/bin/env python3
"""
Test script to verify FCM email notification fixes
"""
import requests
import json
import time

def test_fcm_endpoints():
    """Test FCM endpoints to verify fixes"""
    base_url = "http://localhost:5000/api"
    
    print("🧪 Testing FCM endpoints...")
    
    # Test 1: Simple FCM test
    try:
        response = requests.get(f"{base_url}/fcm/test-simple", timeout=10)
        print(f"✅ Simple test: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Simple test failed: {e}")
    
    # Test 2: Test email notification
    try:
        response = requests.post(f"{base_url}/fcm/test/email-notification", timeout=10)
        print(f"✅ Test email notification: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Test email notification failed: {e}")
    
    # Test 3: Check email status (this might take longer)
    try:
        print("📧 Testing email processing (this may take a while)...")
        response = requests.get(f"{base_url}/fcm/check-email-status", timeout=30)
        print(f"✅ Email status check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Email status check failed: {e}")

if __name__ == "__main__":
    test_fcm_endpoints() 