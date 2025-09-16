# Robot Console Docker Deployment Guide

This guide provides comprehensive instructions for deploying the Robot Console application using Docker containers.

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Prerequisites](#prerequisites)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Deployment Options](#deployment-options)
- [Management](#management)
- [Troubleshooting](#troubleshooting)
- [Security](#security)
- [Backup & Recovery](#backup--recovery)

## 🚀 Quick Start

### For VPS Production Deployment

```bash
# Clone the repository
git clone https://github.com/shanooo773/Robot-live-console-v2.git
cd Robot-live-console-v2

# Copy and configure environment
cp .env.docker .env
# Edit .env with your production settings

# Run the automated deployment script
sudo ./docker-deploy.sh
```

### For Development

```bash
# Start development environment
./docker-manage.sh --dev start

# View logs
./docker-manage.sh logs

# Stop services
./docker-manage.sh stop
```

## 📦 Prerequisites

### System Requirements

- **OS**: Ubuntu 20.04+ or Debian 11+ (recommended)
- **RAM**: Minimum 4GB, recommended 8GB+
- **Storage**: Minimum 20GB free space
- **CPU**: 2+ cores recommended

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Git
- curl

The deployment script will automatically install Docker if not present.

## 🏗️ Architecture

The Docker setup includes the following services:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │────│    Frontend     │────│    Backend      │
│   (Port 80/443) │    │   (React SPA)   │    │   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Video Server   │    │   MySQL DB      │
                       │   (Kurento)     │    │  (Persistent)   │
                       └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Theia IDE      │    │     Redis       │
                       │ (User Containers)│    │   (Optional)    │
                       └─────────────────┘    └─────────────────┘
```

### Services

1. **Frontend** (nginx:alpine)
   - React application built with Vite
   - Served via Nginx with optimized configuration
   - Port: 80 (internal)

2. **Backend** (python:3.11-slim)
   - FastAPI application with Gunicorn
   - Handles API requests and WebSocket connections
   - Port: 8000 (internal)

3. **MySQL** (mysql:8.0)
   - Primary database for application data
   - Persistent storage with volume mounts
   - Port: 3306 (internal)

4. **Video Server** (kurento/kurento-media-server)
   - WebRTC/RTSP video streaming
   - Handles robot video feeds
   - Port: 8888 (internal)

5. **Theia IDE** (custom image)
   - Eclipse Theia-based code editor
   - Per-user container instances
   - Port: 3000 (per container)

6. **Nginx Proxy** (nginx:alpine) - Production only
   - Reverse proxy for all services
   - SSL termination (optional)
   - Port: 80, 443

7. **Redis** (redis:7-alpine) - Optional
   - Session management and caching
   - Port: 6379 (internal)

## ⚙️ Configuration

### Environment Variables

Copy `.env.docker` to `.env` and configure:

```bash
cp .env.docker .env
```

#### Required Variables

```bash
# Database
MYSQL_ROOT_PASSWORD=your_strong_root_password
MYSQL_PASSWORD=your_strong_password
MYSQL_DATABASE=robot_console

# Security
SECRET_KEY=your_jwt_secret_key_32_characters_minimum

# Network
PRODUCTION_CORS_ORIGINS=https://yourdomain.com,http://your-vps-ip
VPS_URL=http://your-vps-ip
```

#### Optional Variables

```bash
# SSL (for production)
SSL_ENABLED=true
DOMAIN_NAME=yourdomain.com

# Video
MAX_VIDEO_SIZE_MB=100

# Admin
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=secure_admin_password
```

### Docker Compose Profiles

- **Default**: Core services (mysql, backend, frontend, theia-base, video-server)
- **Production**: Adds nginx-proxy and redis
- **Development**: Adds adminer and development overrides
- **Monitoring**: Adds watchtower for auto-updates

## 🚢 Deployment Options

### 1. Development Deployment

For local development with hot reloading:

```bash
# Start development environment
./docker-manage.sh --dev start

# Access services
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# Database Admin: http://localhost:8080 (Adminer)
```

### 2. Production Deployment

#### Automated VPS Deployment

```bash
sudo ./docker-deploy.sh
```

This script will:
- Install Docker and Docker Compose
- Set up project directories
- Configure environment
- Build and deploy all services
- Set up SSL (optional)
- Configure firewall
- Run health checks

#### Manual Production Deployment

```bash
# Copy and configure environment
cp .env.docker .env
# Edit .env with production values

# Build images
docker-compose build

# Start production services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Or use the management script
./docker-manage.sh --prod start
```

### 3. Staging Deployment

```bash
# Use base configuration with minimal overrides
docker-compose up -d mysql backend frontend video-server
```

## 🎛️ Management

### Using the Management Script

The `docker-manage.sh` script provides convenient management commands:

```bash
# Service management
./docker-manage.sh --prod start      # Start production services
./docker-manage.sh --dev start       # Start development services
./docker-manage.sh stop              # Stop all services
./docker-manage.sh restart           # Restart all services
./docker-manage.sh status            # Show service status

# Development
./docker-manage.sh build             # Build all images
./docker-manage.sh logs backend      # Show backend logs
./docker-manage.sh shell mysql       # Open MySQL shell

# Maintenance
./docker-manage.sh backup            # Create backup
./docker-manage.sh clean             # Clean up everything
```

### Manual Docker Commands

```bash
# View service status
docker-compose ps

# View logs
docker-compose logs -f [service_name]

# Scale services
docker-compose up -d --scale backend=3

# Update services
docker-compose pull
docker-compose up -d

# Execute commands in containers
docker-compose exec backend bash
docker-compose exec mysql mysql -u root -p
```

### Health Monitoring

All services include health checks:

```bash
# Check overall health
./docker-manage.sh status

# Individual service health
curl http://localhost/health          # Frontend
curl http://localhost:8000/health     # Backend (if exposed)
docker-compose exec mysql mysqladmin ping -h localhost
```

## 🔧 Troubleshooting

### Common Issues

#### 1. Port Conflicts

```bash
# Check what's using a port
sudo lsof -i :80
sudo lsof -i :3306

# Stop conflicting services
sudo systemctl stop apache2
sudo systemctl stop mysql
```

#### 2. Permission Issues

```bash
# Fix Docker permissions
sudo usermod -aG docker $USER
newgrp docker

# Fix volume permissions
sudo chown -R 1000:1000 data/
```

#### 3. Database Connection Issues

```bash
# Check MySQL status
docker-compose exec mysql mysqladmin ping -h localhost

# View MySQL logs
docker-compose logs mysql

# Reset database
docker-compose down -v
docker-compose up -d mysql
```

#### 4. Build Failures

```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache

# Check disk space
df -h
docker system df
```

### Log Locations

```bash
# Application logs
docker-compose logs [service]

# Container logs
docker logs [container_name]

# Host logs
journalctl -u docker.service
```

### Debug Mode

Enable debug logging:

```bash
# In .env file
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart
```

## 🔒 Security

### Production Security Checklist

- [ ] Change all default passwords
- [ ] Use strong JWT secret key
- [ ] Enable SSL/TLS
- [ ] Configure firewall
- [ ] Set up log monitoring
- [ ] Regular security updates
- [ ] Backup strategy
- [ ] Monitor resource usage

### SSL/TLS Setup

#### Let's Encrypt (Automated)

The deployment script can set up Let's Encrypt automatically:

```bash
sudo ./docker-deploy.sh
# Follow prompts for SSL setup
```

#### Manual SSL Setup

```bash
# Create SSL directory
mkdir -p ssl/

# Copy your certificates
cp your-cert.pem ssl/cert.pem
cp your-key.pem ssl/key.pem

# Update environment
echo "SSL_ENABLED=true" >> .env

# Restart nginx proxy
docker-compose restart nginx-proxy
```

### Firewall Configuration

```bash
# Install and configure UFW
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

## 💾 Backup & Recovery

### Automated Backups

```bash
# Create backup
./docker-manage.sh backup

# Backup location: backups/YYYYMMDD_HHMMSS/
```

### Manual Backup

```bash
# Database backup
docker-compose exec mysql mysqldump -u root -pROOT_PASSWORD robot_console > backup.sql

# Volume backup
docker run --rm -v robot-console-mysql-data:/data -v $(pwd):/backup alpine tar czf /backup/mysql-data.tar.gz -C /data .
```

### Restore

```bash
# Restore from backup
./docker-manage.sh restore backups/20231201_120000

# Manual restore
docker-compose exec -T mysql mysql -u root -pROOT_PASSWORD robot_console < backup.sql
```

### Scheduled Backups

Add to crontab:

```bash
# Daily backup at 2 AM
0 2 * * * cd /opt/robot-console && ./docker-manage.sh backup
```

## 📊 Monitoring & Maintenance

### Log Rotation

Logs are automatically rotated using Docker's built-in log rotation:

```json
"log-driver": "json-file",
"log-opts": {
    "max-size": "10m",
    "max-file": "3"
}
```

### Resource Monitoring

```bash
# Monitor resource usage
docker stats

# Monitor disk usage
docker system df

# Clean up unused resources
docker system prune -f
```

### Updates

```bash
# Update images
docker-compose pull

# Restart with new images
docker-compose up -d

# Auto-updates with Watchtower (production profile)
docker-compose --profile monitoring up -d watchtower
```

## 🌐 Access URLs

After successful deployment:

- **Frontend**: `http://your-vps-ip/` or `https://yourdomain.com/`
- **API Documentation**: `http://your-vps-ip/api/docs`
- **API Health**: `http://your-vps-ip/api/health`
- **Video Streaming**: `http://your-vps-ip/video/`
- **Theia IDE**: `http://your-vps-ip/theia/{user_id}/`

## 📞 Support

For issues and questions:

1. Check the [troubleshooting section](#troubleshooting)
2. Review service logs: `./docker-manage.sh logs`
3. Check service health: `./docker-manage.sh status`
4. Verify environment configuration
5. Check system resources and connectivity

## 🔄 Migration from Non-Docker Setup

If migrating from a non-Docker deployment:

1. **Backup existing data**:
   ```bash
   mysqldump -u robot_console -p robot_console > migration-backup.sql
   cp -r backend/videos migration-videos/
   ```

2. **Deploy Docker setup**:
   ```bash
   ./docker-deploy.sh
   ```

3. **Import data**:
   ```bash
   docker-compose exec -T mysql mysql -u root -p robot_console < migration-backup.sql
   docker cp migration-videos/. robot-console-backend:/app/videos/
   ```

4. **Verify migration**:
   ```bash
   ./docker-manage.sh status
   ```

## 📝 Final VPS Deployment Checklist

- [ ] Install prerequisites (Docker, Docker Compose)
- [ ] Clone repository and configure environment
- [ ] Update security settings (passwords, JWT secret)
- [ ] Configure domain/IP settings
- [ ] Run deployment script
- [ ] Verify all services are healthy
- [ ] Set up SSL certificates (recommended)
- [ ] Configure firewall
- [ ] Set up automated backups
- [ ] Configure monitoring (optional)
- [ ] Test all functionality
- [ ] Document any custom configurations

## 🎯 Production-Ready Features

✅ **Container Orchestration**: Full Docker Compose setup  
✅ **Health Checks**: All services include health monitoring  
✅ **Persistent Storage**: Data volumes for database and files  
✅ **Environment Isolation**: Separate dev/prod configurations  
✅ **Security**: Non-root users, secrets management  
✅ **SSL/TLS**: Optional HTTPS with Let's Encrypt  
✅ **Monitoring**: Health checks and log management  
✅ **Backup**: Automated backup and restore scripts  
✅ **Updates**: Auto-update capability with Watchtower  
✅ **Scaling**: Ready for horizontal scaling  
✅ **Networking**: Isolated Docker networks  
✅ **Reverse Proxy**: Nginx for routing and SSL termination