# VPS Deployment Checklist for Robot Console v2

## Pre-Deployment Requirements

### Server Requirements
- [ ] Ubuntu 20.04+ or Debian 11+ VPS
- [ ] Minimum 2GB RAM, 2 CPU cores
- [ ] 20GB+ storage space
- [ ] Root or sudo access
- [ ] Public IP address assigned

### Domain and DNS (Optional but Recommended)
- [ ] Domain name purchased and configured
- [ ] DNS A record pointing to VPS IP
- [ ] SSL certificate ready (Let's Encrypt recommended)

### Required Software Installation
- [ ] Docker 20.10+ installed
- [ ] Docker Compose 2.0+ installed
- [ ] Git installed
- [ ] Nginx installed (for reverse proxy)
- [ ] UFW or iptables configured for firewall

## Deployment Methods

Choose one of the following deployment methods:

### Method 1: Docker Deployment (Recommended)

#### Step 1: Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login to apply group changes
```

#### Step 2: Application Setup
```bash
# Clone repository
git clone https://github.com/shanooo773/Robot-live-console-v2.git
cd Robot-live-console-v2

# Setup Docker environment
./docker-setup.sh

# Configure environment
cp .env.docker .env
nano .env  # Update with production settings
```

#### Step 3: Production Configuration
Update `.env` file with production values:
```bash
# Database Configuration
MYSQL_PASSWORD=strong_production_password
MYSQL_ROOT_PASSWORD=strong_root_password

# Security
SECRET_KEY=generate_strong_secret_key_here
ENVIRONMENT=production

# Domain Configuration
PRODUCTION_CORS_ORIGINS=https://yourdomain.com,http://your-vps-ip

# Admin Configuration
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=strong_admin_password
```

#### Step 4: Deploy Services
```bash
# Deploy in production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check service status
docker-compose ps
docker-compose logs

# Verify health
curl http://localhost/health
curl http://localhost:8000/health
```

#### Step 5: Nginx Reverse Proxy Setup
```bash
# Create nginx site configuration
sudo nano /etc/nginx/sites-available/robot-console

# Add configuration:
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location / {
        proxy_pass http://localhost;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/robot-console /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### Step 6: SSL Certificate (Optional but Recommended)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Verify auto-renewal
sudo certbot renew --dry-run
```

### Method 2: Traditional VPS Deployment

Use the existing deployment scripts:

#### Step 1: Quick Setup
```bash
# Clone and configure
git clone https://github.com/shanooo773/Robot-live-console-v2.git
cd Robot-live-console-v2
cp .env.template backend/.env
```

#### Step 2: Configure Environment
Edit `backend/.env` with production settings as shown in DEPLOYMENT.md

#### Step 3: Setup Database
```bash
sudo ./setup_mysql.sh
```

#### Step 4: Deploy Application
```bash
sudo ./deploy_vps.sh
```

## Post-Deployment Verification

### Service Health Checks
- [ ] Frontend accessible at http://your-domain or http://your-ip
- [ ] Backend API responding at /api/health
- [ ] MySQL database connection working
- [ ] User registration and login working
- [ ] Booking system functional
- [ ] Theia IDE accessible (if using Docker method)

### Performance Checks
- [ ] Response times < 2 seconds
- [ ] Memory usage < 80%
- [ ] Disk usage < 80%
- [ ] CPU usage normal

### Security Verification
- [ ] Firewall configured (only necessary ports open)
- [ ] SSL certificate installed and working
- [ ] Admin credentials changed from defaults
- [ ] Database credentials are strong
- [ ] File permissions are correct

### Monitoring Setup
- [ ] Log rotation configured
- [ ] Backup strategy implemented
- [ ] Monitoring alerts configured
- [ ] Update schedule planned

## Firewall Configuration

### UFW (Ubuntu Firewall)
```bash
# Reset firewall
sudo ufw --force reset

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow MySQL (only if needed externally)
# sudo ufw allow 3306/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

### Docker-specific Firewall Rules
```bash
# If using Docker, ensure Docker networks don't bypass UFW
echo 'DOCKER_OPTS="--iptables=false"' | sudo tee -a /etc/default/docker
sudo systemctl restart docker
```

## Backup Strategy

### Database Backup
```bash
# Create automated backup script
cat > /opt/backup-robot-console.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/robot-console"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker exec robot-console-mysql mysqldump -u robot_console -p$MYSQL_PASSWORD robot_console > $BACKUP_DIR/db_backup_$DATE.sql

# Backup application data
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz /opt/robot-console/data /opt/robot-console/projects

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
EOF

# Make executable and add to cron
sudo chmod +x /opt/backup-robot-console.sh
sudo crontab -e
# Add: 0 2 * * * /opt/backup-robot-console.sh
```

## Troubleshooting

### Common Issues

#### Docker Services Not Starting
```bash
# Check Docker daemon
sudo systemctl status docker

# Check logs
docker-compose logs

# Restart services
docker-compose restart
```

#### Database Connection Issues
```bash
# Check MySQL status
docker exec robot-console-mysql mysql -u root -p -e "SHOW DATABASES;"

# Reset database
docker-compose down
docker volume rm robot-live-console-v2_mysql_data
docker-compose up -d
```

#### Port Conflicts
```bash
# Check what's using ports
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :8000

# Update docker-compose.yml port mappings if needed
```

### Log Locations
- Docker logs: `docker-compose logs [service]`
- Nginx logs: `/var/log/nginx/`
- System logs: `journalctl -u [service]`

## Maintenance

### Regular Tasks
- [ ] Weekly: Check service health and logs
- [ ] Monthly: Update Docker images
- [ ] Monthly: Review security logs
- [ ] Quarterly: Update system packages
- [ ] Quarterly: Review and rotate credentials

### Update Procedure
```bash
# Backup current state
./backup-robot-console.sh

# Pull latest changes
git pull origin main

# Rebuild and restart services
docker-compose build --no-cache
docker-compose up -d

# Verify deployment
curl http://localhost/health
```

## Support and Monitoring

### Health Monitoring
- Frontend: http://your-domain/health
- Backend: http://your-domain/api/health
- Database: Check via backend health endpoint

### Log Monitoring
```bash
# Real-time logs
docker-compose logs -f

# Service-specific logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mysql
```

### Performance Monitoring
```bash
# Resource usage
docker stats

# Disk usage
df -h
du -sh /opt/robot-console/data/*
```

---

## Final Checklist

Before going live:
- [ ] All services running and healthy
- [ ] SSL certificate installed and working
- [ ] Backup strategy tested
- [ ] Monitoring configured
- [ ] Security hardening complete
- [ ] Documentation updated with your specific configuration
- [ ] Team trained on maintenance procedures
- [ ] Emergency contact information documented

**Deployment completed successfully!** 🚀