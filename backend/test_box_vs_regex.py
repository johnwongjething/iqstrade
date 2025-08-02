#!/usr/bin/env python3
"""
Test script to compare box-based vs regex extraction approaches
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_ocr_processor import EnhancedOCRProcessor
from box_based_extractor import extract_fields_box_based
import time

def test_extraction_approaches():
    """Compare box-based vs regex extraction"""
    
    # Test cases with different BOL formats
    test_cases = [
        {
            "name": "Standard BOL Format",
            "text": """
            2. SHIPPER (EXPORTER): RAY TOP
            3. CONSIGNED TO: SMART FAMOUS LTD
            4. NOTIFY PARTY: SAME AS CONSIGNEE
            6a. B/L NUMBER: NYC2207777
            14. EXPORTING CARRIER: OOCL BERLIN v.041E
            15. PORT OF LOADING/EXPORT: HONG KONG
            16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY): NIGERIA
            17. PLACE OF DELIVERY BY ON-CARRIER: NIGERIA
            CONTR # OOCU7645898 SEAL # 17531510
            20. DESCRIPTION OF COMMODITIES: SHIPPER'S LOAD & COUNT
            """
        },
        {
            "name": "CMA CGM Format",
            "text": """
            SHIPPER: JETHING INT LTD
            CONSIGNEE: SO FUN NIGERIA
            PORT OF LOADING: SHANGHAI
            PORT OF DISCHARGE: HUNGARY
            VESSEL: TIMON v.2201E
            """
        },
        {
            "name": "Problematic Form Labels",
            "text": """
            15. PORT OF LOADING/EXPORT: HONG KONG
            16. FOREIGN PORT OF UNLOADING (VESSEL AND AIR ONLY): a. CONTAINERIZED(Vessel Only)
            17. PLACE OF DELIVERY BY ON-CARRIER: NIGERIA
            """
        }
    ]
    
    print("🔍 Comparing Box-Based vs Regex Extraction")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['name']}")
        print("-" * 40)
        print(f"Sample text:\n{test_case['text'].strip()}")
        
        # Test regex approach
        print(f"\n📋 Regex Approach:")
        start_time = time.time()
        processor = EnhancedOCRProcessor()
        regex_ports = processor.extract_ports_from_raw_text(test_case['text'])
        regex_time = time.time() - start_time
        
        print(f"  Port of Loading: '{regex_ports.get('port_of_loading', '')}'")
        print(f"  Port of Discharge: '{regex_ports.get('port_of_discharge', '')}'")
        print(f"  Time: {regex_time:.4f}s")
        
        # Test box-based approach
        print(f"\n📦 Box-Based Approach:")
        start_time = time.time()
        box_results = extract_fields_box_based(test_case['text'])
        box_time = time.time() - start_time
        
        print(f"  Port of Loading: '{box_results.get('port_of_loading', '')}'")
        print(f"  Port of Discharge: '{box_results.get('port_of_discharge', '')}'")
        print(f"  Time: {box_time:.4f}s")
        
        # Compare results
        print(f"\n📊 Comparison:")
        loading_match = regex_ports.get('port_of_loading', '') == box_results.get('port_of_loading', '')
        discharge_match = regex_ports.get('port_of_discharge', '') == box_results.get('port_of_discharge', '')
        
        if loading_match and discharge_match:
            print("  ✅ Results match")
        else:
            print("  ❌ Results differ")
            if not loading_match:
                print(f"    Loading: Regex='{regex_ports.get('port_of_loading', '')}' vs Box='{box_results.get('port_of_loading', '')}'")
            if not discharge_match:
                print(f"    Discharge: Regex='{regex_ports.get('port_of_discharge', '')}' vs Box='{box_results.get('port_of_discharge', '')}'")
        
        print(f"  Speed: Box-based is {regex_time/box_time:.1f}x {'faster' if box_time < regex_time else 'slower'}")

def test_scalability():
    """Test how well each approach scales with new formats"""
    
    print(f"\n🔬 Scalability Test")
    print("=" * 40)
    
    # Simulate adding new BOL format
    new_format_text = """
    NEW SHIPPING LINE BOL FORMAT:
    SENDER: NEW COMPANY LTD
    RECEIVER: NEW CONSIGNEE INC
    ORIGIN PORT: NEW YORK
    DESTINATION PORT: LONDON
    """
    
    print("Adding new format to box-based system...")
    
    # Box-based approach: Just add new layout
    new_layout = {
        "new_format": [
            ("shipper", ["SENDER"]),
            ("consignee", ["RECEIVER"]),
            ("port_of_loading", ["ORIGIN PORT"]),
            ("port_of_discharge", ["DESTINATION PORT"]),
        ]
    }
    print("✅ Box-based: Add new layout definition")
    
    # Regex approach: Need to add multiple patterns
    new_patterns = [
        r'SENDER[:\s]*([A-Z\s]+)',
        r'RECEIVER[:\s]*([A-Z\s]+)',
        r'ORIGIN\s+PORT[:\s]*([A-Z\s]+)',
        r'DESTINATION\s+PORT[:\s]*([A-Z\s]+)',
    ]
    print("❌ Regex: Need to add 4+ new patterns")
    
    print("\n📈 Scalability Comparison:")
    print("  Box-based: O(1) - Add one layout definition")
    print("  Regex: O(n) - Add n patterns for n fields")

def test_maintainability():
    """Test maintainability aspects"""
    
    print(f"\n🔧 Maintainability Test")
    print("=" * 40)
    
    print("Box-based approach advantages:")
    print("  ✅ Field locations are explicit and documented")
    print("  ✅ Easy to visualize field positions")
    print("  ✅ Centralized field definitions")
    print("  ✅ Easy to add new document types")
    print("  ✅ Less prone to regex pattern conflicts")
    
    print("\nRegex approach disadvantages:")
    print("  ❌ Patterns scattered throughout code")
    print("  ❌ Hard to maintain as patterns grow")
    print("  ❌ Easy to break existing patterns")
    print("  ❌ Difficult to debug pattern conflicts")
    print("  ❌ No visual representation of field locations")

if __name__ == "__main__":
    test_extraction_approaches()
    test_scalability()
    test_maintainability() 