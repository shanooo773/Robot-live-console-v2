# MySQL Migration and VPS Deployment Guide

This guide provides step-by-step instructions for migrating from SQLite to MySQL and deploying the Robot Console application on a VPS.

## Prerequisites

- Ubuntu/Debian VPS with sudo access
- Python 3.8+
- Node.js 16+
- Git

## Quick Start (VPS Deployment)

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/shanooo773/Robot-live-console-v2.git
cd Robot-live-console-v2

# Copy environment template
cp .env.template backend/.env
```

### 2. Configure Environment

Edit `backend/.env` with your settings:

```bash
# Database Configuration
DATABASE_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=robot_console
MYSQL_PASSWORD=your_strong_password_here
MYSQL_DATABASE=robot_console

# Environment
ENVIRONMENT=production

# CORS Origins - update with your domain/IP
PRODUCTION_CORS_ORIGINS=http://your-vps-ip,https://your-domain.com

# JWT Secret - generate a strong secret
SECRET_KEY=your-super-secret-jwt-key-here
```

### 3. Setup MySQL Database

```bash
# Run MySQL setup script
sudo ./setup_mysql.sh
```

This script will:
- Install MySQL if not present
- Create database and user
- Test connection
- Migrate existing SQLite data (if any)
- Update environment for production

### 4. Deploy Application

```bash
# Run VPS deployment script
sudo ./deploy_vps.sh
```

This script will:
- Setup directories with proper permissions
- Create system user for the service
- Install Python dependencies
- Build React frontend for production
- Setup systemd service
- Configure Nginx reverse proxy
- Start all services

### 5. Verify Deployment

Check that everything is running:

```bash
# Check backend service
sudo systemctl status robot-console-backend

# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost/

# View logs
sudo journalctl -u robot-console-backend -f
```

## Manual Migration Steps

If you prefer to migrate manually:

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Setup MySQL

```bash
# Install MySQL
sudo apt-get update
sudo apt-get install mysql-server

# Create database
mysql -u root -p
```

```sql
CREATE DATABASE robot_console CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'robot_console'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON robot_console.* TO 'robot_console'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Update Configuration

Edit `backend/.env`:
```bash
DATABASE_TYPE=mysql
ENVIRONMENT=production
```

### 4. Migrate Data

```bash
python migrate_to_mysql.py
```

### 5. Test Connection

```bash
cd backend
python -c "
from database import DatabaseManager
db = DatabaseManager()
print(f'Database type: {db.db_type}')
print('✅ Connection successful!')
"
```

## Database Configuration Options

### Development (SQLite)
```env
DATABASE_TYPE=sqlite
DATABASE_URL=sqlite:///robot_console.db
ENVIRONMENT=development
```

### Production (MySQL)
```env
DATABASE_TYPE=mysql
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=robot_console
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=robot_console
ENVIRONMENT=production
```

## Service Management

### Backend Service Commands

```bash
# Start/stop/restart backend
sudo systemctl start robot-console-backend
sudo systemctl stop robot-console-backend
sudo systemctl restart robot-console-backend

# Check status
sudo systemctl status robot-console-backend

# View logs
sudo journalctl -u robot-console-backend -f
sudo journalctl -u robot-console-backend --since "1 hour ago"
```

### Nginx Commands

```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# Restart nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status nginx
```

## Frontend Configuration

### Development
The frontend automatically detects the environment and uses:
- Development: `http://localhost:8000`
- Production: `/api` (proxied through Nginx)

### Custom API URL
Set environment variable:
```bash
export VITE_API_URL=http://your-custom-api-url
```

## Security Considerations

### 1. Database Security
- Use strong passwords
- Limit MySQL user privileges
- Configure firewall to restrict database access

### 2. Application Security
- Generate strong JWT secret key
- Use HTTPS in production
- Configure proper CORS origins
- Regular security updates

### 3. System Security
- Create dedicated system user
- Use proper file permissions
- Regular backups
- Monitor logs

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Check what's using the port
sudo lsof -i :8000

# Kill the process
sudo kill -9 <PID>

# Or use alternative port in systemd service
```

#### 2. Database Connection Failed
```bash
# Check MySQL status
sudo systemctl status mysql

# Test connection manually
mysql -u robot_console -p robot_console

# Check credentials in .env file
cat backend/.env | grep MYSQL
```

#### 3. Permission Denied
```bash
# Fix file permissions
sudo chown -R robot-console:robot-console /opt/robot-console
sudo chmod 755 /opt/robot-console/backend
sudo chmod 775 /opt/robot-console/backend/logs
```

#### 4. Service Won't Start
```bash
# Check detailed logs
sudo journalctl -u robot-console-backend -f

# Check service file
sudo systemctl cat robot-console-backend

# Reload systemd if service file changed
sudo systemctl daemon-reload
```

### Log Locations

- Application logs: `/opt/robot-console/backend/logs/`
- Systemd logs: `sudo journalctl -u robot-console-backend`
- Nginx logs: `/var/log/nginx/`
- MySQL logs: `/var/log/mysql/`

## Backup and Recovery

### Database Backup
```bash
# Create backup
mysqldump -u robot_console -p robot_console > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
mysql -u robot_console -p robot_console < backup_file.sql
```

### Application Backup
```bash
# Backup application files
sudo tar -czf robot_console_backup_$(date +%Y%m%d).tar.gz -C /opt robot-console
```

## Performance Optimization

### 1. Database Optimization
- Enable MySQL slow query log
- Add appropriate indexes
- Regular OPTIMIZE TABLE

### 2. Application Optimization
- Use connection pooling
- Enable caching
- Monitor resource usage

### 3. Nginx Optimization
- Enable gzip compression
- Configure proper caching headers
- Use HTTP/2

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review application logs
3. Check system resources (disk, memory, CPU)
4. Verify network connectivity

## Advanced Configuration

### Custom Domain Setup
1. Point domain to VPS IP
2. Update nginx configuration with domain name
3. Setup SSL certificate (Let's Encrypt recommended)

### Load Balancing
For high-traffic deployments, consider:
- Multiple backend instances
- Load balancer (nginx upstream)
- Database replication

### Monitoring
- Setup monitoring (Prometheus + Grafana)
- Configure alerts
- Log aggregation (ELK stack)