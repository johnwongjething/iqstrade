# CONFIG.PY LOADED
import os
import psycopg2
import time
import logging
from datetime import timedelta
from dotenv import load_dotenv

# Setup basic logging (visible in Render logs)
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

# Load .env.local for local development
env_file = os.path.join(os.path.dirname(__file__), '.env.local')
if os.path.exists(env_file):
    load_dotenv(env_file)
    logging.info(f"Loaded .env.local from: {env_file}")
else:
    logging.info(".env.local not found, using system environment variables")

# Environment Detection
def get_environment():
    """Detect if we're running locally or in production"""
    env = os.getenv('FLASK_ENV', '').lower()
    if env in ['production', 'development', 'local']:
        return env
    
    if os.getenv('PORT') or os.getenv('RAILWAY_ENVIRONMENT') or os.getenv('RENDER'):
        return 'production'
    
    return 'local'

CURRENT_ENV = get_environment()
logging.info(f"Running in environment: {CURRENT_ENV}")

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

def _db_connect_kwargs():
    kwargs = {
        'dbname': DatabaseConfig.dbname(),
        'user': DatabaseConfig.user(),
        'password': DatabaseConfig.password(),
        'host': DatabaseConfig.host(),
        'port': DatabaseConfig.port(),
        'connect_timeout': 10,
        # Temporarily removed 'options' - Neon/PgBouncer may reject custom -c params
        # 'options': '-c statement_timeout=30000 -c search_path=public'
    }
    host = DatabaseConfig.host() or ''
    if host and host not in ('localhost', '127.0.0.1'):
        kwargs['sslmode'] = 'require'
        kwargs['channel_binding'] = 'require'
        logging.info("Added Neon-required SSL params: sslmode=require, channel_binding=require")
    
    logging.debug(f"DB connect kwargs: {kwargs}")
    return kwargs

# Try to use connection pool
try:
    from psycopg2_pool import SimpleConnectionPool
    
    _conn_kwargs = _db_connect_kwargs()
    logging.info("Attempting to initialize SimpleConnectionPool...")
    
    db_pool = SimpleConnectionPool(
        minconn=1,
        maxconn=20,
        **_conn_kwargs
    )
    logging.info("Database connection pool created successfully")
    
    def get_db_conn(max_retries=3, retry_delay=2):
        """Get database connection from pool with retries and logging"""
        for attempt in range(max_retries):
            try:
                logging.debug(f"Pool getconn attempt {attempt + 1}")
                conn = db_pool.getconn()
                if conn:
                    logging.debug("Successfully got connection from pool")
                    return conn
                else:
                    logging.warning("Pool returned None connection")
            except Exception as e:
                logging.error(f"Pool getconn failed (attempt {attempt + 1}): {str(e)}", exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        logging.error("Failed to get connection from pool after all retries")
        return None
    
    def return_db_conn(conn):
        """Return connection to pool"""
        if conn:
            try:
                db_pool.putconn(conn)
                logging.debug("Connection returned to pool")
            except Exception as e:
                logging.error(f"Error returning connection to pool: {str(e)}")

except Exception as pool_error:  # Catch ALL errors during pool init (not just ImportError)
    logging.error(f"Failed to initialize connection pool: {str(pool_error)}", exc_info=True)
    logging.warning("Falling back to direct connections (no pooling)")
    
    def get_db_conn(max_retries=3, retry_delay=2):
        """Fallback: direct psycopg2.connect with retries"""
        for attempt in range(max_retries):
            try:
                logging.info(f"Direct connect attempt {attempt + 1}")
                conn = psycopg2.connect(**_db_connect_kwargs())
                logging.info("Direct connection established successfully")
                return conn
            except Exception as e:
                logging.error(f"Direct connect failed (attempt {attempt + 1}): {str(e)}", exc_info=True)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
        logging.error("All direct connect attempts failed")
        return None
    
    def return_db_conn(conn):
        """Close direct connection"""
        if conn:
            try:
                conn.close()
                logging.debug("Direct connection closed")
            except Exception as e:
                logging.error(f"Error closing direct connection: {str(e)}")

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

# OCR Configuration (kept for compatibility)
class OCRConfig:
    pass

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