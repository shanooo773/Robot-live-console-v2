import os
import time
import json
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import logging
from pathlib import Path

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
            vps_url = os.getenv('VPS_URL', 'http://172.104.207.139')
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
    
    total_users = len(users)
    total_bookings = len(bookings)
    active_bookings = len([b for b in bookings if b["status"] == "active"])
    total_messages = len(messages)
    unread_messages = len([m for m in messages if m["status"] == "unread"])
    total_announcements = len(announcements)
    active_announcements = len([a for a in announcements if a["is_active"]])
    
    return {
        "total_users": total_users,
        "total_bookings": total_bookings,
        "active_bookings": active_bookings,
        "total_messages": total_messages,
        "unread_messages": unread_messages,
        "total_announcements": total_announcements,
        "active_announcements": active_announcements,
        "recent_users": users[:5],  # 5 most recent users
        "recent_bookings": bookings[:10],  # 10 most recent bookings
        "recent_messages": messages[:10]  # 10 most recent messages
    }

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
    """Get list of available robot types"""
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
    robot_type: str
    language: str = "python"

@app.post("/robot/execute")
async def execute_robot_code(request: RobotExecuteRequest, current_user: dict = Depends(get_current_user)):
    """Execute robot code and return simulation results"""
    
    # Check if user has access (completed booking)
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])
    
    # Get user's bookings
    bookings = booking_service.get_user_bookings(user_id)
    
    # Check if user has at least one completed booking for this robot type
    has_completed_booking = any(
        booking["robot_type"] == request.robot_type and booking["status"] == "completed"
        for booking in bookings
    )
    
    if not has_completed_booking:
        raise HTTPException(
            status_code=403, 
            detail=f"You need a completed booking for {request.robot_type} robot to execute code."
        )
    
    try:
        # TODO: Implement actual robot simulation
        # For now, return a placeholder response that matches the expected format
        
        # Generate a unique execution ID
        execution_id = f"exec_{user_id}_{int(time.time())}"
        
        # Check if we have a simulation video for this robot type
        video_files = {
            "turtlebot": "turtlebot_simulation.mp4",
            "arm": "arm_simulation.mp4", 
            "hand": "hand_simulation.mp4"
        }
        
        video_file = video_files.get(request.robot_type)
        video_url = None
        
        if video_file:
            video_path = Path("videos") / video_file
            if video_path.exists():
                video_url = f"/videos/{request.robot_type}"
        
        # Simulate processing time
        await asyncio.sleep(1)
        
        return {
            "success": True,
            "execution_id": execution_id,
            "video_url": video_url,
            "simulation_type": "fallback",  # Will be "gazebo" when real simulation is implemented
            "message": "Code executed successfully in fallback mode",
            "robot_type": request.robot_type,
            "language": request.language,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Error executing robot code for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute robot code: {str(e)}"
        )

# WebRTC Signaling Endpoints
class WebRTCOffer(BaseModel):
    robot_type: str
    sdp: str
    type: str = "offer"

class WebRTCAnswer(BaseModel):
    robot_type: str
    sdp: str 
    type: str = "answer"

class ICECandidate(BaseModel):
    robot_type: str
    candidate: str
    sdpMLineIndex: int
    sdpMid: str

@app.post("/webrtc/offer")
async def handle_webrtc_offer(offer: WebRTCOffer, current_user: dict = Depends(get_current_user)):
    """Handle WebRTC SDP offer from client"""
    # Validate user has active booking session
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])
    
    # Check if user has active session for this robot type
    has_active_session = booking_service.has_active_session(user_id, offer.robot_type)
    
    if not has_active_session:
        raise HTTPException(
            status_code=403,
            detail=f"No active booking session for {offer.robot_type}. Video access requires an active session during your booking time."
        )
    
    # TODO: Forward offer to WebRTC signaling server or robot
    # For now, return a mock response indicating signaling server will handle this
    return {
        "success": True,
        "message": "SDP offer received and forwarded to signaling server",
        "robot_type": offer.robot_type,
        "signaling_endpoint": f"ws://localhost:8080/socket.io/",
        "room_id": f"robot_{offer.robot_type}_{user_id}",
        "timestamp": time.time()
    }

@app.post("/webrtc/answer")
async def handle_webrtc_answer(answer: WebRTCAnswer, current_user: dict = Depends(get_current_user)):
    """Handle WebRTC SDP answer from robot/server"""
    # Validate user has active booking session
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])
    
    # Check if user has active session for this robot type
    has_active_session = booking_service.has_active_session(user_id, answer.robot_type)
    
    if not has_active_session:
        raise HTTPException(
            status_code=403,
            detail=f"No active booking session for {answer.robot_type}. Video access requires an active session during your booking time."
        )
    
    # TODO: Forward answer to WebRTC signaling server
    return {
        "success": True,
        "message": "SDP answer received and processed",
        "robot_type": answer.robot_type,
        "timestamp": time.time()
    }

@app.get("/webrtc/answer")
async def get_webrtc_answer(robot_type: str, current_user: dict = Depends(get_current_user)):
    """Get WebRTC SDP answer from robot/server for a specific robot type"""
    # Validate user has active booking session
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])
    
    # Check if user has active session for this robot type
    has_active_session = booking_service.has_active_session(user_id, robot_type)
    
    if not has_active_session:
        raise HTTPException(
            status_code=403,
            detail=f"No active booking session for {robot_type}. Video access requires an active session during your booking time."
        )
    
    # TODO: Retrieve answer from WebRTC signaling server or robot
    # For now, return a mock response indicating no answer is available yet
    return {
        "success": False,
        "message": "No SDP answer available yet. The robot may not be online or hasn't responded to the offer.",
        "robot_type": robot_type,
        "answer": None,
        "timestamp": time.time()
    }

@app.post("/webrtc/ice-candidate")
async def handle_ice_candidate(candidate: ICECandidate, current_user: dict = Depends(get_current_user)):
    """Handle ICE candidate from client or robot"""
    # Validate user has active booking session  
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])
    
    # Check if user has active session for this robot type
    has_active_session = booking_service.has_active_session(user_id, candidate.robot_type)
    
    if not has_active_session:
        raise HTTPException(
            status_code=403, 
            detail=f"No active booking session for {candidate.robot_type}. Video access requires an active session during your booking time."
        )
    
    # TODO: Forward ICE candidate to WebRTC signaling server
    return {
        "success": True,
        "message": "ICE candidate received and forwarded",
        "robot_type": candidate.robot_type,
        "timestamp": time.time()
    }

@app.get("/webrtc/config")
async def get_webrtc_config(current_user: dict = Depends(get_current_user)):
    """Get WebRTC configuration for client"""
    return {
        "signaling_url": "ws://localhost:8080/socket.io/",
        "ice_servers": [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"}
        ],
        "video_constraints": {
            "width": {"ideal": 1280},
            "height": {"ideal": 720},
            "frameRate": {"ideal": 30}
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)