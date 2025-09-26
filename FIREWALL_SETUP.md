# 🔥 Firewall Configuration for Theia Container System

## Overview

The Robot Live Console v2 uses dynamic port allocation for Theia containers in the range 4000-9000. This document provides the necessary firewall configuration to ensure proper functionality.

## Required Port Ranges

### Core Application Ports
```bash
# Backend API
8000/tcp

# Frontend (development)
3000/tcp
5173/tcp

# WebRTC Signaling
8080/tcp

# HTTPS (production)
443/tcp
80/tcp
```

### Theia Container Ports (Dynamic Range)
```bash
# Theia containers use dynamic port allocation
4000-9000/tcp
```

## UFW (Ubuntu Firewall) Configuration

### 1. Allow Core Application Ports
```bash
# Backend API
sudo ufw allow 8000/tcp

# Frontend development ports
sudo ufw allow 3000/tcp
sudo ufw allow 5173/tcp

# WebRTC signaling
sudo ufw allow 8080/tcp

# Production web ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### 2. Allow Theia Dynamic Port Range
```bash
# Allow the full Theia port range
sudo ufw allow 4000:9000/tcp

# Verify the rules
sudo ufw status numbered
```

### 3. Enable Firewall (if not already enabled)
```bash
sudo ufw enable
```

## Iptables Configuration (Alternative)

If you prefer iptables directly:

```bash
# Allow core application ports
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
iptables -A INPUT -p tcp --dport 3000 -j ACCEPT
iptables -A INPUT -p tcp --dport 5173 -j ACCEPT
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Allow Theia dynamic port range
iptables -A INPUT -p tcp --dport 4000:9000 -j ACCEPT

# Save rules (Ubuntu/Debian)
iptables-save > /etc/iptables/rules.v4
```

## Port Usage Monitoring

### Check Active Theia Containers
```bash
# List running Theia containers and their ports
docker ps --filter "name=theia-" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

### Check Port Usage
```bash
# Check which ports in the range are in use
netstat -tuln | grep -E ":(400[0-9]|[5-8][0-9]{3}|900[0-9])"

# Or using ss (modern replacement)
ss -tuln | grep -E ":(400[0-9]|[5-8][0-9]{3}|900[0-9])"
```

## Security Considerations

### 1. Source IP Restrictions (Optional)
If you want to restrict access to specific IP ranges:

```bash
# Allow only from specific network (example: 10.0.0.0/8)
sudo ufw allow from 10.0.0.0/8 to any port 4000:9000
```

### 2. Rate Limiting (Recommended)
```bash
# Limit connection attempts to prevent abuse
sudo ufw limit ssh
sudo ufw limit 8000/tcp
```

### 3. Monitoring and Logging
```bash
# Enable UFW logging
sudo ufw logging on

# View firewall logs
sudo tail -f /var/log/ufw.log
```

## Environment-Specific Configuration

### Development Environment
```bash
# More permissive for development
sudo ufw allow 3000:9000/tcp
```

### Production Environment
```bash
# Only allow necessary ports
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 8000/tcp
sudo ufw allow 4000:9000/tcp
```

## Verification

### Test Port Accessibility
```bash
# Test if a specific port is accessible (replace 4001 with actual port)
telnet your-server-ip 4001

# Or using nc (netcat)
nc -zv your-server-ip 4001
```

### Docker Network Verification
```bash
# Ensure Docker containers can access the network
docker network ls
docker network inspect robot-console-network
```

## Troubleshooting

### Common Issues

1. **Container can't bind to port**
   - Check if port is already in use: `netstat -tuln | grep :PORT`
   - Verify firewall allows the port
   - Check Docker daemon is running

2. **Frontend can't connect to Theia**
   - Verify the port mapping in the backend API response
   - Check if the container is actually running
   - Ensure no proxy/load balancer is blocking the connection

3. **Multiple containers conflict**
   - The system uses automatic port allocation to prevent conflicts
   - Check logs: `docker logs theia-<userid>`
   - Verify the port management system is working

### Debug Commands
```bash
# Check container status
curl -H "Authorization: Bearer <token>" http://localhost:8000/theia/status

# List all Theia containers (admin)
curl -H "Authorization: Bearer <admin-token>" http://localhost:8000/theia/containers

# Test port allocation
python3 -c "
import sys
sys.path.append('backend')
from services.theia_service import TheiaContainerManager
manager = TheiaContainerManager()
print(f'Port for user 1: {manager.get_user_port(1)}')
print(f'Port mappings: {manager._port_mappings}')
"
```

## Configuration Files

### Environment Variables
```bash
# Add to .env file
THEIA_BASE_PORT=4000
THEIA_MAX_PORT=9000
THEIA_MAX_CONTAINERS=50
```

### UFW Status Check
```bash
sudo ufw status verbose
```

This should show your configured rules including the 4000:9000/tcp range.