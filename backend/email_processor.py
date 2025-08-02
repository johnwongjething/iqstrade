"""
Background Email Processor for IQSTrade
- Handles email ingestion in background threads
- Prevents blocking the main application
- Provides status tracking for ingestion process
"""

import threading
import time
import logging
from queue import Queue
from datetime import datetime
import traceback
from email_ingestor_working import process_inbox
from config import get_db_conn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailProcessor:
    def __init__(self):
        self.processing = False
        self.email_queue = Queue()
        self.worker_thread = None
        self.last_processing_time = None
        self.processing_status = {
            'is_running': False,
            'last_start': None,
            'last_completion': None,
            'emails_processed': 0,
            'errors': [],
            'current_batch': 0
        }
        # Add control flags
        self.paused = False
        self.manual_processing_requested = False
    
    def start_processing(self):
        """Start the background email processing"""
        if not self.processing:
            self.processing = True
            self.paused = False
            self.worker_thread = threading.Thread(target=self._process_emails, daemon=True)
            self.worker_thread.start()
            logger.info("✅ Background email processor started")
        else:
            logger.info("⚠️ Email processor already running")
    
    def stop_processing(self):
        """Stop the background email processing"""
        self.processing = False
        self.paused = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
            logger.info("✅ Background email processor stopped")
    
    def pause_processing(self):
        """Pause background processing temporarily"""
        self.paused = True
        logger.info("⏸️ Background email processor paused")
    
    def resume_processing(self):
        """Resume background processing"""
        self.paused = False
        logger.info("▶️ Background email processor resumed")
    
    def _process_emails(self):
        """Background thread for processing emails"""
        while self.processing:
            try:
                # Check if processing is paused
                if self.paused:
                    logger.info("⏸️ Email processing paused, waiting...")
                    time.sleep(10)  # Wait 10 seconds before checking again
                    continue
                
                # Check if manual processing was requested
                if self.manual_processing_requested:
                    logger.info("⏳ Manual processing requested, waiting for completion...")
                    time.sleep(5)  # Wait 5 seconds before checking again
                    continue
                
                self.processing_status['is_running'] = True
                self.processing_status['last_start'] = datetime.now().isoformat()
                self.processing_status['current_batch'] += 1
                
                logger.info(f"🔄 Starting email processing batch #{self.processing_status['current_batch']}")
                
                # Process emails with timeout
                start_time = time.time()
                results = process_inbox(user_id='background_processor')
                processing_time = time.time() - start_time
                
                # Update status
                self.processing_status['last_completion'] = datetime.now().isoformat()
                self.processing_status['emails_processed'] += len(results) if results else 0
                self.last_processing_time = processing_time
                
                logger.info(f"✅ Email processing completed in {processing_time:.2f}s - processed {len(results) if results else 0} emails")
                
                # Wait before next processing cycle (longer wait to be less aggressive)
                wait_time = 600  # 10 minutes between checks (increased from 5 minutes)
                if results and len(results) > 0:
                    wait_time = 300  # 5 minutes if emails were found (increased from 2 minutes)
                
                logger.info(f"⏳ Waiting {wait_time}s before next processing cycle")
                time.sleep(wait_time)
                
            except Exception as e:
                error_msg = f"Email processing error: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                
                # Add error to status
                self.processing_status['errors'].append({
                    'timestamp': datetime.now().isoformat(),
                    'error': error_msg
                })
                
                # Keep only last 10 errors
                if len(self.processing_status['errors']) > 10:
                    self.processing_status['errors'] = self.processing_status['errors'][-10:]
                
                # Wait longer on error
                logger.info("⏳ Waiting 10 minutes before retry due to error")
                time.sleep(600)
            
            finally:
                self.processing_status['is_running'] = False
    
    def get_status(self):
        """Get current processing status"""
        return {
            **self.processing_status,
            'is_processing': self.processing,
            'is_paused': self.paused,
            'manual_processing_requested': self.manual_processing_requested,
            'last_processing_time': self.last_processing_time
        }
    
    def force_process(self):
        """Force immediate email processing"""
        if self.processing_status['is_running']:
            return {'status': 'already_running', 'message': 'Email processing already in progress'}
        
        try:
            # Pause background processing temporarily
            self.manual_processing_requested = True
            logger.info("🔄 Force processing emails...")
            
            results = process_inbox(user_id='manual_force_processor')
            
            # Resume background processing
            self.manual_processing_requested = False
            
            return {
                'status': 'success',
                'emails_processed': len(results) if results else 0,
                'message': f'Processed {len(results) if results else 0} emails'
            }
        except Exception as e:
            # Resume background processing on error
            self.manual_processing_requested = False
            error_msg = f"Force processing error: {str(e)}"
            logger.error(error_msg)
            return {'status': 'error', 'message': error_msg}

# Global processor instance
email_processor = EmailProcessor()

def start_email_processor():
    """Start the background email processor"""
    email_processor.start_processing()

def stop_email_processor():
    """Stop the background email processor"""
    email_processor.stop_processing()

def pause_email_processor():
    """Pause the background email processor"""
    email_processor.pause_processing()

def resume_email_processor():
    """Resume the background email processor"""
    email_processor.resume_processing()

def get_email_processor_status():
    """Get email processor status"""
    return email_processor.get_status()

def force_email_processing():
    """Force immediate email processing"""
    return email_processor.force_process()

# Auto-start processor when module is imported
# Temporarily disabled to prevent hanging during app startup
# if __name__ != "__main__":
#     # Only auto-start if not running as main script
#     start_email_processor() 