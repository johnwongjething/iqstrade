#!/usr/bin/env python3
"""
Test Email Validation Integration
Send test emails to verify validation system
"""

import os
import sys
from datetime import datetime

def test_validation_integration():
    """Test the validation integration"""
    
    print("🧪 TESTING EMAIL VALIDATION INTEGRATION")
    print("=" * 40)
    
    # Test cases that should trigger validation
    test_emails = [
        {
            "subject": "[VALIDATION TEST] CTN Processing Time",
            "body": "Hi, I need CTN number for BL 001-123. Also, how long does CTN processing take?",
            "expected_issues": ["ctn_process"]
        },
        {
            "subject": "[VALIDATION TEST] Wrong Amount",
            "body": "I paid $300 for BL NAM20. Please confirm receipt.",
            "expected_issues": ["amount_validation"]
        },
        {
            "subject": "[VALIDATION TEST] Business Hours",
            "body": "What are your business hours? I need to contact you.",
            "expected_issues": ["business_hours"]
        }
    ]
    
    print("📧 Test emails that should trigger validation:")
    for i, test in enumerate(test_emails, 1):
        print(f"   {i}. {test['subject']}")
        print(f"      Expected issues: {', '.join(test['expected_issues'])}")
    
    print("\n📋 To test:")
    print("   1. Send these test emails to your system")
    print("   2. Check logs for 'Validation failed' messages")
    print("   3. Verify enhanced responses are generated")
    print("   4. Run: python monitor_validation.py")

if __name__ == "__main__":
    test_validation_integration()
