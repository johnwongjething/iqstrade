print("CONFIG.PY LOADED")
import os
import psycopg2
import time

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

# Email Configuration
class EmailConfig:
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL', 'ray6330099@gmail.com')

# OCR Configuration
class OCRConfig:
    pass  # No longer needed, but kept for compatibility

# File Paths
class PathConfig:
    UPLOADS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    REPORTS_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'reports')

# JWT Configuration
class JWTConfig:
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'change-this-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 86400))  # 24 hours

# Update database connection function to use config with timeout and retry
def get_db_conn(max_retries=3, retry_delay=2):
    # Remove or comment out debug prints for production
    # print("get_db_conn CALLED")
    for attempt in range(max_retries):
        try:
            # print(f"[DEBUG] DB_NAME={DatabaseConfig.dbname()} DB_USER={DatabaseConfig.user()} DB_HOST={DatabaseConfig.host()} DB_PORT={DatabaseConfig.port()} (attempt {attempt + 1})")
            conn = psycopg2.connect(
                dbname=DatabaseConfig.dbname(),
                user=DatabaseConfig.user(),
                password=DatabaseConfig.password(),
                host=DatabaseConfig.host(),
                port=DatabaseConfig.port(),
                connect_timeout=10,  # 10 second connection timeout
                options='-c statement_timeout=30000'  # 30 second query timeout
            )
            # print("Database connection established successfully")
            return conn
        except Exception as e:
            # print(f"Error connecting to database (attempt {attempt + 1}): {str(e)}")
            if attempt < max_retries - 1:
                # print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                # print(f"Failed to connect to database after {max_retries} attempts")
                # print(f"Database config: {DatabaseConfig.dbname()}, {DatabaseConfig.user()}, {DatabaseConfig.host()}, {DatabaseConfig.port()}")
                return None

# --- HTTPS Enforcement Helper ---
def is_https_enforced():
    # Only enforce HTTPS in production, never in development or testing
    flask_env = os.getenv('FLASK_ENV', '').lower()
    force_https = os.getenv('FORCE_HTTPS', '0') == '1'
    enforce = flask_env == 'production' or force_https
    # print(f"[DEBUG] HTTPS enforcement: {enforce} (FLASK_ENV={flask_env}, FORCE_HTTPS={force_https})")
    return enforce

# --- Backup & Monitoring Guidance ---
# These are operational, not code, but provide reminders/logs

def backup_reminder():
    # print("[SECURITY] Ensure regular, automated database backups are scheduled (e.g., pg_dump, managed snapshots). Test recovery procedures regularly.")
    pass

def monitoring_reminder():
    # print("[SECURITY] Set up monitoring/logging for database and application (e.g., CloudWatch, Sentry, pg_stat_statements). Enable alerts for suspicious activity.")
    pass

backup_reminder()
monitoring_reminder()
