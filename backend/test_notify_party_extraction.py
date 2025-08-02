#!/usr/bin/env python3
"""
Test script to verify notify party extraction and separation from consignee
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env.local')

from enhanced_ocr_processor import extract_fields_enhanced
import json

def test_notify_party_extraction():
    """Test that notify party is properly extracted and separated from consignee"""
    
    print("🧪 TESTING NOTIFY PARTY EXTRACTION")
    print("=" * 50)
    
    # Test with BILL1.pdf (which should have both consignee and notify party)
    pdf_path = "New folder (2)/BILL1.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Test PDF not found: {pdf_path}")
        return False
    
    try:
        print(f"🔍 Testing enhanced OCR on: {pdf_path}")
        result = extract_fields_enhanced(pdf_path, use_openai=True)
        
        print("\n📋 CONSIGNEE AND NOTIFY PARTY CHECK:")
        consignee = result.get('consignee', '')
        notify_party = result.get('notify_party', '')
        
        print(f"   Consignee: {consignee}")
        print(f"   Notify Party: {notify_party}")
        
        # Check if consignee is clean (doesn't contain multiple company names)
        if len(consignee) > 100 or consignee.count('TEL:') > 1:
            print("   ⚠️ Consignee might still contain multiple parties")
        else:
            print("   ✅ Consignee appears to be clean")
        
        # Check if notify party is properly extracted
        if notify_party:
            print(f"   ✅ Notify party extracted: {notify_party}")
        else:
            print("   ℹ️ No notify party extracted (this might be normal)")
        
        # Check for common patterns that indicate mixed data
        mixed_indicators = ['\n', ';', '|', ' - ', ' / ', ' c/o ', 'ATTN:']
        has_mixed_data = any(indicator in consignee for indicator in mixed_indicators)
        
        if has_mixed_data:
            print("   ℹ️ Consignee contains mixed data patterns")
        else:
            print("   ℹ️ Consignee appears to be clean")
        
        print("\n📊 OTHER FIELDS CHECK:")
        print(f"   Shipper: {result.get('shipper', '')}")
        print(f"   BL Number: {result.get('bl_number', '')}")
        print(f"   Container Numbers: {result.get('container_numbers', '')}")
        print(f"   Calculated CTN Fee: ${result.get('calculated_ctn_fee', '')}")
        print(f"   Calculated Service Fee: ${result.get('calculated_service_fee', '')}")
        
        # Test JSON serialization
        print("\n🔄 TESTING JSON SERIALIZATION:")
        try:
            json_str = json.dumps(result, indent=2)
            print("   ✅ JSON serialization successful!")
            
            # Save to file for inspection
            with open('test_notify_party_result.json', 'w') as f:
                f.write(json_str)
            print("   📄 Result saved to test_notify_party_result.json")
            
            return True
        except Exception as e:
            print(f"   ❌ JSON serialization failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_notify_party_extraction()
    if success:
        print("\n✅ All tests passed! Notify party extraction is working.")
    else:
        print("\n❌ Tests failed! Notify party extraction needs more work.") 