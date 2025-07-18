import pytz
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from config import get_db_conn  # Updated import
import os
import bcrypt

# Load encryption key from environment or generate for dev
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key()
    # Remove or comment out debug prints for production
    # print(f"Generated new encryption key: {ENCRYPTION_KEY.decode()}")
    # print("Please add this to your .env file as ENCRYPTION_KEY=<key>")
else:
    if isinstance(ENCRYPTION_KEY, str):
        ENCRYPTION_KEY = ENCRYPTION_KEY.encode()
fernet = Fernet(ENCRYPTION_KEY)

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

def encrypt_sensitive_data(data):
    if not data:
        return data
    try:
        if isinstance(data, str):
            return fernet.encrypt(data.encode()).decode()
        return data
    except Exception as e:
        # print(f"Encryption error for data: {data[:50]}... Error: {str(e)}")
        return data

def decrypt_sensitive_data(encrypted_data):
    if not encrypted_data:
        return encrypted_data
    try:
        if isinstance(encrypted_data, str) and encrypted_data.startswith('gAAAAA'):
            try:
                return fernet.decrypt(encrypted_data.encode()).decode()
            except Exception as decrypt_error:
                # print(f"Decryption failed for data: {encrypted_data[:50]}... Error: {str(decrypt_error)}")
                return encrypted_data
        else:
            return encrypted_data
    except Exception as e:
        # print(f"Decryption error for data: {encrypted_data[:50]}... Error: {str(e)}")
        return encrypted_data

def is_account_locked(cur, user_id):
    cur.execute("SELECT lockout_until FROM users WHERE id=%s", (user_id,))
    row = cur.fetchone()
    if row and row[0]:
        lockout_until = row[0]
        now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
        if lockout_until and now < lockout_until:
            return True, lockout_until.isoformat()
    return False, None

def increment_failed_attempts(cur, user_id, max_attempts=5, lockout_minutes=15):
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
    cur.execute("UPDATE users SET failed_attempts=0, lockout_until=NULL WHERE id=%s", (user_id,))

def log_sensitive_operation(user_id, operation, details):
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        hk_now = datetime.now(pytz.timezone('Asia/Hong_Kong'))
        cur.execute(
            'INSERT INTO audit_logs (user_id, operation, details, timestamp) VALUES (%s, %s, %s, %s)',
            (user_id, operation, details, hk_now)
        )
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        # print(f"Error logging operation: {str(e)}")
        pass

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
