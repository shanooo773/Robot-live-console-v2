#!/bin/bash

# Build script for Robot Console - Theia + WebRTC Services Only

echo "🚀 Building Robot Console - Theia + WebRTC Services..."

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

# Create Docker network if it doesn't exist
echo "🌐 Creating Docker network..."
docker network create robot-console-network 2>/dev/null || echo "✅ Network already exists"

# Start WebRTC signaling service
echo "📡 Starting WebRTC signaling service..."
docker compose up -d webrtc-signaling

if [ $? -eq 0 ]; then
    echo "✅ WebRTC signaling service started successfully"
else
    echo "❌ Failed to start WebRTC signaling service"
    exit 1
fi

# Pull Theia prebuilt image
echo "📦 Pulling Eclipse Theia prebuilt image..."
docker pull elswork/theia 2>/dev/null || {
    echo "⚠️  Failed to pull elswork/theia - will try to use local copy if available"
}

# Check if image is available
if docker images elswork/theia | grep -q elswork/theia; then
    echo "✅ Theia image available: elswork/theia"
else
    echo "❌ Theia image not available. Please ensure internet connection and try again."
    echo "    Manual command: docker pull elswork/theia"
fi

# Create projects directory if it doesn't exist
mkdir -p projects

# Ensure demo user directories exist
mkdir -p projects/-1 projects/-2

echo ""
echo "🎉 Build completed successfully!"
echo ""
echo "✅ Services Status:"
echo "   📡 WebRTC Signaling: http://localhost:8080/health" 
echo "   🏗️ Theia Image: elswork/theia (prebuilt)"
echo "   📁 User Projects: ./projects/"
echo ""
echo "🔧 Next Steps:"
echo "1. Start the backend: cd backend && source venv/bin/activate && python main.py"
echo "2. Start the frontend: cd frontend && npm run dev"
echo "3. Access the application at: http://localhost:3000"
echo ""
echo "📋 Docker Services (Theia + WebRTC Only):"
echo "• ✅ WebRTC Signaling Service (Port 8080)"
echo "• ✅ Theia Base Image (User containers managed by backend)"
echo "• ✅ Persistent user workspaces in ./projects/"
echo "• ✅ Demo user directories (-1, -2) configured"
echo ""
echo "🧪 Test WebRTC:"
echo "• Health: curl http://localhost:8080/health"
echo "• Config: curl http://localhost:8080/config"
echo ""
echo "🔧 Manage Theia containers via backend API:"
echo "• Check status: GET /theia/status"
echo "• Start container: POST /theia/start"
echo "• Stop container: POST /theia/stop"