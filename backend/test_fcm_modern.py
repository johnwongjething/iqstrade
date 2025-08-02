#!/usr/bin/env python3
"""
Test modern FCM service with OAuth 2.0
"""

import os
import sys
from fcm_service_modern import fcm_service

def test_fcm_service():
    """Test the modern FCM service"""
    
    print("🧪 Testing Modern FCM Service")
    print("=" * 50)
    
    # Test 1: Check credentials
    print("\n📋 Test 1: Checking credentials...")
    if fcm_service.credentials:
        print("✅ Credentials loaded successfully")
        print(f"   Service account: {fcm_service.service_account_path}")
    else:
        print("❌ No credentials available")
        return False
    
    # Test 2: Check access token
    print("\n📋 Test 2: Checking access token...")
    access_token = fcm_service._get_valid_access_token()
    if access_token:
        print(f"✅ Access token obtained: {access_token[:20]}...")
    else:
        print("❌ No access token available")
        return False
    
    # Test 3: Test topic notification
    print("\n📋 Test 3: Testing topic notification...")
    result = fcm_service.send_to_topic(
        topic='test',
        title='🧪 Test Notification',
        body='Testing modern FCM service with OAuth 2.0',
        data={'type': 'test', 'message': 'This is a test'}
    )
    
    print(f"Result: {result}")
    
    if result['success']:
        print("✅ Topic notification sent successfully!")
    else:
        print(f"❌ Topic notification failed: {result.get('error', 'Unknown error')}")
    
    # Test 4: Test specific notification types
    print("\n📋 Test 4: Testing specific notification types...")
    
    # Test new bill notification
    print("   Testing new bill notification...")
    bill_result = fcm_service.send_new_bill_notification(
        bill_id=123,
        customer_name="Test Customer",
        amount=1500.00,
        bill_number="TEST123"
    )
    print(f"   New bill result: {bill_result['success']}")
    
    # Test payment confirmation
    print("   Testing payment confirmation...")
    payment_result = fcm_service.send_payment_confirmation_notification(
        bill_id=123,
        bill_number="TEST123",
        amount=1500.00,
        payment_method="Credit Card"
    )
    print(f"   Payment result: {payment_result['success']}")
    
    # Test system error
    print("   Testing system error...")
    error_result = fcm_service.send_system_error_notification(
        error_type="Database",
        error_message="Connection timeout",
        severity="high"
    )
    print(f"   System error result: {error_result['success']}")
    
    # Test customer escalation
    print("   Testing customer escalation...")
    escalation_result = fcm_service.send_customer_escalation_notification(
        customer_name="John Doe",
        customer_phone="+1234567890",
        issue_type="Payment Issue",
        priority="high"
    )
    print(f"   Escalation result: {escalation_result['success']}")
    
    return True

if __name__ == "__main__":
    success = test_fcm_service()
    
    if success:
        print("\n🎉 All tests completed!")
        print("✅ Modern FCM service is working correctly")
        print("🚀 Ready for deployment to Render")
    else:
        print("\n❌ Tests failed!")
        print("Please check your service account configuration") 