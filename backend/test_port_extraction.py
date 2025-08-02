#!/usr/bin/env python3
"""
Test script to verify improved port extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_ocr_processor import EnhancedOCRProcessor

def test_port_extraction():
    """Test the port extraction improvements"""
    
    processor = EnhancedOCRProcessor()
    
    # Test cases based on the screenshots
    test_cases = [
        {
            "name": "Picture 1 - Port of Discharge showing form label",
            "text": """
            15. PORT OF LOADING/EXPORT: HONG KONG
            16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY): NIGERIA
            17. PLACE OF DELIVERY BY ON-CARRIER: NIGERIA
            """,
            "expected_loading": "HONG KONG",
            "expected_discharge": "NIGERIA"
        },
        {
            "name": "Picture 2 - Port of Discharge showing form label",
            "text": """
            15. PORT OF LOADING/EXPORT: SHANGHAI
            16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY): HUNGARY
            17. PLACE OF DELIVERY BY ON-CARRIER: HUNGARY
            """,
            "expected_loading": "SHANGHAI",
            "expected_discharge": "HUNGARY"
        },
        {
            "name": "Test 3 - Form labels that should be filtered out",
            "text": """
            PORT OF DISCHARGE: a. CONTAINERIZED(Vessel Only)
            """,
            "expected_loading": "",
            "expected_discharge": ""
        },
        {
            "name": "Test 4 - Another form label",
            "text": """
            PORT OF DISCHARGE: a. CONTAIN
            """,
            "expected_loading": "",
            "expected_discharge": ""
        }
    ]
    
    print("🔍 Testing Port Extraction Improvements")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 30)
        print(f"Sample text: {test_case['text'].strip()}")
        
        # Test raw text extraction
        result = processor.extract_ports_from_raw_text(test_case['text'])
        
        print(f"Port of Loading: '{result.get('port_of_loading', '')}'")
        print(f"Port of Discharge: '{result.get('port_of_discharge', '')}'")
        print(f"Expected Loading: '{test_case['expected_loading']}'")
        print(f"Expected Discharge: '{test_case['expected_discharge']}'")
        
        loading_pass = result.get('port_of_loading', '') == test_case['expected_loading']
        discharge_pass = result.get('port_of_discharge', '') == test_case['expected_discharge']
        
        if loading_pass and discharge_pass:
            print("✅ PASS")
        else:
            print("❌ FAIL")
            if not loading_pass:
                print(f"   Loading mismatch: got '{result.get('port_of_loading', '')}', expected '{test_case['expected_loading']}'")
            if not discharge_pass:
                print(f"   Discharge mismatch: got '{result.get('port_of_discharge', '')}', expected '{test_case['expected_discharge']}'")
    
    # Test legacy extraction with form labels
    print(f"\nTest Legacy Extraction with Form Labels:")
    print("-" * 40)
    
    test_text = """
    15. PORT OF LOADING/EXPORT: HONG KONG
    16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY): a. CONTAINERIZED(Vessel Only)
    17. PLACE OF DELIVERY BY ON-CARRIER: NIGERIA
    """
    
    result = processor.extract_ports_legacy(test_text)
    print(f"Legacy extraction result:")
    print(f"  Port of Loading: '{result.get('port_of_loading', '')}'")
    print(f"  Port of Discharge: '{result.get('port_of_discharge', '')}'")
    
    # Test the form label filtering
    form_labels = ['CONTAINERIZED', 'CONTAIN', 'VESSEL', 'ONLY']
    discharge = result.get('port_of_discharge', '')
    has_form_label = any(label in discharge.upper() for label in form_labels)
    
    print(f"  Contains form label: {has_form_label}")
    if has_form_label:
        print("  ✅ Form label correctly identified")
    else:
        print("  ❌ Form label not detected")

if __name__ == "__main__":
    test_port_extraction() 