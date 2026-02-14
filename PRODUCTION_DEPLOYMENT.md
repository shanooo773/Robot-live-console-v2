# Production Deployment Guide

## Overview

This guide covers deploying the Robot Live Console with production-ready authentication to a live server.

## Prerequisites

- Ubuntu/Debian server with root or sudo access
- MySQL 5.7+ or MariaDB 10.3+
- Python 3.8+
- Node.js 16+ (for frontend)
- Domain name (optional but recommended)
- SSL certificate (required for production - use Let's Encrypt)

## Pre-Deployment Checklist

### 1. Environment Configuration

Create a production `.env` file in the `backend` directory:

```bash
cd /path/to/Robot-live-console-v2/backend
cp ../.env.template .env
nano .env
```

**Critical settings to configure:**

```env
# REQUIRED: Generate a strong secret key
# Run: python3 -c "import secrets; print(secrets.token_urlsafe(64))"
JWT_SECRET_KEY=your-very-long-random-secret-key-minimum-64-characters

# REQUIRED: Email configuration for confirmation and password reset
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_FROM=noreply@yourdomain.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

# REQUIRED: Google OAuth Client ID (from Google Cloud Console)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com

# REQUIRED: Server URLs (MUST use HTTPS in production)
SERVER_HOST=https://yourdomain.com/api
FRONTEND_URL=https://yourdomain.com

# REQUIRED: Production mode
ENVIRONMENT=production

# REQUIRED: Production CORS (restrict to your domain only)
PRODUCTION_CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Database credentials
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=robot_console
MYSQL_PASSWORD=your-strong-database-password
MYSQL_DATABASE=robot_console
```

### 2. Database Setup

```bash
# Create database and user
sudo mysql -u root -p

CREATE DATABASE robot_console CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'robot_console'@'localhost' IDENTIFIED BY 'your-strong-database-password';
GRANT ALL PRIVILEGES ON robot_console.* TO 'robot_console'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Run Database Migration

```bash
cd /path/to/Robot-live-console-v2
mysql -u robot_console -p robot_console < migration_production_auth.sql
```

This migration will:
- Activate existing users (one-time transition)
- Remove demo user accounts
- Clean up test data

### 4. Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable "Google+ API"
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Add authorized JavaScript origins:
   - `https://yourdomain.com`
   - `http://localhost:3000` (for development)
6. Add authorized redirect URIs:
   - `https://yourdomain.com`
7. Copy the Client ID to your `.env` file

### 5. Gmail App Password Setup

For email functionality:

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable 2-Factor Authentication
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Generate a new app password for "Mail"
5. Copy the 16-character password to `MAIL_PASSWORD` in `.env`

## Deployment Steps

### 1. Install Dependencies

```bash
cd /path/to/Robot-live-console-v2

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
npm run build
```

### 2. Setup SSL Certificate (Let's Encrypt)

```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 3. Configure Nginx

Create `/etc/nginx/sites-available/robot-console`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend
    location / {
        root /path/to/Robot-live-console-v2/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket support for Theia
    location ~ ^/theia/(\d+)/ {
        proxy_pass http://127.0.0.1:$1;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/robot-console /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 4. Setup Systemd Service

Create `/etc/systemd/system/robot-console-backend.service`:

```ini
[Unit]
Description=Robot Console Backend API
After=network.target mysql.service

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/Robot-live-console-v2/backend
Environment="PATH=/path/to/Robot-live-console-v2/backend/venv/bin"
ExecStart=/path/to/Robot-live-console-v2/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable robot-console-backend
sudo systemctl start robot-console-backend
sudo systemctl status robot-console-backend
```

### 5. Frontend Environment Variables

Create `frontend/.env.production`:

```env
VITE_API_URL=https://yourdomain.com/api
VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
```

Rebuild frontend:

```bash
cd frontend
npm run build
```

## Security Verification

### 1. Test Authentication Flows

#### Email Registration:
1. Navigate to `https://yourdomain.com`
2. Click "Sign Up"
3. Enter name, email, password
4. Verify email received with confirmation link
5. Click confirmation link
6. Log in with credentials

#### Google OAuth:
1. Click "Continue with Google"
2. Select Google account
3. Verify email is verified in Google account
4. Should be automatically logged in

#### Password Reset:
1. Click "Forgot Password?"
2. Enter email address
3. Check email for reset link
4. Click link and set new password
5. Log in with new password

### 2. Security Checks

```bash
# Check that JWT_SECRET_KEY is strong
cd backend
python3 << EOF
import os
from dotenv import load_dotenv
load_dotenv()
secret = os.getenv('JWT_SECRET_KEY')
print(f"Secret length: {len(secret)} chars")
if len(secret) < 64:
    print("⚠️  WARNING: Secret is too short!")
else:
    print("✅ Secret is strong")
EOF

# Verify HTTPS is enforced
curl -I http://yourdomain.com | grep -i location
# Should redirect to HTTPS

# Check CORS configuration
curl -H "Origin: https://malicious.com" -I https://yourdomain.com/api/health
# Should NOT include Access-Control-Allow-Origin for unauthorized origin
```

## Post-Deployment Tasks

### 1. Create Admin Account

```bash
cd backend
source venv/bin/activate
python3 << EOF
from database import DatabaseManager
db = DatabaseManager()
admin = db.create_user(
    name="Admin User",
    email="admin@yourdomain.com",
    password="temporary-password-change-me",
    role="admin"
)
# Activate immediately
db.activate_user_by_email("admin@yourdomain.com")
print(f"Admin created: {admin['email']}")
print("⚠️  Change password immediately after first login!")
EOF
```

### 2. Monitor Logs

```bash
# Backend logs
sudo journalctl -u robot-console-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 3. Setup Log Rotation

Create `/etc/logrotate.d/robot-console`:

```
/path/to/Robot-live-console-v2/backend/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 your-username your-username
    sharedscripts
}
```

## Backup Strategy

### 1. Database Backups

```bash
# Daily backup script
cat > /usr/local/bin/backup-robot-console.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups/robot-console"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
mysqldump -u robot_console -p'your-db-password' robot_console | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: db_$DATE.sql.gz"
EOF

chmod +x /usr/local/bin/backup-robot-console.sh

# Add to crontab
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-robot-console.sh") | crontab -
```

## Monitoring

### Health Check Endpoints

- `GET /api/health` - Overall health
- `GET /api/health/services` - Service status
- `GET /api/auth/me` - Auth check (requires token)

### Key Metrics to Monitor

- Failed login attempts (check logs for "❌ Database authentication failed")
- Email delivery failures (check logs for "❌ Failed to send")
- Token validation errors (check logs for "⚠️ Invalid confirmation token")
- Database connection issues

## Troubleshooting

### Issue: Email not sending

Check:
1. SMTP credentials in `.env`
2. Gmail App Password (not regular password)
3. 2FA enabled on Gmail account
4. Less secure apps disabled (use App Password)

```bash
# Test email from command line
cd backend
source venv/bin/activate
python3 -c "
from services.mail_service import MailService
import asyncio
mail = MailService()
asyncio.run(mail.send_confirmation_email('test@example.com', 'http://test.com', 'Test User'))
"
```

### Issue: Google Sign-In not working

Check:
1. GOOGLE_CLIENT_ID in backend `.env`
2. VITE_GOOGLE_CLIENT_ID in frontend `.env.production`
3. Authorized origins in Google Cloud Console
4. HTTPS is being used (Google requires HTTPS in production)

### Issue: Password reset link expired

- Links expire after 1 hour (configurable in `token_service.py`)
- User must request a new reset link

## Maintenance

### Updating the Application

```bash
cd /path/to/Robot-live-console-v2

# Pull latest changes
git pull origin main

# Update backend
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart robot-console-backend

# Update frontend
cd ../frontend
npm install
npm run build

# Check status
sudo systemctl status robot-console-backend
```

### Rotating JWT Secret

If JWT secret is compromised:

1. Generate new secret: `python3 -c "import secrets; print(secrets.token_urlsafe(64))"`
2. Update `JWT_SECRET_KEY` in `.env`
3. Restart backend: `sudo systemctl restart robot-console-backend`
4. All users will need to log in again (existing tokens become invalid)

## Support

For issues or questions:
- Check logs: `sudo journalctl -u robot-console-backend -n 100`
- Review backend logs: `/path/to/Robot-live-console-v2/backend/logs/backend.log`
- Test endpoints manually with `curl`
