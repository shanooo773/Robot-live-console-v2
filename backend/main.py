import os
import time
import json
import asyncio
import uuid
import secrets
import re
from threading import Lock
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, WebSocket, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import logging
from pathlib import Path
from datetime import datetime, time as dt_time

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import environment support
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Environment-based configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

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

logger = setup_logging()

# WebRTC imports for compatibility and future direct handling if needed
try:
    from aiortc import RTCPeerConnection
    from aiortc.contrib.media import MediaPlayer, MediaRelay
    WEBRTC_AVAILABLE = True
    logger.info("WebRTC modules (aiortc) loaded successfully")
except ImportError as e:
    logger.warning(f"WebRTC modules not available - using fallbacks: {e}")
    WEBRTC_AVAILABLE = False
    RTCPeerConnection = None
    MediaPlayer = None
    MediaRelay = None

# Import our modules with fallback handling
from database import DatabaseManager
from auth import auth_manager, get_current_user, require_admin

# Import streams router
try:
    from routes import streams
    STREAMS_ROUTER_AVAILABLE = True
    logger.info("Streams router loaded successfully")
except ImportError as e:
    logger.warning(f"Streams router not available: {e}")
    STREAMS_ROUTER_AVAILABLE = False
    streams = None

# Optional service imports - use fallbacks if not available
try:
    from services.service_manager import AdminServiceManager
    from services.theia_service import TheiaContainerManager
    SERVICES_AVAILABLE = True
    logger.info("Service modules loaded successfully")
except ImportError as e:
    logger.warning(f"Service modules not available - using fallbacks: {e}")
    SERVICES_AVAILABLE = False
    AdminServiceManager = None
    TheiaContainerManager = None

# CORS configuration based on environment
def get_cors_origins():
    if ENVIRONMENT == 'production':
        production_origins = os.getenv('PRODUCTION_CORS_ORIGINS', '')
        if production_origins:
            return production_origins.split(',')
        else:
            # Fallback to VPS IP if no production origins specified
            vps_url = os.getenv('VPS_URL', 'http://172.232.105.47')
            origins = [VPS_URL, f"{VPS_URL}:3000", f"{VPS_URL}:5173", "http://anybot.brainswarmrobotics.com","http://anybot.brainswarmrobotics.com:3000","http://anybot.brainswarmrobotics.com:5173",]
    else:
        # Development origins
        dev_origins = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173,http://172.232.105.47:3000,http://172.232.105.47:5173')
        return dev_origins.split(',')

CORS_ORIGINS = get_cors_origins()
logger.info(f"Environment: {ENVIRONMENT}")
logger.info(f"CORS Origins: {CORS_ORIGINS}")

# Initialize database with fallback
try:
    db = DatabaseManager()
    DATABASE_AVAILABLE = True
    logger.info("Database connection established")
except Exception as e:
    logger.warning(f"Database connection failed - using demo mode: {e}")
    DATABASE_AVAILABLE = False
    # Create a mock database manager with authentication support
    class MockDatabaseManager:
        def __init__(self):
            # In-memory storage for users when database is unavailable
            self._users = {}
            self._user_id_counter = 1
            self._bookings = []
            self._booking_id_counter = 1
            
            # Initialize demo robots for demo user access
            self._robots = [
                {
                    "id": 1,
                    "name": "Demo TurtleBot",
                    "type": "turtlebot",
                    "webrtc_url": "wss://robot1.brainswarmrobotics.com/stream",
                    "upload_endpoint": "https://robot1.brainswarmrobotics.com/upload",
                    "status": "active",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": None
                },
                {
                    "id": 2,
                    "name": "Demo Robot Arm",
                    "type": "arm",
                    "webrtc_url": "wss://robot2.brainswarmrobotics.com/stream",
                    "upload_endpoint": "https://robot2.brainswarmrobotics.com/upload",
                    "status": "active",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": None
                },
                {
                    "id": 3,
                    "name": "Demo Dexterous Hand",
                    "type": "hand",
                    "webrtc_url": "wss://robot3.brainswarmrobotics.com/stream",
                    "upload_endpoint": "https://robot3.brainswarmrobotics.com/upload",
                    "status": "active",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": None
                }
            ]
            self._robot_id_counter = 4  # Next available ID
            
            logger.info("MockDatabaseManager initialized with in-memory user storage and demo robots")
        
        def _hash_password(self, password: str) -> str:
            """Hash a password using SHA-256 with salt"""
            import secrets
            import hashlib
            salt = secrets.token_hex(16)
            pwd_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return f"{salt}:{pwd_hash}"
        
        def _verify_password(self, password: str, password_hash: str) -> bool:
            """Verify a password against its hash"""
            import hashlib
            try:
                salt, pwd_hash = password_hash.split(':')
                return hashlib.sha256((password + salt).encode()).hexdigest() == pwd_hash
            except ValueError:
                return False
        
        def create_user(self, name: str, email: str, password: str, role: str = "user") -> dict:
            """Create a new user in memory"""
            if email in self._users:
                raise ValueError("Email already exists")
            
            user_id = self._user_id_counter
            self._user_id_counter += 1
            
            password_hash = self._hash_password(password)
            user = {
                "id": user_id,
                "name": name,
                "email": email,
                "password_hash": password_hash,
                "role": role,
                "theia_port": None,  # Will be assigned during onboarding (preview container)
                "theia_booking_port": None,  # Will be assigned when booking container starts
                "theia_admin_watch_port": None,  # Admin watch container port
                "created_at": datetime.now().isoformat()
            }
            
            self._users[email] = user
            logger.info(f"MockDB: Created user {email} with ID {user_id}")
            
            # Return user without password hash
            return {
                "id": user_id,
                "name": name,
                "email": email,
                "role": role,
                "created_at": user["created_at"]
            }
        
        def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
            """Authenticate a user against in-memory storage"""
            user = self._users.get(email)
            if not user:
                return None
            
            if self._verify_password(password, user["password_hash"]):
                return {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"],
                    "created_at": user["created_at"]
                }
            return None
        
        def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
            """Get user by ID from in-memory storage"""
            for user in self._users.values():
                if user["id"] == user_id:
                    return {
                        "id": user["id"],
                        "name": user["name"],
                        "email": user["email"],
                        "role": user["role"],
                        "theia_port": user.get("theia_port"),
                        "created_at": user["created_at"]
                    }
            return None
        
        def get_all_users(self):
            """Return all users (without password hashes)"""
            return [
                {
                    "id": user["id"],
                    "name": user["name"],
                    "email": user["email"],
                    "role": user["role"],
                    "created_at": user["created_at"]
                }
                for user in self._users.values()
            ]
        
        def create_booking(self, user_id: int, robot_type: str, date: str, start_time: str, end_time: str) -> Dict[str, Any]:
            """Create a booking in memory"""
            booking_id = self._booking_id_counter
            self._booking_id_counter += 1
            
            booking = {
                "id": booking_id,
                "user_id": user_id,
                "robot_type": robot_type,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "status": "active",
                "created_at": datetime.now().isoformat()
            }
            
            self._bookings.append(booking)
            logger.info(f"MockDB: Created booking {booking_id} for user {user_id}")
            return booking
        
        def get_all_bookings(self):
            """Return all bookings with demo data if empty"""
            if not self._bookings:
                return [
                    {"id": 1, "user_id": 1, "user_name": "Demo User", "user_email": "demo@user.com", "robot_type": "turtlebot", "date": "2024-01-20", "start_time": "10:00", "end_time": "11:00", "status": "active", "created_at": "2024-01-15T11:00:00"},
                    {"id": 2, "user_id": 1, "user_name": "Demo User", "user_email": "demo@user.com", "robot_type": "arm", "date": "2024-01-19", "start_time": "14:00", "end_time": "15:00", "status": "completed", "created_at": "2024-01-14T13:30:00"},
                    {"id": 3, "user_id": 1, "user_name": "Demo User", "user_email": "demo@user.com", "robot_type": "hand", "date": "2024-01-18", "start_time": "16:00", "end_time": "17:00", "status": "completed", "created_at": "2024-01-13T15:45:00"}
                ]
            return self._bookings
        
        def get_bookings_for_date_range(self, start_date: str, end_date: str):
            """Get bookings within date range"""
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
                
                all_bookings = self.get_all_bookings()
                filtered_bookings = []
                
                for booking in all_bookings:
                    try:
                        booking_date = datetime.strptime(booking["date"], "%Y-%m-%d").date()
                        if start_dt <= booking_date <= end_dt:
                            filtered_bookings.append(booking)
                    except (ValueError, KeyError):
                        continue
                
                return filtered_bookings
            except Exception as e:
                logger.error(f"Error filtering bookings by date range: {e}")
                return []
        
        def get_user_bookings(self, user_id: int):
            """Get bookings for a specific user"""
            all_bookings = self.get_all_bookings()
            return [booking for booking in all_bookings if booking.get("user_id") == user_id]
        
        def update_booking_status(self, booking_id: int, status: str):
            """Update booking status"""
            for booking in self._bookings:
                if booking["id"] == booking_id:
                    booking["status"] = status
                    return booking
            return None
        
        def get_all_messages(self):
            return [
                {"id": 1, "name": "Contact User", "email": "contact@example.com", "message": "Hello, I'm interested in using the robot console.", "status": "unread", "created_at": "2024-01-15T12:00:00"}
            ]
        
        def get_all_announcements(self):
            return [
                {"id": 1, "title": "Welcome to Robot Console", "content": "The system is running in demo mode.", "priority": "normal", "is_active": True, "created_by": 2, "created_by_name": "Admin User", "created_at": "2024-01-14T09:30:00", "updated_at": "2024-01-14T09:30:00"},
                {"id": 2, "title": "Database Connection Info", "content": "Database is currently unavailable, showing demo data.", "priority": "low", "is_active": False, "created_by": 2, "created_by_name": "Admin User", "created_at": "2024-01-13T14:00:00", "updated_at": "2024-01-13T14:00:00"}
            ]
        
        def get_all_robots(self):
            # Return robots from in-memory storage for demo/testing
            return getattr(self, '_robots', [])
        
        def get_active_robots(self):
            """Get only active robots"""
            all_robots = self.get_all_robots()
            return [robot for robot in all_robots if robot.get('status') == 'active']
        
        def get_active_robot_by_type(self, robot_type: str):
            """Get first active robot of specified type"""
            active_robots = self.get_active_robots()
            for robot in active_robots:
                if robot.get('type') == robot_type:
                    return robot
            return None
        
        def create_robot(self, name: str, robot_type: str, webrtc_url: str = None, upload_endpoint: str = None, status: str = 'active'):
            """Create a new robot in memory"""
            if not hasattr(self, '_robots'):
                self._robots = []
            if not hasattr(self, '_robot_id_counter'):
                self._robot_id_counter = 1
            
            robot_id = self._robot_id_counter
            self._robot_id_counter += 1
            
            robot = {
                "id": robot_id,
                "name": name,
                "type": robot_type,
                "webrtc_url": webrtc_url,
                "upload_endpoint": upload_endpoint,
                "status": status,
                "created_at": datetime.now().isoformat(),
                "updated_at": None
            }
            
            self._robots.append(robot)
            logger.info(f"MockDB: Created robot {name} (ID: {robot_id}, Type: {robot_type})")
            return robot
        
        def get_robot_by_id(self, robot_id: int):
            """Get robot by ID"""
            robots = self.get_all_robots()
            for robot in robots:
                if robot["id"] == robot_id:
                    return robot
            return None
        
        def update_robot(self, robot_id: int, name: str = None, robot_type: str = None, webrtc_url: str = None, upload_endpoint: str = None, status: str = None):
            """Update robot in memory"""
            robot = self.get_robot_by_id(robot_id)
            if not robot:
                return False
            
            if name is not None:
                robot["name"] = name
            if robot_type is not None:
                robot["type"] = robot_type
            if webrtc_url is not None:
                robot["webrtc_url"] = webrtc_url
            if upload_endpoint is not None:
                robot["upload_endpoint"] = upload_endpoint
            if status is not None:
                robot["status"] = status
            
            robot["updated_at"] = datetime.now().isoformat()
            logger.info(f"MockDB: Updated robot {robot_id}")
            return True
        
        def delete_robot(self, robot_id: int):
            """Delete robot from memory"""
            if not hasattr(self, '_robots'):
                return False
            
            self._robots = [robot for robot in self._robots if robot["id"] != robot_id]
            logger.info(f"MockDB: Deleted robot {robot_id}")
            return True
        
        # Theia service support methods
        def get_user_theia_port(self, user_id: int) -> Optional[int]:
            """Get user's assigned Theia port from in-memory storage"""
            for user in self._users.values():
                if user["id"] == user_id:
                    return user.get("theia_port")
            return None
        
        def set_user_theia_port(self, user_id: int, port: int) -> bool:
            """Set user's assigned Theia port in in-memory storage"""
            for user in self._users.values():
                if user["id"] == user_id:
                    user["theia_port"] = port
                    logger.info(f"MockDB: Set theia_port {port} for user {user_id}")
                    return True
            logger.warning(f"MockDB: User {user_id} not found for theia_port assignment")
            return False
        
        def clear_user_theia_port(self, user_id: int) -> bool:
            """Clear user's assigned Theia port in in-memory storage"""
            for user in self._users.values():
                if user["id"] == user_id:
                    user["theia_port"] = None
                    logger.info(f"MockDB: Cleared theia_port for user {user_id}")
                    return True
            return False
        
        def get_user_theia_booking_port(self, user_id: int) -> Optional[int]:
            """Get user's assigned booking Theia port from in-memory storage"""
            for user in self._users.values():
                if user["id"] == user_id:
                    return user.get("theia_booking_port")
            return None
        
        def set_user_theia_booking_port(self, user_id: int, port: int) -> bool:
            """Set user's assigned booking Theia port in in-memory storage"""
            for user in self._users.values():
                if user["id"] == user_id:
                    user["theia_booking_port"] = port
                    logger.info(f"MockDB: Set theia_booking_port {port} for user {user_id}")
                    return True
            logger.warning(f"MockDB: User {user_id} not found for theia_booking_port assignment")
            return False
        
        def clear_user_theia_booking_port(self, user_id: int) -> bool:
            """Clear user's assigned booking Theia port in in-memory storage"""
            for user in self._users.values():
                if user["id"] == user_id:
                    user["theia_booking_port"] = None
                    logger.info(f"MockDB: Cleared theia_booking_port for user {user_id}")
                    return True
            return False
        
        def get_all_assigned_ports(self) -> List[int]:
            """Get all currently assigned Theia ports (preview, booking, admin watch) from in-memory storage"""
            ports = []
            for user in self._users.values():
                port = user.get("theia_port")
                if port:
                    ports.append(port)
                booking_port = user.get("theia_booking_port")
                if booking_port:
                    ports.append(booking_port)
                admin_watch_port = user.get("theia_admin_watch_port")
                if admin_watch_port:
                    ports.append(admin_watch_port)
            return ports

        def get_user_theia_admin_watch_port(self, user_id: int) -> Optional[int]:
            for user in self._users.values():
                if user["id"] == user_id:
                    return user.get("theia_admin_watch_port")
            return None

        def set_user_theia_admin_watch_port(self, user_id: int, port: int) -> bool:
            for user in self._users.values():
                if user["id"] == user_id:
                    user["theia_admin_watch_port"] = port
                    return True
            return False

        def clear_user_theia_admin_watch_port(self, user_id: int) -> bool:
            for user in self._users.values():
                if user["id"] == user_id:
                    user["theia_admin_watch_port"] = None
                    return True
            return False

        def get_active_bookings_now(self) -> List[Dict]:
            """Get all bookings active at current time (mock)"""
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M")
            active = []
            for booking in self._bookings:
                if (booking.get("date") == current_date
                        and booking.get("status") == "active"
                        and booking.get("start_time", "00:00") <= current_time
                        and booking.get("end_time", "23:59") >= current_time):
                    active.append(booking)
            return active

    db = MockDatabaseManager()

# Initialize service manager with fallback
if SERVICES_AVAILABLE:
    theia_manager = TheiaContainerManager(db_manager=db)
    service_manager = AdminServiceManager(db, theia_manager)
else:
    # Create simple fallback service manager
    class FallbackServiceManager:
        def __init__(self, db):
            self.db = db
        
        def get_booking_service(self):
            class FallbackBookingService:
                def get_all_bookings(self):
                    return []
            return FallbackBookingService()
        
        def get_auth_service(self):
            class FallbackAuthService:
                def get_user_by_token(self, user_data):
                    return {"id": user_data.get("sub"), "email": user_data.get("email"), "role": user_data.get("role", "user")}
            return FallbackAuthService()
        
        def get_service_status(self):
            return {
                "overall_status": "degraded",
                "core_services_available": False,
                "services": {"database": "unavailable", "admin": "fallback"}
            }
        
        def get_available_features(self):
            return {"admin_dashboard": True, "booking": False, "webrtc": False}
    
    service_manager = FallbackServiceManager(db)
    theia_manager = None

async def _booking_autostop_loop():
    """Periodic background task: stop booking containers when their booking time ends."""
    def _parse_booking_active(booking, current_date, current_time_obj):
        """Return True if booking is currently within its active time window."""
        try:
            start_time_obj = _parse_booking_time(booking.get("start_time"))
            end_time_obj = _parse_booking_time(booking.get("end_time"))
            if not start_time_obj or not end_time_obj:
                return False
            return (
                booking.get("date") == current_date
                and booking.get("status") == "active"
                and booking.get("robot_id")
                and start_time_obj <= current_time_obj
                and current_time_obj <= end_time_obj
            )
        except (ValueError, KeyError):
            return False

    while True:
        try:
            await asyncio.sleep(60)  # check every minute
            if not theia_manager:
                continue
            booking_service = service_manager.get_booking_service()
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time_obj = now.time()
            containers = theia_manager.list_user_containers()
            for container in containers:
                if container.get("container_type") != "booking":
                    continue
                if "Up" not in container.get("status", ""):
                    continue
                try:
                    user_id = int(container["user_id"])
                except (ValueError, TypeError):
                    continue
                try:
                    bookings = booking_service.get_user_bookings(user_id)
                    has_active = any(
                        _parse_booking_active(b, current_date, current_time_obj)
                        for b in bookings
                    )
                    if not has_active:
                        logger.info(f"⏱ Auto-stopping expired booking container for user {user_id}")
                        theia_manager.stop_booking_container(user_id)
                except Exception as e:
                    logger.warning(f"Booking auto-stop check failed for user {user_id}: {e}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Booking auto-stop loop error: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events"""
    logger.info("🚀 Admin Backend API starting up...")
    
    # Validate production configuration
    if ENVIRONMENT == 'production':
        logger.info("🔐 Validating production configuration...")
        # Hard-required: auth cannot function without these
        required_vars = [
            'JWT_SECRET_KEY',
            'APP_PUBLIC_BASE_URL',
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            error_msg = f"Production requires these environment variables: {', '.join(missing_vars)}"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        # Warn (but don't block startup) if email delivery is not configured
        if not os.getenv('RESEND_API_KEY'):
            logger.warning(
                "⚠️ RESEND_API_KEY not set — email delivery is disabled. "
                "Set RESEND_API_KEY and MAIL_FROM to enable transactional email."
            )
        
        # Validate JWT_SECRET_KEY is not a placeholder
        jwt_secret = os.getenv('JWT_SECRET_KEY', '')
        if ('placeholder' in jwt_secret.lower() or 
            'your_secret' in jwt_secret.lower() or 
            'change_me' in jwt_secret.lower() or
            len(jwt_secret) < 32):
            error_msg = "JWT_SECRET_KEY must be changed from default placeholder and be at least 32 characters"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)
        
        logger.info("✅ Production configuration validated")
    
    logger.info("📊 Database initialized")
    
    # Log environment variables for streams feature
    logger.info(f"🌐 BRIDGE_WS_URL: {os.getenv('BRIDGE_WS_URL', 'ws://localhost:8081')}")
    bridge_control = os.getenv('BRIDGE_CONTROL_URL')
    if bridge_control:
        logger.info(f"🎛️ BRIDGE_CONTROL_URL: {bridge_control}")
    else:
        logger.info("🎛️ BRIDGE_CONTROL_URL: Not configured (optional)")
    
    # Log service status
    status = service_manager.get_service_status()
    logger.info(f"🔧 Services status: {status['overall_status']}")
    logger.info(f"📋 Core services available: {status['core_services_available']}")
    
    if not status['core_services_available']:
        logger.error("❌ Critical: Core services not available!")
    
    # Start booking auto-stop background task
    autostop_task = asyncio.create_task(_booking_autostop_loop())
    logger.info("⏱ Booking auto-stop background task started")
    
    yield
    
    autostop_task.cancel()
    try:
        await autostop_task
    except asyncio.CancelledError:
        logger.info("⏱ Booking auto-stop background task stopped")
    logger.info("🛑 Admin Backend API shutting down...")

# Create FastAPI app with lifespan
app = FastAPI(title="Robot Admin Backend API", version="1.0.0", lifespan=lifespan)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global exception handler for better error logging
@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    logger.error(f"Internal server error: {str(exc)}", exc_info=True)
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "Please check server logs"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    logger.warning(f"HTTP exception: {exc.status_code} - {exc.detail}")
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "Request failed", "detail": exc.detail}
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include streams router
if STREAMS_ROUTER_AVAILABLE:
    app.include_router(streams.router)
    logger.info("✅ Streams router registered at /api/streams")

# API Models

# Authentication Models
class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class GoogleExchangeRequest(BaseModel):
    code: str

class GitHubLogin(BaseModel):
    code: str
    redirect_uri: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class ResendConfirmationRequest(BaseModel):
    email: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class RegistrationResponse(BaseModel):
    message: str
    email: str
    confirm_url: str
    user: dict

class ConfirmationResponse(BaseModel):
    message: str
    user: dict

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: Optional[str] = None
    is_active: bool = False
    last_login: Optional[str] = None
    login_count: int = 0

# Booking Models
class BookingCreate(BaseModel):
    """Create a booking for a specific robot instance."""
    robot_id: Optional[int] = None
    robot_type: Optional[str] = None  # Legacy/compatibility hint
    date: str
    start_time: str
    end_time: str

class BookingResponse(BaseModel):
    id: int
    user_id: int
    robot_id: Optional[int] = None
    robot_type: Optional[str] = None
    robot_name: Optional[str] = None
    robot_image: Optional[str] = None
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
    webrtc_url: Optional[str] = None
    rtsp_url: Optional[str] = None
    upload_endpoint: Optional[str] = None
    container_image: Optional[str] = None
    status: str = 'active'

class RobotUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    webrtc_url: Optional[str] = None
    rtsp_url: Optional[str] = None
    upload_endpoint: Optional[str] = None
    container_image: Optional[str] = None
    status: Optional[str] = None

class RobotStatusUpdate(BaseModel):
    status: str

class RobotResponse(BaseModel):
    id: int
    name: str
    type: str
    webrtc_url: Optional[str] = None
    rtsp_url: Optional[str] = None
    upload_endpoint: Optional[str] = None
    container_image: Optional[str] = None
    status: str
    created_at: str
    updated_at: Optional[str] = None


def _validate_container_image(image: Optional[str]) -> Optional[str]:
    """Validate and normalize container image names."""
    if image is None:
        return None
    image = image.strip()
    if not image:
        return None
    if not re.match(r"^[\w./:-]+$", image):
        raise HTTPException(
            status_code=400,
            detail="Invalid container image format. Use registry/name:tag without spaces or shell characters."
        )
    return image

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Robot Programming Console API", "version": "1.0.0"}

# Authentication Endpoints
@app.post("/auth/register", response_model=RegistrationResponse)
@limiter.limit("5/hour")
async def register(request: Request, user_data: UserRegister, background_tasks: BackgroundTasks):
    """Register a new user and send confirmation email"""
    auth_service = service_manager.get_auth_service()
    return await auth_service.register_user(user_data.name, user_data.email, user_data.password, background_tasks)

@app.get("/auth/confirm", response_model=ConfirmationResponse)
async def confirm_email(token: str):
    """Confirm user email with token"""
    auth_service = service_manager.get_auth_service()
    return auth_service.confirm_email(token)

@app.post("/auth/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, user_data: UserLogin):
    """Login user"""
    auth_service = service_manager.get_auth_service()
    return auth_service.login_user(user_data.email, user_data.password)

@app.post("/auth/google/callback")
async def google_callback(request: Request, credential: str = Form(...)):
    """Handles GIS redirect-mode POST and returns short-lived exchange code via redirect."""
    auth_service = service_manager.get_auth_service()
    nonce = request.cookies.get("gis_nonce")
    try:
        result = await asyncio.to_thread(auth_service.login_with_google, credential, nonce)

        now = time.monotonic()
        one_time_code = secrets.token_urlsafe(32)
        with google_auth_exchange_lock:
            if len(google_auth_exchange_store) >= 200:
                expired_codes = [code for code, payload in google_auth_exchange_store.items() if payload.get("expires_at", 0) <= now]
                for code in expired_codes:
                    google_auth_exchange_store.pop(code, None)

            google_auth_exchange_store[one_time_code] = {
                "access_token": result["access_token"],
                "token_type": result["token_type"],
                "user": result["user"],
                "expires_at": now + GOOGLE_AUTH_CODE_TTL_SECONDS,
            }

        response = RedirectResponse(url=f"/?google_code={one_time_code}", status_code=302)
        response.delete_cookie("gis_nonce", path="/")
        return response
    except HTTPException as e:
        import urllib.parse
        response = RedirectResponse(url=f"/?google_error={urllib.parse.quote(e.detail)}", status_code=302)
        response.delete_cookie("gis_nonce", path="/")
        return response
    except Exception as e:
        logger.error(f"Google callback error: {e}")
        response = RedirectResponse(url="/?google_error=Authentication+failed.+Please+try+again.", status_code=302)
        response.delete_cookie("gis_nonce", path="/")
        return response

@app.post("/auth/google/exchange", response_model=TokenResponse)
@limiter.limit("15/minute")
async def google_exchange_code(request: Request, exchange_request: GoogleExchangeRequest):
    """Exchange one-time Google redirect code for application JWT."""
    with google_auth_exchange_lock:
        payload = google_auth_exchange_store.pop(exchange_request.code, None)
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired Google login code.")

    if payload.get("expires_at", 0) <= time.monotonic():
        raise HTTPException(status_code=400, detail="Invalid or expired Google login code.")

    return {
        "access_token": payload["access_token"],
        "token_type": payload["token_type"],
        "user": payload["user"]
    }

@app.post("/auth/github", response_model=TokenResponse)
@limiter.limit("10/minute")
async def github_login(request: Request, github_data: GitHubLogin):
    """Login or register user with GitHub OAuth"""
    auth_service = service_manager.get_auth_service()
    # GitHub token exchange is also blocking — run in thread pool
    return await asyncio.to_thread(auth_service.login_with_github, github_data.code, github_data.redirect_uri)

@app.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    # JWT contains `sub` as user id
    user_id = current_user.get("sub") or current_user.get("id")
    if not current_user.get("sub") and current_user.get("id"):
        logger.warning(f"Token missing 'sub' field, falling back to 'id': {current_user.get('id')}")
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    
    # Fetch full user data from database
    try:
        query = """
            SELECT id, name, email, role, is_active, created_at, last_login, 
                   login_count, google_id, email_confirmed_at
            FROM users 
            WHERE id = %s
        """
        result = await database.fetch_one(query, (user_id,))
        
        if not result:
            # Fallback to token data if database fetch fails
            return {
                "id": user_id,
                "email": current_user.get("email"),
                "name": current_user.get("name"),
                "role": current_user.get("role", "user"),
                "is_active": True,
                "created_at": None,
                "google_id": None
            }
        
        # Return full user data from database
        return {
            "id": result["id"],
            "email": result["email"],
            "name": result["name"],
            "role": result["role"],
            "is_active": bool(result["is_active"]),
            "created_at": str(result["created_at"]) if result.get("created_at") else None,
            "last_login": str(result["last_login"]) if result.get("last_login") else None,
            "login_count": result.get("login_count", 0),
            "google_id": result.get("google_id"),
            "email_confirmed_at": str(result["email_confirmed_at"]) if result.get("email_confirmed_at") else None
        }
    except Exception as e:
        logger.error(f"Error fetching user data: {e}")
        # Return token data as fallback
        return {
            "id": user_id,
            "email": current_user.get("email"),
            "name": None,
            "role": current_user.get("role", "user"),
            "is_active": True,
            "created_at": None,
            "google_id": None
        }


@app.post("/auth/forgot-password")
@limiter.limit("3/hour")
async def forgot_password(request: Request, req: ForgotPasswordRequest, background_tasks: BackgroundTasks):
    """Request password reset email"""
    auth_service = service_manager.get_auth_service()
    return auth_service.request_password_reset(req.email, background_tasks)

@app.post("/auth/reset-password")
async def reset_password(req: ResetPasswordRequest):
    """Reset password with token"""
    auth_service = service_manager.get_auth_service()
    return auth_service.reset_password(req.token, req.new_password)

@app.post("/auth/resend-confirmation")
@limiter.limit("3/hour")
async def resend_confirmation(request: Request, req: ResendConfirmationRequest, background_tasks: BackgroundTasks):
    """Resend confirmation email"""
    auth_service = service_manager.get_auth_service()
    return auth_service.resend_confirmation_email(req.email, background_tasks)

# Booking Endpoints
@app.post("/bookings", response_model=BookingResponse)
async def create_booking(booking_data: BookingCreate, current_user: dict = Depends(get_current_user)):
    """Create a new booking"""
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])
    if booking_data.robot_id is None:
        raise HTTPException(status_code=400, detail="robot_id is required to create a booking")
    booking = booking_service.create_booking(
        user_id=user_id,
        robot_id=booking_data.robot_id,
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
    """Get all bookings (admin only) - Real data only, no demo fallback"""
    try:
        if not DATABASE_AVAILABLE:
            logger.error("Database connection required for admin booking data")
            raise HTTPException(
                status_code=503, 
                detail="Database service unavailable. Admin dashboard requires database connection for real data."
            )
        
        booking_service = service_manager.get_booking_service()
        bookings = booking_service.get_all_bookings()
        
        # Filter out demo/test users for production admin view
        real_bookings = []
        for booking in bookings:
            user_email = booking.get('user_email', '')
            # Exclude demo users and test accounts from admin view
            if not any(demo_indicator in user_email.lower() for demo_indicator in ['demo', 'test', 'example']):
                real_bookings.append(booking)
        
        logger.info(f"Admin bookings retrieved: {len(real_bookings)} real bookings (filtered from {len(bookings)} total)")
        return real_bookings
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve admin bookings: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve booking data. Please check system status."
        )

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

@app.get("/bookings/available-slots")
async def get_available_slots(date: str, robot_id: Optional[int] = None, robot_type: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get available time slots for a specific date and robot (authenticated users only)"""
    booking_service = service_manager.get_booking_service()
    
    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    if not robot_id:
        raise HTTPException(status_code=400, detail="robot_id is required.")
    
    slots = booking_service.get_available_time_slots(date, robot_id=robot_id, robot_type=robot_type)
    return {
        "date": date,
        "robot_id": robot_id,
        "robot_type": robot_type,
        "available_slots": slots,
        "working_hours": "09:00-18:00",
        "max_session_duration": "2 hours",
        "slot_duration": "1 hour"
    }

# Admin Endpoints
@app.get("/admin/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(require_admin)):
    """Get all users (admin only) - Real users only, excluding demo accounts"""
    try:
        if not DATABASE_AVAILABLE:
            logger.error("Database connection required for user management")
            raise HTTPException(
                status_code=503, 
                detail="Database service unavailable. User management requires database connection."
            )
        
        users = db.get_all_users()
        # Filter out demo/test users from admin view, but keep real admin accounts
        real_users = []
        for user in users:
            email = user.get('email', '').lower()
            # Keep real admin accounts, exclude demo/test accounts
            if (user.get('role') == 'admin' and not any(demo_indicator in email for demo_indicator in ['demo', 'test', 'example'])) or \
               (user.get('role') != 'admin' and not any(demo_indicator in email for demo_indicator in ['demo', 'test', 'example'])):
                real_users.append(user)
        
        logger.info(f"Admin users retrieved: {len(real_users)} real users (filtered from {len(users)} total)")
        return [UserResponse(**user) for user in real_users]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve admin users: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user data. Please check system status."
        )

@app.get("/admin/stats")
async def get_admin_stats(current_user: dict = Depends(require_admin)):
    """Admin dashboard statistics. Gracefully degrade if DB is unavailable."""
    try:
        if not DATABASE_AVAILABLE:
            logger.warning("Database unavailable for /admin/stats; returning minimal stats")
            return {
                "total_users": 0,
                "total_bookings": 0,
                "active_bookings": 0,
                "total_messages": 0,
                "unread_messages": 0,
                "total_announcements": 0,
                "active_announcements": 0,
                "total_robots": 0,
                "recent_users": [],
                "recent_bookings": [],
                "recent_messages": []
            }

        users = db.get_all_users()
        bookings = db.get_all_bookings()
        messages = db.get_all_messages()
        announcements = db.get_all_announcements()
        robots = db.get_all_robots()

        real_users = [u for u in users if not any(demo in u.get('email', '').lower() for demo in ['demo','test','example'])]
        real_bookings = [b for b in bookings if not any(demo in b.get('user_email', '').lower() for demo in ['demo','test','example'])]
        real_messages = [m for m in messages if not any(demo in m.get('email', '').lower() for demo in ['demo','test','example'])]

        total_users = len(real_users)
        total_bookings = len(real_bookings)
        active_bookings = len([b for b in real_bookings if b.get("status") == "active"])
        total_messages = len(real_messages)
        unread_messages = len([m for m in real_messages if m.get("status") == "unread"])
        total_announcements = len(announcements)
        active_announcements = len([a for a in announcements if a.get("is_active", False)])
        admin_managed_robots = [r for r in robots if r.get("status") == "active"]

        return {
            "total_users": total_users,
            "total_bookings": total_bookings,
            "active_bookings": active_bookings,
            "total_messages": total_messages,
            "unread_messages": unread_messages,
            "total_announcements": total_announcements,
            "active_announcements": active_announcements,
            "total_robots": len(admin_managed_robots),
            "recent_users": real_users[-5:] if real_users else [],
            "recent_bookings": real_bookings[:10],
            "recent_messages": real_messages[:10],
        }
    except Exception as e:
        logger.error(f"/admin/stats failed: {e}. Returning minimal stats.")
        return {
            "total_users": 0,
            "total_bookings": 0,
            "active_bookings": 0,
            "total_messages": 0,
            "unread_messages": 0,
            "total_announcements": 0,
            "active_announcements": 0,
            "total_robots": 0,
            "recent_users": [],
            "recent_bookings": [],
            "recent_messages": []
        }
@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(require_admin)):
    """Delete user and all associated data (admin only)"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    
    # Prevent self-deletion
    current_user_id = int(current_user["sub"])
    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Delete user's workspace and container
    try:
        theia_service = service_manager.get_theia_service()
        if theia_service:
            theia_service.delete_user_container_and_files(user_id)
    except Exception as e:
        logger.warning(f"⚠️ Failed to delete user workspace: {e}")
    
    # Delete user from database (cascade deletes bookings, sessions)
    deleted = db.delete_user_cascade(user_id)
    
    return {
        "message": "User deleted successfully",
        "deleted": deleted
    }

@app.patch("/admin/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_data: dict,
    current_user: dict = Depends(require_admin)
):
    """Update user role (admin only)"""
    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database service unavailable")
    
    # Prevent self-demotion
    current_user_id = int(current_user["sub"])
    if current_user_id == user_id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    
    new_role = role_data.get("role")
    if not new_role:
        raise HTTPException(status_code=400, detail="Role is required")
    
    user = db.update_user_role(user_id, new_role)
    
    return {
        "message": f"User role updated to {new_role}",
        "user": user
    }

@app.post("/admin/change-password")
async def admin_change_password(
    password_data: dict,
    current_user: dict = Depends(require_admin)
):
    """Change admin password (admin only)"""
    auth_service = service_manager.get_auth_service()
    
    current_password = password_data.get("current_password")
    new_password = password_data.get("new_password")
    confirm_password = password_data.get("confirm_password")
    
    if not all([current_password, new_password, confirm_password]):
        raise HTTPException(
            status_code=400,
            detail="All password fields are required"
        )
    
    return auth_service.change_admin_password(
        current_user["email"],
        current_password,
        new_password,
        confirm_password
    )

# Robot Admin Endpoints
@app.post("/admin/robots", response_model=RobotResponse)
async def create_robot(robot_data: RobotCreate, current_user: dict = Depends(require_admin)):
    """Create a new robot (admin only)"""
    container_image = _validate_container_image(robot_data.container_image)
    robot = db.create_robot(
        name=robot_data.name,
        robot_type=robot_data.type,
        webrtc_url=robot_data.webrtc_url,
        rtsp_url=robot_data.rtsp_url,
        upload_endpoint=robot_data.upload_endpoint,
        container_image=container_image,
        status=robot_data.status
    )
    return RobotResponse(**robot)

@app.get("/admin/robots", response_model=List[RobotResponse])
async def get_all_robots_admin(current_user: dict = Depends(require_admin)):
    """Get all robots (admin only) - Only show admin-managed robots"""
    try:
        if not DATABASE_AVAILABLE:
            logger.error("Database connection required for robot management")
            raise HTTPException(
                status_code=503, 
                detail="Database service unavailable. Robot management requires database connection."
            )
        
        robots = db.get_all_robots()
        # Only show robots that are explicitly managed by admin actions
        # This ensures only robots added/managed by admins are visible
        admin_managed_robots = [robot for robot in robots if robot.get('status') in ['active', 'inactive']]
        
        logger.info(f"Admin robots retrieved: {len(admin_managed_robots)} admin-managed robots")
        return [RobotResponse(**robot) for robot in admin_managed_robots]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve admin robots: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve robot data. Please check system status."
        )

@app.put("/admin/robots/{robot_id}", response_model=RobotResponse)
async def update_robot(robot_id: int, robot_data: RobotUpdate, current_user: dict = Depends(require_admin)):
    """Update a robot (admin only)"""
    container_image = _validate_container_image(robot_data.container_image)
    success = db.update_robot(
        robot_id=robot_id,
        name=robot_data.name,
        robot_type=robot_data.type,
        webrtc_url=robot_data.webrtc_url,
        rtsp_url=robot_data.rtsp_url,
        upload_endpoint=robot_data.upload_endpoint,
        container_image=container_image,
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
    """Get all contact messages (admin only). Graceful fallback when DB is unavailable."""
    try:
        if not DATABASE_AVAILABLE:
            logger.warning("Database unavailable for /messages; returning empty list")
            return []
        messages = db.get_all_messages()
        # Filter out demo/test messages
        real_messages = [m for m in messages if not any(demo_indicator in m.get('email', '').lower()
                                                        for demo_indicator in ['demo', 'test', 'example'])]
        logger.info(f"Admin messages: {len(real_messages)} real messages")
        return [MessageResponse(**message) for message in real_messages]
    except Exception as e:
        logger.error(f"/messages failed: {e}. Returning empty list.")
        return []
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
    """Get all announcements (admin only) - Graceful fallback when DB is unavailable or errors occur"""
    try:
        if not DATABASE_AVAILABLE:
            logger.warning("Database unavailable for /announcements; returning empty list")
            return []
        announcements = db.get_all_announcements() or []
        logger.info(f"Admin announcements retrieved: {len(announcements)}")
        return [AnnouncementResponse(**announcement) for announcement in announcements]
    except Exception as e:
        logger.error(f"/announcements failed: {e}. Returning empty list.")
        return []
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
    """Get list of available robot types from registry - admin-added robots only"""
    try:
        # Get only active robots from registry (admin-added only)
        robots = db.get_active_robots()
        
        # Extract just the types for backward compatibility
        robot_types = list(set(robot["type"] for robot in robots))
        
        # Create details from database registry data instead of hardcoded values
        details = {}
        robots_by_id = {}
        for robot in robots:
            robot_type = robot["type"]
            robots_by_id[robot["id"]] = robot
            if robot_type not in details:
                details[robot_type] = {
                    "name": robot["name"],
                    "description": f"Robot type: {robot_type}",
                    "container_image": robot.get("container_image")
                }
        
        return {
            "robots": robot_types,
            "details": details,
            "registry": robots,  # Include full registry data for admin use
            "by_id": robots_by_id
        }
    except Exception as e:
        # Log error but don't fall back to dummy data
        logger.error(f"Error accessing robot registry: {e}")
        return {
            "robots": [],
            "details": {},
            "registry": [],
            "error": "Unable to retrieve robot registry. Please ensure robots are added via admin dashboard."
        }

# Video serving and access control
@app.get("/videos/{robot_type}")
async def get_video(robot_type: str, robot_id: Optional[int] = None, current_user: dict = Depends(get_current_user)):
    """Serve video files for active booking sessions only"""
    # Check if user has active booking session for this robot type
    booking_service = service_manager.get_booking_service()
    user_id = int(current_user["sub"])

    resolved_robot_id = robot_id
    robot_type_value = robot_type
    robot_meta = None
    # Allow numeric path param to represent robot_id
    if resolved_robot_id is None and robot_type.isdigit():
        resolved_robot_id = int(robot_type)
    if resolved_robot_id:
        robot_meta = db.get_robot_by_id(resolved_robot_id)
        if robot_meta:
            robot_type_value = robot_meta.get("type", robot_type_value)
    
    # Check if user has active session (during their booking time)
    has_active_session = booking_service.has_active_session(user_id, robot_type=robot_type_value if not resolved_robot_id else None, robot_id=resolved_robot_id)
    
    if not has_active_session:
        # Also check for admin access
        is_admin = current_user.get("role") == "admin"
        if not is_admin:
            raise HTTPException(
                status_code=403, 
                detail=f"Access denied. Video access requires an active booking session for this robot during your scheduled time. Include robot_id for specific robots."
            )
    
    # Define video file mapping
    video_files = {
        "turtlebot": "turtlebot_simulation.mp4",
        "arm": "arm_simulation.mp4", 
        "hand": "hand_simulation.mp4"
    }
    
    if robot_type_value not in video_files:
        raise HTTPException(status_code=404, detail=f"Video not found for robot type: {robot_type_value}")
    
    video_path = Path("videos") / video_files[robot_type_value]
    
    if not video_path.exists():
        raise HTTPException(
            status_code=404, 
            detail=f"Video file not found: {video_files[robot_type]}. Please contact administrator."
        )
    
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename=video_files[robot_type_value]
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

def _has_active_booking(user_id: int, is_demo: bool) -> bool:
    """Return True if user is in booking mode (demo user or has a currently active booking)."""
    if is_demo:
        return True
    try:
        booking_service = service_manager.get_booking_service()
        bookings = booking_service.get_user_bookings(user_id)
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time_obj = now.time()
        for booking in bookings:
            if (booking["date"] == current_date and booking["status"] == "active" and booking.get("robot_id")):
                try:
                    start_time_obj = _parse_booking_time(booking.get("start_time"))
                    end_time_obj = _parse_booking_time(booking.get("end_time"))
                    if not start_time_obj or not end_time_obj:
                        continue
                    if start_time_obj <= current_time_obj <= end_time_obj:
                        return True
                except ValueError:
                    continue
    except Exception as e:
        logger.warning(f"Could not check booking status for user {user_id}: {e}")
    return False


def _get_active_booking_with_robot(user_id: int) -> Optional[Dict[str, Any]]:
    """Return the user's current active booking (with robot details if available)."""
    try:
        booking_service = service_manager.get_booking_service()
        bookings = booking_service.get_user_bookings(user_id)
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time_obj = now.time()
        for booking in bookings:
            if (
                booking["date"] == current_date
                and booking["status"] == "active"
                and booking.get("robot_id")
            ):
                try:
                    start_time_obj = _parse_booking_time(booking.get("start_time"))
                    end_time_obj = _parse_booking_time(booking.get("end_time"))
                    if not start_time_obj or not end_time_obj:
                        continue
                    if start_time_obj <= current_time_obj <= end_time_obj:
                        robot = db.get_robot_by_id(booking["robot_id"])
                        if robot:
                            booking_with_robot = dict(booking)
                            booking_with_robot["robot_details"] = robot
                            return booking_with_robot
                        return booking
                except ValueError:
                    continue
    except Exception as e:
        logger.warning(f"Could not fetch active booking for user {user_id}: {e}")
    return None


def _resolve_booking_image(active_booking: Optional[Dict[str, Any]]) -> Optional[str]:
    """Return container image string from an active booking if available."""
    if not active_booking:
        return None
    robot_details = active_booking.get("robot_details") or {}
    # robot_image is kept for backward compatibility with stored booking records
    return robot_details.get("container_image") or active_booking.get("robot_image")


def _parse_booking_time(value: Optional[str]) -> Optional[dt_time]:
    """Parse booking time fields that may be HH:MM or HH:MM:SS."""
    normalized = (value or "").strip()
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(normalized, fmt).time()
        except ValueError:
            continue
    return None

@app.get("/theia/status")  
async def get_theia_status(current_user: dict = Depends(get_current_user)):
    """Get status of user's Theia containers - dual-container workflow.
    Preview container is always auto-started. Booking container is started when user has an active booking."""
    user_id = int(current_user["sub"])
    
    # Update user activity for cleanup tracking
    theia_manager.update_user_activity(user_id)
    
    # Determine booking mode
    has_active_booking = _has_active_booking(user_id, is_demo_user(current_user))
    active_booking = _get_active_booking_with_robot(user_id) if has_active_booking else None
    
    status = theia_manager.get_container_status(user_id)
    
    # Auto-start preview container for all users if not running (always-on)
    if status.get("preview_status") in ["not_created", "stopped", "error", None]:
        user_type = "demo" if is_demo_user(current_user) else "regular"
        logger.info(f"🎯 Auto-starting preview container for {user_type} user {user_id}")
        preview_result = theia_manager.start_preview_container(user_id)
        if preview_result.get("success"):
            logger.info(f"✅ User {user_id} preview container auto-started successfully")
        else:
            logger.error(f"❌ Failed to auto-start preview container for user {user_id}: {preview_result.get('error')}")
            status["auto_start_attempted"] = True
            status["auto_start_error"] = preview_result.get("error")
        # Refresh status after starting
        status = theia_manager.get_container_status(user_id)
    
    # Auto-start booking container if user has an active booking and it's not running
    if has_active_booking and status.get("booking_status") in ["not_created", "stopped", "error", None]:
        logger.info(f"🎯 Auto-starting booking container for user {user_id} (active booking)")
        booking_image = _resolve_booking_image(active_booking)
        booking_result = theia_manager.start_booking_container(user_id, image_override=booking_image)
        if booking_result.get("success"):
            logger.info(f"✅ User {user_id} booking container auto-started successfully")
        else:
            logger.error(f"❌ Failed to auto-start booking container for user {user_id}: {booking_result.get('error')}")
        # Refresh status after starting
        status = theia_manager.get_container_status(user_id)
    
    # Stop booking container if no active booking and it's running
    if not has_active_booking and status.get("booking_status") == "running":
        logger.info(f"🛑 Stopping booking container for user {user_id} (no active booking)")
        stop_result = theia_manager.stop_booking_container(user_id)
        if not stop_result.get("success"):
            logger.error(f"❌ Failed to stop booking container for user {user_id}: {stop_result.get('error')}")
        status = theia_manager.get_container_status(user_id)
    
    # Add booking status information for UI to determine mode
    status["has_active_booking"] = has_active_booking
    status["user_mode"] = "booking" if has_active_booking else "preview"
    # Primary url/status reflects the relevant container for current mode
    if has_active_booking and status.get("booking_url"):
        status["url"] = status["booking_url"]
        status["status"] = status.get("booking_status", status.get("status"))
    else:
        status["url"] = status.get("preview_url") or status.get("url")
        status["status"] = status.get("preview_status", status.get("status"))
    
    return status

@app.get("/theia/demo/status")
async def get_demo_theia_status():
    """Get status of demo user Theia containers (bypasses auth for demo purposes)"""
    user_id = -1  # Demo user ID
    logger.info(f"🎯 Demo endpoint accessed - checking Theia status for user {user_id}")
    
    status = theia_manager.get_container_status(user_id)
    
    # Auto-start preview container for demo user if not running
    if status.get("preview_status") in ["not_created", "stopped", "error", None]:
        logger.info(f"🎯 Auto-starting preview container for demo user {user_id}")
        preview_result = theia_manager.start_preview_container(user_id)
        if preview_result.get("success"):
            logger.info(f"✅ Demo user {user_id} preview container auto-started successfully")
            status = theia_manager.get_container_status(user_id)
        else:
            logger.error(f"❌ Failed to auto-start preview container for demo user {user_id}: {preview_result.get('error')}")
            status["auto_start_attempted"] = True
            status["auto_start_error"] = preview_result.get("error")
    
    # Also start booking container for demo users
    if status.get("booking_status") in ["not_created", "stopped", "error", None]:
        logger.info(f"🎯 Auto-starting booking container for demo user {user_id}")
        booking_result = theia_manager.start_booking_container(user_id)
        if booking_result.get("success"):
            status = theia_manager.get_container_status(user_id)
    
    status["has_active_booking"] = True
    status["user_mode"] = "booking"
    status["url"] = status.get("booking_url") or status.get("preview_url") or status.get("url")
    
    return status

@app.post("/theia/start")
async def start_theia_container(current_user: dict = Depends(get_current_user)):
    """Start user's preview Theia container - Available for all authenticated users.
    If user has an active booking, also starts the booking container."""
    user_id = int(current_user["sub"])
    
    has_active_booking = _has_active_booking(user_id, is_demo_user(current_user))
    active_booking = _get_active_booking_with_robot(user_id) if has_active_booking else None
    if is_demo_user(current_user):
        logger.info(f"🎯 Demo user {user_id} starting Theia containers (preview + booking)")
    else:
        logger.info(f"✅ Regular user {user_id} starting Theia containers (preview{' + booking' if has_active_booking else ''})")
    
    # Always start the preview container
    preview_result = theia_manager.start_preview_container(user_id)
    
    # Also start booking container if user has an active booking
    booking_result = None
    if has_active_booking or is_demo_user(current_user):
        booking_image = _resolve_booking_image(active_booking)
        booking_result = theia_manager.start_booking_container(user_id, image_override=booking_image)
    
    if preview_result.get("success"):
        status = theia_manager.get_container_status(user_id)
        return {
            "message": "Theia containers started successfully",
            "preview_url": status.get("preview_url"),
            "booking_url": status.get("booking_url"),
            "url": status.get("booking_url") if has_active_booking else status.get("preview_url"),
            "status": "running"
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start preview Theia container: {preview_result.get('error', 'Unknown error')}"
        )

@app.post("/theia/booking/start")
async def start_booking_theia_container(current_user: dict = Depends(get_current_user)):
    """Explicitly start the booking IDE container for user. Requires an active booking."""
    user_id = int(current_user["sub"])
    
    has_active_booking = _has_active_booking(user_id, is_demo_user(current_user))
    active_booking = _get_active_booking_with_robot(user_id) if has_active_booking else None
    if not has_active_booking and not is_demo_user(current_user):
        raise HTTPException(
            status_code=403,
            detail="No active booking found. Book a session to use the booking IDE."
        )
    
    booking_image = _resolve_booking_image(active_booking)
    result = theia_manager.start_booking_container(user_id, image_override=booking_image)
    if result.get("success"):
        return {
            "message": "Booking Theia container started successfully",
            "status": result.get("status"),
            "url": result.get("url"),
            "port": result.get("port")
        }
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start booking Theia container: {result.get('error', 'Unknown error')}"
        )

@app.post("/theia/booking/stop")
async def stop_booking_theia_container(current_user: dict = Depends(get_current_user)):
    """Stop user's booking Theia container (preview container remains running)"""
    user_id = int(current_user["sub"])
    result = theia_manager.stop_booking_container(user_id)
    
    if result.get("success"):
        return {"message": "Booking Theia container stopped successfully"}
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop booking Theia container: {result.get('error', 'Unknown error')}"
        )

@app.post("/theia/stop")
async def stop_theia_container(current_user: dict = Depends(get_current_user)):
    """Stop user's preview Theia container"""
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
    """Restart user's Theia containers"""
    user_id = int(current_user["sub"])
    
    # Determine booking mode so the restarted container uses the correct image
    booking_mode = _has_active_booking(user_id, is_demo_user(current_user))
    active_booking = _get_active_booking_with_robot(user_id) if booking_mode else None
    booking_image = _resolve_booking_image(active_booking)
    
    result = theia_manager.restart_container(user_id, booking_mode=booking_mode, booking_image=booking_image)
    
    if result.get("success"):
        status = theia_manager.get_container_status(user_id)
        return {
            "message": "Theia container restarted successfully",
            "preview_url": status.get("preview_url"),
            "booking_url": status.get("booking_url"),
            "url": status.get("booking_url") if booking_mode else status.get("preview_url"),
            "status": "running"
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to restart Theia container: {result.get('error', 'Unknown error')}"
        )

@app.post("/theia/schedule-cleanup")
async def schedule_container_cleanup(current_user: dict = Depends(get_current_user)):
    """Schedule container cleanup on user logout with timeout to save resources"""
    user_id = int(current_user["sub"])
    
    try:
        # Use the new logout cleanup functionality
        result = theia_manager.schedule_logout_cleanup(user_id)
        
        if result.get("success"):
            logger.info(f"Scheduled container cleanup for user {user_id} on logout")
            return {
                "message": "Container cleanup scheduled successfully",
                "user_id": user_id,
                "cleanup_scheduled": True,
                "note": f"Container will be cleaned up after {theia_manager.logout_grace_period_minutes} minutes of inactivity"
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to schedule container cleanup: {result.get('error')}"
            )
        
    except Exception as e:
        logger.error(f"Failed to schedule cleanup for user {user_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to schedule container cleanup: {str(e)}"
        )

@app.get("/theia/logs")
async def get_theia_logs(
    type: str = "preview",
    lines: int = 200,
    current_user: dict = Depends(get_current_user)
):
    """Return the last N log lines from the requesting user's preview or booking container.

    Query params:
        type  – "preview" (default) or "booking"
        lines – number of tail lines, clamped to 1-500
    """
    if not theia_manager:
        raise HTTPException(status_code=503, detail="Theia service not available")

    if type not in ("preview", "booking"):
        raise HTTPException(status_code=400, detail="type must be 'preview' or 'booking'")

    user_id = int(current_user["sub"])
    lines = min(max(lines, 1), 500)

    result = theia_manager.get_container_logs(user_id, container_type=type, lines=lines)
    return result


@app.get("/theia/containers")
async def list_theia_containers(current_user: dict = Depends(require_admin)):
    """List all Theia containers (admin only)"""
    containers = theia_manager.list_user_containers()
    return {"containers": containers}

# Additional Theia Admin Endpoints
@app.post("/theia/admin/stop/{user_id}")
async def admin_stop_theia_container(user_id: int, current_user: dict = Depends(require_admin)):
    """Stop any user's Theia containers (preview and booking) (admin only)"""
    preview_result = theia_manager.stop_container(user_id)
    theia_manager.stop_booking_container(user_id)
    
    if preview_result.get("success"):
        return {"message": f"Theia containers for user {user_id} stopped successfully"}
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to stop Theia containers for user {user_id}: {preview_result.get('error', 'Unknown error')}"
        )

@app.post("/theia/admin/restart/{user_id}")
async def admin_restart_theia_container(user_id: int, current_user: dict = Depends(require_admin)):
    """Restart any user's Theia container (admin only)"""
    booking_mode = _has_active_booking(user_id, False)
    active_booking = _get_active_booking_with_robot(user_id) if booking_mode else None
    booking_image = _resolve_booking_image(active_booking)
    result = theia_manager.restart_container(user_id, booking_mode=booking_mode, booking_image=booking_image)
    
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

@app.post("/theia/admin/cleanup")
async def admin_cleanup_stale_containers(current_user: dict = Depends(require_admin)):
    """Clean up stale containers (admin only)"""
    result = theia_manager.cleanup_stale_containers()
    
    if result.get("success"):
        return {
            "message": f"Cleanup completed: {result.get('cleaned_count', 0)} stale containers removed",
            "containers": result.get("containers", [])
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to cleanup containers: {result.get('error', 'Unknown error')}"
        )

@app.post("/theia/admin/cleanup-idle")
async def admin_cleanup_idle_containers(current_user: dict = Depends(require_admin)):
    """Clean up idle containers (admin only)"""
    result = theia_manager.cleanup_idle_containers()
    
    if result.get("success"):
        return {
            "message": f"Idle cleanup completed: {result.get('cleaned_count', 0)} idle containers removed",
            "containers": result.get("containers", []),
            "timeout_hours": theia_manager.idle_timeout_hours
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to cleanup idle containers: {result.get('error', 'Unknown error')}"
        )

@app.post("/theia/admin/stop-all")
async def admin_stop_all_containers(current_user: dict = Depends(require_admin)):
    """Stop all running Theia containers (admin only)"""
    result = theia_manager.stop_all_user_containers()
    
    if result.get("success"):
        return {
            "message": f"Stopped {result.get('stopped_count', 0)} running containers",
            "containers": result.get("containers", [])
        }
    else:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to stop all containers: {result.get('error', 'Unknown error')}"
        )

@app.get("/theia/admin/surveillance/{user_id}")
async def admin_surveillance_ide(user_id: int, current_user: dict = Depends(require_admin)):
    """Get URLs for admin to open and view any user's Theia IDE containers (admin surveillance)"""
    if not theia_manager:
        raise HTTPException(status_code=503, detail="Theia manager not available")
    status = theia_manager.get_container_status(user_id)
    return {
        "user_id": user_id,
        "preview_url": status.get("preview_url"),
        "preview_status": status.get("preview_status"),
        "booking_url": status.get("booking_url"),
        "booking_status": status.get("booking_status"),
    }

# ─── Admin Surveillance (Watch Container) Endpoints ───────────────────────────

@app.get("/admin/bookings/active-now")
async def get_active_bookings_now(current_user: dict = Depends(require_admin)):
    """Return all bookings that are active at the current moment (admin only)."""
    try:
        if DATABASE_AVAILABLE:
            bookings = db.get_active_bookings_now()
        else:
            bookings = db.get_active_bookings_now()
        return {"bookings": bookings}
    except Exception as e:
        logger.error(f"Error getting active bookings now: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get active bookings: {str(e)}")

class AdminWatchStartRequest(BaseModel):
    booking_id: int
    robot_id: int

# ------------------------------------------------------------------
# Admin settings endpoints
# ------------------------------------------------------------------

SURVEILLANCE_BASE_IMAGE_KEY = "surveillance_base_image"


@app.get("/admin/settings")
async def get_admin_settings(current_user: dict = Depends(require_admin)):
    """Return current admin-configurable settings (admin only)."""
    if not theia_manager:
        raise HTTPException(status_code=503, detail="Theia manager not available")

    allowed = theia_manager.get_allowed_images()
    fallback = theia_manager.get_default_surveillance_image()

    configured_image: str = fallback
    if DATABASE_AVAILABLE:
        try:
            stored = db.get_admin_setting(SURVEILLANCE_BASE_IMAGE_KEY)
            if stored and stored in allowed:
                configured_image = stored
            elif stored:
                logger.warning(
                    f"Stored surveillance_base_image '{stored}' is not in the allowlist; "
                    f"falling back to '{fallback}'"
                )
        except Exception as e:
            logger.error(f"Failed to read admin settings from DB: {e}")

    return {
        "surveillance_base_image": configured_image,
        "allowed_images": allowed,
    }


class AdminSettingsUpdate(BaseModel):
    surveillance_base_image: str


@app.put("/admin/settings")
async def update_admin_settings(body: AdminSettingsUpdate, current_user: dict = Depends(require_admin)):
    """Update admin-configurable settings (admin only)."""
    if not theia_manager:
        raise HTTPException(status_code=503, detail="Theia manager not available")

    image = body.surveillance_base_image.strip()
    if not theia_manager.is_image_allowed(image):
        allowed = theia_manager.get_allowed_images()
        raise HTTPException(
            status_code=400,
            detail=f"Image '{image}' is not in the allowlist. Permitted images: {allowed}",
        )

    if not DATABASE_AVAILABLE:
        raise HTTPException(status_code=503, detail="Database not available; cannot persist settings")

    try:
        db.set_admin_setting(SURVEILLANCE_BASE_IMAGE_KEY, image)
    except Exception as e:
        logger.error(f"Failed to persist admin settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to save settings")

    logger.info(f"Admin {current_user.get('sub')} set surveillance_base_image='{image}'")
    return {
        "surveillance_base_image": image,
        "allowed_images": theia_manager.get_allowed_images(),
        "message": "Settings saved successfully",
    }


@app.post("/admin/theia/watch/start")
async def admin_watch_start(body: AdminWatchStartRequest, current_user: dict = Depends(require_admin)):
    """Start/restart the admin watch container mounting a booked user's workspace (admin only)."""
    if not theia_manager:
        raise HTTPException(status_code=503, detail="Theia manager not available")

    admin_id = int(current_user["sub"])
    booking_id = body.booking_id
    requested_robot_id = body.robot_id

    # Resolve the booking to get the target user
    try:
        if DATABASE_AVAILABLE:
            active_bookings = db.get_active_bookings_now()
        else:
            active_bookings = db.get_active_bookings_now()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch active bookings: {str(e)}")

    target_booking = next((b for b in active_bookings if b["id"] == booking_id), None)
    if target_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found or not currently active")

    # Validate requested robot
    robot = db.get_robot_by_id(requested_robot_id)
    if not robot or robot.get("status") != "active":
        raise HTTPException(status_code=404, detail="Requested robot is not available or inactive")
    
    if requested_robot_id and target_booking.get("robot_id") != requested_robot_id:
        raise HTTPException(
            status_code=400,
            detail="Booking does not match the requested robot_id. Please refresh active bookings."
        )

    target_user_id = target_booking["user_id"]
    target_project_dir = theia_manager.get_user_project_dir(target_user_id)
    theia_manager.ensure_user_project_dir(target_user_id)

    # Determine image to use:
    # 1. Per-robot container_image (highest priority)
    # 2. Admin-configured surveillance_base_image (from DB settings)
    # 3. Fallback handled inside theia_manager._resolve_image_to_use
    robot_image = robot.get("container_image")
    admin_configured_image: Optional[str] = None
    if not robot_image and DATABASE_AVAILABLE:
        try:
            stored = db.get_admin_setting(SURVEILLANCE_BASE_IMAGE_KEY)
            allowed = theia_manager.get_allowed_images()
            if stored and stored in allowed:
                admin_configured_image = stored
            elif stored:
                logger.warning(
                    f"Admin-configured surveillance image '{stored}' is not in allowlist; "
                    f"using default fallback"
                )
        except Exception as e:
            logger.warning(f"Could not read admin surveillance image setting: {e}")

    image_override = robot_image or admin_configured_image

    result = theia_manager.start_admin_watch_container(
        admin_id, target_project_dir, image_override=image_override
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=f"Failed to start watch container: {result.get('error')}")

    logger.info(f"Admin {admin_id} started surveillance watch on booking {booking_id} (user {target_user_id})")
    return {
        "url": result.get("url"),
        "mode": "surveillance",
        "booking_id": booking_id,
        "user_id": target_user_id,
        "user_name": target_booking.get("user_name"),
        "robot_id": target_booking.get("robot_id"),
        "robot_image": robot_image or admin_configured_image,
        "robot_name": robot.get("name") or target_booking.get("robot_name"),
    }

@app.post("/admin/theia/watch/start-self")
async def admin_watch_start_self(current_user: dict = Depends(require_admin)):
    """Start/restart the admin watch container mounting the admin's own workspace (admin only)."""
    if not theia_manager:
        raise HTTPException(status_code=503, detail="Theia manager not available")

    admin_id = int(current_user["sub"])
    admin_project_dir = theia_manager.get_user_project_dir(admin_id)
    theia_manager.ensure_user_project_dir(admin_id)

    result = theia_manager.start_admin_watch_container(admin_id, admin_project_dir)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=f"Failed to start admin watch container: {result.get('error')}")

    logger.info(f"Admin {admin_id} started self-mode watch container")
    return {"url": result.get("url"), "mode": "admin"}

@app.get("/admin/theia/watch/status")
async def admin_watch_status(current_user: dict = Depends(require_admin)):
    """Get status of the admin's watch container (admin only)."""
    if not theia_manager:
        raise HTTPException(status_code=503, detail="Theia manager not available")
    admin_id = int(current_user["sub"])
    status = theia_manager.get_admin_watch_container_status(admin_id)
    return {"admin_id": admin_id, **status}

@app.post("/admin/theia/watch/stop")
async def admin_watch_stop(current_user: dict = Depends(require_admin)):
    """Stop and remove the admin's watch container (admin only)."""
    if not theia_manager:
        raise HTTPException(status_code=503, detail="Theia manager not available")
    admin_id = int(current_user["sub"])
    result = theia_manager.stop_admin_watch_container(admin_id)
    if result.get("success"):
        return {"message": "Admin watch container stopped successfully"}
    else:
        raise HTTPException(status_code=500, detail=f"Failed to stop watch container: {result.get('error')}")

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

# Workspace Files Endpoint
@app.get("/theia/workspace/files")
async def list_workspace_files(current_user: dict = Depends(get_current_user)):
    """List all .py and .cpp files in the user's workspace"""
    import os
    
    user_id = int(current_user["sub"])
    
    if not theia_manager:
        raise HTTPException(status_code=503, detail="Theia manager not available")
    
    try:
        user_project_dir = theia_manager.get_user_project_dir(user_id)
        
        if not user_project_dir.exists():
            return {"files": []}
        
        # List all .py and .cpp files
        files = []
        for root, dirs, filenames in os.walk(user_project_dir):
            for filename in filenames:
                if filename.endswith(('.py', '.cpp')):
                    # Get relative path from project directory
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, user_project_dir)
                    files.append({
                        "name": filename,
                        "path": rel_path,
                        "language": "cpp" if filename.endswith('.cpp') else "python"
                    })
        
        return {"files": files}
    
    except Exception as e:
        logger.error(f"Failed to list workspace files for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list workspace files: {str(e)}")

@app.get("/theia/workspace/file/{file_path:path}")
async def get_workspace_file_content(file_path: str, current_user: dict = Depends(get_current_user)):
    """Get content of a specific file from the user's workspace"""
    user_id = int(current_user["sub"])
    
    if not theia_manager:
        raise HTTPException(status_code=503, detail="Theia manager not available")
    
    try:
        user_project_dir = theia_manager.get_user_project_dir(user_id)
        full_path = user_project_dir / file_path
        
        # Security check: ensure the file is within the user's project directory
        if not str(full_path.resolve()).startswith(str(user_project_dir.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        content = full_path.read_text()
        return {"content": content, "filename": file_path}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to read file {file_path} for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

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
    
    # Demo users have unrestricted access - skip booking validation
    if is_demo_user(current_user):
        logger.info(f"🎯 Demo user {user_id} executing robot code without booking restrictions")
        # For demo users, use the requested robot_type or default to 'turtlebot'
        robot_type = request.robot_type or 'turtlebot'
        # Get the first available robot of the requested type for demo users
        robot = db.get_active_robot_by_type(robot_type)
        if not robot:
            raise HTTPException(
                status_code=404,
                detail=f"No active {robot_type} robot available for demo access."
            )
    else:
        # Get user's active bookings for regular users
        bookings = booking_service.get_user_bookings(user_id)
        
        # Find current active booking
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time_obj = now.time()
        
        active_booking = None
        for booking in bookings:
            if (booking["date"] == current_date and booking["status"] == "active" and booking.get("robot_id")):
                try:
                    start_time_obj = datetime.strptime(booking["start_time"], "%H:%M").time()
                    end_time_obj = datetime.strptime(booking["end_time"], "%H:%M").time()
                    if start_time_obj <= current_time_obj <= end_time_obj:
                        active_booking = booking
                        break
                except ValueError:
                    continue
        
        if not active_booking:
            raise HTTPException(
                status_code=403,
                detail="Code execution on robot requires booking. You can still use the IDE to edit and save code in Preview Mode."
            )
        
        # Get the specific robot assigned to this user
        robot = db.get_robot_by_id(active_booking["robot_id"])
        if not robot:
            raise HTTPException(
                status_code=404,
                detail=f"Assigned robot (ID: {active_booking['robot_id']}) not found."
            )
        
        robot_type = robot.get("type")
    
    # At this point, 'robot' contains the specific robot assigned to the user
    # Code execution uses robot registry (get_active_robot_by_type) for endpoint URLs
    # upload_endpoint was formerly known as code_api_url in the schema migration
    upload_endpoint = robot.get("upload_endpoint")  # Previously code_api_url
    robot_id = robot.get("id")
    robot_name = robot.get("name")
    
    # Enhanced logging with robot details
    logger.info(f"Robot code execution request - User: {user_id}, Robot: {robot_name} (ID: {robot_id}, Type: {robot_type}), Upload Endpoint: {upload_endpoint}")
    
    if not upload_endpoint:
        # Fallback to simulation mode if no upload endpoint is configured
        logger.warning(f"No upload_endpoint configured for robot {robot_name} (ID: {robot_id}, Type: {robot_type}), using fallback simulation")
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
        
        # Execute code via external robot API using file upload as specified
        # If filename is provided, try to load from user's Theia workspace first
        code_to_execute = request.code
        
        if request.filename and hasattr(theia_manager, 'get_user_project_dir'):
            user_project_dir = theia_manager.get_user_project_dir(user_id)
            file_path = user_project_dir / request.filename
            
            # If the file exists in user's workspace, use its content
            if file_path.exists():
                try:
                    code_to_execute = file_path.read_text()
                    logger.info(f"Loaded code from user workspace: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to read file from workspace {file_path}: {e}")
                    # Fall back to provided code
        
        # Create a temporary file for upload as specified in problem statement
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(code_to_execute)
            temp_file_path = temp_file.name
        
        try:
            # Upload code using file upload as specified: files = {"file": (os.path.basename(file_path), f)}
            with open(temp_file_path, 'rb') as f:
                files = {"file": (os.path.basename(temp_file_path), f)}
                
                # Use requests instead of aiohttp for file upload as specified in problem statement
                import requests
                resp = requests.post(upload_endpoint, files=files, timeout=120)
                
                if resp.status_code != 200:
                    logger.error(f"Failed to upload code to robot {robot_name} (ID: {robot_id}) at {upload_endpoint}: {resp.status_code} - {resp.text}")
                    raise HTTPException(
                        status_code=502,
                        detail=f"Failed to upload code to robot: HTTP {resp.status_code}"
                    )
                
                upload_result = resp.json() if resp.headers.get('content-type', '').startswith('application/json') else {"status": "uploaded"}
                
        except requests.exceptions.ConnectionError:
            logger.error(f"Failed to connect to robot API for {robot_name} (ID: {robot_id}) at {upload_endpoint}")
            raise HTTPException(
                status_code=503,
                detail="Robot API is unreachable. Please try again later."
            )
        except requests.exceptions.Timeout:
            logger.error(f"Timeout connecting to robot API for {robot_name} (ID: {robot_id}) at {upload_endpoint}")
            raise HTTPException(
                status_code=504,
                detail="Robot API timeout. Please try again later."
            )
        finally:
            # Clean up temporary file
            if 'temp_file_path' in locals():
                os.unlink(temp_file_path)
        
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
            "simulation_type": "robot_upload"
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

class WebRTCAnswer(BaseModel):
    robot_id: Optional[int] = None
    robot_type: Optional[str] = None
    sdp: str
    type: str = "answer"

class WebRTCIceCandidate(BaseModel):
    robot_id: Optional[int] = None
    robot_type: Optional[str] = None
    candidate: str
    sdp_mid: Optional[str] = None
    sdp_m_line_index: Optional[int] = None

# Helper functions for WebRTC management
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

async def resolve_robot_id_from_answer(answer: WebRTCAnswer) -> int:
    """Resolve robot_id from either robot_id or robot_type in the answer"""
    if answer.robot_id is not None:
        return answer.robot_id
    
    if answer.robot_type is not None:
        # Find robot by type - get the first robot of this type
        robots = db.get_all_robots()
        for robot in robots:
            if robot.get('type') == answer.robot_type:
                return robot['id']
        raise HTTPException(
            status_code=404, 
            detail=f"No robot found with type '{answer.robot_type}'"
        )
    
    raise HTTPException(
        status_code=400, 
        detail="Either robot_id or robot_type must be provided"
    )

async def resolve_robot_id_from_ice(ice_candidate: WebRTCIceCandidate) -> int:
    """Resolve robot_id from either robot_id or robot_type in the ICE candidate"""
    if ice_candidate.robot_id is not None:
        return ice_candidate.robot_id
    
    if ice_candidate.robot_type is not None:
        # Find robot by type - get the first robot of this type
        robots = db.get_all_robots()
        for robot in robots:
            if robot.get('type') == ice_candidate.robot_type:
                return robot['id']
        raise HTTPException(
            status_code=404, 
            detail=f"No robot found with type '{ice_candidate.robot_type}'"
        )
    
    raise HTTPException(
        status_code=400, 
        detail="Either robot_id or robot_type must be provided"
    )

def is_demo_user(current_user: dict) -> bool:
    """Check if the current user is a demo user"""
    user_id = int(current_user.get("sub", 0))
    user_email = current_user.get("email", "")
    
    # Check for demo user flags in token
    if current_user.get("isDemoUser") or current_user.get("isDemoAdmin"):
        return True
    
    # Check for demo user IDs (negative IDs are used for demo users)
    if user_id in [-1, -2]:
        return True
    
    # Check for demo user email patterns
    demo_indicators = ['demo', 'test', 'example']
    if any(indicator in user_email.lower() for indicator in demo_indicators):
        return True
    
    return False

async def has_booking_for_robot(user_id: int, robot_id: int, current_user: dict = None) -> bool:
    """Check if user has active booking for the specific robot"""
    # Demo users have unrestricted access - bypass booking validation
    if current_user and is_demo_user(current_user):
        logger.info(f"🎯 Demo user {user_id} granted unrestricted robot access (robot_id: {robot_id})")
        return True
    
    booking_service = service_manager.get_booking_service()
    
    # Check if user has active session for this specific robot
    return booking_service.has_active_robot_session(user_id, robot_id)

async def getRobotWebRTCUrl(robot_type: str, current_user: dict) -> dict:
    """Get robot WebRTC URL for direct connection"""
    user_id = int(current_user["sub"])
    
    # Get robot by type from registry
    robot = db.get_active_robot_by_type(robot_type)
    if not robot:
        raise HTTPException(
            status_code=404,
            detail=f"No active robot found with type '{robot_type}'"
        )
    
    robot_id = robot.get('id')
    
    # Validate user has active booking session for this robot  
    if not await has_booking_for_robot(user_id, robot_id, current_user):
        raise HTTPException(
            status_code=403,
            detail="To access the real-time robot feed, please book the service. Video access requires an active booking session."
        )
    
    webrtc_url = robot.get('webrtc_url')
    if not webrtc_url:
        raise HTTPException(
            status_code=404,  
            detail=f"Robot {robot_id} does not have a WebRTC URL configured"
        )
    
    return {
        "robot_id": robot_id,
        "robot_name": robot.get("name", "Unknown"),
        "robot_type": robot_type,
        "webrtc_url": webrtc_url,
        "message": "Connect directly to robot WebRTC server using this URL"
    }

async def sendOfferToRobot(webrtc_url: str, offer: dict) -> dict:
    """Send offer directly to robot WebRTC server"""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{webrtc_url}/offer", json=offer, timeout=10) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=502,
                        detail=f"Robot WebRTC server returned {response.status}"
                    )
                result = await response.json()
                return result
    except aiohttp.ClientError as e:
        logger.error(f"Failed to send offer to robot at {webrtc_url}: {e}")
        raise HTTPException(
            status_code=503,
            detail="Failed to connect to robot WebRTC server"
        )

@app.post("/webrtc/offer")
async def handle_webrtc_offer(offer: WebRTCOffer, current_user: dict = Depends(get_current_user)):
    """Handle WebRTC SDP offer from client - now returns robot WebRTC URL for direct connection"""
    user_id = int(current_user["sub"])
    
    # Resolve robot_id from offer (supports both robot_id and robot_type)
    robot_id = await resolve_robot_id(offer)
    
    # Validate user has active booking session for this robot
    if not await has_booking_for_robot(user_id, robot_id, current_user):
        robot = db.get_robot_by_id(robot_id)
        robot_type = robot.get('type', 'unknown') if robot else 'unknown'
        raise HTTPException(
            status_code=403,
            detail=f"To access the real-time robot feed, please book the service. Video access requires an active booking session."
        )
    
    # Get robot details including webrtc_url
    robot = db.get_robot_by_id(robot_id)
    if not robot:
        raise HTTPException(status_code=404, detail=f"Robot with ID {robot_id} not found")
    
    webrtc_url = robot.get('webrtc_url')
    if not webrtc_url:
        raise HTTPException(
            status_code=404, 
            detail=f"Robot {robot_id} does not have a WebRTC URL configured"
        )
    
    robot_name = robot.get("name", "Unknown")
    robot_type = robot.get("type", "Unknown")
    
    logger.info(f"Providing WebRTC URL for robot {robot_name} (ID: {robot_id}, Type: {robot_type}): {webrtc_url}")
    
    # Return the robot's WebRTC signaling endpoint instead of handling the offer
    return {
        "robot_id": robot_id,
        "robot_name": robot_name,
        "robot_type": robot_type,
        "webrtc_url": webrtc_url,
        "message": "Connect directly to robot WebRTC server using this URL"
    }

@app.post("/webrtc/answer")
async def handle_webrtc_answer(answer: WebRTCAnswer, current_user: dict = Depends(get_current_user)):
    """Handle WebRTC SDP answer from client - forwards to robot WebRTC server"""
    user_id = int(current_user["sub"])
    
    # Resolve robot_id from answer
    robot_id = await resolve_robot_id_from_answer(answer)
    
    # Validate user has active booking session for this robot
    if not await has_booking_for_robot(user_id, robot_id, current_user):
        robot = db.get_robot_by_id(robot_id)
        robot_type = robot.get('type', 'unknown') if robot else 'unknown'
        raise HTTPException(
            status_code=403,
            detail="To access the real-time robot feed, please book the service. Video access requires an active booking session."
        )
    
    # Get robot details including webrtc_url
    robot = db.get_robot_by_id(robot_id)
    if not robot:
        raise HTTPException(status_code=404, detail=f"Robot with ID {robot_id} not found")
    
    webrtc_url = robot.get('webrtc_url')
    if not webrtc_url:
        raise HTTPException(
            status_code=404, 
            detail=f"Robot {robot_id} does not have a WebRTC URL configured"
        )
    
    robot_name = robot.get("name", "Unknown")
    robot_type = robot.get("type", "Unknown")
    
    logger.info(f"Forwarding WebRTC answer for robot {robot_name} (ID: {robot_id}, Type: {robot_type})")
    
    # In a real implementation, this would forward the answer to the robot's WebRTC server
    # For now, we return the robot's WebRTC URL for direct connection
    return {
        "robot_id": robot_id,
        "robot_name": robot_name,
        "robot_type": robot_type,
        "webrtc_url": webrtc_url,
        "message": "Answer should be sent directly to robot WebRTC server",
        "status": "forwarded"
    }

@app.post("/webrtc/ice-candidate")
async def handle_ice_candidate(ice_candidate: WebRTCIceCandidate, current_user: dict = Depends(get_current_user)):
    """Handle WebRTC ICE candidate from client - forwards to robot WebRTC server"""
    user_id = int(current_user["sub"])
    
    # Resolve robot_id from ice candidate
    robot_id = await resolve_robot_id_from_ice(ice_candidate)
    
    # Validate user has active booking session for this robot
    if not await has_booking_for_robot(user_id, robot_id, current_user):
        robot = db.get_robot_by_id(robot_id)
        robot_type = robot.get('type', 'unknown') if robot else 'unknown'
        raise HTTPException(
            status_code=403,
            detail="To access the real-time robot feed, please book the service. Video access requires an active booking session."
        )
    
    # Get robot details including webrtc_url
    robot = db.get_robot_by_id(robot_id)
    if not robot:
        raise HTTPException(status_code=404, detail=f"Robot with ID {robot_id} not found")
    
    webrtc_url = robot.get('webrtc_url')
    if not webrtc_url:
        raise HTTPException(
            status_code=404, 
            detail=f"Robot {robot_id} does not have a WebRTC URL configured"
        )
    
    robot_name = robot.get("name", "Unknown")
    robot_type = robot.get("type", "Unknown")
    
    logger.info(f"Forwarding ICE candidate for robot {robot_name} (ID: {robot_id}, Type: {robot_type})")
    
    # In a real implementation, this would forward the ICE candidate to the robot's WebRTC server
    # For now, we return the robot's WebRTC URL for direct connection
    return {
        "robot_id": robot_id,
        "robot_name": robot_name,
        "robot_type": robot_type,
        "webrtc_url": webrtc_url,
        "message": "ICE candidate should be sent directly to robot WebRTC server",
        "status": "forwarded"
    }

@app.get("/webrtc/health")
async def webrtc_health_check():
    """Health check for WebRTC services"""
    try:
        # Check if WebRTC configuration is valid
        ice_servers = [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"},
        ]
        
        # Check if any robots have WebRTC URLs configured
        robots = db.get_all_robots()
        webrtc_robots = [r for r in robots if r.get('webrtc_url')]
        
        return {
            "status": "healthy",
            "ice_servers_configured": len(ice_servers) > 0,
            "robots_with_webrtc": len(webrtc_robots),
            "total_robots": len(robots),
            "webrtc_endpoints": [
                "/webrtc/offer",
                "/webrtc/answer", 
                "/webrtc/ice-candidate",
                "/webrtc/config",
                "/webrtc/health"
            ]
        }
    except Exception as e:
        logger.error(f"WebRTC health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

# Legacy WebRTC endpoints - deprecated in favor of direct robot connection
# Keeping minimal versions for backward compatibility during transition

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
        {"urls": f"stun:{os.getenv('VPS_URL', '174.232.105.47').replace('http://', '').replace('https://', '')}:3478"},
        {
            "urls": f"turn:{os.getenv('VPS_URL', '174.232.105.47').replace('http://', '').replace('https://', '')}:5349",
            "username": "robotuser",
            "credential": "robotpass"
        }
    ]
    
    return {
        "ice_servers": ice_servers,
        "ice_transport_policy": "all",  # Use both STUN and TURN
        "bundle_policy": "max-bundle"
    }

# ──────────────────────────────────────────────────────────────────────────────
# Community
# ──────────────────────────────────────────────────────────────────────────────

def _rank_for(total: int) -> dict:
    if total >= 500:
        return {"rank": "Legend",        "emoji": "🚀", "color": "purple"}
    if total >= 200:
        return {"rank": "Diamond",       "emoji": "💎", "color": "cyan"}
    if total >= 100:
        return {"rank": "Gold Member",   "emoji": "🥇", "color": "gold"}
    if total >= 50:
        return {"rank": "Silver Member", "emoji": "🥈", "color": "silver"}
    if total >= 10:
        return {"rank": "Member",        "emoji": "🔵", "color": "blue"}
    return      {"rank": "Newbie",       "emoji": "🤖", "color": "gray"}


def _enrich(item: dict) -> dict:
    """Attach rank info to any dict that has total_messages."""
    item["rank_info"] = _rank_for(item.get("total_messages", 0))
    return item


@app.get("/community/posts")
async def community_get_posts(
    page: int = 1,
    limit: int = 20,
    current_user: dict = Depends(get_current_user),
):
    limit = min(max(limit, 1), 50)
    result = db.get_community_posts(page=page, limit=limit)
    result["posts"] = [_enrich(p) for p in result["posts"]]
    return result


@app.post("/community/posts")
async def community_create_post(
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["sub"])
    if db.is_community_blocked(user_id):
        raise HTTPException(status_code=403, detail="You have been blocked from community posting.")
    body = await request.json()
    content = (body.get("content") or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Content cannot be empty.")
    if len(content) > 1000:
        raise HTTPException(status_code=400, detail="Post must be 1000 characters or less.")
    post = db.create_community_post(user_id, content)
    return _enrich(post)


@app.get("/community/posts/{post_id}/replies")
async def community_get_replies(
    post_id: int,
    current_user: dict = Depends(get_current_user),
):
    replies = db.get_community_replies(post_id)
    return [_enrich(r) for r in replies]


@app.post("/community/posts/{post_id}/reply")
async def community_create_reply(
    post_id: int,
    request: Request,
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["sub"])
    if db.is_community_blocked(user_id):
        raise HTTPException(status_code=403, detail="You have been blocked from community posting.")
    body = await request.json()
    content = (body.get("content") or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Reply cannot be empty.")
    if len(content) > 500:
        raise HTTPException(status_code=400, detail="Reply must be 500 characters or less.")
    try:
        reply = db.create_community_reply(post_id, user_id, content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _enrich(reply)


@app.delete("/community/posts/{post_id}")
async def community_delete_post(
    post_id: int,
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["sub"])
    is_admin = current_user.get("role") == "admin"
    try:
        ok = db.delete_community_post(post_id, user_id, is_admin)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="Post not found.")
    return {"success": True}


@app.delete("/community/replies/{reply_id}")
async def community_delete_reply(
    reply_id: int,
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["sub"])
    is_admin = current_user.get("role") == "admin"
    try:
        ok = db.delete_community_reply(reply_id, user_id, is_admin)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="Reply not found.")
    return {"success": True}


@app.get("/community/leaderboard")
async def community_leaderboard(
    current_user: dict = Depends(get_current_user),
):
    board = db.get_community_leaderboard(limit=10)
    return [_enrich(u) for u in board]


@app.get("/admin/community/users")
async def admin_community_users(current_user: dict = Depends(require_admin)):
    users = db.get_community_users_for_admin()
    return [_enrich(u) for u in users]


@app.patch("/admin/community/users/{user_id}/block")
async def admin_community_block(
    user_id: int,
    request: Request,
    current_user: dict = Depends(require_admin),
):
    body = await request.json()
    blocked = bool(body.get("blocked", True))
    ok = db.set_community_blocked(user_id, blocked)
    if not ok:
        raise HTTPException(status_code=404, detail="User not found.")
    action = "blocked" if blocked else "unblocked"
    logger.info(f"Admin {current_user['sub']} {action} user {user_id} from community")
    return {"success": True, "user_id": user_id, "community_blocked": blocked}


# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
