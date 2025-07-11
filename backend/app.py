from dotenv import load_dotenv
import os
# Load .env at the very top, before any other imports
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

from flask import Flask, send_from_directory, request, jsonify, redirect, g, abort
from flask_cors import CORS
from flask_jwt_extended import JWTManager, decode_token
from limiter_instance import limiter
from urllib.parse import unquote
from werkzeug.middleware.proxy_fix import ProxyFix

from config import get_db_conn

from routes.auth_routes import auth_routes
from routes.bill_routes import bill_routes
from routes.stats_routes import stats_routes
from routes.misc_routes import misc_routes
from routes.admin_routes import admin_routes
from payment_webhook import payment_webhook  # Register payment webhook blueprint
from payment_link import payment_link  # Register payment link blueprint

app = Flask(__name__, static_folder='build', static_url_path='')
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Allowed origins for CORS and CSP
allowed_origins = []
if os.getenv('ALLOWED_ORIGINS'):
    prod_domains = [origin.strip() for origin in os.getenv('ALLOWED_ORIGINS').split(',') if origin.strip()]
    allowed_origins.extend(prod_domains)

CORS(app, origins=allowed_origins, supports_credentials=True)

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_SECURE'] = True
app.config['JWT_COOKIE_SAMESITE'] = 'None'  # Allow cross-site cookies
app.config['JWT_COOKIE_DOMAIN'] = 'iqstrade.onrender.com'  # Set to exact domain for browser compatibility
app.config['JWT_COOKIE_HTTPONLY'] = True
app.config['JWT_COOKIE_CSRF_PROTECT'] = True  # Enable CSRF protection for production
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

jwt = JWTManager(app)
limiter.init_app(app)

# Register all route blueprints
app.register_blueprint(auth_routes, url_prefix='/api')
app.register_blueprint(bill_routes, url_prefix='/api')
app.register_blueprint(stats_routes, url_prefix='/api')
app.register_blueprint(misc_routes, url_prefix='/api')
app.register_blueprint(admin_routes, url_prefix='/api')
app.register_blueprint(payment_webhook, url_prefix='/api/webhook')
app.register_blueprint(payment_link, url_prefix='/api')

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

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

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    safe_filename = unquote(filename)
    full_path = os.path.join(UPLOAD_FOLDER, safe_filename)
    try:
        response = send_from_directory(UPLOAD_FOLDER, safe_filename)
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
        return "File not found", 404

# --- SESSION MANAGEMENT ---
active_sessions = set()
MAX_CONCURRENT_USERS = 100

@app.before_request
def limit_concurrent_users():
    # Only enforce for authenticated endpoints
    if request.endpoint and request.endpoint not in ['login', 'register', 'static', 'ping', 'health_check']:
        token = request.cookies.get('access_token_cookie')
        if token:
            try:
                identity = decode_token(token)['sub']
                if identity not in active_sessions:
                    if len(active_sessions) >= MAX_CONCURRENT_USERS:
                        abort(429, description='Maximum concurrent users reached. Please try again later.')
                    active_sessions.add(identity)
                g.current_identity = identity
            except Exception:
                pass

@app.after_request
def cleanup_sessions(response):
    # Remove session if user logs out or token is invalid
    if request.endpoint == 'logout':
        token = request.cookies.get('access_token_cookie')
        if token:
            try:
                identity = decode_token(token)['sub']
                if identity in active_sessions:
                    active_sessions.remove(identity)
            except Exception:
                pass
    return response

# --- ENHANCED AUDIT LOGGING ---
def log_sensitive_operation(user_id, operation, details):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO audit_logs (user_id, operation, details, timestamp, ip_address) VALUES (%s, %s, %s, NOW(), %s)',
            (user_id, operation, details, request.remote_addr)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        pass

# --- FILE UPLOAD VIRUS SCAN (stub) ---
def scan_file_for_viruses(file_path):
    # Placeholder for virus scan integration (e.g., ClamAV)
    # Return True if clean, False if infected
    return True

# In upload endpoint, after saving file:
# if not scan_file_for_viruses(file_path):
#     os.remove(file_path)
#     return jsonify({'error': 'File failed virus scan'}), 400

# --- STRICTER INPUT VALIDATION (example for registration) ---
def is_valid_email(email):
    import re
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email)

def is_valid_phone(phone):
    import re
    return re.match(r"^[0-9\-\+\s]{7,20}$", phone)

# In register endpoint:
# if not is_valid_email(customer_email):
#     return jsonify({'error': 'Invalid email format'}), 400
# if not is_valid_phone(customer_phone):
#     return jsonify({'error': 'Invalid phone number'}), 400

# --- ENFORCE HTTPS IN PRODUCTION ---
@app.before_request
def enforce_https():
    if not app.debug and not request.is_secure and 'render' in request.host:
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 10MB.'}), 413

@app.route('/static/<path:filename>')
def serve_static(filename):
    build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
    static_path = os.path.join(build_dir, 'static', filename)
    print(f"[DEBUG] Serving static file: {static_path}")
    if not os.path.exists(static_path):
        print(f"[ERROR] File not found: {static_path}")
    return send_from_directory(os.path.join(build_dir, 'static'), filename)

# --- SERVE REACT FRONTEND BUILD ---
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react_app(path):
    build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
    if path != "" and os.path.exists(os.path.join(build_dir, path)):
        return send_from_directory(build_dir, path)
    else:
        return send_from_directory(build_dir, 'index.html')

print(f"[DEBUG] FLASK_ENV: {os.getenv('FLASK_ENV')}")
print(f"[DEBUG] ALLOWED_ORIGINS: {allowed_origins}")
print(f"[DEBUG] JWT_COOKIE_DOMAIN: {app.config['JWT_COOKIE_DOMAIN']}")
print(f"[DEBUG] JWT_COOKIE_SAMESITE: {app.config['JWT_COOKIE_SAMESITE']}")
print(f"[DEBUG] JWT_COOKIE_SECURE: {app.config['JWT_COOKIE_SECURE']}")
print(f"[DEBUG] JWT_COOKIE_HTTPONLY: {app.config['JWT_COOKIE_HTTPONLY']}")
print(f"[DEBUG] JWT_COOKIE_CSRF_PROTECT: {app.config['JWT_COOKIE_CSRF_PROTECT']}")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
