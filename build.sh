#!/bin/bash

# Build script for Robot Console with Theia IDE

echo "🚀 Building Robot Console with Eclipse Theia IDE..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✅ Docker is available"

# Build Theia base image
echo "📦 Building Eclipse Theia base image..."
cd theia
docker build -t robot-console-theia:latest . --no-cache

if [ $? -eq 0 ]; then
    echo "✅ Theia image built successfully"
else
    echo "❌ Failed to build Theia image"
    exit 1
fi

cd ..

# Install backend dependencies
echo "📦 Installing backend dependencies..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Backend dependencies installed"
else
    echo "❌ Failed to install backend dependencies"
    exit 1
fi

cd ..

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install

if [ $? -eq 0 ]; then
    echo "✅ Frontend dependencies installed"
else
    echo "❌ Failed to install frontend dependencies"
    exit 1
fi

# Build frontend
echo "🔨 Building frontend..."
npm run build

if [ $? -eq 0 ]; then
    echo "✅ Frontend built successfully"
else
    echo "❌ Failed to build frontend"
    exit 1
fi

cd ..

# Create projects directory if it doesn't exist


echo ""
echo "🎉 Build completed successfully!"
echo ""
echo "Next steps:"
echo "1. Start the backend: cd backend && source venv/bin/activate && python main.py"
echo "2. Start the frontend: cd frontend && npm run dev"
echo "3. Access the application at: http://localhost:3000"
echo ""
echo "📋 Features:"
echo "• ✅ Preserved booking system and authentication"
echo "• ✅ Eclipse Theia IDE (replaces Monaco)"
echo "• ✅ RTSP/WebRTC video player (replaces VPS iframe)"
echo "• ✅ Per-user project folders"
echo "• ✅ Container management APIs"
echo "• ✅ WebSocket endpoint for future robot communication"
echo ""
echo "🔧 To manage Theia containers:"
echo "• Check status: curl -H 'Authorization: Bearer <token>' http://localhost:8000/theia/status"
echo "• Start container: curl -X POST -H 'Authorization: Bearer <token>' http://localhost:8000/theia/start"
echo "• Stop container: curl -X POST -H 'Authorization: Bearer <token>' http://localhost:8000/theia/stop"
