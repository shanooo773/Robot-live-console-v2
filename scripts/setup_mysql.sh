#!/bin/bash

# MySQL Setup Script for Robot Console
# This script sets up MySQL for production deployment

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

# Function to check if MySQL is installed
check_mysql() {
    if ! command -v mysql >/dev/null 2>&1; then
        print_error "MySQL is not installed!"
        print_status "Installing MySQL server..."
        
        # Detect OS and install MySQL
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Ubuntu/Debian
            if command -v apt-get >/dev/null 2>&1; then
                sudo apt-get update
                sudo apt-get install -y mysql-server mysql-client
            # CentOS/RHEL
            elif command -v yum >/dev/null 2>&1; then
                sudo yum install -y mysql-server mysql
            else
                print_error "Unsupported Linux distribution. Please install MySQL manually."
                exit 1
            fi
        else
            print_error "Unsupported operating system. Please install MySQL manually."
            exit 1
        fi
    else
        print_success "MySQL is already installed"
    fi
}

# Function to setup MySQL database and user
setup_mysql_database() {
    print_status "Setting up MySQL database and user..."
    
    # Read configuration from .env file
    if [ -f "backend/.env" ]; then
        source backend/.env
    else
        print_error ".env file not found in backend directory!"
        exit 1
    fi
    
    # Use environment variables or defaults
    DB_HOST=${MYSQL_HOST:-localhost}
    DB_PORT=${MYSQL_PORT:-3306}
    DB_USER=${MYSQL_USER:-robot_console}
    DB_PASSWORD=${MYSQL_PASSWORD:-robot_console_pass}
    DB_NAME=${MYSQL_DATABASE:-robot_console}
    
    print_status "Database configuration:"
    echo "  Host: $DB_HOST"
    echo "  Port: $DB_PORT"
    echo "  Database: $DB_NAME"
    echo "  User: $DB_USER"
    
    # Create MySQL commands
    read -p "Enter MySQL root password: " -s MYSQL_ROOT_PASSWORD
    echo
    
    # Create database and user
    mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<EOF
CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' IDENTIFIED BY '$DB_PASSWORD';
CREATE USER IF NOT EXISTS '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'localhost';
GRANT ALL PRIVILEGES ON \`$DB_NAME\`.* TO '$DB_USER'@'%';
FLUSH PRIVILEGES;
EOF

    if [ $? -eq 0 ]; then
        print_success "MySQL database and user created successfully!"
    else
        print_error "Failed to create MySQL database and user"
        exit 1
    fi
}

# Function to test database connection
test_mysql_connection() {
    print_status "Testing database connection..."
    
    cd backend
    
    # Create temporary test script
    cat > test_mysql.py << 'EOF'
import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'robot_console'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'robot_console'),
    'charset': 'utf8mb4'
}

try:
    conn = pymysql.connect(**config)
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    result = cursor.fetchone()
    conn.close()
    print("✅ MySQL connection successful!")
    exit(0)
except Exception as e:
    print(f"❌ MySQL connection failed: {e}")
    exit(1)
EOF

    # Run the test
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        python test_mysql.py
        TEST_RESULT=$?
        rm test_mysql.py
    else
        print_error "Virtual environment not found. Please run deployment script first."
        exit 1
    fi
    
    cd ..
    
    if [ $TEST_RESULT -eq 0 ]; then
        print_success "Database connection test passed!"
    else
        print_error "Database connection test failed!"
        exit 1
    fi
}

# Function to migrate existing SQLite data
migrate_sqlite_data() {
    if [ -f "backend/robot_console.db" ]; then
        print_status "Found existing SQLite database. Migrating data to MySQL..."
        
        cd backend
        
        if [ -f "venv/bin/activate" ]; then
            source venv/bin/activate
            python ../migrate_to_mysql.py
        else
            print_error "Virtual environment not found!"
            exit 1
        fi
        
        cd ..
        
        print_success "Data migration completed!"
    else
        print_status "No existing SQLite database found. Skipping migration."
    fi
}

# Function to update environment for production
update_env_for_mysql() {
    print_status "Updating .env file for MySQL production mode..."
    
    if [ -f "backend/.env" ]; then
        # Update DATABASE_TYPE to mysql
        sed -i 's/DATABASE_TYPE=sqlite/DATABASE_TYPE=mysql/' backend/.env
        # Update ENVIRONMENT to production
        sed -i 's/ENVIRONMENT=development/ENVIRONMENT=production/' backend/.env
        
        print_success ".env file updated for production MySQL setup"
    else
        print_error ".env file not found!"
        exit 1
    fi
}

# Main function
main() {
    echo "🗄️  MySQL Setup for Robot Console"
    echo "=================================="
    echo
    
    # Check if we're in the right directory
    if [ ! -d "backend" ] || [ ! -f "migrate_to_mysql.py" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    print_status "Starting MySQL setup process..."
    
    # Step 1: Check and install MySQL
    check_mysql
    
    # Step 2: Setup database and user
    setup_mysql_database
    
    # Step 3: Test connection
    test_mysql_connection
    
    # Step 4: Migrate existing data
    migrate_sqlite_data
    
    # Step 5: Update environment
    update_env_for_mysql
    
    echo
    print_success "🎉 MySQL setup completed successfully!"
    print_status "Next steps:"
    echo "  1. Restart your backend service"
    echo "  2. Verify all functionality works with MySQL"
    echo "  3. Consider setting up automated backups"
    echo
}

# Check if script is run with sudo for MySQL installation
if [ "$EUID" -ne 0 ] && ! command -v mysql >/dev/null 2>&1; then
    print_warning "This script may need sudo privileges to install MySQL"
    print_status "You can run: sudo $0"
    echo
fi

# Run main function
main