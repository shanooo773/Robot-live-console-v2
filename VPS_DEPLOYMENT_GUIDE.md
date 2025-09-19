# 🚀 VPS Deployment Guide for Robot Live Console

This guide explains how to properly deploy the Robot Live Console application on a VPS with the correct IP configuration.

## 📋 Quick Start

### Option 1: Automatic VPS Deployment (Recommended)

```bash
# Clone the repository on your VPS
git clone <repository-url>
cd Robot-live-console-v2

# Run the VPS deployment script (auto-detects IP)
sudo ./deploy_vps.sh

# Or specify your VPS IP explicitly
sudo ./deploy_vps.sh --vps-ip 172.232.105.47
```

### Option 2: Manual Configuration + Deployment

```bash
# 1. Update VPS IP configuration across all files
./update_vps_ip.sh 172.232.105.47

# 2. Deploy using the regular deployment script
./scripts/deploy.sh --production --vps-ip 172.232.105.47
```

## 🔧 What the Scripts Do

### `deploy_vps.sh` - Full VPS Deployment
- **Auto-detects** your VPS IP address or accepts `--vps-ip` parameter
- Sets up **systemd services** for production
- Configures **nginx** as reverse proxy
- Updates all configuration files with correct VPS IP
- Validates external access

### `update_vps_ip.sh` - Configuration Update Only
- Updates VPS IP in all configuration files:
  - `frontend/src/api.js` - Frontend API endpoint
  - `.env.template` - Environment template
  - `backend/.env` - Backend environment
  - `backend/main.py` - Backend fallback configuration

### `scripts/deploy.sh` - Enhanced Standard Deployment
- Now supports `--vps-ip` parameter
- Updates environment files during deployment
- Configures frontend with correct API endpoints

## 📁 Files Modified by VPS Configuration

| File | Purpose | What Gets Updated |
|------|---------|-------------------|
| `frontend/src/api.js` | Frontend API calls | Development fallback URL |
| `.env.template` | Environment template | VPS_URL and CORS origins |
| `backend/.env` | Backend environment | VPS_URL and CORS settings |
| `backend/main.py` | Backend fallback | Default VPS URL fallback |

## 🌐 Network Configuration

### Required Ports
- **Port 80**: HTTP (nginx reverse proxy)
- **Port 8000**: Backend API (internal)
- **Port 443**: HTTPS (if SSL configured)

### Firewall Settings
```bash
# Allow HTTP and HTTPS traffic
sudo ufw allow 80
sudo ufw allow 443

# Backend port should only be accessible locally
# (nginx will proxy to it)
```

## 🔍 Troubleshooting

### Problem: "No result in output"

**Possible Causes:**
1. **Frontend can't connect to backend** - Check API URL configuration
2. **CORS issues** - Verify CORS origins include your VPS IP
3. **Firewall blocking** - Ensure ports 80/443 are open
4. **Service not running** - Check systemd service status

**Debugging Steps:**

1. **Check service status:**
```bash
sudo systemctl status robot-console-backend
sudo systemctl status nginx
```

2. **Check logs:**
```bash
sudo journalctl -u robot-console-backend -f
sudo tail -f /var/log/nginx/error.log
```

3. **Verify configuration:**
```bash
# Check backend is responding
curl http://localhost:8000/health

# Check frontend configuration
grep -n "VITE_API_URL\|return.*http" frontend/src/api.js

# Check backend CORS settings
grep -n "CORS\|VPS_URL" backend/.env
```

4. **Test connectivity:**
```bash
# From inside VPS
curl http://172.232.105.47/
curl http://172.232.105.47:8000/health

# From outside (replace with your VPS IP)
curl http://172.232.105.47/
```

### Problem: API calls failing

**Solution:**
```bash
# Update VPS IP configuration
./update_vps_ip.sh YOUR_VPS_IP

# Restart services
sudo systemctl restart robot-console-backend
sudo systemctl restart nginx
```

### Problem: CORS errors in browser console

**Solution:**
```bash
# Check backend CORS configuration
cat backend/.env | grep CORS

# Should include your VPS IP like:
# CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://172.232.105.47,http://172.232.105.47:3000,http://172.232.105.47:5173
```

## 📊 Health Checks

### Automatic Health Checks
The deployment script includes automatic health checks:
- ✅ Backend health endpoint (`/health`)
- ✅ Frontend accessibility
- ✅ External VPS IP access

### Manual Health Checks
```bash
# Check if all services are running
sudo systemctl status robot-console-backend nginx

# Test endpoints
curl http://localhost:8000/health          # Backend health
curl http://localhost/                     # Frontend
curl http://YOUR_VPS_IP/                   # External access
```

## 🔄 Re-deployment

### If you change VPS IP:
```bash
# Method 1: Use update script + restart
./update_vps_ip.sh NEW_VPS_IP
sudo systemctl restart robot-console-backend nginx

# Method 2: Full re-deployment
sudo ./deploy_vps.sh --vps-ip NEW_VPS_IP
```

### If you update code:
```bash
# Pull latest changes
git pull

# Re-run VPS deployment
sudo ./deploy_vps.sh --vps-ip YOUR_VPS_IP
```

## 📞 Support

If you're still experiencing issues after following this guide:

1. **Check all configuration files** have the correct VPS IP
2. **Verify firewall settings** allow HTTP/HTTPS traffic
3. **Check service logs** for specific error messages
4. **Test each component** individually (backend, frontend, nginx)

The deployment scripts now include comprehensive error checking and will provide detailed feedback about any issues encountered.