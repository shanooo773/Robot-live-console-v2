#!/bin/bash

# Enhanced Deployment Script for VPS
# Handles port conflicts, file permissions, and systemd service setup
# 
# Usage:
#   sudo ./deploy_vps.sh                    # Auto-detect VPS IP
#   sudo ./deploy_vps.sh --vps-ip 172.232.105.47  # Specify VPS IP
#
# This script will:
# - Auto-detect or use provided VPS IP address
# - Update all configuration files with the correct IP
# - Set up systemd services for production
# - Configure nginx as reverse proxy
# - Validate external access to the application

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

# Function to check port availability
check_port() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        print_warning "Port $port is already in use"
        return 1
    else
        print_success "Port $port is available"
        return 0
    fi
}

# Function to find available port
find_available_port() {
    local start_port=$1
    local max_port=$((start_port + 100))
    
    for port in $(seq $start_port $max_port); do
        if ! lsof -i :$port >/dev/null 2>&1; then
            echo $port
            return 0
        fi
    done
    
    print_error "No available ports found in range $start_port-$max_port"
    exit 1
}

# Function to setup directories with proper permissions
setup_directories() {
    print_status "Setting up directories with proper permissions..."
    
    # Use absolute paths
    PROJECT_ROOT="/opt/robot-console"
    
    # Create project directory if it doesn't exist
    if [ ! -d "$PROJECT_ROOT" ]; then
        sudo mkdir -p "$PROJECT_ROOT"
        print_success "Created project directory: $PROJECT_ROOT"
    fi
    
    # Copy files to production location
    sudo cp -r . "$PROJECT_ROOT/"
    
    # Create necessary directories
    sudo mkdir -p "$PROJECT_ROOT/backend/logs"
    sudo mkdir -p "$PROJECT_ROOT/backend/videos"
    sudo mkdir -p "$PROJECT_ROOT/backend/temp"
    
    # Create user for the service
    if ! id "robot-console" &>/dev/null; then
        sudo useradd --system --home "$PROJECT_ROOT" --shell /bin/false robot-console
        print_success "Created robot-console user"
    fi
    
    # Set ownership and permissions
    sudo chown -R robot-console:robot-console "$PROJECT_ROOT"
    sudo chmod 755 "$PROJECT_ROOT"
    sudo chmod 755 "$PROJECT_ROOT/backend"
    sudo chmod 775 "$PROJECT_ROOT/backend/logs"
    sudo chmod 775 "$PROJECT_ROOT/backend/videos"
    sudo chmod 775 "$PROJECT_ROOT/backend/temp"
    sudo chmod 644 "$PROJECT_ROOT/backend/.env"
    
    print_success "Directory setup completed"
}

# Function to setup Python environment
setup_python_environment() {
    print_status "Setting up Python environment..."
    
    PROJECT_ROOT="/opt/robot-console"
    cd "$PROJECT_ROOT/backend"
    
    # Create virtual environment
    sudo -u robot-console python3 -m venv venv
    
    # Install dependencies
    sudo -u robot-console bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
    
    # Create/update .env file with VPS configuration
    print_status "Creating/updating .env file with VPS configuration..."
    if [ ! -f ".env" ]; then
        # Copy from template
        cp ../.env.template .env
    fi
    
    # Update VPS-specific settings
    sudo -u robot-console bash -c "
    sed -i 's|VPS_URL=.*|VPS_URL=http://$VPS_IP|g' .env
    sed -i 's|CORS_ORIGINS=.*|CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://$VPS_IP,http://$VPS_IP:3000,http://$VPS_IP:5173,http://$VPS_IP:80,http://$VPS_IP:443|g' .env
    sed -i 's|PRODUCTION_CORS_ORIGINS=.*|PRODUCTION_CORS_ORIGINS=http://$VPS_IP,http://$VPS_IP:3000,http://$VPS_IP:5173,http://$VPS_IP:80,http://$VPS_IP:443,https://your-domain.com|g' .env
    sed -i 's|ENVIRONMENT=.*|ENVIRONMENT=production|g' .env
    "
    
    print_success "Python environment setup completed"
}

# Function to setup systemd service
setup_systemd_service() {
    print_status "Setting up systemd service..."
    
    # Copy service file
    sudo cp robot-console-backend.service /etc/systemd/system/
    
    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable robot-console-backend
    
    print_success "Systemd service setup completed"
}

# Function to start services
start_services() {
    print_status "Starting services..."
    
    # Start backend service
    sudo systemctl start robot-console-backend
    
    # Check service status
    if sudo systemctl is-active --quiet robot-console-backend; then
        print_success "Backend service started successfully"
    else
        print_error "Failed to start backend service"
        sudo systemctl status robot-console-backend
        exit 1
    fi
}

# Function to setup nginx
setup_nginx() {
    print_status "Setting up Nginx configuration..."
    
    # Check if nginx is installed
    if ! command -v nginx >/dev/null 2>&1; then
        print_status "Installing Nginx..."
        sudo apt-get update
        sudo apt-get install -y nginx
    fi
    
    # Create nginx configuration
    cat > /tmp/robot-console.nginx.conf << 'EOF'
# HTTP server - redirect to HTTPS in production
server {
    listen 80;
    server_name _;  # Replace with your domain
    
    # Allow Let's Encrypt challenges
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect all other traffic to HTTPS (uncomment for production)
    # return 301 https://$server_name$request_uri;
    
    # Temporary HTTP access for development/testing
    # Security headers
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy strict-origin-when-cross-origin;
    
    # Serve React frontend
    location / {
        root /opt/robot-console/frontend/dist;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API proxy to backend
    location /api/ {
        rewrite ^/api/(.*) /$1 break;
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        access_log off;
    }
}

# HTTPS server configuration (for production with SSL certificate)
# server {
#     listen 443 ssl http2;
#     server_name your-domain.com;  # Replace with your actual domain
#     
#     # SSL certificate paths (update with your certificate paths)
#     ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
#     ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
#     
#     # SSL configuration
#     ssl_protocols TLSv1.2 TLSv1.3;
#     ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
#     ssl_prefer_server_ciphers off;
#     ssl_session_cache shared:SSL:10m;
#     
#     # Security headers
#     add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
#     add_header X-Content-Type-Options nosniff;
#     add_header X-Frame-Options DENY;
#     add_header X-XSS-Protection "1; mode=block";
#     add_header Referrer-Policy strict-origin-when-cross-origin;
#     add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' ws: wss:; frame-src 'self';";
#     
#     # Same location blocks as HTTP server above
#     # ... (copy location blocks from HTTP server)
# }
EOF
    
    # Move configuration to nginx sites-available
    sudo mv /tmp/robot-console.nginx.conf /etc/nginx/sites-available/robot-console
    
    # Enable the site
    sudo ln -sf /etc/nginx/sites-available/robot-console /etc/nginx/sites-enabled/
    
    # Remove default site if it exists
    sudo rm -f /etc/nginx/sites-enabled/default
    
    # Test nginx configuration
    if sudo nginx -t; then
        print_success "Nginx configuration is valid"
        sudo systemctl restart nginx
        print_success "Nginx restarted successfully"
    else
        print_error "Nginx configuration is invalid"
        exit 1
    fi
}

# Function to build frontend
build_frontend() {
    print_status "Building frontend for production..."
    
    cd /opt/robot-console/frontend
    
    # Create production environment file
    cat > .env.production << EOF
VITE_API_URL=http://$VPS_IP:8000
EOF
    
    # Update backend .env with VPS IP if it exists
    if [ -f "/opt/robot-console/backend/.env" ]; then
        print_status "Updating backend .env with VPS IP: $VPS_IP"
        sed -i "s|VPS_URL=.*|VPS_URL=http://$VPS_IP|g" /opt/robot-console/backend/.env
        sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://$VPS_IP,http://$VPS_IP:3000,http://$VPS_IP:5173,http://$VPS_IP:80,http://$VPS_IP:443|g" /opt/robot-console/backend/.env
        sed -i "s|PRODUCTION_CORS_ORIGINS=.*|PRODUCTION_CORS_ORIGINS=http://$VPS_IP,http://$VPS_IP:3000,http://$VPS_IP:5173,http://$VPS_IP:80,http://$VPS_IP:443,https://your-domain.com|g" /opt/robot-console/backend/.env
    fi
    
    # Install dependencies and build
    npm install
    npm run build
    
    print_success "Frontend build completed"
}

# Function to check service health
check_service_health() {
    print_status "Checking service health..."
    
    # Wait a moment for services to start
    sleep 5
    
    # Check backend health
    if curl -s http://localhost:8000/health >/dev/null; then
        print_success "Backend health check passed"
    else
        print_error "Backend health check failed"
        return 1
    fi
    
    # Check if nginx is serving content
    if curl -s http://localhost/ >/dev/null; then
        print_success "Frontend health check passed"
    else
        print_error "Frontend health check failed"
        return 1
    fi
    
    # Test external access with VPS IP
    print_status "Testing external access with VPS IP: $VPS_IP"
    if curl -s -m 10 http://$VPS_IP/ >/dev/null 2>&1; then
        print_success "External access test passed"
    else
        print_warning "External access test failed - check firewall settings"
    fi
    
    print_success "All health checks passed!"
}

# Function to validate VPS configuration before deployment
validate_vps_config() {
    print_status "Validating VPS configuration..."
    
    # Check if frontend has correct API URL
    if grep -q "http://$VPS_IP:8000" frontend/src/api.js; then
        print_success "Frontend API configuration is correct"
    else
        print_warning "Frontend API configuration may need updating"
    fi
    
    # Check if backend .env exists and has VPS IP
    if [ -f "backend/.env" ]; then
        if grep -q "VPS_URL=http://$VPS_IP" backend/.env; then
            print_success "Backend VPS configuration is correct"
        else
            print_warning "Backend VPS configuration will be updated"
        fi
    fi
    
    # Test if VPS IP is reachable (ping test)
    if ping -c 1 -W 5 $VPS_IP >/dev/null 2>&1; then
        print_success "VPS IP $VPS_IP is reachable"
    else
        print_warning "VPS IP $VPS_IP may not be reachable (this might be normal if ping is disabled)"
    fi
}

# Main deployment function
main() {
    echo "🚀 VPS Deployment Script for Robot Console"
    echo "=========================================="
    echo
    
    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root or with sudo"
        exit 1
    fi
    
    # Parse command line arguments for VPS IP
    VPS_IP=""
    while [[ $# -gt 0 ]]; do
        case $1 in
            --vps-ip)
                VPS_IP="$2"
                shift 2
                ;;
            *)
                shift
                ;;
        esac
    done
    
    # Auto-detect VPS IP if not provided
    if [ -z "$VPS_IP" ]; then
        print_status "Auto-detecting VPS IP address..."
        VPS_IP=$(hostname -I | awk '{print $1}')
        if [ ! -z "$VPS_IP" ]; then
            print_success "Detected VPS IP: $VPS_IP"
        else
            print_warning "Could not auto-detect VPS IP. Using localhost."
            VPS_IP="localhost"
        fi
    else
        print_status "Using provided VPS IP: $VPS_IP"
    fi
    
    # Validate VPS configuration
    validate_vps_config
    
    # Check required ports
    print_status "Checking port availability..."
    print_status "Checking port availability..."
    if ! check_port 8000; then
        NEW_PORT=$(find_available_port 8001)
        print_warning "Using alternative port: $NEW_PORT"
        # Update service file with new port
        sed -i "s/:8000/:$NEW_PORT/g" robot-console-backend.service
    fi
    
    # Setup directories and permissions
    setup_directories
    
    # Setup Python environment
    setup_python_environment
    
    # Build frontend
    build_frontend
    
    # Setup systemd service
    setup_systemd_service
    
    # Start services
    start_services
    
    # Setup nginx
    setup_nginx
    
    # Check health
    if check_service_health; then
        echo
        print_success "🎉 Deployment completed successfully!"
        echo
        print_status "Service Status:"
        echo "  Backend: http://$VPS_IP:8000/health"
        echo "  Frontend: http://$VPS_IP/"
        echo "  API Docs: http://$VPS_IP:8000/docs"
        echo
        print_status "Management Commands:"
        echo "  sudo systemctl status robot-console-backend"
        echo "  sudo systemctl restart robot-console-backend"
        echo "  sudo systemctl stop robot-console-backend"
        echo "  sudo journalctl -u robot-console-backend -f"
        echo
    else
        print_error "Deployment completed with errors. Check logs for details."
        exit 1
    fi
}

# Check if Node.js and npm are installed
if ! command -v node >/dev/null 2>&1; then
    print_error "Node.js is not installed. Please install Node.js first."
    exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

# Run main function
main