#!/usr/bin/env python3
"""
Hybrid Email Ingestor - Uses normal email_ingestor with safety measures
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_import_email_ingestor():
    """Safely import email_ingestor functions with timeout"""
    import threading
    import queue
    import time
    
    result_queue = queue.Queue()
    
    def import_worker():
        try:
            # Import the specific functions we need
            from email_ingestor import (
                process_inbox, 
                get_db_processing_status,
                acquire_db_processing_lock,
                release_db_processing_lock
            )
            result_queue.put(('success', {
                'process_inbox': process_inbox,
                'get_db_processing_status': get_db_processing_status,
                'acquire_db_processing_lock': acquire_db_processing_lock,
                'release_db_processing_lock': release_db_processing_lock
            }))
        except Exception as e:
            result_queue.put(('error', str(e)))
    
    thread = threading.Thread(target=import_worker)
    thread.daemon = True
    thread.start()
    
    try:
        result = result_queue.get(timeout=30)  # 30 second timeout
        return result
    except queue.Empty:
        return ('timeout', 'Import hung for 30 seconds')

# Try to import the normal email_ingestor functions
import_result, import_data = safe_import_email_ingestor()

if import_result == 'success':
    # Use the normal email_ingestor functions
    process_inbox = import_data['process_inbox']
    get_db_processing_status = import_data['get_db_processing_status']
    acquire_db_processing_lock = import_data['acquire_db_processing_lock']
    release_db_processing_lock = import_data['release_db_processing_lock']
    logger.info("✅ Using normal email_ingestor functions")
else:
    # Fallback to minimal version
    logger.warning(f"⚠️ Normal email_ingestor import failed: {import_data}")
    logger.info("🔄 Falling back to minimal email_ingestor")
    
    from email_ingestor_minimal import (
        process_inbox,
        get_db_processing_status,
        acquire_db_processing_lock,
        release_db_processing_lock
    )

# Export the functions
__all__ = [
    'process_inbox',
    'get_db_processing_status', 
    'acquire_db_processing_lock',
    'release_db_processing_lock'
] 