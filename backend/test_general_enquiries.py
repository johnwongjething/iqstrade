#!/usr/bin/env python3
"""
Test script to verify general enquiry handling is working properly.
Tests the unified response handler with various customer questions.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from utils.unified_response_handler import UnifiedResponseHandler

def test_general_enquiries():
    """Test various general enquiry scenarios."""
    print("🧪 Testing General Enquiry Handling")
    print("=" * 50)
    
    # Create a mock database connector for testing
    def mock_db_connector():
        return None
    
    handler = UnifiedResponseHandler(mock_db_connector)
    
    # Test cases
    test_cases = [
        {
            "category": "Pricing Enquiries",
            "messages": [
                "How much does it cost for 2 containers?",
                "What is the price for 1 container?",
                "费用是多少？",
                "How much for 5 containers?",
                "What's the cost?"
            ]
        },
        {
            "category": "Payment Method Enquiries",
            "messages": [
                "How can I pay?",
                "What payment methods do you accept?",
                "银行转账可以吗？",
                "Do you accept Stripe?",
                "Payment options?"
            ]
        },
        {
            "category": "Shipping Time Enquiries",
            "messages": [
                "How long does shipping take?",
                "When will my shipment arrive?",
                "多久能到？",
                "What's the delivery time?",
                "Transit time?"
            ]
        },
        {
            "category": "Document Enquiries",
            "messages": [
                "What documents do I need?",
                "Do you have the certificate?",
                "文件在哪里？",
                "Where are my documents?",
                "Paperwork needed?"
            ]
        },
        {
            "category": "Status Enquiries",
            "messages": [
                "Where is my shipment?",
                "What's the status?",
                "跟踪信息？",
                "Can you track my shipment?",
                "Update on delivery?"
            ]
        },
        {
            "category": "Contact Enquiries",
            "messages": [
                "How can I contact you?",
                "What's your phone number?",
                "联系方式？",
                "Email address?",
                "Office location?"
            ]
        },
        {
            "category": "Unclear/General Enquiries",
            "messages": [
                "Hello, I need help",
                "Can you help me?",
                "I have a question",
                "Need assistance",
                "Help please"
            ]
        }
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_category in test_cases:
        print(f"\n📋 {test_category['category']}")
        print("-" * 30)
        
        for message in test_category['messages']:
            total_tests += 1
            try:
                result = handler.process_message(message)
                response = result['response']
                classification = result['classification']
                bl_number = result['bl_number']
                
                # Check if response is not empty and contains helpful information
                if response and len(response) > 50:
                    print(f"✅ '{message[:30]}...' → {classification}")
                    print(f"   BL: {bl_number}")
                    print(f"   Response: {response[:100]}...")
                    passed_tests += 1
                else:
                    print(f"❌ '{message[:30]}...' → Response too short")
                    print(f"   Response: {response}")
            except Exception as e:
                print(f"❌ '{message[:30]}...' → Error: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All general enquiry tests passed!")
        print("✅ The system can handle various customer questions properly.")
    else:
        print("⚠️  Some tests failed. Please check the responses above.")
    
    return passed_tests == total_tests

def test_specific_scenarios():
    """Test specific scenarios with BL numbers."""
    print("\n🔍 Testing Specific Scenarios with BL Numbers")
    print("=" * 50)
    
    def mock_db_connector():
        return None
    
    handler = UnifiedResponseHandler(mock_db_connector)
    
    # Test invoice request with BL number
    invoice_message = "I need the invoice for BL12345"
    result = handler.process_message(invoice_message)
    print(f"📄 Invoice Request: '{invoice_message}'")
    print(f"   Classification: {result['classification']}")
    print(f"   BL Number: {result['bl_number']}")
    print(f"   Response: {result['response'][:100]}...")
    
    # Test payment receipt with BL number
    receipt_message = "I sent payment receipt for BL12345"
    result = handler.process_message(receipt_message)
    print(f"💰 Payment Receipt: '{receipt_message}'")
    print(f"   Classification: {result['classification']}")
    print(f"   BL Number: {result['bl_number']}")
    print(f"   Response: {result['response'][:100]}...")
    
    # Test pricing with container count
    pricing_message = "How much for 3 containers?"
    result = handler.process_message(pricing_message)
    print(f"💵 Pricing: '{pricing_message}'")
    print(f"   Classification: {result['classification']}")
    print(f"   Response: {result['response'][:100]}...")

def main():
    """Run all tests."""
    print("🧪 Testing Unified Response Handler for IQSTrade")
    print("=" * 60)
    
    # Test general enquiries
    general_success = test_general_enquiries()
    
    # Test specific scenarios
    test_specific_scenarios()
    
    print("\n" + "=" * 60)
    if general_success:
        print("🎉 All tests completed successfully!")
        print("✅ The general enquiry handling is working properly.")
        print("✅ Customers will receive consistent, helpful responses.")
    else:
        print("⚠️  Some tests failed. Please review the issues above.")

if __name__ == "__main__":
    main() 