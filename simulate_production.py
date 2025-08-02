#!/usr/bin/env python3
"""
Production environment simulation script
This helps test production settings locally before deploying to Render
"""

import os
import subprocess
import time

def setup_production_env():
    """Set up production-like environment variables"""
    
    print("🔧 Setting up production-like environment...")
    
    # Production environment variables
    env_vars = {
        'FLASK_ENV': 'production',
        'FLASK_DEBUG': '0',
        'JWT_COOKIE_SECURE': 'True',
        'JWT_COOKIE_SAMESITE': 'Lax',
        'JWT_COOKIE_HTTPONLY': 'True',
        'JWT_COOKIE_CSRF_PROTECT': 'False',
        'ALLOWED_ORIGINS': 'https://iqstrade.onrender.com,http://localhost:3000',
        'ENABLE_EMAIL_SCHEDULER': 'false',  # Disable for testing
    }
    
    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   Set {key} = {value}")
    
    print("✅ Production environment variables set!")

def run_flask_with_production_settings():
    """Run Flask with production settings"""
    
    print("\n🚀 Starting Flask with production settings...")
    
    # Set the environment variables
    setup_production_env()
    
    # Run Flask with production settings
    cmd = [
        'python', '-m', 'flask', 'run',
        '--host=0.0.0.0',
        '--port=5000',
        '--no-debugger',
        '--no-reload'
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print("Press Ctrl+C to stop the server")
    
    try:
        subprocess.run(cmd, env=os.environ)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")

if __name__ == "__main__":
    run_flask_with_production_settings() 