#!/usr/bin/env python3
"""
Test enhanced OCR without OpenAI API key
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_ocr_processor import extract_fields_enhanced
import json

def test_without_openai():
    # Test with one of the BOL files
    pdf_path = "New folder (2)/BILL1.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    print(f"🔍 Testing enhanced OCR WITHOUT OpenAI on: {pdf_path}")
    print("=" * 60)
    
    try:
        # Extract fields using enhanced OCR with use_openai=False
        result = extract_fields_enhanced(pdf_path, use_openai=False)
        
        print("📊 EXTRACTED DATA:")
        print(f"   Shipment Type: {result.get('shipment_type', 'N/A')}")
        print(f"   Container Type: {result.get('container_type', 'N/A')}")
        print(f"   Container Count: {result.get('container_count', 'N/A')}")
        print(f"   Total Weight: {result.get('total_weight_kg', 'N/A')} kg")
        print(f"   Pricing Method: {result.get('pricing_method', 'N/A')}")
        print(f"   OCR Confidence: {result.get('ocr_confidence_score', 'N/A')}")
        
        print("\n💰 FEE CALCULATIONS:")
        print(f"   Calculated CTN Fee: ${result.get('calculated_ctn_fee', 'N/A')}")
        print(f"   Calculated Service Fee: ${result.get('calculated_service_fee', 'N/A')}")
        
        print("\n📦 CONTAINER NUMBERS:")
        container_numbers = result.get('container_numbers', [])
        if isinstance(container_numbers, str):
            container_numbers = [container_numbers] if container_numbers else []
        for i, num in enumerate(container_numbers, 1):
            print(f"   {i}. {num}")
        
        print("\n📋 PRICING CALCULATION LOG:")
        pricing_log = result.get('pricing_calculation_log', {})
        for key, value in pricing_log.items():
            print(f"   {key}: {value}")
        
        print("\n🔍 RAW CONTAINER NUMBERS FROM OCR:")
        print(f"   Raw: '{result.get('container_numbers', 'N/A')}'")
        print(f"   Type: {type(result.get('container_numbers', 'N/A'))}")
        
        print("\n✅ Test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_without_openai() 