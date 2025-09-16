#!/bin/bash

# Docker Setup Script
# This script prepares the environment for running Robot Console with Docker

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

echo "🐳 Robot Console Docker Setup"
echo "============================="
echo

# Check if Docker is installed
if ! command -v docker >/dev/null 2>&1; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose >/dev/null 2>&1; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_success "Docker and Docker Compose are installed"

# Create data directories
print_status "Creating data directories..."

DATA_DIR=${DATA_DIR:-./data}
mkdir -p "${DATA_DIR}/mysql"
mkdir -p "${DATA_DIR}/videos"
mkdir -p "${DATA_DIR}/theia"
mkdir -p "./projects"
mkdir -p "./logs"

# Set appropriate permissions
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux: Set proper ownership for bind mounts
    sudo chown -R 999:999 "${DATA_DIR}/mysql" 2>/dev/null || true
    sudo chown -R 1001:1001 "${DATA_DIR}/theia" 2>/dev/null || true
    sudo chown -R $(id -u):$(id -g) "${DATA_DIR}/videos" 2>/dev/null || true
fi

print_success "Data directories created: ${DATA_DIR}"

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.docker" ]; then
        print_status "Copying Docker environment configuration..."
        cp .env.docker .env
        print_warning "Please review and update .env file with your settings"
    elif [ -f ".env.template" ]; then
        print_status "Copying environment template..."
        cp .env.template .env
        print_warning "Please update .env file with appropriate settings for Docker"
    else
        print_error "No environment template found. Please create .env file manually."
        exit 1
    fi
fi

print_success "Environment file ready"

# Show next steps
echo
print_success "Setup complete! Next steps:"
echo
echo "1. Review and update .env file with your settings"
echo "2. For development:"
echo "   docker-compose up -d"
echo
echo "3. For production:"
echo "   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d"
echo
echo "4. Access the application:"
echo "   - Frontend: http://localhost"
echo "   - Backend API: http://localhost:8000"
echo "   - Theia IDE: http://localhost:3001"
echo "   - MySQL: localhost:3306"
echo
echo "5. Check status:"
echo "   docker-compose ps"
echo "   docker-compose logs"
echo

print_warning "Note: Make sure to update production settings in .env before deploying!"