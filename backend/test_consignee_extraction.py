#!/usr/bin/env python3
"""
Test script to verify improved consignee extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_ocr_processor import EnhancedOCRProcessor

def test_consignee_extraction():
    """Test the consignee extraction improvements"""
    
    processor = EnhancedOCRProcessor()
    
    # Test cases based on the screenshots
    test_cases = [
        {
            "name": "Picture 1 - Dict consignee with notify party",
            "consignee_dict": {'company_name': 'HAYWARD INDUSTRIES, INC.', 'address': 'C/O DEAN WAREHOUSE SVC. 292 KILVERT STREET WARWICK, RI 02886 USA'},
            "expected": "HAYWARD INDUSTRIES, INC."
        },
        {
            "name": "Picture 2 - String consignee with address",
            "consignee_string": "SMART FAMOUS LTD, 1200 BRUNSWICK AVENUE FAR ROCKAWAY, NY 11691",
            "expected": "SMART FAMOUS LTD"
        },
        {
            "name": "Test 3 - Consignee with phone number",
            "consignee_string": "SMART FAMOUS LTD TEL: (401) 583-1100",
            "expected": "SMART FAMOUS LTD"
        },
        {
            "name": "Test 4 - Consignee with C/O",
            "consignee_string": "SMART FAMOUS LTD C/O DEAN WAREHOUSE SVC.",
            "expected": "SMART FAMOUS LTD"
        },
        {
            "name": "Test 5 - Consignee with ATTN",
            "consignee_string": "SMART FAMOUS LTD ATTN: DIANNE BARBOSA",
            "expected": "SMART FAMOUS LTD"
        }
    ]
    
    print("🔍 Testing Consignee Extraction Improvements")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 30)
        
        if 'consignee_dict' in test_case:
            # Test dict input
            result = processor.extract_company_name_only(str(test_case['consignee_dict']))
            print(f"Input (dict): {test_case['consignee_dict']}")
        else:
            # Test string input
            result = processor.extract_company_name_only(test_case['consignee_string'])
            print(f"Input (string): {test_case['consignee_string']}")
        
        print(f"Result: '{result}'")
        print(f"Expected: '{test_case['expected']}'")
        
        if result == test_case['expected']:
            print("✅ PASS")
        else:
            print("❌ FAIL")
    
    # Test raw text extraction
    print(f"\nTest Raw Text Extraction:")
    print("-" * 30)
    
    sample_text = """
    3. CONSIGNED TO
    SMART FAMOUS LTD
    C/O DEAN WAREHOUSE SVC.
    292 KILVERT STREET
    WARWICK, RI 02886 USA
    TEL: (401) 583-1100
    
    4. NOTIFY PARTY/INTERMEDIATE CONSIGNEE
    HAYWARD INDUSTRIES, INC.
    C/O DEAN WAREHOUSE SVC.
    292 KILVERT STREET
    WARWICK, RI 02886 USA
    """
    
    extracted = processor.extract_consignee_from_raw_text(sample_text)
    print(f"Raw text extraction result: '{extracted}'")
    print("Expected: 'SMART FAMOUS LTD'")
    
    if extracted == "SMART FAMOUS LTD":
        print("✅ PASS")
    else:
        print("❌ FAIL")

if __name__ == "__main__":
    test_consignee_extraction() 