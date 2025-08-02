#!/usr/bin/env python3
"""
Standalone Email Service for IQSTrade
Runs the email scheduler independently of the Flask app.
Use this when you want to run email processing separately.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
if not os.path.exists(env_file):
    env_file = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_file)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('email_service.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Start the email service."""
    logger.info("🚀 Starting IQSTrade Email Service")
    logger.info("📧 This service will process emails every 15 minutes")
    logger.info("📁 Logs will be saved to email_service.log")
    
    # Check environment variables
    required_vars = ['EMAIL_USERNAME', 'EMAIL_PASSWORD', 'EMAIL_HOST', 'OPENAI_API_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        logger.error("Please check your .env or .env.local file")
        sys.exit(1)
    
    logger.info("✅ Environment variables loaded successfully")
    
    # Import and start the email scheduler
    try:
        from email_scheduler import main as scheduler_main
        scheduler_main()
    except KeyboardInterrupt:
        logger.info("🛑 Email service stopped by user")
    except Exception as e:
        logger.error(f"❌ Email service failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 