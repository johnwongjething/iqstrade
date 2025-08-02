#!/usr/bin/env python3
"""
Simplified authentication test script
Tests only the auth-related endpoints without loading external dependencies
"""

import os
import sys
import requests
import json

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set environment variables for testing
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'
os.environ['JWT_COOKIE_SECURE'] = 'True'
os.environ['JWT_COOKIE_SAMESITE'] = 'Lax'
os.environ['JWT_COOKIE_HTTPONLY'] = 'True'
os.environ['JWT_COOKIE_CSRF_PROTECT'] = 'False'
os.environ['ALLOWED_ORIGINS'] = 'https://iqstrade.onrender.com,http://localhost:3000'
os.environ['ENABLE_EMAIL_SCHEDULER'] = 'false'

# Mock external dependencies
class MockVisionClient:
    def __init__(self):
        pass

# Mock the Google Cloud Vision import
sys.modules['google.cloud.vision_v1'] = type('MockVision', (), {
    'ImageAnnotatorClient': MockVisionClient
})()

# Mock other external dependencies
sys.modules['google.cloud'] = type('MockGoogleCloud', (), {})()
sys.modules['google'] = type('MockGoogle', (), {})()

def create_minimal_app():
    """Create a minimal Flask app with only auth routes"""
    from flask import Flask, jsonify
    from flask_cors import CORS
    from flask_jwt_extended import JWTManager
    from datetime import timedelta
    
    app = Flask(__name__)
    
    # Basic CORS
    CORS(app, origins=['http://localhost:3000'], supports_credentials=True)
    
    # JWT Configuration
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
    app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
    app.config['JWT_REFRESH_COOKIE_PATH'] = '/api/refresh'
    app.config['JWT_COOKIE_SECURE'] = True
    app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
    app.config['JWT_COOKIE_DOMAIN'] = None
    app.config['JWT_COOKIE_HTTPONLY'] = True
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False
    
    jwt = JWTManager(app)
    
    # Mock database connection
    class MockDB:
        def cursor(self):
            return self
        def execute(self, query, params):
            pass
        def fetchone(self):
            return (84, 'pbkdf2:sha256:600000$hIwLj4Br9vdp2kiW$1f3d23d0f330129794e49b04e7c3576b0e5610e6577214a3b9207b7d590ef2f0', 'staff', True, 'ray40', 'test@email.com', 'test_phone')
        def close(self):
            pass
        def commit(self):
            pass
    
    def get_db_conn():
        return MockDB()
    
    # Import auth routes with mocked dependencies
    from routes.auth_routes import auth_routes
    
    # Register auth routes
    app.register_blueprint(auth_routes, url_prefix='/api')
    
    return app

def test_auth_endpoints():
    """Test the authentication endpoints"""
    
    print("🔧 Creating minimal Flask app for testing...")
    app = create_minimal_app()
    
    print("🚀 Starting test server...")
    
    # Run the app in test mode
    with app.test_client() as client:
        print("\n🔍 Testing Authentication Endpoints")
        print("=" * 50)
        
        # Test 1: Clear cookies
        print("\n1️⃣ Testing clear-cookies endpoint...")
        response = client.post('/api/clear-cookies')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.get_json()}")
        
        # Test 2: Geetest registration
        print("\n2️⃣ Testing Geetest registration...")
        response = client.get('/api/geetest/register')
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.get_json()}")
        
        # Test 3: Login
        print("\n3️⃣ Testing login...")
        login_data = {
            "username": "ray40",
            "password": "Raysan11!!",
            "captcha_id": "test_id",
            "lot_number": "test_lot",
            "pass_token": "test_token",
            "captcha_output": "test_output"
        }
        response = client.post('/api/login', json=login_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.get_json()}")
        print(f"   Cookies: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("   ✅ Login successful!")
            
            # Test 4: /api/me endpoint
            print("\n4️⃣ Testing /api/me endpoint...")
            response = client.get('/api/me')
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.get_json()}")
            
            if response.status_code == 200:
                print("   ✅ /api/me successful!")
            else:
                print("   ❌ /api/me failed!")
        else:
            print("   ❌ Login failed!")
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")

if __name__ == "__main__":
    test_auth_endpoints() 