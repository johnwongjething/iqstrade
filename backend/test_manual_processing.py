#!/usr/bin/env python3
"""
Test script to verify manual email processing works correctly
"""

import requests
import json
import time

def test_manual_processing():
    """Test the manual email processing endpoint"""
    
    # Base URL for local development
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Manual Email Processing...")
    
    # Test 1: Check processor status
    print("\n1. Checking email processor status...")
    try:
        response = requests.get(f"{base_url}/admin/email/processor/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✅ Processor Status: {status}")
        else:
            print(f"❌ Failed to get status: {response.status_code}")
    except Exception as e:
        print(f"❌ Error getting status: {e}")
    
    # Test 2: Pause background processing
    print("\n2. Pausing background processing...")
    try:
        response = requests.post(f"{base_url}/admin/email/processor/pause")
        if response.status_code == 200:
            print("✅ Background processing paused")
        else:
            print(f"❌ Failed to pause: {response.status_code}")
    except Exception as e:
        print(f"❌ Error pausing: {e}")
    
    # Test 3: Test manual processing
    print("\n3. Testing manual email processing...")
    try:
        response = requests.post(f"{base_url}/admin/process_unprocessed_payment_emails")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Manual processing result: {result}")
        else:
            print(f"❌ Failed to process: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Error in manual processing: {e}")
    
    # Test 4: Resume background processing
    print("\n4. Resuming background processing...")
    try:
        response = requests.post(f"{base_url}/admin/email/processor/resume")
        if response.status_code == 200:
            print("✅ Background processing resumed")
        else:
            print(f"❌ Failed to resume: {response.status_code}")
    except Exception as e:
        print(f"❌ Error resuming: {e}")
    
    print("\n🎯 Manual processing test completed!")

if __name__ == "__main__":
    test_manual_processing() 