# Email Ingestion Test Suite

This directory contains test scripts to verify that the email ingestion system works correctly across all scenarios.

## Test Scripts

### 1. `test_email_scenarios.py` - Full Integration Tests
This script tests the complete email processing pipeline with mocked dependencies. It covers all 8 scenarios:

- **Scenario 1**: New email from customer - plain text enquiry
- **Scenario 2**: New email from customer - text based bank transfer  
- **Scenario 3**: New email from customer - PDF based bank transfer
- **Scenario 4**: Customer reply from our last email - plain text enquiry
- **Scenario 5**: Customer reply from our last email - text based bank transfer
- **Scenario 6**: Customer reply from our last email - PDF based bank transfer
- **Scenario 7**: No text with attachment (NYC239 scenario)
- **Scenario 8**: Short meaningful reply (e.g., "No")

**Usage:**
```bash
python test_email_scenarios.py
```

**Requirements:**
- Full backend environment setup
- All dependencies installed
- Database connection available
- OpenAI API access (mocked)

### 2. `test_ai_extraction_simple.py` - Core Logic Tests
This script tests the AI content extraction logic directly without requiring the full email processing pipeline. It focuses on:

- Regex-based content extraction
- Old content pattern detection
- Content validation logic

**Usage:**
```bash
python test_ai_extraction_simple.py
```

**Requirements:**
- Basic Python environment
- Backend directory accessible

## What the Tests Verify

### ✅ AI Content Extraction
- Correctly removes quoted/forwarded content from email replies
- Preserves meaningful new content from customers
- Returns empty string when no new content exists
- Handles multiple levels of quoted content

### ✅ Content Validation Logic
- Keeps AI output when it contains meaningful new content
- Reverts to original when AI output is mostly quoted (>60% quoted lines)
- Applies stricter validation (40% threshold) for "no new text with attachment" scenarios
- Detects and reverts when multiple BL numbers indicate old quoted content

### ✅ BL Number Processing
- Extracts BL numbers from new content only
- Does not process BL numbers from quoted/old content
- Handles PDF attachments correctly
- Prevents duplicate payment triggers from old content

### ✅ Payment Processing
- Extracts payment amounts from new content only
- Processes PDF-based payments correctly
- Maintains separation between old and new payment information

## Key Test Cases

### NYC239 Scenario (Critical)
This tests the specific issue where an email with no new text but an attachment was incorrectly processing old quoted BL numbers:

**Input:**
```
On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:
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
> Customer
```

**Expected Output:**
- AI should return empty string (no new content)
- Only NYC239 should be processed (from PDF attachment)
- NYC238 and NYC240 should NOT be processed (old quoted content)

### Short Meaningful Replies
Tests that short but meaningful content like "No" is preserved:

**Input:**
```
No

On Mon, Aug 10, 2025 at 2:30 PM, Support <support@company.com> wrote:
> Hello,
> 
> Have you made the payment for BL-001-123?
> 
> Best regards,
> Support Team
```

**Expected Output:**
- AI should return "No"
- Content should be processed normally
- Old quoted content should be ignored

## Running Tests

### Prerequisites
1. Ensure you're in the project root directory
2. Backend dependencies are installed
3. Environment variables are set (if needed)

### Quick Test (Recommended)
```bash
python test_ai_extraction_simple.py
```

### Full Integration Test
```bash
python test_email_scenarios.py
```

### Individual Test Functions
You can also run individual test functions by modifying the scripts:

```python
# In test_ai_extraction_simple.py
if __name__ == "__main__":
    # Test only regex extraction
    test_extract_new_content_from_reply_regex()
    
    # Test only pattern detection
    test_old_content_patterns()
    
    # Test only validation logic
    test_content_validation_logic()
```

## Expected Results

### All Tests Should Pass
- ✅ Regex Content Extraction: 5/5 test cases
- ✅ Old Content Pattern Detection: 7/7 test cases  
- ✅ Content Validation Logic: 4/4 test cases

### If Tests Fail
1. Check the error messages for specific failures
2. Verify the AI content extraction logic in `email_ingestor_working.py`
3. Check that the `no_new_text_scenario` flag is working correctly
4. Ensure the quoted content thresholds (40% and 60%) are appropriate
5. Verify that old content patterns are correctly identified

## Troubleshooting

### Import Errors
If you get import errors:
```bash
# Make sure you're in the project root
cd /path/to/iqstrade

# Check that backend directory exists
ls backend/

# Verify Python path
python -c "import sys; print(sys.path)"
```

### Database Connection Issues
The full integration tests may require database access. If you get database errors:
1. Use the simple test script instead
2. Mock the database functions
3. Set up a test database

### OpenAI API Issues
The tests mock OpenAI calls, but if you want to test with real API:
1. Set your OpenAI API key
2. Remove the mocking patches
3. Be aware of API rate limits and costs

## Code Coverage

These tests cover the critical paths in the email ingestion system:

- `extract_new_content_from_reply()` - AI-powered content extraction
- `extract_new_content_from_reply_regex()` - Regex fallback extraction
- Content validation logic in `handle_email_via_openai()`
- BL number extraction and filtering
- Payment amount processing
- Request type classification

## Maintenance

When modifying the email ingestion logic:
1. Run the tests to ensure existing functionality works
2. Add new test cases for new scenarios
3. Update test expectations if behavior changes
4. Keep the test data realistic and representative

## Summary

This test suite ensures that:
- ✅ Old quoted content is properly filtered out
- ✅ New customer content is preserved and processed
- ✅ PDF attachments are handled correctly
- ✅ BL numbers from old content don't trigger duplicate processing
- ✅ The system works correctly across all email scenarios
- ✅ The NYC239 issue and similar problems are prevented
