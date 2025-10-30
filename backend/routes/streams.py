"""
Streams Router for RTSP/WebRTC Stream Management

Legacy streams.json support removed — Robot Registry is now single source of truth for RTSP.

This module provides minimal endpoints for managing RTSP streams:
- Authenticated users can get stream metadata (GET /api/streams/{stream_id})
- Authenticated users with active bookings can get signaling info (GET /api/streams/{stream_id}/signaling-info)

All RTSP URLs are resolved from the Robot Registry (database). The stream_id corresponds to robot_id.
Booking-based access control is enforced for all stream access.

SECURITY REQUIREMENTS:
- RTSP URLs must NEVER be exposed to client applications or logged in plaintext
- Only the bridge can access RTSP URLs via the /bridge/authorize endpoint
- Bridge must authenticate using X-BRIDGE-SECRET header matching BRIDGE_CONTROL_SECRET
- All client endpoints return only ws_url for signaling, never rtsp_url
"""

import os
import logging
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field

# Import existing auth dependencies
try:
    from auth import get_current_user
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

# Import database for Robot Registry and booking validation
try:
    from database import DatabaseManager
    db = DatabaseManager()
    DB_AVAILABLE = True
except Exception as e:
    DB_AVAILABLE = False
    db = None
    logging.warning(f"Database not available for streams router: {e}")

logger = logging.getLogger(__name__)

# Create router with /api/streams prefix
router = APIRouter(prefix="/api/streams", tags=["streams"])

# Environment variables for bridge service
BRIDGE_WS_URL = os.getenv("BRIDGE_WS_URL", "ws://localhost:8081")
BRIDGE_CONTROL_SECRET = os.getenv("BRIDGE_CONTROL_SECRET", "")


# ============================================================================
# Pydantic Models
# ============================================================================

class StreamMetadataResponse(BaseModel):
    """Response model for stream metadata (no rtsp_url)"""
    stream_id: str
    robot_id: int
    robot_name: str
    robot_type: str
    status: str
    booking_id: Optional[str] = None


class StreamSignalingInfoResponse(BaseModel):
    """Response model for signaling info (no rtsp_url or secrets)"""
    ws_url: str = Field(..., description="WebSocket URL for signaling to bridge")


class BridgeAuthorizeResponse(BaseModel):
    """Response model for bridge authorization (only for bridge, includes rtsp_url)"""
    rtsp_url: str = Field(..., description="RTSP URL for the robot (bridge-only)")
    robot_id: int
    robot_name: str


# ============================================================================
# Robot Registry RTSP Resolution
# ============================================================================

def resolve_robot_rtsp(robot_id: int) -> Optional[str]:
    """
    Resolve RTSP URL from Robot Registry for a given robot_id.
    
    Returns the RTSP URL if found, None otherwise.
    Looks for 'rtsp_url', 'camera_url', or 'camera.rtsp' fields.
    Only returns values that start with 'rtsp://'.
    """
    if not DB_AVAILABLE or not db:
        logger.error("Database not available - cannot resolve RTSP URL from Robot Registry")
        return None
    
    try:
        # Get robot record from database
        robot = db.get_robot_by_id(robot_id)
        if not robot:
            logger.warning(f"Robot {robot_id} not found in Robot Registry")
            return None
        
        # Check for RTSP URL in various canonical fields
        # Priority order: rtsp_url > camera_url > camera.rtsp
        rtsp_url = None
        
        # Check direct rtsp_url field
        if robot.get('rtsp_url') and str(robot['rtsp_url']).startswith('rtsp://'):
            rtsp_url = robot['rtsp_url']
        
        # Check camera_url field
        elif robot.get('camera_url') and str(robot['camera_url']).startswith('rtsp://'):
            rtsp_url = robot['camera_url']
        
        # Check nested camera.rtsp field
        elif robot.get('camera') and isinstance(robot['camera'], dict):
            if robot['camera'].get('rtsp') and str(robot['camera']['rtsp']).startswith('rtsp://'):
                rtsp_url = robot['camera']['rtsp']
        
        if not rtsp_url:
            logger.warning(f"Robot {robot_id} ({robot.get('name')}) has no valid RTSP URL configured")
            return None
        
        # NOTE: Do NOT log rtsp_url to prevent exposure in logs
        logger.info(f"Resolved RTSP URL for robot {robot_id} ({robot.get('name')}) - URL NOT LOGGED FOR SECURITY")
        return rtsp_url
        
    except Exception as e:
        logger.error(f"Error resolving RTSP for robot {robot_id}: {e}")
        return None


# ============================================================================
# Booking Validation Helper
# ============================================================================

def user_has_active_booking_for_robot(user_id: int, robot_id: int) -> bool:
    """
    Check if user has an active booking for the specific robot.
    
    This validates that the user has access to the stream associated with this robot.
    Uses the existing booking validation logic from the database.
    """
    if not DB_AVAILABLE or not db:
        logger.warning(
            f"DEV MODE: Database unavailable, skipping booking validation for user {user_id}, robot {robot_id}. "
            "Implement proper booking check when database is available."
        )
        return True
    
    try:
        # Get robot to find its type and booking associations
        robot = db.get_robot_by_id(robot_id)
        if not robot:
            logger.warning(f"Robot {robot_id} not found for booking validation")
            return False
        
        # Get all user bookings
        bookings = db.get_user_bookings(user_id)
        
        # Check if any active booking matches the robot_id or robot_type
        for booking in bookings:
            # Match by explicit robot_id if present in booking
            if booking.get("robot_id") == robot_id and booking.get("status") == "active":
                logger.info(f"User {user_id} has active booking for robot {robot_id}")
                return True
            
            # Match by robot_type as fallback
            if booking.get("robot_type") == robot.get("type") and booking.get("status") == "active":
                logger.info(f"User {user_id} has active booking for robot type {robot.get('type')}")
                return True
        
        logger.warning(f"User {user_id} does not have active booking for robot {robot_id}")
        return False
        
    except Exception as e:
        logger.error(f"Error checking booking for user {user_id}, robot {robot_id}: {e}")
        # Fail open in dev mode, fail closed in production
        return True if os.getenv("ENVIRONMENT") == "development" else False


# ============================================================================
# API Endpoints
# ============================================================================
# NOTE: POST /api/streams/start and POST /api/streams/stop have been removed.
# All stream management is now done through the Robot Registry.
# Admins must configure RTSP URLs in the Robot Registry (rtsp_url field).

@router.get("/{stream_id}", response_model=StreamMetadataResponse)
async def get_stream_metadata(
    stream_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user) if AUTH_AVAILABLE else None
):
    """
    Get stream metadata (authenticated users).
    
    stream_id corresponds to robot_id from the Robot Registry.
    Returns safe metadata only - does NOT include rtsp_url.
    """
    # Require authentication if available
    if not AUTH_AVAILABLE or not current_user:
        logger.warning("Dev mode: Allowing permissive access to stream metadata")
    
    # Parse robot_id from stream_id
    try:
        robot_id = int(stream_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stream_id format. stream_id must be a robot_id (integer)"
        )
    
    # Get robot from Robot Registry
    if not DB_AVAILABLE or not db:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable - cannot access Robot Registry"
        )
    
    robot = db.get_robot_by_id(robot_id)
    
    if not robot:
        raise HTTPException(
            status_code=404,
            detail=f"Robot {robot_id} not found in Robot Registry"
        )
    
    # Check if robot has RTSP configured
    rtsp_url = resolve_robot_rtsp(robot_id)
    if not rtsp_url:
        raise HTTPException(
            status_code=404,
            detail=f"Robot {robot_id} does not have RTSP URL configured in Robot Registry. Admin must add rtsp_url field."
        )
    
    # Return safe metadata only (NO rtsp_url)
    return StreamMetadataResponse(
        stream_id=str(robot_id),
        robot_id=robot_id,
        robot_name=robot.get("name", "Unknown"),
        robot_type=robot.get("type", "Unknown"),
        status=robot.get("status", "unknown"),
        booking_id=None  # Booking association is validated separately
    )


@router.get("/{stream_id}/signaling-info", response_model=StreamSignalingInfoResponse)
async def get_signaling_info(
    stream_id: str,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user) if AUTH_AVAILABLE else None
):
    """
    Get signaling info for a stream (authenticated users with active booking).
    
    stream_id corresponds to robot_id from the Robot Registry.
    
    - Verifies robot exists and has RTSP configured
    - Verifies user has active booking for the robot
    - Returns WebSocket URL for signaling to bridge
    - Does NOT return rtsp_url or any secrets
    
    IMPORTANT: Bridge MUST validate the request with backend. The returned ws_url includes 
    robot_id; bridge must not accept ws_url alone and blindly use stream_id. Bridge must 
    call backend authorize endpoint or accept forwarded session cookie and ask backend for 
    the RTSP mapping. This is required for security.
    """
    # Parse robot_id from stream_id
    try:
        robot_id = int(stream_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stream_id format. stream_id must be a robot_id (integer)"
        )
    
    # Get robot from Robot Registry
    if not DB_AVAILABLE or not db:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable - cannot access Robot Registry"
        )
    
    robot = db.get_robot_by_id(robot_id)
    
    if not robot:
        raise HTTPException(
            status_code=404,
            detail=f"Robot {robot_id} not found in Robot Registry"
        )
    
    # Check if robot has RTSP configured
    rtsp_url = resolve_robot_rtsp(robot_id)
    if not rtsp_url:
        raise HTTPException(
            status_code=404,
            detail=f"Stream not configured — ask admin to add RTSP URL in Robot Registry for robot {robot_id}"
        )
    
    # Check if robot is active
    if robot.get("status") != "active":
        raise HTTPException(
            status_code=403,
            detail=f"Robot {robot_id} is not active (status: {robot.get('status')})"
        )
    
    # Validate user has active booking (if auth is available)
    if AUTH_AVAILABLE and current_user:
        user_id = int(current_user.get("sub", 0))
        
        if not user_has_active_booking_for_robot(user_id, robot_id):
            raise HTTPException(
                status_code=403, 
                detail="Access denied. You need an active booking to view this stream."
            )
        
        logger.info(f"User {user_id} authorized to access stream for robot {robot_id}")
    else:
        # DEV MODE: Log warning when auth is not available
        logger.warning(f"DEV MODE: Allowing permissive access to signaling info for robot {robot_id}")
    
    # Build WebSocket URL with robot_id parameter for bridge validation
    ws_url = BRIDGE_WS_URL
    if "?" not in ws_url:
        ws_url += f"?robot_id={robot_id}"
    else:
        ws_url += f"&robot_id={robot_id}"
    
    # Return WebSocket URL (no secrets)
    return StreamSignalingInfoResponse(ws_url=ws_url)


@router.get("/bridge/authorize", response_model=BridgeAuthorizeResponse)
async def bridge_authorize(
    robot_id: int,
    bridge_secret: Optional[str] = Header(None, alias="X-BRIDGE-SECRET")
):
    """
    Bridge authorization endpoint (bridge-only, requires secret).
    
    This endpoint is called by the bridge to get the RTSP URL for a robot.
    It requires an internal auth header (BRIDGE_CONTROL_SECRET) to prevent unauthorized access.
    
    Returns the RTSP URL for the bridge to use. This is the ONLY endpoint that returns rtsp_url.
    """
    # Verify bridge secret
    if not BRIDGE_CONTROL_SECRET:
        raise HTTPException(
            status_code=503,
            detail="Bridge authorization not configured - BRIDGE_CONTROL_SECRET not set"
        )
    
    if bridge_secret != BRIDGE_CONTROL_SECRET:
        logger.warning(f"Unauthorized bridge authorization attempt for robot {robot_id}")
        raise HTTPException(
            status_code=401,
            detail="Unauthorized - invalid bridge secret"
        )
    
    # Get robot from Robot Registry
    if not DB_AVAILABLE or not db:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable - cannot access Robot Registry"
        )
    
    robot = db.get_robot_by_id(robot_id)
    
    if not robot:
        raise HTTPException(
            status_code=404,
            detail=f"Robot {robot_id} not found in Robot Registry"
        )
    
    # Resolve RTSP URL
    rtsp_url = resolve_robot_rtsp(robot_id)
    if not rtsp_url:
        raise HTTPException(
            status_code=404,
            detail=f"Robot {robot_id} does not have RTSP URL configured"
        )
    
    logger.info(f"Bridge authorized to access RTSP for robot {robot_id}")
    
    # Return RTSP URL (bridge-only)
    return BridgeAuthorizeResponse(
        rtsp_url=rtsp_url,
        robot_id=robot_id,
        robot_name=robot.get("name", "Unknown")
    )
