#!/usr/bin/env python3
"""
Railway Database Download Script
Downloads your Railway PostgreSQL database to local
"""
import os
import subprocess
import sys
from datetime import datetime

def download_railway_db():
    """Download Railway database to local"""
    print("🗄️ Railway Database Download Tool")
    print("=" * 50)
    
    # Get database connection details
    print("Please enter your Railway database details:")
    host = input("Host (e.g., shortline.proxy.rlwy.net): ").strip()
    port = input("Port (e.g., 42570): ").strip()
    user = input("Username (e.g., postgres): ").strip()
    db_name = input("Database name (e.g., railway): ").strip()
    password = input("Password: ").strip()
    
    if not all([host, port, user, db_name, password]):
        print("❌ All fields are required!")
        return
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"railway_backup_{timestamp}.sql"
    
    print(f"\n📥 Downloading database to: {backup_file}")
    print("⏳ This may take a few minutes...")
    
    try:
        # Set password environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = password
        
        # Run pg_dump command
        cmd = [
            'pg_dump',
            '-h', host,
            '-p', port,
            '-U', user,
            '-d', db_name,
            '--no-password',  # Use environment variable
            '--verbose',       # Show progress
            '--clean',         # Add DROP commands
            '--if-exists',     # Add IF EXISTS to DROP
            '--create',        # Add CREATE DATABASE
            '--no-owner',      # Don't set ownership
            '--no-privileges'  # Don't set privileges
        ]
        
        with open(backup_file, 'w') as f:
            result = subprocess.run(cmd, env=env, stdout=f, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print(f"✅ Database downloaded successfully to: {backup_file}")
            
            # Get file size
            file_size = os.path.getsize(backup_file)
            print(f"📊 File size: {file_size / 1024 / 1024:.2f} MB")
            
            # Show restore instructions
            print(f"\n🔄 To restore this backup to your local database:")
            print(f"   psql -h localhost -U postgres -d your_local_db < {backup_file}")
            
        else:
            print(f"❌ Download failed!")
            print(f"Error: {result.stderr}")
            
    except FileNotFoundError:
        print("❌ pg_dump not found!")
        print("💡 Make sure PostgreSQL client tools are installed:")
        print("   Windows: Install PostgreSQL from https://www.postgresql.org/download/windows/")
        print("   macOS: brew install postgresql")
        print("   Linux: sudo apt-get install postgresql-client")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def restore_to_local():
    """Restore downloaded backup to local database"""
    print("\n🔄 Restore to Local Database")
    print("=" * 30)
    
    backup_file = input("Backup file path: ").strip()
    local_db = input("Local database name: ").strip()
    
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return
    
    print(f"📥 Restoring {backup_file} to local database: {local_db}")
    
    try:
        cmd = ['psql', '-h', 'localhost', '-U', 'postgres', '-d', local_db, '-f', backup_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database restored successfully!")
        else:
            print(f"❌ Restore failed!")
            print(f"Error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "restore":
        restore_to_local()
    else:
        download_railway_db() 