#!/bin/bash

# Admin Backend Deployment Script
# This script deploys the lightweight admin/booking backend

echo "🚀 Deploying Robot Admin Backend..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Copy database if it doesn't exist
if [ ! -f "robot_console.db" ]; then
    if [ -f "../robot_console.db" ]; then
        echo "💾 Copying database from parent directory..."
        cp ../robot_console.db .
    else
        echo "⚠️  Database not found - will be created on first run"
    fi
fi

echo "✅ Admin backend setup complete!"
echo "🎯 To start the admin backend:"
echo "   cd admin-backend"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "📍 Admin backend will run on: http://localhost:8000"
echo "🔧 Endpoints available:"
echo "   - Authentication: /auth/*"
echo "   - Booking: /bookings/*"
echo "   - Admin: /admin/*"
echo "   - Health: /health"