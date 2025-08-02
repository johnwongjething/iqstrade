#!/usr/bin/env python3
"""
Quick Validation Test
Test the validation system with actual email processing
"""

import sys
import os
from email_validation_production import EmailValidationSystem, validate_email_with_openai
from email_ingestor import handle_email_via_openai

def test_validation_system():
    """Test the validation system with real email processing"""
    
    print("🧪 QUICK VALIDATION SYSTEM TEST")
    print("=" * 40)
    
    # Test cases that should trigger validation
    test_cases = [
        {
            "name": "CTN Processing Time",
            "subject": "[TEST] CTN Processing Time",
            "body": "Hi, I need CTN number for BL 001-123. Also, how long does CTN processing take?",
            "expected_issues": ["ctn_process"]
        },
        {
            "name": "Wrong Amount",
            "subject": "[TEST] Wrong Amount",
            "body": "I paid $300 for BL NAM20. Please confirm receipt.",
            "expected_issues": ["amount_validation"]
        },
        {
            "name": "Business Hours",
            "subject": "[TEST] Business Hours",
            "body": "What are your business hours? I need to contact you.",
            "expected_issues": ["business_hours"]
        }
    ]
    
    validator = EmailValidationSystem()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📧 Test {i}: {test_case['name']}")
        print("-" * 30)
        
        # Test validation detection
        detected_requests = validator.detect_request_types(test_case['body'])
        print(f"Detected requests: {detected_requests}")
        
        # Test amount extraction
        amounts = validator.extract_amounts(test_case['body'])
        print(f"Extracted amounts: {amounts}")
        
        # Test with actual OpenAI processing
        try:
            print("Processing with OpenAI...")
            result = validate_email_with_openai(
                test_case['subject'],
                test_case['body'],
                [],  # No attachments
                "test@example.com",
                handle_email_via_openai
            )
            
            print(f"✅ Processing completed")
            print(f"   Confidence: {result.get('confidence_score', 0)}")
            print(f"   Enhanced used: {result.get('enhanced_processing_used', False)}")
            
            validation_result = result.get('validation_result', {})
            if validation_result.get('needs_reclassification'):
                print(f"   🚨 Validation issues detected:")
                print(f"      Missed: {validation_result.get('missed_request_types', [])}")
                print(f"      Amount issues: {len(validation_result.get('amount_validation_issues', []))}")
            else:
                print(f"   ✅ No validation issues")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n🎉 Validation system test completed!")
    print("If you see validation issues detected, the system is working correctly!")

if __name__ == "__main__":
    test_validation_system() 