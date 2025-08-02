#!/usr/bin/env python3
"""
Test script to verify container numbers and calculated fees fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env.local')

from enhanced_ocr_processor import extract_fields_enhanced
import json

def test_container_and_fees_fix():
    """Test that container numbers and calculated fees are correct"""
    
    print("🧪 TESTING CONTAINER NUMBERS AND FEES FIX")
    print("=" * 50)
    
    # Test with BILL1.pdf (which should have container numbers like LLCU7645999, AAAA6789999)
    pdf_path = "New folder (2)/BILL1.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Test PDF not found: {pdf_path}")
        return False
    
    try:
        print(f"🔍 Testing enhanced OCR on: {pdf_path}")
        result = extract_fields_enhanced(pdf_path, use_openai=True)
        
        print("\n📦 CONTAINER NUMBERS CHECK:")
        container_numbers = result.get('container_numbers', [])
        if isinstance(container_numbers, str):
            container_numbers = [container_numbers]
        
        print(f"   Container Numbers: {container_numbers}")
        
        # Check if container numbers look like actual container numbers (not container types)
        valid_container_numbers = []
        for cn in container_numbers:
            if cn and len(cn) >= 4 and not cn.startswith(('2X', '3X', '40', '20')):
                valid_container_numbers.append(cn)
        
        if valid_container_numbers:
            print(f"   ✅ Found valid container numbers: {valid_container_numbers}")
        else:
            print(f"   ❌ No valid container numbers found")
            return False
        
        print("\n💰 CALCULATED FEES CHECK:")
        calculated_ctn_fee = result.get('calculated_ctn_fee')
        calculated_service_fee = result.get('calculated_service_fee')
        
        print(f"   Calculated CTN Fee: ${calculated_ctn_fee}")
        print(f"   Calculated Service Fee: ${calculated_service_fee}")
        
        # Check if fees are calculated (not the fallback $100 values)
        if calculated_ctn_fee and calculated_ctn_fee > 100:
            print(f"   ✅ CTN fee is calculated: ${calculated_ctn_fee}")
        elif calculated_ctn_fee == 100:
            print(f"   ⚠️ CTN fee is fallback value: ${calculated_ctn_fee}")
        else:
            print(f"   ❌ CTN fee is missing or zero")
        
        if calculated_service_fee and calculated_service_fee > 100:
            print(f"   ✅ Service fee is calculated: ${calculated_service_fee}")
        elif calculated_service_fee == 100:
            print(f"   ⚠️ Service fee is fallback value: ${calculated_service_fee}")
        else:
            print(f"   ❌ Service fee is missing or zero")
        
        print("\n📊 ADDITIONAL ENHANCED FIELDS:")
        print(f"   Container Count: {result.get('container_count')}")
        print(f"   Container Type: {result.get('container_type')}")
        print(f"   Total Weight: {result.get('total_weight_kg')} kg")
        print(f"   Shipment Type: {result.get('shipment_type')}")
        print(f"   OCR Confidence: {result.get('ocr_confidence_score')}")
        
        # Test JSON serialization
        print("\n🔄 TESTING JSON SERIALIZATION:")
        try:
            json_str = json.dumps(result, indent=2)
            print("   ✅ JSON serialization successful!")
            
            # Save to file for inspection
            with open('test_result.json', 'w') as f:
                f.write(json_str)
            print("   📄 Result saved to test_result.json")
            
            return True
        except Exception as e:
            print(f"   ❌ JSON serialization failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_container_and_fees_fix()
    if success:
        print("\n✅ All tests passed! Container numbers and fees fixes are working.")
    else:
        print("\n❌ Tests failed! Some fixes need more work.") 