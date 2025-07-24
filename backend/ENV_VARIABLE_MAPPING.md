# 🔄 Environment Variable Mapping Guide

## 📋 Production → Local Development

This guide shows how to map your Render production environment variables to local development.

### 🎯 **Key Principle: Same Variable Names**
- ✅ **Use the EXACT same variable names** as production
- ✅ **No need to change any code** - just copy values
- ✅ **Consistent configuration** across environments

---

## 📊 Variable Mapping Table

| **Production (Render)** | **Local (.env.local)** | **Description** |
|-------------------------|------------------------|-----------------|
| `DATABASE_URL` | `DATABASE_URL` | Railway PostgreSQL connection |
| `DB_HOST` | `DB_HOST` | Database host |
| `DB_NAME` | `DB_NAME` | Database name |
| `DB_USER` | `DB_USER` | Database user |
| `DB_PASSWORD` | `DB_PASSWORD` | Database password |
| `DB_PORT` | `DB_PORT` | Database port |
| `SECRET_KEY` | `SECRET_KEY` | Flask secret key |
| `JWT_SECRET_KEY` | `JWT_SECRET_KEY` | JWT signing key |
| `ENCRYPTION_KEY` | `ENCRYPTION_KEY` | Data encryption key |
| `EMAIL_HOST` | `EMAIL_HOST` | IMAP server (gmail.com) |
| `EMAIL_USERNAME` | `EMAIL_USERNAME` | Email username |
| `EMAIL_PASSWORD` | `EMAIL_PASSWORD` | Email app password |
| `EMAIL_PORT` | `EMAIL_PORT` | Email port (587) |
| `SMTP_SERVER` | `SMTP_SERVER` | SMTP server (smtp.gmail.com) |
| `SMTP_PORT` | `SMTP_PORT` | SMTP port (587) |
| `SMTP_USERNAME` | `SMTP_USERNAME` | SMTP username |
| `SMTP_PASSWORD` | `SMTP_PASSWORD` | SMTP password |
| `FROM_EMAIL` | `FROM_EMAIL` | From email address |
| `GOOGLE_APPLICATION_CREDENTIALS` | `GOOGLE_APPLICATION_CREDENTIALS` | Google OCR credentials file |
| `CLOUDINARY_CLOUD_NAME` | `CLOUDINARY_CLOUD_NAME` | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | `CLOUDINARY_API_KEY` | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | `CLOUDINARY_API_SECRET` | Cloudinary API secret |
| `GEETEST_ID` | `GEETEST_ID` | Geetest captcha ID |
| `GEETEST_KEY` | `GEETEST_KEY` | Geetest captcha key |
| `JWT_ACCESS_TOKEN_EXPIRES` | `JWT_ACCESS_TOKEN_EXPIRES` | JWT token expiry (900) |

---

## 🆕 New Variables for OpenAI Integration

| **Variable** | **Value** | **Description** |
|--------------|-----------|-----------------|
| `OPENAI_API_KEY` | `sk-...` | Your OpenAI API key |
| `EMAIL_CHECK_INTERVAL` | `300` | Check emails every 5 minutes |
| `AUTO_SEND_ENABLED` | `true` | Enable auto-send functionality |
| `CONFIDENCE_THRESHOLD` | `0.8` | Minimum confidence for auto-send |

---

## 🔧 Local Development Overrides

| **Variable** | **Local Value** | **Production Value** | **Reason** |
|--------------|-----------------|---------------------|------------|
| `FLASK_ENV` | `local` | `production` | Environment detection |
| `FLASK_DEBUG` | `true` | `false` | Debug mode for development |
| `ALLOWED_ORIGINS` | `http://localhost:3000,...` | `https://iqstrade.onrender.com` | CORS for localhost |
| `FORCE_HTTPS` | `0` | `1` | Disable HTTPS locally |
| `JWT_COOKIE_SECURE` | `false` | `true` | Allow HTTP cookies locally |

---

## 📝 Quick Setup Steps

### 1. Create Local Environment File
```bash
cd backend
python setup_local_env.py
```

### 2. Copy Values from Render
- Go to your Render dashboard
- Navigate to Environment section
- Copy all values to `.env.local`
- Replace `your_*_from_render` placeholders

### 3. Add OpenAI API Key
```bash
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your_actual_api_key_here
```

### 4. Test Setup
```bash
python test_local_setup.py
```

### 5. Start Development
```bash
# Terminal 1: Backend
python run_local.py

# Terminal 2: Frontend
cd frontend
npm start
```

---

## 🎯 Benefits of This Approach

### ✅ **Consistency**
- Same variable names across environments
- No code changes needed
- Easy to maintain

### ✅ **Simplicity**
- Copy-paste from production
- No complex mapping
- Clear documentation

### ✅ **Reliability**
- Uses same services (Railway, Gmail, Google OCR)
- Same configuration as production
- Reduced debugging time

### ✅ **Security**
- Local overrides for development
- Production security maintained
- Sensitive data handled properly

---

## 🚨 Important Notes

### **Database Connection**
- Uses the **same Railway database** as production
- **No local database** needed
- **All data is shared** between local and production

### **Email Services**
- Uses the **same Gmail account** as production
- **Same IMAP/SMTP settings**
- **Emails will be processed** by local development

### **File Storage**
- Uses the **same Cloudinary account** as production
- **Files uploaded locally** will appear in production
- **Google OCR credentials** shared

### **Security**
- **JWT cookies** configured for localhost
- **HTTPS enforcement** disabled locally
- **CORS** configured for localhost

---

## 🔍 Troubleshooting

### **Common Issues:**

1. **CORS Errors**
   - Check `ALLOWED_ORIGINS` includes `http://localhost:3000`
   - Verify frontend is running on correct port

2. **Database Connection**
   - Verify `DATABASE_URL` is copied correctly from Render
   - Check Railway database is accessible

3. **Email Issues**
   - Verify email credentials are copied correctly
   - Check Gmail app password is valid

4. **OpenAI Errors**
   - Verify API key is valid and has credits
   - Check network connectivity

### **Testing Commands:**
```bash
# Test environment setup
python test_local_setup.py

# Test database connection
python check_db_schema.py

# Test OpenAI integration
python test_openai_integration.py
``` 