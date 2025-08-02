#!/usr/bin/env python3
"""
Local Development Server for IQSTrade
Handles CORS, database, and environment setup for local development
"""

import os
import sys
from dotenv import load_dotenv

# Configure logging to reduce noise
from logging_config import configure_logging
configure_logging()

# Load local environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

# Set environment for local development
os.environ['FLASK_ENV'] = 'local'
os.environ['FLASK_DEBUG'] = 'true'

# Enable email scheduler for local development
os.environ['ENABLE_EMAIL_SCHEDULER'] = 'true'

from flask import Flask
from config_local import LocalConfig, get_config
from app import app

def setup_local_app():
    """Setup Flask app for local development"""
    
    # Initialize configuration
    config = get_config()
    config.init_app(app)
    
    # Override database connection for local development
    from config_local import get_local_db_conn
    import db_utils
    db_utils.get_db_conn = get_local_db_conn
    
    # Override config database connection
    import config as main_config
    main_config.get_db_conn = get_local_db_conn
    
    pass  # = * 60
    pass  # 🚀 LOCAL DEVELOPMENT SERVER STARTING
    pass  # = * 60
    pass  # 📁 Environment: {os.getenv('FLASK_ENV', 'local')}
    pass  # 🔧 Debug Mode: {app.config.get('DEBUG', False)}
    pass  # 🌐 CORS Origins: {config.CORS_ORIGINS}
    pass  # 🗄️  Database: {config.DATABASE_URL}
    pass  # 🤖 OpenAI API: {'✅ Set' if config.OPENAI_API_KEY != 'sk-your_openai_api_key_here' else '❌ NOT SET'}
    pass  # 📧 Email Scheduler: {'❌ Disabled' if os.getenv('ENABLE_EMAIL_SCHEDULER', 'false').lower() == 'false' else '✅ Enabled'}
    pass  # = * 60
    
    return app

if __name__ == '__main__':
    # Setup local app
    local_app = setup_local_app()
    
    # Run development server
    try:
        pass  # 🌐 Starting Flask development server...
        pass  # 📱 Frontend should be running on: http://localhost:3000
        pass  # 🔧 Backend API will be on: http://localhost:5000
        pass  # ⏹️  Press Ctrl+C to stop
        pass  # - * 60
        
        local_app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )
    except KeyboardInterrupt:
        pass  # 🛑 Server stopped by user
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1) 