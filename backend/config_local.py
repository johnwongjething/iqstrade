"""
Local Development Configuration
Handles CORS, database, and environment variables for local development
Uses same variable names as production for consistency
"""

import os
from dotenv import load_dotenv

# Load local environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env.local'))

class LocalConfig:
    """Configuration for local development using same variable names as production"""
    
    # Flask settings
    DEBUG = True
    TESTING = False
    
    # SECRET_KEY - Construct from individual components or use default
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        # Try to construct from JWT_SECRET_KEY or use default
        SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database settings (Railway PostgreSQL - same as production)
    # Construct DATABASE_URL from individual components
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_PORT = os.getenv('DB_PORT', '5432')
    
    # Construct DATABASE_URL if individual components are available
    if all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        DATABASE_URL = os.getenv('DATABASE_URL')  # Fallback if provided directly
    
    # CORS settings for local development
    CORS_ORIGINS = [
        'http://localhost:3000',  # React dev server
        'http://127.0.0.1:3000',
        'http://localhost:3001',
        'http://127.0.0.1:3001',
        'http://localhost:5000',  # Flask dev server
        'http://127.0.0.1:5000'
    ]
    
    # JWT settings for local development
    from datetime import timedelta
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'local-jwt-secret-key')
    JWT_COOKIE_SECURE = False  # Allow HTTP in local development
    JWT_COOKIE_SAMESITE = 'Lax'  # Less restrictive for local development
    JWT_COOKIE_DOMAIN = None  # No domain restriction for localhost
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # Email settings (same as production)
    EMAIL_HOST = os.getenv('EMAIL_HOST', 'imap.gmail.com')
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    
    # SMTP settings (same as production)
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL')
    
    # Google OCR settings (same as production)
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # Cloudinary settings (same as production)
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
    
    # Geetest settings (same as production)
    GEETEST_ID = os.getenv('GEETEST_ID')
    GEETEST_KEY = os.getenv('GEETEST_KEY')
    
    # Security settings (same as production)
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'sk-your_openai_api_key_here')
    
    # Email scheduler settings
    EMAIL_CHECK_INTERVAL = int(os.getenv('EMAIL_CHECK_INTERVAL', 300))
    AUTO_SEND_ENABLED = os.getenv('AUTO_SEND_ENABLED', 'true').lower() == 'true'
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 0.8))
    
    # File upload settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_EMAIL_SIZE', 10 * 1024 * 1024))  # 10MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_ATTACHMENT_TYPES = os.getenv('ALLOWED_ATTACHMENT_TYPES', 'pdf,jpg,jpeg,png').split(',')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'DEBUG')
    ENABLE_EMAIL_LOGGING = os.getenv('ENABLE_EMAIL_LOGGING', 'true').lower() == 'true'
    
    # Local development overrides
    FORCE_HTTPS = os.getenv('FORCE_HTTPS', '0') == '1'
    
    @staticmethod
    def init_app(app):
        """Initialize Flask app with local configuration"""
        app.config.from_object(LocalConfig)
        
        # Set up CORS for local development
        from flask_cors import CORS
        CORS(app, 
             origins=LocalConfig.CORS_ORIGINS,
             supports_credentials=True,
             allow_headers=['Content-Type', 'Authorization', 'X-CSRF-TOKEN'],
             methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
        
        # Disable HTTPS enforcement for local development
        app.config['JWT_COOKIE_SECURE'] = False
        app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
        
        print(f"[LOCAL CONFIG] Environment: {os.getenv('FLASK_ENV', 'local')}")
        print(f"[LOCAL CONFIG] CORS origins: {LocalConfig.CORS_ORIGINS}")
        print(f"[LOCAL CONFIG] Database: {LocalConfig.DATABASE_URL}")
        print(f"[LOCAL CONFIG] Email: {LocalConfig.EMAIL_USERNAME}")
        print(f"[LOCAL CONFIG] Google OCR: {LocalConfig.GOOGLE_APPLICATION_CREDENTIALS}")
        print(f"[LOCAL CONFIG] OpenAI API: {'✅ Set' if LocalConfig.OPENAI_API_KEY != 'sk-your_openai_api_key_here' else '❌ NOT SET'}")

class ProductionConfig:
    """Configuration for production (Render) - same variable names"""
    
    DEBUG = False
    TESTING = False
    
    # SECRET_KEY - Construct from individual components or use default
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        # Try to construct from JWT_SECRET_KEY or use default
        SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'production-secret-key')
    
    # Database settings (Railway)
    # Construct DATABASE_URL from individual components
    DB_HOST = os.getenv('DB_HOST')
    DB_NAME = os.getenv('DB_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_PORT = os.getenv('DB_PORT', '5432')
    
    # Construct DATABASE_URL if individual components are available
    if all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    else:
        DATABASE_URL = os.getenv('DATABASE_URL')  # Fallback if provided directly
    
    # CORS settings for production
    CORS_ORIGINS = [
        'https://iqstrade.onrender.com',
        'https://iqstrade-frontend.onrender.com'
    ]
    
    # JWT settings for production
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_SAMESITE = 'None'
    JWT_COOKIE_DOMAIN = 'iqstrade.onrender.com'
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 900))
    
    # Email settings
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    
    # SMTP settings
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL')
    
    # Google OCR settings
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    # Cloudinary settings
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET')
    
    # Geetest settings
    GEETEST_ID = os.getenv('GEETEST_ID')
    GEETEST_KEY = os.getenv('GEETEST_KEY')
    
    # Security settings
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
    
    # OpenAI settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Email scheduler settings
    EMAIL_CHECK_INTERVAL = int(os.getenv('EMAIL_CHECK_INTERVAL', 300))
    AUTO_SEND_ENABLED = os.getenv('AUTO_SEND_ENABLED', 'true').lower() == 'true'
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 0.8))
    
    # File upload settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_EMAIL_SIZE', 10 * 1024 * 1024))  # 10MB
    
    @staticmethod
    def init_app(app):
        """Initialize Flask app with production configuration"""
        app.config.from_object(ProductionConfig)
        
        # Set up CORS for production
        from flask_cors import CORS
        CORS(app, 
             origins=ProductionConfig.CORS_ORIGINS,
             supports_credentials=True,
             allow_headers=['Content-Type', 'Authorization', 'X-CSRF-TOKEN'],
             methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])

def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'local').lower()
    
    if env == 'production':
        return ProductionConfig
    else:
        return LocalConfig

# Database connection function for local development
def get_local_db_conn():
    """Get database connection for local development"""
    import psycopg2
    from urllib.parse import urlparse
    
    database_url = LocalConfig.DATABASE_URL
    if database_url and database_url.startswith('postgresql://'):
        # Parse the URL
        parsed = urlparse(database_url)
        return psycopg2.connect(
            dbname=parsed.path[1:],  # Remove leading slash
            user=parsed.username,
            password=parsed.password,
            host=parsed.hostname,
            port=parsed.port or 5432
        )
    else:
        # Fallback to individual environment variables
        return psycopg2.connect(
            dbname=LocalConfig.DB_NAME,
            user=LocalConfig.DB_USER,
            password=LocalConfig.DB_PASSWORD,
            host=LocalConfig.DB_HOST,
            port=LocalConfig.DB_PORT
        ) 