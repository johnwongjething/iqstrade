from flask import Blueprint, request, jsonify
from config import get_db_conn  # Updated import
from utils.security import decrypt_sensitive_data
from email_utils import send_contact_email, send_simple_email, send_unique_number_email, send_invoice_email  # Import all email functions
import pytz
from datetime import datetime

misc_routes = Blueprint('misc_routes', __name__)

@misc_routes.route('/contact', methods=['POST'])
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

@misc_routes.route('/ping', methods=['GET'])
def ping():
    return jsonify(message="pong"), 200

@misc_routes.route('/', methods=['GET'])
def root():
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

@misc_routes.route('/health', methods=['GET'])
def health():
    try:
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
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

@misc_routes.route('/request_username', methods=['POST'])
def request_username():
    from utils.security import decrypt_sensitive_data
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400
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
            if decrypted_email == email:
                username = db_username
                break
        except Exception:
            continue
    if not username:
        return jsonify({'error': 'No user found with this email'}), 404
    subject = "Your Username Recovery Request"
    body = f"Hi,\n\nYour username is: {username}\n\nIf you did not request this, please ignore this email.\n\nThanks,\nSupport Team"
    # Use imported send_simple_email
    try:
        send_simple_email(email, subject, body)
        return jsonify({'message': 'Username sent to your email'}), 200
    except Exception as e:
        return jsonify({'error': f'Email failed: {str(e)}'}), 500

@misc_routes.route('/notify_new_user', methods=['POST'])
def notify_new_user():
    data = request.get_json()
    customer_username = data.get('username')
    email = data.get('email')
    role = data.get('role')
    admin_email = 'ray6330099@gmail.com'
    subject = f"📬 New User Registration: {customer_username}"
    body = f"""Hi Admin,\n\nA new user has just registered on the system.\n\nUsername: {customer_username}\nEmail: {email}\nRole: {role}\n\nYou can log in to review and approve the user if necessary.\n\nBest regards,\nYour System\n"""
    # Use imported send_simple_email
    try:
        send_simple_email(admin_email, subject, body)
        return jsonify({'message': 'Notification email sent'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
