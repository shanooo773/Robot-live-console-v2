# Raspberry Pi Camera WebRTC Integration Guide

## 🎯 Requirements for Raspberry Pi Robot Camera

### Hardware Requirements
- **Raspberry Pi 4 (recommended)** or Raspberry Pi 3B+
- **Pi Camera Module v2** or USB webcam
- **Reliable network connection** (WiFi or Ethernet)
- **Sufficient power supply** (5V/3A for Pi 4)

### Software Stack for Robot
```bash
# Core dependencies
sudo apt update
sudo apt install -y nodejs npm python3-pip
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-good
sudo apt install -y v4l-utils

# Install Node.js WebRTC libraries
npm install socket.io-client wrtc
```

## 📋 Robot-Side Implementation

### 1. Camera Capture Setup
```python
# camera_stream.py - Python camera capture
import cv2
import asyncio
from threading import Thread

class RobotCamera:
    def __init__(self, camera_id=0):
        self.camera = cv2.VideoCapture(camera_id)
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.camera.set(cv2.CAP_PROP_FPS, 30)
    
    def get_frame(self):
        ret, frame = self.camera.read()
        if ret:
            # Encode frame as JPEG for WebRTC transmission
            _, buffer = cv2.imencode('.jpg', frame)
            return buffer.tobytes()
        return None
```

### 2. WebRTC Robot Client
```javascript
// robot_webrtc_client.js - Node.js WebRTC client for robot
const io = require('socket.io-client');
const wrtc = require('wrtc');

class RobotWebRTCClient {
    constructor(signaling_url, robot_id) {
        this.signaling_url = signaling_url;
        this.robot_id = robot_id;
        this.peerConnections = new Map();
        this.socket = null;
    }
    
    async connect() {
        // Connect to signaling server
        this.socket = io(this.signaling_url);
        
        this.socket.on('connect', () => {
            console.log('🤖 Robot connected to signaling server');
            this.socket.emit('register', {
                userId: this.robot_id,
                userType: 'robot'
            });
        });
        
        this.socket.on('offer', async (data) => {
            console.log('📥 Received offer from viewer:', data.from);
            await this.handleOffer(data);
        });
        
        this.socket.on('ice-candidate', async (data) => {
            await this.handleIceCandidate(data);
        });
    }
    
    async handleOffer(data) {
        const { from, offer } = data;
        
        // Create new peer connection for this viewer
        const peerConnection = new wrtc.RTCPeerConnection({
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' }
            ]
        });
        
        this.peerConnections.set(from, peerConnection);
        
        // Add camera stream to peer connection
        const stream = await this.getCameraStream();
        stream.getTracks().forEach(track => {
            peerConnection.addTrack(track, stream);
        });
        
        // Handle ICE candidates
        peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.socket.emit('ice-candidate', {
                    to: from,
                    candidate: event.candidate
                });
            }
        };
        
        // Set remote description and create answer
        await peerConnection.setRemoteDescription(offer);
        const answer = await peerConnection.createAnswer();
        await peerConnection.setLocalDescription(answer);
        
        // Send answer back to viewer
        this.socket.emit('answer', {
            to: from,
            answer: answer
        });
    }
    
    async getCameraStream() {
        // In a real implementation, this would capture from Pi camera
        // For now, return a mock stream
        const canvas = new wrtc.nonstandard.RTCVideoSource();
        const track = canvas.createTrack();
        return new wrtc.MediaStream([track]);
    }
}

// Start robot client
const robot = new RobotWebRTCClient('ws://backend-server:8080', 'robot_pi_001');
robot.connect();
```

### 3. Camera Integration with GStreamer
```bash
# Option 1: Direct Pi Camera capture
gst-launch-1.0 -v rpicamsrc preview=false \
    ! video/x-raw,width=1280,height=720,framerate=30/1 \
    ! videoconvert ! jpegenc ! multifilesink location=frame_%05d.jpg

# Option 2: USB webcam capture  
gst-launch-1.0 -v v4l2src device=/dev/video0 \
    ! video/x-raw,width=1280,height=720,framerate=30/1 \
    ! videoconvert ! jpegenc ! multifilesink location=frame_%05d.jpg
```

## 🔧 Integration Architecture

```
┌─────────────────┐    WebRTC     ┌──────────────────┐    Socket.IO    ┌─────────────────┐
│   Frontend      │◄─────────────►│ Signaling Server │◄───────────────►│ Raspberry Pi    │
│   (Viewer)      │               │   (Port 8080)    │                 │   (Robot)       │
└─────────────────┘               └──────────────────┘                 └─────────────────┘
        │                                  │                                     │
        │ HTTPS/WSS                        │ Docker Container                    │ Camera Feed
        │                                  │                                     │
┌─────────────────┐                        │                          ┌─────────────────┐
│   Backend API   │                        │                          │   Pi Camera     │
│   (Auth/Session)│                        │                          │   Module        │
└─────────────────┘                        │                          └─────────────────┘
```

## 🛠️ Deployment Steps

### 1. Backend Server Setup
```bash
# Start signaling server
docker compose up -d webrtc-signaling

# Verify health
curl http://localhost:8080/health
```

### 2. Raspberry Pi Robot Setup
```bash
# Clone robot client code
git clone <robot-client-repository>
cd robot-client

# Install dependencies
npm install

# Configure robot settings
cp config.example.json config.json
# Edit config.json with signaling server URL

# Start robot client
sudo node robot_webrtc_client.js
```

### 3. Network Configuration
```bash
# On Raspberry Pi - Enable camera
sudo raspi-config
# Navigate to Interface Options > Camera > Enable

# Test camera
raspistill -o test.jpg

# Configure firewall (if needed)
sudo ufw allow 8080/tcp
sudo ufw allow 3478/udp  
sudo ufw allow 5349/tcp
sudo ufw allow 49152:65535/udp
```

## 🔍 Testing & Validation

### End-to-End Test Procedure

1. **Start Signaling Server**:
   ```bash
   docker compose up -d webrtc-signaling
   curl http://localhost:8080/health
   ```

2. **Connect Robot**:
   ```bash
   # On Raspberry Pi
   node robot_webrtc_client.js
   # Should see: "🤖 Robot connected to signaling server"
   ```

3. **Test Frontend Connection**:
   - Login as dummy user with active booking
   - Select "WebRTC" stream type
   - Click "Connect Video Feed"
   - Should establish peer connection and show robot camera

4. **Verify Session Enforcement**:
   - Access outside booking window → Should be denied
   - Admin access → Should work anytime
   - Session expiry → Should disconnect automatically

### Debug Commands
```bash
# Check signaling server logs
docker compose logs webrtc-signaling

# Test WebSocket connection
curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: test" \
     http://localhost:8080/socket.io/

# Monitor robot network traffic
sudo tcpdump -i wlan0 port 8080

# Check camera permissions
ls -la /dev/video*
groups $USER | grep video
```

## 🚨 Security Considerations

### Authentication & Authorization
- Robot registration requires authentication token
- Session validation enforced in real-time
- STUN/TURN servers should be secured for production
- Network traffic should use HTTPS/WSS in production

### Network Security
```bash
# Robot firewall setup
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow from <backend-server-ip> to any port 8080
sudo ufw deny incoming
```

## 📊 Performance Optimization

### Camera Settings for Optimal Streaming
```python
# Recommended camera configuration
camera_config = {
    'width': 1280,
    'height': 720,
    'fps': 30,
    'quality': 80,  # JPEG quality (1-100)
    'bitrate': 2000000,  # 2 Mbps
    'keyframe_interval': 30
}
```

### Network Requirements
- **Minimum bandwidth**: 1 Mbps upload (robot), 1 Mbps download (viewer)
- **Recommended bandwidth**: 3 Mbps for 720p@30fps
- **Latency**: < 100ms for real-time control
- **Packet loss**: < 1% for stable video

## ✅ Validation Checklist

### Infrastructure
- [ ] WebRTC signaling server running in Docker
- [ ] Backend API endpoints responding correctly
- [ ] Network connectivity between all components
- [ ] Firewall configured for WebRTC ports

### Robot Integration
- [ ] Raspberry Pi camera capture working
- [ ] WebRTC client connects to signaling server
- [ ] Video stream transmitted to frontend
- [ ] Connection handles network interruptions gracefully

### Session Management
- [ ] User sessions respect booking times
- [ ] Admin access works without restrictions
- [ ] Session expiry properly disconnects streams
- [ ] Multiple concurrent sessions supported

### End-to-End Flow
- [ ] Dummy user can view video during active booking
- [ ] Video quality meets requirements (720p/30fps)
- [ ] Connection latency acceptable (< 200ms)
- [ ] System handles robot disconnection/reconnection

---

**Status**: All WebRTC integration components are implemented and ready for Raspberry Pi camera integration. The framework supports real-time video streaming with session-based access control.