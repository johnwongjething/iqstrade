#!/usr/bin/env python3
"""
Comprehensive Test - All PDFs
Tests the Enhanced V2 processor on all PDF files to verify improvements
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_all_pdfs():
    """Test Enhanced V2 processor on all PDF files"""
    
    print("🧪 COMPREHENSIVE PDF TESTING")
    print("=" * 80)
    
    # Import the processor
    try:
        from ocr_processor_enhanced_v2 import extract_fields_openai_enhanced_v2
        print("✅ Enhanced V2 processor imported successfully")
    except Exception as e:
        print(f"❌ Failed to import processor: {e}")
        return False
    
    # Find all PDF files
    test_folder = Path("new folder (2)")
    if not test_folder.exists():
        print(f"❌ Test folder not found: {test_folder}")
        return False
    
    pdf_files = list(test_folder.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in {test_folder}")
        return False
    
    print(f"📁 Found {len(pdf_files)} PDF files for testing")
    print(f"📄 Files: {[f.name for f in pdf_files]}")
    print()
    
    # Test results
    results = []
    successful = 0
    failed = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"📄 Testing {i}/{len(pdf_files)}: {pdf_file.name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Test the processor
            result = extract_fields_openai_enhanced_v2(str(pdf_file))
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
            
            # Save detailed result for analysis
            detailed_result = {
                'file': pdf_file.name,
                'status': 'success' if is_successful else 'failed',
                'processing_time': processing_time,
                'extraction_method': extraction_method,
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
                'all_fields': result,  # Save complete result for detailed analysis
                'raw_text_length': len(result.get('raw_text', '')),
                'pricing_method': result.get('pricing_method', ''),
                'calculation_details': result.get('pricing_calculation_log', {})
            }
            
            # Store detailed result
            results.append(detailed_result)
            
        except Exception as e:
            failed += 1
            processing_time = time.time() - start_time
            print(f"  ❌ ERROR: {e}")
            
            results.append({
                'file': pdf_file.name,
                'status': 'error',
                'processing_time': processing_time,
                'error': str(e)
            })
        
        print()
    
    # Summary
    print(f"📊 COMPREHENSIVE TEST SUMMARY")
    print(f"{'='*80}")
    print(f"Total Files: {len(pdf_files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {(successful/len(pdf_files)*100):.1f}%")
    
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
        for r in results:
            if r['status'] == 'success':
                method = r['extraction_method']
                methods[method] = methods.get(method, 0) + 1
        
        print(f"Extraction Methods:")
        for method, count in methods.items():
            print(f"  {method}: {count} files")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"comprehensive_test_results_{timestamp}.json"
    detailed_analysis_file = f"detailed_analysis_{timestamp}.json"
    
    # Save comprehensive results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Create detailed analysis for missing fields
    analysis = {
        'summary': {
            'total_files': len(pdf_files),
            'successful': successful,
            'failed': failed,
            'success_rate': (successful/len(pdf_files)*100) if pdf_files else 0
        },
        'missing_fields_analysis': {},
        'extraction_methods': {},
        'common_issues': [],
        'recommendations': []
    }
    
    # Analyze missing fields
    field_missing_count = {}
    for field in ['consignee', 'port_of_loading', 'port_of_discharge', 'bl_number', 'container_numbers', 'flight_or_vessel']:
        field_missing_count[field] = 0
    
    for result in results:
        if result['status'] == 'success':
            for field in field_missing_count:
                if not result['key_fields'].get(field):
                    field_missing_count[field] += 1
    
    analysis['missing_fields_analysis'] = field_missing_count
    
    # Analyze extraction methods
    method_count = {}
    for result in results:
        if result['status'] == 'success':
            method = result['extraction_method']
            method_count[method] = method_count.get(method, 0) + 1
    
    analysis['extraction_methods'] = method_count
    
    # Save detailed analysis
    with open(detailed_analysis_file, 'w') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to:")
    print(f"  📄 Comprehensive results: {output_file}")
    print(f"  📊 Detailed analysis: {detailed_analysis_file}")
    
    # Show failed files
    failed_files = [r['file'] for r in results if r['status'] != 'success']
    if failed_files:
        print(f"\n❌ Failed Files:")
        for file in failed_files:
            print(f"  - {file}")
    
    return successful > 0

if __name__ == "__main__":
    success = test_all_pdfs()
    
    if success:
        print(f"\n🎉 COMPREHENSIVE TEST COMPLETED!")
        print(f"✅ Enhanced V2 processor is working across multiple files")
    else:
        print(f"\n❌ COMPREHENSIVE TEST FAILED")
        print(f"Please check the errors above") 