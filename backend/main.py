import os
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import logging
from pathlib import Path

# Import our modules
from database import DatabaseManager
from auth import auth_manager, get_current_user, require_admin
from services.service_manager import AdminServiceManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize database
db = DatabaseManager()

# Initialize service manager
service_manager = AdminServiceManager(db)
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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite dev server
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
    """Serve video files for completed bookings only"""
    # Check if user has completed booking for this robot type
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])
    
    # Get user's bookings
    bookings = booking_service.get_user_bookings(user_id)
    
    # Check if user has at least one completed booking for this robot type
    has_completed_booking = any(
        booking["robot_type"] == robot_type and booking["status"] == "completed"
        for booking in bookings
    )
    
    if not has_completed_booking:
        raise HTTPException(
            status_code=403, 
            detail=f"Access denied. You need a completed booking for {robot_type} robot to access this video."
        )
    
    # Define video file mapping
    video_files = {
        "turtlebot": "turtlebot_simulation.mp4",
        "arm": "arm_simulation.mp4", 
        "hand": "hand_simulation.mp4"
    }
    
    if robot_type not in video_files:
        raise HTTPException(status_code=404, detail=f"Video not found for robot type: {robot_type}")
    
    video_path = Path("../videos") / video_files[robot_type]
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)