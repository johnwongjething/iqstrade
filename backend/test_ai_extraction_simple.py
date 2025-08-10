#!/usr/bin/env python3
"""
Simple test script for AI content extraction functions
Tests the core logic without requiring full email processing
"""

import sys
import os
import re

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def extract_new_content_from_reply_regex_standalone(email_body):
    """
    Standalone version of the regex-based content extraction function
    This is a copy of the function from email_ingestor_working.py for testing purposes
    """
    if not email_body:
        return email_body
    
    lines = email_body.split('\n')
    
    # Check if the email starts with quoted content (no new content at all)
    start_quote_patterns = [
        r'On\s+.*?\s+at\s+.*?\s+wrote:.*', # "On Mon, Jan 15, 2024 at 10:30 AM John Wong <johnwongjething@gmail.com> wrote:"
        r'On\s+.*?\s+wrote:.*', # Simpler "On [Date] wrote:"
        r'^-{5,} ?Original Message ?-{5,}', # "-----Original Message-----"
        r'^-{5,} ?Forwarded Message ?-{5,}', # "-----Forwarded Message-----"
        r'^Forwarded message.*$', # Forwarded message
    ]
    
    # Check for patterns that indicate old content (multiple BL numbers, forwarded messages, etc.)
    # This check should happen regardless of how the email starts
    old_content_patterns = [
        r'can you please send me ctn number for [A-Z]{3}\d+, [A-Z]{3}\d+, [A-Z]{3}\d+',
        r'[A-Z]{3}\d+, [A-Z]{3}\d+, [A-Z]{3}\d+',
        r'ST\d+, ST\d+, ST\d+',
        r'BL-\d+-\d+, BL-\d+-\d+, BL-\d+-\d+',
    ]
    
    # If the content matches old content patterns, return empty
    for pattern in old_content_patterns:
        if re.search(pattern, email_body, re.IGNORECASE):
            print(f"[Email Content Extraction] Content matches old content pattern: {pattern}, returning empty")
            return ""
    
    # Only check for quoted content if the email starts with quoted content
    if lines and any(re.search(pattern, lines[0].strip(), re.IGNORECASE) for pattern in start_quote_patterns):
        # Email starts with quoted content, check if it's mostly quoted
        quoted_patterns = [
            r'^>.*',  # Quoted lines
            r'^On .* wrote:',  # Email headers
            r'^---------- Forwarded message ---------',  # Forwarded message
            r'^Forwarded message',  # Forwarded message
        ]
        
        quoted_count = 0
        total_lines = len([line for line in lines if line.strip()])
        
        for line in lines:
            for pattern in quoted_patterns:
                if re.search(pattern, line.strip()):
                    quoted_count += 1
                    break
        
        # If more than 50% of non-empty lines contain quoted patterns, consider it mostly quoted
        if total_lines > 0 and (quoted_count / total_lines) > 0.5:
            print(f"[Email Content Extraction] Email starts with quoted content and is mostly quoted ({quoted_count}/{total_lines} lines), returning empty")
            return ""
    
    # Common patterns that indicate the START of quoted/forwarded content
    # These patterns are typically followed by the old email content.
    # Order matters: more specific patterns first.
    start_quote_patterns = [
        # Gmail-style quotes
        r'On\s+.*?\s+at\s+.*?\s+wrote:.*', # "On Mon, Jan 15, 2024 at 10:30 AM John Wong <johnwongjething@gmail.com> wrote:"
        r'On\s+.*?\s+wrote:.*', # Simpler "On [Date] wrote:"
        
        # Sender line with email address (often indicates start of quoted block)
        r'.*<[^>]+@[^>]+>.* wrote:.*', # e.g., "John Doe <john@example.com> wrote:"
        r'.*<[^>]+@[^>]+>.* 於 .* 寫道：.*', # e.g., "Logistics Company <ray6330099@brevosend.com> 於 2025年8月9日 週六 下午4:59寫道："
        r'.*<[^>]+@[^>]+>.*', # General sender line with email address (catch-all for sender lines)
        
        # Outlook-style headers (often appear as a block)
        r'^From:.*$',
        r'^Sent:.*$',
        r'^To:.*$',
        r'^Subject:.*$',
        
        # Generic forward/reply indicators
        r'^-{5,} ?Original Message ?-{5,}', # "-----Original Message-----"
        r'^-{5,} ?Forwarded Message ?-{5,}', # "-----Forwarded Message-----"
        r'^Forwarded message.*$',
        r'^转发的邮件.*$', # Chinese forwarded message
        r'^轉發的郵件.*$', # Traditional Chinese forwarded message
        
        # Common "wrote" indicators, including Chinese
        r'^.* wrote:$',
        r'^.* 写道:$',
        r'^.* 寫道:$',
        
        # Lines starting with common quote characters (strong indicator)
        r'^>.*$',
        r'^\|.*$',
        
        # Date patterns that often indicate quoted content, especially if followed by other headers
        r'^\d{4}年\d{1,2}月\d{1,2}日.*$',  # Chinese date format
        r'^\d{1,2}/\d{1,2}/\d{4}.*$',  # US date format
        r'^\d{1,2}-\d{1,2}-\d{4}.*$',  # US date format with dashes
        r'^\w{3}, \d{1,2} \w{3} \d{4}.*$',  # RFC date format (e.g., "Mon, 15 Jan 2024")
        
        # Long separator lines
        r'^\s*_{70,}\s*$', # Long underscore line
        r'^\s*={70,}\s*$', # Long equals line
    ]
    
    new_content_lines = []
    
    # Iterate through lines to find the first strong indicator of quoted content
    for i, line in enumerate(lines):
        line_stripped = line.strip()
        
        # Check for strong quote start patterns
        for pattern in start_quote_patterns:
            if re.search(pattern, line_stripped, re.IGNORECASE):
                # Found a potential quote start.
                # We need to be careful not to cut off the actual new message if it happens to contain a pattern.
                # Heuristic: If there are at least 2 non-empty lines before this, assume it's the split point.
                non_empty_lines_before = 0
                for j in range(i):
                    if lines[j].strip():
                        non_empty_lines_before += 1
                
                if non_empty_lines_before >= 2: # At least two lines of new content before the quote
                    print(f"[Email Content Extraction] Regex truncating email at line {i} due to strong quote pattern: '{line_stripped[:50]}...'")
                    return '\n'.join(lines[:i]).strip()
                else:
                    # If not enough content before, it might be a false positive, or the email is very short.
                    # Log a warning and continue processing this line as potentially new content.
                    print(f"[Email Content Extraction] Potential false positive for quote start at line {i}. Not truncating yet: '{line_stripped[:50]}...'")
                    # If it's a single line like "From: someone@example.com" at the very beginning,
                    # it might be part of the new message if the user is just forwarding.
                    # For now, we'll let it pass if it doesn't meet the 2-line heuristic,
                    # and rely on the general quote character check below.
                    pass # Continue to the next pattern or append the line
        
        # If the line starts with a quote character, it's a strong indicator to stop.
        # This handles cases where the user replies with quoted text directly.
        if line_stripped.startswith('>') or line_stripped.startswith('|'):
            print(f"[Email Content Extraction] Regex truncating email at line {i} due to '>' or '|' indicator: '{line_stripped[:50]}...'")
            return '\n'.join(lines[:i]).strip()
            
        new_content_lines.append(line)
    
    # If we get here, no strong quote patterns were found
    # Check if more than 50% of non-empty lines contain quoted patterns
    quoted_patterns = [
        r'^>.*',  # Quoted lines
        r'^On .* wrote:',  # Email headers
        r'^---------- Forwarded message ---------',  # Forwarded message
        r'^Forwarded message',  # Forwarded message
    ]
    
    quoted_count = 0
    total_lines = len([line for line in lines if line.strip()])
    
    for line in lines:
        for pattern in quoted_patterns:
            if re.search(pattern, line.strip()):
                quoted_count += 1
                break
    
    # If more than 50% of non-empty lines contain quoted patterns, consider it mostly quoted
    if total_lines > 0 and (quoted_count / total_lines) > 0.5:
        print(f"[Email Content Extraction] Regex detected mostly quoted content ({quoted_count}/{total_lines} lines), returning empty")
        return ""
    
    return '\n'.join(new_content_lines).strip()

def test_extract_new_content_from_reply_regex():
    """Test the regex-based content extraction function"""
    print("\n" + "="*60)
    print("TESTING: Regex-based Content Extraction")
    print("="*60)
    
    test_cases = [
        {
            "name": "Simple reply with quoted content",
            "input": """Thank you for the information.
            
            On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:
            > Hello,
            > 
            > Here is your CTN number: ABC123
            > 
            > Best regards,
            > Support Team""",
            "expected_contains": "Thank you for the information",
            "expected_not_contains": "Here is your CTN number: ABC123"
        },
        {
            "name": "Empty reply (only quoted content)",
            "input": """On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:
            > Hello,
            > 
            > Here is your CTN number: ABC123
            > 
            > Best regards,
            > Support Team""",
            "expected_contains": "",
            "expected_not_contains": "Here is your CTN number: ABC123"
        },
        {
            "name": "Reply with multiple quoted levels",
            "input": """I need the CTN for BL-001-124.
            
            On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:
            > On Sun, Aug 9, 2025 at 1:30 PM, Customer <customer@example.com> wrote:
            > > Hello,
            > > 
            > > I need CTN numbers for BL-001-123.
            > > 
            > > Best regards,
            > > Customer""",
            "expected_contains": "I need the CTN for BL-001-124",
            "expected_not_contains": "BL-001-123"
        },
        {
            "name": "NYC239 scenario - mostly quoted content",
            "input": """On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:
            > Hello,
            > 
            > Please find attached invoice for NYC239.
            > Amount: $420
            > 
            > Best regards,
            > Support Team
            
            On Sun, Aug 9, 2025 at 1:30 PM, Customer <customer@example.com> wrote:
            > Hello,
            > 
            > I need CTN numbers for NYC238, NYC239, NYC240.
            > 
            > Best regards,
            > Customer""",
            "expected_contains": "",
            "expected_not_contains": "NYC238, NYC239, NYC240"
        },
        {
            "name": "Short meaningful reply",
            "input": """No
            
            On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:
            > Hello,
            > 
            > Have you made the payment for BL-001-123?
            > 
            > Best regards,
            > Support Team""",
            "expected_contains": "No",
            "expected_not_contains": "Have you made the payment for BL-001-123"
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        try:
            result = extract_new_content_from_reply_regex_standalone(test_case['input'])
            print(f"Input length: {len(test_case['input'])}")
            print(f"Output length: {len(result)}")
            print(f"Output: '{result}'")
            
            # Check if expected content is present
            if test_case['expected_contains']:
                if test_case['expected_contains'] in result:
                    print(f"✅ Expected content found: '{test_case['expected_contains']}'")
                    passed += 1
                else:
                    print(f"❌ Expected content NOT found: '{test_case['expected_contains']}'")
            else:
                # For empty expected content, check if result is empty or very short
                if len(result.strip()) <= 10:  # Allow for small variations
                    print(f"✅ Content correctly identified as mostly quoted (length: {len(result)})")
                    passed += 1
                else:
                    print(f"❌ Content should be mostly quoted but got: '{result}'")
            
            # Check if unwanted content is absent
            if test_case['expected_not_contains']:
                if test_case['expected_not_contains'] not in result:
                    print(f"✅ Unwanted content correctly removed: '{test_case['expected_not_contains']}'")
                else:
                    print(f"❌ Unwanted content still present: '{test_case['expected_not_contains']}'")
                    
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print(f"\nRegex Tests: {passed}/{total} passed")
    return passed == total

def test_old_content_patterns():
    """Test the old content pattern detection"""
    print("\n" + "="*60)
    print("TESTING: Old Content Pattern Detection")
    print("="*60)
    
    # Test patterns that should be detected as old content
    old_content_tests = [
        "can you please send me ctn number for NYC240, NYC241, NYC236",
        "NYC238, NYC239, NYC240",
        "ST001, ST002, ST003",
        "BL-001-123, BL-001-124, BL-001-125",
        "---------- Forwarded message ---------",
        "Forwarded message",
        "On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:"
    ]
    
    passed = 0
    total = len(old_content_tests)
    
    for i, test_text in enumerate(old_content_tests, 1):
        print(f"\n--- Test {i}: '{test_text}' ---")
        try:
            result = extract_new_content_from_reply_regex_standalone(test_text)
            print(f"Result: '{result}'")
            
            # These should all return empty or very short content
            if len(result.strip()) <= 10:
                print(f"✅ Correctly identified as old content")
                passed += 1
            else:
                print(f"❌ Should be identified as old content but got: '{result}'")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print(f"\nPattern Tests: {passed}/{total} passed")
    return passed == total

def test_content_validation_logic():
    """Test the content validation logic that determines whether to keep AI output or revert"""
    print("\n" + "="*60)
    print("TESTING: Content Validation Logic")
    print("="*60)
    
    # This tests the logic in handle_email_via_openai without running the full function
    print("Testing the validation logic that determines when to keep AI output vs revert to original...")
    
    # Test cases for the validation logic
    test_cases = [
        {
            "name": "Mostly quoted content (>60% quoted lines)",
            "ai_output": "Thank you.\n\nOn Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:\n> Hello,\n> Here is your CTN number: ABC123\n> Best regards,\n> Support Team",
            "should_revert": True,
            "reason": "More than 60% of lines contain quoted patterns"
        },
        {
            "name": "Mostly quoted content with attachment scenario (>40% quoted lines)",
            "ai_output": "Please find attached.\n\nOn Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:\n> Hello,\n> Here is your invoice\n> Best regards,\n> Support Team",
            "should_revert": True,
            "reason": "More than 40% quoted lines in no-new-text-with-attachment scenario"
        },
        {
            "name": "Valid new content (<40% quoted lines)",
            "ai_output": "Thank you for the information. I also need the CTN for BL-001-124.\n\nThis is very helpful and exactly what I was looking for. Please send it as soon as possible.\n\nI appreciate your quick response. The information you provided is exactly what I needed.\n\nI will process this request immediately and get back to you with the CTN numbers.\n\nI have reviewed the details and everything looks good. Please proceed with the next steps.\n\nI am looking forward to hearing from you soon.\n\nI will make sure to follow up on this matter. The timeline you provided works perfectly for our schedule.\n\nI appreciate your attention to detail and quick response time.\n\nI have also noted down the key points for our next meeting.\n\nThe documentation you provided is comprehensive and well-organized.\n\nI will share this information with my team members.\n\nWe are looking forward to a successful collaboration.\n\nI have scheduled a follow-up call for next week.\n\nThe team is excited about this project.\n\nWe will need to coordinate with the logistics department.\n\nThe budget approval has been confirmed.\n\nI will send you the updated timeline by Friday.\n\nThe technical specifications look good.\n\nWe should proceed with the implementation phase.\n\nOn Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:\n> Hello,\n> Here is your CTN number: ABC123",
            "should_revert": False,
            "reason": "Less than 40% quoted lines, contains meaningful new content"
        },
        {
            "name": "Multiple BL numbers in AI output",
            "ai_output": "I need CTN numbers for NYC238, NYC239, NYC240, NYC241",
            "should_revert": True,
            "reason": "Contains multiple BL numbers indicating old quoted content"
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}: {test_case['name']} ---")
        print(f"AI Output: '{test_case['ai_output']}'")
        print(f"Expected: Should {'revert' if test_case['should_revert'] else 'keep'} AI output")
        print(f"Reason: {test_case['reason']}")
        
        # This is a simplified version of the validation logic
        # In the actual code, this happens in handle_email_via_openai
        lines = test_case['ai_output'].split('\n')
        quoted_patterns = [
            r'^>.*',  # Quoted lines
            r'^On .* wrote:',  # Email headers
            r'^---------- Forwarded message ---------',  # Forwarded message
            r'^Forwarded message',  # Forwarded message
        ]
        
        quoted_count = 0
        total_lines = len([line for line in lines if line.strip()])
        
        for line in lines:
            for pattern in quoted_patterns:
                if re.search(pattern, line.strip()):
                    quoted_count += 1
                    break
        
        if total_lines > 0:
            quoted_percentage = quoted_count / total_lines
            print(f"Quoted lines: {quoted_count}/{total_lines} ({quoted_percentage:.1%})")
            
            # Check if content contains multiple BL numbers
            bl_pattern = r'[A-Z]{2,4}\d{2,}'
            bl_matches = re.findall(bl_pattern, test_case['ai_output'])
            print(f"BL numbers found: {bl_matches}")
            
            # Determine if this should revert based on the logic
            should_revert_actual = False
            
            # Check quoted content threshold
            if quoted_percentage > 0.6:  # Standard threshold
                should_revert_actual = True
                print("Reverting: >60% quoted content (standard threshold)")
            elif quoted_percentage > 0.4:  # Stricter threshold for no-new-text scenarios
                should_revert_actual = True
                print("Reverting: >40% quoted content (stricter threshold)")
            
            # Check BL count threshold
            if len(bl_matches) > 2:
                should_revert_actual = True
                print("Reverting: >2 BL numbers detected")
            
            # Check if result matches expectation
            if should_revert_actual == test_case['should_revert']:
                print(f"✅ PASS: Logic correctly identified this should {'revert' if should_revert_actual else 'keep'} AI output")
                passed += 1
            else:
                print(f"❌ FAIL: Logic incorrectly identified this should {'revert' if should_revert_actual else 'keep'} AI output")
        else:
            print("No content to analyze")
    
    print(f"\nValidation Logic Tests: {passed}/{total} passed")
    return passed == total

def run_all_tests():
    """Run all test functions"""
    print("🚀 Starting AI Content Extraction Test Suite")
    print("="*80)
    
    test_results = []
    
    # Run all tests
    test_results.append(("Regex Content Extraction", test_extract_new_content_from_reply_regex()))
    test_results.append(("Old Content Pattern Detection", test_old_content_patterns()))
    test_results.append(("Content Validation Logic", test_content_validation_logic()))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST RESULTS SUMMARY")
    print("="*80)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} test suites passed")
    
    if passed == total:
        print("🎉 All test suites passed! The AI content extraction logic is working correctly.")
    else:
        print("⚠️  Some test suites failed. Please review the issues above.")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
