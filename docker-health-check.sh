#!/bin/bash

# Docker Health Check Script for Robot Console
# This script verifies that all services are running correctly

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

# Function to check if a URL responds
check_url() {
    local url=$1
    local name=$2
    local expected_code=${3:-200}
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_code"; then
        print_success "$name is healthy"
        return 0
    else
        print_error "$name is not responding correctly"
        return 1
    fi
}

# Function to check Docker service status
check_docker_service() {
    local service=$1
    
    if docker-compose ps "$service" | grep -q "Up"; then
        print_success "Docker service '$service' is running"
        return 0
    else
        print_error "Docker service '$service' is not running"
        return 1
    fi
}

echo "🏥 Robot Console Health Check"
echo "============================"
echo

# Check if Docker Compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    print_error "Docker Compose is not available"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Please run this script from the project root."
    exit 1
fi

print_status "Checking Docker services..."

# Check individual services
SERVICES=("mysql" "backend" "frontend" "theia")
ALL_SERVICES_OK=true

for service in "${SERVICES[@]}"; do
    if ! check_docker_service "$service"; then
        ALL_SERVICES_OK=false
    fi
done

if [ "$ALL_SERVICES_OK" = false ]; then
    print_error "Some Docker services are not running. Run 'docker-compose ps' for details."
    exit 1
fi

print_status "Checking service health endpoints..."

# Wait a moment for services to be ready
sleep 5

# Check health endpoints
HEALTH_OK=true

# Frontend health check
if ! check_url "http://localhost/health" "Frontend"; then
    HEALTH_OK=false
fi

# Backend health check
if ! check_url "http://localhost:8000/health" "Backend API"; then
    HEALTH_OK=false
fi

# Theia health check
if ! check_url "http://localhost:3001" "Theia IDE"; then
    HEALTH_OK=false
fi

# Database connectivity check (via backend)
if ! check_url "http://localhost:8000/health/services" "Database connectivity"; then
    HEALTH_OK=false
fi

if [ "$HEALTH_OK" = true ]; then
    echo
    print_success "All services are healthy! 🎉"
    echo
    echo "Service URLs:"
    echo "- Frontend: http://localhost"
    echo "- Backend API: http://localhost:8000"
    echo "- API Docs: http://localhost:8000/docs"
    echo "- Theia IDE: http://localhost:3001"
    echo "- MySQL: localhost:3306"
    echo
else
    echo
    print_error "Some health checks failed. Please check the logs:"
    echo "docker-compose logs"
    exit 1
fi

# Additional system checks
print_status "Checking system resources..."

# Check disk space
DISK_USAGE=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    print_warning "Disk usage is high: ${DISK_USAGE}%"
elif [ "$DISK_USAGE" -gt 80 ]; then
    print_warning "Disk usage is getting high: ${DISK_USAGE}%"
else
    print_success "Disk usage is normal: ${DISK_USAGE}%"
fi

# Check memory usage if available
if command -v free >/dev/null 2>&1; then
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$MEMORY_USAGE" -gt 90 ]; then
        print_warning "Memory usage is high: ${MEMORY_USAGE}%"
    elif [ "$MEMORY_USAGE" -gt 80 ]; then
        print_warning "Memory usage is getting high: ${MEMORY_USAGE}%"
    else
        print_success "Memory usage is normal: ${MEMORY_USAGE}%"
    fi
fi

echo
print_success "Health check completed successfully!"