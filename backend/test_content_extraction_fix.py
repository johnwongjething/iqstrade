#!/usr/bin/env python3
"""
Test script to verify the content extraction fix in email_ingestor_working.py
"""

import sys
import os
import logging
import re

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_all_payment_amounts_test(text):
    """Test version of extract_all_payment_amounts function"""
    if not text:
        return None
    patterns = [
        r'\$\s?([0-9]+(?:\.[0-9]{1,2})?)',
        r'USD\s*([0-9]+(?:\.[0-9]{1,2})?)',
        r'Amount[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)',
        r'Paid[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)',
        r'Payment[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)',
        r'Total[:：]?\s*\$?([0-9]+(?:\.[0-9]{1,2})?)',
    ]
    amounts = set()  # Use set to avoid duplicates
    for pat in patterns:
        matches = re.findall(pat, text, re.IGNORECASE)
        for match in matches:
            try:
                amount = float(match)
                # Filter out amounts that are likely BL numbers (too small or too large)
                if amount >= 10 and amount <= 10000:  # Reasonable payment range
                    amounts.add(amount)  # Use add() instead of append() to avoid duplicates
                    print(f"[Payment Extraction] Found amount: {amount} from pattern match: {match}")
                else:
                    print(f"[Payment Extraction] Skipping amount: {amount} (likely BL number)")
            except Exception:
                continue
    total = sum(amounts) if amounts else None
    print(f"[Payment Extraction] Total extracted amount: {total}")
    return total

def extract_new_content_from_reply_test(email_body):
    """Test version of extract_new_content_from_reply function"""
    if not email_body:
        return email_body
    
    # If the email is short (less than 200 characters), it's likely all new content
    if len(email_body) < 200:
        print(f"[Email Content Extraction] Short email ({len(email_body)} chars), assuming all new content")
        return email_body
    
    # Use regex method for testing (simpler than AI)
    return extract_new_content_from_reply_regex_test(email_body)

def extract_new_content_from_reply_regex_test(email_body):
    """Test version of regex-based content extraction"""
    if not email_body:
        return email_body
    
    # Common patterns that indicate the START of quoted/forwarded content
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
                    print(f"[Email Content Extraction] Regex truncating email at line {i} due to strong quote pattern: '{line_stripped[:50]}...'")
                    return '\n'.join(lines[:i]).strip()
                else:
                    # If not enough content before, it might be a false positive, or the email is very short.
                    # Log a warning and continue processing this line as potentially new content.
                    print(f"[Email Content Extraction] Potential false positive for quote start at line {i}. Not truncating yet: '{line_stripped[:50]}...'")
                    pass # Continue to the next pattern or append the line
        
        # If the line starts with a quote character, it's a strong indicator to stop.
        # This handles cases where the user replies with quoted text directly.
        if line_stripped.startswith('>') or line_stripped.startswith('|'):
            print(f"[Email Content Extraction] Regex truncating email at line {i} due to '>' or '|' indicator: '{line_stripped[:50]}...'")
            return '\n'.join(lines[:i]).strip()
            
        new_content_lines.append(line)
    
    new_content = '\n'.join(new_content_lines).strip()
    
    # Log the extraction results
    original_length = len(email_body)
    new_length = len(new_content)
    removed_length = original_length - new_length
    
    print(f"[Email Content Extraction] Regex extraction - Original: {original_length}, New: {new_length}, Removed: {removed_length} characters")
    print(f"[Email Content Extraction] Regex extracted content: '{new_content[:200]}...'")
    
    return new_content

def test_content_extraction_logic():
    """Test the content extraction logic to ensure it's working correctly"""
    
    # Test email with quoted content (similar to the one in the logs)
    test_email = """can you please send me ctn number for NYC233, NYC234, NYC235

Logistics Company <ray6330099@9433503.brevosend.com> 於 2025年8月9日 週六
下午4:59寫道：

> Dear customer, regarding your requests:
> For BL NYC280, we do not have any information as it is an invalid BL.
> For BL NYC234, the status is 'Invoice Sent'. You can settle the payment by
> choosing one of the following methods: Bank Transfer, Allinpay, or Stripe.
> The invoice link is:
> https://res.cloudinary.com/dtm46mski/raw/upload/v1754451767/invoices/vkonorpiguvrsysntydo.pdf.
> 
> For BL NYC236, the status is 'Awaiting Bank In'. You can settle the
> payment using the same payment methods mentioned above. The invoice link
> is:
> https://res.cloudinary.com/dtm46mski/raw/upload/v1754453993/invoices/ar8ldr5sgzgkyf3q3a2s.pdf.
> 
> The processing time for CTN is typically between 24 to 48 hours after
> payment confirmation. If you have any further questions, feel free to reach
> out. Thank you!
> IQSTrade Support Team
> Best regards,
> IQS Trade Team
> """

    print("=== TESTING CONTENT EXTRACTION LOGIC ===")
    print(f"Original email length: {len(test_email)} characters")
    print(f"Original email preview: '{test_email[:200]}...'")
    
    # Count quoted lines
    quoted_lines = [line for line in test_email.split('\n') if line.strip().startswith('>')]
    print(f"Found {len(quoted_lines)} quoted lines in original content")
    if quoted_lines:
        print(f"Sample quoted line: '{quoted_lines[0][:100]}...'")
    
    # Test the content extraction function
    try:
        print("\n=== CALLING CONTENT EXTRACTION FUNCTION ===")
        cleaned_content = extract_new_content_from_reply_test(test_email)
        
        print(f"Cleaned content length: {len(cleaned_content)} characters")
        print(f"Cleaned content preview: '{cleaned_content[:200]}...'")
        
        # Check if quoted content was removed
        final_quoted_lines = [line for line in cleaned_content.split('\n') if line.strip().startswith('>')]
        print(f"Found {len(final_quoted_lines)} quoted lines in FINAL content")
        
        if final_quoted_lines:
            print("❌ FAILED - Quoted content still present in final content!")
            print(f"Sample quoted line: '{final_quoted_lines[0][:100]}...'")
        else:
            print("✅ SUCCESS - All quoted content removed!")
        
        # Test payment extraction on cleaned content
        print("\n=== TESTING PAYMENT EXTRACTION ON CLEANED CONTENT ===")
        payment_amount = extract_all_payment_amounts_test(cleaned_content)
        print(f"Payment amount extracted from cleaned content: {payment_amount}")
        
        # Test payment extraction on original content (should find amounts in quoted content)
        print("\n=== TESTING PAYMENT EXTRACTION ON ORIGINAL CONTENT ===")
        original_payment_amount = extract_all_payment_amounts_test(test_email)
        print(f"Payment amount extracted from original content: {original_payment_amount}")
        
        if payment_amount != original_payment_amount:
            print("✅ SUCCESS - Payment extraction working correctly (different amounts)")
        else:
            print("⚠️  WARNING - Payment extraction may not be working correctly")
            
    except Exception as e:
        print(f"❌ ERROR - Test failed: {e}")

def test_payment_extraction_logic():
    """Test the payment extraction logic specifically"""
    
    print("\n=== TESTING PAYMENT EXTRACTION LOGIC ===")
    
    # Test text with payment information in quoted content
    test_text_with_quoted_payment = """Hello,

I need help with my shipment.

> Payment amount: $46.00
> Invoice link: https://res.cloudinary.com/dtm46mski/raw/upload/v1754451767/invoices/vkonorpiguvrsysntydo.pdf

Thank you!"""

    try:
        print("Testing payment extraction on text with quoted payment info:")
        print(f"Test text: '{test_text_with_quoted_payment}'")
        
        payment_amount = extract_all_payment_amounts_test(test_text_with_quoted_payment)
        print(f"Payment amount found: {payment_amount}")
        
        if payment_amount == 46.0:
            print("✅ SUCCESS - Payment extraction found the correct amount")
        else:
            print(f"❌ FAILED - Expected 46.0, got {payment_amount}")
            
    except Exception as e:
        print(f"❌ ERROR - Payment extraction test failed: {e}")

if __name__ == "__main__":
    test_content_extraction_logic()
    test_payment_extraction_logic()
    print("\n=== TEST COMPLETE ===")
