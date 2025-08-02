#!/usr/bin/env python3
"""
Test Failed Files V3
Tests the Enhanced V3 processor specifically on files that failed in V2
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_failed_files_v3():
    """Test Enhanced V3 processor on files that failed in V2"""
    
    print("🧪 TESTING FAILED FILES WITH V3")
    print("=" * 80)
    
    # Import the V3 processor
    try:
        from ocr_processor_enhanced_v3 import extract_fields_openai_enhanced_v3
        print("✅ Enhanced V3 processor imported successfully")
    except Exception as e:
        print(f"❌ Failed to import V3 processor: {e}")
        return False
    
    # List of files that failed in V2 (0% accuracy)
    failed_files = [
        "b0994f47-71dc-48ef-a6b1-c3add4a356ab.pdf",
        "BILL6.pdf", 
        "Screenshot_20250702_151730_Chrome.PDF",
        "__ MAERSK LINE - New Page 1.pdf"
    ]
    
    # Also test the poor performance file
    poor_performance_files = [
        "account_page (4).pdf"
    ]
    
    all_test_files = failed_files + poor_performance_files
    
    print(f"📁 Testing {len(all_test_files)} files that failed in V2")
    print(f"📄 Files: {all_test_files}")
    print()
    
    # Test results
    results = []
    successful = 0
    failed = 0
    
    for i, filename in enumerate(all_test_files, 1):
        pdf_path = Path("new folder (2)") / filename
        
        if not pdf_path.exists():
            print(f"❌ File not found: {filename}")
            continue
            
        print(f"📄 Testing {i}/{len(all_test_files)}: {filename}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Test the V3 processor
            result = extract_fields_openai_enhanced_v3(str(pdf_path))
            processing_time = time.time() - start_time
            
            # Analyze results
            key_fields = [
                'consignee', 'port_of_loading', 'port_of_discharge',
                'bl_number', 'container_numbers', 'flight_or_vessel'
            ]
            
            populated_fields = sum(1 for field in key_fields if result.get(field) and str(result.get(field)).strip())
            field_accuracy = (populated_fields / len(key_fields)) * 100
            
            # Check if container breakdown is working
            container_count = result.get('container_count', 0)
            container_working = container_count > 0
            
            # Check if fees are calculated
            fees_working = result.get('calculated_ctn_fee') and result.get('calculated_service_fee')
            
            # Check extraction method
            extraction_method = result.get('extraction_method', 'ai')
            document_format = result.get('document_format', 'unknown')
            
            # Determine success
            is_successful = field_accuracy > 50 and container_working and fees_working
            
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
                'raw_text_length': raw_text_length,
                'pricing_method': result.get('pricing_method', ''),
                'calculation_details': result.get('pricing_calculation_log', {})
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
    print(f"📊 V3 TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total Files: {len(all_test_files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(successful/len(all_test_files)*100):.1f}%")
    
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
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"failed_files_v3_test_results_{timestamp}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_file}")
    
    # Show failed files
    failed_files_list = [r['file'] for r in results if r['status'] != 'success']
    if failed_files_list:
        print(f"\n❌ Still Failed Files:")
        for file in failed_files_list:
            print(f"  - {file}")
    
    return successful > 0

if __name__ == "__main__":
    success = test_failed_files_v3()
    
    if success:
        print(f"\n🎉 V3 TEST COMPLETED!")
        print(f"✅ Enhanced V3 processor improved some failed files")
    else:
        print(f"\n❌ V3 TEST FAILED")
        print(f"All files still failing - need further improvements") 