#!/usr/bin/env python3
"""
Simple Flask app test without email processor
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.local')

def test_flask_app():
    """Test Flask app startup without email processor"""
    try:
        print("Testing Flask app startup...")
        
        # Import Flask and create a simple app
        from flask import Flask
        
        app = Flask(__name__)
        
        @app.route('/')
        def hello():
            return "Hello, Flask is working!"
        
        print("✅ Flask app created successfully")
        
        # Test if we can run it
        with app.test_client() as client:
            response = client.get('/')
            print(f"✅ Flask test response: {response.data.decode()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_flask_app()
    sys.exit(0 if success else 1) 