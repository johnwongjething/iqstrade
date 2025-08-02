#!/usr/bin/env python3
"""
Test to compare original AI-based approach vs enhanced regex approach
"""

import sys
import os
import time
from pathlib import Path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ocr_processor import extract_fields_openai
from enhanced_ocr_processor import extract_fields_enhanced
import json

def test_approaches():
    """Compare original AI-based vs enhanced regex approaches"""
    
    print("🧪 COMPARING ORIGINAL AI vs ENHANCED REGEX APPROACHES")
    print("=" * 70)
    print("Original: AI-powered (OpenAI Vision + GPT-4)")
    print("Enhanced: Regex patterns + fallback logic")
    print()
    
    # Test cases with different BOL formats
    test_cases = [
        {
            "name": "Standard BOL with form labels",
            "description": "Tests port extraction with form labels like 'a. CONTAINERIZED'"
        },
        {
            "name": "MAERSK BOL Format", 
            "description": "Tests different shipping line format"
        },
        {
            "name": "OOCL BOL Format",
            "description": "Tests another shipping line format"
        }
    ]
    
    print("📋 Test Cases:")
    for i, case in enumerate(test_cases, 1):
        print(f"  {i}. {case['name']}: {case['description']}")
    
    print(f"\n🎯 Key Differences:")
    print(f"  Original (AI):")
    print(f"    ✅ Uses OpenAI GPT-4 Vision for document understanding")
    print(f"    ✅ AI can see field locations and context")
    print(f"    ✅ Handles new BOL formats automatically")
    print(f"    ✅ Intelligent extraction based on document structure")
    print(f"    ✅ Fallback: Text → Vision → Error handling")
    
    print(f"\n  Enhanced (Regex):")
    print(f"    ❌ Uses multiple regex patterns")
    print(f"    ❌ Patterns scattered across code")
    print(f"    ❌ Breaks with new BOL formats")
    print(f"    ❌ Hard to maintain and debug")
    print(f"    ❌ No understanding of document structure")
    
    print(f"\n📊 Performance Comparison:")
    print(f"  Original AI:")
    print(f"    - Processing: AI model inference")
    print(f"    - Accuracy: High (AI understands context)")
    print(f"    - Scalability: Excellent (handles new formats)")
    print(f"    - Maintenance: Low (AI adapts automatically)")
    
    print(f"\n  Enhanced Regex:")
    print(f"    - Processing: Multiple regex evaluations")
    print(f"    - Accuracy: Medium (depends on pattern quality)")
    print(f"    - Scalability: Poor (needs new patterns for each format)")
    print(f"    - Maintenance: High (constant pattern updates)")
    
    print(f"\n🔍 Why Your Original Approach Was Better:")
    print(f"  1. **AI Intelligence**: GPT-4 can understand document structure")
    print(f"  2. **Visual Context**: Vision API can 'see' where fields are")
    print(f"  3. **Adaptability**: Handles new BOL formats without code changes")
    print(f"  4. **Robustness**: Multiple fallback mechanisms")
    print(f"  5. **Professional**: This is how enterprise systems work")
    
    print(f"\n💡 Recommendation:")
    print(f"  ✅ Keep using your original ocr_processor.py")
    print(f"  ✅ It's more sophisticated than regex patterns")
    print(f"  ✅ Only use enhanced_ocr_processor.py for specific edge cases")
    print(f"  ✅ Consider the enhanced processor as a 'fallback' for AI failures")
    
    print(f"\n🛠️ Suggested Architecture:")
    print(f"  1. Primary: ocr_processor.py (AI-based)")
    print(f"  2. Fallback: enhanced_ocr_processor.py (regex-based)")
    print(f"  3. Hybrid: Use AI first, fallback to regex if AI fails")
    
    return {
        "recommendation": "Use original AI-based approach",
        "reason": "More intelligent and scalable than regex patterns",
        "architecture": "AI primary, regex fallback"
    }

def test_with_real_pdfs():
    """Test with real PDFs if API key is available"""
    print(f"\n🧪 Testing with Real PDFs")
    print("=" * 40)
    
    # Check if we have API key
    import os
    from dotenv import load_dotenv
    
    # Try .env.local first, then .env
    load_dotenv('.env.local')
    load_dotenv('.env')
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OpenAI API key found")
        print("   To test with real PDFs, set OPENAI_API_KEY in .env file")
        return
    
    print("✅ OpenAI API key found")
    print("📁 Looking for test PDFs...")
    
    test_folder = Path("new folder (2)")
    if not test_folder.exists():
        print(f"❌ Test folder not found: {test_folder}")
        return
    
    pdf_files = list(test_folder.glob("*.pdf"))
    if not pdf_files:
        print(f"❌ No PDF files found in {test_folder}")
        return
    
    print(f"📄 Found {len(pdf_files)} PDF files")
    print("⚠️  Note: Testing with real PDFs requires API calls (costs money)")
    
    # Test first PDF only to avoid high costs
    test_pdf = pdf_files[0]
    print(f"\n🔍 Testing with: {test_pdf.name}")
    
    try:
        print("📋 Testing Original AI Approach...")
        start_time = time.time()
        original_result = extract_fields_openai(str(test_pdf))
        original_time = time.time() - start_time
        
        print(f"✅ Original completed in {original_time:.2f}s")
        print(f"  Port of Loading: '{original_result.get('port_of_loading', '')}'")
        print(f"  Port of Discharge: '{original_result.get('port_of_discharge', '')}'")
        print(f"  Consignee: '{original_result.get('consignee', '')}'")
        
        print(f"\n📦 Testing Enhanced Regex Approach...")
        start_time = time.time()
        enhanced_result = extract_fields_enhanced(str(test_pdf))
        enhanced_time = time.time() - start_time
        
        print(f"✅ Enhanced completed in {enhanced_time:.2f}s")
        print(f"  Port of Loading: '{enhanced_result.get('port_of_loading', '')}'")
        print(f"  Port of Discharge: '{enhanced_result.get('port_of_discharge', '')}'")
        print(f"  Consignee: '{enhanced_result.get('consignee', '')}'")
        
        print(f"\n📊 Comparison:")
        print(f"  Original AI Time: {original_time:.2f}s")
        print(f"  Enhanced Regex Time: {enhanced_time:.2f}s")
        print(f"  Speed Difference: {enhanced_time/original_time:.1f}x {'slower' if enhanced_time > original_time else 'faster'}")
        
        # Check for form label issues
        form_labels = ['CONTAINERIZED', 'CONTAIN', 'VESSEL', 'ONLY']
        original_has_form_label = any(label in original_result.get('port_of_discharge', '').upper() for label in form_labels)
        enhanced_has_form_label = any(label in enhanced_result.get('port_of_discharge', '').upper() for label in form_labels)
        
        print(f"\n🚨 Form Label Issues:")
        print(f"  Original AI has form label: {original_has_form_label}")
        print(f"  Enhanced Regex has form label: {enhanced_has_form_label}")
        
        if original_has_form_label and not enhanced_has_form_label:
            print("  ✅ Enhanced approach fixed form label issue")
        elif not original_has_form_label and enhanced_has_form_label:
            print("  ❌ Enhanced approach introduced form label issue")
        elif original_has_form_label and enhanced_has_form_label:
            print("  ⚠️  Both approaches have form label issues")
        else:
            print("  ✅ Both approaches correctly handled form labels")
            
    except Exception as e:
        print(f"❌ Error during testing: {str(e)}")

if __name__ == "__main__":
    # Run theoretical comparison
    result = test_approaches()
    
    # Test with real PDFs
    test_with_real_pdfs() 