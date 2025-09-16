#!/bin/bash

# ==============================================
# Robot Console Docker VPS Deployment Script
# ==============================================

set -e  # Exit on any error

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

# ==============================================
# Configuration
# ==============================================
PROJECT_NAME="robot-console"
PROJECT_DIR="/opt/${PROJECT_NAME}"
COMPOSE_FILE="docker-compose.yml"

# ==============================================
# Pre-deployment Checks
# ==============================================
check_requirements() {
    print_status "Checking system requirements..."
    
    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root or with sudo"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Installing Docker..."
        install_docker
    else
        print_success "Docker is installed"
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Installing Docker Compose..."
        install_docker_compose
    else
        print_success "Docker Compose is installed"
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        print_status "Starting Docker service..."
        systemctl start docker
        systemctl enable docker
    fi
    
    print_success "All requirements satisfied"
}

install_docker() {
    print_status "Installing Docker..."
    
    # Remove old versions
    apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Update package index
    apt-get update
    
    # Install dependencies
    apt-get install -y \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Set up the repository
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    
    print_success "Docker installed successfully"
}

install_docker_compose() {
    print_status "Installing Docker Compose..."
    
    # Download Docker Compose
    curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # Make it executable
    chmod +x /usr/local/bin/docker-compose
    
    # Create symlink
    ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    
    print_success "Docker Compose installed successfully"
}

# ==============================================
# Environment Setup
# ==============================================
setup_project_directory() {
    print_status "Setting up project directory..."
    
    # Create project directory
    mkdir -p "$PROJECT_DIR"
    
    # Copy project files
    if [ -d ".git" ]; then
        # We're in the git repo, copy everything
        cp -r . "$PROJECT_DIR/"
    else
        print_error "Not in a git repository. Please run this script from the project root."
        exit 1
    fi
    
    # Set permissions
    chown -R root:root "$PROJECT_DIR"
    chmod -R 755 "$PROJECT_DIR"
    
    print_success "Project directory setup completed"
}

setup_environment() {
    print_status "Setting up environment configuration..."
    
    cd "$PROJECT_DIR"
    
    # Check if .env.docker exists
    if [ ! -f ".env.docker" ]; then
        print_error ".env.docker file not found. Please create it from the template."
        exit 1
    fi
    
    # Copy environment file
    cp .env.docker .env
    
    # Get server IP
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || hostname -I | awk '{print $1}')
    
    print_warning "Please update the following environment variables in .env:"
    echo "  - MYSQL_ROOT_PASSWORD"
    echo "  - MYSQL_PASSWORD"
    echo "  - SECRET_KEY"
    echo "  - PRODUCTION_CORS_ORIGINS (add your domain/IP: $SERVER_IP)"
    echo "  - VPS_URL (current IP: $SERVER_IP)"
    echo "  - ADMIN_EMAIL"
    echo "  - ADMIN_PASSWORD"
    
    read -p "Have you updated the environment variables? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_warning "Please update .env file manually at: $PROJECT_DIR/.env"
        print_warning "You can continue deployment and update the configuration later."
    fi
    
    print_success "Environment setup completed"
}

# ==============================================
# Docker Deployment
# ==============================================
build_images() {
    print_status "Building Docker images..."
    
    cd "$PROJECT_DIR"
    
    # Build all images
    docker-compose build --no-cache
    
    print_success "Docker images built successfully"
}

deploy_services() {
    print_status "Deploying services..."
    
    cd "$PROJECT_DIR"
    
    # Stop any existing containers
    docker-compose down 2>/dev/null || true
    
    # Start core services
    print_status "Starting core services..."
    docker-compose up -d mysql backend frontend theia-base video-server
    
    # Wait for services to be healthy
    print_status "Waiting for services to become healthy..."
    sleep 30
    
    # Check service health
    for i in {1..12}; do
        if docker-compose ps | grep -q "Up (healthy)"; then
            print_success "Services are healthy"
            break
        elif [ $i -eq 12 ]; then
            print_error "Services failed to become healthy"
            docker-compose logs
            exit 1
        else
            print_status "Waiting for services... (attempt $i/12)"
            sleep 10
        fi
    done
    
    print_success "Core services deployed successfully"
}

setup_nginx_proxy() {
    print_status "Setting up Nginx reverse proxy..."
    
    cd "$PROJECT_DIR"
    
    # Start nginx proxy for production
    docker-compose --profile production up -d nginx-proxy
    
    print_success "Nginx reverse proxy setup completed"
}

# ==============================================
# Post-deployment Configuration
# ==============================================
setup_firewall() {
    print_status "Configuring firewall..."
    
    # Install ufw if not present
    if ! command -v ufw &> /dev/null; then
        apt-get update
        apt-get install -y ufw
    fi
    
    # Configure firewall rules
    ufw --force reset
    ufw default deny incoming
    ufw default allow outgoing
    
    # Allow SSH
    ufw allow ssh
    
    # Allow HTTP and HTTPS
    ufw allow 80/tcp
    ufw allow 443/tcp
    
    # Allow application ports (if accessed directly)
    ufw allow 8000/tcp  # Backend API
    ufw allow 8888/tcp  # Video server
    
    # Enable firewall
    ufw --force enable
    
    print_success "Firewall configured successfully"
}

setup_ssl() {
    print_status "Setting up SSL (optional)..."
    
    print_warning "SSL setup is optional but recommended for production."
    print_warning "You can set up SSL manually using Let's Encrypt or other providers."
    
    read -p "Do you want to set up Let's Encrypt SSL? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_letsencrypt
    else
        print_warning "Skipping SSL setup. You can configure it manually later."
    fi
}

setup_letsencrypt() {
    print_status "Setting up Let's Encrypt SSL..."
    
    # Install certbot
    apt-get update
    apt-get install -y certbot
    
    # Get domain name
    read -p "Enter your domain name (e.g., example.com): " DOMAIN_NAME
    
    if [ -z "$DOMAIN_NAME" ]; then
        print_warning "No domain provided. Skipping SSL setup."
        return
    fi
    
    # Create SSL directory
    mkdir -p "$PROJECT_DIR/ssl"
    
    # Stop nginx temporarily
    docker-compose stop nginx-proxy 2>/dev/null || true
    
    # Get certificate
    certbot certonly --standalone -d "$DOMAIN_NAME" --non-interactive --agree-tos --email "admin@$DOMAIN_NAME"
    
    # Copy certificates
    cp "/etc/letsencrypt/live/$DOMAIN_NAME/fullchain.pem" "$PROJECT_DIR/ssl/cert.pem"
    cp "/etc/letsencrypt/live/$DOMAIN_NAME/privkey.pem" "$PROJECT_DIR/ssl/key.pem"
    
    # Update environment
    cd "$PROJECT_DIR"
    sed -i "s/SSL_ENABLED=false/SSL_ENABLED=true/" .env
    sed -i "s/your-domain.com/$DOMAIN_NAME/" .env
    
    # Restart nginx with SSL
    docker-compose --profile production up -d nginx-proxy
    
    # Setup certificate renewal
    (crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | crontab -
    
    print_success "SSL setup completed for $DOMAIN_NAME"
}

# ==============================================
# Health Checks and Monitoring
# ==============================================
verify_deployment() {
    print_status "Verifying deployment..."
    
    cd "$PROJECT_DIR"
    
    # Get server IP
    SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || hostname -I | awk '{print $1}')
    
    # Check services
    echo
    print_status "Service Status:"
    docker-compose ps
    
    echo
    print_status "Health Checks:"
    
    # Check backend
    if curl -s -f "http://localhost:8000/health" >/dev/null; then
        print_success "✓ Backend API is healthy"
    else
        print_error "✗ Backend API health check failed"
    fi
    
    # Check frontend
    if curl -s -f "http://localhost/health" >/dev/null; then
        print_success "✓ Frontend is healthy"
    else
        print_error "✗ Frontend health check failed"
    fi
    
    # Check database
    if docker-compose exec -T mysql mysqladmin ping -h localhost >/dev/null 2>&1; then
        print_success "✓ MySQL database is healthy"
    else
        print_error "✗ MySQL database health check failed"
    fi
    
    echo
    print_success "Deployment verification completed!"
    
    # Show access URLs
    echo
    print_status "🎉 Robot Console is now deployed!"
    echo "────────────────────────────────────────"
    echo "Access URLs:"
    echo "  Frontend:     http://$SERVER_IP/"
    echo "  API Docs:     http://$SERVER_IP/api/docs"
    echo "  API Health:   http://$SERVER_IP/api/health"
    echo
    echo "Management Commands:"
    echo "  View logs:    cd $PROJECT_DIR && docker-compose logs -f"
    echo "  Restart:      cd $PROJECT_DIR && docker-compose restart"
    echo "  Stop:         cd $PROJECT_DIR && docker-compose down"
    echo "  Start:        cd $PROJECT_DIR && docker-compose up -d"
    echo
}

# ==============================================
# Main Deployment Function
# ==============================================
main() {
    echo "🚀 Robot Console Docker VPS Deployment"
    echo "========================================"
    echo
    
    # Pre-deployment checks
    check_requirements
    
    # Setup
    setup_project_directory
    setup_environment
    
    # Docker deployment
    build_images
    deploy_services
    
    # Production setup
    read -p "Do you want to set up production features (nginx proxy, SSL, firewall)? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_nginx_proxy
        setup_firewall
        setup_ssl
    fi
    
    # Verification
    verify_deployment
    
    print_success "🎉 Deployment completed successfully!"
}

# ==============================================
# Error Handler
# ==============================================
handle_error() {
    print_error "Deployment failed at step: $1"
    print_error "Check logs for details: docker-compose logs"
    exit 1
}

trap 'handle_error ${LINENO}' ERR

# ==============================================
# Script Execution
# ==============================================
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    main "$@"
fi