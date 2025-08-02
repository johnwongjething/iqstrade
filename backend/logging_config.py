#!/usr/bin/env python3
"""
Logging configuration for the IQSTrade application
Reduces noise while keeping important information
"""

import logging
import os

def configure_logging():
    """Configure logging to reduce noise while keeping important information"""
    
    # Set Flask's logging level to WARNING to reduce HTTP 200 noise
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    # Set other noisy loggers to WARNING
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    # Suppress Flask-Limiter warnings (very noisy)
    logging.getLogger('flask_limiter').setLevel(logging.ERROR)
    
    # Suppress performance monitor warnings in development
    if os.getenv('FLASK_ENV') == 'local':
        logging.getLogger('utils.performance_monitor').setLevel(logging.ERROR)
    
    # Keep our application logs at INFO level
    logging.getLogger('root').setLevel(logging.INFO)
    
    # Configure format for cleaner output
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Apply to root logger
    root_logger = logging.getLogger()
    root_logger.handlers = [console_handler]
    root_logger.setLevel(logging.INFO)
    
    # Environment-specific settings
    if os.getenv('FLASK_ENV') == 'production':
        # In production, be more quiet
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
        logging.getLogger('root').setLevel(logging.WARNING)
    else:
        # In development, show more info but reduce noise
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
        logging.getLogger('root').setLevel(logging.INFO) 