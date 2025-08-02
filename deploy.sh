#!/bin/bash

# 🚀 IQSTrade Unified Deployment Script
# This script handles the complete deployment process

echo "🚀 Starting IQSTrade Unified Deployment..."

# Check if we're in the right directory
if [ ! -f "render.yaml" ]; then
    echo "❌ Error: render.yaml not found. Please run this script from the project root."
    exit 1
fi

# Step 1: Build Frontend
echo "📦 Building Frontend..."
cd frontend
npm install
npm run build
cd ..

# Step 2: Copy build to backend
echo "📋 Copying build to backend..."
if [ -d "backend/build" ]; then
    rm -rf backend/build
fi
cp -r frontend/build backend/

# Step 3: Commit changes
echo "💾 Committing changes..."
git add .
git commit -m "Deploy: $(date +%Y-%m-%d_%H-%M-%S)"

# Step 4: Push to Render
echo "🚀 Pushing to Render..."
git push origin main

echo "✅ Deployment completed!"
echo "🌐 Your app will be available at: https://iqstrade-unified.onrender.com"
echo "📊 Monitor deployment at: https://dashboard.render.com" 