# RTSP Streaming Implementation Guide

## Overview

This implementation enables administrators to register RTSP streams (e.g., from cameras at rtsp://10.0.0.2:8554) and allows authenticated users with active bookings to view these streams through an external WebRTC bridge.

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐      ┌─────────┐
│   Admin     │─────▶│   Backend    │─────▶│ WebRTC Bridge   │─────▶│  RTSP   │
│  (Register) │      │ (API Server) │      │  (GStreamer)    │      │ Camera  │
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
  - `POST /api/streams/start` - Register RTSP stream (admin only)
  - `POST /api/streams/stop` - Stop stream (admin only)
  - `GET /api/streams/{stream_id}` - Get stream metadata (authenticated)
  - `GET /api/streams/{stream_id}/signaling-info` - Get WebSocket URL (booked users)

### 2. WebRTC Bridge (External Service)
- **Not included in this repository** - runs separately
- **Purpose**: Converts RTSP to WebRTC
- **Technology**: GStreamer with webrtcbin
- **Endpoint**: Exposes WebSocket at `ws://localhost:8081/ws/stream`

### 3. Frontend (React)
- Connects to backend for authentication
- Obtains WebSocket URL from `/api/streams/{stream_id}/signaling-info`
- Establishes WebRTC connection through bridge

## Configuration

### Backend Environment Variables (.env)

```bash
# WebRTC Bridge Configuration
BRIDGE_WS_URL=ws://localhost:8081/ws/stream
BRIDGE_CONTROL_URL=http://localhost:8081
ADMIN_API_KEY=choose-a-secure-key-for-production
```

### Environment Variables Explained

- **BRIDGE_WS_URL**: WebSocket endpoint for stream signaling
  - Development: `ws://localhost:8081/ws/stream`
  - Production: `wss://your-bridge.domain.com/ws/stream`

- **BRIDGE_CONTROL_URL**: Optional HTTP endpoint for bridge control
  - Used to notify bridge when streams start/stop
  - Can be omitted if bridge auto-discovers streams

- **ADMIN_API_KEY**: Fallback admin authentication
  - Only used when standard auth is unavailable
  - Should be a strong random key in production

## Usage

### 1. Admin: Register RTSP Stream

```bash
curl -X POST http://localhost:8000/api/streams/start \
  -H "Content-Type: application/json" \
  -H "X-ADMIN-KEY: your-admin-key" \
  -d '{
    "rtsp_url": "rtsp://10.0.0.2:8554",
    "booking_id": "booking-123",
    "type": "rtsp"
  }'
```

**Response:**
```json
{
  "stream_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Note**: RTSP URL is never returned in responses for security.

### 2. Viewer: Get Stream Metadata

```bash
curl http://localhost:8000/api/streams/{stream_id} \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "stream_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "rtsp",
  "booking_id": "booking-123",
  "status": "running",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### 3. Viewer: Get WebSocket URL (Requires Active Booking)

```bash
curl http://localhost:8000/api/streams/{stream_id}/signaling-info \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "ws_url": "ws://localhost:8081/ws/stream?stream_id=550e8400-e29b-41d4-a716-446655440000"
}
```

### 4. Admin: Stop Stream

```bash
curl -X POST http://localhost:8000/api/streams/stop \
  -H "Content-Type: application/json" \
  -H "X-ADMIN-KEY: your-admin-key" \
  -d '{
    "stream_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

## Security Features

### 1. RTSP URL Protection
- RTSP URLs are **never** exposed in API responses
- Stored server-side only in `backend/data/streams.json`
- Frontend never has access to RTSP credentials

### 2. Authentication & Authorization
- Stream registration requires admin authentication
- Stream viewing requires:
  - Valid JWT token (user authentication)
  - Active booking for the stream's booking_id
- WebSocket URL includes stream_id for bridge-side validation

### 3. Booking Validation
- Users can only access streams for their active bookings
- Validation checks:
  - User has booking with matching booking_id
  - Booking status is "active"
  - Current time is within booking window (if implemented)

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
   - [ ] WebRTC bridge running (external)

2. **Admin Stream Registration**
   - [ ] Can register RTSP stream with valid URL
   - [ ] Cannot register with invalid URL (http://)
   - [ ] RTSP URL not in response
   - [ ] Stream ID returned

3. **Stream Metadata Access**
   - [ ] Can get metadata with authentication
   - [ ] Metadata includes status, type, booking_id
   - [ ] RTSP URL not in metadata

4. **WebSocket Signaling Info**
   - [ ] Can get ws_url with valid booking
   - [ ] Cannot get ws_url without booking
   - [ ] RTSP URL not in signaling info
   - [ ] stream_id in WebSocket URL

5. **Stream Control**
   - [ ] Can stop stream as admin
   - [ ] Status updated to "stopped"
   - [ ] Cannot access stopped stream

6. **No Regression**
   - [ ] Existing robot WebRTC streams work
   - [ ] Booking system unaffected
   - [ ] Admin dashboard functional

## Troubleshooting

### Stream Not Accessible

**Problem**: User cannot access stream
**Checks**:
1. User has valid JWT token?
2. User has active booking for this booking_id?
3. Stream status is "running"?
4. WebRTC bridge is running?

### RTSP Connection Failed

**Problem**: Bridge cannot connect to RTSP source
**Checks**:
1. RTSP URL correct (rtsp://10.0.0.2:8554)?
2. Camera accessible from bridge server?
3. Network/firewall allows RTSP port (554)?
4. Bridge logs show connection attempt?

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
BRIDGE_CONTROL_URL=https://bridge.yourdomain.com
ADMIN_API_KEY=<generate-secure-random-key>
ENVIRONMENT=production
```

### 2. Secure Admin API Key

```bash
# Generate secure key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Deploy WebRTC Bridge

The bridge service should:
- Run on separate server or container
- Expose WebSocket on wss:// (TLS required)
- Handle authentication/validation
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
