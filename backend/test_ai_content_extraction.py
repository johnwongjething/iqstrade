#!/usr/bin/env python3
"""
Test script for the AI-powered email content extraction function.
This tests the new AI-based approach for extracting only new content from email replies.
"""

import re
import logging
import os
import sys

# Add the current directory to Python path to import from email_ingestor_working
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the functions we need to test
try:
    from email_ingestor_working import openai_call_with_fallback
except ImportError as e:
    print(f"Error importing functions: {e}")
    print("Make sure you're running this from the backend directory")
    sys.exit(1)

def extract_new_content_from_reply_standalone(email_body):
    """
    Standalone version of the extract_new_content_from_reply function for testing.
    This replicates the logic from the main function.
    """
    if not email_body:
        return email_body
    
    # If the email is short (less than 200 characters), it's likely all new content
    if len(email_body) < 200:
        logger.info(f"[Email Content Extraction] Short email ({len(email_body)} chars), assuming all new content")
        return email_body
    
    try:
        # Use AI to extract only the new content
        messages = [
            {
                "role": "system",
                "content": """You are an email content extraction expert. Your task is to extract ONLY the new content from an email reply, removing all quoted/forwarded content.

IMPORTANT RULES:
1. Return ONLY the new content written by the sender
2. Remove ALL quoted content, forwarded content, and email headers
3. Do NOT include any lines starting with ">", "|", or similar quote indicators
4. Do NOT include "On [date] wrote:", "From:", "Sent:", "To:", "Subject:" lines
5. Do NOT include Chinese quote patterns like "於 [date] 寫道："
6. Do NOT include separator lines like "-----Original Message-----"
7. If the email appears to be entirely new (no quotes), return the full content
8. If you're unsure, err on the side of keeping more content rather than removing too much
9. Return ONLY the extracted text, no explanations or formatting

Examples:
Input: "Hi there,\n\nCan you help me?\n\nThanks!\n\nOn Mon, Jan 15, 2024 at 10:30 AM John wrote:\n> Hello,\n> I need help\n> Thanks"
Output: "Hi there,\n\nCan you help me?\n\nThanks!"

Input: "Hello,\n\nI have a question.\n\nBest regards,\nJohn\n\nLogistics Company <email> 於 2025年8月9日 週六 下午4:59寫道：\n> Original content here"
Output: "Hello,\n\nI have a question.\n\nBest regards,\nJohn"
"""
            },
            {
                "role": "user",
                "content": f"Extract only the new content from this email reply:\n\n{email_body}"
            }
        ]
        
        logger.info(f"[Email Content Extraction] Using AI to extract new content from {len(email_body)} character email")
        
        # Call OpenAI to extract new content
        extracted_content = openai_call_with_fallback(messages, temperature=0, max_retries=1)
        
        if extracted_content and extracted_content.strip():
            # Log the extraction results
            original_length = len(email_body)
            new_length = len(extracted_content)
            removed_length = original_length - new_length
            
            logger.info(f"[Email Content Extraction] AI extraction successful - Original: {original_length}, New: {new_length}, Removed: {removed_length} characters")
            logger.info(f"[Email Content Extraction] AI extracted content: '{extracted_content[:200]}...'")
            
            return extracted_content.strip()
        else:
            logger.warning(f"[Email Content Extraction] AI returned empty content, falling back to original")
            return email_body
            
    except Exception as e:
        logger.error(f"[Email Content Extraction] AI extraction failed: {e}, falling back to regex method")
        
        # Fallback to regex method if AI fails
        return extract_new_content_from_reply_regex_standalone(email_body)

def extract_new_content_from_reply_regex_standalone(email_body):
    """
    Standalone fallback regex-based method for extracting new content from email replies.
    This is used when AI extraction fails.
    """
    if not email_body:
        return email_body
    
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
    
    lines = email_body.split('\n')
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
                    logger.info(f"[Email Content Extraction] Regex truncating email at line {i} due to strong quote pattern: '{line_stripped[:50]}...'")
                    return '\n'.join(lines[:i]).strip()
                else:
                    # If not enough content before, it might be a false positive, or the email is very short.
                    # Log a warning and continue processing this line as potentially new content.
                    logger.warning(f"[Email Content Extraction] Potential false positive for quote start at line {i}. Not truncating yet: '{line_stripped[:50]}...'")
                    # If it's a single line like "From: someone@example.com" at the very beginning,
                    # it might be part of the new message if the user is just forwarding.
                    # For now, we'll let it pass if it doesn't meet the 2-line heuristic,
                    # and rely on the general quote character check below.
                    pass # Continue to the next pattern or append the line
        
        # If the line starts with a quote character, it's a strong indicator to stop.
        # This handles cases where the user replies with quoted text directly.
        if line_stripped.startswith('>') or line_stripped.startswith('|'):
            logger.info(f"[Email Content Extraction] Regex truncating email at line {i} due to '>' or '|' indicator: '{line_stripped[:50]}...'")
            return '\n'.join(lines[:i]).strip()
            
        new_content_lines.append(line)
    
    new_content = '\n'.join(new_content_lines).strip()
    
    # Log the extraction results
    original_length = len(email_body)
    new_length = len(new_content)
    removed_length = original_length - new_length
    
    logger.info(f"[Email Content Extraction] Regex extraction - Original: {original_length}, New: {new_length}, Removed: {removed_length} characters")
    logger.info(f"[Email Content Extraction] Regex extracted content: '{new_content[:200]}...'")
    
    return new_content

def test_ai_content_extraction():
    """Test the AI-powered content extraction with various email formats."""
    
    # Test case 1: Chinese quote pattern (the one that was failing)
    test_email_1 = """Hi there,

Can you give me ctn number on NYC233, NYC234 and NYC235?

Thanks!

Logistics Company <ray6330099@brevosend.com> 於 2025年8月9日 週六 下午4:59寫道：

> Hi there,
> 
> I need some information about my shipments.
> 
> Can you help me with the following:
> 1. Payment status for BL-123456
> 2. Container numbers for NYC233, NYC234, NYC235
> 3. Delivery schedule
> 
> Thanks,
> John

From: johnwongjething@gmail.com
Sent: Friday, August 9, 2025 4:30 PM
To: ray6330088@gmail.com
Subject: Shipment Inquiry

Original message content here..."""

    # Test case 2: Gmail-style quote
    test_email_2 = """Hello,

I have a question about my shipment.

Best regards,
John

On Mon, Jan 15, 2024 at 10:30 AM John Wong <johnwongjething@gmail.com> wrote:

> Hello,
> 
> I need information about my shipment.
> 
> Thanks,
> John"""

    # Test case 3: Short email (should not trigger AI)
    test_email_3 = """Hi,

Can you help me?

Thanks!"""

    # Test case 4: Email with multiple quote patterns
    test_email_4 = """Good morning,

I need to check the status of my containers.

Regards,
Customer

-----Original Message-----
From: customer@example.com
Sent: Monday, January 15, 2024 9:00 AM
To: support@company.com
Subject: Container Status

> Hello,
> 
> I have containers that need status updates.
> 
> Thanks"""

    test_cases = [
        ("Chinese Quote Pattern", test_email_1),
        ("Gmail Quote Pattern", test_email_2),
        ("Short Email", test_email_3),
        ("Multiple Quote Patterns", test_email_4)
    ]
    
    print("=" * 80)
    print("TESTING AI-POWERED EMAIL CONTENT EXTRACTION")
    print("=" * 80)
    
    for test_name, test_email in test_cases:
        print(f"\n{'='*20} {test_name} {'='*20}")
        print("Original email:")
        print("-" * 40)
        print(test_email)
        print("-" * 40)
        
        try:
            result = extract_new_content_from_reply_standalone(test_email)
            
            print("\nExtracted content:")
            print("-" * 40)
            print(result)
            print("-" * 40)
            
            # Basic validation
            original_length = len(test_email)
            result_length = len(result)
            
            print(f"\nResults:")
            print(f"Original length: {original_length} characters")
            print(f"Extracted length: {result_length} characters")
            print(f"Removed: {original_length - result_length} characters")
            
            # Check if extraction was reasonable
            if result_length < original_length * 0.3:
                print("⚠️  WARNING: Extracted content seems too short")
            elif result_length > original_length * 0.9:
                print("ℹ️  INFO: Most content preserved (may be a new email)")
            else:
                print("✅ SUCCESS: Content extraction looks reasonable")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)

def test_openai_call():
    """Test the OpenAI call function directly."""
    
    print("\n" + "=" * 80)
    print("TESTING OPENAI CALL FUNCTION")
    print("=" * 80)
    
    test_email = """Hi there,

Can you give me ctn number on NYC233, NYC234 and NYC235?

Thanks!

Logistics Company <ray6330099@brevosend.com> 於 2025年8月9日 週六 下午4:59寫道：

> Original content here"""

    messages = [
        {
            "role": "system",
            "content": """You are an email content extraction expert. Extract ONLY the new content from an email reply, removing all quoted/forwarded content.

IMPORTANT RULES:
1. Return ONLY the new content written by the sender
2. Remove ALL quoted content, forwarded content, and email headers
3. Do NOT include any lines starting with ">", "|", or similar quote indicators
4. Do NOT include "On [date] wrote:", "From:", "Sent:", "To:", "Subject:" lines
5. Do NOT include Chinese quote patterns like "於 [date] 寫道："
6. Do NOT include separator lines like "-----Original Message-----"
7. If the email appears to be entirely new (no quotes), return the full content
8. If you're unsure, err on the side of keeping more content rather than removing too much
9. Return ONLY the extracted text, no explanations or formatting

Examples:
Input: "Hi there,\n\nCan you help me?\n\nThanks!\n\nOn Mon, Jan 15, 2024 at 10:30 AM John wrote:\n> Hello,\n> I need help\n> Thanks"
Output: "Hi there,\n\nCan you help me?\n\nThanks!"

Input: "Hello,\n\nI have a question.\n\nBest regards,\nJohn\n\nLogistics Company <email> 於 2025年8月9日 週六 下午4:59寫道：\n> Original content here"
Output: "Hello,\n\nI have a question.\n\nBest regards,\nJohn"
"""
        },
        {
            "role": "user",
            "content": f"Extract only the new content from this email reply:\n\n{test_email}"
        }
    ]
    
    try:
        print("Testing OpenAI call...")
        result = openai_call_with_fallback(messages, temperature=0, max_retries=1)
        
        print("OpenAI Response:")
        print("-" * 40)
        print(result)
        print("-" * 40)
        
        if result and result.strip():
            print("✅ SUCCESS: OpenAI call worked")
        else:
            print("❌ FAILED: OpenAI returned empty response")
            
    except Exception as e:
        print(f"❌ ERROR: OpenAI call failed: {e}")

if __name__ == "__main__":
    # Test OpenAI call first
    test_openai_call()
    
    # Then test the full extraction function
    test_ai_content_extraction()
