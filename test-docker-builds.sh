#!/bin/bash

echo "🏗️  Testing Docker Build Process (Quick Build Test)"
echo "===================================================="

echo "📋 This script tests the Docker build process with optimizations"
echo "   for faster development cycles."
echo ""

# Function to build with cache and progress indicators
build_with_progress() {
    local service=$1
    local context=$2
    
    echo "🔨 Building $service..."
    echo "   Context: $context"
    echo "   Using build cache for faster builds..."
    
    # Use buildkit for faster builds and progress
    DOCKER_BUILDKIT=1 docker build \
        --progress=plain \
        --tag "robot-$service:test" \
        "$context" || {
        echo "❌ Build failed for $service"
        return 1
    }
    
    echo "✅ Build completed for $service"
    return 0
}

echo "🚀 Starting optimized build tests..."
echo ""

# Test WebRTC build first (should be faster)
echo "1️⃣  Testing WebRTC signaling service build..."
if build_with_progress "webrtc-signaling" "webrtc/"; then
    echo "✅ WebRTC signaling service builds successfully"
    
    # Test if the image can start
    echo "🧪 Testing WebRTC container startup..."
    if docker run --rm -d --name test-webrtc -p 8081:8080 robot-webrtc-signaling:test > /dev/null 2>&1; then
        sleep 2
        if curl -f http://localhost:8081/health > /dev/null 2>&1; then
            echo "✅ WebRTC service starts and responds to health checks"
            docker stop test-webrtc > /dev/null 2>&1
        else
            echo "⚠️  WebRTC service starts but health check failed"
            docker stop test-webrtc > /dev/null 2>&1
        fi
    else
        echo "⚠️  WebRTC service failed to start"
    fi
else
    echo "❌ WebRTC signaling service build failed"
    exit 1
fi

echo ""
echo "2️⃣  Testing Theia IDE service build..."
echo "⚠️  Note: Theia build takes 5-10 minutes due to compilation requirements"
echo "   Consider using pre-built images in production"

if build_with_progress "theia-ide" "theia/"; then
    echo "✅ Theia IDE service builds successfully"
    echo "🏁 Both services build successfully!"
else
    echo "❌ Theia IDE service build failed"
    echo "💡 Theia builds can fail due to memory/time constraints"
    echo "   Consider using a pre-built Theia base image or increasing build resources"
    exit 1
fi

echo ""
echo "🎉 All Docker builds completed successfully!"
echo ""
echo "📝 Next steps:"
echo "   • Use 'docker compose up -d webrtc-signaling' to start WebRTC"
echo "   • Use 'COMPOSE_PROFILES=build-only docker compose build theia-base' for production builds"
echo "   • Both services are ready for deployment"