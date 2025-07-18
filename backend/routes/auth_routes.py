from flask import Blueprint, request, jsonify, make_response, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, set_access_cookies, set_refresh_cookies, unset_jwt_cookies, jwt_required, get_jwt_identity, get_csrf_token
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
from config import get_db_conn
from email_utils import send_simple_email
import os
# from geetest import GeetestLib
import requests
import logging

auth_routes = Blueprint('auth_routes', __name__)

# Set a 10MB max upload size for all file uploads
from flask import Flask

def set_max_content_length(app: Flask):
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

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

# Geetest register endpoint
@auth_routes.route('/geetest/register', methods=['GET'])
def geetest_register():
    import os
    geetest_id = os.environ.get('GEETEST_ID')
    print("GEETEST_ID being sent:", geetest_id)
    logging.info(f"[Geetest] /register called, captcha_id: {geetest_id}")
    url = "https://gcaptcha4.geetest.com/register"
    payload = {
        "captcha_id": geetest_id,
        "client_type": "web",
        "lang": "en"
    }
    challenge = ""
    try:
        logging.info(f"[Geetest] Register payload: {payload}")
        resp = requests.post(url, json=payload, timeout=5)
        logging.info(f"[Geetest] Register raw response: {resp.text}")
        try:
            resp_json = resp.json()
            print("Geetest register API response:", resp_json)
            challenge = resp_json.get("challenge", "")
        except Exception as e:
            print("Geetest v4 register error (JSON parse):", e)
            logging.error(f"[Geetest] Register error (JSON parse): {e}")
            challenge = ""
    except Exception as e:
        print("Geetest v4 register error:", e)
        logging.error(f"[Geetest] Register error: {e}")
        challenge = ""
    return (
        jsonify({
            "success": 1,
            "gt": geetest_id,
            "challenge": challenge,
            "new_captcha": True
        }),
        200,
        {'Content-Type': 'application/json'}
    )

# Login
@auth_routes.route('/login', methods=['POST'])
def login():
    print("AUTH ROUTE LOGIN CALLED")
    logging.info("[Login] /login called")
    data = request.get_json()
    logging.info(f"[Login] Request data: {data}")
    username = data.get('username')
    password = data.get('password')
    lot_number = data.get('lot_number')
    captcha_output = data.get('captcha_output')
    pass_token = data.get('pass_token')
    if not (lot_number and captcha_output and pass_token):
        logging.warning("[Login] Missing Geetest data")
        return jsonify({'error': 'Missing Geetest data'}), 400
    captcha_id = os.environ.get('GEETEST_ID')
    print("captcha_id being sent:", captcha_id)
    logging.info(f"[Login] captcha_id: {captcha_id}")
    def verify_geetest_v4(lot_number, captcha_output, pass_token, captcha_id):
        # Real Geetest v4 validation
        url = "https://gcaptcha4.geetest.com/validate"
        payload = {
            "lot_number": lot_number,
            "captcha_output": captcha_output,
            "pass_token": pass_token,
            "captcha_id": captcha_id
        }
        logging.info(f"[Geetest] Validate payload: {payload}")
        try:
            resp = requests.post(url, json=payload, timeout=5)
            logging.info(f"[Geetest] Validate raw response: {resp.text}")
            try:
                resp_json = resp.json()
                print("Geetest validate API response:", resp_json)
                return resp_json.get("result") == "success"
            except Exception as e:
                print("Geetest v4 validate error (JSON parse):", e)
                logging.error(f"[Geetest] Validate error (JSON parse): {e}")
                return False
        except Exception as e:
            print("Geetest v4 validate error:", e)
            logging.error(f"[Geetest] Validate error: {e}")
            return False
    if not verify_geetest_v4(lot_number, captcha_output, pass_token, captcha_id):
        logging.warning("[Login] Geetest verification failed")
        return jsonify({'error': 'Geetest verification failed'}), 400
    # Proceed with login logic
    conn = get_db_conn()
    print("conn from get_db_conn:", conn)
    logging.info(f"[Login] DB connection: {conn}")
    cur = conn.cursor()
    cur.execute("SELECT id, password_hash, role, approved, customer_name, customer_email, customer_phone FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    logging.info(f"[Login] DB user fetch: {user}")
    if not user:
        log_sensitive_operation(None, 'login_failed', f'Username {username} not found')
        cur.close()
        conn.close()
        logging.warning(f"[Login] User not found: {username}")
        return jsonify({'error': 'User not found'}), 401
    user_id, password_hash, role, approved, customer_name, customer_email, customer_phone = user
    locked, lockout_until = is_account_locked(cur, user_id)
    logging.info(f"[Login] Account locked: {locked}, lockout_until: {lockout_until}")
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
        logging.warning(f"[Login] Incorrect password for user {username}, attempts: {failed_attempts}")
        if lockout_until:
            return jsonify({'error': f'Account locked. Try again after {lockout_until}'}), 403
        return jsonify({'error': 'Incorrect password'}), 401
    reset_failed_attempts(cur, user_id)
    conn.commit()
    identity = json.dumps({'id': user_id, 'role': role, 'username': username})
    access_token = create_access_token(identity=identity)
    refresh_token = create_refresh_token(identity=identity)
    log_sensitive_operation(user_id, 'login', 'User logged in successfully')
    response = make_response(jsonify({
        "customer_name": customer_name,
        "customer_email": customer_email,
        "customer_phone": customer_phone,
        'role': role,
        'username': username
    }), 200)
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    cur.close()
    conn.close()
    logging.info(f"[Login] Login successful for user {username}")
    return response

# Refresh endpoint
@auth_routes.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity)
    response = jsonify({"msg": "token refreshed"})
    set_access_cookies(response, access_token)
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
    print("🔍 /me route hit")
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
    reset_link = f"https://iqstrade.onrender.com/reset-password/{token}"
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
    # If CSRF protection is disabled, 'csrf' key will not exist
    jwt_data = get_jwt()
    csrf_token = jwt_data.get('csrf')
    if csrf_token is None:
        # Return a dummy token or a message for frontend compatibility
        return jsonify({'csrf_token': None, 'message': 'CSRF protection is disabled on the server.'})
    return jsonify({'csrf_token': csrf_token})
