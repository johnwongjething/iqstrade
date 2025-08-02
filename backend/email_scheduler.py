#!/usr/bin/env python3
"""
Email Scheduler for IQSTrade
Runs email ingestor continuously in the background.
"""

import time
import schedule
import logging
import os
import sys
from datetime import datetime
from email_ingestor_working import process_inbox
from utils.timezone_utils import get_hk_now
import signal
import threading

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
running = True

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    logger.info(f"🛑 Received signal {signum}, shutting down gracefully...")
    running = False

def run_email_ingestion():
    """Run email ingestion process."""
    try:
        logger.info("🔄 Starting email ingestion process...")
        start_time = get_hk_now()
        
        results = process_inbox(user_id='background_scheduler')
        
        end_time = get_hk_now()
        duration = (end_time - start_time).total_seconds()
        
        if results:
            logger.info(f"✅ Email ingestion completed successfully - processed {len(results)} emails in {duration:.2f}s")
        else:
            logger.info(f"✅ Email ingestion completed - no new emails found in {duration:.2f}s")
            
    except Exception as e:
        logger.error(f"❌ Email ingestion failed: {e}")
        # Don't let errors stop the scheduler
        pass

def main():
    """Main scheduler function."""
    global running
    
    # Set up signal handlers for graceful shutdown (only in main thread)
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logger.info("🚀 Starting Email Scheduler for IQSTrade (with signal handlers)")
    except ValueError:
        logger.info("🚀 Starting Email Scheduler for IQSTrade (background mode)")
    
    logger.info(f"📧 Email processing interval: 15 minutes")
    logger.info(f"📁 Log file: email_scheduler.log")
    
    # Schedule email processing every 15 minutes
    schedule.every(15).minutes.do(run_email_ingestion)
    
    # Also run immediately on startup
    logger.info("🔄 Running initial email ingestion...")
    run_email_ingestion()
    
    logger.info("⏰ Scheduler running - checking emails every 15 minutes")
    
    try:
        while running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
            # Log heartbeat every hour
            if get_hk_now().minute == 0:
                logger.info("💓 Email scheduler heartbeat - running normally")
                
    except KeyboardInterrupt:
        logger.info("🛑 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}")
    finally:
        logger.info("🛑 Email scheduler shutdown complete")

def run_as_service():
    """Run the scheduler as a background service."""
    logger.info("🔧 Starting email scheduler as background service...")
    
    # Create a daemon thread for the scheduler
    scheduler_thread = threading.Thread(target=main, daemon=True)
    scheduler_thread.start()
    
    logger.info("✅ Email scheduler started as background service")
    return scheduler_thread

if __name__ == "__main__":
    main() 