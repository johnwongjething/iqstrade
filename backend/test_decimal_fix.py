#!/usr/bin/env python3
"""
Test script to verify Decimal to float conversion fix
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env.local')

from enhanced_ocr_processor import extract_fields_enhanced
import json

def test_decimal_conversion():
    """Test that no Decimal objects are returned"""
    
    print("🧪 TESTING DECIMAL CONVERSION FIX")
    print("=" * 40)
    
    # Test with a sample PDF
    pdf_path = "New folder (2)/BILL1.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Test PDF not found: {pdf_path}")
        return False
    
    try:
        print(f"🔍 Testing enhanced OCR on: {pdf_path}")
        result = extract_fields_enhanced(pdf_path, use_openai=True)
        
        print("\n📊 CHECKING FOR DECIMAL OBJECTS:")
        
        # Check for Decimal objects in the result
        decimal_found = False
        
        def check_for_decimals(obj, path=""):
            nonlocal decimal_found
            if hasattr(obj, '__class__') and obj.__class__.__name__ == 'Decimal':
                print(f"   ❌ Found Decimal at {path}: {obj}")
                decimal_found = True
            elif isinstance(obj, dict):
                for key, value in obj.items():
                    check_for_decimals(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, value in enumerate(obj):
                    check_for_decimals(value, f"{path}[{i}]")
        
        check_for_decimals(result)
        
        if not decimal_found:
            print("   ✅ No Decimal objects found!")
        else:
            print("   ❌ Decimal objects still present!")
            return False
        
        # Test JSON serialization
        print("\n🔄 TESTING JSON SERIALIZATION:")
        try:
            json_str = json.dumps(result)
            print("   ✅ JSON serialization successful!")
            return True
        except Exception as e:
            print(f"   ❌ JSON serialization failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_decimal_conversion()
    if success:
        print("\n✅ All tests passed! Decimal conversion fix is working.")
    else:
        print("\n❌ Tests failed! Decimal conversion fix needs more work.") 