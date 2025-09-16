# VPS Deployment Checklist for Robot Console

## Pre-Deployment Requirements

### System Requirements
- [ ] Ubuntu/Debian VPS with minimum 2GB RAM, 20GB storage
- [ ] Root/sudo access to the VPS
- [ ] Domain name pointed to VPS IP (optional, for HTTPS)
- [ ] Ports 80, 443, and 8000 available and not blocked by firewall

### Software Dependencies
- [ ] Python 3.8+ installed
- [ ] Node.js 16+ and npm installed
- [ ] MySQL 8.0+ server installed and running
- [ ] Nginx installed
- [ ] Git installed

## Backend Configuration Review

### Environment Variables (.env)
- [ ] Copy `.env.template` to `backend/.env`
- [ ] **ENVIRONMENT**: Set to `production`
- [ ] **DATABASE_TYPE**: Set to `mysql` for production
- [ ] **MYSQL_HOST**: Database host (usually `localhost`)
- [ ] **MYSQL_PORT**: Database port (usually `3306`)
- [ ] **MYSQL_USER**: Database username
- [ ] **MYSQL_PASSWORD**: Strong database password
- [ ] **MYSQL_DATABASE**: Database name (`robot_console`)
- [ ] **SECRET_KEY**: Generate strong JWT secret (min 32 characters)
- [ ] **PRODUCTION_CORS_ORIGINS**: Set to your domain(s), e.g., `https://yourdomain.com,http://your-vps-ip`
- [ ] **VPS_URL**: Set to your VPS IP or domain

### Database Setup
- [ ] MySQL server is running: `sudo systemctl status mysql`
- [ ] Database and user created: `sudo ./setup_mysql.sh`
- [ ] Database connection tested: `python test_database.py`
- [ ] Database tables initialized successfully

### Backend Dependencies
- [ ] Python virtual environment created in `/opt/robot-console/backend/venv`
- [ ] All requirements installed: `pip install -r requirements.txt`
- [ ] Gunicorn installed for production serving
- [ ] Dependencies tested: Try importing main modules

### Logging Configuration
- [ ] Logs directory exists: `/opt/robot-console/backend/logs/`
- [ ] Log directory permissions set: `chmod 775 /opt/robot-console/backend/logs/`
- [ ] Log rotation configured (optional): Setup logrotate for `backend.log`

### Error Handling
- [ ] Global exception handlers configured in FastAPI
- [ ] Database connection errors handled gracefully
- [ ] Service unavailability handled in endpoints
- [ ] Health check endpoint responds correctly: `curl http://localhost:8000/health`

## Frontend Configuration Review

### Build Optimization
- [ ] Production build configured in `vite.config.js`
- [ ] Bundle size optimizations enabled (code splitting)
- [ ] Source maps disabled for production
- [ ] Static assets optimization configured

### Environment Variables
- [ ] Production environment file created: `frontend/.env.production`
- [ ] **VITE_API_URL**: Set to `/api` (proxied through nginx)
- [ ] Build tested: `npm run build` completes successfully
- [ ] Built files exist in `frontend/dist/`

### Frontend Build Process
- [ ] Dependencies installed: `npm install` (no critical vulnerabilities)
- [ ] Production build completes without errors
- [ ] Bundle size warnings addressed (chunks under 1MB)
- [ ] Static assets properly generated

## Systemd Service Configuration

### Backend Service
- [ ] Service file configured: `/etc/systemd/system/robot-console-backend.service`
- [ ] User and group set to `robot-console`
- [ ] Working directory: `/opt/robot-console/backend`
- [ ] Environment path configured
- [ ] Gunicorn command with proper settings
- [ ] Restart policy: `always` with 10-second delay
- [ ] Security restrictions enabled (`NoNewPrivileges`, `PrivateTmp`)
- [ ] Logging configured: `StandardOutput=journal`

### Service Management
- [ ] Service file reloaded: `sudo systemctl daemon-reload`
- [ ] Service enabled: `sudo systemctl enable robot-console-backend`
- [ ] Service starts successfully: `sudo systemctl start robot-console-backend`
- [ ] Service status healthy: `sudo systemctl status robot-console-backend`
- [ ] Service logs accessible: `sudo journalctl -u robot-console-backend -f`

## Nginx Configuration

### Basic Configuration
- [ ] Nginx configuration file: `/etc/nginx/sites-available/robot-console`
- [ ] Site enabled: `sudo ln -sf /etc/nginx/sites-available/robot-console /etc/nginx/sites-enabled/`
- [ ] Default site disabled: `sudo rm -f /etc/nginx/sites-enabled/default`
- [ ] Configuration syntax valid: `sudo nginx -t`

### Security Headers
- [ ] X-Content-Type-Options: nosniff
- [ ] X-Frame-Options: DENY
- [ ] X-XSS-Protection: enabled
- [ ] Referrer-Policy: strict-origin-when-cross-origin
- [ ] Content-Security-Policy configured (for HTTPS)

### Performance Optimization
- [ ] Static asset caching configured (1 year for JS/CSS/images)
- [ ] Gzip compression enabled
- [ ] HTTP/2 enabled (for HTTPS)
- [ ] Proxy timeouts configured for WebSocket support

### Reverse Proxy Setup
- [ ] Frontend served from `/opt/robot-console/frontend/dist`
- [ ] API requests proxied from `/api/` to `http://localhost:8000`
- [ ] Health check endpoint accessible: `/health`
- [ ] WebSocket upgrade headers configured
- [ ] Proper forwarded headers set

## HTTPS and SSL Configuration

### SSL Certificate (Production)
- [ ] Domain DNS properly configured
- [ ] Certbot installed: `sudo apt install certbot python3-certbot-nginx`
- [ ] SSL certificate obtained: `sudo certbot --nginx -d yourdomain.com`
- [ ] Certificate auto-renewal configured: `sudo crontab -e`
- [ ] HTTPS redirect enabled in nginx configuration

### Security Configuration
- [ ] Strong SSL ciphers configured
- [ ] TLS 1.2+ only enabled
- [ ] HSTS header configured
- [ ] Secure session configuration
- [ ] SSL certificate valid and not expired

## Deployment Process

### File Permissions and Ownership
- [ ] Project directory: `/opt/robot-console/` owned by `robot-console:robot-console`
- [ ] Backend directory permissions: `755`
- [ ] Logs directory permissions: `775`
- [ ] Videos directory permissions: `775`
- [ ] Environment file permissions: `644` (readable by service user)

### Service User Setup
- [ ] System user created: `robot-console`
- [ ] User shell set to `/bin/false` for security
- [ ] User home directory: `/opt/robot-console`
- [ ] User has access to required directories only

### Deployment Script Execution
- [ ] VPS deployment script permissions: `chmod +x deploy_vps.sh`
- [ ] Script executed with sudo: `sudo ./deploy_vps.sh`
- [ ] All deployment steps completed successfully
- [ ] No critical errors in deployment logs

## Post-Deployment Verification

### Health Checks
- [ ] Backend health check: `curl http://localhost:8000/health`
- [ ] Frontend accessibility: `curl http://localhost/`
- [ ] API documentation: `curl http://localhost:8000/docs`
- [ ] Database connectivity confirmed through health endpoint
- [ ] All services status: "healthy" in health check response

### Functional Testing
- [ ] Frontend loads in browser without console errors
- [ ] User registration and login functional
- [ ] API endpoints respond correctly
- [ ] Video streaming works (if videos are uploaded)
- [ ] WebSocket connections work (if applicable)
- [ ] Container management functional (if using Docker)

### Performance Verification
- [ ] Frontend loads in under 3 seconds
- [ ] API response times under 500ms for most endpoints
- [ ] No memory leaks in backend service
- [ ] CPU usage reasonable under normal load
- [ ] Log file sizes manageable

### Security Verification
- [ ] Sensitive files not world-readable: `ls -la /opt/robot-console/backend/.env`
- [ ] Service runs as non-root user
- [ ] Firewall configured: `sudo ufw status`
- [ ] Only necessary ports open (80, 443, 22)
- [ ] No debug mode enabled in production

## Monitoring and Maintenance

### Log Monitoring
- [ ] Backend logs: `sudo tail -f /opt/robot-console/backend/logs/backend.log`
- [ ] Service logs: `sudo journalctl -u robot-console-backend -f`
- [ ] Nginx access logs: `sudo tail -f /var/log/nginx/access.log`
- [ ] Nginx error logs: `sudo tail -f /var/log/nginx/error.log`

### Service Management Commands
```bash
# Check service status
sudo systemctl status robot-console-backend

# Restart service
sudo systemctl restart robot-console-backend

# Stop service
sudo systemctl stop robot-console-backend

# View logs
sudo journalctl -u robot-console-backend -f

# Check nginx status
sudo systemctl status nginx

# Reload nginx configuration
sudo nginx -s reload
```

### Backup Procedures
- [ ] Database backup script configured
- [ ] Regular backups scheduled with cron
- [ ] Project files backup procedure documented
- [ ] SSL certificates backup procedure documented

### Update Procedures
- [ ] Application update procedure documented
- [ ] Database migration procedure tested
- [ ] Rollback procedure documented
- [ ] Zero-downtime deployment configured (optional)

## Troubleshooting Common Issues

### Backend Won't Start
1. Check MySQL service: `sudo systemctl status mysql`
2. Verify database connection: `python test_database.py`
3. Check .env file permissions and content
4. Review service logs: `sudo journalctl -u robot-console-backend`
5. Test manual startup: `cd /opt/robot-console/backend && source venv/bin/activate && python main.py`

### Frontend Not Loading
1. Check nginx configuration: `sudo nginx -t`
2. Verify frontend build exists: `ls -la /opt/robot-console/frontend/dist/`
3. Check nginx logs: `sudo tail -f /var/log/nginx/error.log`
4. Verify file permissions on dist directory

### CORS Issues
1. Verify PRODUCTION_CORS_ORIGINS in .env includes your domain
2. Check that ENVIRONMENT=production in .env
3. Restart backend service after .env changes
4. Test with browser developer tools

### SSL Certificate Issues
1. Verify domain DNS points to VPS IP
2. Check certificate expiry: `sudo certbot certificates`
3. Renew certificate: `sudo certbot renew`
4. Restart nginx: `sudo systemctl restart nginx`

## Security Considerations

### Database Security
- [ ] MySQL root password is strong and secured
- [ ] Application database user has minimal required privileges
- [ ] Database server only listens on localhost (unless clustering)
- [ ] Regular security updates applied

### Application Security
- [ ] JWT secret key is strong (32+ characters, random)
- [ ] Environment variables not exposed in process lists
- [ ] File upload restrictions in place
- [ ] Input validation implemented
- [ ] Rate limiting configured (optional)

### System Security
- [ ] VPS keeps OS packages updated
- [ ] SSH key authentication enabled (password auth disabled)
- [ ] Fail2ban configured for brute force protection
- [ ] Regular security monitoring in place
- [ ] Automated security updates configured

## Documentation Links

- [Backend Configuration Guide](./backend/README.md)
- [Frontend Configuration Guide](./frontend/README.md)
- [Database Setup Guide](./DEPLOYMENT.md)
- [Video Endpoint Configuration](./VIDEO_ENDPOINT_FIX.md)
- [Service Architecture](./other-docs/SERVICE_ARCHITECTURE.md)

---

**Note**: This checklist ensures a production-ready deployment. Skip HTTPS configuration for initial testing, but implement it before going live with real users.