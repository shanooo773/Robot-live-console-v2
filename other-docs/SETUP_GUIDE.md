# 🚀 VNC/NoVNC Gazebo GUI Setup - Complete Solution

## 📋 Quick Start Guide

### Option 1: Fresh Setup (Recommended)
```bash
# Clone and setup
git clone <repository>
cd Robot-live-console

# Copy environment template
cp .env.template .env

# Build and start with fixed configuration
docker compose build --no-cache gazebo
docker compose up -d

# Verify setup
./debug-vnc.sh check

# Access Gazebo GUI via browser
# Open: http://localhost:8080/vnc.html
# Password: gazebo
```

### Option 2: Fix Existing Container
```bash
# Apply fixes to running container
./apply-vnc-fixes.sh apply

# Test the fixes
./apply-vnc-fixes.sh test

# Check status
./apply-vnc-fixes.sh status
```

### Option 3: Manual Configuration
If automatic scripts fail, apply these manual fixes:

#### Step 1: Update Container Packages
```bash
docker compose exec gazebo bash -c "
    apt-get update && apt-get install -y \
        tigervnc-standalone-server \
        openbox \
        dbus-x11 \
        libgl1-mesa-glx \
        websockify
"
```

#### Step 2: Create Fixed VNC Startup Script
```bash
docker compose exec gazebo bash -c "cat > /root/.vnc/xstartup << 'EOF'
#!/bin/bash
set -e
export DISPLAY=:1
source /opt/ros/noetic/setup.bash
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe

# Start GUI components
eval \`dbus-launch --sh-syntax\`
openbox-session &
sleep 3

# Start ROS and Gazebo
roscore &
sleep 5
gazebo --verbose /opt/simulation/robots/worlds/empty.world &

# Keep session alive
wait
EOF"

docker compose exec gazebo chmod +x /root/.vnc/xstartup
```

#### Step 3: Restart VNC Server
```bash
docker compose exec gazebo bash -c "
    vncserver -kill :1 2>/dev/null || true
    vncserver :1 -geometry 1280x720 -depth 24 -SecurityTypes None
    cd /opt/novnc && ./utils/websockify --web . 8080 localhost:5901 &
"
```

## 🔧 Configuration Files

### Enhanced docker-compose.yml
```yaml
services:
  gazebo:
    build:
      context: ./docker
      dockerfile: Dockerfile
    container_name: gazebo-vnc-gui
    ports:
      - "8080:8080"  # NoVNC web interface
      - "5901:5901"  # VNC server
    volumes:
      - ./docker/robots/worlds:/opt/simulation/robots/worlds
      - ./docker/robots:/opt/simulation/robots
      - ./custom_worlds:/opt/simulation/custom_worlds:ro
    environment:
      - DISPLAY=:1
      - VNC_PASSWORD=gazebo
      - LIBGL_ALWAYS_SOFTWARE=1      # Software rendering
      - GALLIUM_DRIVER=llvmpipe       # Mesa driver
    restart: unless-stopped
    shm_size: 1g                     # GUI memory
    security_opt:
      - seccomp:unconfined
    cap_add:
      - SYS_ADMIN
    stdin_open: true
    tty: true
```

### Fixed VNC xstartup Script
```bash
#!/bin/bash
set -e

# Environment setup
export DISPLAY=:1
source /opt/ros/noetic/setup.bash
export ROS_PACKAGE_PATH=/opt/simulation:$ROS_PACKAGE_PATH
export PYTHONPATH=/opt/simulation:$PYTHONPATH

# Software rendering
export LIBGL_ALWAYS_SOFTWARE=1
export GALLIUM_DRIVER=llvmpipe

# Start services
eval `dbus-launch --sh-syntax`
openbox-session &
WM_PID=$!
sleep 3

# ROS and Gazebo
roscore &
ROS_PID=$!
sleep 5

gazebo --verbose /opt/simulation/robots/worlds/empty.world &
GAZEBO_PID=$!

# Cleanup handling
cleanup() {
    kill $GAZEBO_PID $ROS_PID $WM_PID 2>/dev/null || true
    exit 0
}
trap cleanup SIGINT SIGTERM

wait $GAZEBO_PID
```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### Issue: Black Screen in Browser
**Symptoms**: NoVNC loads but shows black screen
**Solution**:
```bash
# Check VNC server
docker compose exec gazebo pgrep -f Xvnc

# Restart VNC if not running
docker compose exec gazebo vncserver -kill :1
docker compose exec gazebo vncserver :1 -geometry 1280x720 -depth 24 -SecurityTypes None
```

#### Issue: Cannot Connect to NoVNC
**Symptoms**: Browser cannot reach http://localhost:8080
**Solution**:
```bash
# Check ports
docker compose ps
netstat -tulpn | grep :8080

# Restart websocket proxy
docker compose exec gazebo pkill websockify
docker compose exec gazebo bash -c "cd /opt/novnc && ./utils/websockify --web . 8080 localhost:5901 &"
```

#### Issue: Gazebo Not Visible
**Symptoms**: VNC works but no Gazebo GUI
**Solution**:
```bash
# Check Gazebo process
docker compose exec gazebo pgrep -f gazebo

# Check display
docker compose exec gazebo bash -c "export DISPLAY=:1; xset q"

# Restart Gazebo manually
docker compose exec gazebo bash -c "
    export DISPLAY=:1
    export LIBGL_ALWAYS_SOFTWARE=1
    gazebo --verbose /opt/simulation/robots/worlds/empty.world
"
```

#### Issue: Slow Performance
**Symptoms**: GUI is very slow or unresponsive
**Solution**:
```bash
# Increase container resources in docker-compose.yml
mem_limit: 4g
shm_size: 2g

# Reduce VNC quality
vncserver :1 -geometry 1024x768 -depth 16

# Check system resources
docker stats gazebo-vnc-gui
```

## 📊 Verification Steps

After setup, verify these work:

1. **Container Status**: `docker compose ps` shows "Up"
2. **VNC Server**: `docker compose exec gazebo pgrep -f Xvnc` returns PID
3. **Port Access**: `nc -z localhost 8080` and `nc -z localhost 5901` succeed
4. **Web Interface**: `curl http://localhost:8080` returns HTML
5. **Gazebo Process**: `docker compose exec gazebo pgrep -f gazebo` returns PID
6. **ROS Topics**: `docker compose exec gazebo rostopic list` shows /gazebo topics

## 🌐 Access Methods

### Browser Access (Primary)
- **URL**: http://localhost:8080/vnc.html
- **Password**: gazebo
- **Features**: Full interaction, no additional software needed

### Direct VNC (Alternative)
- **Address**: localhost:5901
- **Password**: gazebo
- **Client**: Any VNC viewer (RealVNC, TigerVNC, etc.)

## 🔄 Maintenance Commands

```bash
# Check everything
./debug-vnc.sh check

# View logs
docker compose logs gazebo --tail=50

# Restart container
docker compose restart gazebo

# Clean restart
docker compose down && docker compose up -d

# Access container shell
docker compose exec gazebo bash

# Apply fixes to existing container
./apply-vnc-fixes.sh apply
```

## 📈 Performance Tuning

### For Better Performance
```yaml
# docker-compose.yml
services:
  gazebo:
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
    shm_size: 2g
    environment:
      - LIBGL_ALWAYS_SOFTWARE=1
      - MESA_GL_VERSION_OVERRIDE=3.3
```

### For Lower Resource Usage
```bash
# Use lower resolution
vncserver :1 -geometry 1024x768 -depth 16

# Reduce Gazebo quality
gazebo --verbose -g libgazebo_ros_paths_plugin.so /opt/simulation/robots/worlds/empty.world
```

## 🆘 Emergency Recovery

If everything fails:
```bash
# Nuclear option - clean slate
docker compose down
docker system prune -f
docker compose build --no-cache
docker compose up -d

# Wait 30 seconds then test
sleep 30
./debug-vnc.sh check
```

## 📝 Summary

This solution addresses all major VNC/NoVNC issues:
- ✅ Container GUI support with proper dependencies
- ✅ VNC server configuration with correct display
- ✅ NoVNC websocket proxy setup
- ✅ Gazebo GUI rendering with software OpenGL
- ✅ Proper environment variable configuration
- ✅ Error handling and process management
- ✅ Multiple debugging and testing tools
- ✅ Comprehensive troubleshooting guides

The fixes can be applied to existing containers or used to build new ones from scratch.