# Docker Deployment Guide for Robot Console v2

This guide covers running the Robot Console application using Docker containers.

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ available RAM
- 10GB+ available disk space

### Setup and Run

1. **Clone and setup:**
```bash
git clone https://github.com/shanooo773/Robot-live-console-v2.git
cd Robot-live-console-v2
./docker-setup.sh
```

2. **Configure environment:**
```bash
# Copy Docker environment template
cp .env.docker .env

# Edit with your settings
nano .env
```

3. **Start services:**
```bash
# Development
docker-compose up -d

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

4. **Verify deployment:**
```bash
./docker-health-check.sh
```

## Services Overview

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| Frontend | 80 | React web application | http://localhost/health |
| Backend | 8000 | FastAPI Python backend | http://localhost:8000/health |
| MySQL | 3306 | Database server | Internal |
| Theia IDE | 3001 | Eclipse Theia development environment | http://localhost:3001 |
| WebRTC* | 8081 | Video streaming (future) | Not implemented |

*WebRTC service is disabled by default (placeholder for future implementation)

## Volume Persistence

All important data is persisted in Docker volumes:

- **Database:** `./data/mysql` - MySQL database files
- **Videos:** `./data/videos` - Simulation video recordings  
- **IDE Files:** `./data/theia` - Theia workspace files
- **Projects:** `./projects` - User project files (shared with host)

## Environment Configuration

Key environment variables in `.env`:

### Database
```bash
MYSQL_USER=robot_console
MYSQL_PASSWORD=strong_password_here
MYSQL_DATABASE=robot_console
MYSQL_ROOT_PASSWORD=strong_root_password
```

### Application
```bash
SECRET_KEY=your-super-secret-jwt-key
ENVIRONMENT=production
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=strong_admin_password
```

### CORS (Important for production)
```bash
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
PRODUCTION_CORS_ORIGINS=https://yourdomain.com,http://your-vps-ip
```

## Service Management

### Basic Commands
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart backend

# View logs
docker-compose logs -f
docker-compose logs -f backend

# Check status
docker-compose ps
```

### Health Monitoring
```bash
# Run health check script
./docker-health-check.sh

# Manual health checks
curl http://localhost/health
curl http://localhost:8000/health
curl http://localhost:3001
```

### Database Management
```bash
# Access MySQL console
docker exec -it robot-console-mysql mysql -u robot_console -p

# Backup database
docker exec robot-console-mysql mysqldump -u robot_console -p robot_console > backup.sql

# Restore database
docker exec -i robot-console-mysql mysql -u robot_console -p robot_console < backup.sql
```

## Production Deployment

### 1. Environment Setup
```bash
# Update production environment
cp .env.docker .env
nano .env  # Update with production values
```

### 2. Production Docker Compose
```bash
# Deploy with production overrides
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. Reverse Proxy (Recommended)
Set up Nginx as reverse proxy:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. SSL Certificate
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com
```

## Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check Docker daemon
sudo systemctl status docker

# Check logs for errors
docker-compose logs

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

#### Database Connection Issues
```bash
# Check MySQL logs
docker-compose logs mysql

# Verify database exists
docker exec robot-console-mysql mysql -u root -p -e "SHOW DATABASES;"

# Reset database volume (WARNING: Deletes all data)
docker-compose down
docker volume rm robot-live-console-v2_mysql_data
docker-compose up -d
```

#### Port Conflicts
```bash
# Check what's using ports
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :8000

# Update port mappings in docker-compose.yml if needed
```

#### Permission Issues
```bash
# Fix data directory permissions
sudo chown -R $(id -u):$(id -g) ./data
sudo chown -R 999:999 ./data/mysql
sudo chown -R 1001:1001 ./data/theia
```

### Log Analysis
```bash
# All service logs
docker-compose logs

# Specific service logs  
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mysql
docker-compose logs theia

# Follow logs in real-time
docker-compose logs -f backend
```

### Performance Monitoring
```bash
# Resource usage
docker stats

# Container processes
docker-compose top

# Disk usage
du -sh ./data/*
```

## Development vs Production

### Development Mode
- Uses docker-compose.yml only
- Debug logging enabled
- Hot reloading for frontend
- Less strict security settings

### Production Mode  
- Uses docker-compose.yml + docker-compose.prod.yml
- Optimized for performance
- Production logging
- Security hardening
- Proper volume mounts to `/opt/robot-console`

## Backup and Recovery

### Automated Backup Script
```bash
#!/bin/bash
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup database
docker exec robot-console-mysql mysqldump -u robot_console -p$MYSQL_PASSWORD robot_console > "$BACKUP_DIR/database.sql"

# Backup application data
tar -czf "$BACKUP_DIR/app_data.tar.gz" ./data ./projects

echo "Backup completed: $BACKUP_DIR"
```

### Recovery
```bash
# Restore database
docker exec -i robot-console-mysql mysql -u robot_console -p robot_console < backup/database.sql

# Restore application data
tar -xzf backup/app_data.tar.gz
```

## Integration with Existing Services

### With Existing MySQL
If you have an existing MySQL server:

1. Comment out the `mysql` service in docker-compose.yml
2. Update environment variables to point to your MySQL server:
```bash
MYSQL_HOST=your-mysql-server
MYSQL_PORT=3306
```

### With Existing Nginx
If you have Nginx already running:

1. Change frontend port mapping in docker-compose.yml:
```yaml
ports:
  - "8080:80"  # Use different port
```

2. Configure your Nginx to proxy to port 8080

## Security Considerations

- Change all default passwords
- Use strong JWT secret keys
- Configure proper CORS origins
- Keep Docker images updated
- Use reverse proxy with SSL
- Implement proper firewall rules
- Regular security updates

## Support

For issues and questions:
1. Check this documentation
2. Run `./docker-health-check.sh`
3. Check Docker logs: `docker-compose logs`
4. Review the main [DEPLOYMENT.md](./DEPLOYMENT.md)
5. Check [VPS_DEPLOYMENT_CHECKLIST.md](./VPS_DEPLOYMENT_CHECKLIST.md) for production deployment