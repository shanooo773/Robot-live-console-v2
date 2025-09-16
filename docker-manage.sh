#!/bin/bash

# Robot Console Docker Management Script

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Default configuration
ENVIRONMENT="development"
COMPOSE_FILES="-f docker-compose.yml"

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --prod|--production)
                ENVIRONMENT="production"
                shift
                ;;
            --dev|--development)
                ENVIRONMENT="development"
                shift
                ;;
            *)
                break
                ;;
        esac
    done
    
    # Set compose files based on environment
    case $ENVIRONMENT in
        production)
            COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
            ;;
        development)
            COMPOSE_FILES="-f docker-compose.yml -f docker-compose.dev.yml"
            ;;
        *)
            COMPOSE_FILES="-f docker-compose.yml"
            ;;
    esac
    
    print_status "Environment: $ENVIRONMENT"
    print_status "Compose files: $COMPOSE_FILES"
}

# Commands
cmd_start() {
    print_status "Starting Robot Console services..."
    
    # Create data directories for development
    if [ "$ENVIRONMENT" = "development" ]; then
        mkdir -p data/{mysql,logs,videos}
    fi
    
    docker-compose $COMPOSE_FILES up -d
    
    print_success "Services started successfully!"
    cmd_status
}

cmd_stop() {
    print_status "Stopping Robot Console services..."
    docker-compose $COMPOSE_FILES down
    print_success "Services stopped!"
}

cmd_restart() {
    print_status "Restarting Robot Console services..."
    docker-compose $COMPOSE_FILES restart
    print_success "Services restarted!"
}

cmd_build() {
    print_status "Building Robot Console images..."
    docker-compose $COMPOSE_FILES build --no-cache
    print_success "Images built successfully!"
}

cmd_logs() {
    local service="${1:-}"
    if [ -n "$service" ]; then
        docker-compose $COMPOSE_FILES logs -f "$service"
    else
        docker-compose $COMPOSE_FILES logs -f
    fi
}

cmd_status() {
    print_status "Robot Console Service Status:"
    echo
    docker-compose $COMPOSE_FILES ps
    echo
    
    # Health checks
    print_status "Health Status:"
    
    # Check backend
    if curl -s -f "http://localhost:8000/health" >/dev/null 2>&1; then
        print_success "✓ Backend API"
    else
        print_error "✗ Backend API"
    fi
    
    # Check frontend
    if curl -s -f "http://localhost/health" >/dev/null 2>&1; then
        print_success "✓ Frontend"
    else
        print_error "✗ Frontend"
    fi
    
    # Check database
    if docker-compose $COMPOSE_FILES exec -T mysql mysqladmin ping -h localhost >/dev/null 2>&1; then
        print_success "✓ MySQL Database"
    else
        print_error "✗ MySQL Database"
    fi
}

cmd_shell() {
    local service="${1:-backend}"
    print_status "Opening shell in $service container..."
    docker-compose $COMPOSE_FILES exec "$service" /bin/bash
}

cmd_clean() {
    print_warning "This will remove all containers, images, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up..."
        docker-compose $COMPOSE_FILES down -v --rmi all
        docker system prune -f
        print_success "Cleanup completed!"
    else
        print_status "Cleanup cancelled."
    fi
}

cmd_backup() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    print_status "Creating backup..."
    
    # Backup database
    docker-compose $COMPOSE_FILES exec -T mysql mysqldump -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword}" robot_console > "$backup_dir/database.sql"
    
    # Backup volumes
    docker run --rm -v robot-console-backend-videos:/data -v "$(pwd)/$backup_dir:/backup" alpine tar czf /backup/videos.tar.gz -C /data .
    docker run --rm -v robot-console-backend-logs:/data -v "$(pwd)/$backup_dir:/backup" alpine tar czf /backup/logs.tar.gz -C /data .
    
    print_success "Backup created: $backup_dir"
}

cmd_restore() {
    local backup_dir="$1"
    
    if [ -z "$backup_dir" ]; then
        print_error "Please specify backup directory"
        exit 1
    fi
    
    if [ ! -d "$backup_dir" ]; then
        print_error "Backup directory not found: $backup_dir"
        exit 1
    fi
    
    print_status "Restoring from backup: $backup_dir"
    
    # Restore database
    if [ -f "$backup_dir/database.sql" ]; then
        docker-compose $COMPOSE_FILES exec -T mysql mysql -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword}" robot_console < "$backup_dir/database.sql"
        print_success "Database restored"
    fi
    
    # Restore volumes
    if [ -f "$backup_dir/videos.tar.gz" ]; then
        docker run --rm -v robot-console-backend-videos:/data -v "$(pwd)/$backup_dir:/backup" alpine tar xzf /backup/videos.tar.gz -C /data
        print_success "Videos restored"
    fi
    
    if [ -f "$backup_dir/logs.tar.gz" ]; then
        docker run --rm -v robot-console-backend-logs:/data -v "$(pwd)/$backup_dir:/backup" alpine tar xzf /backup/logs.tar.gz -C /data
        print_success "Logs restored"
    fi
    
    print_success "Restore completed!"
}

cmd_help() {
    echo "Robot Console Docker Management Script"
    echo
    echo "Usage: $0 [OPTIONS] COMMAND [ARGS]"
    echo
    echo "Options:"
    echo "  --env ENV                Set environment (development|production)"
    echo "  --dev, --development     Use development environment"
    echo "  --prod, --production     Use production environment"
    echo
    echo "Commands:"
    echo "  start                    Start all services"
    echo "  stop                     Stop all services"
    echo "  restart                  Restart all services"
    echo "  build                    Build all images"
    echo "  status                   Show service status and health"
    echo "  logs [SERVICE]           Show logs (all services or specific service)"
    echo "  shell [SERVICE]          Open shell in container (default: backend)"
    echo "  clean                    Remove all containers, images, and volumes"
    echo "  backup                   Create backup of data and database"
    echo "  restore BACKUP_DIR       Restore from backup"
    echo "  help                     Show this help message"
    echo
    echo "Examples:"
    echo "  $0 --dev start           Start in development mode"
    echo "  $0 --prod start          Start in production mode"
    echo "  $0 logs backend          Show backend logs"
    echo "  $0 shell mysql           Open MySQL shell"
    echo "  $0 backup                Create backup"
    echo "  $0 restore backups/20231201_120000"
}

# Main script
main() {
    parse_args "$@"
    
    case "$1" in
        start)
            cmd_start
            ;;
        stop)
            cmd_stop
            ;;
        restart)
            cmd_restart
            ;;
        build)
            cmd_build
            ;;
        logs)
            cmd_logs "$2"
            ;;
        status)
            cmd_status
            ;;
        shell)
            cmd_shell "$2"
            ;;
        clean)
            cmd_clean
            ;;
        backup)
            cmd_backup
            ;;
        restore)
            cmd_restore "$2"
            ;;
        help|--help|-h)
            cmd_help
            ;;
        "")
            print_error "No command specified"
            cmd_help
            exit 1
            ;;
        *)
            print_error "Unknown command: $1"
            cmd_help
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"