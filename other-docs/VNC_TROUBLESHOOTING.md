# VNC/NoVNC Gazebo GUI Troubleshooting Guide

## 🎯 Problem Summary

This guide addresses the common issues preventing Gazebo GUI from working properly with VNC/NoVNC access in Docker containers. Users report seeing black screens, connection failures, or no GUI rendering when accessing Gazebo through a browser.

## 🔍 Root Cause Analysis

### Container Level Issues ❌

1. **Missing GUI Dependencies**: Container lacks essential X11/OpenGL libraries
2. **Incorrect Display Configuration**: DISPLAY environment variable not properly set
3. **No Software Rendering**: Missing Mesa drivers for GPU-less environments
4. **User Permissions**: VNC running as root without proper X11 setup

### VNC/NoVNC Issues ❌

1. **Display Mismatch**: VNC server on :1 but Gazebo trying to use :0
2. **Missing Window Manager**: No desktop environment inside container
3. **WebSocket Proxy Issues**: NoVNC websockify not properly configured
4. **Security Settings**: VNC authentication blocking connections

### Gazebo Rendering Issues ❌

1. **Headless Mode**: Running gzserver instead of full Gazebo GUI
2. **OpenGL Failures**: Hardware acceleration not available in container
3. **ROS Environment**: Missing ROS setup in VNC session

## 🛠️ Comprehensive Solutions

### Solution 1: Enhanced Docker Configuration

The main `docker/Dockerfile` has been updated with the following fixes:

```dockerfile
# Added essential GUI dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    tigervnc-standalone-server \
    tigervnc-xorg-extension \
    websockify \
    openbox \
    dbus-x11 \
    libgl1-mesa-glx \
    libgl1-mesa-dri \
    libglu1-mesa \
    libxrender1 \
    libxext6 \
    mesa-utils \
    && rm -rf /var/lib/apt/lists/*
```

### Solution 2: Improved VNC Startup Script

The VNC xstartup script now includes:

```bash
#!/bin/bash
set -e

# Set display and source environment
export DISPLAY=:1
source /opt/ros/noetic/setup.bash
export ROS_PACKAGE_PATH=/opt/simulation:$ROS_PACKAGE_PATH

# Configure Mesa for software rendering
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe

# Start D-Bus for GUI applications
eval `dbus-launch --sh-syntax`

# Start window manager
openbox-session &
WM_PID=$!
sleep 3

# Start roscore
roscore &
ROS_PID=$!
sleep 5

# Launch Gazebo with GUI
gazebo --verbose /opt/simulation/robots/worlds/empty.world &
GAZEBO_PID=$!

# Proper cleanup and signal handling
cleanup() {
    kill $GAZEBO_PID $ROS_PID $WM_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM
wait $GAZEBO_PID
```

### Solution 3: Enhanced Docker Compose Configuration

Updated `docker-compose.yml` with:

```yaml
services:
  gazebo:
    environment:
      - DISPLAY=:1
      - VNC_PASSWORD=gazebo
      - LIBGL_ALWAYS_SOFTWARE=1    # Software rendering
      - GALLIUM_DRIVER=llvmpipe     # Mesa driver
    shm_size: 1g                   # Increased shared memory
    security_opt:
      - seccomp:unconfined
    cap_add:
      - SYS_ADMIN
```

## 🔧 Quick Fix Application

### For Existing Containers

1. **Generate fix scripts**:
   ```bash
   ./fix-vnc.sh
   ```

2. **Apply to running container**:
   ```bash
   docker compose cp /tmp/xstartup gazebo:/root/.vnc/xstartup
   docker compose cp /tmp/start-vnc-fixed.sh gazebo:/start-vnc-fixed.sh
   docker compose restart gazebo
   ```

### For New Deployments

1. **Build with enhanced configuration**:
   ```bash
   docker compose build --no-cache gazebo
   docker compose up -d
   ```

2. **Verify setup**:
   ```bash
   ./debug-vnc.sh check
   ```

## 🐛 Debugging Tools

### Debug Script Usage

```bash
# Run all diagnostic checks
./debug-vnc.sh check

# Show container logs
./debug-vnc.sh logs

# Test VNC connection
./debug-vnc.sh vnc

# Show troubleshooting steps
./debug-vnc.sh troubleshoot

# Restart and check
./debug-vnc.sh restart
```

### Manual Testing Commands

```bash
# Check VNC server status
docker compose exec gazebo pgrep -f "Xvnc.*:1"

# Test display access
docker compose exec gazebo bash -c "export DISPLAY=:1; xset q"

# Check Gazebo process
docker compose exec gazebo pgrep -f gazebo

# Test NoVNC websocket
curl http://localhost:8080

# Check OpenGL rendering
docker compose exec gazebo bash -c "export DISPLAY=:1; glxinfo | grep rendering"
```

## 🌐 Access Methods

### Browser Access (Recommended)
- **URL**: `http://your-server-ip:8080/vnc.html`
- **Password**: `gazebo`
- **Resolution**: 1280x720 (configurable)

### Direct VNC Access
- **Address**: `your-server-ip:5901`
- **Password**: `gazebo`
- **Protocol**: VNC

## ⚡ Performance Optimization

### Container Resources
```yaml
# In docker-compose.yml
services:
  gazebo:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
    shm_size: 1g
```

### VNC Display Settings
```bash
# Higher resolution (in startup script)
vncserver :1 -geometry 1920x1080 -depth 24

# Lower color depth for speed
vncserver :1 -geometry 1280x720 -depth 16
```

## 🔄 Common Error Resolutions

### Black Screen in NoVNC
**Cause**: VNC server not starting or window manager failure
**Solution**:
```bash
docker compose exec gazebo vncserver -kill :1
docker compose exec gazebo vncserver :1 -geometry 1280x720 -depth 24 -SecurityTypes None
```

### "Cannot Connect" Error
**Cause**: Port not exposed or websocket proxy down
**Solution**:
```bash
# Check port mapping
docker compose ps
# Restart websocket proxy
docker compose exec gazebo pkill websockify
docker compose exec gazebo bash -c "cd /opt/novnc && ./utils/websockify --web . 8080 localhost:5901 &"
```

### Gazebo Not Visible
**Cause**: Gazebo running headless or display misconfigured
**Solution**:
```bash
# Check Gazebo GUI process
docker compose exec gazebo pgrep -f gzclient
# Restart with explicit GUI
docker compose exec gazebo bash -c "export DISPLAY=:1; gazebo --verbose /opt/simulation/robots/worlds/empty.world"
```

### Slow Performance
**Cause**: Insufficient resources or hardware acceleration issues
**Solution**:
- Increase container memory: `mem_limit: 4g`
- Use software rendering: `LIBGL_ALWAYS_SOFTWARE=1`
- Reduce VNC color depth: `-depth 16`

## 🎛️ Configuration Options

### Custom VNC Password
```bash
# Modify docker-compose.yml
environment:
  - VNC_PASSWORD=your_new_password

# Rebuild container
docker compose up -d --build
```

### Custom Display Resolution
```bash
# Edit startup script resolution
vncserver :1 -geometry 1920x1080 -depth 24
```

### Custom Gazebo World
```bash
# Mount custom world
volumes:
  - ./your-worlds:/opt/simulation/custom_worlds

# Update xstartup script
gazebo --verbose /opt/simulation/custom_worlds/your_world.world
```

## 📊 Success Verification

After applying fixes, you should see:

1. ✅ VNC server running on display :1
2. ✅ NoVNC web interface accessible on port 8080
3. ✅ Gazebo GUI visible in browser with world loaded
4. ✅ Interactive GUI with mouse/keyboard control
5. ✅ ROS topics available (rostopic list shows /gazebo topics)

## 🆘 Emergency Recovery

If the container becomes unresponsive:

```bash
# Force restart
docker compose down
docker compose up -d

# Reset VNC completely
docker compose exec gazebo rm -rf /tmp/.X*
docker compose exec gazebo vncserver -kill :1
docker compose restart gazebo

# Check logs for errors
docker compose logs gazebo --tail=50
```

This guide addresses all the failure points mentioned in the original problem statement and provides comprehensive solutions for each layer of the VNC/NoVNC/Gazebo stack.