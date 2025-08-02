#!/usr/bin/env python3
"""
Comprehensive test script using real PDFs
Tests both regex and box-based extraction approaches
"""

import sys
import os
import time
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_ocr_processor import EnhancedOCRProcessor
from box_based_extractor import extract_fields_box_based
from ocr_processor import extract_fields_openai
import json

def test_pdf_extraction(pdf_path: str) -> dict:
    """Test extraction on a single PDF"""
    print(f"\n📄 Testing: {os.path.basename(pdf_path)}")
    print("-" * 50)
    
    try:
        # Extract raw text using OpenAI OCR
        print("🔍 Extracting text with OpenAI OCR...")
        start_time = time.time()
        basic_fields = extract_fields_openai(pdf_path)
        ocr_time = time.time() - start_time
        
        raw_text = basic_fields.get('raw_text', '')
        print(f"✅ OCR completed in {ocr_time:.2f}s")
        print(f"📝 Text length: {len(raw_text)} characters")
        
        if not raw_text:
            print("❌ No text extracted from PDF")
            return {
                "filename": os.path.basename(pdf_path),
                "status": "failed",
                "error": "No text extracted"
            }
        
        # Test regex approach
        print("\n📋 Testing Regex Approach...")
        start_time = time.time()
        processor = EnhancedOCRProcessor()
        
        # Test port extraction
        regex_ports = processor.extract_ports_from_raw_text(raw_text)
        
        # Test consignee extraction
        regex_consignee = processor.extract_consignee_from_raw_text(raw_text)
        
        # Test container extraction
        container_patterns = [
            r'\b[A-Z]{4}\d{7}\b',  # Standard container format
            r'CONTR\s*#\s*([A-Z]{4}\d{7})',
        ]
        regex_containers = []
        for pattern in container_patterns:
            matches = re.findall(pattern, raw_text, re.IGNORECASE)
            if matches:
                if isinstance(matches[0], tuple):
                    regex_containers.extend([m[0] for m in matches if m[0]])
                else:
                    regex_containers.extend(matches)
                break
        
        regex_time = time.time() - start_time
        
        # Test box-based approach
        print("\n📦 Testing Box-Based Approach...")
        start_time = time.time()
        box_results = extract_fields_box_based(raw_text)
        box_time = time.time() - start_time
        
        # Compare results
        print("\n📊 Results Comparison:")
        print(f"  Port of Loading:")
        print(f"    Regex: '{regex_ports.get('port_of_loading', '')}'")
        print(f"    Box:   '{box_results.get('port_of_loading', '')}'")
        
        print(f"  Port of Discharge:")
        print(f"    Regex: '{regex_ports.get('port_of_discharge', '')}'")
        print(f"    Box:   '{box_results.get('port_of_discharge', '')}'")
        
        print(f"  Consignee:")
        print(f"    Regex: '{regex_consignee}'")
        print(f"    Box:   '{box_results.get('consignee', '')}'")
        
        print(f"  Container Numbers:")
        print(f"    Regex: '{', '.join(regex_containers)}'")
        print(f"    Box:   '{box_results.get('container_numbers', '')}'")
        
        print(f"\n⏱️ Performance:")
        print(f"  OCR Time: {ocr_time:.2f}s")
        print(f"  Regex Time: {regex_time:.2f}s")
        print(f"  Box Time: {box_time:.2f}s")
        print(f"  Total Regex: {ocr_time + regex_time:.2f}s")
        print(f"  Total Box: {ocr_time + box_time:.2f}s")
        
        # Check for form label issues
        form_labels = ['CONTAINERIZED', 'CONTAIN', 'VESSEL', 'ONLY', 'AIR', 'FREIGHT']
        regex_has_form_label = any(label in regex_ports.get('port_of_discharge', '').upper() for label in form_labels)
        box_has_form_label = any(label in box_results.get('port_of_discharge', '').upper() for label in form_labels)
        
        print(f"\n🚨 Form Label Detection:")
        print(f"  Regex has form label: {regex_has_form_label}")
        print(f"  Box has form label: {box_has_form_label}")
        
        return {
            "filename": os.path.basename(pdf_path),
            "status": "success",
            "text_length": len(raw_text),
            "ocr_time": ocr_time,
            "regex_results": {
                "port_of_loading": regex_ports.get('port_of_loading', ''),
                "port_of_discharge": regex_ports.get('port_of_discharge', ''),
                "consignee": regex_consignee,
                "container_numbers": regex_containers,
                "processing_time": regex_time,
                "has_form_label": regex_has_form_label
            },
            "box_results": {
                "port_of_loading": box_results.get('port_of_loading', ''),
                "port_of_discharge": box_results.get('port_of_discharge', ''),
                "consignee": box_results.get('consignee', ''),
                "container_numbers": box_results.get('container_numbers', ''),
                "processing_time": box_time,
                "has_form_label": box_has_form_label
            }
        }
        
    except Exception as e:
        print(f"❌ Error processing {pdf_path}: {str(e)}")
        return {
            "filename": os.path.basename(pdf_path),
            "status": "error",
            "error": str(e)
        }

def analyze_results(all_results: list):
    """Analyze and summarize all test results"""
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE ANALYSIS")
    print("="*80)
    
    successful_tests = [r for r in all_results if r["status"] == "success"]
    failed_tests = [r for r in all_results if r["status"] != "success"]
    
    print(f"\n📈 Summary:")
    print(f"  Total PDFs: {len(all_results)}")
    print(f"  Successful: {len(successful_tests)}")
    print(f"  Failed: {len(failed_tests)}")
    
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"  - {test['filename']}: {test.get('error', 'Unknown error')}")
    
    if successful_tests:
        # Performance analysis
        total_ocr_time = sum(r["ocr_time"] for r in successful_tests)
        total_regex_time = sum(r["regex_results"]["processing_time"] for r in successful_tests)
        total_box_time = sum(r["box_results"]["processing_time"] for r in successful_tests)
        
        print(f"\n⏱️ Performance Analysis:")
        print(f"  Total OCR Time: {total_ocr_time:.2f}s")
        print(f"  Total Regex Processing: {total_regex_time:.2f}s")
        print(f"  Total Box Processing: {total_box_time:.2f}s")
        print(f"  Regex is {total_regex_time/total_box_time:.1f}x {'slower' if total_regex_time > total_box_time else 'faster'} than Box")
        
        # Form label analysis
        regex_form_labels = sum(1 for r in successful_tests if r["regex_results"]["has_form_label"])
        box_form_labels = sum(1 for r in successful_tests if r["box_results"]["has_form_label"])
        
        print(f"\n🚨 Form Label Issues:")
        print(f"  Regex approach: {regex_form_labels} files with form labels")
        print(f"  Box approach: {box_form_labels} files with form labels")
        print(f"  Improvement: {regex_form_labels - box_form_labels} fewer form label issues")
        
        # Accuracy analysis
        print(f"\n🎯 Accuracy Analysis:")
        
        # Port extraction comparison
        port_loading_matches = sum(1 for r in successful_tests 
                                 if r["regex_results"]["port_of_loading"] == r["box_results"]["port_of_loading"])
        port_discharge_matches = sum(1 for r in successful_tests 
                                   if r["regex_results"]["port_of_discharge"] == r["box_results"]["port_of_discharge"])
        
        print(f"  Port of Loading matches: {port_loading_matches}/{len(successful_tests)} ({port_loading_matches/len(successful_tests)*100:.1f}%)")
        print(f"  Port of Discharge matches: {port_discharge_matches}/{len(successful_tests)} ({port_discharge_matches/len(successful_tests)*100:.1f}%)")
        
        # Show specific differences
        print(f"\n🔍 Detailed Differences:")
        for test in successful_tests:
            if (test["regex_results"]["port_of_loading"] != test["box_results"]["port_of_loading"] or
                test["regex_results"]["port_of_discharge"] != test["box_results"]["port_of_discharge"]):
                print(f"\n  {test['filename']}:")
                if test["regex_results"]["port_of_loading"] != test["box_results"]["port_of_loading"]:
                    print(f"    Loading: Regex='{test['regex_results']['port_of_loading']}' vs Box='{test['box_results']['port_of_loading']}'")
                if test["regex_results"]["port_of_discharge"] != test["box_results"]["port_of_discharge"]:
                    print(f"    Discharge: Regex='{test['regex_results']['port_of_discharge']}' vs Box='{test['box_results']['port_of_discharge']}'")

def main():
    """Main test function"""
    print("🧪 REAL PDF EXTRACTION TEST")
    print("="*60)
    print("Testing both regex and box-based approaches on 12 real PDFs")
    
    # Get test PDFs
    test_folder = Path("new folder (2)")
    if not test_folder.exists():
        print(f"❌ Test folder not found: {test_folder}")
        return
    
    pdf_files = list(test_folder.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in {test_folder}")
        return
    
    print(f"📁 Found {len(pdf_files)} PDF files for testing")
    
    # Test each PDF
    all_results = []
    for pdf_file in pdf_files:
        result = test_pdf_extraction(str(pdf_file))
        all_results.append(result)
        
        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump(all_results, f, indent=2)
    
    # Analyze results
    analyze_results(all_results)
    
    print(f"\n💾 Detailed results saved to: test_results.json")
    print(f"✅ Testing completed!")

if __name__ == "__main__":
    import re  # Import here for the regex patterns
    main() 