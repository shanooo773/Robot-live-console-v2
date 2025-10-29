# Streams Router Implementation

## Overview

This implementation provides stream access endpoints for managing RTSP streaming in the Robot Console backend using Robot Registry as the single source of truth.

**Migration Note**: Legacy file-based `streams.json` support has been removed. All RTSP URLs are now managed through Robot Registry (database).

## Architecture

- **Router Location**: `backend/routes/streams.py`
- **Storage**: Database (Robot Registry) - `robots.rtsp_url` field
- **Authentication**: Reuses existing `get_current_user` dependency
- **Authorization**: Booking-based access control

## Endpoints

### 1. GET /api/streams/{robot_id}
**Auth**: Authenticated users (permissive in dev mode)

**Parameters**:
- `robot_id`: Robot ID from Robot Registry (used as stream_id)

**Response** (200 OK):
```json
{
  "stream_id": "5",
  "robot_id": 5,
  "robot_name": "Security Camera 1",
  "robot_type": "camera",
  "status": "active"
}
```

**Features**:
- Returns safe metadata only
- **Never includes `rtsp_url`**
- Verifies robot exists and has RTSP configured
- Returns 404 if robot not found or has no RTSP URL

### 2. GET /api/streams/{robot_id}/signaling-info
**Auth**: Authenticated users with active booking

**Parameters**:
- `robot_id`: Robot ID from Robot Registry (used as stream_id)

**Response** (200 OK):
```json
{
  "ws_url": "ws://localhost:8081/ws/stream?robot_id=5"
}
```

**Features**:
- Returns WebSocket URL for signaling to bridge
- Verifies user has active booking for the robot
- Verifies robot exists, has RTSP configured, and is active
- **Never returns `rtsp_url` or secrets**
- Returns 403 if user has no active booking
- Returns 404 if robot not found or has no RTSP URL
- Returns 403 if robot is not active

### 3. GET /api/streams/bridge/authorize
**Auth**: Bridge only (X-BRIDGE-SECRET header required)

**Query Parameters**:
- `robot_id`: Robot ID to authorize

**Headers**:
- `X-BRIDGE-SECRET`: Bridge control secret (from BRIDGE_CONTROL_SECRET env var)

**Response** (200 OK):
```json
{
  "rtsp_url": "rtsp://10.0.0.2:8554",
  "robot_id": 5,
  "robot_name": "Security Camera 1"
}
```

**Features**:
- **ONLY endpoint that returns `rtsp_url`**
- Requires BRIDGE_CONTROL_SECRET for authorization
- Used by bridge to get RTSP URL for streaming
- Returns 401 if secret is invalid
- Returns 404 if robot not found or has no RTSP URL

## Security Features

1. **rtsp_url Protection**: Server-side only, never exposed to clients
2. **Bridge Authorization**: Bridge must provide secret to access RTSP URLs
3. **Input Validation**: RTSP URL format, duplicate stream IDs
4. **Proper HTTP Status Codes**: 400/401/403/404

## File Storage

The implementation uses atomic file writes with file locking:

```python
# Read with shared lock
with open(file, 'r') as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_SH)
    data = json.load(f)
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)

# Write with exclusive lock
with open(temp_file, 'w') as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    json.dump(data, f)
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
temp_file.replace(actual_file)  # Atomic rename
```

## Environment Variables

- **BRIDGE_WS_URL**: WebSocket URL for signaling (default: `ws://localhost:8081`)
- **BRIDGE_CONTROL_URL**: Bridge control service URL (optional)
- **ADMIN_API_KEY**: Admin authentication key for fallback (optional)

## Database Migration Path

All file I/O operations are marked with `TODO-DB` comments for easy migration:

```python
# TODO-DB: Replace this with: db.get_all_streams()
def read_streams_file() -> List[Dict[str, Any]]:
    ...

# TODO-DB: Replace this with: db.create_stream(stream_data)
def add_stream(stream_data: Dict[str, Any]) -> bool:
    ...

# TODO-DB: Replace this with: db.update_stream_status(stream_id, status)
def update_stream_status(stream_id: str, status: str) -> bool:
    ...
```

## Integration

The router is automatically included in `backend/main.py`:

```python
# Import streams router
from routes import streams

# Include router
app.include_router(streams.router)
logger.info("✅ Streams router registered at /api/streams")
```

## Testing

Run the test suite:

```bash
cd backend
python3 test_streams.py
```

All tests verify:
- ✅ Admin authentication
- ✅ RTSP URL validation
- ✅ Stream lifecycle (start/stop)
- ✅ Metadata retrieval
- ✅ rtsp_url is never leaked
- ✅ Signaling info access
- ✅ Error handling (404, 409, etc.)

## Example Usage

### Starting a Stream (Admin)

```bash
curl -X POST http://localhost:8000/api/streams/start \
  -H "Content-Type: application/json" \
  -H "X-ADMIN-KEY: your-admin-key" \
  -d '{
    "rtsp_url": "rtsp://camera.example.com:554/live",
    "booking_id": "booking-789",
    "type": "rtsp"
  }'
```

### Getting Stream Info (User)

```bash
curl http://localhost:8000/api/streams/stream-id-here
```

### Getting Signaling Info (User with Booking)

```bash
curl http://localhost:8000/api/streams/stream-id-here/signaling-info
```

## Notes

- Implementation is intentionally minimal and focused
- No SQLAlchemy or database migrations added
- File storage is suitable for development/testing
- Clear migration path to database provided
- Bridge control integration is optional and non-blocking
- Authentication uses existing system with simple fallback

## Migration from Legacy streams.json

**BREAKING CHANGE**: Legacy `POST /api/streams/start` and `POST /api/streams/stop` endpoints have been removed.

**Migration Steps**:
1. Remove any code that calls `/api/streams/start` or `/api/streams/stop`
2. Configure RTSP URLs in Robot Registry via `/admin/robots` endpoints
3. Update frontend to use robot_id as stream_id
4. Ensure BRIDGE_CONTROL_SECRET is set for production
5. Update bridge to call `/api/streams/bridge/authorize` to get RTSP URLs

**New Workflow**:
- Admin configures RTSP URLs in Robot Registry (database)
- Users access streams using robot_id
- Bridge authorizes with secret to get RTSP URL
- No file-based storage - all data in database
