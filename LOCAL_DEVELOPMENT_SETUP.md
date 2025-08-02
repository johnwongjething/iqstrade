# Local Development Setup Guide

This guide explains how to run your IQS Trade system locally while keeping production running.

## 🎯 Overview

Your system is designed to run both local and production environments simultaneously:
- **Production**: Runs on Render.com with production database
- **Local**: Runs on your machine with local database

## 🚀 Quick Start

### Option 1: Using Scripts (Recommended)

#### Backend (Local)
```bash
cd backend
python run_local.py
```

#### Frontend (Local)
```bash
cd frontend
node start_local.js
```

### Option 2: Manual Setup

#### Backend Setup
```bash
cd backend
export FLASK_ENV=local
export LOCAL_DB_NAME=iqstrade_local
export LOCAL_DB_USER=postgres
export LOCAL_DB_PASSWORD=123456
export LOCAL_DB_HOST=localhost
export LOCAL_DB_PORT=5432
export PORT=8000
python app.py
```

#### Frontend Setup
```bash
cd frontend
export NODE_ENV=development
export REACT_APP_API_BASE_URL=http://localhost:8000
npm start
```

## 🗄️ Database Setup

### Local PostgreSQL Database
1. Install PostgreSQL if not already installed
2. Create local database:
```sql
CREATE DATABASE iqstrade_local;
```

### Database Migrations
```bash
cd backend
python -c "
from config import get_db_conn
conn = get_db_conn()
if conn:
    with open('schema.sql', 'r') as f:
        conn.cursor().execute(f.read())
    conn.commit()
    conn.close()
    print('✅ Local database schema created')
else:
    print('❌ Database connection failed')
"
```

## 🔧 Configuration

### Environment Variables

#### Local Backend (.env file in backend/)
```env
FLASK_ENV=local
LOCAL_DB_NAME=iqstrade_local
LOCAL_DB_USER=postgres
LOCAL_DB_PASSWORD=123456
LOCAL_DB_HOST=localhost
LOCAL_DB_PORT=5432
PORT=8000
JWT_SECRET_KEY=local-development-secret-key
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
FORCE_HTTPS=0
```

#### Local Frontend (.env file in frontend/)
```env
NODE_ENV=development
REACT_APP_API_BASE_URL=http://localhost:8000
```

## 🌐 Access URLs

| Environment | Frontend | Backend API | Database |
|-------------|----------|-------------|----------|
| **Production** | https://iqstrade.onrender.com | https://iqstrade.onrender.com/api | Production DB |
| **Local** | http://localhost:3000 | http://localhost:8000/api | Local PostgreSQL |

## 🔄 How It Works

### Environment Detection
The system automatically detects the environment:

1. **Production Detection**:
   - `PORT` environment variable set
   - `RAILWAY_ENVIRONMENT` or `RENDER` environment variables
   - `FLASK_ENV=production`

2. **Local Detection**:
   - `FLASK_ENV=local`
   - No production indicators found

### Database Configuration
- **Production**: Uses `DB_NAME`, `DB_USER`, `DB_HOST`, etc.
- **Local**: Uses `LOCAL_DB_NAME`, `LOCAL_DB_USER`, `LOCAL_DB_HOST`, etc.

### Frontend Configuration
- **Production**: Uses relative URLs (`/api`)
- **Local**: Uses absolute URLs (`http://localhost:8000/api`)

## 🛠️ Development Workflow

1. **Start Local Environment**:
   ```bash
   # Terminal 1: Backend
   cd backend && python run_local.py
   
   # Terminal 2: Frontend
   cd frontend && node start_local.js
   ```

2. **Access Local System**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api

3. **Production Continues Running**:
   - Production remains unaffected at https://iqstrade.onrender.com

## 🔍 Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check PostgreSQL is running
sudo service postgresql status

# Create database if missing
sudo -u postgres psql
CREATE DATABASE iqstrade_local;
\q
```

#### Port Already in Use
```bash
# Check what's using port 8000
lsof -i :8000

# Kill process if needed
kill -9 <PID>
```

#### Frontend Can't Connect to Backend
- Ensure backend is running on port 8000
- Check CORS configuration in backend
- Verify `REACT_APP_API_BASE_URL` is set correctly

### Debug Mode
Both local environments run in debug mode:
- Backend: `debug=True` with detailed error messages
- Frontend: React development tools enabled

## 📝 Notes

- Local and production environments are completely isolated
- Changes to local environment don't affect production
- You can test new features locally before deploying
- Production database remains untouched during local development

## 🎉 Success Indicators

✅ **Backend Running**: `[LOCAL] Starting Flask app on port 8000 with debug=True`
✅ **Frontend Running**: `Local: http://localhost:3000`
✅ **Database Connected**: `✅ Database connection successful`
✅ **API Accessible**: `http://localhost:8000/api/health` returns 200 