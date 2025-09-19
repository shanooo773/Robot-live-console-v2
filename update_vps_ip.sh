#!/bin/bash

# Simple script to update VPS IP configuration across all files
# Usage: ./update_vps_ip.sh <new_vps_ip>

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
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check arguments
if [ -z "$1" ]; then
    print_error "Usage: $0 <vps_ip>"
    echo "Example: $0 172.232.105.47"
    exit 1
fi

NEW_VPS_IP="$1"

# Validate IP format (basic validation)
if [[ ! $NEW_VPS_IP =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    print_error "Invalid IP address format: $NEW_VPS_IP"
    exit 1
fi

echo "🚀 Updating VPS IP Configuration"
echo "================================="
print_status "New VPS IP: $NEW_VPS_IP"
echo

# Update frontend API configuration
print_status "Updating frontend API configuration..."
if [ -f "frontend/src/api.js" ]; then
    sed -i "s|return \"http://[0-9.]*:8000\";|return \"http://$NEW_VPS_IP:8000\";|g" frontend/src/api.js
    print_success "Updated frontend/src/api.js"
else
    print_warning "frontend/src/api.js not found"
fi

# Update environment template
print_status "Updating environment template..."
if [ -f ".env.template" ]; then
    sed -i "s|VPS_URL=http://[0-9.]*|VPS_URL=http://$NEW_VPS_IP|g" .env.template
    sed -i "s|http://[0-9.]*\([,:]\)|http://$NEW_VPS_IP\1|g" .env.template
    print_success "Updated .env.template"
else
    print_warning ".env.template not found"
fi

# Update production template
print_status "Updating production environment template..."
if [ -f ".env.production.template" ]; then
    sed -i "s|VPS_URL=http://[0-9.]*|VPS_URL=http://$NEW_VPS_IP|g" .env.production.template
    sed -i "s|http://[0-9.]*\([,:]\)|http://$NEW_VPS_IP\1|g" .env.production.template
    print_success "Updated .env.production.template"
else
    print_warning ".env.production.template not found"
fi

# Update backend environment
print_status "Updating backend environment..."
if [ -f "backend/.env" ]; then
    sed -i "s|VPS_URL=http://[0-9.]*|VPS_URL=http://$NEW_VPS_IP|g" backend/.env
    sed -i "s|http://[0-9.]*\([,:]\)|http://$NEW_VPS_IP\1|g" backend/.env
    print_success "Updated backend/.env"
else
    print_warning "backend/.env not found"
fi

# Update main environment
print_status "Updating main environment..."
if [ -f ".env" ]; then
    sed -i "s|VPS_URL=http://[0-9.]*|VPS_URL=http://$NEW_VPS_IP|g" .env
    sed -i "s|http://[0-9.]*\([,:]\)|http://$NEW_VPS_IP\1|g" .env
    print_success "Updated .env"
else
    print_warning ".env not found"
fi

# Update backend main.py fallback
print_status "Updating backend fallback configuration..."
if [ -f "backend/main.py" ]; then
    sed -i "s|'http://[0-9.]*'|'http://$NEW_VPS_IP'|g" backend/main.py
    # Fix WebRTC configuration
    sed -i "s|replace('http://[0-9.]*', '')|replace('http://', '')|g" backend/main.py
    print_success "Updated backend/main.py"
else
    print_warning "backend/main.py not found"
fi

echo
print_success "🎉 VPS IP configuration updated successfully!"
echo
print_status "Updated VPS IP to: $NEW_VPS_IP"
print_status "Next steps:"
echo "  1. Redeploy the application:"
echo "     ./scripts/deploy.sh --production --vps-ip $NEW_VPS_IP"
echo "  2. Or for VPS deployment:"
echo "     sudo ./deploy_vps.sh --vps-ip $NEW_VPS_IP"
echo
print_warning "Note: Make sure to restart any running services after this update."