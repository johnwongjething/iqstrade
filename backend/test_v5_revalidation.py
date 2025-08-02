#!/usr/bin/env python3
"""
Test V5 Re-validation System
Tests the Enhanced V5 processor with re-validation on test files
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_v5_revalidation():
    """Test Enhanced V5 processor with re-validation system"""
    
    print("🧪 TESTING V5 RE-VALIDATION SYSTEM")
    print("=" * 80)
    
    # Import the V5 processor
    try:
        from ocr_processor_enhanced_v5 import extract_fields_openai_enhanced_v5
        print("✅ Enhanced V5 processor imported successfully")
    except Exception as e:
        print(f"❌ Failed to import V5 processor: {e}")
        return False
    
    # Test files from new folder (2)
    test_files = [
        "b0994f47-71dc-48ef-a6b1-c3add4a356ab.pdf",
        "BILL6.pdf", 
        "Screenshot_20250702_151730_Chrome.PDF",
        "__ MAERSK LINE - New Page 1.pdf",
        "account_page (4).pdf",
        "BILL1.pdf",
        "BILL2.pdf",
        "BILL3.pdf",
        "BILL4.pdf",
        "BILL5.pdf",
        "2201003.NYC.pdf",
        "2206002.NYC.pdf"
    ]
    
    print(f"📁 Testing {len(test_files)} files with V5 re-validation")
    print(f"📄 Files: {test_files}")
    print()
    
    # Test results
    results = []
    successful = 0
    failed = 0
    revalidations_performed = 0
    
    for i, filename in enumerate(test_files, 1):
        pdf_path = Path("new folder (2)") / filename
        
        if not pdf_path.exists():
            print(f"❌ File not found: {filename}")
            continue
            
        print(f"📄 Testing {i}/{len(test_files)}: {filename}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Test the V5 processor
            result = extract_fields_openai_enhanced_v5(str(pdf_path))
            processing_time = time.time() - start_time
            
            # Analyze results
            key_fields = [
                'consignee', 'port_of_loading', 'port_of_discharge',
                'bl_number', 'container_numbers', 'flight_or_vessel', 'shipper'
            ]
            
            populated_fields = sum(1 for field in key_fields if result.get(field) and str(result.get(field)).strip())
            field_accuracy = (populated_fields / len(key_fields)) * 100
            
            # Check validation results
            validation_result = result.get('validation_result', {})
            missing_fields = validation_result.get('missing_fields', [])
            has_critical_missing = validation_result.get('has_critical_missing', False)
            revalidation_performed = validation_result.get('revalidation_performed', False)
            
            if revalidation_performed:
                revalidations_performed += 1
            
            # Check if container breakdown is working
            container_count = result.get('container_count', 0)
            container_working = container_count > 0
            
            # Check if fees are calculated
            fees_working = result.get('calculated_ctn_fee') and result.get('calculated_service_fee')
            
            # Check extraction method
            extraction_method = result.get('extraction_method', 'ai')
            document_format = result.get('document_type', 'unknown')
            
            # Determine success
            is_successful = field_accuracy > 70 and not has_critical_missing
            
            if is_successful:
                successful += 1
                status = "✅ SUCCESS"
            else:
                failed += 1
                status = "❌ FAILED"
            
            # Print results
            print(f"  Status: {status}")
            print(f"  Processing Time: {processing_time:.2f}s")
            print(f"  Extraction Method: {extraction_method}")
            print(f"  Document Format: {document_format}")
            print(f"  Field Accuracy: {populated_fields}/{len(key_fields)} ({field_accuracy:.1f}%)")
            print(f"  Container Count: {container_count}")
            print(f"  Fees Calculated: {'✅' if fees_working else '❌'}")
            print(f"  Revalidation Performed: {'✅' if revalidation_performed else '❌'}")
            print(f"  Missing Fields: {missing_fields}")
            print(f"  Critical Missing: {'❌' if has_critical_missing else '✅'}")
            
            # Show key fields
            print(f"  Key Fields:")
            for field in key_fields:
                value = result.get(field, '')
                status_icon = "✅" if value else "❌"
                print(f"    {field}: {status_icon} {value}")
            
            # Show container breakdown
            print(f"  Container Breakdown:")
            print(f"    20ft: {result.get('container_count_20ft', 0)}")
            print(f"    40ft: {result.get('container_count_40ft', 0)}")
            print(f"    40ft HC: {result.get('container_count_40ft_hc', 0)}")
            
            # Show fees
            print(f"  Fees:")
            print(f"    CTN Fee: ${result.get('calculated_ctn_fee', 0)}")
            print(f"    Service Fee: ${result.get('calculated_service_fee', 0)}")
            print(f"    Total: ${result.get('calculated_total_fee', 0)}")
            
            # Show confidence breakdown
            confidence_breakdown = result.get('confidence_breakdown', {})
            print(f"  Confidence Breakdown:")
            print(f"    Field Validation: {confidence_breakdown.get('field_validation', 0):.2f}")
            print(f"    Container Detection: {confidence_breakdown.get('container_detection', 0):.2f}")
            print(f"    Weight Detection: {confidence_breakdown.get('weight_detection', 0):.2f}")
            print(f"    Shipment Classification: {confidence_breakdown.get('shipment_classification', 0):.2f}")
            print(f"    Overall: {confidence_breakdown.get('overall', 0):.2f}")
            
            # Show raw text length
            raw_text_length = len(result.get('raw_text', ''))
            print(f"  Raw Text Length: {raw_text_length} characters")
            
            # Store result
            results.append({
                'file': filename,
                'status': 'success' if is_successful else 'failed',
                'processing_time': processing_time,
                'extraction_method': extraction_method,
                'document_format': document_format,
                'field_accuracy': field_accuracy,
                'populated_fields': populated_fields,
                'total_fields': len(key_fields),
                'container_count': container_count,
                'fees_working': fees_working,
                'revalidation_performed': revalidation_performed,
                'missing_fields': missing_fields,
                'has_critical_missing': has_critical_missing,
                'confidence': result.get('ocr_confidence_score', 0),
                'key_fields': {field: result.get(field, '') for field in key_fields},
                'container_breakdown': {
                    '20ft': result.get('container_count_20ft', 0),
                    '40ft': result.get('container_count_40ft', 0),
                    '40ft_hc': result.get('container_count_40ft_hc', 0)
                },
                'fees': {
                    'ctn_fee': result.get('calculated_ctn_fee', 0),
                    'service_fee': result.get('calculated_service_fee', 0),
                    'total_fee': result.get('calculated_total_fee', 0)
                },
                'confidence_breakdown': confidence_breakdown,
                'raw_text_length': raw_text_length,
                'pricing_method': result.get('pricing_method', ''),
                'calculation_details': result.get('pricing_calculation_log', {}),
                'validation_result': validation_result
            })
            
        except Exception as e:
            failed += 1
            processing_time = time.time() - start_time
            print(f"  ❌ ERROR: {e}")
            
            results.append({
                'file': filename,
                'status': 'error',
                'processing_time': processing_time,
                'error': str(e)
            })
        
        print()
    
    # Summary
    print(f"📊 V5 RE-VALIDATION TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total Files: {len(test_files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(successful/len(test_files)*100):.1f}%")
    print(f"Revalidations Performed: {revalidations_performed}")
    print(f"Revalidation Rate: {(revalidations_performed/len(test_files)*100):.1f}%")
    
    if results:
        # Calculate averages
        successful_results = [r for r in results if r['status'] == 'success']
        if successful_results:
            avg_processing_time = sum(r['processing_time'] for r in successful_results) / len(successful_results)
            avg_field_accuracy = sum(r['field_accuracy'] for r in successful_results) / len(successful_results)
            avg_confidence = sum(r['confidence'] for r in successful_results) / len(successful_results)
            
            print(f"Average Processing Time: {avg_processing_time:.2f}s")
            print(f"Average Field Accuracy: {avg_field_accuracy:.1f}%")
            print(f"Average Confidence: {avg_confidence:.2f}")
        
        # Show extraction method breakdown
        methods = {}
        formats = {}
        for r in results:
            if r['status'] == 'success':
                method = r['extraction_method']
                methods[method] = methods.get(method, 0) + 1
                
                format_type = r['document_format']
                formats[format_type] = formats.get(format_type, 0) + 1
        
        print(f"Extraction Methods:")
        for method, count in methods.items():
            print(f"  {method}: {count} files")
        
        print(f"Document Formats:")
        for format_type, count in formats.items():
            print(f"  {format_type}: {count} files")
        
        # Show missing fields analysis
        all_missing_fields = []
        for r in results:
            if r['status'] == 'success':
                all_missing_fields.extend(r.get('missing_fields', []))
        
        if all_missing_fields:
            from collections import Counter
            missing_field_counts = Counter(all_missing_fields)
            print(f"Most Common Missing Fields:")
            for field, count in missing_field_counts.most_common():
                print(f"  {field}: {count} times")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"v5_revalidation_test_results_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Show failed files
    failed_files_list = [r['file'] for r in results if r['status'] != 'success']
    if failed_files_list:
        print(f"\n❌ Failed Files:")
        for file in failed_files_list:
            print(f"  - {file}")
    
    # Show files that needed revalidation
    revalidation_files = [r['file'] for r in results if r.get('revalidation_performed', False)]
    if revalidation_files:
        print(f"\n🔄 Files That Needed Revalidation:")
        for file in revalidation_files:
            print(f"  - {file}")
    
    return successful > 0

if __name__ == "__main__":
    success = test_v5_revalidation()
    
    if success:
        print(f"\n🎉 V5 RE-VALIDATION TEST COMPLETED!")
        print(f"✅ Enhanced V5 processor with re-validation system is working")
    else:
        print(f"\n❌ V5 RE-VALIDATION TEST FAILED")
        print(f"Need to investigate and improve the re-validation system") 