#!/usr/bin/env python3
"""
Debug script to identify which import in email_ingestor is causing the hang
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_import_with_timeout(import_name, timeout=10):
    """Test import with timeout to identify hanging imports"""
    import threading
    import queue
    
    result_queue = queue.Queue()
    
    def import_worker():
        try:
            start_time = time.time()
            module = __import__(import_name)
            end_time = time.time()
            result_queue.put(('success', end_time - start_time))
        except Exception as e:
            result_queue.put(('error', str(e)))
    
    thread = threading.Thread(target=import_worker)
    thread.daemon = True
    thread.start()
    
    try:
        result = result_queue.get(timeout=timeout)
        return result
    except queue.Empty:
        return ('timeout', f'Import hung for {timeout} seconds')

def debug_email_ingestor_imports():
    """Debug which imports in email_ingestor are causing issues"""
    print("🔍 Debugging email_ingestor imports...")
    
    # Test individual imports that email_ingestor uses
    imports_to_test = [
        'os',
        'imaplib', 
        'email',
        'logging',
        'json',
        'tempfile',
        'datetime',
        'db_utils',
        'config',
        'utils.timezone_utils',
        'utils.unified_response_handler',
        'utils.confidence_scorer',
        'ocr_processor',
        'invoice_utils',
        'cloudinary_utils',
        'openai'
    ]
    
    for import_name in imports_to_test:
        print(f"Testing import: {import_name}")
        result, details = test_import_with_timeout(import_name)
        if result == 'success':
            print(f"  ✅ {import_name}: {details:.2f}s")
        elif result == 'timeout':
            print(f"  ❌ {import_name}: {details}")
            return import_name
        else:
            print(f"  ⚠️ {import_name}: {details}")
    
    print("Testing full email_ingestor import...")
    result, details = test_import_with_timeout('email_ingestor', timeout=30)
    if result == 'success':
        print(f"  ✅ email_ingestor: {details:.2f}s")
        return None
    elif result == 'timeout':
        print(f"  ❌ email_ingestor: {details}")
        return 'email_ingestor'
    else:
        print(f"  ⚠️ email_ingestor: {details}")
        return 'email_ingestor'

if __name__ == "__main__":
    hanging_import = debug_email_ingestor_imports()
    if hanging_import:
        print(f"\n🎯 Identified hanging import: {hanging_import}")
    else:
        print("\n✅ All imports working correctly") 