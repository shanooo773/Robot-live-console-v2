# WebRTC Streaming System Refactor Guide

## Overview

This document describes the refactoring of the WebRTC streaming system from a backend-mediated approach to a direct frontend-robot connection architecture.

## Architecture Changes

### Old Architecture (Backend-Mediated)
```
Robot → RTSP Stream → Backend (RTSP→WebRTC conversion) → Frontend
```

**Issues:**
- Backend becomes a bottleneck for video traffic
- Requires complex RTSP to WebRTC conversion
- High resource usage on backend server
- Latency introduced by conversion process
- Scaling issues with multiple robots

### New Architecture (Direct Connection)
```
Robot (WebRTC Server) ↔ Frontend (Direct WebRTC)
Backend: Metadata + Auth only
```

**Benefits:**
- No video traffic through backend (reduced bandwidth/CPU)
- Lower latency direct robot connection
- Better scalability 
- Simplified backend architecture
- Native WebRTC end-to-end

## Implementation Changes

### Backend Changes

#### 1. Database Schema Updates
- Added `webrtc_url` field to robots table
- Migration support for existing installations

```sql
ALTER TABLE robots ADD COLUMN webrtc_url VARCHAR(500);
```

#### 2. API Model Updates
Updated robot models to include `webrtc_url`:

```python
class RobotCreate(BaseModel):
    name: str
    type: str
    rtsp_url: Optional[str] = None
    webrtc_url: Optional[str] = None  # NEW
    code_api_url: Optional[str] = None
    status: str = 'active'
```

#### 3. WebRTC Endpoint Simplification
- `POST /webrtc/offer` now returns robot WebRTC URL instead of processing offer
- Deprecated `GET /webrtc/answer` and `POST /webrtc/ice-candidate`
- Kept `GET /webrtc/config` for STUN/TURN server configuration

**Before:**
```python
# Complex RTSP to WebRTC conversion
rtsp_player = await get_or_create_rtsp_player(robot_id)
video_track = media_relay.subscribe(rtsp_player.video)
pc.addTrack(video_track)
```

**After:**
```python
# Simple URL return
return {
    "robot_id": robot_id,
    "webrtc_url": robot.webrtc_url,
    "message": "Connect directly to robot WebRTC server"
}
```

### Frontend Changes

#### 1. API Layer Updates
New direct robot connection functions:

```javascript
// Get robot WebRTC URL from backend (with auth validation)
export const getRobotWebRTCUrl = async (robotType, token) => {
  const response = await API.post("/webrtc/offer", {
    robot_type: robotType,
    sdp: "dummy",
    type: "offer"
  }, {
    headers: { Authorization: `Bearer ${token}` }
  });
  return response.data;
};

// Send offer directly to robot
export const sendOfferToRobot = async (webrtcUrl, offer) => {
  const response = await fetch(`${webrtcUrl}/offer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sdp: offer.sdp, type: offer.type })
  });
  return await response.json();
};
```

#### 2. WebRTC Connection Logic
Updated RTSPVideoPlayer component:

**Before:**
```javascript
// Complex backend signaling with socket.io fallback
const offerResponse = await sendWebRTCOffer(robotType, offer.sdp, authToken);
await peerConnection.setRemoteDescription({
  sdp: offerResponse.sdp,
  type: offerResponse.type
});
startICECandidatePolling(offerResponse.peer_id);
```

**After:**
```javascript
// Direct robot connection
const robotInfo = await getRobotWebRTCUrl(robotType, authToken);
const answerResponse = await sendOfferToRobot(robotInfo.webrtc_url, offer);
await peerConnection.setRemoteDescription({
  sdp: answerResponse.sdp,
  type: answerResponse.type
});
```

### Robot-Side WebRTC Server

#### 1. New Component: robot_webrtc_server.py
Created a complete WebRTC signaling server for robots:

```python
from aiortc import RTCPeerConnection, VideoStreamTrack
from aiohttp import web
import cv2

class CameraStream(VideoStreamTrack):
    def __init__(self, camera_id=0):
        super().__init__()
        self.cap = cv2.VideoCapture(camera_id)
    
    async def recv(self):
        # Capture and return video frames
        pass

class RobotWebRTCServer:
    async def offer_handler(self, request):
        # Handle SDP offers from frontend
        pass
    
    async def ice_candidate_handler(self, request):
        # Handle ICE candidates from frontend  
        pass
```

#### 2. Key Features
- **Camera Integration**: OpenCV-based camera capture with fallback dummy stream
- **HTTP Signaling**: Simple REST API for WebRTC signaling
- **CORS Support**: Cross-origin requests from frontend
- **Error Handling**: Graceful degradation for missing hardware

#### 3. API Endpoints
- `POST /offer` - Accept SDP offers from frontend
- `POST /ice-candidate` - Accept ICE candidates from frontend
- `GET /status` - Server health and connection status

## Migration Guide

### For Existing Installations

#### 1. Database Migration
Run this SQL to add the new webrtc_url field:

```sql
ALTER TABLE robots ADD COLUMN webrtc_url VARCHAR(500);
```

#### 2. Robot Configuration
For each robot, set the webrtc_url:

```sql
UPDATE robots SET webrtc_url = 'http://robot-ip:8080' WHERE id = 1;
```

#### 3. Robot Setup
1. Copy `robot_webrtc_server.py` to each robot
2. Install dependencies: `pip install -r robot_requirements.txt`
3. Run server: `python robot_webrtc_server.py --port 8080`

### For New Installations

#### 1. Admin Dashboard
Use the admin interface to create robots with webrtc_url:

```json
{
  "name": "Lab Robot 1",
  "type": "turtlebot",
  "webrtc_url": "http://192.168.1.100:8080",
  "status": "active"
}
```

#### 2. Robot Deployment
Deploy the WebRTC server on each robot and configure the URL in the admin dashboard.

## Testing

### 1. Robot Server Test
```bash
python test_robot_webrtc.py --basic
```

### 2. Full Integration Test
1. Start robot WebRTC server: `python robot_webrtc_server.py --port 8080`
2. Configure robot in admin dashboard with `webrtc_url: "http://localhost:8080"`
3. Create booking for robot
4. Connect from frontend - should stream directly from robot

## Configuration Examples

### Robot WebRTC Server Configuration
```python
# Start server on custom port with specific camera
python robot_webrtc_server.py --port 8081 --camera 1 --verbose
```

### Admin Dashboard Robot Entry
```json
{
  "name": "Mobile Robot Alpha",
  "type": "turtlebot",
  "rtsp_url": "rtmp://robot-alpha:1935/live/stream",  // Legacy, still supported
  "webrtc_url": "http://robot-alpha:8080",           // New direct connection
  "code_api_url": "http://robot-alpha:9000",
  "status": "active"
}
```

### Frontend Connection Flow
```javascript
// 1. Get robot WebRTC URL (with auth/booking validation)
const robotInfo = await getRobotWebRTCUrl('turtlebot', authToken);

// 2. Connect directly to robot
const peerConnection = new RTCPeerConnection(rtcConfig);
const offer = await peerConnection.createOffer();
const answer = await sendOfferToRobot(robotInfo.webrtc_url, offer);

// 3. Complete WebRTC handshake
await peerConnection.setRemoteDescription(answer);
```

## Backward Compatibility

### Legacy Endpoint Support
Old endpoints return deprecation messages:
- `GET /webrtc/answer` → 410 Gone with migration message
- `POST /webrtc/ice-candidate` → 410 Gone with migration message

### Fallback Strategy
If robot webrtc_url is not configured, the system can:
1. Return clear error message to admin
2. Fall back to RTSP streaming (if rtsp_url is available)
3. Display configuration guidance

## Security Considerations

### Authentication Flow
1. Frontend authenticates with backend (JWT)
2. Backend validates booking/session
3. Backend returns robot WebRTC URL (if authorized)
4. Frontend connects directly to robot (no auth needed - trusted network)

### Network Security
- Robots should be on trusted internal network
- WebRTC server only accepts connections from authorized frontend origins
- CORS properly configured for security

## Performance Benefits

### Reduced Backend Load
- No video processing/conversion
- No WebRTC peer connection management
- Only metadata and authentication handling

### Lower Latency
- Direct frontend ↔ robot connection
- No intermediate processing steps
- Native WebRTC performance

### Better Scalability
- Each robot handles its own video streaming
- Backend resources scale with users, not video streams
- Horizontal scaling of robot fleet

## Troubleshooting

### Common Issues

#### 1. Robot WebRTC URL Not Configured
**Error**: "Robot does not have a WebRTC URL configured"
**Solution**: Add webrtc_url to robot in admin dashboard

#### 2. Robot Server Not Running
**Error**: "Failed to connect to robot: Connection refused"
**Solution**: Start robot WebRTC server: `python robot_webrtc_server.py`

#### 3. Network Connectivity
**Error**: "Robot may be offline or not configured"
**Solution**: Check robot network connectivity and firewall settings

#### 4. Camera Not Available
**Warning**: "OpenCV not available. Using dummy video stream."
**Solution**: Install OpenCV: `pip install opencv-python` or accept dummy stream for testing

### Debugging Commands

```bash
# Test robot server
python test_robot_webrtc.py --server

# Check robot server status
curl http://robot-ip:8080/status

# Test backend WebRTC config
curl -H "Authorization: Bearer <token>" http://backend/webrtc/config
```

This refactoring provides a more scalable, efficient, and maintainable WebRTC streaming architecture while preserving the existing user experience and booking system.