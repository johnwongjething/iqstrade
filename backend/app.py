from flask import Flask
from routes.auth_routes import auth_routes
from routes.email_routes import email_routes
from email_processor import start_email_processor
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

from config import get_db_conn, return_db_conn

from routes.auth_routes import auth_routes
from routes.bill_routes import bill_routes
from routes.stats_routes import stats_routes
from routes.misc_routes import misc_routes

from routes.admin_routes import admin_routes
from routes.management_routes import management_routes
from routes.fcm_routes import fcm_routes  # Register FCM routes
from payment_webhook import payment_webhook  # Register payment webhook blueprint
from payment_link import payment_link  # Register payment link blueprint
from bank_routes import bank_routes
# Removed duplicate email processing system - using main email_ingestor.py instead
from outlook_addin_api import outlook_api  # Register Outlook add-in API

from datetime import datetime, timedelta
import pytz
import logging
from utils.timezone_utils import get_hk_now_iso

# Import email scheduler
from email_scheduler import run_as_service

# Import performance monitoring
from utils.performance_monitor import performance_monitor, monitor_request

app = Flask(__name__, static_folder='build', static_url_path='/')
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Allowed origins for CORS and CSP
allowed_origins = []
if os.getenv('ALLOWED_ORIGINS'):
    prod_domains = [origin.strip() for origin in os.getenv('ALLOWED_ORIGINS').split(',') if origin.strip()]
    allowed_origins.extend(prod_domains)

CORS(app, origins=allowed_origins, supports_credentials=True)

app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)  # 1 hour access token
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=7)  # 7 days refresh token

app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
app.config['JWT_REFRESH_COOKIE_PATH'] = '/api/refresh'

# JWT Cookie configuration - simplified for production
app.config['JWT_COOKIE_SECURE'] = True
app.config['JWT_COOKIE_SAMESITE'] = 'None'  # Allow cross-site cookies for Render deployment
app.config['JWT_COOKIE_DOMAIN'] = None  # No domain restriction
app.config['JWT_COOKIE_HTTPONLY'] = True
app.config['JWT_COOKIE_CSRF_PROTECT'] = False  # Disable CSRF for simplicity
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

jwt = JWTManager(app)

# Add JWT error handlers for debugging
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    logging.error(f"[JWT DEBUG] Token expired: {jwt_payload}")
    return jsonify({"error": "Token has expired"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    logging.error(f"[JWT DEBUG] Invalid token: {error}")
    return jsonify({"error": "Invalid token"}), 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    logging.error(f"[JWT DEBUG] Missing token: {error}")
    return jsonify({"error": "Missing token"}), 401
limiter.init_app(app)

# Register all route blueprints

app.register_blueprint(auth_routes, url_prefix='/api')
app.register_blueprint(bill_routes, url_prefix='/api')
app.register_blueprint(stats_routes, url_prefix='/api')
app.register_blueprint(misc_routes, url_prefix='/api')
app.register_blueprint(fcm_routes, url_prefix='/api')  # Register FCM routes
app.register_blueprint(admin_routes)
app.register_blueprint(management_routes, url_prefix='/api')
app.register_blueprint(payment_webhook, url_prefix='/api/webhook')
app.register_blueprint(payment_link, url_prefix='/api')
app.register_blueprint(bank_routes)
# Removed duplicate email processing blueprint registration
app.register_blueprint(email_routes, url_prefix='/admin/email')
app.register_blueprint(outlook_api)  # Register Outlook add-in API

# Migration: Removed UPLOAD_FOLDER, switching to Cloudinary for all file storage

# Start email scheduler as background service
email_scheduler_thread = None
if os.getenv('ENABLE_EMAIL_SCHEDULER', 'true').lower() == 'true':
    try:
        email_scheduler_thread = run_as_service()
        # Email scheduler started as background service
    except Exception as e:
        print(f'[WARNING] Failed to start email scheduler: {e}')

# Performance monitoring endpoints
@app.route('/api/performance/stats', methods=['GET'])
def get_performance_stats():
    """Get current performance statistics"""
    stats = performance_monitor.get_performance_stats()
    return jsonify(stats)

@app.route('/api/performance/summary', methods=['GET'])
def log_performance_summary():
    """Log and return performance summary"""
    performance_monitor.log_performance_summary()
    return jsonify({'message': 'Performance summary logged'})

# --- SESSION MANAGEMENT ---
active_sessions = set()
MAX_CONCURRENT_USERS = 100

# Combined middleware for performance monitoring, session management, and HTTPS enforcement
@app.before_request
def combined_before_request():
    """Combined middleware for performance monitoring, session management, and HTTPS enforcement"""
    # Start performance monitoring
    g.start_time = performance_monitor.start_request_timer()
    
    # HTTPS enforcement for production
    if not app.debug and not request.is_secure and 'render' in request.host:
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)
    
    # Session management for authenticated endpoints
    if request.endpoint and request.endpoint not in ['login', 'register', 'static', 'ping', 'health_check', 'get_performance_stats', 'log_performance_summary']:
        token = request.cookies.get('access_token_cookie')
        if token:
            try:
                identity = decode_token(token)['sub']
                if identity not in active_sessions:
                    if len(active_sessions) >= MAX_CONCURRENT_USERS:
                        performance_monitor.record_error('concurrent_users_limit', f'Max users reached: {len(active_sessions)}')
                        abort(429, description='Maximum concurrent users reached. Please try again later.')
                    active_sessions.add(identity)
                g.current_identity = identity
            except Exception:
                pass

@app.after_request
def end_request_timer(response):
    """End timing each request and record it"""
    if hasattr(g, 'start_time'):
        performance_monitor.end_request_timer(g.start_time, request.endpoint)
    return response

@app.teardown_appcontext
def cleanup_session(error):
    """Clean up user session on request end"""
    if hasattr(g, 'current_identity'):
        try:
            active_sessions.discard(g.current_identity)
        except:
            pass

# --- ENHANCED AUDIT LOGGING ---
def log_sensitive_operation(user_id, operation, details):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
        cur.execute(
            'INSERT INTO audit_logs (user_id, operation, details, timestamp, ip_address) VALUES (%s, %s, %s, %s, %s)',
            (user_id, operation, details, hk_now, request.remote_addr)
        )
        conn.commit()
        cur.close()
        return_db_conn(conn)
    except Exception as e:
        performance_monitor.record_error('audit_log_error', str(e))
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
def enforce_https():
    if not app.debug and not request.is_secure and 'render' in request.host:
        url = request.url.replace("http://", "https://", 1)
        return redirect(url, code=301)

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 10MB.'}), 413

@app.errorhandler(404)
def not_found(error):
    # If it's an API route, return JSON 404
    if request.path.startswith('/api/') or request.path.startswith('/admin/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    
    # Handle static file requests that might have wrong paths
    if request.path.startswith('/reset-password/static/') or request.path.startswith('/static/'):
        # Extract the actual static file path
        static_path = request.path.replace('/reset-password/static/', '/static/')
        if static_path.startswith('/static/'):
            build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
            static_file = static_path.replace('/static/', '')
            static_file_path = os.path.join(build_dir, 'static', static_file)
            
            if os.path.exists(static_file_path):
                return send_from_directory(os.path.join(build_dir, 'static'), static_file)
            else:
                print(f"[ERROR] Static file not found: {static_file_path}")
    
    # For all other routes, try to serve index.html
    build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
    index_path = os.path.join(build_dir, 'index.html')
    
    if os.path.exists(index_path):
        return send_from_directory(build_dir, 'index.html')
    else:
        print(f"[ERROR] index.html not found at: {index_path}")
        return jsonify({'error': 'Frontend not found'}), 404

# Test route to verify Flask is working
@app.route('/test')
def test_route():
            return jsonify({'message': 'Flask app is working', 'timestamp': get_hk_now_iso()})

@app.route('/static/<path:filename>')
def serve_static(filename):
    build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
    static_path = os.path.join(build_dir, 'static', filename)
    if not os.path.exists(static_path):
        print(f"[ERROR] File not found: {static_path}")
    return send_from_directory(os.path.join(build_dir, 'static'), filename)

@app.route('/outlook_addin/<path:filename>')
def serve_outlook_addin(filename):
    """Serve Outlook add-in files"""
    return send_from_directory('outlook_addin', filename)

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    """Serve add-in assets (icons, etc.)"""
    return send_from_directory('outlook_addin/assets', filename)


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'build')
    
    # Check if build directory exists
    if not os.path.exists(build_dir):
        print(f"[ERROR] Build directory not found: {build_dir}")
        return jsonify({'error': 'Frontend not built', 'build_dir': build_dir}), 500
    
    # Check if index.html exists
    index_path = os.path.join(build_dir, 'index.html')
    if not os.path.exists(index_path):
        print(f"[ERROR] index.html not found: {index_path}")
        return jsonify({'error': 'Frontend index.html not found', 'index_path': index_path}), 500

    # For API routes, return 404 instead of serving index.html
    if path.startswith('api/') or path.startswith('admin/'):
        return jsonify({'error': 'API endpoint not found'}), 404
    
    # Handle static file requests that might have wrong paths
    if path.startswith('reset-password/static/') or path.startswith('static/'):
        # Extract the actual static file path
        static_path = path.replace('reset-password/static/', 'static/')
        if static_path.startswith('static/'):
            static_file = static_path.replace('static/', '')
            static_file_path = os.path.join(build_dir, 'static', static_file)
            
            if os.path.exists(static_file_path):
                return send_from_directory(os.path.join(build_dir, 'static'), static_file)
            else:
                print(f"[ERROR] Static file not found in catch-all: {static_file_path}")
    
    # For static files, serve them directly
    full_path = os.path.join(build_dir, path)
    if path != "" and os.path.exists(full_path):
        return send_from_directory(build_dir, path)
    
    # For all other routes (including /reset-password/:token), serve index.html
    try:
        return send_from_directory(build_dir, 'index.html')
    except Exception as e:
        print(f"[ERROR] Failed to serve index.html: {e}")
        return jsonify({'error': f'Failed to serve index.html: {str(e)}'}), 500


# @app.route('/', defaults={'path': ''})
# @app.route('/<path:path>')
# def serve_react(path):
#     if path != "" and os.path.exists(os.path.join('build', path)):
#         return send_from_directory('build', path)
#     else:
#         return send_from_directory('build', 'index.html')

# Configuration loaded

if __name__ == '__main__':
    from config import CURRENT_ENV
    
    # Start background email processor
    try:
        start_email_processor()
        print("✅ Background email processor started")
    except Exception as e:
        print(f"⚠️ Failed to start email processor: {e}")
    
    if CURRENT_ENV == 'local':
        # Local development - use port 8000
        port = int(os.environ.get('PORT', 8000))
        debug = True
        print(f"[LOCAL] Starting Flask app on port {port} with debug=True")
    else:
        # Production - use environment port
        port = int(os.environ.get('PORT', 5000))
        debug = False
        print(f"[PRODUCTION] Starting Flask app on port {port} with debug=False")
    
    app.run(host='0.0.0.0', port=port, debug=debug)