import os
import time
import json
import asyncio
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from pathlib import Path

# WebRTC imports
from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
from aiortc.contrib.media import MediaPlayer, MediaRelay

# Import environment support
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from database import DatabaseManager
from auth import auth_manager, get_current_user, require_admin
from services.service_manager import AdminServiceManager
from services.theia_service import TheiaContainerManager

# Configure logging based on environment
def setup_logging():
    log_level = logging.DEBUG if ENVIRONMENT == 'development' else logging.INFO
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(),  # Console output
            logging.FileHandler(log_dir / "backend.log", mode='a')  # File output
        ]
    )
    return logging.getLogger(__name__)

# Environment-based configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
logger = setup_logging()

# CORS configuration based on environment
def get_cors_origins():
    if ENVIRONMENT == 'production':
        production_origins = os.getenv('PRODUCTION_CORS_ORIGINS', '')
        if production_origins:
            return production_origins.split(',')
        else:
            # Fallback to VPS IP if no production origins specified
            vps_url = os.getenv('VPS_URL', 'http://172.232.105.47')
            return [vps_url, f"{vps_url}:3000", f"{vps_url}:5173"]
    else:
        # Development origins
        dev_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173')
        return dev_origins.split(',')

CORS_ORIGINS = get_cors_origins()
logger.info(f"Environment: {ENVIRONMENT}")
logger.info(f"CORS Origins: {CORS_ORIGINS}")

# Initialize database
db = DatabaseManager()

# Initialize service manager
service_manager = AdminServiceManager(db)
theia_manager = TheiaContainerManager()

# Global WebRTC state management
peer_connections: Dict[str, RTCPeerConnection] = {}
media_relay = MediaRelay()
rtsp_players: Dict[str, MediaPlayer] = {}  # Cache RTSP players by robot_id
peer_ice_candidates: Dict[str, List[Dict]] = {}  # Store server ICE candidates per peer
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events"""
    logger.info("🚀 Admin Backend API starting up...")
    logger.info("📊 Database initialized")
    
    # Log service status
    status = service_manager.get_service_status()
    logger.info(f"🔧 Services status: {status['overall_status']}")
    logger.info(f"📋 Core services available: {status['core_services_available']}")
    
    if not status['core_services_available']:
        logger.error("❌ Critical: Core services not available!")
    
    yield
    
    # Cleanup WebRTC connections on shutdown
    logger.info("🧹 Cleaning up WebRTC connections...")
    for peer_id in list(peer_connections.keys()):
        await cleanup_peer_connection(peer_id)
    
    # Cleanup RTSP players
    for robot_id, player in rtsp_players.items():
        try:
            player.audio = None
            player.video = None
            logger.info(f"Cleaned up RTSP player for robot {robot_id}")
        except Exception as e:
            logger.error(f"Error cleaning up RTSP player for robot {robot_id}: {e}")
    rtsp_players.clear()
    
    logger.info("🛑 Admin Backend API shutting down...")

# Create FastAPI app with lifespan
app = FastAPI(title="Robot Admin Backend API", version="1.0.0", lifespan=lifespan)

# Global exception handler for better error logging
@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    logger.error(f"Internal server error: {str(exc)}", exc_info=True)
    return {"error": "Internal server error", "detail": "Please check server logs"}

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return {"error": "Request failed", "detail": exc.detail}

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Models

# Authentication Models
class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: str

# Booking Models
class BookingCreate(BaseModel):
    robot_type: str
    date: str
    start_time: str
    end_time: str

class BookingResponse(BaseModel):
    id: int
    user_id: int
    robot_type: str
    date: str
    start_time: str
    end_time: str
    status: str
    created_at: str

class BookingUpdate(BaseModel):
    status: str

# Message Models
class MessageCreate(BaseModel):
    name: str
    email: str
    message: str

class MessageResponse(BaseModel):
    id: int
    name: str
    email: str
    message: str
    status: str
    created_at: str

class MessageUpdate(BaseModel):
    status: str

# Announcement Models
class AnnouncementCreate(BaseModel):
    title: str
    content: str
    priority: str = "normal"

class AnnouncementUpdate(BaseModel):
    title: str
    content: str
    priority: str
    is_active: bool

class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    priority: str
    is_active: bool
    created_by: int
    created_by_name: str
    created_at: str
    updated_at: str

# Robot Registry Models
class RobotCreate(BaseModel):
    name: str
    type: str
    rtsp_url: Optional[str] = None
    code_api_url: Optional[str] = None
    status: str = 'active'

class RobotUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    rtsp_url: Optional[str] = None
    code_api_url: Optional[str] = None
    status: Optional[str] = None

class RobotStatusUpdate(BaseModel):
    status: str

class RobotResponse(BaseModel):
    id: int
    name: str
    type: str
    rtsp_url: Optional[str] = None
    code_api_url: Optional[str] = None
    status: str
    created_at: str
    updated_at: Optional[str] = None

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Robot Programming Console API", "version": "1.0.0"}

# Authentication Endpoints
@app.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    """Register a new user"""
    auth_service = service_manager.get_auth_service()
    return auth_service.register_user(user_data.name, user_data.email, user_data.password)

@app.post("/auth/login", response_model=TokenResponse)
async def login(user_data: UserLogin):
    """Login user"""
    auth_service = service_manager.get_auth_service()
    return auth_service.login_user(user_data.email, user_data.password)

@app.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    auth_service = service_manager.get_auth_service()
    user = auth_service.get_user_by_token(current_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user)

# Booking Endpoints
@app.post("/bookings", response_model=BookingResponse)
async def create_booking(booking_data: BookingCreate, current_user: dict = Depends(get_current_user)):
    """Create a new booking"""
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])
    booking = booking_service.create_booking(
        user_id=user_id,
        robot_type=booking_data.robot_type,
        date=booking_data.date,
        start_time=booking_data.start_time,
        end_time=booking_data.end_time
    )
    return BookingResponse(**booking)

@app.get("/bookings", response_model=List[BookingResponse])
async def get_user_bookings(current_user: dict = Depends(get_current_user)):
    """Get current user's bookings"""
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])
    bookings = booking_service.get_user_bookings(user_id)
    return [BookingResponse(**booking) for booking in bookings]

@app.get("/my-bookings", response_model=List[BookingResponse])
async def get_my_active_bookings(current_user: dict = Depends(get_current_user)):
    """Get current user's active bookings"""
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])
    bookings = booking_service.get_user_bookings(user_id)
    # Filter for active bookings only
    active_bookings = [booking for booking in bookings if booking["status"] == "active"]
    return [BookingResponse(**booking) for booking in active_bookings]

@app.get("/bookings/all", response_model=List[dict])
async def get_all_bookings(current_user: dict = Depends(require_admin)):
    """Get all bookings (admin only)"""
    booking_service = service_manager.get_booking_service()
    bookings = booking_service.get_all_bookings()
    return bookings

@app.put("/bookings/{booking_id}", response_model=dict)
async def update_booking(booking_id: int, booking_data: BookingUpdate, current_user: dict = Depends(require_admin)):
    """Update booking status (admin only)"""
    booking_service = service_manager.get_booking_service()
    booking = booking_service.update_booking_status(booking_id, booking_data.status)
    return {"message": "Booking updated successfully", "booking": booking}

@app.delete("/bookings/{booking_id}")
async def delete_booking(booking_id: int, current_user: dict = Depends(require_admin)):
    """Delete booking (admin only)"""
    success = db.delete_booking(booking_id)
    if not success:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {"message": "Booking deleted successfully"}

@app.get("/bookings/schedule")
async def get_booking_schedule(start_date: str, end_date: str):
    """Get booking schedule for date range (public)"""
    bookings = db.get_bookings_for_date_range(start_date, end_date)
    return {"bookings": bookings}

# Admin Endpoints
@app.get("/admin/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(require_admin)):
    """Get all users (admin only)"""
    users = db.get_all_users()
    return [UserResponse(**user) for user in users]

@app.get("/admin/stats")
async def get_admin_stats(current_user: dict = Depends(require_admin)):
    """Get admin dashboard statistics"""
    users = db.get_all_users()
    bookings = db.get_all_bookings()
    messages = db.get_all_messages()
    announcements = db.get_all_announcements()
    robots = db.get_all_robots()
    
    total_users = len(users)
    total_bookings = len(bookings)
    active_bookings = len([b for b in bookings if b["status"] == "active"])
    total_messages = len(messages)
    unread_messages = len([m for m in messages if m["status"] == "unread"])
    total_announcements = len(announcements)
    active_announcements = len([a for a in announcements if a["is_active"]])
    total_robots = len(robots)
    
    return {
        "total_users": total_users,
        "total_bookings": total_bookings,
        "active_bookings": active_bookings,
        "total_messages": total_messages,
        "unread_messages": unread_messages,
        "total_announcements": total_announcements,
        "active_announcements": active_announcements,
        "total_robots": total_robots,
        "recent_users": users[:5],  # 5 most recent users
        "recent_bookings": bookings[:10],  # 10 most recent bookings
        "recent_messages": messages[:10]  # 10 most recent messages
    }

# Robot Admin Endpoints
@app.post("/admin/robots", response_model=RobotResponse)
async def create_robot(robot_data: RobotCreate, current_user: dict = Depends(require_admin)):
    """Create a new robot (admin only)"""
    robot = db.create_robot(
        name=robot_data.name,
        robot_type=robot_data.type,
        rtsp_url=robot_data.rtsp_url,
        code_api_url=robot_data.code_api_url,
        status=robot_data.status
    )
    return RobotResponse(**robot)

@app.get("/admin/robots", response_model=List[RobotResponse])
async def get_all_robots_admin(current_user: dict = Depends(require_admin)):
    """Get all robots (admin only)"""
    robots = db.get_all_robots()
    return [RobotResponse(**robot) for robot in robots]

@app.put("/admin/robots/{robot_id}", response_model=RobotResponse)
async def update_robot(robot_id: int, robot_data: RobotUpdate, current_user: dict = Depends(require_admin)):
    """Update a robot (admin only)"""
    success = db.update_robot(
        robot_id=robot_id,
        name=robot_data.name,
        robot_type=robot_data.type,
        rtsp_url=robot_data.rtsp_url,
        code_api_url=robot_data.code_api_url,
        status=robot_data.status
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    updated_robot = db.get_robot_by_id(robot_id)
    if not updated_robot:
        raise HTTPException(status_code=404, detail="Robot not found after update")
    
    return RobotResponse(**updated_robot)

@app.delete("/admin/robots/{robot_id}")
async def delete_robot(robot_id: int, current_user: dict = Depends(require_admin)):
    """Delete a robot (admin only)"""
    success = db.delete_robot(robot_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    return {"message": "Robot deleted successfully"}

@app.patch("/admin/robots/{robot_id}/status")
async def update_robot_status(robot_id: int, status_data: RobotStatusUpdate, current_user: dict = Depends(require_admin)):
    """Update robot status (admin only)"""
    if status_data.status not in ['active', 'inactive']:
        raise HTTPException(status_code=400, detail="Status must be 'active' or 'inactive'")
    
    success = db.update_robot(robot_id=robot_id, status=status_data.status)
    
    if not success:
        raise HTTPException(status_code=404, detail="Robot not found")
    
    updated_robot = db.get_robot_by_id(robot_id)
    if not updated_robot:
        raise HTTPException(status_code=404, detail="Robot not found after update")
    
    logger.info(f"Robot status updated - Robot: {updated_robot.get('name')} (ID: {robot_id}), Status: {status_data.status}")
    return {"message": f"Robot status updated to {status_data.status}", "robot": RobotResponse(**updated_robot)}

# Message Endpoints
@app.post("/messages", response_model=MessageResponse)
async def create_message(message_data: MessageCreate):
    """Submit a contact message (public)"""
    message = db.create_message(
        name=message_data.name,
        email=message_data.email,
        message=message_data.message
    )
    return MessageResponse(**message)

@app.get("/messages", response_model=List[MessageResponse])
async def get_all_messages(current_user: dict = Depends(require_admin)):
    """Get all contact messages (admin only)"""
    messages = db.get_all_messages()
    return [MessageResponse(**message) for message in messages]

@app.put("/messages/{message_id}/status")
async def update_message_status(message_id: int, message_data: MessageUpdate, current_user: dict = Depends(require_admin)):
    """Update message status (admin only)"""
    success = db.update_message_status(message_id, message_data.status)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Message status updated successfully"}

@app.delete("/messages/{message_id}")
async def delete_message(message_id: int, current_user: dict = Depends(require_admin)):
    """Delete a message (admin only)"""
    success = db.delete_message(message_id)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found")
    return {"message": "Message deleted successfully"}

# Announcement Endpoints
@app.post("/announcements", response_model=AnnouncementResponse)
async def create_announcement(announcement_data: AnnouncementCreate, current_user: dict = Depends(require_admin)):
    """Create a new announcement (admin only)"""
    user_id = int(current_user["sub"])
    announcement = db.create_announcement(
        title=announcement_data.title,
        content=announcement_data.content,
        priority=announcement_data.priority,
        created_by=user_id
    )
    # Add the created_by_name for the response
    user = db.get_user_by_id(user_id)
    announcement["created_by_name"] = user["name"] if user else "Unknown"
    return AnnouncementResponse(**announcement)

@app.get("/announcements", response_model=List[AnnouncementResponse])
async def get_all_announcements(current_user: dict = Depends(require_admin)):
    """Get all announcements (admin only)"""
    announcements = db.get_all_announcements()
    return [AnnouncementResponse(**announcement) for announcement in announcements]

@app.get("/announcements/active")
async def get_active_announcements():
    """Get active announcements (public)"""
    announcements = db.get_active_announcements()
    return {"announcements": announcements}

@app.put("/announcements/{announcement_id}", response_model=dict)
async def update_announcement(announcement_id: int, announcement_data: AnnouncementUpdate, current_user: dict = Depends(require_admin)):
    """Update an announcement (admin only)"""
    success = db.update_announcement(
        announcement_id=announcement_id,
        title=announcement_data.title,
        content=announcement_data.content,
        priority=announcement_data.priority,
        is_active=announcement_data.is_active
    )
    if not success:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"message": "Announcement updated successfully"}

@app.delete("/announcements/{announcement_id}")
async def delete_announcement(announcement_id: int, current_user: dict = Depends(require_admin)):
    """Delete an announcement (admin only)"""
    success = db.delete_announcement(announcement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return {"message": "Announcement deleted successfully"}

# Service Health Check Endpoints
@app.get("/health")
async def health_check():
    """Get overall system health"""
    status = service_manager.get_service_status()
    return {
        "status": status['overall_status'],
        "timestamp": time.time(),
        "core_services": status['core_services_available'],
        "services": status['services']
    }

@app.get("/health/services")
async def services_status():
    """Get detailed service status"""
    return service_manager.get_service_status()

@app.get("/health/features")
async def available_features():
    """Get available features based on service status"""
    return service_manager.get_available_features()

@app.get("/robots")
def get_available_robots():
    """Get list of available robot types from registry"""
    try:
        # Get only active robots from registry
        robots = db.get_active_robots()
        
        # Extract just the types for backward compatibility
        robot_types = list(set(robot["type"] for robot in robots))
        
        # Fall back to hardcoded list if no robots in registry
        if not robot_types:
            robot_types = ["turtlebot", "arm", "hand"]
        
        booking_service = service_manager.get_booking_service()
        return {
            "robots": robot_types,
            "details": booking_service.get_available_robots(),
            "registry": robots  # Include full registry data for admin use
        }
    except Exception as e:
        # Fallback to original hardcoded response if registry fails
        logger.error(f"Error accessing robot registry: {e}")
        booking_service = service_manager.get_booking_service()
        return {
            "robots": ["turtlebot", "arm", "hand"],
            "details": booking_service.get_available_robots()
        }

# Video serving and access control
@app.get("/videos/{robot_type}")
async def get_video(robot_type: str, current_user: dict = Depends(get_current_user)):
    """Serve video files for active booking sessions only"""
    # Check if user has active booking session for this robot type
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])
    
    # Check if user has active session (during their booking time)
    has_active_session = booking_service.has_active_session(user_id, robot_type)
    
    if not has_active_session:
        # Also check for admin access
        is_admin = current_user.get("role") == "admin"
        if not is_admin:
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. Video access requires an active booking session for {robot_type} robot during your scheduled time."
            )
    
    # Define video file mapping
    video_files = {
        "turtlebot": "turtlebot_simulation.mp4",
        "arm": "arm_simulation.mp4", 
        "hand": "hand_simulation.mp4"
    }
    
    if robot_type not in video_files:
        raise HTTPException(status_code=404, detail=f"Video not found for robot type: {robot_type}")
    
    video_path = Path("videos") / video_files[robot_type]
    
    if not video_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"Video file not found: {video_files[robot_type]}. Please contact administrator."
        )
    
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=video_files[robot_type]
    )

@app.get("/access/check")
async def check_access(current_user: dict = Depends(get_current_user)):
    """Check if user has access to Monaco Editor and VPS iframe"""
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])
    
    # Get user's bookings
    bookings = booking_service.get_user_bookings(user_id)
    
    # Check if user has at least one completed booking
    has_completed_booking = any(
        booking["status"] == "completed" for booking in bookings
    )
    
    return {
        "has_access": has_completed_booking,
        "user_id": user_id,
        "completed_bookings": [
            booking for booking in bookings if booking["status"] == "completed"
        ]
    }

@app.get("/videos/available")
async def get_available_videos(current_user: dict = Depends(get_current_user)):
    """Get list of videos available to the current user"""
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])
    
    # Get user's completed bookings
    bookings = booking_service.get_user_bookings(user_id)
    completed_bookings = [b for b in bookings if b["status"] == "completed"]
    
    # Get unique robot types from completed bookings
    available_robot_types = list(set(
        booking["robot_type"] for booking in completed_bookings
    ))
    
    return {
        "available_videos": available_robot_types,
        "completed_bookings": completed_bookings
    }

# Eclipse Theia Container Management Endpoints

@app.get("/theia/status")
async def get_theia_status(current_user: dict = Depends(get_current_user)):
    """Get status of user's Theia container"""
    user_id = int(current_user["sub"])
    status = theia_manager.get_container_status(user_id)
    return status

@app.post("/theia/start")
async def start_theia_container(current_user: dict = Depends(get_current_user)):
    """Start user's Theia container"""
    # Check if user has access (completed booking)
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])
    
    # Get user's bookings
    bookings = booking_service.get_user_bookings(user_id)
    
    # Check if user has at least one completed booking
    has_completed_booking = any(
        booking["status"] == "completed" for booking in bookings
    )
    
    if not has_completed_booking:
        raise HTTPException(
            status_code=403, 
            detail="You need to complete a booking before accessing the development environment"
        )
    
    result = theia_manager.start_container(user_id)
    
    if result.get("success"):
        return {
            "message": "Theia container started successfully",
            "status": result.get("status"),
            "url": result.get("url"),
            "port": result.get("port")
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to start Theia container: {result.get('error', 'Unknown error')}"
        )

@app.post("/theia/stop")
async def stop_theia_container(current_user: dict = Depends(get_current_user)):
    """Stop user's Theia container"""
    user_id = int(current_user["sub"])
    result = theia_manager.stop_container(user_id)
    
    if result.get("success"):
        return {"message": "Theia container stopped successfully"}
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to stop Theia container: {result.get('error', 'Unknown error')}"
        )

@app.post("/theia/restart")
async def restart_theia_container(current_user: dict = Depends(get_current_user)):
    """Restart user's Theia container"""
    user_id = int(current_user["sub"])
    result = theia_manager.restart_container(user_id)
    
    if result.get("success"):
        return {
            "message": "Theia container restarted successfully",
            "status": result.get("status"),
            "url": result.get("url"),
            "port": result.get("port")
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to restart Theia container: {result.get('error', 'Unknown error')}"
        )

@app.get("/theia/containers")
async def list_theia_containers(current_user: dict = Depends(require_admin)):
    """List all Theia containers (admin only)"""
    containers = theia_manager.list_user_containers()
    return {"containers": containers}

# Additional Theia Admin Endpoints
@app.post("/theia/admin/stop/{user_id}")
async def admin_stop_theia_container(user_id: int, current_user: dict = Depends(require_admin)):
    """Stop any user's Theia container (admin only)"""
    result = theia_manager.stop_container(user_id)
    
    if result.get("success"):
        return {"message": f"Theia container for user {user_id} stopped successfully"}
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to stop Theia container for user {user_id}: {result.get('error', 'Unknown error')}"
        )

@app.post("/theia/admin/restart/{user_id}")
async def admin_restart_theia_container(user_id: int, current_user: dict = Depends(require_admin)):
    """Restart any user's Theia container (admin only)"""
    result = theia_manager.restart_container(user_id)
    
    if result.get("success"):
        return {
            "message": f"Theia container for user {user_id} restarted successfully",
            "status": result.get("status"),
            "url": result.get("url"),
            "port": result.get("port")
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to restart Theia container for user {user_id}: {result.get('error', 'Unknown error')}"
        )

@app.get("/theia/admin/status/{user_id}")
async def admin_get_theia_status(user_id: int, current_user: dict = Depends(require_admin)):
    """Get any user's Theia container status (admin only)"""
    status = theia_manager.get_container_status(user_id)
    return {"user_id": user_id, **status}

# WebSocket endpoint for future robot communication
@app.websocket("/ws/robot/{user_id}")
async def robot_websocket(websocket, user_id: int):
    """WebSocket endpoint for robot communication (future enhancement)"""
    await websocket.accept()
    try:
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": f"Connected to robot WebSocket for user {user_id}",
            "user_id": user_id
        }))
        
        # TODO: Implement robot communication protocol
        # This will be used for:
        # - Real-time robot status updates
        # - Streaming robot sensor data
        # - Sending control commands to robots
        
        while True:
            data = await websocket.receive_text()
            # Echo back for now - replace with robot communication
            await websocket.send_text(json.dumps({
                "type": "echo",
                "data": data,
                "timestamp": time.time()
            }))
            
    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
    finally:
        await websocket.close()

# Robot Code Execution Endpoint
class RobotExecuteRequest(BaseModel):
    code: str
    robot_type: Optional[str] = None  # Optional, will be resolved from active booking
    language: str = "python"
    filename: Optional[str] = None  # Optional filename for the code

@app.post("/robot/execute")
async def execute_robot_code(request: RobotExecuteRequest, current_user: dict = Depends(get_current_user)):
    """Execute robot code and return simulation results"""
    import aiohttp
    import re
    
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])
    
    # Get user's active bookings
    bookings = booking_service.get_user_bookings(user_id)
    active_bookings = [booking for booking in bookings if booking["status"] == "active"]
    
    if not active_bookings:
        raise HTTPException(
            status_code=403, 
            detail="You need an active booking to execute robot code."
        )
    
    # If robot_type is provided, verify user has booking for it
    # If not provided, use the first active booking
    if request.robot_type:
        has_active_booking = any(
            booking["robot_type"] == request.robot_type
            for booking in active_bookings
        )
        if not has_active_booking:
            raise HTTPException(
                status_code=403,
                detail=f"You don't have an active booking for {request.robot_type} robot."
            )
        robot_type = request.robot_type
    else:
        # Use the first active booking
        robot_type = active_bookings[0]["robot_type"]
    
    # Get active robot details from database
    robot = db.get_active_robot_by_type(robot_type)
    if not robot:
        raise HTTPException(
            status_code=404,
            detail=f"Active robot of type {robot_type} not found in registry or robot is inactive."
        )
    
    code_api_url = robot.get("code_api_url")
    robot_id = robot.get("id")
    robot_name = robot.get("name")
    
    # Enhanced logging with robot details
    logger.info(f"Robot code execution request - User: {user_id}, Robot: {robot_name} (ID: {robot_id}, Type: {robot_type}), Code API: {code_api_url}")
    
    if not code_api_url:
        # Fallback to simulation mode if no code API URL is configured
        logger.warning(f"No code_api_url configured for robot {robot_name} (ID: {robot_id}, Type: {robot_type}), using fallback simulation")
        return await _fallback_simulation(request, user_id, robot_type)
    
    try:
        # Sanitize filename if provided
        filename = request.filename or "main.py"
        filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)  # Remove potentially dangerous characters
        if not filename.endswith(('.py', '.cpp', '.c', '.h')):
            filename += '.py'  # Default to Python extension
        
        # Sanitize code content (basic validation)
        if len(request.code) > 100000:  # 100KB limit
            raise HTTPException(status_code=413, detail="Code too large (max 100KB)")
        
        # Execute code via external robot API
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            # Upload code
            upload_payload = {
                "filename": filename,
                "content": request.code,
                "language": request.language
            }
            
            try:
                async with session.post(f"{code_api_url}/upload", json=upload_payload) as upload_response:
                    if upload_response.status != 200:
                        upload_text = await upload_response.text()
                        logger.error(f"Failed to upload code to robot {robot_name} (ID: {robot_id}) at {code_api_url}/upload: {upload_response.status} - {upload_text}")
                        raise HTTPException(
                            status_code=502,
                            detail=f"Failed to upload code to robot: HTTP {upload_response.status}"
                        )
                    upload_result = await upload_response.json()
            except aiohttp.ClientConnectorError:
                logger.error(f"Failed to connect to robot API for {robot_name} (ID: {robot_id}) at {code_api_url}")
                raise HTTPException(
                    status_code=503,
                    detail="Robot API is unreachable. Please try again later."
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout connecting to robot API for {robot_name} (ID: {robot_id}) at {code_api_url}")
                raise HTTPException(
                    status_code=504,
                    detail="Robot API timeout. Please try again later."
                )
            
            # Execute code
            execute_payload = {
                "filename": filename,
                "language": request.language
            }
            
            try:
                async with session.post(f"{code_api_url}/run", json=execute_payload) as execute_response:
                    if execute_response.status != 200:
                        execute_text = await execute_response.text()
                        logger.error(f"Failed to execute code on {code_api_url}/run: {execute_response.status} - {execute_text}")
                        raise HTTPException(
                            status_code=502,
                            detail=f"Failed to execute code on robot: HTTP {execute_response.status}"
                        )
                    execute_result = await execute_response.json()
            except aiohttp.ClientConnectorError:
                logger.error(f"Failed to connect to robot API at {code_api_url}")
                raise HTTPException(
                    status_code=503,
                    detail="Robot API is unreachable. Please try again later."
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout executing code on robot API at {code_api_url}")
                raise HTTPException(
                    status_code=504,
                    detail="Robot execution timeout. Please try again later."
                )
        
        # Generate execution ID
        execution_id = f"exec_{user_id}_{int(time.time())}"
        
        # Return successful execution result
        return {
            "success": True,
            "execution_id": execution_id,
            "robot_type": robot_type,
            "robot_name": robot["name"],
            "language": request.language,
            "timestamp": time.time(),
            "upload_result": upload_result,
            "execute_result": execute_result,
            "simulation_type": "external_api"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error executing robot code for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute robot code: {str(e)}"
        )

async def _fallback_simulation(request: RobotExecuteRequest, user_id: int, robot_type: str):
    """Fallback simulation when no external robot API is configured"""
    # Generate a unique execution ID
    execution_id = f"exec_{user_id}_{int(time.time())}"
    
    # Check if we have a simulation video for this robot type
    video_files = {
        "turtlebot": "turtlebot_simulation.mp4",
        "arm": "arm_simulation.mp4", 
        "hand": "hand_simulation.mp4"
    }
    
    video_file = video_files.get(robot_type)
    video_url = None
    
    if video_file:
        video_path = Path("videos") / video_file
        if video_path.exists():
            video_url = f"/videos/{robot_type}"
    
    # Simulate processing time
    await asyncio.sleep(1)
    
    return {
        "success": True,
        "execution_id": execution_id,
        "video_url": video_url,
        "simulation_type": "fallback",
        "message": "Code executed successfully in fallback mode",
        "robot_type": robot_type,
        "language": request.language,
        "timestamp": time.time()
    }

# WebRTC Signaling Endpoints
class WebRTCOffer(BaseModel):
    robot_id: Optional[int] = None
    robot_type: Optional[str] = None  # Support both robot_id and robot_type for backward compatibility
    sdp: str
    type: str = "offer"

class ICECandidate(BaseModel):
    peer_id: str
    candidate: Dict[str, Any]  # Full RTCIceCandidate object with candidate, sdpMLineIndex, sdpMid fields

# Helper functions for WebRTC management
async def get_robot_rtsp_url(robot_id: int) -> str:
    """Get RTSP URL for a robot from the database registry"""
    robot = db.get_robot_by_id(robot_id)
    if not robot:
        raise HTTPException(status_code=404, detail=f"Robot with ID {robot_id} not found")
    
    rtsp_url = robot.get('rtsp_url')
    if not rtsp_url:
        raise HTTPException(status_code=404, detail=f"Robot {robot_id} does not have an RTSP URL configured")
    
    return rtsp_url

async def resolve_robot_id(offer: WebRTCOffer) -> int:
    """Resolve robot_id from either robot_id or robot_type in the offer"""
    if offer.robot_id is not None:
        return offer.robot_id
    
    if offer.robot_type is not None:
        # Find robot by type - get the first robot of this type
        robots = db.get_all_robots()
        for robot in robots:
            if robot.get('type') == offer.robot_type:
                return robot['id']
        raise HTTPException(
            status_code=404, 
            detail=f"No robot found with type '{offer.robot_type}'"
        )
    
    raise HTTPException(
        status_code=400, 
        detail="Either robot_id or robot_type must be provided"
    )

async def get_or_create_rtsp_player(robot_id: int) -> MediaPlayer:
    """Get cached RTSP player or create new one for robot"""
    if robot_id not in rtsp_players:
        rtsp_url = await get_robot_rtsp_url(robot_id)
        robot = db.get_robot_by_id(robot_id)
        robot_name = robot.get("name", "Unknown") if robot else "Unknown"
        robot_type = robot.get("type", "Unknown") if robot else "Unknown"
        logger.info(f"Creating new RTSP player for robot {robot_name} (ID: {robot_id}, Type: {robot_type}): {rtsp_url}")
        rtsp_players[robot_id] = MediaPlayer(rtsp_url)
    return rtsp_players[robot_id]

async def cleanup_peer_connection(peer_id: str):
    """Clean up a peer connection and remove from tracking"""
    if peer_id in peer_connections:
        pc = peer_connections[peer_id]
        await pc.close()
        del peer_connections[peer_id]
        logger.info(f"Cleaned up peer connection: {peer_id}")
    
    # Clean up ICE candidates
    if peer_id in peer_ice_candidates:
        del peer_ice_candidates[peer_id]
        logger.debug(f"Cleaned up ICE candidates for peer: {peer_id}")

async def has_booking_for_robot(user_id: int, robot_id: int) -> bool:
    """Check if user has active booking for the robot"""
    booking_service = service_manager.get_booking_service()
    
    # Get robot info to determine robot type
    robot = db.get_robot_by_id(robot_id)
    if not robot:
        return False
    
    robot_type = robot.get('type')
    if not robot_type:
        return False
    
    return booking_service.has_active_session(user_id, robot_type)

@app.post("/webrtc/offer")
async def handle_webrtc_offer(offer: WebRTCOffer, current_user: dict = Depends(get_current_user)):
    """Handle WebRTC SDP offer from client"""
    user_id = int(current_user["sub"])
    
    # Resolve robot_id from offer (supports both robot_id and robot_type)
    robot_id = await resolve_robot_id(offer)
    
    # Validate user has active booking session for this robot
    if not await has_booking_for_robot(user_id, robot_id):
        robot = db.get_robot_by_id(robot_id)
        robot_type = robot.get('type', 'unknown') if robot else 'unknown'
        raise HTTPException(
            status_code=403,
            detail=f"No active booking session for robot {robot_id} ({robot_type}). Video access requires an active session during your booking time."
        )
    
    try:
        # Create unique peer ID for this connection
        peer_id = str(uuid.uuid4())
        
        # Create RTCPeerConnection
        pc = RTCPeerConnection()
        peer_connections[peer_id] = pc
        peer_ice_candidates[peer_id] = []  # Initialize ICE candidates list
        
        # Get RTSP stream from robot and set up media relay
        rtsp_player = await get_or_create_rtsp_player(robot_id)
        
        # Add video track from RTSP stream via media relay
        if rtsp_player.video:
            video_track = media_relay.subscribe(rtsp_player.video)
            pc.addTrack(video_track)
        
        # Set remote description from client offer
        await pc.setRemoteDescription(RTCSessionDescription(sdp=offer.sdp, type=offer.type))
        
        # Create answer
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        
        # Set up connection state monitoring
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            logger.info(f"Connection state for {peer_id}: {pc.connectionState}")
            if pc.connectionState in ["failed", "closed"]:
                await cleanup_peer_connection(peer_id)
        
        # Note: aiortc doesn't emit icecandidate events in the same way as browser WebRTC
        # ICE candidates are handled internally during the setLocalDescription process
        # Server-side ICE candidates will be collected from the localDescription
        
        robot = db.get_robot_by_id(robot_id)
        robot_name = robot.get("name", "Unknown") if robot else "Unknown"
        robot_type = robot.get("type", "Unknown") if robot else "Unknown"
        rtsp_url = robot.get("rtsp_url", "Unknown") if robot else "Unknown"
        
        logger.info(f"Created WebRTC offer answer for robot {robot_name} (ID: {robot_id}, Type: {robot_type}), RTSP: {rtsp_url}, peer {peer_id}")
        
        # Extract server ICE candidates from the SDP for later retrieval
        if pc.localDescription:
            # Parse SDP to extract ICE candidates
            sdp_lines = pc.localDescription.sdp.split('\n')
            for line in sdp_lines:
                if line.startswith('a=candidate:'):
                    candidate_dict = {
                        "candidate": line.strip(),
                        "sdpMLineIndex": 0,  # This would need proper parsing for multiple media lines
                        "sdpMid": "0",  # This would need proper parsing
                        "timestamp": time.time()
                    }
                    peer_ice_candidates[peer_id].append(candidate_dict)
                    logger.debug(f"Extracted ICE candidate for peer {peer_id}: {line[:50]}...")
        
        return {
            "peer_id": peer_id,
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }
        
    except Exception as e:
        # Clean up on error
        if peer_id in peer_connections:
            await cleanup_peer_connection(peer_id)
        logger.error(f"Error handling WebRTC offer for robot {robot_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process WebRTC offer: {str(e)}")

@app.get("/webrtc/answer")
async def get_webrtc_answer(robot_type: str = None, peer_id: str = None, current_user: dict = Depends(get_current_user)):
    """Get WebRTC SDP answer for a specific peer connection"""
    # Support both robot_type and peer_id parameters for flexibility
    if peer_id:
        # Direct peer lookup
        if peer_id not in peer_connections:
            raise HTTPException(status_code=404, detail=f"Peer connection {peer_id} not found")
        
        pc = peer_connections[peer_id]
        if not pc.localDescription:
            raise HTTPException(status_code=404, detail=f"No answer available for peer {peer_id}")
        
        return {
            "peer_id": peer_id,
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type,
            "timestamp": time.time()
        }
    
    elif robot_type:
        # Find peer connection by robot type (for backward compatibility)
        user_id = int(current_user["sub"])
        
        # This is a simplified lookup - in practice, you might need to track
        # which peer connections belong to which users and robots
        for peer_id, pc in peer_connections.items():
            if pc.localDescription:
                return {
                    "peer_id": peer_id,
                    "sdp": pc.localDescription.sdp,
                    "type": pc.localDescription.type,
                    "robot_type": robot_type,
                    "timestamp": time.time()
                }
        
        raise HTTPException(status_code=404, detail=f"No active WebRTC answer found for robot type {robot_type}")
    
    else:
        raise HTTPException(status_code=400, detail="Either 'robot_type' or 'peer_id' parameter is required")

@app.post("/webrtc/ice-candidate")
async def handle_ice_candidate(candidate: ICECandidate, current_user: dict = Depends(get_current_user)):
    """Handle ICE candidate from client"""
    # Get the peer connection
    if candidate.peer_id not in peer_connections:
        raise HTTPException(status_code=404, detail=f"Peer connection {candidate.peer_id} not found")
    
    pc = peer_connections[candidate.peer_id]
    
    try:
        # Add ICE candidate to peer connection
        from aiortc import RTCIceCandidate
        ice_candidate = RTCIceCandidate(
            candidate=candidate.candidate.get("candidate"),
            sdpMLineIndex=candidate.candidate.get("sdpMLineIndex"),
            sdpMid=candidate.candidate.get("sdpMid")
        )
        await pc.addIceCandidate(ice_candidate)
        
        logger.debug(f"Added ICE candidate for peer {candidate.peer_id}")
        
        return {
            "success": True,
            "message": "ICE candidate added successfully",
            "peer_id": candidate.peer_id,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error adding ICE candidate for peer {candidate.peer_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add ICE candidate: {str(e)}")

@app.get("/webrtc/config")
async def get_webrtc_config(current_user: dict = Depends(get_current_user)):
    """Get WebRTC configuration for client with TURN/STUN servers"""
    # Production-ready ICE servers with both STUN and TURN
    ice_servers = [
        # Public STUN servers
        {"urls": "stun:stun.l.google.com:19302"},
        {"urls": "stun:stun1.l.google.com:19302"},
        {"urls": "stun:stun2.l.google.com:19302"},
        # Local STUN/TURN server (configured in docker-compose)
        {"urls": f"stun:{os.getenv('VPS_URL', 'localhost').replace('http://', '').replace('https://', '')}:3478"},
        {
            "urls": f"turn:{os.getenv('VPS_URL', 'localhost').replace('http://', '').replace('https://', '')}:5349",
            "username": "robotuser",
            "credential": "robotpass"
        }
    ]
    
    return {
        "ice_servers": ice_servers,
        "ice_transport_policy": "all",  # Use both STUN and TURN
        "bundle_policy": "max-bundle"
    }

@app.get("/webrtc/candidates/{peer_id}")
async def get_peer_ice_candidates(peer_id: str, current_user: dict = Depends(get_current_user)):
    """Get server ICE candidates for a specific peer connection"""
    if peer_id not in peer_connections:
        raise HTTPException(status_code=404, detail=f"Peer connection {peer_id} not found")
    
    candidates = peer_ice_candidates.get(peer_id, [])
    return {
        "peer_id": peer_id,
        "candidates": candidates,
        "count": len(candidates),
        "timestamp": time.time()
    }

@app.delete("/webrtc/peer/{peer_id}")
async def cleanup_peer(peer_id: str, current_user: dict = Depends(get_current_user)):
    """Clean up a specific peer connection"""
    if peer_id not in peer_connections:
        raise HTTPException(status_code=404, detail=f"Peer connection {peer_id} not found")
    
    await cleanup_peer_connection(peer_id)
    return {"success": True, "message": f"Peer connection {peer_id} cleaned up"}

@app.get("/webrtc/health")
async def webrtc_health(current_user: dict = Depends(get_current_user)):
    """Get WebRTC service health and active connections"""
    active_connections = len(peer_connections)
    active_rtsp_players = len(rtsp_players)
    
    # Clean up any failed connections
    failed_peers = []
    for peer_id, pc in list(peer_connections.items()):
        if pc.connectionState in ["failed", "closed"]:
            failed_peers.append(peer_id)
            await cleanup_peer_connection(peer_id)
    
    return {
        "status": "healthy",
        "active_peer_connections": active_connections - len(failed_peers),
        "active_rtsp_players": active_rtsp_players,
        "cleaned_up_peers": failed_peers,
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)