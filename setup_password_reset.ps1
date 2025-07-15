Write-Host "Setting up password reset security..."

# Install ESLint and security plugins
npm install --save-dev eslint eslint-plugin-security eslint-plugin-react

# Initialize ESLint configuration
echo y | npx eslint --init -- -- --javascript-modules --react --none --browser --json --y

# Create .eslintrc.json for security rules
@"
{
  "env": { "browser": true, "es2021": true },
  "extends": [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:security/recommended"
  ],
  "plugins": ["security", "react"],
  "rules": {
    "security/detect-object-injection": "warn",
    "security/detect-unsafe-regex": "error",
    "security/detect-non-literal-regexp": "error",
    "no-eval": "error",
    "react/prop-types": "off"
  }
}
"@ | Out-File -FilePath .eslintrc.json -Encoding UTF8

# Install GeeTest for China-compatible CAPTCHA
npm install geetest-react --save

# Create forgot-password.js
@"
import React, { useState, useContext } from 'react';
import { UserContext } from './UserContext';
import { TextField, Button, Snackbar, Alert } from '@mui/material';
import GeeTest from 'geetest-react';
import { API_BASE_URL } from './config';

const ForgotPassword = () => {
  const { setSnackbar } = useContext(UserContext);
  const [email, setEmail] = useState('');
  const [captchaToken, setCaptchaToken] = useState('');

  const isValidEmail = val => /^[\w\.-]+@[\w\.-]+\.\w+$/.test(val);

  const handleSubmit = async () => {
    if (!isValidEmail(email)) {
      setSnackbar({ open: true, message: 'Invalid email format', severity: 'error' });
      return;
    }
    try {
      const res = await fetch(`${API_BASE_URL}/api/request_password_reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, captchaToken }),
      });
      if (res.ok) {
        setSnackbar({ open: true, message: 'Reset link sent to email', severity: 'success' });
      } else if (res.status === 429) {
        setSnackbar({ open: true, message: 'Too many requests. Try again later.', severity: 'error' });
        setTimeout(() => handleSubmit(), 60000);
      } else if (res.status === 403) {
        setSnackbar({ open: true, message: 'Account locked due to excessive attempts', severity: 'error' });
      } else {
        setSnackbar({ open: true, message: 'Error sending reset link', severity: 'error' });
      }
    } catch (error) {
      setSnackbar({ open: true, message: 'Network error', severity: 'error' });
    }
  };

  const handleCaptcha = (token) => setCaptchaToken(token);

  return (
    <div>
      <TextField
        label="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <GeeTest onSuccess={handleCaptcha} appId={process.env.REACT_APP_GEETEST_ID} />
      <Button onClick={handleSubmit}>Send Reset Link</Button>
    </div>
  );
};

export default ForgotPassword;
"@ | Out-File -FilePath src/forgot-password.js -Encoding UTF8

# Create reset-password.js
@"
import React, { useState, useContext } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { UserContext } from './UserContext';
import { TextField, Button, Snackbar, Alert } from '@mui/material';
import { API_BASE_URL } from './config';

const ResetPassword = () => {
  const { token } = useParams();
  const { setSnackbar } = useContext(UserContext);
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const isValidPassword = val => /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$/.test(val);

  const handleSubmit = async () => {
    if (!isValidPassword(password)) {
      setSnackbar({ open: true, message: 'Password must be 8+ characters with uppercase, lowercase, number, and special character', severity: 'error' });
      return;
    }
    try {
      const res = await fetch(`${API_BASE_URL}/api/reset_password/${token}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      });
      if (res.ok) {
        setSnackbar({ open: true, message: 'Password reset successfully', severity: 'success' });
        navigate('/login');
      } else if (res.status === 429) {
        setSnackbar({ open: true, message: 'Too many requests. Try again later.', severity: 'error' });
        setTimeout(() => handleSubmit(), 60000);
      } else if (res.status === 403) {
        setSnackbar({ open: true, message: 'Account locked or invalid token', severity: 'error' });
      } else {
        setSnackbar({ open: true, message: 'Error resetting password', severity: 'error' });
      }
    } catch (error) {
      setSnackbar({ open: true, message: 'Network error', severity: 'error' });
    }
  };

  return (
    <div>
      <TextField
        label="New Password"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      <Button onClick={handleSubmit}>Reset Password</Button>
    </div>
  );
};

export default ResetPassword;
"@ | Out-File -FilePath src/reset-password.js -Encoding UTF8

# Append to app.py
@"
from flask_limiter.util import get_remote_address
import secrets
import smtplib
from email.mime.text import MIMEText
import re

@app.route('/api/request_password_reset', methods=['POST'])
@limiter.limit('3 per minute', key_func=get_remote_address)
def request_password_reset():
    data = request.get_json()
    email = data.get('email')
    captcha_token = data.get('captchaToken')

    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
        return jsonify({'error': 'Invalid email format'}), 400

    if not verify_captcha(captcha_token):
        return jsonify({'error': 'Invalid CAPTCHA'}), 400

    if is_account_locked(email):
        return jsonify({'error': 'Account locked due to excessive attempts'}), 403

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('SELECT id FROM users WHERE email=%s', (encrypt_sensitive_data(email),))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if not user:
        return jsonify({'error': 'Email not found'}), 404

    reset_token = secrets.token_urlsafe(32)
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('UPDATE users SET reset_token=%s, reset_token_expiry=%s WHERE id=%s',
                (reset_token, datetime.now() + timedelta(hours=1), user[0]))
    conn.commit()
    cur.close()
    conn.close()

    msg = MIMEText(f'Reset your password: {os.getenv('API_BASE_URL', 'https://iqstrade.onrender.com')}/reset-password/{reset_token}')
    msg['Subject'] = 'Password Reset Request'
    msg['From'] = os.getenv('SMTP_USERNAME')
    msg['To'] = email
    with smtplib.SMTP(os.getenv('SMTP_HOST'), os.getenv('SMTP_PORT')) as server:
        server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
        server.send_message(msg)

    log_sensitive_operation(user[0], 'password_reset_request')
    return jsonify({'message': 'Reset link sent'}), 200

@app.route('/api/reset_password/<token>', methods=['POST'])
@limiter.limit('3 per minute', key_func=get_remote_address)
def reset_password(token):
    data = request.get_json()
    password = data.get('password')

    if not validate_password(password):
        return jsonify({'error': 'Invalid password format'}), 400

    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute('SELECT id, email FROM users WHERE reset_token=%s AND reset_token_expiry > %s',
                (token, datetime.now()))
    user = cur.fetchone()
    if not user:
        cur.close()
        conn.close()
        return jsonify({'error': 'Invalid or expired token'}), 400

    if is_account_locked(decrypt_sensitive_data(user[1])):
        cur.close()
        conn.close()
        return jsonify({'error': 'Account locked due to excessive attempts'}), 403

    hashed_password = hash_password(password)
    cur.execute('UPDATE users SET password=%s, reset_token=NULL, reset_token_expiry=NULL WHERE id=%s',
                (hashed_password, user[0]))
    conn.commit()
    cur.close()
    conn.close()

    log_sensitive_operation(user[0], 'password_reset')
    return jsonify({'message': 'Password reset successfully'}), 200
"@ | Add-Content -Path app.py

# Run ESLint to check security
npx eslint src/forgot-password.js src/reset-password.js

Write-Host "Setup complete! Please install SonarLint extension in VS Code and add GeeTest credentials to .env."
Write-Host "Add to .env: REACT_APP_GEETEST_ID=your_geetest_id"
Write-Host "Add to .env: GEETEST_SECRET_KEY=your_geetest_secret"
Write-Host "Update app.py verify_captcha for GeeTest if needed."