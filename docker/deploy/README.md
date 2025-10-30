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

Edit `backend/.env` and **add** these variables (they may not exist yet):

```bash
# Required: Secret for bridge-to-backend authorization (ADD THIS)
BRIDGE_CONTROL_SECRET=your-secure-secret-here

# Optional: Backend host configuration (ADD THIS if not present)
BRIDGE_BACKEND_HOST=host.docker.internal  # Mac/Windows
# Or use: 172.17.0.1 (Linux default Docker bridge)
# Or use your host machine's IP address
```

**Note**: `BRIDGE_CONTROL_SECRET` is a new variable required for bridge authorization. Add it to your `backend/.env` file before running docker compose.

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

## Testing the RTSP → WebRTC Flow

### 1. Setup Test Environment

Ensure backend is running locally:

```bash
cd ../../backend
uvicorn main:app --port 8000 --reload
```

### 2. Create Test Robot with RTSP URL

Use curl with admin token to create a test robot:

```bash
# First, login as admin to get token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@robot-console.com", "password": "admin123"}'

# Save the token from response, then create robot
TOKEN="your-token-here"

curl -X POST http://localhost:8000/admin/robots \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test RTSP Camera",
    "type": "turtlebot",
    "rtsp_url": "rtsp://wowzaec2demo.streamlock.net/vod/mp4:BigBuckBunny_115k.mp4",
    "status": "active"
  }'

# Note the robot ID from the response
```

### 3. Test Signaling Info Endpoint (User with Booking)

Test the signaling-info endpoint (requires active booking):

```bash
# Get signaling info for robot ID 1
curl -X GET http://localhost:8000/api/streams/1/signaling-info \
  -H "Authorization: Bearer $TOKEN"

# Expected response:
# {
#   "ws_url": "ws://localhost:8081/ws/stream?robot_id=1"
# }
```

### 4. Test Bridge Authorization (Bridge-Only)

Test the bridge authorize endpoint with secret:

```bash
# Get BRIDGE_CONTROL_SECRET from backend/.env
SECRET=$(grep BRIDGE_CONTROL_SECRET ../../backend/.env | cut -d'=' -f2)

# Call authorize endpoint (only bridge should call this)
curl -X GET "http://localhost:8000/api/streams/bridge/authorize?robot_id=1" \
  -H "X-BRIDGE-SECRET: $SECRET"

# Expected response (bridge-only, contains RTSP URL):
# {
#   "rtsp_url": "rtsp://...",
#   "robot_id": 1,
#   "robot_name": "Test RTSP Camera"
# }
```

### 5. Test from Within Bridge Container

Once docker compose is running:

```bash
# Test backend reachability from bridge
docker compose exec bridge curl http://host.docker.internal:8000/health

# Test authorize endpoint from bridge
docker compose exec bridge sh -c '
  curl -X GET "http://host.docker.internal:8000/api/streams/bridge/authorize?robot_id=1" \
    -H "X-BRIDGE-SECRET: $BRIDGE_CONTROL_SECRET"
'
```

## Verification Script

Run the automated verification script:

```bash
cd ../..
python scripts/verify_streaming_setup.py \
  --backend-url http://localhost:8000 \
  --test-robot-id 1
```

This script checks:
- ✓ All required files exist
- ✓ No legacy stream management code
- ✓ Backend endpoints respond correctly
- ✓ Bridge authorization works (if secret provided)
- ✓ Pytest integration tests pass

## Security Notes

### RTSP URL Security

**CRITICAL**: RTSP URLs must NEVER be exposed to client applications.

- ✅ **Backend** stores RTSP URLs in database (rtsp_url column)
- ✅ **Admin UI** allows admins to configure RTSP URLs
- ✅ **GET /api/streams/{robot_id}** returns metadata but NOT rtsp_url
- ✅ **GET /api/streams/{robot_id}/signaling-info** returns ws_url but NOT rtsp_url
- ✅ **GET /api/streams/bridge/authorize** returns rtsp_url ONLY to bridge with X-BRIDGE-SECRET
- ✅ **Bridge** obtains RTSP URL via authorize endpoint and does NOT log it
- ❌ **Client applications** NEVER receive RTSP URLs

### Bridge Authorization Flow

1. User with active booking requests stream via frontend
2. Frontend calls GET /api/streams/{robot_id}/signaling-info
3. Backend validates booking and returns ws_url
4. Frontend opens WebSocket to bridge using ws_url
5. Bridge receives connection with robot_id query param
6. Bridge calls GET /api/streams/bridge/authorize?robot_id={robot_id} with X-BRIDGE-SECRET header
7. Backend verifies secret and returns rtsp_url to bridge
8. Bridge creates GStreamer pipeline and forwards stream to frontend

## Common Error Messages

### "Bridge authorization not configured"
- Add BRIDGE_CONTROL_SECRET to backend/.env

### "Access denied. You need an active booking"
- User must have an active booking for the robot
- Create a booking for the robot type or robot_id

### "Robot does not have RTSP URL configured"
- Admin must add rtsp_url field in Robot Registry via admin dashboard

### "bridge_service.py not found"
- Implement services/webrtc-bridge/bridge_service.py with GStreamer pipeline
- See stub file for implementation requirements

## Additional Resources

- GStreamer documentation: https://gstreamer.freedesktop.org/documentation/
- WebRTC integration guide: https://gstreamer.freedesktop.org/documentation/webrtc/
- Docker Compose reference: https://docs.docker.com/compose/
- GStreamer WebRTC demos: https://github.com/centricular/gstwebrtc-demos
