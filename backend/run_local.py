#!/usr/bin/env python3
"""
Local Development Server Runner
This script sets up the environment for local development and runs the Flask app.
"""

import os
import sys
import subprocess

def setup_local_environment():
    """Set up environment variables for local development"""
    
    # Set Flask environment to local
    os.environ['FLASK_ENV'] = 'local'
    
    # Local database configuration (adjust these as needed)
    os.environ['LOCAL_DB_NAME'] = 'iqstrade_local'
    os.environ['LOCAL_DB_USER'] = 'postgres'
    os.environ['LOCAL_DB_PASSWORD'] = '123456'
    os.environ['LOCAL_DB_HOST'] = 'localhost'
    os.environ['LOCAL_DB_PORT'] = '5432'
    
    # Local server configuration
    os.environ['PORT'] = '8000'
    
    # Disable HTTPS enforcement for local development
    os.environ['FORCE_HTTPS'] = '0'
    
    # JWT configuration for local development
    os.environ['JWT_SECRET_KEY'] = 'local-development-secret-key'
    
    # CORS configuration for local development
    os.environ['ALLOWED_ORIGINS'] = 'http://localhost:3000,http://localhost:3001'
    
    # Email configuration (use your local email settings)
    os.environ['SMTP_SERVER'] = 'smtp.gmail.com'
    os.environ['SMTP_PORT'] = '587'
    os.environ['SMTP_USERNAME'] = 'your-email@gmail.com'
    os.environ['SMTP_PASSWORD'] = 'your-app-password'
    os.environ['FROM_EMAIL'] = 'your-email@gmail.com'
    
    # Cloudinary configuration (use your own account)
    os.environ['CLOUDINARY_CLOUD_NAME'] = 'your-cloud-name'
    os.environ['CLOUDINARY_API_KEY'] = 'your-api-key'
    os.environ['CLOUDINARY_API_SECRET'] = 'your-api-secret'
    
    # Geetest configuration (use bypass mode for local development)
    os.environ['GEETEST_ID'] = 'test-id'
    os.environ['GEETEST_KEY'] = 'test-key'
    
    print("✅ Local environment configured")
    print(f"   Database: {os.environ['LOCAL_DB_HOST']}:{os.environ['LOCAL_DB_PORT']}/{os.environ['LOCAL_DB_NAME']}")
    print(f"   Server: http://localhost:{os.environ['PORT']}")
    print(f"   Frontend: http://localhost:3000")

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import flask
        import psycopg2
        import cloudinary
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def check_database():
    """Check if local database is accessible"""
    try:
        from config import get_db_conn
        conn = get_db_conn()
        if conn:
            conn.close()
            print("✅ Database connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    """Main function to run local development server"""
    print("🚀 Starting IQS Trade Local Development Server")
    print("=" * 50)
    
    # Setup environment
    setup_local_environment()
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check database
    if not check_database():
        print("⚠️  Database connection failed. Make sure PostgreSQL is running.")
        print("   You can still start the server, but database operations will fail.")
    
    print("\n" + "=" * 50)
    print("🌐 Starting Flask development server...")
    print("   Frontend should be running on: http://localhost:3000")
    print("   Backend API will be on: http://localhost:8000")
    print("   Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Import and run the Flask app
    try:
        from app import app
        app.run(host='0.0.0.0', port=8000, debug=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 