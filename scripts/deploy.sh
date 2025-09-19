#!/bin/bash

set -e  # Exit on any error

echo "🚀 Robot Live Console App Deployment Script"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BACKEND_PORT=8000
FRONTEND_PORT=3000
PRODUCTION_MODE=False
VPS_IP=""


# Function to print colored output
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to deploy backend
deploy_backend() {
    print_status "Deploying FastAPI backend..."
	pwd    
    cd backend
    
    # Create production virtual environment
    if [ ! -d "venv" ]; then
        print_status "Creating production virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    if [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        print_error "Could not find virtual environment activation script"
        exit 1
    fi
    
    # Install production dependencies
    print_status "Installing production dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Create necessary directories
    mkdir -p videos temp logs
    
    # Copy environment template if .env doesn't exist
    if [ ! -f ".env" ] && [ -f "../.env.template" ]; then
        print_status "Creating .env file from template..."
        cp ../.env.template .env
        
        # Update VPS IP if provided
        if [ ! -z "$VPS_IP" ]; then
            print_status "Updating VPS IP to $VPS_IP in .env..."
            sed -i "s|VPS_URL=.*|VPS_URL=http://$VPS_IP|g" .env
            sed -i "s|CORS_ORIGINS=.*|CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://$VPS_IP,http://$VPS_IP:3000,http://$VPS_IP:5173|g" .env
            sed -i "s|PRODUCTION_CORS_ORIGINS=.*|PRODUCTION_CORS_ORIGINS=http://$VPS_IP,http://$VPS_IP:3000,http://$VPS_IP:5173,http://$VPS_IP:80,http://$VPS_IP:443,https://your-domain.com|g" .env
        fi
        
        print_warning "Please edit .env file with your production settings"
    fi
    
    # Start backend with production settings
    if [ "$PRODUCTION_MODE" = true ]; then
        print_status "Starting backend in production mode..."
        nohup gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$BACKEND_PORT > logs/backend.log 2>&1 &
        echo $! > backend.pid
    else
        print_status "Starting backend in development mode..."
        nohup python main.py > logs/backend.log 2>&1 &
        echo $! > backend.pid
    fi
    
    cd ..
    print_success "Backend deployed successfully"
}

# Function to deploy frontend
deploy_frontend() {
    print_status "Deploying React frontend..."
    pwd
    cd frontend
    
    # Install dependencies
    print_status "Installing frontend dependencies..."
    npm install
    
    if [ "$PRODUCTION_MODE" = true ]; then
        # Build for production
        print_status "Building frontend for production..."
        
        # Create production environment file
        if [ ! -z "$VPS_IP" ]; then
            print_status "Setting up production environment with VPS IP: $VPS_IP"
            cat > .env.production << EOF
VITE_API_URL=http://$VPS_IP:$BACKEND_PORT
EOF
        else
            cat > .env.production << EOF
VITE_API_URL=/api
EOF
        fi
        
        npm run build
        
        # Serve with a production server (e.g., serve)
        if ! command_exists serve; then
            print_status "Installing serve globally..."
            npm install -g serve
        fi
        
        print_status "Starting frontend production server..."
        nohup serve -s dist -l $FRONTEND_PORT > logs/frontend.log 2>&1 &
        echo $! > frontend.pid
    else
        # Start development server
        print_status "Starting frontend development server..."
        mkdir -p logs
        nohup npm run dev > logs/frontend.log 2>&1 &
        echo $! > frontend.pid
    fi
    
    cd ..
    print_success "Frontend deployed successfully"
}

# Function to setup nginx (if available)
setup_nginx() {
    if command_exists nginx; then
        print_status "Setting up nginx configuration..."
        
        # Create nginx config for the app
        cat > robot-console-app.nginx.conf << EOF
server {
    listen 80;
    server_name localhost;

    # Frontend
    location / {
        proxy_pass http://localhost:$FRONTEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # Backend API
    location /api {
        rewrite ^/api/(.*) /\$1 break;
        proxy_pass http://localhost:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }

    # Backend direct access
    location /docs {
        proxy_pass http://localhost:$BACKEND_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
        
        print_status "Nginx configuration created: robot-console-app.nginx.conf"
        print_warning "Please copy this configuration to your nginx sites-available directory"
    fi
}

# Function to install production dependencies
install_production_deps() {
    print_status "Installing production dependencies..."
    
    # Install gunicorn for production backend
    cd ../backend
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        pip install gunicorn
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
        pip install gunicorn
    fi
    cd ..
    
    # Install serve for production frontend
    if command_exists npm; then
        if [ "$PRODUCTION_MODE" = true ]; then
            npm install -g serve
        fi
    fi
}

# Function to create systemd service files
create_systemd_services() {
    if command_exists systemctl; then
        print_status "Creating systemd service files..."
        
        # Backend service
        cat > robot-console-backend.service << EOF
[Unit]
Description=Robot Console Backend
After=network.target

[Service]
Type=simple
User=\${USER}
WorkingDirectory=$(pwd)/backend
Environment=PATH=$(pwd)/backend/venv/bin
ExecStart=$(pwd)/backend/venv/bin/gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:$BACKEND_PORT
Restart=always

[Install]
WantedBy=multi-user.target
EOF
        
        # Frontend service
        cat > robot-console-frontend.service << EOF
[Unit]
Description=Robot Console Frontend
After=network.target

[Service]
Type=simple
User=\${USER}
WorkingDirectory=$(pwd)/frontend
ExecStart=/usr/local/bin/serve -s dist -l $FRONTEND_PORT
Restart=always

[Install]
WantedBy=multi-user.target
EOF
        
        print_status "Systemd service files created"
        print_warning "To install services, run:"
        print_warning "  sudo cp robot-console-*.service /etc/systemd/system/"
        print_warning "  sudo systemctl enable robot-console-backend"
        print_warning "  sudo systemctl enable robot-console-frontend"
        print_warning "  sudo systemctl start robot-console-backend"
        print_warning "  sudo systemctl start robot-console-frontend"
    fi
}

# Function to show deployment info
show_deployment_info() {
    print_success "🎉 Robot Live Console App deployed successfully!"
    echo ""
    print_status "📱 Frontend: http://localhost:$FRONTEND_PORT"
    print_status "🔧 Backend API: http://localhost:$BACKEND_PORT"
    print_status "📊 API Docs: http://localhost:$BACKEND_PORT/docs"
    echo ""
    
    if [ "$PRODUCTION_MODE" = true ]; then
        print_status "🏭 Production mode enabled"
        print_status "📂 Backend logs: backend/logs/backend.log"
        print_status "📂 Frontend logs: frontend/logs/frontend.log"
    else
        print_status "🔧 Development mode enabled"
    fi
    
    echo ""
    print_status "🛑 To stop the application:"
    print_status "  pkill -f 'python main.py'"
    print_status "  pkill -f 'npm run dev'"
    print_status "  or use: ./scripts/setup.sh stop"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --production    Deploy in production mode"
    echo "  -d, --development   Deploy in development mode (default)"
    echo "  --port-backend PORT Set backend port (default: 8000)"
    echo "  --port-frontend PORT Set frontend port (default: 3000)"
    echo "  --vps-ip IP         Set VPS IP address for configuration"
    echo "  --nginx             Setup nginx configuration"
    echo "  --systemd           Create systemd service files"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                  # Deploy in development mode"
    echo "  $0 --production     # Deploy in production mode"
    echo "  $0 --production --vps-ip 172.232.105.47 # Deploy with VPS IP"
    echo "  $0 --nginx --systemd # Deploy with nginx and systemd configs"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--production)
                PRODUCTION_MODE=true
                shift
                ;;
            -d|--development)
                PRODUCTION_MODE=false
                shift
                ;;
            --port-backend)
                BACKEND_PORT="$2"
                shift 2
                ;;
            --port-frontend)
                FRONTEND_PORT="$2"
                shift 2
                ;;
            --vps-ip)
                VPS_IP="$2"
                shift 2
                ;;
            --nginx)
                SETUP_NGINX=true
                shift
                ;;
            --systemd)
                SETUP_SYSTEMD=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# Main function
main() {
    parse_args "$@"
    
    print_status "Deployment mode: $([ "$PRODUCTION_MODE" = true ] && echo "Production" || echo "Development")"
    print_status "Backend port: $BACKEND_PORT"
    print_status "Frontend port: $FRONTEND_PORT"
    echo ""
    
    # Check requirements
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    if ! command_exists node; then
        print_error "Node.js is required but not installed"
        exit 1
    fi
    
    if ! command_exists npm; then
        print_error "npm is required but not installed"
        exit 1
    fi
    
    # Install production dependencies if needed
    if [ "$PRODUCTION_MODE" = true ]; then
        install_production_deps
    fi
    
    # Deploy services
    deploy_backend
    deploy_frontend
    
    # Setup additional services if requested
    if [ "$SETUP_NGINX" = true ]; then
        setup_nginx
    fi
    
    if [ "$SETUP_SYSTEMD" = true ]; then
        create_systemd_services
    fi
    
    # Wait for services to start
    sleep 5
    
    show_deployment_info
}

# Run main function with all arguments
main "$@"
