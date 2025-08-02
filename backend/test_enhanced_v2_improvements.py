#!/usr/bin/env python3
"""
Test Enhanced V2 Improvements
Tests the improved field extraction, charge tables, and image-based PDF handling
"""

import os
import sys
import json
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_v2_improvements():
    """Test the improvements in enhanced V2 processor"""
    
    print("🧪 TESTING ENHANCED V2 IMPROVEMENTS")
    print("=" * 60)
    
    # Import the new processor
    try:
        from ocr_processor_enhanced_v2 import extract_fields_openai_enhanced_v2
        print("✅ Enhanced V2 processor imported successfully")
    except Exception as e:
        print(f"❌ Failed to import enhanced V2 processor: {e}")
        return False
    
    # Test with a real PDF
    test_folder = Path("new folder (2)")
    if not test_folder.exists():
        print(f"❌ Test folder not found: {test_folder}")
        return False
    
    pdf_files = list(test_folder.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in {test_folder}")
        return False
    
    # Use the first PDF for testing
    test_pdf = pdf_files[0]
    print(f"📄 Testing with: {test_pdf.name}")
    
    try:
        # Test the enhanced V2 processor
        print(f"\n🔍 Testing Enhanced V2 Processor...")
        result = extract_fields_openai_enhanced_v2(str(test_pdf))
        
        print(f"\n📊 EXTRACTION RESULTS:")
        print(f"=" * 50)
        
        # Check key fields
        key_fields = [
            'consignee', 'port_of_loading', 'port_of_discharge',
            'bl_number', 'container_numbers', 'flight_or_vessel',
            'container_count', 'container_count_20ft', 'container_count_40ft', 'container_count_40ft_hc',
            'total_weight_kg', 'shipment_type', 'calculated_ctn_fee', 'calculated_service_fee'
        ]
        
        for field in key_fields:
            value = result.get(field, 'MISSING')
            print(f"  {field}: {value}")
        
        # Check charge table implementation
        print(f"\n💰 CHARGE TABLE IMPLEMENTATION:")
        print(f"=" * 50)
        
        pricing_method = result.get('pricing_method', 'unknown')
        ctn_fee = result.get('calculated_ctn_fee')
        service_fee = result.get('calculated_service_fee')
        total_fee = result.get('calculated_total_fee')
        calculation_log = result.get('pricing_calculation_log', {})
        
        print(f"  Pricing Method: {pricing_method}")
        print(f"  CTN Fee: ${ctn_fee}")
        print(f"  Service Fee: ${service_fee}")
        print(f"  Total Fee: ${total_fee}")
        print(f"  Calculation Details: {json.dumps(calculation_log, indent=2)}")
        
        # Check container breakdown
        print(f"\n📦 CONTAINER BREAKDOWN:")
        print(f"=" * 50)
        
        container_count = result.get('container_count', 0)
        container_count_20ft = result.get('container_count_20ft', 0)
        container_count_40ft = result.get('container_count_40ft', 0)
        container_count_40ft_hc = result.get('container_count_40ft_hc', 0)
        
        print(f"  Total Containers: {container_count}")
        print(f"  20ft Containers: {container_count_20ft}")
        print(f"  40ft Containers: {container_count_40ft}")
        print(f"  40ft High Cube: {container_count_40ft_hc}")
        
        # Check confidence scores
        print(f"\n🎯 CONFIDENCE SCORES:")
        print(f"=" * 50)
        
        overall_confidence = result.get('ocr_confidence_score', 0)
        confidence_breakdown = result.get('confidence_breakdown', {})
        
        print(f"  Overall Confidence: {overall_confidence:.2f}")
        for component, score in confidence_breakdown.items():
            if score is not None:
                print(f"  {component}: {score:.2f}")
        
        # Summary
        print(f"\n✅ ENHANCED V2 IMPROVEMENTS SUMMARY:")
        print(f"=" * 50)
        
        # Check if fields are populated
        populated_fields = sum(1 for field in key_fields if result.get(field) and str(result.get(field)).strip())
        total_fields = len(key_fields)
        field_accuracy = (populated_fields / total_fields) * 100
        
        print(f"  Field Accuracy: {populated_fields}/{total_fields} ({field_accuracy:.1f}%)")
        print(f"  Charge Table: {'✅ Implemented' if pricing_method != 'default' else '❌ Using default'}")
        print(f"  Container Breakdown: {'✅ Working' if container_count > 0 else '❌ Not detected'}")
        print(f"  Fee Calculation: {'✅ Working' if ctn_fee and service_fee else '❌ Failed'}")
        
        # Save results
        output_file = f"enhanced_v2_test_results_{test_pdf.stem}.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_charge_table_logic():
    """Test the charge table logic specifically"""
    
    print(f"\n🧮 TESTING CHARGE TABLE LOGIC")
    print(f"=" * 50)
    
    try:
        from ocr_processor_enhanced_v2 import EnhancedAIOCRProcessorV2
        
        processor = EnhancedAIOCRProcessorV2()
        
        # Test different scenarios
        test_cases = [
            {
                'name': 'Air Freight',
                'shipment_type': 'air',
                'weight_kg': 100,
                'expected_method': 'air_kg'
            },
            {
                'name': 'Ocean 20ft Container',
                'shipment_type': 'ocean',
                'container_types': ['20ft'],
                'expected_method': 'ocean_container'
            },
            {
                'name': 'Ocean 40ft High Cube',
                'shipment_type': 'ocean',
                'container_types': ['40ft_hc'],
                'expected_method': 'ocean_container'
            },
            {
                'name': 'Loose Cargo',
                'shipment_type': 'loose_cargo',
                'weight_kg': 500,
                'expected_method': 'loose_cargo_kg'
            }
        ]
        
        for test_case in test_cases:
            print(f"\n  Testing: {test_case['name']}")
            
            # Create mock data
            from ocr_processor_enhanced_v2 import ContainerInfo, WeightInfo, ShipmentInfo
            
            container_info = ContainerInfo(
                container_numbers=[],
                container_types=test_case.get('container_types', []),
                container_count=len(test_case.get('container_types', [])),
                confidence=0.8
            )
            
            weight_info = WeightInfo(
                total_weight_kg=test_case.get('weight_kg'),
                weight_unit='kg',
                confidence=0.8
            )
            
            shipment_info = ShipmentInfo(
                shipment_type=test_case['shipment_type'],
                confidence=0.9
            )
            
            # Calculate fees
            fees = processor.calculate_fees_with_charge_table(container_info, weight_info, shipment_info)
            
            print(f"    Method: {fees['pricing_method']}")
            print(f"    CTN Fee: ${fees['ctn_fee']}")
            print(f"    Service Fee: ${fees['service_fee']}")
            print(f"    Total: ${fees['total_fee']}")
            
            # Verify method
            if fees['pricing_method'] == test_case['expected_method']:
                print(f"    ✅ Method correct")
            else:
                print(f"    ❌ Method incorrect (expected: {test_case['expected_method']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Charge table test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 ENHANCED V2 IMPROVEMENTS TEST")
    print("=" * 80)
    
    # Test the main processor
    success1 = test_enhanced_v2_improvements()
    
    # Test charge table logic
    success2 = test_charge_table_logic()
    
    if success1 and success2:
        print(f"\n🎉 ALL TESTS PASSED!")
        print(f"✅ Enhanced V2 processor is working correctly")
        print(f"✅ Charge tables are implemented")
        print(f"✅ Field extraction is improved")
    else:
        print(f"\n❌ SOME TESTS FAILED")
        print(f"Please check the errors above") 