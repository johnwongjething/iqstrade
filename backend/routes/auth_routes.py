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
    encrypt_sensitive_data, decrypt_sensitive_data, validate_password, is_account_locked, increment_failed_attempts, reset_failed_attempts, log_sensitive_operation, hash_password
)
from utils.helpers import get_hk_date_range
from config import get_db_conn
from email_utils import send_simple_email
import os
# from geetest import GeetestLib
import requests
import logging
import re
import bcrypt

auth_routes = Blueprint('auth_routes', __name__)

# Set a 10MB max upload size for all file uploads
from flask import Flask

def set_max_content_length(app: Flask):
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

# Registration
@auth_routes.route('/check-username', methods=['POST'])
def check_username():
    """Check if username is available"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'available': False, 'error': 'Username is required'}), 400
        
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        exists = cur.fetchone() is not None
        cur.close()
        conn.close()
        
        return jsonify({'available': not exists, 'username': username})
    except Exception as e:
        return jsonify({'available': False, 'error': 'Server error'}), 500

@auth_routes.route('/check-email', methods=['POST'])
def check_email():
    """Check if email is available"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        
        if not email:
            return jsonify({'available': False, 'error': 'Email is required'}), 400
        
        # Basic email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'available': False, 'error': 'Invalid email format'}), 400
        
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE customer_email = %s", (email,))
        exists = cur.fetchone() is not None
        cur.close()
        conn.close()
        
        return jsonify({'available': not exists, 'email': email})
    except Exception as e:
        return jsonify({'available': False, 'error': 'Server error'}), 500

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
    
    # Basic email validation
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, customer_email):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Password validation
    is_valid, message = validate_password(password)
    if not is_valid:
        return jsonify({'error': message}), 400
    
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        
        # Check if username is already taken
        cur.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'error': 'Username is already taken'}), 400
        
        # Check if email is already taken
        cur.execute("SELECT id FROM users WHERE customer_email = %s", (customer_email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'error': 'Email is already taken by another user'}), 400
        
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
    # GEETEST_ID loaded from environment
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
            # Geetest register API response: {resp_json}
            challenge = resp_json.get("challenge", "")
        except Exception as e:
            # Geetest v4 register error (JSON parse): {e}
            logging.error(f"[Geetest] Register error (JSON parse): {e}")
            challenge = ""
    except Exception as e:
        # Geetest v4 register error: {e}
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
    logging.info("[Login] /login called")
    data = request.get_json()
    logging.info(f"[Login] Request data: {data}")
    username = data.get('username')
    password = data.get('password')
    lot_number = data.get('lot_number')
    captcha_output = data.get('captcha_output')
    pass_token = data.get('pass_token')
    captcha_id = os.environ.get('GEETEST_ID')
    # GEETEST_ID loaded from environment
    if not (lot_number and captcha_output and pass_token):
        logging.warning("[Login] Missing Geetest data")
        return jsonify({'error': 'Missing Geetest data'}), 400
    logging.info(f"[Login] captcha_id: {captcha_id}")
    def verify_geetest_v4(lot_number, captcha_output, pass_token, captcha_id):
        # Geetest verification called
        logging.info(f"[Geetest] Validate payload: {{'lot_number': lot_number, 'captcha_output': captcha_output, 'pass_token': pass_token, 'captcha_id': captcha_id}}")
        # BYPASS: Always return True for development/testing
        logging.info('[Geetest] BYPASS: Always returning True for verification')
        return True
        # --- Real validation below (keep for future use) ---
        # url = "https://gcaptcha4.geetest.com/validate"
        # payload = {
        #     "lot_number": lot_number,
        #     "captcha_output": captcha_output,
        #     "pass_token": pass_token,
        #     "captcha_id": captcha_id
        # }
        # try:
        #     resp = requests.post(url, json=payload, timeout=5)
        #     logging.info(f"[Geetest] Validate raw response: {resp.text}")
        #     try:
        #         resp_json = resp.json()
        #         print("Geetest validate API response:", resp_json)
        #         return resp_json.get("result") == "success"
        #     except Exception as e:
        #         print("Geetest v4 validate error (JSON parse):", e)
        #         logging.error(f"[Geetest] Validate error (JSON parse): {e}")
        #         return False
        # except Exception as e:
        #     print("Geetest v4 validate error:", e)
        #     logging.error(f"[Geetest] Validate error: {e}")
        #     return False
    if not verify_geetest_v4(lot_number, captcha_output, pass_token, captcha_id):
        logging.warning("[Login] Geetest verification failed")
        return jsonify({'error': 'Geetest verification failed'}), 400
    # Proceed with login logic
    conn = get_db_conn()
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
    
    # Debug: Decode and log token info
    import jwt as pyjwt
    try:
        decoded = pyjwt.decode(access_token, os.environ.get('JWT_SECRET_KEY', 'your-secret-key'), algorithms=['HS256'])
        logging.info(f"[JWT DEBUG] Token created at: {decoded.get('iat')}")
        logging.info(f"[JWT DEBUG] Token expires at: {decoded.get('exp')}")
        logging.info(f"[JWT DEBUG] Current time: {int(datetime.now().timestamp())}")
        logging.info(f"[JWT DEBUG] Token valid for: {decoded.get('exp') - decoded.get('iat')} seconds")
    except Exception as e:
        logging.error(f"[JWT DEBUG] Error decoding token: {e}")
    
    log_sensitive_operation(user_id, 'login', 'User logged in successfully')
    response = make_response(jsonify({
        "customer_name": customer_name,
        "customer_email": customer_email,
        "customer_phone": customer_phone,
        'role': role,
        'username': username
    }), 200)
    
    # Clear old cookies first with explicit domain and path
    response.delete_cookie('access_token_cookie', path='/', domain=None)
    response.delete_cookie('refresh_token_cookie', path='/api/refresh', domain=None)
    
    # Set new cookies
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    
    # Debug: Log the cookies being set
    logging.info(f"[DEBUG] Response cookies: {dict(response.headers)}")
    logging.info(f"[DEBUG] Set-Cookie headers: {[h for h in response.headers if h[0].lower() == 'set-cookie']}")
    
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

# Test endpoint to check JWT without database
@auth_routes.route('/test-jwt', methods=['GET'])
@jwt_required()
def test_jwt():
    logging.info(f"[JWT TEST] JWT is working!")
    return jsonify({"message": "JWT is working!"})

# Get current user
@auth_routes.route('/me', methods=['GET'])
@jwt_required()
def get_me():
    # Debug: Log all cookies
    logging.info(f"[DEBUG] All cookies: {dict(request.cookies)}")
    logging.info(f"[DEBUG] Access token cookie: {request.cookies.get('access_token_cookie')}")
    logging.info(f"[DEBUG] Refresh token cookie: {request.cookies.get('refresh_token_cookie')}")
    
    # Debug: Decode the token being used
    import jwt as pyjwt
    try:
        token = request.cookies.get('access_token_cookie')
        if token:
            decoded = pyjwt.decode(token, os.environ.get('JWT_SECRET_KEY', 'your-secret-key'), algorithms=['HS256'])
            logging.info(f"[DEBUG] Token being used - created at: {decoded.get('iat')}, expires at: {decoded.get('exp')}")
    except Exception as e:
        logging.error(f"[DEBUG] Error decoding token in /me: {e}")
    
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

def is_strong_password(password):
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True

@auth_routes.route('/request_password_reset', methods=['POST'])
def request_password_reset():
    data = request.get_json()
    email = data.get('email')
    if not email:
        return jsonify({'error': 'Email is required'}), 400

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE customer_email = %s", (email,))
    row = cur.fetchone()
    if not row:
        return jsonify({'message': 'If the email exists, a reset link will be sent.'})

    user_id = row[0]
    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(pytz.timezone('Asia/Hong_Kong')) + timedelta(hours=2)
    cur.execute("INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)", (user_id, token, expires_at))
    conn.commit()
    cur.close()
    conn.close()

    reset_link = f"https://iqstrade.onrender.com/reset-password/{token}"
    send_simple_email(email, "Password Reset Request", f"Click the link to reset your password: {reset_link}\nThis link will expire in 2 hours.")

    return jsonify({'message': 'If the email exists, a reset link will be sent.'})

@auth_routes.route('/reset_password/<token>', methods=['POST'])
def reset_password(token):
    data = request.get_json()
    new_password = data.get('password')
    if not is_strong_password(new_password):
        return jsonify({'error': 'Password must be at least 8 characters and include uppercase, lowercase, number, and special character.'}), 400

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, expires_at FROM password_reset_tokens WHERE token = %s", (token,))
    row = cur.fetchone()
    if not row:
        return jsonify({'error': 'Invalid or expired token.'}), 400

    user_id, expires_at = row
    if datetime.now(pytz.timezone('Asia/Hong_Kong')) > expires_at:
        return jsonify({'error': 'Token expired.'}), 400

    hashed = hash_password(new_password)
    cur.execute("UPDATE users SET password_hash = %s WHERE id = %s", (hashed, user_id))
    cur.execute("DELETE FROM password_reset_tokens WHERE token = %s", (token,))
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({'message': 'Password reset successful.'})

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

@auth_routes.route('/verify_sensitive_access', methods=['POST'])
def verify_sensitive_access():
    """
    POST body: { email, bl_number, invoice_number, ctn_number, ctn (optional) }
    At least one of bl_number, invoice_number, ctn_number must be provided.
    Returns 200 with {success: true} if email matches the record, else 200 with {success: false}.
    """
    import sys
    data = request.get_json()
    email = data.get('email')
    bl_number = data.get('bl_number')
    invoice_number = data.get('invoice_number')
    ctn_number = data.get('ctn_number')
    ctn = data.get('ctn')
    if not email or not (bl_number or invoice_number or ctn_number):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    conn = get_db_conn()
    cur = conn.cursor()
    # Try BL first
    if bl_number:
        cur.execute("SELECT customer_email FROM bill_of_lading WHERE bl_number = %s", (bl_number,))
        bl_row = cur.fetchone()
        if not bl_row:
            cur.close(); conn.close()
            return jsonify({'success': False, 'message': 'BL not found'}), 200
        bl_email = bl_row[0]
        # Now scan users table and decrypt each email to find a match
        cur.execute("SELECT customer_email, customer_phone FROM users")
        user_rows = cur.fetchall()
        found = False
        for db_email, db_phone in user_rows:
            decrypted_email = decrypt_sensitive_data(db_email) if db_email else ''
            decrypted_phone = decrypt_sensitive_data(db_phone) if db_phone else ''
            if decrypted_email.lower() == bl_email.lower():
                found = True
                break
        if not found:
            cur.close(); conn.close()
            return jsonify({'success': False, 'message': 'No user found matching BL email'}), 200
        # Now check if provided email matches
        if bl_email.lower() != email.lower():
            cur.close(); conn.close()
            return jsonify({'success': False, 'message': 'Email does not match record for this BL'}), 200
        # Optionally check CTN if needed (using decrypted_phone)
        if ctn and decrypted_phone and ctn != decrypted_phone:
            cur.close(); conn.close()
            return jsonify({'success': False, 'message': 'CTN does not match record for this BL'}), 200
        cur.close(); conn.close()
        return jsonify({'success': True, 'message': 'Verified for BL'}), 200
    # Try invoice
    if invoice_number:
        cur.execute("SELECT customer_email, customer_phone FROM users u JOIN invoice_table i ON u.id = i.user_id WHERE i.invoice_number = %s", (invoice_number,))
        row = cur.fetchone()
        if not row:
            cur.close(); conn.close()
            return jsonify({'success': False, 'message': 'Invoice not found'}), 200
        db_email, db_phone = row
        decrypted_email = decrypt_sensitive_data(db_email) if db_email else ''
        decrypted_phone = decrypt_sensitive_data(db_phone) if db_phone else ''
        if decrypted_email.lower() != email.lower():
            cur.close(); conn.close()
            return jsonify({'success': False, 'message': 'Email does not match record for this invoice'}), 200
        if ctn and decrypted_phone and ctn != decrypted_phone:
            cur.close(); conn.close()
            return jsonify({'success': False, 'message': 'CTN does not match record for this invoice'}), 200
        cur.close(); conn.close()
        return jsonify({'success': True, 'message': 'Verified for invoice'}), 200
    # Try CTN
    if ctn_number:
        cur.execute("SELECT customer_email, customer_phone FROM users u JOIN ctn_table c ON u.id = c.user_id WHERE c.ctn_number = %s", (ctn_number,))
        row = cur.fetchone()
        if not row:
            cur.close(); conn.close()
            return jsonify({'success': False, 'message': 'CTN not found'}), 200
        db_email, db_phone = row
        decrypted_email = decrypt_sensitive_data(db_email) if db_email else ''
        decrypted_phone = decrypt_sensitive_data(db_phone) if db_phone else ''
        if decrypted_email.lower() != email.lower():
            cur.close(); conn.close()
            return jsonify({'success': False, 'message': 'Email does not match record for this CTN'}), 200
        if ctn and decrypted_phone and ctn != decrypted_phone:
            cur.close(); conn.close()
            return jsonify({'success': False, 'message': 'CTN does not match record for this CTN'}), 200
        cur.close(); conn.close()
        return jsonify({'success': True, 'message': 'Verified for CTN'}), 200
    cur.close(); conn.close()
    return jsonify({'success': False, 'message': 'No valid identifier provided'}), 400

# @auth_routes.route('/verify_sensitive_access', methods=['POST'])
# def verify_sensitive_access():
#     """
#     POST body: { email, bl_number, invoice_number, ctn_number, ctn (optional) }
#     At least one of bl_number, invoice_number, ctn_number must be provided.
#     Returns 200 if email matches the record for the BL/invoice/CTN, else 403.
#     """
#     import sys
#     data = request.get_json()
#     email = data.get('email')
#     bl_number = data.get('bl_number')
#     invoice_number = data.get('invoice_number')
#     ctn_number = data.get('ctn_number')
#     ctn = data.get('ctn')
#     print(f"[DEBUG] Incoming verify_sensitive_access: email={email}, bl_number={bl_number}, invoice_number={invoice_number}, ctn_number={ctn_number}, ctn={ctn}", file=sys.stderr)
#     if not email or not (bl_number or invoice_number or ctn_number):
#         print(f"[DEBUG] Missing required fields", file=sys.stderr)
#         return jsonify({'error': 'Missing required fields'}), 400

#     conn = get_db_conn()
#     cur = conn.cursor()
#     # Try BL first
#     if bl_number:
#         print(f"[DEBUG] Executing SQL for BL: SELECT customer_email FROM bill_of_lading WHERE bl_number = {bl_number}", file=sys.stderr)
#         cur.execute("SELECT customer_email FROM bill_of_lading WHERE bl_number = %s", (bl_number,))
#         bl_row = cur.fetchone()
#         print(f"[DEBUG] bill_of_lading row: {bl_row}", file=sys.stderr)
#         if not bl_row:
#             cur.close(); conn.close()
#             print(f"[DEBUG] BL not found for bl_number={bl_number}", file=sys.stderr)
#             return jsonify({'error': 'BL not found'}), 404
#         bl_email = bl_row[0]
#         # Now scan users table and decrypt each email to find a match
#         cur.execute("SELECT customer_email, customer_phone FROM users")
#         user_rows = cur.fetchall()
#         print(f"[DEBUG] Users fetched: {len(user_rows)}", file=sys.stderr)
#         found = False
#         for db_email, db_phone in user_rows:
#             decrypted_email = decrypt_sensitive_data(db_email) if db_email else ''
#             decrypted_phone = decrypt_sensitive_data(db_phone) if db_phone else ''
#             if decrypted_email.lower() == bl_email.lower():
#                 print(f"[DEBUG] Decrypted user email matches BL email: {decrypted_email}", file=sys.stderr)
#                 found = True
#                 break
#         if not found:
#             cur.close(); conn.close()
#             print(f"[DEBUG] No user found with decrypted email matching BL email {bl_email}", file=sys.stderr)
#             return jsonify({'error': 'BL not found'}), 404
#         # Now check if provided email matches
#         if bl_email.lower() != email.lower():
#             cur.close(); conn.close()
#             print(f"[DEBUG] Provided email does not match BL email: {email} != {bl_email}", file=sys.stderr)
#             return jsonify({'error': 'Email does not match record for this BL'}), 403
#         # Optionally check CTN if needed (using decrypted_phone)
#         if ctn and decrypted_phone and ctn != decrypted_phone:
#             cur.close(); conn.close()
#             print(f"[DEBUG] CTN does not match: {ctn} != {decrypted_phone}", file=sys.stderr)
#             return jsonify({'error': 'CTN does not match record for this BL'}), 403
#         cur.close(); conn.close()
#         print(f"[DEBUG] Success: Verified for BL", file=sys.stderr)
#         return jsonify({'success': True, 'message': 'Verified for BL'})
#     # Try invoice
#     if invoice_number:
#         cur.execute("SELECT customer_email, customer_phone FROM users u JOIN invoice_table i ON u.id = i.user_id WHERE i.invoice_number = %s", (invoice_number,))
#         row = cur.fetchone()
#         if not row:
#             cur.close(); conn.close()
#             return jsonify({'error': 'Invoice not found'}), 404
#         db_email, db_phone = row
#         decrypted_email = decrypt_sensitive_data(db_email) if db_email else ''
#         decrypted_phone = decrypt_sensitive_data(db_phone) if db_phone else ''
#         if decrypted_email.lower() != email.lower():
#             cur.close(); conn.close()
#             return jsonify({'error': 'Email does not match record for this invoice'}), 403
#         if ctn and decrypted_phone and ctn != decrypted_phone:
#             cur.close(); conn.close()
#             return jsonify({'error': 'CTN does not match record for this invoice'}), 403
#         cur.close(); conn.close()
#         return jsonify({'success': True, 'message': 'Verified for invoice'})
#     # Try CTN
#     if ctn_number:
#         cur.execute("SELECT customer_email, customer_phone FROM users u JOIN ctn_table c ON u.id = c.user_id WHERE c.ctn_number = %s", (ctn_number,))
#         row = cur.fetchone()
#         if not row:
#             cur.close(); conn.close()
#             return jsonify({'error': 'CTN not found'}), 404
#         db_email, db_phone = row
#         decrypted_email = decrypt_sensitive_data(db_email) if db_email else ''
#         decrypted_phone = decrypt_sensitive_data(db_phone) if db_phone else ''
#         if decrypted_email.lower() != email.lower():
#             cur.close(); conn.close()
#             return jsonify({'error': 'Email does not match record for this CTN'}), 403
#         if ctn and decrypted_phone and ctn != decrypted_phone:
#             cur.close(); conn.close()
#             return jsonify({'error': 'CTN does not match record for this CTN'}), 403
#         cur.close(); conn.close()
#         return jsonify({'success': True, 'message': 'Verified for CTN'})
#     cur.close(); conn.close()
#     return jsonify({'error': 'No valid identifier provided'}), 400

@auth_routes.route('/update-profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update customer profile information"""
    try:
        user = json.loads(get_jwt_identity())
        user_id = user['id']
        username = user['username']
        
        data = request.get_json()
        customer_name = data.get('customer_name', '').strip()
        customer_email = data.get('customer_email', '').strip()
        customer_phone = data.get('customer_phone', '').strip()
        
        # Validation
        if not customer_name:
            return jsonify({'error': 'Customer name is required'}), 400
        
        if not customer_email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Basic email validation
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, customer_email):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Check if email is already taken by another user
        conn = get_db_conn()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id FROM users 
            WHERE customer_email = %s AND id != %s
        """, (customer_email, user_id))
        
        if cur.fetchone():
            cur.close()
            conn.close()
            return jsonify({'error': 'Email is already taken by another user'}), 400
        
        # Update profile
        cur.execute("""
            UPDATE users 
            SET customer_name = %s, customer_email = %s, customer_phone = %s
            WHERE id = %s
        """, (customer_name, customer_email, customer_phone, user_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Log the action
        # User {username} updated their profile
        
        return jsonify({
            'message': 'Profile updated successfully',
            'profile': {
                'customer_name': customer_name,
                'customer_email': customer_email,
                'customer_phone': customer_phone
            }
        })
        
    except Exception as e:
        print(f"[ERROR] Profile update failed: {e}")
        return jsonify({'error': 'Failed to update profile'}), 500

@auth_routes.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    """Change user password"""
    try:
        user = json.loads(get_jwt_identity())
        user_id = user['id']
        username = user['username']
        
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Validation
        if not current_password or not new_password or not confirm_password:
            return jsonify({'error': 'All password fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'New password and confirmation do not match'}), 400
        
        # Password strength validation
        if len(new_password) < 8:
            return jsonify({'error': 'Password must be at least 8 characters long'}), 400
        
        import re
        if not re.search(r'[A-Z]', new_password):
            return jsonify({'error': 'Password must include an uppercase letter'}), 400
        
        if not re.search(r'[a-z]', new_password):
            return jsonify({'error': 'Password must include a lowercase letter'}), 400
        
        if not re.search(r'\d', new_password):
            return jsonify({'error': 'Password must include a number'}), 400
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', new_password):
            return jsonify({'error': 'Password must include a special character'}), 400
        
        # Verify current password
        conn = get_db_conn()
        cur = conn.cursor()
        
        cur.execute("SELECT password_hash FROM users WHERE id = %s", (user_id,))
        result = cur.fetchone()
        
        if not result:
            cur.close()
            conn.close()
            return jsonify({'error': 'User not found'}), 404
        
        stored_password_hash = result[0]
        
        if not check_password_hash(stored_password_hash, current_password):
            cur.close()
            conn.close()
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Hash new password
        new_password_hash = generate_password_hash(new_password)
        
        # Update password
        cur.execute("""
            UPDATE users 
            SET password_hash = %s
            WHERE id = %s
        """, (new_password_hash, user_id))
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Log the action
        print(f"[PASSWORD CHANGE] User {username} changed their password")
        
        return jsonify({'message': 'Password changed successfully'})
        
    except Exception as e:
        print(f"[ERROR] Password change failed: {e}")
        return jsonify({'error': 'Failed to change password'}), 500
