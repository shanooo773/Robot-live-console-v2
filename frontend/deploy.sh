#!/bin/bash

# Frontend Deployment Script
# This script deploys the React frontend to work with separated services

echo "🚀 Deploying Robot Console Frontend..."

# Install dependencies
echo "📥 Installing frontend dependencies..."
npm install

# Check if both backend services are running
echo "🔍 Checking backend services..."

# Check admin backend
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Admin backend is running on port 8000"
else
    echo "⚠️  Admin backend is not running on port 8000"
    echo "📍 Start it with: cd admin-backend && python main.py"
fi

# Check simulation service
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Simulation service is running on port 8001"
else
    echo "⚠️  Simulation service is not running on port 8001"
    echo "📍 Start it with: cd simulation-service && python main.py"
fi

echo "✅ Frontend setup complete!"
echo "🎯 To start the frontend:"
echo "   npm run dev"
echo ""
echo "📍 Frontend will run on: http://localhost:3000"
echo "🔧 Services configuration:"
echo "   - Admin Backend: http://localhost:8000"
echo "   - Simulation Service: http://localhost:8001"
echo ""
echo "⚡ All UI/UX functionality remains the same!"
echo "📋 Available features:"
echo "   - User authentication and registration"
echo "   - Time slot booking system"
echo "   - Admin dashboard"
echo "   - Monaco code editor"
echo "   - Robot simulation (if Docker available)"
echo "   - Video playback"