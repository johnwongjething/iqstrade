#!/usr/bin/env python3
"""
Test script for the improved email content extraction function.
This tests the specific pattern that was failing: "Logistics Company <ray6330099@brevosend.com> 於 2025年8月9日 週六 下午4:59寫道："
"""

import re
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_new_content_from_reply(email_body):
    """
    Extract only the new content from email replies, removing quoted/forwarded content.
    This prevents the AI from processing old email content when generating replies.
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
                    logger.info(f"[Email Content Extraction] Truncating email at line {i} due to strong quote pattern: '{line_stripped[:50]}...'")
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
            logger.info(f"[Email Content Extraction] Truncating email at line {i} due to '>' or '|' indicator: '{line_stripped[:50]}...'")
            return '\n'.join(lines[:i]).strip()
            
        new_content_lines.append(line)
    
    new_content = '\n'.join(new_content_lines).strip()
    
    # Log the extraction results
    original_length = len(email_body)
    new_length = len(new_content)
    removed_length = original_length - new_length
    
    logger.info(f"[Email Content Extraction] Original length: {original_length}, New content length: {new_length}, Removed: {removed_length} characters")
    logger.info(f"[Email Content Extraction] New content: '{new_content[:200]}...'")
    
    return new_content

def test_chinese_quote_pattern():
    """Test the specific Chinese quote pattern that was failing."""
    
    # Test email with the exact pattern from the logs
    test_email = """Hi there,

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

Original message content here...
"""

    print("=" * 80)
    print("TESTING CHINESE QUOTE PATTERN")
    print("=" * 80)
    print("Original email:")
    print("-" * 40)
    print(test_email)
    print("-" * 40)
    
    result = extract_new_content_from_reply(test_email)
    
    print("\nExtracted new content:")
    print("-" * 40)
    print(result)
    print("-" * 40)
    
    # Check if the extraction worked correctly
    expected_content = """Hi there,

Can you give me ctn number on NYC233, NYC234 and NYC235?

Thanks!"""
    
    if result.strip() == expected_content.strip():
        print("\n✅ SUCCESS: Content extraction worked correctly!")
        print(f"Expected: {len(expected_content)} characters")
        print(f"Actual: {len(result)} characters")
    else:
        print("\n❌ FAILED: Content extraction did not work as expected")
        print("Expected:")
        print(repr(expected_content))
        print("Actual:")
        print(repr(result))

def test_gmail_quote_pattern():
    """Test Gmail-style quote patterns."""
    
    test_email = """Hello,

I have a question about my shipment.

Best regards,
John

On Mon, Jan 15, 2024 at 10:30 AM John Wong <johnwongjething@gmail.com> wrote:

> Hello,
> 
> I need information about my shipment.
> 
> Thanks,
> John
"""

    print("\n" + "=" * 80)
    print("TESTING GMAIL QUOTE PATTERN")
    print("=" * 80)
    print("Original email:")
    print("-" * 40)
    print(test_email)
    print("-" * 40)
    
    result = extract_new_content_from_reply(test_email)
    
    print("\nExtracted new content:")
    print("-" * 40)
    print(result)
    print("-" * 40)
    
    expected_content = """Hello,

I have a question about my shipment.

Best regards,
John"""
    
    if result.strip() == expected_content.strip():
        print("\n✅ SUCCESS: Gmail quote pattern extraction worked correctly!")
    else:
        print("\n❌ FAILED: Gmail quote pattern extraction failed")

def test_short_email():
    """Test with a very short email to ensure we don't truncate unnecessarily."""
    
    test_email = """From: john@example.com
Sent: Monday, January 15, 2024
To: ray6330088@gmail.com
Subject: Test

This is a short test email."""

    print("\n" + "=" * 80)
    print("TESTING SHORT EMAIL (should not truncate)")
    print("=" * 80)
    print("Original email:")
    print("-" * 40)
    print(test_email)
    print("-" * 40)
    
    result = extract_new_content_from_reply(test_email)
    
    print("\nExtracted new content:")
    print("-" * 40)
    print(result)
    print("-" * 40)
    
    # For short emails, we expect the content to remain mostly intact
    if len(result) > len(test_email) * 0.8:
        print("\n✅ SUCCESS: Short email was handled correctly (not over-truncated)")
    else:
        print("\n❌ FAILED: Short email was over-truncated")

if __name__ == "__main__":
    test_chinese_quote_pattern()
    test_gmail_quote_pattern()
    test_short_email()
    
    print("\n" + "=" * 80)
    print("TESTING COMPLETE")
    print("=" * 80)
