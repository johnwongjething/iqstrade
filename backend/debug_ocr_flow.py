#!/usr/bin/env python3
"""
Debug script to test OCR flow and identify extraction issues
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv('.env.local')

import json

def test_ocr_flow():
    """Test the complete OCR flow to identify issues"""
    
    print("🔍 DEBUGGING OCR FLOW")
    print("=" * 50)
    
    # Test with a sample PDF
    pdf_path = "New folder (2)/BILL1.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Test PDF not found: {pdf_path}")
        return False
    
    try:
        print(f"📄 Testing with: {pdf_path}")
        
        # Test 1: Direct OpenAI extraction
        print("\n🧪 TEST 1: Direct OpenAI Extraction")
        print("-" * 30)
        try:
            from ocr_processor import extract_fields_openai
            openai_result = extract_fields_openai(pdf_path)
            print("✅ OpenAI extraction successful")
            print(f"   BL Number: {openai_result.get('bl_number', 'MISSING')}")
            print(f"   Shipper: {openai_result.get('shipper', 'MISSING')}")
            print(f"   Consignee: {openai_result.get('consignee', 'MISSING')}")
            print(f"   Container Numbers: {openai_result.get('container_numbers', 'MISSING')}")
            print(f"   Port of Loading: {openai_result.get('port_of_loading', 'MISSING')}")
            print(f"   Port of Discharge: {openai_result.get('port_of_discharge', 'MISSING')}")
            print(f"   Flight/Vessel: {openai_result.get('flight_or_vessel', 'MISSING')}")
        except Exception as e:
            print(f"❌ OpenAI extraction failed: {e}")
        
        # Test 2: Enhanced OCR with OpenAI
        print("\n🧪 TEST 2: Enhanced OCR with OpenAI")
        print("-" * 35)
        try:
            from enhanced_ocr_processor import extract_fields_enhanced
            enhanced_openai_result = extract_fields_enhanced(pdf_path, use_openai=True)
            print("✅ Enhanced OCR with OpenAI successful")
            print(f"   BL Number: {enhanced_openai_result.get('bl_number', 'MISSING')}")
            print(f"   Shipper: {enhanced_openai_result.get('shipper', 'MISSING')}")
            print(f"   Consignee: {enhanced_openai_result.get('consignee', 'MISSING')}")
            print(f"   Notify Party: {enhanced_openai_result.get('notify_party', 'MISSING')}")
            print(f"   Container Numbers: {enhanced_openai_result.get('container_numbers', 'MISSING')}")
            print(f"   Container Count: {enhanced_openai_result.get('container_count', 'MISSING')}")
            print(f"   Port of Loading: {enhanced_openai_result.get('port_of_loading', 'MISSING')}")
            print(f"   Port of Discharge: {enhanced_openai_result.get('port_of_discharge', 'MISSING')}")
            print(f"   Flight/Vessel: {enhanced_openai_result.get('flight_or_vessel', 'MISSING')}")
            print(f"   Calculated CTN Fee: ${enhanced_openai_result.get('calculated_ctn_fee', 'MISSING')}")
            print(f"   Calculated Service Fee: ${enhanced_openai_result.get('calculated_service_fee', 'MISSING')}")
        except Exception as e:
            print(f"❌ Enhanced OCR with OpenAI failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 3: Enhanced OCR without OpenAI (should fallback to legacy)
        print("\n🧪 TEST 3: Enhanced OCR without OpenAI (Fallback)")
        print("-" * 50)
        try:
            from enhanced_ocr_processor import extract_fields_enhanced
            enhanced_legacy_result = extract_fields_enhanced(pdf_path, use_openai=False)
            print("✅ Enhanced OCR without OpenAI successful")
            print(f"   BL Number: {enhanced_legacy_result.get('bl_number', 'MISSING')}")
            print(f"   Shipper: {enhanced_legacy_result.get('shipper', 'MISSING')}")
            print(f"   Consignee: {enhanced_legacy_result.get('consignee', 'MISSING')}")
            print(f"   Notify Party: {enhanced_legacy_result.get('notify_party', 'MISSING')}")
            print(f"   Container Numbers: {enhanced_legacy_result.get('container_numbers', 'MISSING')}")
            print(f"   Container Count: {enhanced_legacy_result.get('container_count', 'MISSING')}")
            print(f"   Port of Loading: {enhanced_legacy_result.get('port_of_loading', 'MISSING')}")
            print(f"   Port of Discharge: {enhanced_legacy_result.get('port_of_discharge', 'MISSING')}")
            print(f"   Flight/Vessel: {enhanced_legacy_result.get('flight_or_vessel', 'MISSING')}")
            print(f"   Calculated CTN Fee: ${enhanced_legacy_result.get('calculated_ctn_fee', 'MISSING')}")
            print(f"   Calculated Service Fee: ${enhanced_legacy_result.get('calculated_service_fee', 'MISSING')}")
        except Exception as e:
            print(f"❌ Enhanced OCR without OpenAI failed: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_ocr_flow()
    if success:
        print("\n✅ OCR flow debugging completed!")
    else:
        print("\n❌ OCR flow debugging failed!") 