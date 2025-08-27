#!/bin/bash

set -e  # Exit on any error

echo "🤖 Robot Live Console App Setup Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
BACKEND_PORT=8000
FRONTEND_PORT=3000

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

# Function to check if port is open
is_port_open() {
    local port=$1
    local host=${2:-localhost}
    
    if command_exists curl; then
        if curl -s --connect-timeout 2 "http://${host}:${port}/" > /dev/null 2>&1; then
            return 0
        fi
    fi
    
    if command_exists nc; then
        if nc -z "${host}" "${port}" 2>/dev/null; then
            return 0
        fi
    fi
    
    return 1
}

# Function to wait for service
wait_for_service() {
    local service_name=$1
    local port=$2
    local timeout=${3:-30}
    local host=${4:-localhost}
    
    print_status "Waiting for ${service_name} to start on port ${port}..."
    
    for i in $(seq 1 $timeout); do
        if is_port_open "$port" "$host"; then
            print_success "${service_name} started successfully on port ${port}"
            return 0
        fi
        
        if [ $((i % 5)) -eq 0 ]; then
            print_status "Still waiting for ${service_name}... (${i}/${timeout}s)"
        fi
        
        sleep 1
    done
    
    print_error "${service_name} failed to start within ${timeout} seconds"
    return 1
}

# Function to check system requirements
check_requirements() {
    print_status "Checking system requirements..."
    local errors=0
    
    # Check Python
    if ! command_exists python3; then
        print_error "Python 3 is required but not installed"
        errors=$((errors + 1))
    else
        python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        print_status "Python version: $python_version"
    fi
    
    # Check pip
    if ! command_exists pip3 && ! command_exists pip; then
        print_error "pip is required but not installed"
        errors=$((errors + 1))
    fi
    
    # Check Node.js
    if ! command_exists node; then
        print_error "Node.js is required but not installed"
        errors=$((errors + 1))
    else
        node_version=$(node --version)
        print_status "Node.js version: $node_version"
    fi
    
    # Check npm
    if ! command_exists npm; then
        print_error "npm is required but not installed"
        errors=$((errors + 1))
    else
        npm_version=$(npm --version)
        print_status "npm version: $npm_version"
    fi
    
    if [ $errors -gt 0 ]; then
        print_error "System requirements check failed with $errors errors"
        return 1
    fi
    
    print_success "System requirements check passed!"
    return 0
}

# Function to setup backend
setup_backend() {
    print_status "Setting up FastAPI backend..."
    
    cd backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    print_status "Installing Python dependencies..."
    if [ -f "venv/Scripts/activate" ]; then
        # Windows style
        source venv/Scripts/activate
    elif [ -f "venv/bin/activate" ]; then
        # Unix style
        source venv/bin/activate
    else
        print_error "Could not find virtual environment activation script"
        exit 1
    fi
    
    pip install -r requirements.txt
    
    # Create necessary directories
    mkdir -p videos temp
    
    cd ..
    print_success "Backend setup completed"
}

# Function to setup frontend
setup_frontend() {
    print_status "Setting up React frontend..."
    
    cd frontend
    
    # Install npm dependencies
    npm install
    
    cd ..
    print_success "Frontend setup completed"
}

# Function to start backend server
start_backend() {
    print_status "Starting FastAPI backend server..."
    
    cd backend
    
    # Activate virtual environment
    if [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    else
        print_error "Could not find virtual environment activation script"
        exit 1
    fi
    
    # Start backend in background
    nohup python main.py > backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > backend.pid
    
    cd ..
    
    # Wait for backend to start
    if ! wait_for_service "Backend" "$BACKEND_PORT" 30; then
        print_error "Backend startup failed. Check backend/backend.log for details."
        return 1
    fi
    
    return 0
}

# Function to start frontend server
start_frontend() {
    print_status "Starting React frontend server..."
    
    cd frontend
    
    # Start frontend in background
    nohup npm run dev > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > frontend.pid
    
    cd ..
    
    # Wait for frontend to start
    if ! wait_for_service "Frontend" "$FRONTEND_PORT" 30; then
        print_error "Frontend startup failed. Check frontend/frontend.log for details."
        return 1
    fi
    
    return 0
}

# Function to stop servers
stop_servers() {
    print_status "Stopping servers..."
    
    # Stop backend
    if [ -f "backend/backend.pid" ]; then
        BACKEND_PID=$(cat backend/backend.pid)
        if kill -0 "$BACKEND_PID" 2>/dev/null; then
            kill "$BACKEND_PID"
            print_status "Backend stopped"
        fi
        rm -f backend/backend.pid
    fi
    
    # Stop frontend
    if [ -f "frontend/frontend.pid" ]; then
        FRONTEND_PID=$(cat frontend/frontend.pid)
        if kill -0 "$FRONTEND_PID" 2>/dev/null; then
            kill "$FRONTEND_PID"
            print_status "Frontend stopped"
        fi
        rm -f frontend/frontend.pid
    fi
    
    print_success "All servers stopped"
}

# Function to show server status
show_status() {
    print_status "Checking server status..."
    
    # Check backend
    if is_port_open "$BACKEND_PORT"; then
        print_success "Backend is running on port $BACKEND_PORT"
    else
        print_warning "Backend is not running on port $BACKEND_PORT"
    fi
    
    # Check frontend
    if is_port_open "$FRONTEND_PORT"; then
        print_success "Frontend is running on port $FRONTEND_PORT"
    else
        print_warning "Frontend is not running on port $FRONTEND_PORT"
    fi
}

# Function to cleanup temporary files
cleanup() {
    print_status "Cleaning up temporary files..."
    rm -rf backend/temp/* 2>/dev/null || true
    rm -f backend/backend.log frontend/frontend.log 2>/dev/null || true
    print_success "Cleanup completed"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start    - Start the application (default)"
    echo "  stop     - Stop running servers"
    echo "  setup    - Setup dependencies only"
    echo "  status   - Show status of running servers"
    echo "  cleanup  - Clean up temporary files"
    echo "  check    - Check system requirements"
    echo "  help     - Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  BACKEND_PORT  - Backend server port (default: 8000)"
    echo "  FRONTEND_PORT - Frontend server port (default: 3000)"
}

# Main function
main() {
    local command=${1:-start}
    
    case $command in
        "start")
            check_requirements
            setup_backend
            setup_frontend
            start_backend
            start_frontend
            print_success "🎉 Robot Live Console App is running!"
            print_status "📱 Frontend: http://localhost:$FRONTEND_PORT"
            print_status "🔧 Backend API: http://localhost:$BACKEND_PORT"
            print_status "📊 API Docs: http://localhost:$BACKEND_PORT/docs"
            print_status ""
            print_status "🛑 To stop the application, run: $0 stop"
            ;;
        "stop")
            stop_servers
            ;;
        "setup")
            check_requirements
            setup_backend
            setup_frontend
            ;;
        "status")
            show_status
            ;;
        "cleanup")
            cleanup
            ;;
        "check")
            check_requirements
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"