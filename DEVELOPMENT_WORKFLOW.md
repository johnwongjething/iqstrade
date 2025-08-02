# 🚀 IQSTrade Development Workflow

## 📋 Overview

This guide shows you how to develop IQSTrade **without needing to run `npm run build` every time** you make frontend changes.

## 🎯 The Problem

**Before:** Every frontend change required `npm run build` because:
- CSRF tokens need same-domain access
- Build folder must be in backend directory
- Production deployment requires unified build

**After:** Development environment with hot reload!

## 🛠️ Setup Development Environment

### Step 1: Install Dependencies
```bash
# Windows
dev-setup.bat

# Linux/Mac
./dev-setup.sh
```

### Step 2: Start Development Servers

**Terminal 1 - Backend:**
```bash
cd backend
python run_local.py
```
Backend will run on: `http://localhost:5000`

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```
Frontend will run on: `http://localhost:3000`

## 🔄 Development Workflow

### ✅ What You Can Do Now:

1. **Edit frontend files** in `frontend/src/`
2. **Changes auto-reload** in browser
3. **No `npm run build` needed** during development
4. **CSRF works** via proxy configuration
5. **Hot reload** for instant feedback

### 📝 Example Workflow:

```bash
# 1. Start development servers (once)
cd backend && python run_local.py  # Terminal 1
cd frontend && npm start           # Terminal 2

# 2. Make changes (anytime)
# Edit frontend/src/pages/Login.js
# Save file → Browser auto-reloads!

# 3. Test changes
# Open http://localhost:3000
# Changes are immediately visible

# 4. Deploy when ready
# Run deploy.bat from project root
```

## 🔧 How It Works

### Development Mode (Hot Reload):
```
Browser (localhost:3000) 
    ↓ (proxy)
Frontend Dev Server
    ↓ (proxy)
Backend (localhost:5000)
```

### Local Production Testing:
```
Browser (localhost:5000)
    ↓
Backend (serves React build)
    ↓
Same as production!
```

### Production Mode:
```
Browser (onrender.com)
    ↓
Backend (serves React build)
```

## 📁 File Structure

```
iqstrade/
├── frontend/           # React development
│   ├── src/           # Edit these files
│   ├── public/        # Static assets
│   └── package.json   # Frontend dependencies
├── backend/           # Flask backend
│   ├── build/         # Production React build (auto-copied)
│   ├── app.py         # Main Flask app
│   └── requirements.txt
├── render.yaml        # Production deployment
├── deploy.bat         # Production deployment script
└── dev-setup.bat      # Development setup script
```

## 🚀 Commands Summary

### Development (Hot Reload):
```bash
# Setup (once)
dev-setup.bat

# Start development
cd backend && python run_local.py  # Terminal 1
cd frontend && npm start           # Terminal 2

# Make changes
# Edit frontend/src/* files
# Browser auto-reloads!
```

### Local Production Testing (JWT/CSRF):
```bash
# Start local production server
cd backend && python run_local_production.py

# Test tokens locally
python test_local_tokens.py

# Open in browser
# http://localhost:5000
```

### Production Deployment:
```bash
# Deploy to production
deploy.bat

# Manual deployment
git add .
git commit -m "Your changes"
git push origin main
```

## 🔍 Troubleshooting

### CSRF Issues in Development:
- Ensure backend is running on `localhost:5000`
- Ensure frontend is running on `localhost:3000`
- Check browser console for proxy errors
- Restart both servers if needed

### Build Issues:
- Run `npm install` in frontend directory
- Clear browser cache
- Check for syntax errors in console

### Production Issues:
- Use `deploy.bat` for unified deployment
- Check Render logs for build errors
- Verify environment variables are set

## 🎯 Benefits

✅ **No more `npm run build`** for every change  
✅ **Instant feedback** with hot reload  
✅ **CSRF works** in development  
✅ **JWT tokens testable locally**  
✅ **Same code** works in production  
✅ **Faster development** cycle  
✅ **Better debugging** experience  
✅ **Local production simulation** for token testing  

## 📚 Next Steps

### For Development (Hot Reload):
1. **Run `dev-setup.bat`** to set up development environment
2. **Start both servers** (backend + frontend)
3. **Make changes** to frontend files
4. **See changes instantly** in browser

### For Token Testing (Local Production):
1. **Run `cd backend && python run_local_production.py`**
2. **Test tokens** with `python test_local_tokens.py`
3. **Open http://localhost:5000** in browser
4. **Test login and JWT functionality**

### For Production Deployment:
5. **Deploy when ready** with `deploy.bat`

**Happy coding!** 🚀 