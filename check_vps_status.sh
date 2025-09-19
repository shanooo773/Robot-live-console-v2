#!/bin/bash

# VPS Status Check Script for Robot Live Console
# This script helps diagnose deployment and configuration issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✅ OK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠️  WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[❌ ERROR]${NC} $1"
}

echo "🔍 Robot Live Console - VPS Status Check"
echo "========================================"
echo

# Detect VPS IP
VPS_IP=$(hostname -I | awk '{print $1}')
if [ ! -z "$VPS_IP" ]; then
    print_status "Detected VPS IP: $VPS_IP"
else
    VPS_IP="localhost"
    print_warning "Could not detect VPS IP, using localhost"
fi
echo

# Check configuration files
print_status "🔧 Configuration Check"
echo "------------------------"

# Frontend API configuration
if [ -f "frontend/src/api.js" ]; then
    if grep -q "http://$VPS_IP:8000" frontend/src/api.js; then
        print_success "Frontend API points to correct VPS IP"
    else
        api_url=$(grep "return.*http" frontend/src/api.js | cut -d'"' -f2)
        print_warning "Frontend API URL: $api_url (expected: http://$VPS_IP:8000)"
    fi
else
    print_error "frontend/src/api.js not found"
fi

# Backend environment
if [ -f "backend/.env" ]; then
    if grep -q "VPS_URL=http://$VPS_IP" backend/.env; then
        print_success "Backend VPS URL is correctly configured"
    else
        vps_url=$(grep "VPS_URL=" backend/.env | cut -d'=' -f2)
        print_warning "Backend VPS URL: $vps_url (expected: http://$VPS_IP)"
    fi
    
    # Check CORS configuration
    cors_origins=$(grep "CORS_ORIGINS=" backend/.env | cut -d'=' -f2)
    if echo "$cors_origins" | grep -q "$VPS_IP"; then
        print_success "CORS origins include VPS IP"
    else
        print_warning "CORS origins may not include VPS IP: $cors_origins"
    fi
else
    print_error "backend/.env not found"
fi

echo

# Check services
print_status "🚀 Service Status Check"
echo "------------------------"

# Backend service (if systemd is used)
if systemctl list-units --type=service | grep -q "robot-console-backend"; then
    if systemctl is-active --quiet robot-console-backend; then
        print_success "Backend service is running"
    else
        print_error "Backend service is not running"
        echo "    Use: sudo systemctl start robot-console-backend"
    fi
else
    print_warning "Backend systemd service not found"
fi

# Nginx service
if command -v nginx >/dev/null 2>&1; then
    if systemctl is-active --quiet nginx; then
        print_success "Nginx is running"
    else
        print_error "Nginx is not running"
        echo "    Use: sudo systemctl start nginx"
    fi
else
    print_warning "Nginx not installed"
fi

echo

# Check connectivity
print_status "🌐 Connectivity Check"
echo "----------------------"

# Local backend health
if curl -s -m 5 http://localhost:8000/health >/dev/null 2>&1; then
    print_success "Backend health endpoint responding (localhost:8000)"
else
    print_error "Backend health endpoint not responding (localhost:8000)"
fi

# Local frontend
if curl -s -m 5 http://localhost/ >/dev/null 2>&1; then
    print_success "Frontend responding (localhost:80)"
else
    print_error "Frontend not responding (localhost:80)"
fi

# External VPS access
if [ "$VPS_IP" != "localhost" ]; then
    if curl -s -m 10 http://$VPS_IP/ >/dev/null 2>&1; then
        print_success "External access working (http://$VPS_IP/)"
    else
        print_error "External access not working (http://$VPS_IP/)"
        echo "    Check firewall: sudo ufw status"
        echo "    Allow HTTP: sudo ufw allow 80"
    fi
fi

echo

# Check ports
print_status "🔌 Port Status Check"
echo "---------------------"

check_port() {
    local port=$1
    local service=$2
    if lsof -i :$port >/dev/null 2>&1; then
        local process=$(lsof -i :$port | tail -1 | awk '{print $1}')
        print_success "Port $port is in use by $process ($service)"
    else
        print_warning "Port $port is not in use ($service not running)"
    fi
}

check_port 80 "HTTP/Frontend"
check_port 8000 "Backend API"
check_port 443 "HTTPS (if configured)"

echo

# Summary and recommendations
print_status "📋 Summary & Recommendations"
echo "-----------------------------"

# Count issues
issues=0

if [ ! -f "frontend/src/api.js" ] || ! grep -q "http://$VPS_IP:8000" frontend/src/api.js; then
    ((issues++))
fi

if [ ! -f "backend/.env" ] || ! grep -q "VPS_URL=http://$VPS_IP" backend/.env; then
    ((issues++))
fi

if ! curl -s -m 5 http://localhost:8000/health >/dev/null 2>&1; then
    ((issues++))
fi

if [ $issues -eq 0 ]; then
    print_success "✨ All checks passed! Your VPS deployment looks healthy."
else
    print_warning "⚠️  Found $issues potential issues."
    echo
    echo "🔧 Quick fixes:"
    echo "  1. Update VPS IP configuration:"
    echo "     ./update_vps_ip.sh $VPS_IP"
    echo "  2. Restart services:"
    echo "     sudo systemctl restart robot-console-backend nginx"
    echo "  3. Re-deploy if needed:"
    echo "     sudo ./deploy_vps.sh --vps-ip $VPS_IP"
fi

echo
print_status "📞 For more help, see VPS_DEPLOYMENT_GUIDE.md"