# CONFIG.PY LOADED
import os
import psycopg2
import time
from datetime import timedelta
from dotenv import load_dotenv

# Load .env.local for local development
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
if os.path.exists(env_file):
    load_dotenv(env_file)
    pass  # Loaded .env.local from: {env_file}
else:
    pass  # .env.local not found, using system environment variables

# Environment Detection
def get_environment():
    """Detect if we're running locally or in production"""
    # Check for explicit environment variable
    env = os.getenv('FLASK_ENV', '').lower()
    if env in ['production', 'development', 'local']:
        return env
    
    # Auto-detect based on common production indicators
    if os.getenv('PORT') or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER'):
        return 'production'
    
    # Default to local if running on localhost
    return 'local'

CURRENT_ENV = get_environment()
# Running in environment: {CURRENT_ENV}

# Database Configuration
class DatabaseConfig:
    @staticmethod
    def dbname():
        return os.getenv('DB_NAME', 'testdb')
    
    @staticmethod
    def user():
        return os.getenv('DB_USER', 'postgres')
    
    @staticmethod
    def password():
        return os.getenv('DB_PASSWORD', '123456')
    
    @staticmethod
    def host():
        return os.getenv('DB_HOST', 'localhost')
    
    @staticmethod
    def port():
        return os.getenv('DB_PORT', '5432')

# Database connection pool for better concurrent user handling
try:
    from psycopg2_pool import SimpleConnectionPool
    
    # Create connection pool (min=1, max=20 connections)
    # This allows up to 20 concurrent database operations
    db_pool = SimpleConnectionPool(
        1, 20,  # minconn, maxconn
        dbname=DatabaseConfig.dbname(),
        user=DatabaseConfig.user(),
        password=DatabaseConfig.password(),
        host=DatabaseConfig.host(),
        port=DatabaseConfig.port(),
        connect_timeout=10,
        options='-c statement_timeout=30000'
    )
    pass  # Database connection pool created successfully
    
    def get_db_conn(max_retries=3, retry_delay=2):
        """Get database connection from pool"""
        for attempt in range(max_retries):
            try:
                conn = db_pool.getconn()
                if conn:
                    return conn
                else:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                    else:
                        pass  # Failed to get connection from pool
                        return None
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    pass  # Database pool error: {e}
                    return None
    
    def return_db_conn(conn):
        """Return database connection to pool"""
        try:
            if conn:
                db_pool.putconn(conn)
        except Exception as e:
            pass  # Error returning connection to pool: {e}
    
except ImportError:
    pass  # psycopg2-pool not available, using direct connections
    
    def get_db_conn(max_retries=3, retry_delay=2):
        for attempt in range(max_retries):
            try:
                conn = psycopg2.connect(
                    dbname=DatabaseConfig.dbname(),
                    user=DatabaseConfig.user(),
                    password=DatabaseConfig.password(),
                    host=DatabaseConfig.host(),
                    port=DatabaseConfig.port(),
                    connect_timeout=10,  # 10 second connection timeout
                    options='-c statement_timeout=30000'  # 30 second query timeout
                )
                return conn
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    return None
    
    def return_db_conn(conn):
        """Dummy function for direct connections"""
        try:
            if conn:
                conn.close()
        except:
            pass

# Email Configuration
class EmailConfig:
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'ray6330099@gmail.com')

# Cloudinary Configuration
class CloudinaryConfig:
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
    CLOUDINARY_BASE_URL = os.getenv('CLOUDINARY_BASE_URL')

# Global Cloudinary variables for compatibility
CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')


# OCR Configuration
class OCRConfig:
    pass  # No longer needed, but kept for compatibility

# File Paths
class PathConfig:
    UPLOADS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    REPORTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')

# Deployment/Frontend URL config for CORS or API docs
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://iqstrade.onrender.com')

# JWT Configuration
class JWTConfig:
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-this-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

def is_https_enforced():
    flask_env = os.getenv('FLASK_ENV', '').lower()
    force_https = os.getenv('FORCE_HTTPS', '0') == '1'
    enforce = flask_env == 'production' or force_https
    return enforce

def backup_reminder():
    pass

def monitoring_reminder():
    pass

backup_reminder()
monitoring_reminder()
