@echo off
REM 🚀 IQSTrade Development Setup for Windows
REM This sets up a development environment where frontend changes are automatic

echo 🚀 Setting up IQSTrade Development Environment...

REM Check if we're in the right directory
if not exist "render.yaml" (
    echo ❌ Error: render.yaml not found. Please run this script from the project root.
    pause
    exit /b 1
)

echo 📦 Installing frontend dependencies...
cd frontend
call npm install
cd ..

echo 🔧 Setting up development environment...
echo.
echo ✅ Development setup completed!
echo.
echo 🚀 To start development:
echo    1. Start backend: cd backend ^&^& python run_local.py
echo    2. Start frontend: cd frontend ^&^& npm start
echo.
echo 📝 Development Workflow:
echo    - Make frontend changes in frontend/src/
echo    - Changes will auto-reload in browser
echo    - No need to run npm run build during development
echo    - Only run npm run build when deploying to production
echo.
echo 🚀 To deploy to production:
echo    - Run deploy.bat from project root
echo.
pause 