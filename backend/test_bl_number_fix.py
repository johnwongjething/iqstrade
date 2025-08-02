#!/usr/bin/env python3
"""
Test improved BL number extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env.local')

def test_bl_number_extraction():
    """Test BL number extraction improvements"""
    
    print("🔍 TESTING BL NUMBER EXTRACTION IMPROVEMENTS")
    print("=" * 50)
    
    # Test with the problematic documents from the screenshots
    test_files = [
        "New folder (2)/BILL1.pdf",
        "New folder (2)/BILL2.pdf", 
        "New folder (2)/BILL3.pdf",
        "New folder (2)/BILL4.pdf",
        "New folder (2)/BILL5.pdf",
        "New folder (2)/BILL6.pdf"
    ]
    
    for pdf_path in test_files:
        if not os.path.exists(pdf_path):
            print(f"❌ File not found: {pdf_path}")
            continue
            
        print(f"\n📄 Testing: {pdf_path}")
        print("-" * 30)
        
        try:
            from enhanced_ocr_processor import extract_fields_enhanced
            
            # Test enhanced OCR with improved BL number extraction
            result = extract_fields_enhanced(pdf_path, use_openai=True)
            
            print(f"   BL Number: {result.get('bl_number', 'MISSING')}")
            print(f"   Port of Loading: {result.get('port_of_loading', 'MISSING')}")
            print(f"   Port of Discharge: {result.get('port_of_discharge', 'MISSING')}")
            print(f"   Container Numbers: {result.get('container_numbers', 'MISSING')}")
            print(f"   CTN Fee: ${result.get('calculated_ctn_fee', 'MISSING')}")
            print(f"   Service Fee: ${result.get('calculated_service_fee', 'MISSING')}")
            
            # Check if BL number looks like a valid BL number
            bl_number = result.get('bl_number', '')
            if bl_number:
                if len(bl_number) >= 8 and any(c.isdigit() for c in bl_number):
                    print(f"   ✅ BL Number looks valid: {bl_number}")
                else:
                    print(f"   ⚠️ BL Number might be invalid: {bl_number}")
            else:
                print(f"   ❌ BL Number is missing")
            
            # Check if ports are correctly extracted
            pol = result.get('port_of_loading', '')
            pod = result.get('port_of_discharge', '')
            if pol and pod:
                print(f"   ✅ Ports extracted: {pol} → {pod}")
            else:
                print(f"   ⚠️ Ports missing: POL={pol}, POD={pod}")
            
            # Check if fees are calculated
            ctn_fee = result.get('calculated_ctn_fee')
            service_fee = result.get('calculated_service_fee')
            if ctn_fee and service_fee and ctn_fee > 0 and service_fee > 0:
                print(f"   ✅ Fees calculated: CTN=${ctn_fee}, Service=${service_fee}")
            else:
                print(f"   ❌ Fees not calculated or zero")
                
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_bl_number_extraction() 