#!/usr/bin/env python3
"""
Step-by-step test of email_ingestor imports to identify hanging issue
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_imports_step_by_step():
    """Test imports step by step to identify the hanging issue"""
    try:
        print("Testing imports step by step...")
        
        # Step 1: Basic imports
        print("1. Testing basic imports...")
        import os
        import imaplib
        import email
        from email.header import decode_header
        import logging
        print("✅ Basic imports successful")
        
        # Step 2: OCR processor
        print("2. Testing OCR processor...")
        from ocr_processor import process_pdf
        print("✅ OCR processor import successful")
        
        # Step 3: Environment and OpenAI
        print("3. Testing environment and OpenAI...")
        from dotenv import load_dotenv
        import openai
        print("✅ Environment and OpenAI import successful")
        
        # Step 4: Config
        print("4. Testing config...")
        from config import CloudinaryConfig
        print("✅ Config import successful")
        
        # Step 5: Database utils
        print("5. Testing database utils...")
        from db_utils import get_db_conn
        print("✅ Database utils import successful")
        
        # Step 6: Timezone utils
        print("6. Testing timezone utils...")
        from utils.timezone_utils import get_hk_now, get_hk_now_iso, get_hk_timestamp
        print("✅ Timezone utils import successful")
        
        # Step 7: Other utils
        print("7. Testing other utils...")
        from utils.unified_response_handler import get_response_handler
        from utils.confidence_scorer import confidence_scorer
        print("✅ Other utils import successful")
        
        # Step 8: Invoice utils
        print("8. Testing invoice utils...")
        from invoice_utils import find_invoice_info, find_ctn_info, generate_pdf_from_text
        print("✅ Invoice utils import successful")
        
        # Step 9: Cloudinary utils
        print("9. Testing cloudinary utils...")
        from cloudinary_utils import upload_filepath_to_cloudinary
        print("✅ Cloudinary utils import successful")
        
        print("✅ All individual imports successful!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports_step_by_step()
    sys.exit(0 if success else 1) 