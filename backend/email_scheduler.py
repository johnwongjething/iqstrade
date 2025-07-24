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
from email_ingestor import process_inbox

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

def run_email_ingestion():
    """Run email ingestion process."""
    try:
        logger.info("🔄 Starting email ingestion process...")
        process_inbox()
        logger.info("✅ Email ingestion completed successfully")
    except Exception as e:
        logger.error(f"❌ Email ingestion failed: {e}")

def main():
    """Main scheduler function."""
    logger.info("🚀 Starting Email Scheduler for IQSTrade")
    
    # Schedule email processing every 5 minutes
    schedule.every(5).minutes.do(run_email_ingestion)
    
    # Also run immediately on startup
    logger.info("🔄 Running initial email ingestion...")
    run_email_ingestion()
    
    logger.info("⏰ Scheduler running - checking emails every 5 minutes")
    logger.info("Press Ctrl+C to stop")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    except KeyboardInterrupt:
        logger.info("🛑 Scheduler stopped by user")
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}")

if __name__ == "__main__":
    main() 