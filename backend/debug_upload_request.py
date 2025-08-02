#!/usr/bin/env python3
"""
Debug script to test upload request and identify 400 error causes
"""

import requests
import json
import os

def test_upload_request():
    """Test the upload endpoint to identify issues"""
    
    # Test URL (adjust if needed)
    url = "http://localhost:5000/api/upload"
    
    # Test data - minimal required fields
    test_data = {
        'name': 'Test Customer',
        'email': 'test@example.com',
        'phone': '1234567890'
    }
    
    # Test files
    test_files = {}
    
    # Check if test PDF exists
    test_pdf_path = "New folder (2)/BILL1.pdf"
    if os.path.exists(test_pdf_path):
        test_files['bill_pdf'] = open(test_pdf_path, 'rb')
        print(f"✅ Found test PDF: {test_pdf_path}")
    else:
        print(f"❌ Test PDF not found: {test_pdf_path}")
        return
    
    print("🔍 Testing upload request...")
    print(f"URL: {url}")
    print(f"Data: {test_data}")
    print(f"Files: {list(test_files.keys())}")
    
    try:
        # Make the request
        response = requests.post(url, data=test_data, files=test_files)
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        if response.status_code == 400:
            print(f"❌ 400 Error - Bad Request")
            try:
                error_data = response.json()
                print(f"❌ Error Details: {error_data}")
            except:
                print(f"❌ Error Text: {response.text}")
        elif response.status_code == 200:
            print(f"✅ Success!")
            try:
                result = response.json()
                print(f"✅ Response: {result}")
            except:
                print(f"✅ Response Text: {response.text}")
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Is the server running?")
    except Exception as e:
        print(f"❌ Request Error: {e}")
    finally:
        # Clean up
        for file in test_files.values():
            file.close()

def check_server_status():
    """Check if the server is running"""
    try:
        response = requests.get("http://localhost:5000/")
        print(f"✅ Server is running (Status: {response.status_code})")
        return True
    except:
        print("❌ Server is not running on localhost:5000")
        return False

if __name__ == "__main__":
    print("🔧 Debug Upload Request")
    print("=" * 50)
    
    # Check server status first
    if check_server_status():
        test_upload_request()
    else:
        print("\n💡 To start the server:")
        print("cd backend")
        print("python app.py") 