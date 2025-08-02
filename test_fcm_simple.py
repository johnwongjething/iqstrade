#!/usr/bin/env python3
"""
Simple FCM Test Script
Tests if FCM notifications are working properly
"""

import requests
import json
from datetime import datetime

def test_fcm_notification():
    """Test FCM notification via the public endpoint"""
    
    print("🧪 Testing FCM Notification...")
    
    # Test the public FCM endpoint
    url = "http://localhost:5000/api/fcm/test/public"
    
    try:
        response = requests.post(url, timeout=10)
        print(f"📡 Response Status: {response.status_code}")
        
        if response.ok:
            result = response.json()
            print("✅ FCM Test Response:")
            print(json.dumps(result, indent=2))
            
            if result.get('success'):
                print("🎉 FCM notification sent successfully!")
                print("📱 Check if you received the notification in your browser")
            else:
                print("❌ FCM notification failed")
                print(f"Error: {result.get('error', 'Unknown error')}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def test_email_notification():
    """Test email notification specifically"""
    
    print("\n📧 Testing Email Notification...")
    
    url = "http://localhost:5000/api/fcm/test/email-notification"
    
    try:
        response = requests.post(url, timeout=10)
        print(f"📡 Response Status: {response.status_code}")
        
        if response.ok:
            result = response.json()
            print("✅ Email Notification Test Response:")
            print(json.dumps(result, indent=2))
            
            tokens_count = result.get('tokens_count', 0)
            if tokens_count > 0:
                print(f"📱 Found {tokens_count} FCM tokens")
                print("📱 Check if you received the email notification")
            else:
                print("⚠️ No FCM tokens found in database")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def check_fcm_tokens():
    """Check what FCM tokens are in the database"""
    
    print("\n🔍 Checking FCM Tokens in Database...")
    
    # This would require authentication, but let's try a simple check
    url = "http://localhost:5000/api/fcm/test/public"
    
    try:
        response = requests.get(url, timeout=10)
        print(f"📡 FCM Service Status: {response.status_code}")
        
        if response.ok:
            print("✅ FCM service is responding")
        else:
            print("❌ FCM service not responding")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to FCM service: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("FCM Notification Test")
    print("=" * 50)
    
    # Check FCM service status
    check_fcm_tokens()
    
    # Test general FCM notification
    test_fcm_notification()
    
    # Test email-specific notification
    test_email_notification()
    
    print("\n" + "=" * 50)
    print("Test Complete!")
    print("=" * 50) 