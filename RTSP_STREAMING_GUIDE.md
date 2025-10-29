# RTSP Streaming Implementation Guide

## Overview

This implementation enables administrators to configure RTSP streams for robots in the Robot Registry, and allows authenticated users with active bookings to view these streams through an external WebRTC bridge.

**Migration Note**: Legacy file-based `streams.json` has been removed. All RTSP sources must now be configured in the Robot Registry (database).

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐      ┌─────────┐
│   Admin     │─────▶│ Robot        │─────▶│ WebRTC Bridge   │─────▶│  RTSP   │
│ (Configure) │      │ Registry DB  │      │  (GStreamer)    │      │ Camera  │
└─────────────┘      └──────────────┘      └─────────────────┘      └─────────┘
                             │                       │
                             │                       │
                             ▼                       ▼
                     ┌──────────────┐       ┌─────────────┐
                     │  Booking DB  │       │  WebSocket  │
                     │ (Validation) │       │ (Signaling) │
                     └──────────────┘       └─────────────┘
                             │                       │
                             │                       │
                             ▼                       ▼
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Viewer    │─────▶│   Backend    │─────▶│ WebRTC Bridge   │
│  (Booked)   │      │   (Auth)     │      │  (ws://...)     │
└─────────────┘      └──────────────┘      └─────────────────┘
```

## Components

### 1. Backend API (FastAPI)
- **Location**: `backend/routes/streams.py`
- **Endpoints**:
  - `GET /api/streams/{robot_id}` - Get stream metadata (authenticated) - stream_id corresponds to robot_id
  - `GET /api/streams/{robot_id}/signaling-info` - Get WebSocket URL (booked users only)
  - `GET /api/streams/bridge/authorize` - Bridge authorization endpoint (requires BRIDGE_CONTROL_SECRET)

**NOTE**: `POST /api/streams/start` and `POST /api/streams/stop` endpoints have been **removed**. Stream management is now done through Robot Registry.

### 2. Robot Registry (Database)
- **Location**: `backend/database.py`
- **Table**: `robots`
- **RTSP Field**: `rtsp_url` (VARCHAR(500))
- Admins configure RTSP URLs via `/admin/robots` endpoints

### 3. WebRTC Bridge (External Service)
- **Not included in this repository** - runs separately
- **Purpose**: Converts RTSP to WebRTC
- **Technology**: GStreamer with webrtcbin
- **Endpoint**: Exposes WebSocket at `ws://localhost:8081/ws/stream`
- **Security**: Bridge must call `/api/streams/bridge/authorize` to get RTSP URL

### 4. Frontend (React)
- Connects to backend for authentication
- Obtains WebSocket URL from `/api/streams/{robot_id}/signaling-info`
- Establishes WebRTC connection through bridge

## Configuration

### Backend Environment Variables (.env)

```bash
# WebRTC Bridge Configuration
BRIDGE_WS_URL=ws://localhost:8081/ws/stream
BRIDGE_CONTROL_SECRET=choose-a-secure-secret-for-bridge
```

### Environment Variables Explained

- **BRIDGE_WS_URL**: WebSocket endpoint for stream signaling
  - Development: `ws://localhost:8081/ws/stream`
  - Production: `wss://your-bridge.domain.com/ws/stream`

- **BRIDGE_CONTROL_SECRET**: Secret for bridge authorization
  - Bridge must provide this in `X-BRIDGE-SECRET` header
  - Used to authorize bridge to get RTSP URLs from backend
  - Should be a strong random key

## Usage

### 1. Admin: Configure Robot with RTSP URL

Add RTSP URL to a robot in Robot Registry:

```bash
curl -X POST http://localhost:8000/admin/robots \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{
    "name": "Security Camera 1",
    "type": "camera",
    "rtsp_url": "rtsp://10.0.0.2:8554",
    "status": "active"
  }'
```

**Response:**
```json
{
  "id": 5,
  "name": "Security Camera 1",
  "type": "camera",
  "rtsp_url": "rtsp://10.0.0.2:8554",
  "status": "active",
  "created_at": "2024-01-20T10:00:00"
}
```

Update existing robot with RTSP URL:

```bash
curl -X PUT http://localhost:8000/admin/robots/5 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin-token>" \
  -d '{
    "rtsp_url": "rtsp://10.0.0.2:8554"
  }'
```

### 2. Viewer: Get Stream Metadata

**Response:**
```json
{
  "stream_id": "5",
  "robot_id": 5,
  "robot_name": "Security Camera 1",
  "robot_type": "camera",
  "status": "active"
}
```

**Note**: The `stream_id` corresponds to the `robot_id`.

### 3. Viewer: Get WebSocket URL (Requires Active Booking)

```bash
curl http://localhost:8000/api/streams/5/signaling-info \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "ws_url": "ws://localhost:8081/ws/stream?robot_id=5"
}
```

### 4. Bridge: Authorize and Get RTSP URL

The bridge must call the authorization endpoint with the secret to get the RTSP URL:

```bash
curl http://localhost:8000/api/streams/bridge/authorize?robot_id=5 \
  -H "X-BRIDGE-SECRET: your-bridge-secret"
```

**Response:**
```json
{
  "rtsp_url": "rtsp://10.0.0.2:8554",
  "robot_id": 5,
  "robot_name": "Security Camera 1"
}
```

## Security Features

### 1. RTSP URL Protection
- RTSP URLs are **never** exposed in client-facing API responses
- Stored in database (`robots.rtsp_url` field)
- Only accessible via bridge authorization endpoint with secret
- Frontend never has access to RTSP credentials

### 2. Authentication & Authorization
- Robot configuration requires admin authentication
- Stream viewing requires:
  - Valid JWT token (user authentication)
  - Active booking for the robot
- WebSocket URL includes robot_id for bridge-side validation
- Bridge must use secret to authorize and get RTSP URL

### 3. Booking Validation
- Users can only access streams for robots they have active bookings for
- Validation checks:
  - User has booking for robot_id or robot_type
  - Booking status is "active"
  - Current time is within booking window (if implemented)

### 4. Bridge Authorization
- Bridge must provide `BRIDGE_CONTROL_SECRET` in `X-BRIDGE-SECRET` header
- Bridge calls `/api/streams/bridge/authorize?robot_id={id}` to get RTSP URL
- This ensures bridge cannot access arbitrary RTSP URLs
- Backend validates booking before returning RTSP URL to bridge

## Testing

### Run Integration Tests

```bash
cd backend
python test_stream_integration.py
```

### Manual Testing Checklist

1. **Setup**
   - [ ] Backend running: `uvicorn main:app --reload --port 8000`
   - [ ] Environment variables configured in `.env`
   - [ ] Robot with RTSP URL configured in database
   - [ ] WebRTC bridge running (external)

2. **Admin Robot Configuration**
   - [ ] Can create robot with RTSP URL
   - [ ] Can update robot with RTSP URL
   - [ ] RTSP URL validated (must start with rtsp://)
   - [ ] RTSP URL visible in admin responses

3. **Stream Metadata Access**
   - [ ] Can get metadata with authentication (using robot_id as stream_id)
   - [ ] Metadata includes robot info, status
   - [ ] RTSP URL not in client metadata

4. **WebSocket Signaling Info**
   - [ ] Can get ws_url with valid booking
   - [ ] Cannot get ws_url without booking
   - [ ] RTSP URL not in signaling info
   - [ ] robot_id in WebSocket URL

5. **Bridge Authorization**
   - [ ] Bridge can get RTSP URL with secret
   - [ ] Bridge cannot get RTSP URL without secret
   - [ ] RTSP URL returned only to bridge

6. **No Regression**
   - [ ] Existing robot WebRTC streams work
   - [ ] Booking system unaffected
   - [ ] Admin dashboard functional

## Troubleshooting

### Stream Not Accessible

**Problem**: User cannot access stream
**Checks**:
1. User has valid JWT token?
2. User has active booking for this robot?
3. Robot status is "active"?
4. Robot has rtsp_url configured?
5. WebRTC bridge is running?

### RTSP Connection Failed

**Problem**: Bridge cannot connect to RTSP source
**Checks**:
1. RTSP URL correct (rtsp://10.0.0.2:8554)?
2. Camera accessible from bridge server?
3. Network/firewall allows RTSP port (554)?
4. Bridge logs show connection attempt?
5. Bridge called `/api/streams/bridge/authorize` successfully?

### WebSocket Connection Failed

**Problem**: Frontend cannot connect to WebSocket
**Checks**:
1. BRIDGE_WS_URL correct in backend .env?
2. WebRTC bridge WebSocket server running?
3. CORS configured for WebSocket origin?
4. Browser console shows connection attempt?

## Production Deployment

### 1. Update Environment Variables

```bash
# Production .env
BRIDGE_WS_URL=wss://bridge.yourdomain.com/ws/stream
BRIDGE_CONTROL_SECRET=<generate-secure-random-secret>
ENVIRONMENT=production
```

### 2. Secure Bridge Secret

```bash
# Generate secure secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Deploy WebRTC Bridge

The bridge service should:
- Run on separate server or container
- Expose WebSocket on wss:// (TLS required)
- Call `/api/streams/bridge/authorize` with secret to get RTSP URL
- Validate robot_id from WebSocket query parameter
- Use GStreamer pipeline:
  ```
  rtspsrc location='rtsp://10.0.0.2:8554' latency=200 ! 
  rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! 
  queue ! x264enc tune=zerolatency bitrate=800 speed-preset=superfast ! 
  rtph264pay config-interval=1 pt=96 ! 
  application/x-rtp,media=video,encoding-name=H264,payload=96 ! 
  webrtcbin name=webrtcbin
  ```

### 4. Database Migration (Future)

Currently using file storage (`backend/data/streams.json`). For production:

```python
# Replace file operations with database calls
# In streams.py, search for "TODO-DB" comments

# Example migration:
def get_stream_by_id(stream_id: str) -> Optional[Dict[str, Any]]:
    return db.get_stream_by_id(stream_id)  # Use database

def add_stream(stream_data: Dict[str, Any]) -> bool:
    return db.create_stream(stream_data)  # Use database
```

## API Reference

### POST /api/streams/start

**Description**: Register a new RTSP stream (admin only)

**Headers**:
- `X-ADMIN-KEY`: Admin API key (or use JWT with admin role)

**Request Body**:
```json
{
  "rtsp_url": "rtsp://10.0.0.2:8554",
  "booking_id": "booking-123",
  "stream_id": "optional-custom-id",
  "type": "rtsp"
}
```

**Response**: 201 Created
```json
{
  "stream_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### GET /api/streams/{stream_id}

**Description**: Get stream metadata (authenticated users)

**Headers**:
- `Authorization`: Bearer JWT_TOKEN

**Response**: 200 OK
```json
{
  "stream_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "rtsp",
  "booking_id": "booking-123",
  "status": "running",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /api/streams/{stream_id}/signaling-info

**Description**: Get WebSocket URL for stream (booked users only)

**Headers**:
- `Authorization`: Bearer JWT_TOKEN

**Response**: 200 OK
```json
{
  "ws_url": "ws://localhost:8081/ws/stream?stream_id=550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses**:
- 403 Forbidden: User doesn't have active booking
- 404 Not Found: Stream doesn't exist
- 403 Forbidden: Stream not running

### POST /api/streams/stop

**Description**: Stop a stream (admin only)

**Headers**:
- `X-ADMIN-KEY`: Admin API key

**Request Body**:
```json
{
  "stream_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response**: 200 OK
```json
{
  "message": "Stream stopped successfully",
  "stream_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Implementation Notes

### File Storage vs Database

Current implementation uses file-based storage (`backend/data/streams.json`) with:
- File locking for concurrent access
- Atomic writes via temporary files
- JSON format for easy debugging

For production, migrate to database:
1. Add `streams` table to MySQL schema
2. Update helper functions in `routes/streams.py`
3. Search for "TODO-DB" comments for exact locations

### Booking Integration

Stream access validation uses existing booking system:
- `user_has_active_booking()` checks user bookings
- Integrates with `DatabaseManager.get_user_bookings()`
- Falls back to permissive mode if database unavailable

### WebRTC Bridge Independence

Backend is agnostic to bridge implementation:
- Bridge runs as separate service
- Communication via WebSocket (ws://) or secure (wss://)
- Optional control notifications via HTTP
- No tight coupling with GStreamer specifics

## Future Enhancements

1. **Stream Health Monitoring**
   - Periodic health checks to bridge
   - Auto-restart failed streams
   - Alert admins on issues

2. **Multi-Camera Support**
   - Multiple RTSP sources per booking
   - Camera selection in frontend
   - Bandwidth management

3. **Recording & Playback**
   - Record sessions for later review
   - Storage integration (S3, etc.)
   - Playback through same interface

4. **Advanced Security**
   - Token-based WebSocket auth
   - Rate limiting per user
   - IP whitelisting for RTSP sources

5. **Analytics**
   - Stream quality metrics
   - User engagement tracking
   - Bandwidth usage reporting
