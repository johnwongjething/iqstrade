from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import (
    create_access_token, set_access_cookies, unset_jwt_cookies, jwt_required, get_jwt_identity, get_csrf_token
)
import json
import secrets
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import pytz
from utils.security import (
    encrypt_sensitive_data, decrypt_sensitive_data, validate_password, is_account_locked, increment_failed_attempts, reset_failed_attempts, log_sensitive_operation
)
from utils.helpers import get_hk_date_range
from utils.database import get_db_conn
from email_utils import send_simple_email

auth_routes = Blueprint('auth_routes', __name__)

# Registration
@auth_routes.route('/register', methods=['POST'])
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
    is_valid, message = validate_password(password)
    if not is_valid:
        return jsonify({'error': message}), 400
    try:
        conn = get_db_conn()
        cur = conn.cursor()
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

# Login
@auth_routes.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    captcha_token = data.get('captcha_token')
    from utils.helpers import verify_captcha
    if not verify_captcha(captcha_token):
        return jsonify({'error': 'CAPTCHA verification failed'}), 400
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash, role, approved, customer_name, customer_email, customer_phone FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    if not user:
        log_sensitive_operation(None, 'login_failed', f'Username {username} not found')
        cur.close()
        conn.close()
        return jsonify({'error': 'User not found'}), 401
    user_id, password_hash, role, approved, customer_name, customer_email, customer_phone = user
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
    set_access_cookies(response, access_token)
    cur.close()
    conn.close()
    return response

# Logout
@auth_routes.route('/logout', methods=['POST'])
def logout():
    response = jsonify({'message': 'Logged out successfully'})
    unset_jwt_cookies(response)
    return response, 200

# Get current user
@auth_routes.route('/me', methods=['GET'])
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

# Password reset request
@auth_routes.route('/request_password_reset', methods=['POST'])
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
        return jsonify({'message': 'If this email is registered, a reset link will be sent.'})
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

# Password reset
@auth_routes.route('/reset_password/<token>', methods=['POST'])
def reset_password(token):
    data = request.get_json()
    new_password = data.get('password')
    captcha_token = data.get('captcha_token')
    from utils.helpers import verify_captcha
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

# Approve user
@auth_routes.route('/approve_user/<int:user_id>', methods=['POST'])
@jwt_required()
def approve_user(user_id):
    user = json.loads(get_jwt_identity())
    if user['role'] not in ['staff', 'admin']:
        return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE users SET approved=TRUE WHERE id=%s", (user_id,))
    cur.execute("SELECT customer_email, customer_name FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    if row:
        customer_email, customer_name = row
        decrypted_email = decrypt_sensitive_data(customer_email) if customer_email else ''
        if decrypted_email:
            subject = "Your registration has been approved"
            body = f"Dear {customer_name},\n\nYour registration has been approved. You can now log in and use our services.\n\nThank you!"
            send_simple_email(decrypted_email, subject, body)
    return jsonify({'message': 'User approved'})

# Get unapproved users
@auth_routes.route('/unapproved_users', methods=['GET'])
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

# CSRF token endpoint
@auth_routes.route('/csrf-token', methods=['GET'])
@jwt_required()
def csrf_token():
    from flask_jwt_extended import get_jwt
    csrf_token = get_jwt()['csrf']
    return jsonify({'csrf_token': csrf_token})
