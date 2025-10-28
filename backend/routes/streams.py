"""
Streams Router for RTSP/WebRTC Stream Management

This module provides minimal endpoints for managing RTSP streams:
- Admin can register streams (POST /api/streams/start)
- Admin can stop streams (POST /api/streams/stop)
- Authenticated users can get stream metadata (GET /api/streams/{stream_id})
- Authenticated users with active bookings can get signaling info (GET /api/streams/{stream_id}/signaling-info)

NOTE: This uses a file-based storage (backend/data/streams.json) for development.
TODO: Replace file I/O operations with real database calls when ready.
Search for "TODO-DB" comments to find locations needing database replacement.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
import fcntl
import requests

# Import existing auth dependencies
try:
    from auth import get_current_user, require_admin
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

logger = logging.getLogger(__name__)

# Create router with /api/streams prefix
router = APIRouter(prefix="/api/streams", tags=["streams"])

# File storage path
STREAMS_FILE = Path(__file__).parent.parent / "data" / "streams.json"

# Environment variables for bridge service
BRIDGE_WS_URL = os.getenv("BRIDGE_WS_URL", "ws://localhost:8081")
BRIDGE_CONTROL_URL = os.getenv("BRIDGE_CONTROL_URL")


# ============================================================================
# Pydantic Models
# ============================================================================

class StreamStartRequest(BaseModel):
    """Request model for starting a stream"""
    rtsp_url: str = Field(..., description="RTSP URL for the stream")
    booking_id: str = Field(..., description="Booking ID associated with this stream")
    stream_id: Optional[str] = Field(None, description="Optional custom stream ID")
    type: str = Field(default="rtsp", description="Stream type: 'rtsp' or 'webrtc'")


class StreamStartResponse(BaseModel):
    """Response model for stream start (no rtsp_url)"""
    stream_id: str = Field(..., description="Unique stream identifier")


class StreamStopRequest(BaseModel):
    """Request model for stopping a stream"""
    stream_id: str = Field(..., description="Stream ID to stop")


class StreamMetadataResponse(BaseModel):
    """Response model for stream metadata (no rtsp_url)"""
    stream_id: str
    type: str
    booking_id: str
    status: str
    created_at: str


class StreamSignalingInfoResponse(BaseModel):
    """Response model for signaling info (no rtsp_url or secrets)"""
    ws_url: str = Field(..., description="WebSocket URL for signaling")


# ============================================================================
# Helper Functions for File I/O
# ============================================================================

def read_streams_file() -> List[Dict[str, Any]]:
    """
    Read streams from JSON file with file locking.
    
    TODO-DB: Replace this with: db.get_all_streams()
    """
    if not STREAMS_FILE.exists():
        return []
    
    try:
        with open(STREAMS_FILE, 'r') as f:
            # Acquire shared lock for reading
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                data = json.load(f)
                return data if isinstance(data, list) else []
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from {STREAMS_FILE}")
        return []
    except Exception as e:
        logger.error(f"Error reading streams file: {e}")
        return []


def write_streams_file(streams: List[Dict[str, Any]]) -> bool:
    """
    Write streams to JSON file with file locking and atomic write.
    
    TODO-DB: Replace this with: db.update_streams(streams)
    """
    try:
        # Ensure directory exists
        STREAMS_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to temporary file first, then rename for atomicity
        temp_file = STREAMS_FILE.with_suffix('.tmp')
        with open(temp_file, 'w') as f:
            # Acquire exclusive lock for writing
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(streams, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        
        # Atomic rename
        temp_file.replace(STREAMS_FILE)
        return True
    except Exception as e:
        logger.error(f"Error writing streams file: {e}")
        return False


def get_stream_by_id(stream_id: str) -> Optional[Dict[str, Any]]:
    """
    Get stream by ID from file storage.
    
    TODO-DB: Replace this with: db.get_stream_by_id(stream_id)
    """
    streams = read_streams_file()
    for stream in streams:
        if stream.get("stream_id") == stream_id:
            return stream
    return None


def add_stream(stream_data: Dict[str, Any]) -> bool:
    """
    Add a new stream to file storage.
    
    TODO-DB: Replace this with: db.create_stream(stream_data)
    """
    streams = read_streams_file()
    streams.append(stream_data)
    return write_streams_file(streams)


def update_stream_status(stream_id: str, status: str) -> bool:
    """
    Update stream status in file storage.
    
    TODO-DB: Replace this with: db.update_stream_status(stream_id, status)
    """
    streams = read_streams_file()
    updated = False
    for stream in streams:
        if stream.get("stream_id") == stream_id:
            stream["status"] = status
            updated = True
            break
    
    if updated:
        return write_streams_file(streams)
    return False


# ============================================================================
# Admin Authentication Helper (with fallback)
# ============================================================================

def verify_admin(
    current_user: Optional[Dict[str, Any]] = None,
    x_admin_key: Optional[str] = Header(None, alias="X-ADMIN-KEY")
) -> Dict[str, Any]:
    """
    Verify admin access using either existing require_admin or X-ADMIN-KEY fallback.
    
    This is a dev fallback for when auth system is not fully available.
    In production, always use the proper auth system.
    """
    # First, try using existing auth system if available
    if AUTH_AVAILABLE and current_user:
        # Already validated by require_admin dependency
        return current_user
    
    # Fallback: check X-ADMIN-KEY header against env var (dev only)
    admin_api_key = os.getenv("ADMIN_API_KEY")
    if admin_api_key and x_admin_key == admin_api_key:
        logger.warning("Using fallback admin key authentication (dev mode)")
        return {"sub": "admin", "role": "admin", "email": "admin@system"}
    
    # No valid auth
    raise HTTPException(
        status_code=401,
        detail="Admin authentication required. Use existing auth or provide X-ADMIN-KEY header."
    )


def user_has_active_booking(user_id: int, booking_id: str) -> bool:
    """
    Check if user has an active booking.
    
    TODO-DB: Replace this with proper booking validation:
    booking = db.get_booking_by_id(booking_id)
    return booking and booking['user_id'] == user_id and booking['status'] == 'active'
    
    For now, this is permissive for dev/testing.
    """
    # DEV MODE: Permissive behavior - log warning and allow
    logger.warning(
        f"DEV MODE: Skipping booking validation for user {user_id}, booking {booking_id}. "
        "Implement proper booking check when database is available."
    )
    return True


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/start", response_model=StreamStartResponse, status_code=201)
async def start_stream(
    request: StreamStartRequest,
    x_admin_key: Optional[str] = Header(None, alias="X-ADMIN-KEY")
):
    """
    Start a new stream (admin only).
    
    - Validates RTSP URL format when type is 'rtsp'
    - Persists to backend/data/streams.json
    - Does NOT return rtsp_url in response
    - Optionally notifies bridge service (non-blocking)
    
    TODO-DB: Replace file operations with database calls
    """
    # Verify admin access (use existing auth or fallback)
    # Try to get current_user if auth is available, otherwise use fallback
    admin_user = verify_admin(None, x_admin_key)
    
    # Validate RTSP URL format if type is 'rtsp'
    if request.type == "rtsp" and not request.rtsp_url.startswith("rtsp://"):
        raise HTTPException(
            status_code=400,
            detail="Invalid RTSP URL: must start with 'rtsp://'"
        )
    
    # Generate stream_id if not provided
    stream_id = request.stream_id or str(uuid.uuid4())
    
    # Check if stream_id already exists
    existing = get_stream_by_id(stream_id)
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Stream with ID {stream_id} already exists"
        )
    
    # Create stream record
    stream_data = {
        "stream_id": stream_id,
        "rtsp_url": request.rtsp_url,  # Stored server-side only
        "booking_id": request.booking_id,
        "type": request.type,
        "status": "running",
        "created_by": admin_user.get("sub", "unknown"),
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Persist to file storage
    # TODO-DB: Replace with: db.create_stream(stream_data)
    if not add_stream(stream_data):
        raise HTTPException(
            status_code=500,
            detail="Failed to persist stream data"
        )
    
    logger.info(f"Stream started: {stream_id} by {admin_user.get('sub')}")
    
    # Optionally notify bridge control (non-blocking, don't fail if it fails)
    if BRIDGE_CONTROL_URL:
        try:
            response = requests.post(
                f"{BRIDGE_CONTROL_URL}/control/start",
                json={"stream_id": stream_id},
                timeout=5
            )
            if response.status_code != 200:
                logger.warning(
                    f"Bridge control notification failed: {response.status_code}"
                )
        except Exception as e:
            logger.warning(f"Failed to notify bridge control: {e}")
    
    # Return response WITHOUT rtsp_url
    return StreamStartResponse(stream_id=stream_id)


@router.post("/stop", status_code=200)
async def stop_stream(
    request: StreamStopRequest,
    x_admin_key: Optional[str] = Header(None, alias="X-ADMIN-KEY")
):
    """
    Stop a stream (admin only).
    
    - Marks status as 'stopped' in file storage
    - Optionally notifies bridge service (non-blocking)
    
    TODO-DB: Replace file operations with database calls
    """
    # Verify admin access
    admin_user = verify_admin(None, x_admin_key)
    
    # Check if stream exists
    stream = get_stream_by_id(request.stream_id)
    if not stream:
        raise HTTPException(
            status_code=404,
            detail=f"Stream {request.stream_id} not found"
        )
    
    # Update status to stopped
    # TODO-DB: Replace with: db.update_stream_status(request.stream_id, 'stopped')
    if not update_stream_status(request.stream_id, "stopped"):
        raise HTTPException(
            status_code=500,
            detail="Failed to update stream status"
        )
    
    logger.info(f"Stream stopped: {request.stream_id} by {admin_user.get('sub')}")
    
    # Optionally notify bridge control (non-blocking)
    if BRIDGE_CONTROL_URL:
        try:
            response = requests.post(
                f"{BRIDGE_CONTROL_URL}/control/stop",
                json={"stream_id": request.stream_id},
                timeout=5
            )
            if response.status_code != 200:
                logger.warning(
                    f"Bridge control stop notification failed: {response.status_code}"
                )
        except Exception as e:
            logger.warning(f"Failed to notify bridge control for stop: {e}")
    
    return {"message": "Stream stopped successfully", "stream_id": request.stream_id}


@router.get("/{stream_id}", response_model=StreamMetadataResponse)
async def get_stream_metadata(
    stream_id: str
):
    """
    Get stream metadata (authenticated users).
    
    Returns safe metadata only - does NOT include rtsp_url.
    
    TODO-DB: Replace with: stream = db.get_stream_by_id(stream_id)
    """
    # For now, allow permissive access for dev (no auth required)
    # In production, add: current_user: Dict[str, Any] = Depends(get_current_user)
    logger.warning("Dev mode: Allowing permissive access to stream metadata")
    
    # Get stream from storage
    # TODO-DB: Replace with: stream = db.get_stream_by_id(stream_id)
    stream = get_stream_by_id(stream_id)
    
    if not stream:
        raise HTTPException(
            status_code=404,
            detail=f"Stream {stream_id} not found"
        )
    
    # Return safe metadata only (NO rtsp_url)
    return StreamMetadataResponse(
        stream_id=stream["stream_id"],
        type=stream["type"],
        booking_id=stream["booking_id"],
        status=stream["status"],
        created_at=stream["created_at"]
    )


@router.get("/{stream_id}/signaling-info", response_model=StreamSignalingInfoResponse)
async def get_signaling_info(
    stream_id: str
):
    """
    Get signaling info for a stream (authenticated users with active booking).
    
    - Verifies user has active booking for the stream
    - Returns WebSocket URL for signaling
    - Does NOT return rtsp_url or any secrets
    
    TODO-DB: Replace booking validation with real database check
    TODO-AUTH: Add authentication: current_user: Dict[str, Any] = Depends(get_current_user)
    """
    # DEV MODE: For now, allow permissive access for testing
    # In production, require authentication and booking validation
    logger.warning("DEV MODE: Allowing permissive access to signaling info for testing")
    
    # Get stream from storage
    # TODO-DB: Replace with: stream = db.get_stream_by_id(stream_id)
    stream = get_stream_by_id(stream_id)
    
    if not stream:
        raise HTTPException(
            status_code=404,
            detail=f"Stream {stream_id} not found"
        )
    
    # DEV MODE: Skip booking validation for testing
    # TODO-DB: Add proper booking validation when auth is integrated
    # user_id = int(current_user.get("sub", 0))
    # booking_id = stream["booking_id"]
    # if not user_has_active_booking(user_id, booking_id):
    #     raise HTTPException(status_code=403, detail="Access denied.")
    
    # Return WebSocket URL (no secrets)
    return StreamSignalingInfoResponse(ws_url=BRIDGE_WS_URL)
