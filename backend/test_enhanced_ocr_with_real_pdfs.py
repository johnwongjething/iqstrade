#!/usr/bin/env python3
"""
Comprehensive test script for enhanced OCR system using real PDF documents
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_enhanced_ocr_with_pdfs():
    """Test enhanced OCR with all PDF files in the test folder"""
    
    print("🧪 ENHANCED OCR SYSTEM - REAL PDF TEST")
    print("=" * 80)
    
    # Path to the test PDFs
    test_folder = Path("New folder (2)")
    
    if not test_folder.exists():
        print(f"❌ Test folder not found: {test_folder}")
        return False
    
    # Get all PDF files
    pdf_files = list(test_folder.glob("*.pdf"))
    
    if not pdf_files:
        print(f"❌ No PDF files found in {test_folder}")
        return False
    
    print(f"📁 Found {len(pdf_files)} PDF files to test")
    print(f"📂 Test folder: {test_folder.absolute()}")
    
    # Import enhanced OCR processor
    try:
        from enhanced_ocr_processor import extract_fields_enhanced
        print("✅ Enhanced OCR processor imported successfully")
    except Exception as e:
        print(f"❌ Failed to import enhanced OCR processor: {e}")
        return False
    
    # Test results storage
    results = {
        'total_files': len(pdf_files),
        'successful_extractions': 0,
        'failed_extractions': 0,
        'total_processing_time': 0,
        'detailed_results': [],
        'errors': [],
        'summary': {}
    }
    
    # Process each PDF file
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n{'='*60}")
        print(f"📄 Processing file {i}/{len(pdf_files)}: {pdf_file.name}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Process with enhanced OCR
            print(f"🔍 Extracting data from {pdf_file.name}...")
            
            # Try with OpenAI first
            try:
                fields = extract_fields_enhanced(str(pdf_file), use_openai=True)
                ocr_method = "OpenAI"
            except Exception as openai_error:
                print(f"⚠️  OpenAI failed: {openai_error}")
                # Fallback to legacy method
                try:
                    fields = extract_fields_enhanced(str(pdf_file), use_openai=False)
                    ocr_method = "Legacy"
                except Exception as legacy_error:
                    print(f"❌ Both OCR methods failed: {legacy_error}")
                    results['failed_extractions'] += 1
                    results['errors'].append({
                        'file': pdf_file.name,
                        'error': f"OpenAI: {openai_error}, Legacy: {legacy_error}"
                    })
                    continue
            
            processing_time = time.time() - start_time
            results['total_processing_time'] += processing_time
            
            # Analyze the extracted data
            print(f"✅ Extraction completed in {processing_time:.2f}s using {ocr_method}")
            
            # Display extracted information
            print(f"\n📊 EXTRACTED DATA:")
            print(f"   Shipment Type: {fields.get('shipment_type', 'N/A')}")
            print(f"   Container Type: {fields.get('container_type', 'N/A')}")
            print(f"   Container Count: {fields.get('container_count', 'N/A')}")
            print(f"   Total Weight: {fields.get('total_weight_kg', 'N/A')} {fields.get('weight_unit', 'kg')}")
            print(f"   Pricing Method: {fields.get('pricing_method', 'N/A')}")
            print(f"   OCR Confidence: {fields.get('ocr_confidence_score', 'N/A')}")
            
            # Display fee calculations
            print(f"\n💰 FEE CALCULATIONS:")
            print(f"   Calculated CTN Fee: ${fields.get('calculated_ctn_fee', 'N/A')}")
            print(f"   Calculated Service Fee: ${fields.get('calculated_service_fee', 'N/A')}")
            
            if fields.get('calculated_ctn_fee') and fields.get('calculated_service_fee'):
                total_fee = fields.get('calculated_ctn_fee', 0) + fields.get('calculated_service_fee', 0)
                print(f"   Total Calculated Fee: ${total_fee}")
            
            # Display container numbers if available
            if fields.get('container_numbers'):
                print(f"\n📦 CONTAINER NUMBERS:")
                for i, container in enumerate(fields.get('container_numbers', []), 1):
                    print(f"   {i}. {container}")
            
            # Display pricing calculation log
            if fields.get('pricing_calculation_log'):
                print(f"\n📋 PRICING CALCULATION LOG:")
                log = fields.get('pricing_calculation_log', {})
                for key, value in log.items():
                    print(f"   {key}: {value}")
            
            # Store detailed results
            file_result = {
                'file_name': pdf_file.name,
                'file_size_mb': round(pdf_file.stat().st_size / (1024 * 1024), 2),
                'processing_time': round(processing_time, 2),
                'ocr_method': ocr_method,
                'extracted_data': {
                    'shipment_type': fields.get('shipment_type'),
                    'container_type': fields.get('container_type'),
                    'container_count': fields.get('container_count'),
                    'total_weight_kg': fields.get('total_weight_kg'),
                    'weight_unit': fields.get('weight_unit'),
                    'pricing_method': fields.get('pricing_method'),
                    'ocr_confidence_score': fields.get('ocr_confidence_score'),
                    'calculated_ctn_fee': fields.get('calculated_ctn_fee'),
                    'calculated_service_fee': fields.get('calculated_service_fee'),
                    'container_numbers': fields.get('container_numbers', []),
                    'shipper': fields.get('shipper'),
                    'consignee': fields.get('consignee'),
                    'bl_number': fields.get('bl_number'),
                    'port_of_loading': fields.get('port_of_loading'),
                    'port_of_discharge': fields.get('port_of_discharge')
                },
                'pricing_calculation_log': fields.get('pricing_calculation_log', {})
            }
            
            results['detailed_results'].append(file_result)
            results['successful_extractions'] += 1
            
            # Check for potential issues
            issues = []
            if fields.get('ocr_confidence_score', 0) < 0.7:
                issues.append("Low OCR confidence score")
            if not fields.get('container_type') and fields.get('shipment_type') == 'ocean':
                issues.append("Missing container type for ocean shipment")
            if not fields.get('total_weight_kg') and fields.get('shipment_type') in ['air', 'loose_cargo']:
                issues.append("Missing weight for air/loose cargo shipment")
            if not fields.get('calculated_ctn_fee') or not fields.get('calculated_service_fee'):
                issues.append("Missing fee calculations")
            
            if issues:
                print(f"\n⚠️  POTENTIAL ISSUES:")
                for issue in issues:
                    print(f"   - {issue}")
            
        except Exception as e:
            processing_time = time.time() - start_time
            results['total_processing_time'] += processing_time
            results['failed_extractions'] += 1
            results['errors'].append({
                'file': pdf_file.name,
                'error': str(e)
            })
            print(f"❌ Processing failed: {e}")
    
    # Generate summary statistics
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY")
    print(f"{'='*80}")
    
    print(f"📁 Total files processed: {results['total_files']}")
    print(f"✅ Successful extractions: {results['successful_extractions']}")
    print(f"❌ Failed extractions: {results['failed_extractions']}")
    print(f"⏱️  Total processing time: {results['total_processing_time']:.2f}s")
    print(f"📈 Success rate: {(results['successful_extractions']/results['total_files']*100):.1f}%")
    
    if results['successful_extractions'] > 0:
        avg_time = results['total_processing_time'] / results['successful_extractions']
        print(f"⏱️  Average processing time: {avg_time:.2f}s per file")
    
    # Analyze extracted data patterns
    if results['detailed_results']:
        print(f"\n📊 DATA ANALYSIS:")
        
        # Shipment types
        shipment_types = {}
        container_types = {}
        pricing_methods = {}
        confidence_scores = []
        total_fees = []
        
        for result in results['detailed_results']:
            data = result['extracted_data']
            
            # Shipment types
            shipment_type = data.get('shipment_type', 'unknown')
            shipment_types[shipment_type] = shipment_types.get(shipment_type, 0) + 1
            
            # Container types
            container_type = data.get('container_type', 'unknown')
            container_types[container_type] = container_types.get(container_type, 0) + 1
            
            # Pricing methods
            pricing_method = data.get('pricing_method', 'unknown')
            pricing_methods[pricing_method] = pricing_methods.get(pricing_method, 0) + 1
            
            # Confidence scores
            if data.get('ocr_confidence_score'):
                confidence_scores.append(data['ocr_confidence_score'])
            
            # Total fees
            ctn_fee = data.get('calculated_ctn_fee', 0) or 0
            service_fee = data.get('calculated_service_fee', 0) or 0
            total_fee = ctn_fee + service_fee
            if total_fee > 0:
                total_fees.append(total_fee)
        
        print(f"   Shipment Types: {shipment_types}")
        print(f"   Container Types: {container_types}")
        print(f"   Pricing Methods: {pricing_methods}")
        
        if confidence_scores:
            avg_confidence = sum(confidence_scores) / len(confidence_scores)
            print(f"   Average OCR Confidence: {avg_confidence:.3f}")
        
        if total_fees:
            avg_fee = sum(total_fees) / len(total_fees)
            min_fee = min(total_fees)
            max_fee = max(total_fees)
            print(f"   Fee Range: ${min_fee:.2f} - ${max_fee:.2f}")
            print(f"   Average Fee: ${avg_fee:.2f}")
    
    # Display errors if any
    if results['errors']:
        print(f"\n❌ ERRORS ENCOUNTERED:")
        for error in results['errors']:
            print(f"   {error['file']}: {error['error']}")
    
    # Save detailed results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"enhanced_ocr_test_results_{timestamp}.json"
    
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"\n⚠️  Failed to save results: {e}")
    
    print(f"\n{'='*80}")
    if results['successful_extractions'] > 0:
        print("🎉 Enhanced OCR system test completed successfully!")
        print("📋 Review the results above and the saved JSON file for detailed analysis.")
    else:
        print("❌ No successful extractions. Please check the errors above.")
    
    print(f"{'='*80}")
    
    return results['successful_extractions'] > 0

if __name__ == "__main__":
    success = test_enhanced_ocr_with_pdfs()
    sys.exit(0 if success else 1) 