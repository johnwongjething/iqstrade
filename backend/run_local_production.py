#!/usr/bin/env python3
"""
Local Production Simulation
This runs the backend with React build served locally, exactly like production
"""

import os
import subprocess
import sys
import time
from pathlib import Path

def build_frontend():
    """Build frontend and copy to backend"""
    print("📦 Building frontend for local production testing...")
    
    # Build frontend
    frontend_dir = Path("../frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found. Please run from backend/ directory.")
        return False
    
    try:
        # Install dependencies if needed
        print("   Installing frontend dependencies...")
        subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
        
        # Build frontend
        print("   Building React app...")
        subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)
        
        # Copy build to backend
        build_dir = frontend_dir / "build"
        backend_build_dir = Path("build")
        
        if backend_build_dir.exists():
            import shutil
            shutil.rmtree(backend_build_dir)
        
        import shutil
        shutil.copytree(build_dir, backend_build_dir)
        
        print("✅ Frontend built and copied to backend/build/")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def setup_production_env():
    """Set up production-like environment variables"""
    print("🔧 Setting up production-like environment...")
    
    env_vars = {
        'FLASK_ENV': 'production',
        'FLASK_DEBUG': '0',
        'JWT_COOKIE_SECURE': 'False',  # False for localhost
        'JWT_COOKIE_SAMESITE': 'Lax',
        'JWT_COOKIE_HTTPONLY': 'True',
        'JWT_COOKIE_CSRF_PROTECT': 'True',
        'ALLOWED_ORIGINS': 'http://localhost:5000,http://127.0.0.1:5000',
        'ENABLE_EMAIL_SCHEDULER': 'false',
        'PORT': '5000'
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   Set {key} = {value}")
    
    print("✅ Production environment variables set!")

def run_local_production():
    """Run Flask with production settings locally"""
    print("\n🚀 Starting Local Production Simulation...")
    
    # Build frontend first
    if not build_frontend():
        print("❌ Failed to build frontend. Exiting.")
        return
    
    # Set up environment
    setup_production_env()
    
    # Run Flask with production settings
    cmd = [
        sys.executable, '-m', 'flask', 'run',
        '--host=0.0.0.0',
        '--port=5000',
        '--no-debugger',
        '--no-reload'
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print("\n🌐 Your app will be available at: http://localhost:5000")
    print("🔒 This simulates production exactly - test JWT tokens and CSRF here!")
    print("📝 Press Ctrl+C to stop the server")
    
    try:
        subprocess.run(cmd, env=os.environ)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")

if __name__ == "__main__":
    run_local_production() 