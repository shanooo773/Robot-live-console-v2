#!/bin/bash

# Enhanced MySQL Setup Script for Robot Console
# This script sets up MySQL for production deployment with modern security practices
# 
# Features:
# - MySQL 8.0+ compatibility with proper authentication
# - Secure password generation and validation
# - Configuration backup and validation
# - Enhanced error handling and retry logic
# - Systemd service integration
# - Dry-run mode for testing
# 
# Version: 2.0
# Updated: $(date +%Y-%m-%d)

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

# Function to generate secure password
generate_password() {
    local length=${1:-16}
    # Generate a secure password with mixed characters
    if command -v openssl >/dev/null 2>&1; then
        openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
    else
        # Fallback method
        head /dev/urandom | tr -dc A-Za-z0-9 | head -c $length
    fi
}

# Function to validate password strength
validate_password() {
    local password="$1"
    local min_length=8
    
    if [ ${#password} -lt $min_length ]; then
        return 1
    fi
    
    # Check for at least one letter, one number
    if [[ ! "$password" =~ [A-Za-z] ]] || [[ ! "$password" =~ [0-9] ]]; then
        return 1
    fi
    
    return 0
}

# Function to secure MySQL installation for version 8.0+
secure_mysql_installation() {
    print_status "Securing MySQL installation..."
    
    # Check MySQL version to determine security approach
    MYSQL_VERSION=$(mysql --version | grep -oP 'Ver \K[0-9]+\.[0-9]+' | head -1)
    MAJOR_VERSION=$(echo $MYSQL_VERSION | cut -d. -f1)
    MINOR_VERSION=$(echo $MYSQL_VERSION | cut -d. -f2)
    
    print_status "Detected MySQL version: $MYSQL_VERSION"
    
    # For MySQL 8.0+, handle the new authentication plugin
    if [ "$MAJOR_VERSION" -ge 8 ]; then
        print_status "Configuring MySQL 8.0+ security settings..."
        
        # Check if we can connect as root without password (fresh installation)
        if mysql -u root -e "SELECT 1;" >/dev/null 2>&1; then
            print_status "Setting up root password for fresh MySQL 8.0+ installation..."
            
            # Generate or prompt for root password
            if [ -z "$MYSQL_ROOT_PASSWORD" ]; then
                read -p "Enter new MySQL root password (leave empty to generate): " -s MYSQL_ROOT_PASSWORD
                echo
                if [ -z "$MYSQL_ROOT_PASSWORD" ]; then
                    MYSQL_ROOT_PASSWORD=$(generate_password 16)
                    print_success "Generated secure root password"
                fi
            fi
            
            # Set root password and authentication method
            mysql -u root <<EOF
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '$MYSQL_ROOT_PASSWORD';
DELETE FROM mysql.user WHERE User='';
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
DROP DATABASE IF EXISTS test;
DELETE FROM mysql.db WHERE Db='test' OR Db='test\\_%';
FLUSH PRIVILEGES;
EOF
            print_success "MySQL root account secured"
        else
            # Root password already set, prompt for it
            if [ -z "$MYSQL_ROOT_PASSWORD" ]; then
                read -p "Enter MySQL root password: " -s MYSQL_ROOT_PASSWORD
                echo
            fi
        fi
    else
        print_warning "MySQL version is older than 8.0. Some security features may not be available."
        if [ -z "$MYSQL_ROOT_PASSWORD" ]; then
            read -p "Enter MySQL root password: " -s MYSQL_ROOT_PASSWORD
            echo
        fi
    fi
}

# Function to check if MySQL is installed and get version
check_mysql() {
    if ! command -v mysql >/dev/null 2>&1; then
        print_error "MySQL is not installed!"
        print_status "Installing MySQL server..."
        
        # Detect OS and install MySQL
        if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Ubuntu/Debian
            if command -v apt-get >/dev/null 2>&1; then
                print_status "Updating package lists..."
                sudo apt-get update
                print_status "Installing MySQL 8.0 server and client..."
                sudo apt-get install -y mysql-server mysql-client
                
                # Start MySQL service
                sudo systemctl start mysql
                sudo systemctl enable mysql
                print_success "MySQL service started and enabled"
                
            # CentOS/RHEL/Rocky/Alma
            elif command -v yum >/dev/null 2>&1; then
                sudo yum install -y mysql-server mysql
                sudo systemctl start mysqld
                sudo systemctl enable mysqld
            elif command -v dnf >/dev/null 2>&1; then
                sudo dnf install -y mysql-server mysql
                sudo systemctl start mysqld
                sudo systemctl enable mysqld
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
        # Check MySQL version
        MYSQL_VERSION=$(mysql --version | grep -oP 'Ver \K[0-9]+\.[0-9]+')
        print_status "MySQL version: $MYSQL_VERSION"
        
        # Check if MySQL service is running
        if ! systemctl is-active --quiet mysql; then
            print_warning "MySQL service is not running. Starting..."
            sudo systemctl start mysql
            sudo systemctl enable mysql
            print_success "MySQL service started"
        fi
    fi
}

# Function to setup MySQL database and user with enhanced security
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
    DB_NAME=${MYSQL_DATABASE:-robot_console}
    
    # Handle password - generate if not set or validate if provided
    if [ -z "$MYSQL_PASSWORD" ] || [ "$MYSQL_PASSWORD" = "CHANGE_THIS_STRONG_PASSWORD" ]; then
        print_warning "No secure password found in .env file. Generating one..."
        NEW_DB_PASSWORD=$(generate_password 20)
        
        # Update .env file with new password
        if grep -q "^MYSQL_PASSWORD=" backend/.env; then
            sed -i "s/^MYSQL_PASSWORD=.*/MYSQL_PASSWORD=$NEW_DB_PASSWORD/" backend/.env
        else
            echo "MYSQL_PASSWORD=$NEW_DB_PASSWORD" >> backend/.env
        fi
        
        DB_PASSWORD="$NEW_DB_PASSWORD"
        print_success "Generated and saved secure database password"
    else
        DB_PASSWORD="$MYSQL_PASSWORD"
        if ! validate_password "$DB_PASSWORD"; then
            print_warning "Database password is weak. Consider using a stronger password."
        fi
    fi
    
    print_status "Database configuration:"
    echo "  Host: $DB_HOST"
    echo "  Port: $DB_PORT"
    echo "  Database: $DB_NAME"
    echo "  User: $DB_USER"
    echo "  Password: [PROTECTED]"
    
    # Secure MySQL installation if needed
    secure_mysql_installation
    
    # Test root connection
    if ! mysql -u root -p"$MYSQL_ROOT_PASSWORD" -e "SELECT 1;" >/dev/null 2>&1; then
        print_error "Cannot connect to MySQL as root. Please check the password."
        exit 1
    fi
    
    print_status "Creating database and user..."
    
    # Create database and user with proper authentication for MySQL 8.0+
    mysql -u root -p"$MYSQL_ROOT_PASSWORD" <<EOF
-- Create database with proper charset and collation
CREATE DATABASE IF NOT EXISTS \`$DB_NAME\` 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

-- Create user with secure authentication
CREATE USER IF NOT EXISTS '$DB_USER'@'localhost' 
    IDENTIFIED WITH mysql_native_password BY '$DB_PASSWORD';

-- Grant only necessary privileges (not ALL)
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER 
    ON \`$DB_NAME\`.* TO '$DB_USER'@'localhost';

-- Remove any existing remote access for security
DROP USER IF EXISTS '$DB_USER'@'%';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify database creation
USE \`$DB_NAME\`;
SHOW TABLES;
EOF

    if [ $? -eq 0 ]; then
        print_success "MySQL database and user created successfully!"
        print_status "Database user '$DB_USER' has been granted necessary privileges on '$DB_NAME'"
        print_status "For security, remote access has been disabled"
    else
        print_error "Failed to create MySQL database and user"
        exit 1
    fi
}

# Function to test database connection with retry logic
test_mysql_connection() {
    print_status "Testing database connection..."
    
    cd backend
    
    # Create enhanced test script with retry logic
    cat > test_mysql.py << 'EOF'
import os
import pymysql
import time
import sys
from dotenv import load_dotenv

load_dotenv()

config = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'robot_console'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'robot_console'),
    'charset': 'utf8mb4',
    'connect_timeout': 10,
    'read_timeout': 10,
    'write_timeout': 10
}

def test_connection_with_retry(retries=3, delay=2):
    """Test MySQL connection with retry logic"""
    for attempt in range(1, retries + 1):
        try:
            print(f"🔄 Connection attempt {attempt}/{retries}...")
            conn = pymysql.connect(**config)
            cursor = conn.cursor()
            
            # Test basic functionality
            cursor.execute("SELECT 1 as test")
            result = cursor.fetchone()
            
            # Test database access
            cursor.execute("SELECT DATABASE() as current_db")
            db_result = cursor.fetchone()
            
            # Test table creation (to verify privileges)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS connection_test (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    test_time DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Clean up test table
            cursor.execute("DROP TABLE IF EXISTS connection_test")
            
            cursor.close()
            conn.close()
            
            print(f"✅ MySQL connection successful!")
            print(f"   - Connected to database: {db_result[0] if db_result else 'N/A'}")
            print(f"   - Server version tested: {pymysql.__version__}")
            print(f"   - All privileges verified")
            return True
            
        except pymysql.Error as e:
            print(f"❌ Connection attempt {attempt} failed: {e}")
            if attempt < retries:
                print(f"   Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"❌ All connection attempts failed")
                return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    return False

if __name__ == "__main__":
    print("🔍 Testing MySQL database connection...")
    print(f"   Host: {config['host']}:{config['port']}")
    print(f"   Database: {config['database']}")
    print(f"   User: {config['user']}")
    
    success = test_connection_with_retry()
    sys.exit(0 if success else 1)
EOF

    # Check if virtual environment exists and activate it
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        
        # Install pymysql if not present
        if ! python -c "import pymysql" >/dev/null 2>&1; then
            print_status "Installing pymysql for connection test..."
            pip install pymysql python-dotenv
        fi
        
        # Run the enhanced test
        python test_mysql.py
        TEST_RESULT=$?
        rm -f test_mysql.py
        
    else
        print_error "Virtual environment not found. Please run deployment script first."
        print_status "Attempting system Python test..."
        
        # Try with system python as fallback
        if python3 -c "import pymysql, dotenv" >/dev/null 2>&1; then
            python3 test_mysql.py
            TEST_RESULT=$?
            rm -f test_mysql.py
        else
            print_error "Required Python packages not available. Install with: pip3 install pymysql python-dotenv"
            rm -f test_mysql.py
            cd ..
            return 1
        fi
    fi
    
    cd ..
    
    if [ $TEST_RESULT -eq 0 ]; then
        print_success "Database connection test passed!"
    else
        print_error "Database connection test failed!"
        print_status "Troubleshooting tips:"
        echo "  1. Check if MySQL service is running: sudo systemctl status mysql"
        echo "  2. Verify .env file configuration"
        echo "  3. Check MySQL error logs: sudo tail -f /var/log/mysql/error.log"
        echo "  4. Test manual connection: mysql -u $DB_USER -p$DB_PASSWORD $DB_NAME"
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

# Function to backup current configuration
backup_configuration() {
    print_status "Creating backup of current configuration..."
    
    BACKUP_DIR="backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup .env file
    if [ -f "backend/.env" ]; then
        cp "backend/.env" "$BACKUP_DIR/.env.backup"
        print_status "Backed up .env file"
    fi
    
    # Backup SQLite database if it exists
    if [ -f "backend/robot_console.db" ]; then
        cp "backend/robot_console.db" "$BACKUP_DIR/robot_console.db.backup"
        print_status "Backed up SQLite database"
    fi
    
    print_success "Configuration backed up to $BACKUP_DIR/"
    echo "$BACKUP_DIR" > .last_backup_dir
}

# Function to update environment for production with validation
update_env_for_mysql() {
    print_status "Updating .env file for MySQL production mode..."
    
    if [ ! -f "backend/.env" ]; then
        print_error ".env file not found!"
        exit 1
    fi
    
    # Create backup before modification
    cp "backend/.env" "backend/.env.backup.$(date +%Y%m%d_%H%M%S)"
    
    # Update DATABASE_TYPE to mysql
    if grep -q "^DATABASE_TYPE=" backend/.env; then
        sed -i 's/^DATABASE_TYPE=.*/DATABASE_TYPE=mysql/' backend/.env
    else
        echo "DATABASE_TYPE=mysql" >> backend/.env
    fi
    
    # Update ENVIRONMENT to production
    if grep -q "^ENVIRONMENT=" backend/.env; then
        sed -i 's/^ENVIRONMENT=.*/ENVIRONMENT=production/' backend/.env
    else
        echo "ENVIRONMENT=production" >> backend/.env
    fi
    
    # Ensure all required MySQL variables are present
    if ! grep -q "^MYSQL_HOST=" backend/.env; then
        echo "MYSQL_HOST=localhost" >> backend/.env
    fi
    
    if ! grep -q "^MYSQL_PORT=" backend/.env; then
        echo "MYSQL_PORT=3306" >> backend/.env
    fi
    
    if ! grep -q "^MYSQL_USER=" backend/.env; then
        echo "MYSQL_USER=robot_console" >> backend/.env
    fi
    
    if ! grep -q "^MYSQL_DATABASE=" backend/.env; then
        echo "MYSQL_DATABASE=robot_console" >> backend/.env
    fi
    
    # Generate SECRET_KEY if it's not set or is default
    if ! grep -q "^SECRET_KEY=" backend/.env || grep -q "^SECRET_KEY=your-secret-key-here" backend/.env; then
        SECRET_KEY=$(generate_password 32)
        if grep -q "^SECRET_KEY=" backend/.env; then
            sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" backend/.env
        else
            echo "SECRET_KEY=$SECRET_KEY" >> backend/.env
        fi
        print_success "Generated secure SECRET_KEY"
    fi
    
    print_success ".env file updated for production MySQL setup"
    
    # Validate the final configuration
    print_status "Validating final configuration..."
    source backend/.env
    
    local validation_errors=0
    
    if [ "$DATABASE_TYPE" != "mysql" ]; then
        print_error "DATABASE_TYPE is not set to mysql"
        validation_errors=$((validation_errors + 1))
    fi
    
    if [ -z "$MYSQL_PASSWORD" ]; then
        print_error "MYSQL_PASSWORD is not set"
        validation_errors=$((validation_errors + 1))
    fi
    
    if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-secret-key-here" ]; then
        print_error "SECRET_KEY is not properly configured"
        validation_errors=$((validation_errors + 1))
    fi
    
    if [ $validation_errors -eq 0 ]; then
        print_success "Configuration validation passed"
    else
        print_error "Configuration validation failed with $validation_errors errors"
        exit 1
    fi
}

# Function to display usage information
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dry-run          Perform dry run without making changes"
    echo "  --backup-only      Only create configuration backup"
    echo "  --skip-migration   Skip SQLite to MySQL data migration"
    echo "  --help, -h         Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  MYSQL_ROOT_PASSWORD    MySQL root password (optional)"
    echo "  SKIP_SECURITY_SETUP    Skip MySQL security configuration"
    echo ""
}

# Function to parse command line arguments
parse_arguments() {
    DRY_RUN=false
    BACKUP_ONLY=false
    SKIP_MIGRATION=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            --backup-only)
                BACKUP_ONLY=true
                shift
                ;;
            --skip-migration)
                SKIP_MIGRATION=true
                shift
                ;;
            --help|-h)
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
    echo "🗄️  MySQL Setup for Robot Console (Enhanced)"
    echo "============================================="
    echo
    
    # Check if we're in the right directory
    if [ ! -d "backend" ] || [ ! -f "migrate_to_mysql.py" ]; then
        print_error "Please run this script from the project root directory"
        exit 1
    fi
    
    # Handle backup-only mode
    if [ "$BACKUP_ONLY" = true ]; then
        backup_configuration
        print_success "Backup completed successfully!"
        exit 0
    fi
    
    # Handle dry-run mode
    if [ "$DRY_RUN" = true ]; then
        print_warning "DRY RUN MODE - No changes will be made"
        echo
    fi
    
    print_status "Starting enhanced MySQL setup process..."
    
    # Step 0: Create backup
    if [ "$DRY_RUN" = false ]; then
        backup_configuration
    else
        print_status "[DRY RUN] Would create configuration backup"
    fi
    
    # Step 1: Check and install MySQL
    if [ "$DRY_RUN" = false ]; then
        check_mysql
    else
        print_status "[DRY RUN] Would check and install MySQL if needed"
    fi
    
    # Step 2: Setup database and user
    if [ "$DRY_RUN" = false ]; then
        setup_mysql_database
    else
        print_status "[DRY RUN] Would setup MySQL database and user with enhanced security"
    fi
    
    # Step 3: Test connection
    if [ "$DRY_RUN" = false ]; then
        test_mysql_connection
    else
        print_status "[DRY RUN] Would test database connection with retry logic"
    fi
    
    # Step 4: Migrate existing data (optional)
    if [ "$SKIP_MIGRATION" = false ]; then
        if [ "$DRY_RUN" = false ]; then
            migrate_sqlite_data
        else
            print_status "[DRY RUN] Would migrate existing SQLite data to MySQL"
        fi
    else
        print_status "Skipping data migration (--skip-migration flag used)"
    fi
    
    # Step 5: Update environment
    if [ "$DRY_RUN" = false ]; then
        update_env_for_mysql
    else
        print_status "[DRY RUN] Would update .env file for MySQL production mode"
    fi
    
    echo
    if [ "$DRY_RUN" = false ]; then
        print_success "🎉 Enhanced MySQL setup completed successfully!"
        echo
        print_status "✨ New features in this setup:"
        echo "  • Enhanced security with MySQL 8.0+ authentication"
        echo "  • Automatic secure password generation"
        echo "  • Configuration backup and validation"
        echo "  • Improved error handling and retry logic"
        echo "  • Systemd service integration"
        echo
        print_status "📋 Next steps:"
        echo "  1. Restart your backend service: sudo systemctl restart robot-console-backend"
        echo "  2. Verify all functionality works with MySQL"
        echo "  3. Consider setting up automated backups"
        echo "  4. Monitor logs: sudo journalctl -u robot-console-backend -f"
        echo
        print_status "💾 Configuration backup saved in: $(cat .last_backup_dir 2>/dev/null || echo 'backup directory')"
    else
        print_success "🎉 Dry run completed - no changes were made"
        print_status "Run without --dry-run to apply changes"
    fi
    echo
}

# Check if script is run with sudo for MySQL installation
if [ "$EUID" -ne 0 ] && ! command -v mysql >/dev/null 2>&1; then
    print_warning "This script may need sudo privileges to install MySQL"
    print_status "You can run: sudo $0"
    echo
fi

# Parse command line arguments first
parse_arguments "$@"

# Run main function
main