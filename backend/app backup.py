
import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_from_directory, make_response, redirect
from flask_cors import CORS, cross_origin
from flask_jwt_extended import JWTManager, create_access_token, set_access_cookies, unset_jwt_cookies, jwt_required, get_jwt_identity, get_csrf_token
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG if os.getenv('FLASK_ENV') == 'development' else logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder=None)

is_development = os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == 'True'

if is_development:
    app_cookie_secure = False
    app_cookie_samesite = 'Lax'
else:
    app_cookie_secure = True
    app_cookie_samesite = 'None'

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
if not app.config['JWT_SECRET_KEY'] and not is_development:
    raise ValueError("JWT_SECRET_KEY must be set in production")

app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_SECURE'] = app_cookie_secure
app.config['JWT_COOKIE_SAMESITE'] = app_cookie_samesite
app.config['JWT_COOKIE_HTTPONLY'] = True
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['SESSION_COOKIE_SECURE'] = app_cookie_secure
app.config['SESSION_COOKIE_SAMESITE'] = app_cookie_samesite
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}

jwt = JWTManager(app)

allowed_origins = []
if os.getenv('ALLOWED_ORIGINS'):
    prod_domains = [origin.strip() for origin in os.getenv('ALLOWED_ORIGINS').split(',') if origin.strip()]
    allowed_origins.extend(prod_domains)
if is_development:
    local_domains = ['http://localhost:3000', 'http://127.0.0.1:3000']
    allowed_origins.extend(local_domains)

CORS(app, origins=allowed_origins, supports_credentials=True)
logger.info(f"CORS allowed origins: {allowed_origins}")

@app.after_request
def set_csp_header(response):
    csp = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        f"connect-src 'self' {' '.join(allowed_origins)}; "
        f"frame-src 'self' {' '.join(allowed_origins)}; "
        f"frame-ancestors 'self' {' '.join(allowed_origins)}; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "object-src 'none';"
    )
    response.headers['Content-Security-Policy'] = csp
    return response

if is_development:
    limiter = Limiter(get_remote_address, app=app, default_limits=["1000 per day", "100 per hour"])
else:
    limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"], storage_uri="redis://localhost:6379")



# === Original App Logic ===

import json
from flask import Flask, request, jsonify, send_from_directory, make_response, redirect
from flask_cors import CORS, cross_origin
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import date, datetime, timedelta
from invoice_utils import generate_invoice_pdf
from email_utils import send_invoice_email, send_unique_number_email, send_contact_email, send_simple_email
from dotenv import load_dotenv
import secrets
import psycopg2
from config import DatabaseConfig, get_db_conn, EmailConfig
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import smtplib
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from cryptography.fernet import Fernet
import re
from extract_fields import extract_fields
import pytz
from werkzeug.middleware.proxy_fix import ProxyFix
from dateutil import parser
import requests

load_dotenv()

# Disable Flask's default static file handler to ensure custom static route is used
app = Flask(__name__, static_folder=None)
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY")


def verify_captcha(token):
    """Bypass reCAPTCHA verification (disabled for China compatibility)."""
    return True

def set_csp_header(response):
    # Allow embedding from local dev and production (add your prod domain if needed)
    csp = (
        "default-src 'self'; "
        "img-src 'self' data:; "
        "connect-src 'self'; "
        "frame-src 'self' http://localhost:8000 http://127.0.0.1:8000 http://localhost:3000 http://127.0.0.1:3000; "
        "frame-ancestors 'self' http://localhost:3000 http://127.0.0.1:3000 http://localhost:8000 http://127.0.0.1:8000; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "object-src 'none';"
    )
    # If you deploy, add your prod domain to frame-src and frame-ancestors above
    response.headers['Content-Security-Policy'] = csp
    print(f"Applied CSP: {csp}")  # Debug CSP application
    return response

@app.after_request
def apply_csp(response):
    return set_csp_header(response)

# # def set_csp_header(response):
# #     # Allow scripts and styles from self and trusted CDN (adjust as needed)
# #     csp = (
# #         "default-src 'self'; "
# #         "script-src 'self' https://www.terryraylogicticsco.xyz https://terryraylogicticsco.xyz https://rayray.onrender.com; "
# #         "style-src 'self' https://fonts.googleapis.com; "
# #         "img-src 'self' data: https://www.terryraylogicticsco.xyz https://terryraylogicticsco.xyz https://rayray.onrender.com; "
# #         "font-src 'self' https://fonts.gstatic.com; "
# #         "connect-src 'self' https://www.terryraylogicticsco.xyz https://terryraylogicticsco.xyz https://rayray.onrender.com http://localhost:3000 http://localhost:8000 http://127.0.0.1:8000; "
# #         "frame-ancestors 'none'; "
# #         "object-src 'none'; "
# #         "base-uri 'self'; "
# #     )
# #     response.headers['Content-Security-Policy'] = csp
# #     return response

# # Set a secure Content-Security-Policy header for all responses
# # @app.after_request
# # def set_csp_header(response):
# #     # Allow scripts and styles from self and trusted CDN (adjust as needed)
# #     csp = (
# #         "default-src 'self'; "
# #         "script-src 'self' 'unsafe-inline' https://www.terryraylogicticsco.xyz https://terryraylogicticsco.xyz https://rayray.onrender.com; "
# #         "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
# #         "img-src 'self' data: https://www.terryraylogicticsco.xyz https://terryraylogicticsco.xyz https://rayray.onrender.com; "
# #         "font-src 'self' https://fonts.gstatic.com; "
# #         "connect-src 'self' https://www.terryraylogicticsco.xyz https://terryraylogicticsco.xyz https://rayray.onrender.com http://localhost:3000 http://localhost:8000 http://127.0.0.1:8000; "
# #         "frame-ancestors 'none'; "
# #         "object-src 'none'; "
# #         "base-uri 'self'; "
# #     )
# #     response.headers['Content-Security-Policy'] = csp
# #     return response

# # Add ProxyFix middleware to handle X-Forwarded-For headers
# # app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)


allowed_origins = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
]
# Define default allowed origins first
# allowed_origins = [
#     'http://localhost:3000',  # Development
#     'http://localhost:8000',  # Local Flask server
#     'http://127.0.0.1:8000',  # Local Flask server
    # 'https://terryraylogicticsco.xyz',  # Commented out for local dev
    # 'https://www.terryraylogicticsco.xyz',  # Commented out for local dev
# ]

# Add environment variable for additional origins
env_origins = os.getenv('ALLOWED_ORIGINS', '').split(',')
if env_origins and env_origins[0]:
    allowed_origins.extend([origin.strip() for origin in env_origins])

# Debug print for allowed origins (must be after allowed_origins is defined)
print("CORS allowed origins:", allowed_origins)

CORS(app, origins=allowed_origins, supports_credentials=True)
from payment_webhook import payment_webhook
from payment_link import payment_link

app.register_blueprint(payment_webhook, url_prefix='/api/webhook')
app.register_blueprint(payment_link)


@app.route('/static/<path:subpath>')
def static_files(subpath):
    # This should point to /frontend/build/static
    static_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build', 'static'))
    full_path = os.path.join(static_root, subpath)
    print(f"\n📦 Requested subpath: {subpath}")
    print(f"➡️ static_root: {static_root}")
    print(f"➡️ full_path: {full_path}\n")

    if os.path.exists(full_path):
        print(f"✅ File exists: {full_path}")
        return send_from_directory(static_root, subpath)
    else:
        print(f"❌ File not found: {full_path}")
        # List directory contents for debugging
        try:
            print(f"Contents of {static_root}:", os.listdir(static_root))
            parent_dir = os.path.dirname(full_path)
            print(f"Contents of {parent_dir}:", os.listdir(parent_dir))
        except Exception as e:
            print(f"Error listing directory: {e}")
        return "Static file not found", 404


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build'))
    file_path = os.path.join(build_dir, path)
    print(f"🌐 Serving request for: {path} → {file_path}")

    # static assets handled separately
    if path.startswith('static/'):
        return static_files(path[7:])
    
    # serve actual files if they exist
    if path and os.path.exists(file_path):
        return send_from_directory(build_dir, path)
    
    # fallback to index.html (React SPA routing)
    return send_from_directory(build_dir, 'index.html')

@app.route('/api/ping')
def ping():
    return {"message": "pong"}, 200


# Initialize Rate Limiter with conditional limits based on environment
is_development = os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == 'True'


app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
if not app.config['JWT_SECRET_KEY'] and not is_development:
    raise ValueError("JWT_SECRET_KEY must be set in production")
#app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'change-this-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
jwt = JWTManager(app)

# Configure JWT to use cookies
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_SECURE'] = not is_development  # Only send cookies over HTTPS in production
app.config['JWT_COOKIE_HTTPONLY'] = True
app.config['JWT_COOKIE_SAMESITE'] = 'Lax'
# Enable CSRF protection for JWT cookies
app.config['JWT_COOKIE_CSRF_PROTECT'] = True

# Initialize Rate Limiter with conditional limits based on environment
if is_development:
    # More lenient limits for development
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["1000 per day", "100 per hour"]
    )
else:
    # Stricter limits for production
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"]
    )

# Custom error handler for rate limiting
@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({
        'error': 'Too many requests. Please wait before trying again.',
        'retry_after': getattr(e, 'retry_after', 3600)  # Default to 1 hour
    }), 429

encryption_key = os.getenv('ENCRYPTION_KEY')
if not encryption_key:
    if is_development:
        encryption_key = Fernet.generate_key()
        print(f"Generated new encryption key: {encryption_key.decode()}")
        print("Please add this to your .env file as ENCRYPTION_KEY=<key>")
    else:
        raise ValueError("ENCRYPTION_KEY must be set in production")
else:
    if isinstance(encryption_key, str):
        encryption_key = encryption_key.encode()
fernet = Fernet(encryption_key)


# # Initialize Encryption
# # Use a persistent key from environment variables, or generate one if not exists
# encryption_key = os.getenv('ENCRYPTION_KEY')
# if not encryption_key:
#     # Generate a new key and save it (you should save this to your .env file)
#     encryption_key = Fernet.generate_key()
#     print(f"Generated new encryption key: {encryption_key.decode()}")
#     print("Please add this to your .env file as ENCRYPTION_KEY=<key>")
# else:
#     # Convert string key to bytes if needed
#     if isinstance(encryption_key, str):
#         encryption_key = encryption_key.encode()

# fernet = Fernet(encryption_key)

# Security Helper Functions
def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "Password must contain at least one special character"
    return True, "Password is valid"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def encrypt_sensitive_data(data):
    if not data:
        return data
    try:
        if isinstance(data, str):
            return fernet.encrypt(data.encode()).decode()
        return data
    except Exception as e:
        print(f"Encryption error for data: {data[:50]}... Error: {str(e)}")
        # If encryption fails, return the original data
        return data

def decrypt_sensitive_data(encrypted_data):
    if not encrypted_data:
        return encrypted_data
    try:
        # Check if the data looks like it's encrypted (starts with gAAAAA)
        if isinstance(encrypted_data, str) and encrypted_data.startswith('gAAAAA'):
            try:
                return fernet.decrypt(encrypted_data.encode()).decode()
            except Exception as decrypt_error:
                print(f"Decryption failed for data: {encrypted_data[:50]}... Error: {str(decrypt_error)}")
                # If decryption fails, it might be encrypted with a different key
                # Return the original data and log the issue
                return encrypted_data
        else:
            # Data is not encrypted, return as is
            return encrypted_data
    except Exception as e:
        print(f"Decryption error for data: {encrypted_data[:50]}... Error: {str(e)}")
        # If decryption fails, return the original data (assuming it's not encrypted)
        return encrypted_data

def is_account_locked(cur, user_id):
    """Check if the user's account is currently locked."""
    cur.execute("SELECT lockout_until FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    if row and row[0]:
        lockout_until = row[0]
        now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
        if lockout_until and now < lockout_until:
            return True, lockout_until.isoformat()
    return False, None

def increment_failed_attempts(cur, user_id, max_attempts=5, lockout_minutes=15):
    """Increment failed login attempts and lock account if threshold is reached."""
    cur.execute("SELECT failed_attempts FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    failed_attempts = row[0] if row else 0
    failed_attempts += 1
    lockout_until = None
    if failed_attempts >= max_attempts:
        lockout_until = datetime.now(pytz.timezone('Asia/Hong_Kong')) + timedelta(minutes=lockout_minutes)
        cur.execute("UPDATE users SET failed_attempts=%s, lockout_until=%s WHERE id=%s", (failed_attempts, lockout_until, user_id))
    else:
        cur.execute("UPDATE users SET failed_attempts=%s WHERE id=%s", (failed_attempts, user_id))
    return failed_attempts, lockout_until.isoformat() if lockout_until else None

def reset_failed_attempts(cur, user_id):
    """Reset failed login attempts and lockout status after successful login."""
    cur.execute("UPDATE users SET failed_attempts=0, lockout_until=NULL WHERE id=%s", (user_id,))

def log_sensitive_operation(user_id, operation, details):
    # Log sensitive operations to audit_logs for brute force monitoring
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO audit_logs (user_id, operation, details, timestamp) VALUES (%s, %s, %s, NOW())',
            (user_id, operation, details)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error logging operation: {str(e)}")

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Using get_db_conn from config.py

@app.route('/', methods=['GET'])
@limiter.exempt
def root():
    """Root endpoint with API information"""
    return jsonify({
        'message': 'Terry Ray Logistics Shipping System API',
        'version': '1.0.0',
        'status': 'running',
        'endpoints': {
            'health': '/health',
            'api_base': '/api',
            'documentation': 'Check the API endpoints for more information'
        }
    }), 200

@app.route('/health', methods=['GET'])
@limiter.exempt
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test database connection
        conn = get_db_conn()
        if conn:
            conn.close()
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
            }), 503
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
        }), 503

@app.route('/api/register', methods=['POST'])
@limiter.limit("50 per hour" if is_development else "20 per hour")  # More lenient in development
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    customer_name = data.get('customer_name')
    customer_email = data.get('customer_email')
    customer_phone = data.get('customer_phone')
    if not all([username, password, role, customer_name, customer_email, customer_phone]):
        return jsonify({'error': 'Missing fields'}), 400
    
    # Validate password
    is_valid, message = validate_password(password)
    if not is_valid:
        return jsonify({'error': message}), 400
    
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        # Encrypt sensitive data
        encrypted_email = encrypt_sensitive_data(customer_email)
        encrypted_phone = encrypt_sensitive_data(customer_phone)
        
        cur.execute(
            "INSERT INTO users (username, password_hash, role, customer_name, customer_email, customer_phone) VALUES (%s, %s, %s, %s, %s, %s)",
            (username, generate_password_hash(password), role, customer_name, encrypted_email, encrypted_phone)
        )
        conn.commit()
        log_sensitive_operation(None, 'register', f'New user registered: {username}')
        cur.close()
        conn.close()
        return jsonify({'message': 'Registration submitted, waiting for approval.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    captcha_token = data.get('captcha_token')
    print("Received captcha_token:", captcha_token)
    if not verify_captcha(captcha_token):
        return jsonify({'error': 'CAPTCHA verification failed'}), 400
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash, role, approved, customer_name, customer_email, customer_phone FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    if not user:
        # Log failed attempt for monitoring
        log_sensitive_operation(None, 'login_failed', f'Username {username} not found')
        cur.close()
        conn.close()
        return jsonify({'error': 'User not found'}), 401
    user_id, password_hash, role, approved, customer_name, customer_email, customer_phone = user
    # Check account lockout
    locked, lockout_until = is_account_locked(cur, user_id)
    if locked:
        cur.close()
        conn.close()
        return jsonify({'error': f'Account locked. Try again after {lockout_until}'}), 403
    if not approved:
        cur.close()
        conn.close()
        return jsonify({'error': 'User not approved yet'}), 403
    if not check_password_hash(password_hash, password):
        failed_attempts, lockout_until = increment_failed_attempts(cur, user_id)
        conn.commit()
        # Log failed attempt for monitoring
        log_sensitive_operation(user_id, 'login_failed', f'Incorrect password. Attempts: {failed_attempts}')
        cur.close()
        conn.close()
        if lockout_until:
            return jsonify({'error': f'Account locked. Try again after {lockout_until}'}), 403
        return jsonify({'error': 'Incorrect password'}), 401
    reset_failed_attempts(cur, user_id)
    conn.commit()
    access_token = create_access_token(identity=json.dumps({'id': user_id, 'role': role, 'username': username}))
    log_sensitive_operation(user_id, 'login', 'User logged in successfully')
    response = make_response(jsonify({
        "customer_name": customer_name,
        "customer_email": customer_email,
        "customer_phone": customer_phone,
        'role': role,
        'username': username
    }), 200)
    from flask_jwt_extended import set_access_cookies
    set_access_cookies(response, access_token)
    cur.close()
    conn.close()
    return response

@app.route('/api/approve_user/<int:user_id>', methods=['POST'])
@jwt_required()
def approve_user(user_id):
    user = json.loads(get_jwt_identity())
    if user['role'] not in ['staff', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET approved=TRUE WHERE id=%s", (user_id,))
    # Fetch user email and name
    cur.execute("SELECT customer_email, customer_name FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if row:
        customer_email, customer_name = row
        # Decrypt email for sending
        decrypted_email = decrypt_sensitive_data(customer_email) if customer_email else ''
        if decrypted_email:
            # Send confirmation email
            subject = "Your registration has been approved"
            body = f"Dear {customer_name},\n\nYour registration has been approved. You can now log in and use our services.\n\nThank you!"
            send_simple_email(decrypted_email, subject, body)
    return jsonify({'message': 'User approved'})

@app.route('/api/unapproved_users', methods=['GET'])
@jwt_required()
def get_unapproved_users():
    user = json.loads(get_jwt_identity())
    if user['role'] not in ['staff', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, username, customer_name, customer_email, customer_phone, role FROM users WHERE approved = FALSE')
    users = []
    for row in cur.fetchall():
        # Decrypt email and phone
        decrypted_email = decrypt_sensitive_data(row[3]) if row[3] is not None else ''
        decrypted_phone = decrypt_sensitive_data(row[4]) if row[4] is not None else ''
        users.append({
            'id': row[0],
            'username': row[1],
            'customer_name': row[2],
            'customer_email': decrypted_email,
            'customer_phone': decrypted_phone,
            'role': row[5]
        })
    cur.close()
    conn.close()
    return jsonify(users)

@app.route('/api/stats/files_by_date')
@jwt_required()
def files_by_date():
    user = json.loads(get_jwt_identity())
    if user['role'] != 'staff':
        return jsonify({'error': 'Unauthorized'}), 403
    query_date = request.args.get('date')
    conn = get_db_conn()
    cur = conn.cursor()
    # Use timezone-aware date range
    start_date, end_date = get_hk_date_range(query_date)
    cur.execute("SELECT COUNT(*) FROM bill_of_lading WHERE created_at >= %s AND created_at < %s", (start_date, end_date))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return jsonify({'files_created': count})

@app.route('/api/stats/completed_today')
@jwt_required()
def completed_today():
    user = json.loads(get_jwt_identity())
    if user['role'] != 'staff':
        return jsonify({'error': 'Unauthorized'}), 403
    # Use timezone-aware date
    hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
    today = hk_now.date().isoformat()
    conn = get_db_conn()
    cur = conn.cursor()
    # Use timezone-aware date range
    start_date, end_date = get_hk_date_range(today)
    cur.execute("SELECT COUNT(*) FROM bill_of_lading WHERE status='Completed' AND completed_at >= %s AND completed_at < %s", (start_date, end_date))
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return jsonify({'completed_today': count})

@app.route('/api/stats/payments_by_date')
@jwt_required()
def payments_by_date():
    user = json.loads(get_jwt_identity())
    if user['role'] != 'staff':
        return jsonify({'error': 'Unauthorized'}), 403
    query_date = request.args.get('date')
    conn = get_db_conn()
    cur = conn.cursor()
    # Use timezone-aware date range
    start_date, end_date = get_hk_date_range(query_date)
    cur.execute("SELECT SUM(service_fee) FROM bill_of_lading WHERE created_at >= %s AND created_at < %s", (start_date, end_date))
    total = cur.fetchone()[0] or 0
    cur.close()
    conn.close()
    return jsonify({'payments_received': float(total)})

@app.route('/api/stats/bills_by_date')
@jwt_required()
def bills_by_date():
    user = json.loads(get_jwt_identity())
    if user['role'] != 'staff':
        return jsonify({'error': 'Unauthorized'}), 403
    query_date = request.args.get('date')
    conn = get_db_conn()
    cur = conn.cursor()
    # Use timezone-aware date range
    start_date, end_date = get_hk_date_range(query_date)
    cur.execute("""
        SELECT 
            COUNT(*) as total_entries,
            COALESCE(SUM(ctn_fee), 0) as total_ctn_fee,
            COALESCE(SUM(service_fee), 0) as total_service_fee
        FROM bill_of_lading 
        WHERE created_at >= %s AND created_at < %s
    """, (start_date, end_date))
    summary = cur.fetchone()
    cur.execute("""
        SELECT 
            id, customer_name, customer_email, 
            ctn_fee, service_fee, 
            COALESCE(ctn_fee + service_fee, 0) as total,
            created_at
        FROM bill_of_lading 
        WHERE created_at >= %s AND created_at < %s
        ORDER BY created_at DESC
    """, (start_date, end_date))
    entries = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify({
        'summary': {
            'total_entries': summary[0],
            'total_ctn_fee': float(summary[1]),
            'total_service_fee': float(summary[2])
        },
        'entries': entries
    })

@app.route('/api/upload', methods=['POST'])
@jwt_required()
def upload():
    user = json.loads(get_jwt_identity())
    username = user['username']

    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        bill_pdfs = request.files.getlist('bill_pdf')
        invoice_pdf = request.files.get('invoice_pdf')
        packing_pdf = request.files.get('packing_pdf')

        if not name:
            return jsonify({'error': 'Name is required'}), 400
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        if not phone:
            return jsonify({'error': 'Phone is required'}), 400
        if not bill_pdfs and not invoice_pdf and not packing_pdf:
            return jsonify({'error': 'At least one PDF file is required'}), 400

        def save_file_with_timestamp(file, label):
            if not file:
                return None
            now_str = datetime.now(pytz.timezone('Asia/Hong_Kong')).strftime('%Y-%m-%d_%H%M%S')
            filename = f"{now_str}_{label}_{file.filename}"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            print(f"Debug: Requested {filename} from {file_path}")
            file.save(file_path)
            return filename

        uploaded_count = 0
        results = []

        customer_invoice = save_file_with_timestamp(invoice_pdf, 'invoice') if invoice_pdf else None
        customer_packing_list = save_file_with_timestamp(packing_pdf, 'packing') if packing_pdf else None

        if bill_pdfs:
            for bill_pdf in bill_pdfs:
                pdf_filename = save_file_with_timestamp(bill_pdf, 'bill')
                fields = {}

                if bill_pdf:
                    pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
                    fields = extract_fields(pdf_path)

                # 🔍 Debug print
                print("flight_or_vessel:", fields.get("flight_or_vessel", ""))
                print("product_description:", fields.get("product_description", ""))

                fields_json = json.dumps(fields)
                hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()

                conn = get_db_conn()
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO bill_of_lading (
                        customer_name, customer_email, customer_phone, pdf_filename, ocr_text,
                        shipper, consignee, port_of_loading, port_of_discharge, bl_number, container_numbers,
                        flight_or_vessel, product_description, status,
                        customer_username, created_at, customer_invoice, customer_packing_list
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    name, str(email), str(phone), pdf_filename, fields_json,
                    str(fields.get('shipper', '')),
                    str(fields.get('consignee', '')),
                    str(fields.get('port_of_loading', '')),
                    str(fields.get('port_of_discharge', '')),
                    str(fields.get('bl_number', '')),
                    str(fields.get('container_numbers', '')),
                    str(fields.get('flight_or_vessel', '')),
                    str(fields.get('product_description', '')),
                    "Pending",
                    username,
                    hk_now,
                    customer_invoice,
                    customer_packing_list
                ))
                conn.commit()
                cur.close()
                conn.close()
                uploaded_count += 1
        else:
            hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO bill_of_lading (
                    customer_name, customer_email, customer_phone, pdf_filename, ocr_text,
                    shipper, consignee, port_of_loading, port_of_discharge, bl_number, container_numbers, status,
                    customer_username, created_at, customer_invoice, customer_packing_list
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                name, str(email), str(phone), None, None,
                '', '', '', '', '', '',
                "Pending",
                username,
                hk_now,
                customer_invoice,
                customer_packing_list
            ))
            conn.commit()
            cur.close()
            conn.close()
            uploaded_count += 1

        try:
            if EmailConfig.SMTP_SERVER and EmailConfig.SMTP_USERNAME and EmailConfig.SMTP_PASSWORD:
                subject = "We have received your Bill of Lading"
                body = f"Dear {name},\n\nWe have received your documents. Our team will be in touch with you within 24 hours.\n\nThank you!"
                send_simple_email(email, subject, body)
        except Exception as e:
            print(f"Failed to send confirmation email: {str(e)}")

        return jsonify({'message': f'Upload successful! {uploaded_count} bill(s) uploaded.'})

    except Exception as e:
        print(f"Error processing upload: {str(e)}")
        return jsonify({'error': f'Error processing upload: {str(e)}'}), 400


@app.route('/api/bills', methods=['GET'])
def get_bills():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 50))
    offset = (page - 1) * page_size
    bl_number = request.args.get('bl_number')
    status = request.args.get('status')
    date = request.args.get('date')
    conn = get_db_conn()
    cur = conn.cursor()

    # Build WHERE clause
    where_clauses = []
    params = []
    if bl_number:
        where_clauses.append('bl_number ILIKE %s')
        params.append(f'%{bl_number}%')
    if status:
        where_clauses.append('status = %s')
        params.append(status)
    if date:
        start_date, end_date = get_hk_date_range(date)
        where_clauses.append('created_at >= %s AND created_at < %s')
        params.extend([start_date, end_date])
    where_sql = ' AND '.join(where_clauses)
    if where_sql:
        where_sql = 'WHERE ' + where_sql

    # Get total count for pagination
    count_query = f'SELECT COUNT(*) FROM bill_of_lading {where_sql}'
    cur.execute(count_query, tuple(params))
    total_count = cur.fetchone()[0]

    # Get paginated results
    query = f'''
        SELECT id, customer_name, customer_email, customer_phone, pdf_filename, shipper, consignee, port_of_loading, port_of_discharge, bl_number, container_numbers,
               flight_or_vessel, product_description,  -- <-- add here
               service_fee, ctn_fee, payment_link, receipt_filename, status, invoice_filename, unique_number, created_at, receipt_uploaded_at, customer_username, customer_invoice, customer_packing_list
        FROM bill_of_lading
        {where_sql}
        ORDER BY id DESC
        LIMIT %s OFFSET %s
    '''
    cur.execute(query, tuple(params) + (page_size, offset))
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    bills = []
    for row in rows:
        bill_dict = dict(zip(columns, row))
        # Decrypt email and phone
        if bill_dict.get('customer_email') is not None:
            bill_dict['customer_email'] = decrypt_sensitive_data(bill_dict['customer_email'])
        if bill_dict.get('customer_phone') is not None:
            bill_dict['customer_phone'] = decrypt_sensitive_data(bill_dict['customer_phone'])
        bills.append(bill_dict)

    cur.close()
    conn.close()

    return jsonify({
        'bills': bills,
        'total': total_count,
        'page': page,
        'page_size': page_size
    })

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    from urllib.parse import unquote
    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_root = os.path.join(base_dir, UPLOAD_FOLDER)
    safe_filename = unquote(filename)
    full_path = os.path.join(upload_root, safe_filename)
    print(f"Debug: Serving {safe_filename} from {full_path}, Exists: {os.path.exists(full_path)}")
    try:
        response = send_from_directory(upload_root, safe_filename)
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRF-TOKEN'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        if 'X-Frame-Options' in response.headers:
            del response.headers['X-Frame-Options']
        if safe_filename.lower().endswith('.pdf'):
            response.headers['Content-Type'] = 'application/pdf'
        return set_csp_header(response)
    except FileNotFoundError:
        print(f"Error: File not found at {full_path}")
        return "File not found", 404

# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     from urllib.parse import unquote
#     base_dir = os.path.dirname(os.path.abspath(__file__))
#     upload_root = os.path.join(base_dir, UPLOAD_FOLDER)
#     # Decode URL-encoded filenames (for spaces/special chars)
#     safe_filename = unquote(filename)
#     full_path = os.path.join(upload_root, safe_filename)
#     print(f"Debug: Requested {filename} (decoded: {safe_filename}), Base dir: {base_dir}, Upload root: {upload_root}, Full path: {full_path}, Exists: {os.path.exists(full_path)}")
#     try:
#         response = send_from_directory(upload_root, safe_filename)
#         # Remove X-Frame-Options header if present
#         if 'X-Frame-Options' in response.headers:
#             del response.headers['X-Frame-Options']
#         # Set CORS headers for allowed origins
#         origin = request.headers.get('Origin')
#         if origin in allowed_origins:
#             response.headers['Access-Control-Allow-Origin'] = origin
#             response.headers['Vary'] = 'Origin'
#             response.headers['Access-Control-Allow-Credentials'] = 'true'
#         # Set Content-Type for PDFs
#         if safe_filename.lower().endswith('.pdf'):
#             response.headers['Content-Type'] = 'application/pdf'
#         return set_csp_header(response)
#     except FileNotFoundError:
#         return "File not found", 404
    
# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/bill/<int:bill_id>/upload_receipt', methods=['POST'])
def upload_receipt(bill_id):
    if 'receipt' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    receipt = request.files['receipt']
    filename = f"receipt_{bill_id}_{receipt.filename}"
    receipt_path = os.path.join(UPLOAD_FOLDER, filename)
    receipt.save(receipt_path)

    hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE bill_of_lading
        SET receipt_filename=%s, status=%s, receipt_uploaded_at=%s
        WHERE id=%s
    """, (filename, 'Awaiting Bank In', hk_now, bill_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Receipt uploaded'})

@app.route('/api/bill/<int:bill_id>', methods=['GET', 'PUT'])
def bill_detail(bill_id):
    if request.method == 'GET':
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM bill_of_lading WHERE id=%s", (bill_id,))
        bill_row = cur.fetchone()
        if not bill_row:
            cur.close()
            conn.close()
            return jsonify({'error': 'Bill not found'}), 404
        columns = [desc[0] for desc in cur.description]
        bill = dict(zip(columns, bill_row))
        # Decrypt sensitive fields
        if bill.get('customer_email') is not None:
            bill['customer_email'] = decrypt_sensitive_data(bill['customer_email'])
        if bill.get('customer_phone') is not None:
            bill['customer_phone'] = decrypt_sensitive_data(bill['customer_phone'])
        cur.close()
        conn.close()
        return jsonify(bill)
    elif request.method == 'PUT':
        try:
            data = request.get_json()
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM bill_of_lading WHERE id=%s", (bill_id,))
            bill_row = cur.fetchone()
            if not bill_row:
                return jsonify({'error': 'Bill not found'}), 404
            columns = [desc[0] for desc in cur.description]
            bill = dict(zip(columns, bill_row))
            # Allow updating all relevant fields, including new ones
            updatable_fields = [
                'customer_name', 'customer_email', 'customer_phone', 'bl_number',
                'shipper', 'consignee', 'port_of_loading', 'port_of_discharge',
                'container_numbers', 'service_fee', 'ctn_fee', 'payment_link', 'unique_number',
                'flight_or_vessel', 'product_description',
                'payment_method', 'payment_status', 'reserve_status'  # <-- new fields
            ]
            update_fields = []
            update_values = []
            for field in updatable_fields:
                if field in data and data[field] is not None:
                    if field == 'customer_email':
                        update_fields.append(f"{field}=%s")
                        update_values.append(encrypt_sensitive_data(data[field]))
                    elif field == 'customer_phone':
                        update_fields.append(f"{field}=%s")
                        update_values.append(encrypt_sensitive_data(data[field]))
                    else:
                        update_fields.append(f"{field}=%s")
                        update_values.append(data[field])
            if update_fields:
                update_values.append(bill_id)
                update_query = f"""
                    UPDATE bill_of_lading
                    SET {', '.join(update_fields)}
                    WHERE id=%s
                """
                cur.execute(update_query, tuple(update_values))
                conn.commit()
            # Fetch updated bill
            cur.execute("SELECT * FROM bill_of_lading WHERE id=%s", (bill_id,))
            bill_row = cur.fetchone()
            columns = [desc[0] for desc in cur.description]
            bill = dict(zip(columns, bill_row))
            # Decrypt sensitive fields
            if bill.get('customer_email') is not None:
                bill['customer_email'] = decrypt_sensitive_data(bill['customer_email'])
            if bill.get('customer_phone') is not None:
                bill['customer_phone'] = decrypt_sensitive_data(bill['customer_phone'])
            # Regenerate invoice PDF if relevant fields changed
            customer = {
                'name': bill['customer_name'],
                'email': bill['customer_email'],
                'phone': bill['customer_phone']
            }
            try:
                invoice_filename = generate_invoice_pdf(customer, bill, bill.get('service_fee'), bill.get('ctn_fee'), bill.get('payment_link'))
                bill['invoice_filename'] = invoice_filename
            except Exception as e:
                print(f"Error generating invoice PDF: {str(e)}")
            cur.close()
            conn.close()
            return jsonify(bill)
        except Exception as e:
            import traceback
            print(f"Error in PUT /api/bills/{{bill_id}}: {str(e)}\n{traceback.format_exc()}")
            return jsonify({'error': f'Error updating bill: {str(e)}'}), 400
    
@app.route('/api/bill/<int:bill_id>/settle_reserve', methods=['POST'])
@jwt_required()
def settle_reserve(bill_id):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        # Check if bill exists
        cur.execute("SELECT id FROM bill_of_lading WHERE id = %s", (bill_id,))
        if not cur.fetchone():
            return jsonify({"error": "Bill not found"}), 404

        # Update reserve_status field to 'Reserve Settled'
        cur.execute("""
            UPDATE bill_of_lading
            SET reserve_status = 'Reserve Settled'
            WHERE id = %s
        """, (bill_id,))
        conn.commit()
        return jsonify({"message": "Reserve marked as settled"}), 200
    except Exception as e:
        print(f"Error settling reserve: {e}")
        return jsonify({"error": "Failed to settle reserve"}), 500
    finally:
        cur.close()
        conn.close()   


@app.route('/api/bill/<int:bill_id>/complete', methods=['POST'])
def complete_bill(bill_id):
    conn = get_db_conn()
    cur = conn.cursor()
    hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
    # Check payment_method for this bill
    cur.execute("SELECT payment_method FROM bill_of_lading WHERE id=%s", (bill_id,))
    row = cur.fetchone()
    if row and row[0] and row[0].lower() == 'allinpay':
        # For Allinpay, also update payment_status to 'Paid 100%'
        cur.execute("""
            UPDATE bill_of_lading
            SET status=%s, payment_status=%s, completed_at=%s
            WHERE id=%s
        """, ('Paid and CTN Valid', 'Paid 100%', hk_now, bill_id))
    else:
        # For others, just update status and completed_at
        cur.execute("""
            UPDATE bill_of_lading
            SET status=%s, completed_at=%s
            WHERE id=%s
        """, ('Paid and CTN Valid', hk_now, bill_id))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Bill marked as completed'})



@app.route('/api/search_bills', methods=['POST'])
@jwt_required()
def search_bills():
    data = request.get_json()
    customer_name = data.get('customer_name', '')
    customer_id = data.get('customer_id', '')
    created_at = data.get('created_at', '')
    bl_number = data.get('bl_number', '')
    unique_number = data.get('unique_number', '')  # Add support for CTN number search
    username = data.get('username', '')  # Add support for username search
    
    conn = get_db_conn()
    cur = conn.cursor()
    
    query = '''
        SELECT id, customer_name, customer_email, customer_phone, pdf_filename, shipper, consignee, port_of_loading, port_of_discharge, bl_number, container_numbers, service_fee, ctn_fee, payment_link, receipt_filename, status, invoice_filename, unique_number, created_at, receipt_uploaded_at, customer_username, customer_invoice, customer_packing_list
        FROM bill_of_lading
        WHERE 1=1
    '''
    params = []
    
    if customer_name:
        query += ' AND customer_name ILIKE %s'
        params.append(f'%{customer_name}%')
    
    if customer_id:
        # Validate that customer_id is a number
        try:
            int(customer_id)
            query += ' AND id = %s'
            params.append(customer_id)
        except ValueError:
            # If not a number, search by customer name instead
            query += ' AND customer_name ILIKE %s'
            params.append(f'%{customer_id}%')
    
    if created_at:
        # Use timezone-aware date range for created_at
        start_date, end_date = get_hk_date_range(created_at)
        query += ' AND created_at >= %s AND created_at < %s'
        params.extend([start_date, end_date])
    
    if bl_number:
        query += ' AND bl_number ILIKE %s'
        params.append(f'%{bl_number}%')
    
    if unique_number:
        query += ' AND unique_number = %s'
        params.append(unique_number)
    
    if username:
        query += ' AND customer_username = %s'
        params.append(username)
    
    query += ' ORDER BY id DESC'
    
    cur.execute(query, params)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    
    bills = []
    for row in rows:
        bill_dict = dict(zip(columns, row))
        # Decrypt email and phone
        if bill_dict.get('customer_email') is not None:
            bill_dict['customer_email'] = decrypt_sensitive_data(bill_dict['customer_email'])
        if bill_dict.get('customer_phone') is not None:
            bill_dict['customer_phone'] = decrypt_sensitive_data(bill_dict['customer_phone'])
        bills.append(bill_dict)
    
    cur.close()
    conn.close()
    return jsonify(bills)

@app.route('/api/bill/<int:bill_id>/unique_number', methods=['POST'])
def set_unique_number(bill_id):
    data = request.get_json()
    unique_number = data.get('unique_number')
    if not unique_number:
        return jsonify({'error': 'Missing unique number'}), 400

    # Update DB
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""
        UPDATE bill_of_lading
        SET unique_number=%s
        WHERE id=%s
    """, (unique_number, bill_id))
    conn.commit()

    # Fetch customer email
    cur.execute("SELECT customer_email, customer_name FROM bill_of_lading WHERE id=%s", (bill_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        customer_email, customer_name = row
        # Send email
        send_unique_number_email(customer_email, customer_name, unique_number)

    return jsonify({'message': 'Unique number saved and email sent'})

@app.route('/api/send_unique_number_email', methods=['POST'])
def api_send_unique_number_email():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        to_email = data.get('to_email')
        subject = data.get('subject')
        body = data.get('body')
        bill_id = data.get('bill_id')

        if not all([to_email, subject, body, bill_id]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Validate bill_id exists
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM bill_of_lading WHERE id=%s", (bill_id,))
        if not cur.fetchone():
            return jsonify({'error': 'Bill not found'}), 404

        # Send email
        send_unique_number_email(to_email, subject, body)

        return jsonify({'message': 'Unique number email sent successfully'}), 200

    except Exception as e:
        print(f"Error in send_unique_number_email: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/me', methods=['GET'])
@jwt_required()
def get_me():
    user = json.loads(get_jwt_identity())
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT customer_name, customer_email, customer_phone, username, role FROM users WHERE username=%s", (user['username'],))
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        decrypted_email = decrypt_sensitive_data(row[1]) if row[1] is not None else ''
        decrypted_phone = decrypt_sensitive_data(row[2]) if row[2] is not None else ''
        return jsonify({
            "customer_name": row[0],
            "customer_email": decrypted_email,
            "customer_phone": decrypted_phone,
            "username": row[3],
            "role": row[4]
        })
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/api/bill/<int:bill_id>', methods=['DELETE'])
@jwt_required()
def delete_bill(bill_id):
    user = json.loads(get_jwt_identity())
    if user['role'] not in ['staff', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM bill_of_lading WHERE id=%s", (bill_id,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Bill deleted'})

@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')
    if not all([name, email, message]):
        return jsonify({'error': 'Missing fields'}), 400
    try:
        success = send_contact_email(name, email, message)
        if success:
            return jsonify({'message': 'Message sent successfully!'})
        else:
            return jsonify({'error': 'Failed to send email'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats/summary')
@jwt_required()
def stats_summary():
    user = json.loads(get_jwt_identity())
    if user['role'] not in ['staff', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db_conn()
    cur = conn.cursor()

    # Total bills
    cur.execute("SELECT COUNT(*) FROM bill_of_lading")
    total_bills = cur.fetchone()[0]

    # Completed = Paid and CTN Valid
    cur.execute("SELECT COUNT(*) FROM bill_of_lading WHERE status = 'Paid and CTN Valid'")
    completed_bills = cur.fetchone()[0]

    # Pending = Pending
    cur.execute("""
    SELECT COUNT(*) 
    FROM bill_of_lading 
    WHERE status IN ('Pending', 'Invoice Sent', 'Awaiting Bank In')
""")
    pending_bills = cur.fetchone()[0]

    # ✅ Total invoice amount = sum(ctn_fee + service_fee)
    cur.execute("SELECT COALESCE(SUM(ctn_fee + service_fee), 0) FROM bill_of_lading")
    total_invoice_amount = float(cur.fetchone()[0] or 0)

    # ✅ Total Payment Received (Bank + Allinpay 100% + Allinpay 85%)
    cur.execute("""
        SELECT COALESCE(SUM(
            CASE 
                WHEN payment_method != 'Allinpay' AND status = 'Paid and CTN Valid'
                    THEN ctn_fee + service_fee
                WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Reserve Settled'
                    THEN ctn_fee + service_fee
                WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Unsettled'
                    THEN (ctn_fee * 0.85) + (service_fee * 0.85)
                ELSE 0
            END
        ), 0)
        FROM bill_of_lading
    """)
    total_payment_received = float(cur.fetchone()[0] or 0)

    # ✅ Total Payment Outstanding = Awaiting Bank In + reserve_amount (unsettled)
    cur.execute("""
    SELECT COALESCE(SUM(service_fee + ctn_fee), 0)
    FROM bill_of_lading
    WHERE status IN ('Awaiting Bank In', 'Invoice Sent')
""")
    awaiting_payment = float(cur.fetchone()[0] or 0)

    cur.execute("SELECT COALESCE(SUM(reserve_amount), 0) FROM bill_of_lading WHERE LOWER(TRIM(reserve_status)) = 'unsettled'")
    unsettled_reserve = float(cur.fetchone()[0] or 0)

    total_payment_outstanding = awaiting_payment + unsettled_reserve

    cur.close()
    conn.close()

    return jsonify({
        'total_bills': total_bills,
        'completed_bills': completed_bills,
        'pending_bills': pending_bills,
        'total_invoice_amount': round(total_invoice_amount, 2),
        'total_payment_received': round(total_payment_received, 2),
        'total_payment_outstanding': round(total_payment_outstanding, 2)
    })



@app.route('/api/stats/outstanding_bills')
@jwt_required()
def outstanding_bills():
    user = json.loads(get_jwt_identity())
    if user['role'] not in ['staff', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403

    conn = get_db_conn()
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            id, customer_name, bl_number,
            ctn_fee, service_fee, reserve_amount,
            payment_method, reserve_status, invoice_filename
        FROM bill_of_lading
        WHERE status IN ('Awaiting Bank In', 'Invoice Sent')
           OR (payment_method = 'Allinpay' AND LOWER(TRIM(reserve_status)) = 'unsettled')
    """)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    bills = []
    for row in rows:
        bill = dict(zip(columns, row))

        ctn_fee = float(bill.get('ctn_fee') or 0)
        service_fee = float(bill.get('service_fee') or 0)

        # Force lowercase + trim for reliability
        payment_method = str(bill.get('payment_method') or '').strip().lower()
        reserve_status = str(bill.get('reserve_status') or '').strip().lower()

        # Default: full invoice amount
        outstanding_amount = round(ctn_fee + service_fee, 2)

        # Adjust for Allinpay Unsettled (15%)
        if payment_method == 'allinpay' and reserve_status == 'unsettled':
            outstanding_amount = round(ctn_fee * 0.15 + service_fee * 0.15, 2)

        # Debug log to console
        print("DEBUG BILL:", {
            "bl_number": bill.get("bl_number"),
            "payment_method": payment_method,
            "reserve_status": reserve_status,
            "ctn_fee": ctn_fee,
            "service_fee": service_fee,
            "calculated_outstanding": outstanding_amount,
        })

        bill['outstanding_amount'] = outstanding_amount
        bills.append(bill)

    cur.close()
    conn.close()
    return jsonify(bills)

@app.route('/api/request_password_reset', methods=['POST'])
def request_password_reset():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email required'}), 400

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, customer_name, customer_email FROM users")
    users = cur.fetchall()
    user = None
    for row in users:
        user_id, customer_name, encrypted_email = row
        try:
            decrypted_email = decrypt_sensitive_data(encrypted_email)
            if decrypted_email == email:
                user = (user_id, customer_name)
                break
        except Exception as e:
            continue
    if not user:
        cur.close()
        conn.close()
        return jsonify({'message': 'If this email is registered, a reset link will be sent.'})  # Don't reveal user existence

    user_id, customer_name = user
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(pytz.timezone('Asia/Hong_Kong')) + timedelta(hours=1)
    cur.execute("INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)", (user_id, token, expires_at))
    conn.commit()
    cur.close()
    conn.close()

    reset_link = f"https://www.terryraylogicticsco.xyz/reset-password/{token}"
    subject = "Password Reset Request"
    body = f"Dear {customer_name},\n\nClick the link below to reset your password:\n{reset_link}\n\nThis link will expire in 1 hour."
    send_simple_email(email, subject, body)
    return jsonify({'message': 'If this email is registered, a reset link will be sent.'})

@app.route('/api/reset_password/<token>', methods=['POST'])
@limiter.limit("3 per hour")
def reset_password(token):
    data = request.get_json()
    new_password = data.get('password')
    captcha_token = data.get('captcha_token')
    if not new_password:
        return jsonify({'error': 'Password required'}), 400
    if not verify_captcha(captcha_token):
        return jsonify({'error': 'CAPTCHA verification failed'}), 400
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, expires_at FROM password_reset_tokens WHERE token=%s", (token,))
    row = cur.fetchone()
    if not row:
        cur.close()
        conn.close()
        return jsonify({'error': 'Invalid or expired token'}), 400

    user_id, expires_at = row
    if datetime.now(pytz.timezone('Asia/Hong_Kong')) > expires_at:
        cur.execute("DELETE FROM password_reset_tokens WHERE token=%s", (token,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'error': 'Token expired'}), 400
    password_hash = generate_password_hash(new_password)
    cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (password_hash, user_id))
    cur.execute("DELETE FROM password_reset_tokens WHERE token=%s", (token,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Password has been reset successfully.'})

@app.route('/api/send_invoice_email', methods=['POST'])
@jwt_required()
def send_invoice_email_endpoint():
    try:
        data = request.get_json()
        to_email = data.get('to_email')
        subject = data.get('subject')
        body = data.get('body')
        pdf_url = data.get('pdf_url')
        bill_id = data.get('bill_id')

        if not all([to_email, subject, body, pdf_url, bill_id]):
            return jsonify({'error': 'Missing required fields'}), 400

        # Fix: Extract just the filename if pdf_url is a full URL
        import os
        if pdf_url.startswith('http://') or pdf_url.startswith('https://'):
            pdf_filename = os.path.basename(pdf_url)
        else:
            pdf_filename = pdf_url.lstrip('/')
        pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', pdf_filename)
        
        # Send the email
        success = send_invoice_email(to_email, subject, body, pdf_path)
        
        if success:
            # Update bill status to "Invoice Sent"
            conn = get_db_conn()
            cur = conn.cursor()
            cur.execute("UPDATE bill_of_lading SET status=%s WHERE id=%s", ("Invoice Sent", bill_id))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({'message': 'Email sent successfully'})
        else:
            return jsonify({'error': 'Failed to send email'}), 500
            
    except Exception as e:
        print(f"Error sending invoice email: {str(e)}")
        return jsonify({'error': str(e)}), 500

        return jsonify({'error': str(e)}), 500

# Helper function for timezone-aware date queries
def get_hk_date_range(search_date_str):
    """
    Convert a date string (YYYY-MM-DD) to Hong Kong timezone range for database queries.
    Returns (start_datetime, end_datetime) in Hong Kong timezone.
    """
    hk_tz = pytz.timezone('Asia/Hong_Kong')
    search_date = datetime.strptime(search_date_str, '%Y-%m-%d')
    search_date = hk_tz.localize(search_date)
    next_date = search_date + timedelta(days=1)
    return search_date, next_date

@app.route('/api/account_bills', methods=['GET'])
def account_bills():
    completed_at = request.args.get('completed_at')
    bl_number = request.args.get('bl_number')

    conn = get_db_conn()
    cur = conn.cursor()

    # Build base query
    select_clause = '''
        SELECT id, customer_name, customer_email, customer_phone, pdf_filename,
               shipper, consignee, port_of_loading, port_of_discharge, bl_number,
               container_numbers, service_fee, ctn_fee, payment_link, receipt_filename,
               status, invoice_filename, unique_number, created_at, receipt_uploaded_at,
               completed_at, allinpay_85_received_at,
               customer_username, customer_invoice, customer_packing_list,
               payment_method, payment_status, reserve_status
        FROM bill_of_lading
        WHERE status = 'Paid and CTN Valid'
    '''

    where_clauses = []
    params = []

    if completed_at:
        start_date, end_date = get_hk_date_range(completed_at)
        print("DEBUG: start_date", start_date, "end_date", end_date)
        where_clauses.append(
            "((payment_method = 'Allinpay' AND allinpay_85_received_at >= %s AND allinpay_85_received_at < %s) "
            "OR (payment_method = 'Allinpay' AND completed_at >= %s AND completed_at < %s) "
            "OR (payment_method != 'Allinpay' AND completed_at >= %s AND completed_at < %s))"
        )
        params.extend([start_date, end_date, start_date, end_date, start_date, end_date])
    if bl_number:
        where_clauses.append("bl_number ILIKE %s")
        params.append(f'%{bl_number}%')

    if where_clauses:
        select_clause += " AND " + " AND ".join(where_clauses)

    select_clause += " ORDER BY id DESC"

    cur.execute(select_clause, tuple(params))
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]

    bills = []
    total_bank_ctn = 0
    total_bank_service = 0
    total_allinpay_85_ctn = 0
    total_allinpay_85_service = 0
    total_reserve_ctn = 0
    total_reserve_service = 0

    for row in rows:
        bill = dict(zip(columns, row))

        # Decrypt sensitive fields
        if bill.get('customer_email'):
            bill['customer_email'] = decrypt_sensitive_data(bill['customer_email'])
        if bill.get('customer_phone'):
            bill['customer_phone'] = decrypt_sensitive_data(bill['customer_phone'])

        try:
            ctn_fee = float(bill.get('ctn_fee') or 0)
            service_fee = float(bill.get('service_fee') or 0)
        except (TypeError, ValueError):
            ctn_fee = 0
            service_fee = 0

        # Default: show original values
        bill['display_ctn_fee'] = ctn_fee
        bill['display_service_fee'] = service_fee

        # 85%/15% logic for Allinpay
        if bill.get('payment_method') == 'Allinpay':
            allinpay_85_dt = bill.get('allinpay_85_received_at')
            is_85 = False
            if allinpay_85_dt:
                if isinstance(allinpay_85_dt, str):
                    try:
                        allinpay_85_dt = parser.isoparse(allinpay_85_dt)
                    except Exception:
                        allinpay_85_dt = None
                if allinpay_85_dt and allinpay_85_dt.tzinfo is None:
                    allinpay_85_dt = allinpay_85_dt.replace(tzinfo=pytz.UTC)
                if completed_at and allinpay_85_dt and start_date <= allinpay_85_dt < end_date:
                    total_allinpay_85_ctn += bill['display_ctn_fee']
                    total_allinpay_85_service += bill['display_service_fee']
                    is_85 = True
            reserve_status = (bill.get('reserve_status') or '').lower()
            completed_dt = bill.get('completed_at')
            if completed_dt:
                if isinstance(completed_dt, str):
                    try:
                        completed_dt = parser.isoparse(completed_dt)
                    except Exception:
                        completed_dt = None
                if completed_dt and completed_dt.tzinfo is None:
                    completed_dt = completed_dt.replace(tzinfo=pytz.UTC)
            if reserve_status in ['settled', 'reserve settled'] and completed_at and completed_dt and start_date <= completed_dt < end_date and not is_85:
                bill['display_ctn_fee'] = round(ctn_fee * 0.15, 2)
                bill['display_service_fee'] = round(service_fee * 0.15, 2)
                total_reserve_ctn += bill['display_ctn_fee']
                total_reserve_service += bill['display_service_fee']
        else:
            # Bank Transfer: always show full amount, but only count in summary if in date range
            completed_dt = bill.get('completed_at')
            if completed_dt:
                if isinstance(completed_dt, str):
                    try:
                        completed_dt = parser.isoparse(completed_dt)
                    except Exception:
                        completed_dt = None
                if completed_dt and completed_dt.tzinfo is None:
                    completed_dt = completed_dt.replace(tzinfo=pytz.UTC)
            if completed_at and completed_dt and start_date <= completed_dt < end_date:
                total_bank_ctn += ctn_fee
                total_bank_service += service_fee

        bills.append(bill)

    summary = {
        'totalEntries': len(bills),
        'totalCtnFee': round(total_bank_ctn + total_allinpay_85_ctn + total_reserve_ctn, 2),
        'totalServiceFee': round(total_bank_service + total_allinpay_85_service + total_reserve_service, 2),
        'bankTotal': round(total_bank_ctn + total_bank_service, 2),
        'allinpay85Total': round(total_allinpay_85_ctn + total_allinpay_85_service, 2),
        'reserveTotal': round(total_reserve_ctn + total_reserve_service, 2)
    }

    cur.close()
    conn.close()

    return jsonify({'bills': bills, 'summary': summary})


@app.route('/api/generate_payment_link/<int:bill_id>', methods=['POST'])
def generate_payment_link(bill_id):
    try:
        # Simulate link (replace with real Allinpay/Stripe call later)
        payment_link = f"https://pay.example.com/link/{bill_id}"

        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("UPDATE bill_of_lading SET payment_link = %s WHERE id = %s", (payment_link, bill_id))
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"payment_link": payment_link})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/bills/status/<status>', methods=['GET'])
def get_bills_by_status(status):
    conn = get_db_conn()
    cur = conn.cursor()
    
    cur.execute('''
        SELECT id, customer_name, customer_email, customer_phone, pdf_filename, shipper, consignee, port_of_loading, port_of_discharge, bl_number, container_numbers, service_fee, ctn_fee, payment_link, receipt_filename, status, invoice_filename, unique_number, created_at, receipt_uploaded_at, customer_username, customer_invoice, completed_at, customer_packing_list
        FROM bill_of_lading
        WHERE status = %s
        ORDER BY id DESC
    ''', (status,))
    
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    bills = []
    for row in rows:
        bill_dict = dict(zip(columns, row))
        # Decrypt email and phone
        if bill_dict.get('customer_email') is not None:
            bill_dict['customer_email'] = decrypt_sensitive_data(bill_dict['customer_email'])
        if bill_dict.get('customer_phone') is not None:
            bill_dict['customer_phone'] = decrypt_sensitive_data(bill_dict['customer_phone'])
        bills.append(bill_dict)

    cur.close()
    conn.close()  
    return jsonify(bills)

@app.route('/api/bills/awaiting_bank_in', methods=['GET'])
@jwt_required()
def get_awaiting_bank_in_bills():
    try:
        bl_number = request.args.get('bl_number', '').strip()
        conn = get_db_conn()
        cur = conn.cursor()

        where_clauses = []
        params = []

        # Remove reserve_status filter!
        # Only filter by status/payment_method and optional bl_number
        if bl_number:
            where_clauses.append(
                "((status = 'Awaiting Bank In' AND bl_number ILIKE %s) OR "
                "(payment_method = 'Allinpay' AND payment_status = 'Paid 85%' AND bl_number ILIKE %s))"
            )
            params.extend([f"%{bl_number}%", f"%{bl_number}%"])
        else:
            where_clauses.append(
                "((status = 'Awaiting Bank In') OR "
                "(payment_method = 'Allinpay' AND payment_status = 'Paid 85%'))"
            )

        where_sql = " AND ".join(where_clauses)
        query = (
            "SELECT * FROM bill_of_lading "
            "WHERE " + where_sql + " "
            "ORDER BY id DESC"
        )

        if params:
            cur.execute(query, tuple(params))
        else:
            cur.execute(query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        bills = []
        for row in rows:
            bill_dict = dict(zip(columns, row))
            # Decrypt email and phone if needed
            if bill_dict.get('customer_email') is not None:
                bill_dict['customer_email'] = decrypt_sensitive_data(bill_dict['customer_email'])
            if bill_dict.get('customer_phone') is not None:
                bill_dict['customer_phone'] = decrypt_sensitive_data(bill_dict['customer_phone'])
            bills.append(bill_dict)

        return jsonify({'bills': bills, 'total': len(bills)})
    except Exception as e:
        print("❌ ERROR in awaiting_bank_in:", str(e))
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass



@app.route('/api/request_username', methods=['POST'])
def request_username():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Email is required'}), 400

    conn = get_db_conn()
    cur = conn.cursor()

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT username, customer_email FROM users")
    users = cur.fetchall()
    cur.close()
    conn.close()

    username = None
    for row in users:
        db_username, encrypted_email = row
        try:
            decrypted_email = decrypt_sensitive_data(encrypted_email)
            decrypted_email = decrypt_sensitive_data(encrypted_email)
            if decrypted_email == email:
                username = db_username
                break
        except Exception:
            continue

    if not username:
        return jsonify({'error': 'No user found with this email'}), 404
    username = None
    for row in users:
        db_username, encrypted_email = row
        try:
            decrypted_email = decrypt_sensitive_data(encrypted_email)
            decrypted_email = decrypt_sensitive_data(encrypted_email)
            if decrypted_email == email:
                username = db_username
                break
        except Exception:
            continue

    if not username:
        return jsonify({'error': 'No user found with this email'}), 404

    subject = "Your Username Recovery Request"
    body = f"Hi,\n\nYour username is: {username}\n\nIf you did not request this, please ignore this email.\n\nThanks,\nSupport Team"

    try:
        send_simple_email(email, subject, body)
        return jsonify({'message': 'Username sent to your email'}), 200
    except Exception as e:
        return jsonify({'error': f'Email failed: {str(e)}'}), 500

@app.route('/api/notify_new_user', methods=['POST'])
def notify_new_user():
    data = request.get_json()
    customer_username = data.get('username')  # from frontend it's still called 'username'
    email = data.get('email')
    role = data.get('role')

    # Replace with your actual admin email
    admin_email = 'ray6330099@gmail.com'
    subject = f"📬 New User Registration: {customer_username}"
    body = f"""Hi Admin,

A new user has just registered on the system.

Username: {customer_username}
Email: {email}
Role: {role}

You can log in to review and approve the user if necessary.

Best regards,
Your System
"""
    try:
        send_simple_email(admin_email, subject, body)
        return jsonify({'message': 'Notification email sent'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- LOGOUT ENDPOINT ---
from flask_jwt_extended import unset_jwt_cookies

@app.route('/api/logout', methods=['POST'])
def logout():
    response = jsonify({'message': 'Logged out successfully'})
    unset_jwt_cookies(response)
    return response, 200


# @app.route('/api/logout', methods=['POST'])
# @jwt_required()
# def logout():
#     response = jsonify({'message': 'Logged out successfully'})
#     unset_jwt_cookies(response)
#     return response, 200

# --- CSRF TOKEN ENDPOINT (for frontend to fetch CSRF token) ---
from flask_jwt_extended import get_jwt
@app.route('/api/csrf-token', methods=['GET'])
@jwt_required()
def csrf_token():
    csrf_token = get_jwt()['csrf']
    return jsonify({'csrf_token': csrf_token})

# --- GENERIC ERROR HANDLERS ---
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# --- HTTPS Enforcement (production only) ---
@app.before_request
def enforce_https():
    from config import is_https_enforced
    import os
    is_development = os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == 'True'
    if not is_development and is_https_enforced() and not request.is_secure:
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)

        
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)

# import json
# from flask import Flask, request, jsonify, send_from_directory, make_response, redirect
# from flask_cors import CORS, cross_origin
# from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
# from werkzeug.security import generate_password_hash, check_password_hash
# import os
# from datetime import date, datetime, timedelta
# from invoice_utils import generate_invoice_pdf
# from email_utils import send_invoice_email, send_unique_number_email, send_contact_email, send_simple_email
# from dotenv import load_dotenv
# import secrets
# import psycopg2
# from config import DatabaseConfig, get_db_conn, EmailConfig
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from email.utils import formataddr
# import smtplib
# from flask_limiter import Limiter
# from flask_limiter.util import get_remote_address
# from cryptography.fernet import Fernet
# import re
# from extract_fields import extract_fields
# import pytz
# from werkzeug.middleware.proxy_fix import ProxyFix
# from dateutil import parser
# import requests

# load_dotenv()
# print("[DEBUG] JWT_SECRET_KEY loaded:", os.environ.get("JWT_SECRET_KEY"))

# # --- ENVIRONMENT-BASED COOKIE SECURITY CONFIG ---
# is_development = os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == 'True'

# # Set cookie security flags based on environment
# if is_development:
#     app_cookie_secure = False
#     app_cookie_samesite = 'Lax'
# else:
#     app_cookie_secure = True
#     app_cookie_samesite = 'None'

# # Disable Flask's default static file handler to ensure custom static route is used
# app = Flask(__name__, static_folder=None)
# app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY")
# app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
# app.config["JWT_COOKIE_SECURE"] = app_cookie_secure
# app.config["JWT_COOKIE_SAMESITE"] = app_cookie_samesite
# app.config["SESSION_COOKIE_SECURE"] = app_cookie_secure
# app.config["SESSION_COOKIE_SAMESITE"] = app_cookie_samesite
# UPLOAD_FOLDER = 'uploads'
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY")
# print("[DEBUG] Flask app initialized")
# jwt = JWTManager(app)
# print("[DEBUG] JWTManager initialized")

# def verify_captcha(token):
#     """Bypass reCAPTCHA verification (disabled for China compatibility)."""
#     # In production, implement actual reCAPTCHA verification here
#     return True

# # --- CORS and CSP CONFIGURATION ---

# # Get allowed origins from environment
# raw_origins = os.getenv('ALLOWED_ORIGINS', '')
# prod_domains = [o.strip() for o in raw_origins.split(',') if o.strip() and not o.startswith('http://localhost') and not o.startswith('http://127.0.0.1')]
# local_domains = [o.strip() for o in raw_origins.split(',') if o.strip() and (o.startswith('http://localhost') or o.startswith('http://127.0.0.1'))]

# is_development = os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == 'True'

# if is_development:
#     allowed_origins = prod_domains + local_domains
# else:
#     allowed_origins = prod_domains

# # Only one CORS(app, ...) call, with correct allowed_origins
# CORS(app, origins=allowed_origins, supports_credentials=True)

# # --- CSP HEADER ---
# def set_csp_header(response):
#     # Use environment variable for production domains
#     prod_csp_domains = ' '.join(prod_domains)
#     local_csp_domains = ' '.join(local_domains)
#     frame_src = f"'self' {prod_csp_domains}"
#     frame_ancestors = f"'self' {prod_csp_domains}"
#     if is_development and local_csp_domains:
#         frame_src += f" {local_csp_domains}"
#         frame_ancestors += f" {local_csp_domains}"
#     csp = (
#         "default-src 'self'; "
#         "img-src 'self' data:; "
#         "connect-src 'self' " + prod_csp_domains + (f" {local_csp_domains}" if is_development else '') + "; "
#         f"frame-src {frame_src}; "
#         f"frame-ancestors {frame_ancestors}; "
#         "script-src 'self'; "
#         "style-src 'self' 'unsafe-inline'; "
#         "object-src 'none';"
#     )
#     response.headers['Content-Security-Policy'] = csp
#     return response

# @app.after_request
# def apply_csp(response):
#     return set_csp_header(response)

# # # def set_csp_header(response):
# # #     # Allow scripts and styles from self and trusted CDN (adjust as needed)
# # #     csp = (
# # #         "default-src 'self'; "
# # #         "script-src 'self' https://www.terryraylogicticsco.xyz https://terryraylogicticsco.xyz https://rayray.onrender.com; "
# # #         "style-src 'self' https://fonts.googleapis.com; "
# # #         "img-src 'self' data: https://www.terryraylogicticsco.xyz https://terryraylogicticsco.xyz https://rayray.onrender.com; "
# # #         "font-src 'self' https://fonts.gstatic.com; "
# # #         "connect-src 'self' https://www.terryraylogicticsco.xyz https://terryraylogicticsco.xyz https://rayray.onrender.com http://localhost:3000 http://localhost:8000 http://127.0.0.1:8000; "
# # #         "frame-ancestors 'none'; "
# # #         "object-src 'none'; "
# # #         "base-uri 'self'; "
# # #     )
# # #     response.headers['Content-Security-Policy'] = csp
# # #     return response

# # # Set a secure Content-Security-Policy header for all responses
# # # @app.after_request
# # # def set_csp_header(response):
# # #     # Allow scripts and styles from self and trusted CDN (adjust as needed)
# # #     csp = (
# # #         "default-src 'self'; "
# # #         "script-src 'self' 'unsafe-inline' https://www.terryraylogicticsco.xyz https://terryraylogicticsco.xyz https://rayray.onrender.com; "
# # #         "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
# # #         "img-src 'self' data: https://www.terryraylogicticsco.xyz https://terryraylogicticsco.xyz https://rayray.onrender.com; "
# # #         "font-src 'self' https://fonts.gstatic.com; "
# # #         "connect-src 'self' https://www.terryraylogicticsco.xyz https://terryraylogicticsco.xyz https://rayray.onrender.com http://localhost:3000 http://localhost:8000 http://127.0.0.1:8000; "
# # #         "frame-ancestors 'none'; "
# # #         "object-src 'none'; "
# # #         "base-uri 'self'; "
# # #     )
# # #     response.headers['Content-Security-Policy'] = csp
# # #     return response

# # # Add ProxyFix middleware to handle X-Forwarded-For headers
# # # app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)


# @app.route('/static/<path:subpath>')
# def static_files(subpath):
#     static_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build', 'static'))
#     full_path = os.path.join(static_root, subpath)
#     if os.path.exists(full_path):
#         return send_from_directory(static_root, subpath)
#     else:
#         return "Static file not found", 404


# @app.route('/', defaults={'path': ''})
# @app.route('/<path:path>')
# def serve(path):
#     build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend', 'build'))
#     file_path = os.path.join(build_dir, path)

#     # static assets handled separately
#     if path.startswith('static/'):
#         return static_files(path[7:])
    
#     # serve actual files if they exist
#     if path and os.path.exists(file_path):
#         return send_from_directory(build_dir, path)
    
#     # fallback to index.html (React SPA routing)
#     return send_from_directory(build_dir, 'index.html')

# @app.route('/api/ping')
# def ping():
#     return {"message": "pong"}, 200


# # Initialize Rate Limiter with conditional limits based on environment
# is_development = os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_DEBUG') == 'True'

# if is_development:
#     # More lenient limits for development, in-memory storage
#     limiter = Limiter(
#         get_remote_address,
#         app=app,
#         default_limits=["1000 per day", "100 per hour"]
#     )
# else:
#     # Stricter limits for production, use Redis for persistent storage
#     limiter = Limiter(
#         get_remote_address,
#         app=app,
#         default_limits=["200 per day", "50 per hour"],
#         storage_uri="redis://localhost:6379"
#     )

# # Custom error handler for rate limiting
# @app.errorhandler(429)
# def ratelimit_handler(e):
#     return jsonify({
#         'error': 'Too many requests. Please wait before trying again.',
#         'retry_after': getattr(e, 'retry_after', 3600)  # Default to 1 hour
#     }), 429

# encryption_key = os.getenv('ENCRYPTION_KEY')
# if not encryption_key:
#     if is_development:
#         encryption_key = Fernet.generate_key()
#         print(f"Generated new encryption key: {encryption_key.decode()}")
#         print("Please add this to your .env file as ENCRYPTION_KEY=<key>")
#     else:
#         raise ValueError("ENCRYPTION_KEY must be set in production")
# else:
#     if isinstance(encryption_key, str):
#         encryption_key = encryption_key.encode()
# fernet = Fernet(encryption_key)


# # # Initialize Encryption
# # # Use a persistent key from environment variables, or generate one if not exists
# # encryption_key = os.getenv('ENCRYPTION_KEY')
# # if not encryption_key:
# #     # Generate a new key and save it (you should save this to your .env file)
# #     encryption_key = Fernet.generate_key()
# #     print(f"Generated new encryption key: {encryption_key.decode()}")
# #     print("Please add this to your .env file as ENCRYPTION_KEY=<key>")
# # else:
# #     # Convert string key to bytes if needed
# #     if isinstance(encryption_key, str):
# #         encryption_key = encryption_key.encode()

# # fernet = Fernet(encryption_key)

# # Security Helper Functions
# def validate_password(password):
#     if len(password) < 8:
#         return False, "Password must be at least 8 characters long"
#     if not any(c.isupper() for c in password):
#         return False, "Password must contain at least one uppercase letter"
#     if not any(c.islower() for c in password):
#         return False, "Password must contain at least one lowercase letter"
#     if not any(c.isdigit() for c in password):
#         return False, "Password must contain at least one number"
#     if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
#         return False, "Password must contain at least one special character"
#     return True, "Password is valid"

# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# def encrypt_sensitive_data(data):
#     if not data:
#         return data
#     try:
#         if isinstance(data, str):
#             return fernet.encrypt(data.encode()).decode()
#         return data
#     except Exception as e:
#         # In production, log this error securely if needed
#         return data

# def decrypt_sensitive_data(encrypted_data):
#     if not encrypted_data:
#         return encrypted_data
#     try:
#         if isinstance(encrypted_data, str) and encrypted_data.startswith('gAAAAA'):
#             try:
#                 return fernet.decrypt(encrypted_data.encode()).decode()
#             except Exception as decrypt_error:
#                 # In production, log this error securely if needed
#                 return encrypted_data
#         else:
#             return encrypted_data
#     except Exception as e:
#         # In production, log this error securely if needed
#         return encrypted_data

# def is_account_locked(cur, user_id):
#     """Check if the user's account is currently locked."""
#     cur.execute("SELECT lockout_until FROM users WHERE id=%s", (user_id,))
#     row = cur.fetchone()
#     if row and row[0]:
#         lockout_until = row[0]
#         now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
#         if lockout_until and now < lockout_until:
#             return True, lockout_until.isoformat()
#     return False, None

# def increment_failed_attempts(cur, user_id, max_attempts=5, lockout_minutes=15):
#     """Increment failed login attempts and lock account if threshold is reached."""
#     cur.execute("SELECT failed_attempts FROM users WHERE id=%s", (user_id,))
#     row = cur.fetchone()
#     failed_attempts = row[0] if row else 0
#     failed_attempts += 1
#     lockout_until = None
#     if failed_attempts >= max_attempts:
#         lockout_until = datetime.now(pytz.timezone('Asia/Hong_Kong')) + timedelta(minutes=lockout_minutes)
#         cur.execute("UPDATE users SET failed_attempts=%s, lockout_until=%s WHERE id=%s", (failed_attempts, lockout_until, user_id))
#     else:
#         cur.execute("UPDATE users SET failed_attempts=%s WHERE id=%s", (failed_attempts, user_id))
#     return failed_attempts, lockout_until.isoformat() if lockout_until else None

# def reset_failed_attempts(cur, user_id):
#     """Reset failed login attempts and lockout status after successful login."""
#     cur.execute("UPDATE users SET failed_attempts=0, lockout_until=NULL WHERE id=%s", (user_id,))

# def log_sensitive_operation(user_id, operation, details):
#     try:
#         conn = get_db_conn()
#         cur = conn.cursor()
#         cur.execute(
#             'INSERT INTO audit_logs (user_id, operation, details, timestamp) VALUES (%s, %s, %s, NOW())',
#             (user_id, operation, details)
#         )
#         conn.commit()
#         cur.close()
#         conn.close()
#     except Exception as e:
#         # In production, log this error securely if needed
#         pass

# UPLOAD_FOLDER = 'uploads'
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # Using get_db_conn from config.py

# @app.route('/', methods=['GET'])
# @limiter.exempt
# def root():
#     """Root endpoint with API information"""
#     return jsonify({
#         'message': 'Terry Ray Logistics Shipping System API',
#         'version': '1.0.0',
#         'status': 'running',
#         'endpoints': {
#             'health': '/health',
#             'api_base': '/api',
#             'documentation': 'Check the API endpoints for more information'
#         }
#     }), 200

# @app.route('/health', methods=['GET'])
# @limiter.exempt
# def health_check():
#     """Health check endpoint for monitoring"""
#     try:
#         # Test database connection
#         conn = get_db_conn()
#         if conn:
#             conn.close()
#             return jsonify({
#                 'status': 'healthy',
#                 'database': 'connected',
#                 'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
#             }), 200
#         else:
#             return jsonify({
#                 'status': 'unhealthy',
#                 'database': 'disconnected',
#                 'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
#             }), 503
#     except Exception as e:
#         return jsonify({
#             'status': 'unhealthy',
#             'error': str(e),
#             'timestamp': datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
#         }), 503

# @app.route('/api/register', methods=['POST'])
# @limiter.limit("50 per hour" if is_development else "20 per hour")  # More lenient in development
# def register():
#     data = request.get_json()
#     username = data.get('username')
#     password = data.get('password')
#     role = data.get('role')
#     customer_name = data.get('customer_name')
#     customer_email = data.get('customer_email')
#     customer_phone = data.get('customer_phone')
#     if not all([username, password, role, customer_name, customer_email, customer_phone]):
#         return jsonify({'error': 'Missing fields'}), 400
    
#     # Validate password
#     is_valid, message = validate_password(password)
#     if not is_valid:
#         return jsonify({'error': message}), 400
    
#     try:
#         conn = get_db_conn()
#         cur = conn.cursor()
#         # Encrypt sensitive data
#         encrypted_email = encrypt_sensitive_data(customer_email)
#         encrypted_phone = encrypt_sensitive_data(customer_phone)
        
#         cur.execute(
#             "INSERT INTO users (username, password_hash, role, customer_name, customer_email, customer_phone) VALUES (%s, %s, %s, %s, %s, %s)",
#             (username, generate_password_hash(password), role, customer_name, encrypted_email, encrypted_phone)
#         )
#         conn.commit()
#         log_sensitive_operation(None, 'register', f'New user registered: {username}')
#         cur.close()
#         conn.close()
#         return jsonify({'message': 'Registration submitted, waiting for approval.'})
#     except Exception as e:
#         return jsonify({'error': str(e)}), 400

# @app.route('/api/login', methods=['POST'])
# @limiter.limit("5 per minute")
# def login():
#     data = request.get_json()
#     username = data.get('username')
#     password = data.get('password')
#     captcha_token = data.get('captcha_token')
#     ip_address = request.remote_addr  # Get the IP address of the request
#     if not verify_captcha(captcha_token):
#         return jsonify({'error': 'CAPTCHA verification failed'}), 400
#     conn = get_db_conn()
#     cur = conn.cursor()
#     cur.execute("SELECT id, password_hash, role, approved, customer_name, customer_email, customer_phone FROM users WHERE username=%s", (username,))
#     user = cur.fetchone()
#     if not user:
#         # Log failed attempt for monitoring
#         log_sensitive_operation(None, 'login_failed', f'Username {username} not found, IP:{ip_address}')
#         cur.close()
#         conn.close()
#         return jsonify({'error': 'User not found'}), 401
#     user_id, password_hash, role, approved, customer_name, customer_email, customer_phone = user
#     # Check account lockout
#     locked, lockout_until = is_account_locked(cur, user_id)
#     if locked:
#         cur.close()
#         conn.close()
#         return jsonify({'error': f'Account locked. Try again after {lockout_until}'}), 403
#     if not approved:
#         cur.close()
#         conn.close()
#         return jsonify({'error': 'User not approved yet'}), 403
#     if not check_password_hash(password_hash, password):
#         failed_attempts, lockout_until = increment_failed_attempts(cur, user_id)
#         conn.commit()
#         # Log failed attempt for monitoring
#         log_sensitive_operation(user_id, 'login_failed', f'Incorrect password. Attempts: {failed_attempts}, IP:{ip_address}')
#         # --- Monitoring/Alerting ---
#         if failed_attempts >= ALERT_FAILED_ATTEMPTS_THRESHOLD:
#             subject = f"[ALERT] User {username} failed login attempts"
#             body = f"User {username} has failed to login {failed_attempts} times from IP {ip_address}."
#             send_admin_alert(subject, body)
#         cur.close()
#         conn.close()
#         if lockout_until:
#             return jsonify({'error': f'Account locked. Try again after {lockout_until}'}), 403
#         return jsonify({'error': 'Incorrect password'}), 401
#     reset_failed_attempts(cur, user_id)
#     conn.commit()
#     access_token = create_access_token(identity=json.dumps({'id': user_id, 'role': role, 'username': username}))
#     log_sensitive_operation(user_id, 'login', 'User logged in successfully')
#     response = make_response(jsonify({
#         "customer_name": customer_name,
#         "customer_email": decrypt_sensitive_data(customer_email),
#         "customer_phone": decrypt_sensitive_data(customer_phone),
#         'role': role,
#         'username': username
#     }), 200)
#     from flask_jwt_extended import set_access_cookies
#     set_access_cookies(response, access_token)
#     cur.close()
#     conn.close()
#     return response

# @app.route('/api/approve_user/<int:user_id>', methods=['POST'])
# @jwt_required()
# def approve_user(user_id):
#     user = json.loads(get_jwt_identity())
#     if user['role'] not in ['staff', 'admin']:
#         return jsonify({'error': 'Unauthorized'}), 403
#     conn = get_db_conn()
#     cur = conn.cursor()
#     cur.execute("UPDATE users SET approved=TRUE WHERE id=%s", (user_id,))
#     # Fetch user email and name
#     cur.execute("SELECT customer_email, customer_name FROM users WHERE id=%s", (user_id,))
#     row = cur.fetchone()
#     conn.commit()
#     cur.close()
#     conn.close()
#     if row:
#         customer_email, customer_name = row
#         decrypted_email = decrypt_sensitive_data(customer_email) if customer_email else ''
#         if decrypted_email:
#             subject = "Your registration has been approved"
#             body = f"Dear {customer_name},\n\nYour registration has been approved. You can now log in and use our services.\n\nThank you!"
#             send_simple_email(decrypted_email, subject, body)
#     return jsonify({'message': 'User approved'})

# @app.route('/api/unapproved_users', methods=['GET'])
# @jwt_required()
# def get_unapproved_users():
#     user = json.loads(get_jwt_identity())
#     if user['role'] not in ['staff', 'admin']:
#         return jsonify({'error': 'Unauthorized'}), 403
#     conn = get_db_conn()
#     cur = conn.cursor()
#     cur.execute('SELECT id, username, customer_name, customer_email, customer_phone, role FROM users WHERE approved = FALSE')
#     users = []
#     for row in cur.fetchall():
#         decrypted_email = decrypt_sensitive_data(row[3]) if row[3] is not None else ''
#         decrypted_phone = decrypt_sensitive_data(row[4]) if row[4] is not None else ''
#         users.append({
#             'id': row[0],
#             'username': row[1],
#             'customer_name': row[2],
#             'customer_email': decrypted_email,
#             'customer_phone': decrypted_phone,
#             'role': row[5]
#         })
#     cur.close()
#     conn.close()
#     return jsonify(users)

# @app.route('/api/stats/files_by_date')
# @jwt_required()
# def files_by_date():
#     user = json.loads(get_jwt_identity())
#     if user['role'] != 'staff':
#         return jsonify({'error': 'Unauthorized'}), 403
#     query_date = request.args.get('date')
#     conn = get_db_conn()
#     cur = conn.cursor()
#     start_date, end_date = get_hk_date_range(query_date)
#     cur.execute("SELECT COUNT(*) FROM bill_of_lading WHERE created_at >= %s AND created_at < %s", (start_date, end_date))
#     count = cur.fetchone()[0]
#     cur.close()
#     conn.close()
#     return jsonify({'files_created': count})

# @app.route('/api/stats/completed_today')
# @jwt_required()
# def completed_today():
#     user = json.loads(get_jwt_identity())
#     if user['role'] != 'staff':
#         return jsonify({'error': 'Unauthorized'}), 403
#     hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
#     today = hk_now.date().isoformat()
#     conn = get_db_conn()
#     cur = conn.cursor()
#     start_date, end_date = get_hk_date_range(today)
#     cur.execute("SELECT COUNT(*) FROM bill_of_lading WHERE status='Completed' AND completed_at >= %s AND completed_at < %s", (start_date, end_date))
#     count = cur.fetchone()[0]
#     cur.close()
#     conn.close()
#     return jsonify({'completed_today': count})

# @app.route('/api/stats/payments_by_date')
# @jwt_required()
# def payments_by_date():
#     user = json.loads(get_jwt_identity())
#     if user['role'] != 'staff':
#         return jsonify({'error': 'Unauthorized'}), 403
#     query_date = request.args.get('date')
#     conn = get_db_conn()
#     cur = conn.cursor()
#     start_date, end_date = get_hk_date_range(query_date)
#     cur.execute("SELECT SUM(service_fee) FROM bill_of_lading WHERE created_at >= %s AND created_at < %s", (start_date, end_date))
#     total = cur.fetchone()[0] or 0
#     cur.close()
#     conn.close()
#     return jsonify({'payments_received': float(total)})

# @app.route('/api/stats/bills_by_date')
# @jwt_required()
# def bills_by_date():
#     user = json.loads(get_jwt_identity())
#     if user['role'] != 'staff':
#         return jsonify({'error': 'Unauthorized'}), 403
#     query_date = request.args.get('date')
#     conn = get_db_conn()
#     cur = conn.cursor()
#     start_date, end_date = get_hk_date_range(query_date)
#     cur.execute("""
#         SELECT 
#             COUNT(*) as total_entries,
#             COALESCE(SUM(ctn_fee), 0) as total_ctn_fee,
#             COALESCE(SUM(service_fee), 0) as total_service_fee
#         FROM bill_of_lading 
#         WHERE created_at >= %s AND created_at < %s
#     """, (start_date, end_date))
#     summary = cur.fetchone()
#     cur.execute("""
#         SELECT 
#             id, customer_name, customer_email, 
#             ctn_fee, service_fee, 
#             COALESCE(ctn_fee + service_fee, 0) as total,
#             created_at
#         FROM bill_of_lading 
#         WHERE created_at >= %s AND created_at < %s
#         ORDER BY created_at DESC
#     """, (start_date, end_date))
#     entries = [dict(zip([desc[0] for desc in cur.description], row)) for row in cur.fetchall()]
#     cur.close()
#     conn.close()
#     return jsonify({
#         'summary': {
#             'total_entries': summary[0],
#             'total_ctn_fee': float(summary[1]),
#             'total_service_fee': float(summary[2])
#         },
#         'entries': entries
#     })

# @app.route('/api/upload', methods=['POST'])
# @jwt_required()
# def upload():
#     user = json.loads(get_jwt_identity())
#     username = user['username']
#     try:
#         name = request.form.get('name')
#         email = request.form.get('email')
#         phone = request.form.get('phone')
#         bill_pdfs = request.files.getlist('bill_pdf')
#         invoice_pdf = request.files.get('invoice_pdf')
#         packing_pdf = request.files.get('packing_pdf')
#         if not name:
#             return jsonify({'error': 'Name is required'}), 400
#         if not email:
#             return jsonify({'error': 'Email is required'}), 400
#         if not phone:
#             return jsonify({'error': 'Phone is required'}), 400
#         if not bill_pdfs and not invoice_pdf and not packing_pdf:
#             return jsonify({'error': 'At least one PDF file is required'}), 400
#         def save_file_with_timestamp(file, label):
#             if not file:
#                 return None
#             now_str = datetime.now(pytz.timezone('Asia/Hong_Kong')).strftime('%Y-%m-%d_%H%M%S')
#             filename = f"{now_str}_{label}_{file.filename}"
#             file_path = os.path.join(UPLOAD_FOLDER, filename)
#             file.save(file_path)
#             return filename
#         uploaded_count = 0
#         results = []
#         customer_invoice = save_file_with_timestamp(invoice_pdf, 'invoice') if invoice_pdf else None
#         customer_packing_list = save_file_with_timestamp(packing_pdf, 'packing') if packing_pdf else None
#         if bill_pdfs:
#             for bill_pdf in bill_pdfs:
#                 pdf_filename = save_file_with_timestamp(bill_pdf, 'bill')
#                 fields = {}
#                 if bill_pdf:
#                     pdf_path = os.path.join(UPLOAD_FOLDER, pdf_filename)
#                     fields = extract_fields(pdf_path)
#                 fields_json = json.dumps(fields)
#                 hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
#                 conn = get_db_conn()
#                 cur = conn.cursor()
#                 cur.execute("""
#                     INSERT INTO bill_of_lading (
#                         customer_name, customer_email, customer_phone, pdf_filename, ocr_text,
#                         shipper, consignee, port_of_loading, port_of_discharge, bl_number, container_numbers,
#                         flight_or_vessel, product_description, status,
#                         customer_username, created_at, customer_invoice, customer_packing_list
#                     ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#                 """, (
#                     name, str(email), str(phone), pdf_filename, fields_json,
#                     str(fields.get('shipper', '')),
#                     str(fields.get('consignee', '')),
#                     str(fields.get('port_of_loading', '')),
#                     str(fields.get('port_of_discharge', '')),
#                     str(fields.get('bl_number', '')),
#                     str(fields.get('container_numbers', '')),
#                     str(fields.get('flight_or_vessel', '')),
#                     str(fields.get('product_description', '')),
#                     "Pending",
#                     username,
#                     hk_now,
#                     customer_invoice,
#                     customer_packing_list
#                 ))
#                 conn.commit()
#                 cur.close()
#                 conn.close()
#                 uploaded_count += 1
#         else:
#             hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
#             conn = get_db_conn()
#             cur = conn.cursor()
#             cur.execute("""
#                 INSERT INTO bill_of_lading (
#                     customer_name, customer_email, customer_phone, pdf_filename, ocr_text,
#                     shipper, consignee, port_of_loading, port_of_discharge, bl_number, container_numbers, status,
#                     customer_username, created_at, customer_invoice, customer_packing_list
#                 ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
#             """, (
#                 name, str(email), str(phone), None, None,
#                 '', '', '', '', '', '',
#                 "Pending",
#                 username,
#                 hk_now,
#                 customer_invoice,
#                 customer_packing_list
#             ))
#             conn.commit()
#             cur.close()
#             conn.close()
#             uploaded_count += 1
#         try:
#             if EmailConfig.SMTP_SERVER and EmailConfig.SMTP_USERNAME and EmailConfig.SMTP_PASSWORD:
#                 subject = "We have received your Bill of Lading"
#                 body = f"Dear {name},\n\nWe have received your documents. Our team will be in touch with you within 24 hours.\n\nThank you!"
#                 send_simple_email(email, subject, body)
#         except Exception as e:
#             pass
#         return jsonify({'message': f'Upload successful! {uploaded_count} bill(s) uploaded.'})
#     except Exception as e:
#         return jsonify({'error': f'Error processing upload: {str(e)}'}), 400


# @app.route('/api/bills', methods=['GET'])
# def get_bills():
#     page = int(request.args.get('page', 1))
#     page_size = int(request.args.get('page_size', 50))
#     offset = (page - 1) * page_size
#     bl_number = request.args.get('bl_number')
#     status = request.args.get('status')
#     date = request.args.get('date')
#     conn = get_db_conn()
#     cur = conn.cursor()

#     # Build WHERE clause
#     where_clauses = []
#     params = []
#     if bl_number:
#         where_clauses.append('bl_number ILIKE %s')
#         params.append(f'%{bl_number}%')
#     if status:
#         where_clauses.append('status = %s')
#         params.append(status)
#     if date:
#         start_date, end_date = get_hk_date_range(date)
#         where_clauses.append('created_at >= %s AND created_at < %s')
#         params.extend([start_date, end_date])
#     where_sql = ' AND '.join(where_clauses)
#     if where_sql:
#         where_sql = 'WHERE ' + where_sql

#     # Get total count for pagination
#     count_query = f'SELECT COUNT(*) FROM bill_of_lading {where_sql}'
#     cur.execute(count_query, tuple(params))
#     total_count = cur.fetchone()[0]

#     # Get paginated results
#     query = f'''
#         SELECT id, customer_name, customer_email, customer_phone, pdf_filename, shipper, consignee, port_of_loading, port_of_discharge, bl_number, container_numbers,
#                flight_or_vessel, product_description,  -- <-- add here
#                service_fee, ctn_fee, payment_link, receipt_filename, status, invoice_filename, unique_number, created_at, receipt_uploaded_at, customer_username, customer_invoice, customer_packing_list
#         FROM bill_of_lading
#         {where_sql}
#         ORDER BY id DESC
#         LIMIT %s OFFSET %s
#     '''
#     cur.execute(query, tuple(params) + (page_size, offset))
#     rows = cur.fetchall()
#     columns = [desc[0] for desc in cur.description]
#     bills = []
#     for row in rows:
#         bill_dict = dict(zip(columns, row))
#         # Decrypt email and phone
#         if bill_dict.get('customer_email') is not None:
#             bill_dict['customer_email'] = decrypt_sensitive_data(bill_dict['customer_email'])
#         if bill_dict.get('customer_phone') is not None:
#             bill_dict['customer_phone'] = decrypt_sensitive_data(bill_dict['customer_phone'])
#         bills.append(bill_dict)

#     cur.close()
#     conn.close()

#     return jsonify({
#         'bills': bills,
#         'total': total_count,
#         'page': page,
#         'page_size': page_size
#     })

# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     from urllib.parse import unquote
#     base_dir = os.path.dirname(os.path.abspath(__file__))
#     upload_root = os.path.join(base_dir, UPLOAD_FOLDER)
#     safe_filename = unquote(filename)
#     full_path = os.path.join(upload_root, safe_filename)
#     try:
#         response = send_from_directory(upload_root, safe_filename)
#         # Use CORS middleware, do not set manual CORS headers here
#         # if 'X-Frame-Options' in response.headers:
#         #     del response.headers['X-Frame-Options']
#         if safe_filename.lower().endswith('.pdf'):
#             response.headers['Content-Type'] = 'application/pdf'
#         return set_csp_header(response)
#     except FileNotFoundError:
#         print(f"Error: File not found at {full_path}")
#         return "File not found", 404

# # @app.route('/uploads/<filename>')
# # def uploaded_file(filename):
# #     from urllib.parse import unquote
# #     base_dir = os.path.dirname(os.path.abspath(__file__))
# #     upload_root = os.path.join(base_dir, UPLOAD_FOLDER)
# #     # Decode URL-encoded filenames (for spaces/special chars)
# #     safe_filename = unquote(filename)
# #     full_path = os.path.join(upload_root, safe_filename)
# #     print(f"Debug: Requested {filename} (decoded: {safe_filename}), Base dir: {base_dir}, Upload root: {upload_root}, Full path: {full_path}, Exists: {os.path.exists(full_path)}")
# #     try:
# #         response = send_from_directory(upload_root, safe_filename)
# #         # Remove X-Frame-Options header if present
# #         if 'X-Frame-Options' in response.headers:
# #             del response.headers['X-Frame-Options']
# #         # Set CORS headers for allowed origins
# #         origin = request.headers.get('Origin')
# #         if origin in allowed_origins:
# #             response.headers['Access-Control-Allow-Origin'] = origin
# #             response.headers['Vary'] = 'Origin'
# #             response.headers['Access-Control-Allow-Credentials'] = 'true'
# #         # Set Content-Type for PDFs
# #         if safe_filename.lower().endswith('.pdf'):
# #             response.headers['Content-Type'] = 'application/pdf'
# #         return set_csp_header(response)
# #     except FileNotFoundError:
# #         return "File not found", 404
    
# # @app.route('/uploads/<filename>')
# # def uploaded_file(filename):
# #     return send_from_directory(UPLOAD_FOLDER, filename)

# @app.route('/api/bill/<int:bill_id>/upload_receipt', methods=['POST'])
# def upload_receipt(bill_id):
#     if 'receipt' not in request.files:
#         return jsonify({'error': 'No file uploaded'}), 400
#     receipt = request.files['receipt']
#     filename = f"receipt_{bill_id}_{receipt.filename}"
#     receipt_path = os.path.join(UPLOAD_FOLDER, filename)
#     receipt.save(receipt_path)

#     hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong')).isoformat()
#     conn = get_db_conn()
#     cur = conn.cursor()
#     cur.execute("""
#         UPDATE bill_of_lading
#         SET receipt_filename=%s, status=%s, receipt_uploaded_at=%s
#         WHERE id=%s
#     """, (filename, 'Awaiting Bank In', hk_now, bill_id))
#     conn.commit()
#     cur.close()
#     conn.close()
#     return jsonify({'message': 'Receipt uploaded'})

# @app.route('/api/bill/<int:bill_id>', methods=['GET', 'PUT'])
# def bill_detail(bill_id):
#     if request.method == 'GET':
#         conn = get_db_conn()
#         cur = conn.cursor()
#         cur.execute("SELECT * FROM bill_of_lading WHERE id=%s", (bill_id,))
#         bill_row = cur.fetchone()
#         if not bill_row:
#             cur.close()
#             conn.close()
#             return jsonify({'error': 'Bill not found'}), 404
#         columns = [desc[0] for desc in cur.description]
#         bill = dict(zip(columns, bill_row))
#         # Decrypt sensitive fields
#         if bill.get('customer_email') is not None:
#             bill['customer_email'] = decrypt_sensitive_data(bill['customer_email'])
#         if bill.get('customer_phone') is not None:
#             bill['customer_phone'] = decrypt_sensitive_data(bill['customer_phone'])
#         cur.close()
#         conn.close()
#         return jsonify(bill)
#     elif request.method == 'PUT':
#         try:
#             data = request.get_json()
#             conn = get_db_conn()
#             cur = conn.cursor()
#             cur.execute("SELECT * FROM bill_of_lading WHERE id=%s", (bill_id,))
#             bill_row = cur.fetchone()
#             if not bill_row:
#                 return jsonify({'error': 'Bill not found'}), 404
#             columns = [desc[0] for desc in cur.description]
#             bill = dict(zip(columns, bill_row))
#             # Allow updating all relevant fields, including new ones
#             updatable_fields = [
#                 'customer_name', 'customer_email', 'customer_phone', 'bl_number',
#                 'shipper', 'consignee', 'port_of_loading', 'port_of_discharge',
#                 'container_numbers', 'service_fee', 'ctn_fee', 'payment_link', 'unique_number',
#                 'flight_or_vessel', 'product_description',
#                 'payment_method', 'payment_status', 'reserve_status'  # <-- new fields
#             ]
#             update_fields = []
#             update_values = []
#             for field in updatable_fields:
#                 if field in data and data[field] is not None:
#                     if field == 'customer_email':
#                         update_fields.append(f"{field}=%s")
#                         update_values.append(encrypt_sensitive_data(data[field]))
#                     elif field == 'customer_phone':
#                         update_fields.append(f"{field}=%s")
#                         update_values.append(encrypt_sensitive_data(data[field]))
#                     else:
#                         update_fields.append(f"{field}=%s")
#                         update_values.append(data[field])
#             if update_fields:
#                 update_values.append(bill_id)
#                 update_query = f"""
#                     UPDATE bill_of_lading
#                     SET {', '.join(update_fields)}
#                     WHERE id=%s
#                 """
#                 cur.execute(update_query, tuple(update_values))
#                 conn.commit()
#             # Fetch updated bill
#             cur.execute("SELECT * FROM bill_of_lading WHERE id=%s", (bill_id,))
#             bill_row = cur.fetchone()
#             columns = [desc[0] for desc in cur.description]
#             bill = dict(zip(columns, bill_row))
#             # Decrypt sensitive fields
#             if bill.get('customer_email') is not None:
#                 bill['customer_email'] = decrypt_sensitive_data(bill['customer_email'])
#             if bill.get('customer_phone') is not None:
#                 bill['customer_phone'] = decrypt_sensitive_data(bill['customer_phone'])
#             # Regenerate invoice PDF if relevant fields changed
#             customer = {
#                 'name': bill['customer_name'],
#                 'email': bill['customer_email'],
#                 'phone': bill['customer_phone']
#             }
#             try:
#                 invoice_filename = generate_invoice_pdf(customer, bill, bill.get('service_fee'), bill.get('ctn_fee'), bill.get('payment_link'))
#                 bill['invoice_filename'] = invoice_filename
#             except Exception as e:
#                 # In production, log this error securely if needed
#                 pass
#             cur.close()
#             conn.close()
#             return jsonify(bill)
#         except Exception as e:
#             # In production, log this error securely if needed
#             return jsonify({'error': f'Error updating bill: {str(e)}'}), 400
    
# @app.route('/api/bill/<int:bill_id>/settle_reserve', methods=['POST'])
# @jwt_required()
# def settle_reserve(bill_id):
#     conn = get_db_conn()
#     cur = conn.cursor()
#     try:
#         # Check if bill exists
#         cur.execute("SELECT id FROM bill_of_lading WHERE id = %s", (bill_id,))
#         if not cur.fetchone():
#             return jsonify({"error": "Bill not found"}), 404

#         # Update reserve_status field to 'Reserve Settled'
#         cur.execute("""
#             UPDATE bill_of_lading
#             SET reserve_status = 'Reserve Settled'
#             WHERE id = %s
#         """, (bill_id,))
#         conn.commit()
#         return jsonify({"message": "Reserve marked as settled"}), 200
#     except Exception as e:
#         # In production, log this error securely if needed
#         return jsonify({"error": "Failed to settle reserve"}), 500
#     finally:
#         cur.close()
#         conn.close()   


# @app.route('/api/bill/<int:bill_id>/complete', methods=['POST'])
# def complete_bill(bill_id):
#     conn = get_db_conn()
#     cur = conn.cursor()
#     hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
#     # Check payment_method for this bill
#     cur.execute("SELECT payment_method FROM bill_of_lading WHERE id=%s", (bill_id,))
#     row = cur.fetchone()
#     if row and row[0] and row[0].lower() == 'allinpay':
#         # For Allinpay, also update payment_status to 'Paid 100%'
#         cur.execute("""
#             UPDATE bill_of_lading
#             SET status=%s, payment_status=%s, completed_at=%s
#             WHERE id=%s
#         """, ('Paid and CTN Valid', 'Paid 100%', hk_now, bill_id))
#     else:
#         # For others, just update status and completed_at
#         cur.execute("""
#             UPDATE bill_of_lading
#             SET status=%s, completed_at=%s
#             WHERE id=%s
#         """, ('Paid and CTN Valid', hk_now, bill_id))
#     conn.commit()
#     cur.close()
#     conn.close()
#     return jsonify({'message': 'Bill marked as completed'})

# @app.route('/api/request_password_reset', methods=['POST'])
# def request_password_reset():
#     data = request.get_json()
#     email = data.get('email')
#     if not email:
#         return jsonify({'error': 'Email required'}), 400

#     conn = get_db_conn()
#     cur = conn.cursor()
#     cur.execute("SELECT id, customer_name, customer_email FROM users")
#     users = cur.fetchall()
#     user = None
#     for row in users:
#         user_id, customer_name, encrypted_email = row
#         try:
#             decrypted_email = decrypt_sensitive_data(encrypted_email)
#             if decrypted_email == email:
#                 user = (user_id, customer_name)
#                 break
#         except Exception as e:
#             continue
#     if not user:
#         cur.close()
#         conn.close()
#         return jsonify({'message': 'If this email is registered, a reset link will be sent.'})  # Don't reveal user existence

#     user_id, customer_name = user
#     token = secrets.token_urlsafe(32)
#     expires_at = datetime.now(pytz.timezone('Asia/Hong_Kong')) + timedelta(hours=1)
#     cur.execute("INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)", (user_id, token, expires_at))
#     conn.commit()
#     cur.close()
#     conn.close()

#     reset_link = f"https://www.terryraylogicticsco.xyz/reset-password/{token}"
#     subject = "Password Reset Request"
#     body = f"Dear {customer_name},\n\nClick the link below to reset your password:\n{reset_link}\n\nThis link will expire in 1 hour."
#     send_simple_email(email, subject, body)
#     return jsonify({'message': 'If this email is registered, a reset link will be sent.'})

# @app.route('/api/reset_password/<token>', methods=['POST'])
# @limiter.limit("3 per hour")
# def reset_password(token):
#     data = request.get_json()
#     new_password = data.get('password')
#     captcha_token = data.get('captcha_token')
#     if not new_password:
#         return jsonify({'error': 'Password required'}), 400
#     if not verify_captcha(captcha_token):
#         return jsonify({'error': 'CAPTCHA verification failed'}), 400
#     conn = get_db_conn()
#     cur = conn.cursor()
#     cur.execute("SELECT user_id, expires_at FROM password_reset_tokens WHERE token=%s", (token,))
#     row = cur.fetchone()
#     if not row:
#         cur.close()
#         conn.close()
#         return jsonify({'error': 'Invalid or expired token'}), 400

#     user_id, expires_at = row
#     if datetime.now(pytz.timezone('Asia/Hong_Kong')) > expires_at:
#         cur.execute("DELETE FROM password_reset_tokens WHERE token=%s", (token,))
#         conn.commit()
#         cur.close()
#         conn.close()
#         return jsonify({'error': 'Token expired'}), 400
#     password_hash = generate_password_hash(new_password)
#     cur.execute("UPDATE users SET password_hash=%s WHERE id=%s", (password_hash, user_id))
#     cur.execute("DELETE FROM password_reset_tokens WHERE token=%s", (token,))
#     conn.commit()
#     cur.close()
#     conn.close()
#     return jsonify({'message': 'Password has been reset successfully.'})

# @app.route('/api/send_invoice_email', methods=['POST'])
# @jwt_required()
# def send_invoice_email_endpoint():
#     try:
#         data = request.get_json()
#         to_email = data.get('to_email')
#         subject = data.get('subject')
#         body = data.get('body')
#         pdf_url = data.get('pdf_url')
#         bill_id = data.get('bill_id')

#         if not all([to_email, subject, body, pdf_url, bill_id]):
#             return jsonify({'error': 'Missing required fields'}), 400

#         # Fix: Extract just the filename if pdf_url is a full URL
#         import os
#         if pdf_url.startswith('http://') or pdf_url.startswith('https://'):
#             pdf_filename = os.path.basename(pdf_url)
#         else:
#             pdf_filename = pdf_url.lstrip('/')
#         pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', pdf_filename)
        
#         # Send the email
#         success = send_invoice_email(to_email, subject, body, pdf_path)
        
#         if success:
#             # Update bill status to "Invoice Sent"
#             conn = get_db_conn()
#             cur = conn.cursor()
#             cur.execute("UPDATE bill_of_lading SET status=%s WHERE id=%s", ("Invoice Sent", bill_id))
#             conn.commit()
#             cur.close()
#             conn.close()
#             return jsonify({'message': 'Email sent successfully'})
#         else:
#             return jsonify({'error': 'Failed to send email'}), 500
            
#     except Exception as e:
#         print(f"Error sending invoice email: {str(e)}")
#         return jsonify({'error': str(e)}), 500

# @app.route('/api/send_unique_number_email', methods=['POST'])
# def api_send_unique_number_email():
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({'error': 'No data provided'}), 400
#         to_email = data.get('to_email')
#         subject = data.get('subject')
#         body = data.get('body')
#         bill_id = data.get('bill_id')
#         if not all([to_email, subject, body, bill_id]):
#             return jsonify({'error': 'Missing required fields'}), 400
#         # Validate bill_id exists
#         conn = get_db_conn()
#         cur = conn.cursor()
#         cur.execute("SELECT id FROM bill_of_lading WHERE id=%s", (bill_id,))
#         if not cur.fetchone():
#             return jsonify({'error': 'Bill not found'}), 404
#         # Send email
#         send_unique_number_email(to_email, subject, body)
#         return jsonify({'message': 'Unique number email sent successfully'}), 200
#     except Exception as e:
#         print(f"Error in send_unique_number_email: {str(e)}")
#         return jsonify({'error': f'Internal server error: {str(e)}'}), 500

# @app.route('/api/search_bills', methods=['POST'])
# @jwt_required()
# def search_bills():
#     data = request.get_json()
#     customer_name = data.get('customer_name', '')
#     customer_id = data.get('customer_id', '')
#     created_at = data.get('created_at', '')
#     bl_number = data.get('bl_number', '')
#     unique_number = data.get('unique_number', '')
#     username = data.get('username', '')
#     conn = get_db_conn()
#     cur = conn.cursor()
#     query = '''
#         SELECT id, customer_name, customer_email, customer_phone, pdf_filename, shipper, consignee, port_of_loading, port_of_discharge, bl_number, container_numbers, service_fee, ctn_fee, payment_link, receipt_filename, status, invoice_filename, unique_number, created_at, receipt_uploaded_at, customer_username, customer_invoice, customer_packing_list
#         FROM bill_of_lading
#         WHERE 1=1
#     '''
#     params = []
#     if customer_name:
#         query += ' AND customer_name ILIKE %s'
#         params.append(f'%{customer_name}%')
#     if customer_id:
#         try:
#             int(customer_id)
#             query += ' AND id = %s'
#             params.append(customer_id)
#         except ValueError:
#             query += ' AND customer_name ILIKE %s'
#             params.append(f'%{customer_id}%')
#     if created_at:
#         start_date, end_date = get_hk_date_range(created_at)
#         query += ' AND created_at >= %s AND created_at < %s'
#         params.extend([start_date, end_date])
#     if bl_number:
#         query += ' AND bl_number ILIKE %s'
#         params.append(f'%{bl_number}%')
#     if unique_number:
#         query += ' AND unique_number = %s'
#         params.append(unique_number)
#     if username:
#         query += ' AND customer_username = %s'
#         params.append(username)
#     query += ' ORDER BY id DESC'
#     cur.execute(query, params)
#     rows = cur.fetchall()
#     columns = [desc[0] for desc in cur.description]
#     bills = []
#     for row in rows:
#         bill_dict = dict(zip(columns, row))
#         if bill_dict.get('customer_email') is not None:
#             bill_dict['customer_email'] = decrypt_sensitive_data(bill_dict['customer_email'])
#         if bill_dict.get('customer_phone') is not None:
#             bill_dict['customer_phone'] = decrypt_sensitive_data(bill_dict['customer_phone'])
#         bills.append(bill_dict)
#     cur.close()
#     conn.close()
#     return jsonify(bills)

# @app.route('/api/stats/summary')
# @jwt_required()
# def stats_summary():
#     user = json.loads(get_jwt_identity())
#     if user['role'] not in ['staff', 'admin']:
#         return jsonify({'error': 'Unauthorized'}), 403
#     conn = get_db_conn()
#     cur = conn.cursor()
#     cur.execute("SELECT COUNT(*) FROM bill_of_lading")
#     total_bills = cur.fetchone()[0]
#     cur.execute("SELECT COUNT(*) FROM bill_of_lading WHERE status = 'Paid and CTN Valid'")
#     completed_bills = cur.fetchone()[0]
#     cur.execute("""
#     SELECT COUNT(*) 
#     FROM bill_of_lading 
#     WHERE status IN ('Pending', 'Invoice Sent', 'Awaiting Bank In')
#     """)
#     pending_bills = cur.fetchone()[0]
#     cur.execute("SELECT COALESCE(SUM(ctn_fee + service_fee), 0) FROM bill_of_lading")
#     total_invoice_amount = float(cur.fetchone()[0] or 0)
#     cur.execute("""
#         SELECT COALESCE(SUM(
#             CASE 
#                 WHEN payment_method != 'Allinpay' AND status = 'Paid and CTN Valid'
#                     THEN ctn_fee + service_fee
#                 WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Reserve Settled'
#                     THEN ctn_fee + service_fee
#                 WHEN payment_method = 'Allinpay' AND status = 'Paid and CTN Valid' AND reserve_status = 'Unsettled'
#                     THEN (ctn_fee * 0.85) + (service_fee * 0.85)
#                 ELSE 0
#             END
#         ), 0)
#         FROM bill_of_lading
#     """)
#     total_payment_received = float(cur.fetchone()[0] or 0)
#     cur.execute("""
#     SELECT COALESCE(SUM(service_fee + ctn_fee), 0)
#     FROM bill_of_lading
#     WHERE status IN ('Awaiting Bank In', 'Invoice Sent')
#     """)
#     awaiting_payment = float(cur.fetchone()[0] or 0)
#     cur.execute("SELECT COALESCE(SUM(reserve_amount), 0) FROM bill_of_lading WHERE LOWER(TRIM(reserve_status)) = 'unsettled'")
#     unsettled_reserve = float(cur.fetchone()[0] or 0)
#     total_payment_outstanding = awaiting_payment + unsettled_reserve
#     cur.close()
#     conn.close()
#     return jsonify({
#         'total_bills': total_bills,
#         'completed_bills': completed_bills,
#         'pending_bills': pending_bills,
#         'total_invoice_amount': round(total_invoice_amount, 2),
#         'total_payment_received': round(total_payment_received, 2),
#         'total_payment_outstanding': round(total_payment_outstanding, 2)
#     })

# @app.route('/api/stats/outstanding_bills')
# @jwt_required()
# def outstanding_bills():
#     user = json.loads(get_jwt_identity())
#     if user['role'] not in ['staff', 'admin']:
#         return jsonify({'error': 'Unauthorized'}), 403
#     conn = get_db_conn()
#     cur = conn.cursor()
#     cur.execute("""
#         SELECT 
#             id, customer_name, bl_number,
#             ctn_fee, service_fee, reserve_amount,
#             payment_method, reserve_status, invoice_filename
#         FROM bill_of_lading
#         WHERE status IN ('Awaiting Bank In', 'Invoice Sent')
#            OR (payment_method = 'Allinpay' AND LOWER(TRIM(reserve_status)) = 'unsettled')
#     """)
#     rows = cur.fetchall()
#     columns = [desc[0] for desc in cur.description]
#     bills = []
#     for row in rows:
#         bill = dict(zip(columns, row))
#         ctn_fee = float(bill.get('ctn_fee') or 0)
#         service_fee = float(bill.get('service_fee') or 0)
#         payment_method = str(bill.get('payment_method') or '').strip().lower()
#         reserve_status = str(bill.get('reserve_status') or '').strip().lower()
#         outstanding_amount = round(ctn_fee + service_fee, 2)
#         if payment_method == 'allinpay' and reserve_status == 'unsettled':
#             outstanding_amount = round(ctn_fee * 0.15 + service_fee * 0.15, 2)
#         bill['outstanding_amount'] = outstanding_amount
#         bills.append(bill)
#     cur.close()
#     conn.close()
#     return jsonify(bills)

# # --- LOGOUT ENDPOINT ---
# from flask_jwt_extended import unset_jwt_cookies

# @app.route('/api/logout', methods=['POST'])
# def logout():
#     response = jsonify({'message': 'Logged out successfully'})
#     unset_jwt_cookies(response)
#     return response, 200

# # --- CSRF TOKEN ENDPOINT (for frontend to fetch CSRF token) ---
# @app.route('/api/csrf-token', methods=['GET'])
# @jwt_required()
# def csrf_token():
#     verify_jwt_in_request()
#     csrf_token_value = get_jwt()["csrf"]
#     return jsonify({'csrf_token': csrf_token_value})

# # --- USER INFO ENDPOINT (NO CACHE) ---
# @app.route('/api/me', methods=['GET'])
# @jwt_required()
# def get_me():
#     user = json.loads(get_jwt_identity())
#     return jsonify(user)

# # --- GENERIC ERROR HANDLERS ---
# @app.errorhandler(404)
# def not_found_error(error):
#     return jsonify({'error': 'Not found'}), 404

# @app.errorhandler(500)
# def internal_error(error):
#     return jsonify({'error': 'Internal server error'}), 500

# # --- HTTPS ENFORCEMENT (PRODUCTION ONLY) ---
# if not is_development:
#     # Use ProxyFix to respect X-Forwarded-Proto for HTTPS enforcement behind a proxy
#     app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)
#     @app.before_request
#     def enforce_https():
#         if not request.is_secure and request.headers.get('X-Forwarded-Proto', 'http') != 'https':
#             url = request.url.replace('http://', 'https://', 1)
#             return redirect(url, code=301)

# # --- Security Alert Thresholds and Admin Alert Stub ---
# ALERT_FAILED_ATTEMPTS_THRESHOLD = 5  # Default threshold for failed login attempts

# def send_admin_alert(subject, body):
#     admin_email = 'ray6330099@gmail.com'
#     try:
#         send_simple_email(admin_email, subject, body)
#     except Exception as e:
#         print(f"Error sending admin alert: {str(e)}")

# def get_hk_date_range(search_date_str):
#     """
#     Convert a date string (YYYY-MM-DD) to Hong Kong timezone range for database queries.
#     Returns (start_datetime, end_datetime) in Hong Kong timezone.
#     """
#     import pytz
#     from datetime import datetime, timedelta
#     hk_tz = pytz.timezone('Asia/Hong_Kong')
#     search_date = datetime.strptime(search_date_str, '%Y-%m-%d')
#     search_date = hk_tz.localize(search_date)
#     next_date = search_date + timedelta(days=1)
#     return search_date, next_date

# @app.route('/api/bills/awaiting_bank_in', methods=['GET'])
# @jwt_required()
# def bills_awaiting_bank_in():
#     user = json.loads(get_jwt_identity())
#     if user['role'] not in ['staff', 'admin']:
#         return jsonify({'error': 'Unauthorized'}), 403
#     conn = get_db_conn()
#     cur = conn.cursor()
#     cur.execute("""
#         SELECT id, customer_name, customer_email, customer_phone, pdf_filename, bl_number, service_fee, ctn_fee, payment_link, receipt_filename, status, invoice_filename, unique_number, created_at, receipt_uploaded_at, customer_username, customer_invoice, customer_packing_list
#         FROM bill_of_lading
#         WHERE status = 'Awaiting Bank In'
#         ORDER BY id DESC
#     """)
#     rows = cur.fetchall()
#     columns = [desc[0] for desc in cur.description]
#     bills = []
#     for row in rows:
#         bill_dict = dict(zip(columns, row))
#         if bill_dict.get('customer_email') is not None:
#             bill_dict['customer_email'] = decrypt_sensitive_data(bill_dict['customer_email'])
#         if bill_dict.get('customer_phone') is not None:
#             bill_dict['customer_phone'] = decrypt_sensitive_data(bill_dict['customer_phone'])
#         bills.append(bill_dict)
#     cur.close()
#     conn.close()
#     return jsonify(bills)