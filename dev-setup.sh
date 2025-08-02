#!/bin/bash

# 🚀 IQSTrade Development Setup for Linux/Mac
# This sets up a development environment where frontend changes are automatic

echo "🚀 Setting up IQSTrade Development Environment..."

# Check if we're in the right directory
if [ ! -f "render.yaml" ]; then
    echo "❌ Error: render.yaml not found. Please run this script from the project root."
    exit 1
fi

echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo "🔧 Setting up development environment..."
echo ""
echo "✅ Development setup completed!"
echo ""
echo "🚀 To start development:"
echo "   1. Start backend: cd backend && python run_local.py"
echo "   2. Start frontend: cd frontend && npm start"
echo ""
echo "📝 Development Workflow:"
echo "   - Make frontend changes in frontend/src/"
echo "   - Changes will auto-reload in browser"
echo "   - No need to run npm run build during development"
echo "   - Only run npm run build when deploying to production"
echo ""
echo "🚀 To deploy to production:"
echo "   - Run ./deploy.sh from project root"
echo "" 