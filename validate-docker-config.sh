#!/bin/bash

echo "🔍 Validating Docker Configuration (Quick Check)"
echo "================================================"

# Function to check if file exists and report
check_file() {
    if [ -f "$1" ]; then
        echo "✅ $1 exists"
        return 0
    else
        echo "❌ $1 missing"
        return 1
    fi
}

# Function to check if directory exists and report
check_dir() {
    if [ -d "$1" ]; then
        echo "✅ $1 directory exists"
        return 0
    else
        echo "❌ $1 directory missing"
        return 1
    fi
}

echo "📁 Checking required files and directories..."

# Check core Docker files
check_file "docker-compose.yml"
check_file "webrtc/Dockerfile"
check_file "webrtc/server.js"
check_file "theia/Dockerfile"
check_file "theia/package.json"

# Check required directories
check_dir "projects"
check_dir "webrtc"
check_dir "theia"

echo ""
echo "🐳 Validating Docker Compose configuration..."

# Validate docker-compose syntax
if docker compose config > /dev/null 2>&1; then
    echo "✅ Docker Compose syntax is valid"
else
    echo "❌ Docker Compose syntax is invalid"
    exit 1
fi

# Check if required services are present
if docker compose config | grep -q "webrtc-signaling"; then
    echo "✅ WebRTC signaling service found"
else
    echo "❌ WebRTC signaling service missing"
fi

if COMPOSE_PROFILES=build-only docker compose config | grep -q "theia-base"; then
    echo "✅ Theia base service found (build profile)"
else
    echo "❌ Theia base service missing"
fi

echo ""
echo "🔧 Checking Dockerfile syntax..."

# Basic Dockerfile syntax check using docker build --no-cache --dry-run (if available)
echo "  Checking WebRTC Dockerfile..."
if docker build --help 2>/dev/null | grep -q "\-\-dry-run"; then
    if docker build --dry-run webrtc/ > /dev/null 2>&1; then
        echo "✅ WebRTC Dockerfile syntax valid"
    else
        echo "❌ WebRTC Dockerfile has syntax errors"
    fi
else
    echo "⚠️  Skipping dry-run check (not supported in this Docker version)"
fi

echo "  Checking Theia Dockerfile..."
if docker build --help 2>/dev/null | grep -q "\-\-dry-run"; then
    if docker build --dry-run theia/ > /dev/null 2>&1; then
        echo "✅ Theia Dockerfile syntax valid"
    else
        echo "❌ Theia Dockerfile has syntax errors"
    fi
else
    echo "⚠️  Skipping dry-run check (not supported in this Docker version)"
fi

echo ""
echo "📋 Checking Theia package.json..."

# Check if theia package.json has required dependencies
if [ -f "theia/package.json" ]; then
    if grep -q "@theia/core" theia/package.json; then
        echo "✅ Theia core dependency found"
    else
        echo "❌ Theia core dependency missing"
    fi
    
    if grep -q "theia build" theia/package.json; then
        echo "✅ Theia build script found"
    else
        echo "❌ Theia build script missing"
    fi
    
    if grep -q "theia start" theia/package.json; then
        echo "✅ Theia start script found"
    else
        echo "❌ Theia start script missing"
    fi
fi

echo ""
echo "🌐 Checking network configuration..."

# Check if docker-compose references the correct network
if docker compose config | grep -q "robot-console-network"; then
    echo "✅ Robot console network configured"
else
    echo "❌ Robot console network missing"
fi

echo ""
echo "💾 Checking volume configuration..."

# Check if docker-compose has volume bindings
if COMPOSE_PROFILES=build-only docker compose config | grep -q "./projects"; then
    echo "✅ Projects volume binding configured"
else
    echo "❌ Projects volume binding missing"
fi

echo ""
echo "🎯 Configuration Summary:"
echo "========================"

# Count issues
issues=0

# Re-run critical checks and count failures
docker compose config > /dev/null 2>&1 || ((issues++))
[ -f "docker-compose.yml" ] || ((issues++))
[ -f "webrtc/Dockerfile" ] || ((issues++))
[ -f "theia/Dockerfile" ] || ((issues++))
[ -f "theia/package.json" ] || ((issues++))

if [ $issues -eq 0 ]; then
    echo "✅ All critical Docker configuration checks passed!"
    echo "✅ Docker setup appears to be correctly configured"
    echo ""
    echo "📝 Next steps:"
    echo "   • Run 'docker compose build' to build images (may take time)"
    echo "   • Run 'docker compose up -d webrtc-signaling' to start WebRTC service"
    echo "   • Run 'COMPOSE_PROFILES=build-only docker compose build theia-base' to build Theia"
    exit 0
else
    echo "❌ Found $issues critical configuration issues"
    echo "❌ Please fix the issues above before proceeding"
    exit 1
fi