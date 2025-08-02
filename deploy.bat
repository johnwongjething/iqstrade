@echo off
REM 🚀 IQSTrade Unified Deployment Script for Windows
REM This script handles the complete deployment process

echo 🚀 Starting IQSTrade Unified Deployment...

REM Check if we're in the right directory
if not exist "render.yaml" (
    echo ❌ Error: render.yaml not found. Please run this script from the project root.
    pause
    exit /b 1
)

REM Step 1: Build Frontend
echo 📦 Building Frontend...
cd frontend
call npm install
call npm run build
cd ..

REM Step 2: Copy build to backend
echo 📋 Copying build to backend...
if exist "backend\build" (
    rmdir /s /q backend\build
)
xcopy /e /i frontend\build backend\build

REM Step 3: Commit changes
echo 💾 Committing changes...
git add .
git commit -m "Deploy: %date% %time%"

REM Step 4: Push to Render
echo 🚀 Pushing to Render...
git push origin main

echo ✅ Deployment completed!
echo 🌐 Your app will be available at: https://iqstrade-unified.onrender.com
echo 📊 Monitor deployment at: https://dashboard.render.com
pause 