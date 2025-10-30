# Docker Deployment - Frontend + WebRTC Bridge

This directory contains Docker configurations for running the **frontend** and **real GStreamer WebRTC bridge** in containers.

> **IMPORTANT**: This setup does NOT containerize the backend or editor services. The backend must run separately on the host.

## Prerequisites

### Required
- Docker and Docker Compose installed
- Backend running on host (accessible from containers)
- **`services/webrtc-bridge/bridge_service.py` MUST exist** - this file should implement the GStreamer webrtcbin pipeline
- `backend/.env` file with `BRIDGE_CONTROL_SECRET` configured

### Optional (for hardware acceleration)
- **NVIDIA GPU**: Install `nvidia-docker2` for NVENC hardware encoding
- **Intel/AMD GPU**: Ensure `/dev/dri` is accessible for VAAPI
- **GStreamer plugins**: Pre-installed in bridge container, but host drivers may be needed for hardware acceleration

## Quick Start

### 1. Verify Prerequisites

Ensure the backend is configured and `bridge_service.py` exists:

```bash
# Check if bridge_service.py exists
ls -l ../../services/webrtc-bridge/bridge_service.py

# Verify backend/.env has BRIDGE_CONTROL_SECRET
grep BRIDGE_CONTROL_SECRET ../../backend/.env
```

If `bridge_service.py` doesn't exist, you must implement it first. The compose build will fail without it.

### 2. Configure Environment

Edit `backend/.env` and ensure these variables are set:

```bash
# Required: Secret for bridge-to-backend authorization
BRIDGE_CONTROL_SECRET=your-secure-secret-here

# Optional: Backend host configuration
BRIDGE_BACKEND_HOST=host.docker.internal  # Mac/Windows
# Or use: 172.17.0.1 (Linux default Docker bridge)
# Or use your host machine's IP address
```

### 3. Build and Run

From this directory:

```bash
cd docker/deploy
docker compose up -d --build
```

This will:
- Build the frontend container with Node.js dev server
- Build the bridge container with GStreamer and Python
- Start both services in the background

### 4. Access Services

- **Frontend**: http://localhost:3000
- **Bridge WebSocket**: ws://localhost:8081/ws/stream
- **Backend** (must be running separately on host): http://localhost:8000

## Checking Logs

View logs for each service:

```bash
# Bridge logs
docker compose logs -f bridge

# Frontend logs
docker compose logs -f frontend

# Both services
docker compose logs -f
```

## Stopping Services

```bash
# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v
```

## Troubleshooting

### Bridge fails to start

**Error**: `python3: can't open file '/app/bridge_service.py'`
- **Solution**: The `services/webrtc-bridge/bridge_service.py` file doesn't exist. You must implement this file with the GStreamer webrtcbin pipeline before running the compose.

### Bridge can't connect to backend

**Error**: Connection refused or timeout when bridge tries to authorize
- **Solution**: 
  1. Verify backend is running on host: `curl http://localhost:8000/docs`
  2. Check `BRIDGE_BACKEND_HOST` in compose file or backend/.env
  3. On Linux, try using host network mode (uncomment `network_mode: host` in compose)
  4. Or set `BRIDGE_BACKEND_HOST` to your host IP: `ip addr show docker0`

### Test GStreamer installation

Run inside the bridge container:

```bash
docker compose exec bridge gst-launch-1.0 videotestsrc ! autovideosink
docker compose exec bridge gst-inspect-1.0 webrtcbin
```

### Hardware Acceleration Issues

**NVENC (NVIDIA)**:
1. Install `nvidia-docker2` on host
2. Uncomment `runtime: nvidia` in docker-compose.yml
3. Test: `docker compose exec bridge nvidia-smi`

**VAAPI (Intel/AMD)**:
1. Ensure `/dev/dri` exists on host: `ls -la /dev/dri`
2. Uncomment `devices: - /dev/dri:/dev/dri` in docker-compose.yml
3. Test: `docker compose exec bridge vainfo`

**Software encoding fallback**:
If hardware acceleration isn't available, GStreamer will use software encoders (x264, x265) automatically, but this will increase CPU usage.

## Development Mode

Both frontend and bridge mount source code into containers:
- Frontend: `../../frontend` → `/app/frontend` (hot-reload)
- Bridge: `../../services/webrtc-bridge` → `/app` (restart to apply changes)

After editing bridge code:

```bash
docker compose restart bridge
```

## Architecture Notes

- **Backend is NOT containerized**: Runs separately on host (port 8000)
- **Bridge authorization**: Bridge connects to backend using `BRIDGE_CONTROL_SECRET` via `X-BRIDGE-SECRET` header
- **No mock implementations**: This setup requires a real GStreamer-based `bridge_service.py`
- **Frontend**: React dev server with Vite (hot-reload enabled)
- **Bridge**: Python + GStreamer with WebRTC support

## Production Deployment

For production:
1. Build optimized frontend: `npm run build` and serve with nginx
2. Update `BRIDGE_WS_URL` to match your domain
3. Use proper secrets management (not .env files)
4. Configure SSL/TLS termination
5. Consider deploying backend and bridge on same host to avoid network configuration issues

## Additional Resources

- GStreamer documentation: https://gstreamer.freedesktop.org/documentation/
- WebRTC integration guide: https://gstreamer.freedesktop.org/documentation/webrtc/
- Docker Compose reference: https://docs.docker.com/compose/
