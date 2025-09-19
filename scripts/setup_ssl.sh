#!/bin/bash

# SSL Setup Script for Robot Console VPS Deployment
# This script helps configure HTTPS with Let's Encrypt SSL certificates

set -e

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

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root or with sudo"
    exit 1
fi

# Get domain name from user
if [ -z "$1" ]; then
    print_error "Usage: sudo ./setup_ssl.sh <your-domain.com>"
    print_status "Example: sudo ./setup_ssl.sh myrobot.example.com"
    exit 1
fi

DOMAIN=$1
EMAIL="admin@$DOMAIN"  # Default email, can be customized

print_status "🔐 Setting up SSL certificate for domain: $DOMAIN"

# Check if domain resolves to this server
print_status "Checking DNS resolution for $DOMAIN..."
SERVER_IP=$(curl -s ifconfig.me)
DOMAIN_IP=$(dig +short $DOMAIN | tail -1)

if [ "$SERVER_IP" != "$DOMAIN_IP" ]; then
    print_warning "Domain $DOMAIN resolves to $DOMAIN_IP, but server IP is $SERVER_IP"
    print_warning "Please ensure DNS is properly configured before continuing"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Exiting. Please configure DNS first."
        exit 1
    fi
fi

# Install certbot if not already installed
if ! command -v certbot >/dev/null 2>&1; then
    print_status "Installing certbot..."
    apt-get update
    apt-get install -y certbot python3-certbot-nginx
    print_success "Certbot installed"
else
    print_success "Certbot already installed"
fi

# Check if nginx is running
if ! systemctl is-active --quiet nginx; then
    print_status "Starting nginx..."
    systemctl start nginx
fi

# Create nginx configuration with HTTPS support
print_status "Creating enhanced nginx configuration with HTTPS support..."

cat > /etc/nginx/sites-available/robot-console << EOF
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name $DOMAIN;
    
    # Allow Let's Encrypt challenges
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
    
    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://\$server_name\$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL certificate paths (will be populated by certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy strict-origin-when-cross-origin;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' ws: wss:; frame-src 'self';";
    
    # Serve React frontend
    location / {
        root /opt/robot-console/frontend/dist;
        try_files \$uri \$uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
    
    # API proxy to backend
    location /api/ {
        rewrite ^/api/(.*) /\$1 break;
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 86400;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        access_log off;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/robot-console /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx configuration
if nginx -t; then
    print_success "Nginx configuration is valid"
    systemctl reload nginx
else
    print_error "Nginx configuration is invalid"
    exit 1
fi

# Obtain SSL certificate
print_status "Obtaining SSL certificate for $DOMAIN..."
if certbot certonly --webroot --webroot-path=/var/www/html -d $DOMAIN --email $EMAIL --agree-tos --non-interactive; then
    print_success "SSL certificate obtained successfully"
else
    print_error "Failed to obtain SSL certificate"
    exit 1
fi

# Reload nginx with SSL configuration
systemctl reload nginx

# Set up automatic renewal
print_status "Setting up automatic certificate renewal..."
cat > /etc/cron.d/certbot << EOF
# Renew Let's Encrypt certificates twice daily
0 */12 * * * root certbot renew --quiet && systemctl reload nginx
EOF

print_success "SSL certificate renewal cron job created"

# Update backend environment for HTTPS
print_status "Updating backend environment for HTTPS..."
BACKEND_ENV="/opt/robot-console/backend/.env"
if [ -f "$BACKEND_ENV" ]; then
    # Update CORS origins to include HTTPS
    sed -i "s|PRODUCTION_CORS_ORIGINS=.*|PRODUCTION_CORS_ORIGINS=https://$DOMAIN,https://www.$DOMAIN|g" "$BACKEND_ENV"
    # Update VPS URL to HTTPS
    sed -i "s|VPS_URL=.*|VPS_URL=https://$DOMAIN|g" "$BACKEND_ENV"
    
    # Restart backend service to apply changes
    systemctl restart robot-console-backend
    print_success "Backend environment updated for HTTPS"
else
    print_warning "Backend .env file not found. Please update CORS origins manually."
fi

# Final verification
print_status "Verifying SSL setup..."
if curl -s -I https://$DOMAIN | grep -q "HTTP/2"; then
    print_success "✅ HTTPS is working with HTTP/2"
else
    print_warning "HTTPS might not be working properly. Check configuration."
fi

print_success "🎉 SSL setup completed successfully!"
echo
print_status "Summary:"
echo "  🔗 HTTP: http://$DOMAIN (redirects to HTTPS)"
echo "  🔒 HTTPS: https://$DOMAIN"
echo "  📱 Frontend: https://$DOMAIN/"
echo "  🔧 Backend API: https://$DOMAIN/api/"
echo "  📊 API Docs: https://$DOMAIN/api/docs"
echo "  💚 Health Check: https://$DOMAIN/health"
echo
print_status "Certificate will auto-renew. Check status with:"
echo "  sudo certbot certificates"
echo "  sudo certbot renew --dry-run"