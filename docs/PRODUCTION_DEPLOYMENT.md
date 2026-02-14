# Production Deployment Guide

## Robot Live Console - Complete Production Setup

This guide walks you through deploying the Robot Live Console to a production server with all security and authentication features enabled.

## Prerequisites

- VPS or dedicated server (Ubuntu 20.04+ recommended)
- Domain name with DNS configured  
- SSL certificate (Let's Encrypt recommended)
- MySQL database
- SMTP email service (Gmail with App Password recommended)
- Google OAuth Client ID (for Google login)

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/shanooo773/Robot-live-console-v2.git
cd Robot-live-console-v2

# 2. Configure environment
cp .env.template backend/.env
nano backend/.env  # Update with your values

# 3. Run database migration
mysql -u robot_console -p robot_console_db < migrations/002_production_features.sql

# 4. Create admin account
cd backend && python3 setup_admin.py

# 5. Start services
sudo systemctl start robot-console
```

For detailed instructions, see full guide below.

## Support

For issues: https://github.com/shanooo773/Robot-live-console-v2/issues
