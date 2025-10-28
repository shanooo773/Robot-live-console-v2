# Streams Router Implementation

## Overview

This implementation adds a minimal streams router for managing RTSP/WebRTC streams in the Robot Console backend. The router provides admin-controlled stream registration and authenticated user access to stream signaling information.

## Architecture

- **Router Location**: `backend/routes/streams.py`
- **Storage**: File-based JSON storage at `backend/data/streams.json` (development mode)
- **Authentication**: Reuses existing `require_admin` and `get_current_user` dependencies, with X-ADMIN-KEY header fallback

## Endpoints

### 1. POST /api/streams/start
**Auth**: Admin only (X-ADMIN-KEY header)

**Request**:
```json
{
  "rtsp_url": "rtsp://example.com:554/stream",
  "booking_id": "booking-123",
  "stream_id": "optional-custom-id",
  "type": "rtsp"
}
```

**Response** (201 Created):
```json
{
  "stream_id": "unique-stream-id"
}
```

**Features**:
- Validates RTSP URL format when `type === 'rtsp'`
- Auto-generates UUID if `stream_id` not provided
- Persists to `backend/data/streams.json`
- **Never returns `rtsp_url` in response**
- Optionally notifies bridge control service (non-blocking)

### 2. POST /api/streams/stop
**Auth**: Admin only (X-ADMIN-KEY header)

**Request**:
```json
{
  "stream_id": "stream-to-stop"
}
```

**Response** (200 OK):
```json
{
  "message": "Stream stopped successfully",
  "stream_id": "stream-to-stop"
}
```

**Features**:
- Marks stream status as 'stopped'
- Optionally notifies bridge control service (non-blocking)

### 3. GET /api/streams/{stream_id}
**Auth**: Authenticated users (permissive in dev mode)

**Response** (200 OK):
```json
{
  "stream_id": "stream-123",
  "type": "rtsp",
  "booking_id": "booking-456",
  "status": "running",
  "created_at": "2025-10-28T02:35:45.464955"
}
```

**Features**:
- Returns safe metadata only
- **Never includes `rtsp_url`**

### 4. GET /api/streams/{stream_id}/signaling-info
**Auth**: Authenticated users with active booking (permissive in dev mode)

**Response** (200 OK):
```json
{
  "ws_url": "ws://localhost:8081"
}
```

**Features**:
- Returns WebSocket URL for signaling
- Verifies user has active booking (when integrated)
- **Never returns `rtsp_url` or secrets**

## Security Features

1. **rtsp_url Protection**: Server-side only, never exposed in any response
2. **Admin Authentication**: Required for start/stop operations
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
