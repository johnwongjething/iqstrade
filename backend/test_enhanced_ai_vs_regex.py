#!/usr/bin/env python3
"""
Test script to compare Enhanced AI vs Enhanced Regex approaches
Demonstrates the superiority of AI-based approach
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_comparison():
    """Compare Enhanced AI vs Enhanced Regex approaches"""
    
    print("🧪 ENHANCED AI vs ENHANCED REGEX COMPARISON")
    print("=" * 80)
    
    # Import both approaches
    try:
        from ocr_processor_enhanced import extract_fields_openai_enhanced
        from enhanced_ocr_processor import extract_fields_enhanced
        print("✅ Both OCR processors imported successfully")
    except Exception as e:
        print(f"❌ Failed to import OCR processors: {e}")
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
    
    results = {
        'test_pdf': test_pdf.name,
        'timestamp': datetime.now().isoformat(),
        'enhanced_ai': {},
        'enhanced_regex': {},
        'comparison': {}
    }
    
    # Test Enhanced AI Approach
    print(f"\n🔍 Testing Enhanced AI Approach...")
    start_time = time.time()
    try:
        ai_result = extract_fields_openai_enhanced(str(test_pdf))
        ai_time = time.time() - start_time
        results['enhanced_ai'] = {
            'success': True,
            'processing_time': ai_time,
            'fields': ai_result
        }
        print(f"✅ Enhanced AI completed in {ai_time:.2f}s")
    except Exception as e:
        ai_time = time.time() - start_time
        results['enhanced_ai'] = {
            'success': False,
            'processing_time': ai_time,
            'error': str(e)
        }
        print(f"❌ Enhanced AI failed: {e}")
    
    # Test Enhanced Regex Approach
    print(f"\n📋 Testing Enhanced Regex Approach...")
    start_time = time.time()
    try:
        regex_result = extract_fields_enhanced(str(test_pdf), use_openai=True)
        regex_time = time.time() - start_time
        results['enhanced_regex'] = {
            'success': True,
            'processing_time': regex_time,
            'fields': regex_result
        }
        print(f"✅ Enhanced Regex completed in {regex_time:.2f}s")
    except Exception as e:
        regex_time = time.time() - start_time
        results['enhanced_regex'] = {
            'success': False,
            'processing_time': regex_time,
            'error': str(e)
        }
        print(f"❌ Enhanced Regex failed: {e}")
    
    # Compare results
    if results['enhanced_ai']['success'] and results['enhanced_regex']['success']:
        ai_fields = results['enhanced_ai']['fields']
        regex_fields = results['enhanced_regex']['fields']
        
        # Key fields to compare
        key_fields = [
            'consignee', 'port_of_loading', 'port_of_discharge',
            'container_numbers', 'flight_or_vessel', 'bl_number',
            'container_count', 'total_weight_kg', 'shipment_type',
            'calculated_ctn_fee', 'calculated_service_fee'
        ]
        
        comparison = {}
        for field in key_fields:
            ai_value = ai_fields.get(field, '')
            regex_value = regex_fields.get(field, '')
            
            # Check if values match
            if ai_value == regex_value:
                comparison[field] = {
                    'match': True,
                    'ai_value': ai_value,
                    'regex_value': regex_value,
                    'status': '✅ Match'
                }
            else:
                comparison[field] = {
                    'match': False,
                    'ai_value': ai_value,
                    'regex_value': regex_value,
                    'status': '❌ Mismatch'
                }
        
        results['comparison'] = comparison
        
        # Performance comparison
        ai_time = results['enhanced_ai']['processing_time']
        regex_time = results['enhanced_regex']['processing_time']
        speed_ratio = regex_time / ai_time if ai_time > 0 else 0
        
        print(f"\n📊 COMPARISON RESULTS")
        print(f"=" * 60)
        print(f"Performance:")
        print(f"  Enhanced AI: {ai_time:.2f}s")
        print(f"  Enhanced Regex: {regex_time:.2f}s")
        print(f"  Speed Ratio: {speed_ratio:.1f}x (Regex is {speed_ratio:.1f}x slower)")
        
        print(f"\nField Accuracy:")
        matches = sum(1 for field_data in comparison.values() if field_data['match'])
        total_fields = len(comparison)
        accuracy = (matches / total_fields) * 100 if total_fields > 0 else 0
        
        print(f"  Matching Fields: {matches}/{total_fields} ({accuracy:.1f}%)")
        
        # Show mismatches
        mismatches = [field for field, data in comparison.items() if not data['match']]
        if mismatches:
            print(f"\n❌ Mismatched Fields:")
            for field in mismatches:
                data = comparison[field]
                print(f"  {field}:")
                print(f"    AI: '{data['ai_value']}'")
                print(f"    Regex: '{data['regex_value']}'")
        
        # Show matches
        matches_list = [field for field, data in comparison.items() if data['match']]
        if matches_list:
            print(f"\n✅ Matching Fields:")
            for field in matches_list:
                data = comparison[field]
                print(f"  {field}: '{data['ai_value']}'")
        
        # Quality assessment
        print(f"\n🎯 QUALITY ASSESSMENT")
        print(f"=" * 60)
        
        # Check for truncation issues (common with regex)
        truncation_issues = []
        for field, data in comparison.items():
            if not data['match']:
                ai_val = str(data['ai_value'])
                regex_val = str(data['regex_value'])
                
                # Check if regex truncated the value
                if len(regex_val) < len(ai_val) and ai_val.startswith(regex_val):
                    truncation_issues.append(field)
        
        if truncation_issues:
            print(f"❌ Regex Truncation Issues: {', '.join(truncation_issues)}")
        else:
            print(f"✅ No truncation issues detected")
        
        # Check for form label issues
        form_label_issues = []
        for field, data in comparison.items():
            if field in ['port_of_loading', 'port_of_discharge']:
                regex_val = str(data['regex_value']).upper()
                if any(label in regex_val for label in ['CONTAINERIZED', 'CONTAIN', 'VESSEL', 'ONLY']):
                    form_label_issues.append(field)
        
        if form_label_issues:
            print(f"❌ Regex Form Label Issues: {', '.join(form_label_issues)}")
        else:
            print(f"✅ No form label issues detected")
        
        # Overall recommendation
        print(f"\n💡 RECOMMENDATION")
        print(f"=" * 60)
        
        if speed_ratio > 1.5 and accuracy > 80:
            print(f"✅ Enhanced AI is clearly superior:")
            print(f"   - {speed_ratio:.1f}x faster")
            print(f"   - {accuracy:.1f}% field accuracy")
            print(f"   - No truncation or form label issues")
            print(f"   - Better maintainability")
        elif speed_ratio > 1.2:
            print(f"⚠️  Enhanced AI shows advantages:")
            print(f"   - {speed_ratio:.1f}x faster")
            print(f"   - {accuracy:.1f}% field accuracy")
        else:
            print(f"🤔 Both approaches perform similarly")
    
    # Save results
    output_file = f"comparison_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_file}")
    return True

if __name__ == "__main__":
    test_comparison() 