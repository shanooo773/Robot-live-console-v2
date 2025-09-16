"""
Booking Service - Handles robot booking and scheduling
This service is completely independent of Docker and should always be available.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import HTTPException
from database import DatabaseManager

logger = logging.getLogger(__name__)

class BookingServiceException(Exception):
    """Exception raised when booking service encounters an error"""
    pass

class BookingService:
    """
    Service for handling robot bookings and scheduling.
    This service operates independently of Docker and other services.
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.available = True
        self.status = "available"
        logger.info("✅ Booking service initialized successfully")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current service status"""
        return {
            "service": "booking",
            "available": self.available,
            "status": self.status,
            "features": ["create_booking", "view_bookings", "cancel_booking", "admin_management"]
        }
    
    def create_booking(self, user_id: int, robot_type: str, date: str, 
                      start_time: str, end_time: str) -> Dict[str, Any]:
        """Create a new booking"""
        try:
            # Check for conflicting bookings
            existing_bookings = self.db.get_bookings_for_date_range(date, date)
            for existing in existing_bookings:
                if (existing["robot_type"] == robot_type and
                    existing["start_time"] == start_time and
                    existing["end_time"] == end_time and
                    existing["status"] == "active"):
                    raise HTTPException(status_code=400, detail="Time slot already booked")
            
            booking = self.db.create_booking(
                user_id=user_id,
                robot_type=robot_type,
                date=date,
                start_time=start_time,
                end_time=end_time
            )
            return booking
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to create booking: {e}")
            raise BookingServiceException(f"Failed to create booking: {str(e)}")
    
    def get_user_bookings(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all bookings for a user"""
        try:
            return self.db.get_user_bookings(user_id)
        except Exception as e:
            logger.error(f"Failed to get user bookings: {e}")
            raise BookingServiceException(f"Failed to get user bookings: {str(e)}")
    
    def get_all_bookings(self) -> List[Dict[str, Any]]:
        """Get all bookings (admin only)"""
        try:
            return self.db.get_all_bookings()
        except Exception as e:
            logger.error(f"Failed to get all bookings: {e}")
            raise BookingServiceException(f"Failed to get all bookings: {str(e)}")
    
    def update_booking_status(self, booking_id: int, status: str) -> Dict[str, Any]:
        """Update booking status"""
        try:
            booking = self.db.update_booking_status(booking_id, status)
            if not booking:
                raise HTTPException(status_code=404, detail="Booking not found")
            return booking
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update booking status: {e}")
            raise BookingServiceException(f"Failed to update booking status: {str(e)}")
    
    def get_available_robots(self) -> Dict[str, Any]:
        """Get available robot types and their descriptions"""
        return {
            "arm": {
                "name": "Robotic Arm",
                "description": "6-DOF robotic arm for pick and place operations"
            },
            "hand": {
                "name": "Dexterous Hand", 
                "description": "Multi-fingered hand for complex manipulation tasks"
            },
            "turtlebot": {
                "name": "TurtleBot",
                "description": "Mobile robot platform for navigation and exploration"
            }
        }
    
    def validate_booking_time(self, date: str, start_time: str, end_time: str) -> bool:
        """Validate booking time constraints"""
        try:
            # Parse date and times to validate format
            booking_date = datetime.strptime(date, "%Y-%m-%d")
            start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
            
            # Check if booking is in the future
            now = datetime.now()
            if start_dt <= now:
                return False
            
            # Check if end time is after start time
            if end_dt <= start_dt:
                return False
            
            # Check if booking duration is reasonable (e.g., max 4 hours)
            duration = (end_dt - start_dt).total_seconds() / 3600
            if duration > 4:
                return False
            
            return True
        except ValueError:
            return False
    
    def has_active_session(self, user_id: int, robot_type: str) -> bool:
        """Check if user has an active booking session for the robot type"""
        try:
            # Get current time
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time = now.strftime("%H:%M")
            
            # Get user's bookings for today
            bookings = self.get_user_bookings(user_id)
            
            # Check for active booking that matches current time
            for booking in bookings:
                if (booking["robot_type"] == robot_type and 
                    booking["date"] == current_date and
                    booking["status"] == "active"):
                    
                    # Parse booking times
                    start_time = booking["start_time"]
                    end_time = booking["end_time"]
                    
                    # Check if current time is within booking window
                    if start_time <= current_time <= end_time:
                        logger.info(f"Active session found for user {user_id}, robot {robot_type} from {start_time} to {end_time}")
                        return True
            
            logger.debug(f"No active session for user {user_id}, robot {robot_type} at {current_time}")
            return False
            
        except Exception as e:
            logger.error(f"Error checking active session: {e}")
            return False