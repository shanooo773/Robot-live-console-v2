# Video Flow Debugging Guide

This guide provides a comprehensive approach to debugging and fixing the video generation and serving flow in the Robot Live Console.

## Overview

The Robot Live Console consists of:
- **Frontend (React)**: Sends code to backend and displays simulation videos
- **Backend (FastAPI)**: Executes code in Docker containers and serves generated videos
- **Docker Simulation**: ROS/Gazebo environment that generates MP4 videos

## Common Issues and Solutions

### 1. Frontend Doesn't Show Video

**Symptoms:**
- Video area shows "Select a robot and run your code to see the simulation"
- Network tab shows 404 errors for video URLs
- Console errors about video loading

**Debugging Steps:**

1. **Check Backend Connection**
   ```bash
   curl http://localhost:8000/status
   ```
   Should return: `{"status": "Backend is running"}`

2. **Verify Video Directory**
   ```bash
   curl http://localhost:8000/videos-debug
   ```
   Check that `videos_directory_exists` is `true` and permissions are correct.

3. **Test Video Generation**
   - Use the frontend debug panel "Run Full Diagnostics"
   - Check that all systems show ✅ status

### 2. Backend Returns Success But Video Not Accessible

**Symptoms:**
- Backend logs show "Execution completed successfully"
- Frontend receives video_url in response
- Video URL returns 404 or file not found

**Debugging Steps:**

1. **Check Video File Existence**
   ```bash
   curl http://localhost:8000/videos-check/{execution_id}
   ```

2. **Verify Static File Serving**
   ```bash
   curl -I http://localhost:8000/videos/{filename}.mp4
   ```
   Should return `200 OK` with `content-type: video/mp4`

3. **Check File Permissions**
   ```bash
   ls -la backend/videos/
   ```

### 3. Docker Container Issues

**Symptoms:**
- Backend logs show Docker connection errors
- Container execution fails
- Video generation times out

**Debugging Steps:**

1. **Check Docker Status**
   ```bash
   curl http://localhost:8000/docker-status
   ```

2. **Verify Docker Image**
   ```bash
   docker images | grep robot-simulation
   ```

3. **Test Container Manually**
   ```bash
   docker run --rm robot-simulation:latest echo "test"
   ```

## Debugging Tools

### Frontend Debug Panel

The application includes a comprehensive debug panel that provides:

- **System Diagnostics**: Real-time status of backend, Docker, and video directory
- **Video Access Testing**: Test specific video files by execution ID
- **Detailed Results**: JSON responses from all debug endpoints

### Backend Debug Endpoints

- `GET /status` - Backend health check
- `GET /docker-status` - Docker connection and container status
- `GET /videos-debug` - Video directory status and file listing
- `GET /videos-check/{execution_id}` - Check specific video file status

## Mock Simulation Mode

When Docker is not available or the simulation image isn't built, the system automatically falls back to mock simulation mode:

- Creates placeholder video files for testing
- Demonstrates the complete flow without requiring Docker
- Shows success messages instead of actual video playback
- Logs clearly indicate when mock mode is active

## Manual Verification Steps

### 1. End-to-End Flow Test

1. Open frontend at `http://localhost:3000`
2. Click "Run Full Diagnostics" - all should be ✅
3. Select a robot type (TurtleBot3, Arm, or Hand)
4. Click "Run Code"
5. Wait for execution to complete
6. Verify success message or video playback

### 2. Direct API Testing

```bash
# Test code execution
curl -X POST http://localhost:8000/run-code \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello Robot!\")",
    "robot_type": "turtlebot"
  }'

# Check returned video URL
curl -I http://localhost:8000/videos/{returned-execution-id}.mp4
```

### 3. Video Directory Verification

```bash
# Check videos directory
ls -la backend/videos/

# Test static file serving
curl -I http://localhost:8000/videos/test.mp4
```

## Troubleshooting Checklist

- [ ] Backend running at http://localhost:8000
- [ ] Frontend accessible at http://localhost:3000
- [ ] Videos directory exists and is writable
- [ ] Docker available (if using real simulation)
- [ ] Static file serving configured correctly
- [ ] CORS headers allow frontend domain
- [ ] Video files have correct MIME type
- [ ] No file permission issues

## Common Fixes

### Fix 1: Videos Directory Missing
```bash
mkdir -p backend/videos
chmod 755 backend/videos
```

### Fix 2: CORS Issues
Add frontend domain to CORS origins in `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Fix 3: Static Files Not Serving
Ensure static files are mounted correctly:
```python
app.mount("/videos", StaticFiles(directory="videos"), name="videos")
```

### Fix 4: Docker Image Missing
Build the simulation image:
```bash
./setup.sh build
```

## Success Indicators

When everything is working correctly:

1. ✅ Backend diagnostics show all systems operational
2. ✅ Frontend can execute code and receive responses
3. ✅ Video URLs are accessible (200 status)
4. ✅ Videos display in frontend or show success message
5. ✅ No errors in browser console or backend logs

## Need Help?

If issues persist after following this guide:

1. Check the browser developer tools console for JavaScript errors
2. Review backend logs for detailed error messages
3. Verify all dependencies are installed correctly
4. Test with a fresh browser session (clear cache)
5. Ensure all required ports are available and not blocked by firewall