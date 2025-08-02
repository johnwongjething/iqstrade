# 🚀 IQSTrade Deployment Guide

## 📋 Table of Contents
1. [Production Deployment (Render + Railway)](#production-deployment)
2. [Local Development Setup](#local-development)
3. [Environment Variables](#environment-variables)
4. [Database Schema Updates](#database-schema)
5. [Testing & Verification](#testing)

---

## 🏭 Production Deployment (Render + Railway)

### 1. Environment Variables on Render

Add these environment variables to your Render backend service:

```bash
# === EXISTING VARIABLES (Keep these) ===
SECRET_KEY=your_secret_key_here
DATABASE_URL=postgresql://username:password@host:port/database_name
EMAIL_HOST=imap.gmail.com
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
JWT_SECRET_KEY=your_jwt_secret
CORS_ORIGINS=https://your-frontend-domain.onrender.com

# === NEW VARIABLES FOR OPENAI INTEGRATION ===
OPENAI_API_KEY=sk-your_openai_api_key_here

# === OPTIONAL: EMAIL SCHEDULER SETTINGS ===
EMAIL_CHECK_INTERVAL=900  # Check emails every 15 minutes (in seconds)
AUTO_SEND_ENABLED=true    # Enable/disable auto-send functionality
CONFIDENCE_THRESHOLD=0.8  # Minimum confidence for auto-send (0.0-1.0)

# === OPTIONAL: LOGGING SETTINGS ===
LOG_LEVEL=INFO
ENABLE_EMAIL_LOGGING=true

# === OPTIONAL: SECURITY SETTINGS ===
MAX_EMAIL_SIZE=10485760   # 10MB max email size
ALLOWED_ATTACHMENT_TYPES=pdf,jpg,jpeg,png
```

### 2. Database Schema Updates on Railway

Run this SQL script in your Railway PostgreSQL database:

```sql
-- Run the complete schema from: backend/migrations/20250716_openai_integration_schema.sql
```

**Quick Steps:**
1. Go to Railway dashboard
2. Select your PostgreSQL database
3. Go to "Query" tab
4. Copy and paste the SQL from `backend/migrations/20250716_openai_integration_schema.sql`
5. Click "Run"

### 3. Deploy Backend to Render

1. **Update requirements.txt** (already done)
2. **Deploy to Render** - your existing deployment should work
3. **Verify deployment** - check logs for any errors

---

## 💻 Local Development Setup

### 1. Create Local Environment File

```bash
# Copy the template
cp backend/env_local_template.txt backend/.env.local

# Edit .env.local with your local values
```

### 2. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 3. Setup Local Database

```bash
# Create local PostgreSQL database
createdb iqstrade_local

# Run the schema
psql iqstrade_local < backend/migrations/20250716_openai_integration_schema.sql
```

### 4. Test Local Setup

```bash
# Run the test script
python test_local_setup.py
```

### 5. Start Local Development

```bash
# Terminal 1: Start backend
python run_local.py

# Terminal 2: Start frontend
cd frontend
npm start
```

---

## 🔧 Environment Variables

### Production (Render)
- `OPENAI_API_KEY` - Your OpenAI API key
- `EMAIL_CHECK_INTERVAL` - How often to check emails (default: 300 seconds)
- `AUTO_SEND_ENABLED` - Enable auto-send (default: true)
- `CONFIDENCE_THRESHOLD` - Minimum confidence for auto-send (default: 0.8)

### Local Development (.env.local)
- `LOCAL_OPENAI_API_KEY` - Your OpenAI API key for local testing
- `LOCAL_DATABASE_URL` - Local PostgreSQL connection string
- `LOCAL_SECRET_KEY` - Local Flask secret key
- `LOCAL_JWT_SECRET_KEY` - Local JWT secret key

---

## 🗄️ Database Schema Updates

### New Tables Created:
1. **`customer_emails`** - Stores incoming emails
2. **`customer_email_replies`** - Stores AI-generated replies with confidence scores

### New Columns Added:
- `confidence_score` - AI confidence (0.0-1.0)
- `confidence_reasoning` - Detailed reasoning (JSON)
- `auto_send_recommended` - AI recommendation
- `auto_sent` - Whether actually auto-sent
- `auto_sent_at` - When auto-sent

---

## 🧪 Testing & Verification

### 1. Test Local Setup
```bash
python test_local_setup.py
```

### 2. Test OpenAI Integration
```bash
python test_openai_integration.py
```

### 3. Test Email Processing
```bash
python test_general_enquiries.py
```

### 4. Test Production Deployment

**Check Render Logs:**
- Look for OpenAI API connection errors
- Verify email processing is working
- Check database connection

**Test Email Ingestion:**
1. Send a test email to your configured email address
2. Check if it appears in the CustomerEmails interface
3. Verify AI classification and response generation

---

## 🔄 Switching Between Local and Production

### Local → Production
1. Set `FLASK_ENV=production` in Render
2. Ensure all production environment variables are set
3. Deploy to Render

### Production → Local
1. Set `FLASK_ENV=local` locally
2. Use `.env.local` for local environment variables
3. Run `python run_local.py`

---

## 🚨 Common Issues & Solutions

### CORS Errors
**Problem:** Frontend can't connect to backend
**Solution:** 
- Local: Check `config_local.py` CORS origins
- Production: Verify `CORS_ORIGINS` environment variable

### Database Connection Errors
**Problem:** Can't connect to database
**Solution:**
- Local: Check PostgreSQL is running and `.env.local` has correct database URL
- Production: Verify `DATABASE_URL` in Render environment variables

### OpenAI API Errors
**Problem:** OpenAI integration not working
**Solution:**
- Check API key is set correctly
- Verify API key has sufficient credits
- Check network connectivity

### Email Processing Not Working
**Problem:** Emails not being processed
**Solution:**
- Check email credentials in environment variables
- Verify IMAP settings
- Check if email scheduler is running

---

## 📞 Support

If you encounter issues:

1. **Check logs** - Both local and production
2. **Run test scripts** - `test_local_setup.py`
3. **Verify environment variables** - All required variables set
4. **Check database schema** - Tables created correctly

---

## 🎯 Demo Preparation Checklist

### 2 Weeks Before Demo:
- [ ] Deploy to production with OpenAI integration
- [ ] Test email processing end-to-end
- [ ] Verify auto-send functionality
- [ ] Test confidence scoring
- [ ] Prepare demo scenarios

### 1 Week Before Demo:
- [ ] Final testing of all features
- [ ] Prepare backup demo data
- [ ] Test on different browsers/devices
- [ ] Prepare presentation materials

### Day Before Demo:
- [ ] Final system check
- [ ] Backup current data
- [ ] Prepare demo script
- [ ] Test all demo scenarios

---

## 🚀 Quick Start Commands

```bash
# Local Development
cd backend
cp env_local_template.txt .env.local
# Edit .env.local with your values
python test_local_setup.py
python run_local.py

# Production Deployment
# 1. Update environment variables in Render
# 2. Run database schema in Railway
# 3. Deploy to Render
# 4. Test email processing
``` 