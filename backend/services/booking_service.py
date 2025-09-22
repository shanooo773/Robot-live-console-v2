from datetime import timedelta

"""
Booking Service - FIXED VERSION
Handles robot booking and scheduling with proper overlap detection and time comparison.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, time
from fastapi import HTTPException
from database import DatabaseManager

logger = logging.getLogger(__name__)

class BookingServiceException(Exception):
    """Exception raised when booking service encounters an error"""
    pass

class BookingService:
    """
    Service for handling robot bookings and scheduling.
    FIXED VERSION with proper overlap detection and time comparison.
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
    
    def _parse_time_string(self, time_str: str) -> time:
        """Parse time string (HH:MM) to time object, enforcing 24-hour format"""
        try:
            return datetime.strptime(time_str.strip(), "%H:%M").time()
        except ValueError as e:
            logger.error(f"❌ Invalid time format '{time_str}', expected HH:MM (24-hour). Error: {e}")
            raise ValueError(f"Invalid time format: {time_str}, expected HH:MM (24-hour)")

    def _times_overlap(self, start1: str, end1: str, start2: str, end2: str) -> bool:
        """Check if two time ranges overlap"""
        try:
            t1_start = self._parse_time_string(start1)
            t1_end = self._parse_time_string(end1)
            t2_start = self._parse_time_string(start2)
            t2_end = self._parse_time_string(end2)
            
            # Two ranges overlap if: start1 < end2 AND start2 < end1
            return t1_start < t2_end and t2_start < t1_end
        except ValueError as e:
            logger.error(f"Error comparing times: {e}")
            return False
    
    def validate_booking_time(self, date: str, start_time: str, end_time: str) -> bool:
        try:
            booking_date = datetime.strptime(date, "%Y-%m-%d")
            start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")

            now = datetime.now()
            min_advance_time = now + timedelta(minutes=10)
            
            # Check if booking is not in the past
            if start_dt <= min_advance_time:
                logger.warning(f"❌ Booking start {start_dt} is in the past")
                return False
            if end_dt <= start_dt:
                logger.warning(f"❌ End time {end_dt} is not after start {start_dt}")
                return False

            # Validate working hours (9:00-18:00)
            start_time_obj = self._parse_time_string(start_time)
            end_time_obj = self._parse_time_string(end_time)
            working_start = time(9, 0)  # 9:00 AM
            working_end = time(18, 0)   # 6:00 PM
            
            if start_time_obj < working_start or start_time_obj >= working_end:
                logger.warning(f"❌ Booking start {start_time} outside working hours (9:00-18:00)")
                return False
            if end_time_obj > working_end:
                logger.warning(f"❌ Booking end {end_time} outside working hours (9:00-18:00)")
                return False

            # Validate maximum session duration (2 hours)
            duration = (end_dt - start_dt).total_seconds() / 3600
            if duration > 2:
                logger.warning(f"❌ Booking too long ({duration} hours), maximum allowed is 2 hours")
                return False
            
            # Validate minimum session duration (30 minutes)
            if duration < 0.5:
                logger.warning(f"❌ Booking too short ({duration} hours), minimum allowed is 30 minutes")
                return False

            # Confirm both times are valid 24-hour
            self._parse_time_string(start_time)
            self._parse_time_string(end_time)

            return True
        except ValueError as e:
            logger.error(f"❌ Validation failed: {e}")
            return False

    def create_booking(self, user_id: int, robot_type: str, date: str, 
                      start_time: str, end_time: str) -> Dict[str, Any]:
        """Create a new booking with proper overlap detection"""
        try:
            # Validate booking time first
            if not self.validate_booking_time(date, start_time, end_time):
                raise HTTPException(status_code=400, detail="Invalid booking time")
            
            # Check for conflicting bookings with PROPER overlap detection
            existing_bookings = self.db.get_bookings_for_date_range(date, date)
            for existing in existing_bookings:
                if (existing["robot_type"] == robot_type and 
                    existing["status"] == "active"):
                    
                    # Check for ANY overlap, not just exact matches
                    if self._times_overlap(start_time, end_time, 
                                         existing["start_time"], existing["end_time"]):
                        raise HTTPException(
                            status_code=400, 
                            detail=f"Time slot conflicts with existing booking from {existing['start_time']} to {existing['end_time']}"
                        )
            
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
    
    def has_active_session(self, user_id: int, robot_type: str) -> bool:
        """Check if user has an active booking session for the robot type - FIXED VERSION"""
        try:
            # Get current time
            now = datetime.now()
            current_date = now.strftime("%Y-%m-%d")
            current_time_obj = now.time()
            
            # Get user's bookings for today
            bookings = self.get_user_bookings(user_id)
            
            # Check for active booking that matches current time
            for booking in bookings:
                if (booking["robot_type"] == robot_type and 
                    booking["date"] == current_date and
                    booking["status"] == "active"):
                    
                    try:
                        # Parse booking times using proper time objects
                        start_time_obj = self._parse_time_string(booking["start_time"])
                        end_time_obj = self._parse_time_string(booking["end_time"])
                        
                        # Check if current time is within booking window using time objects
                        if start_time_obj <= current_time_obj <= end_time_obj:
                            logger.info(f"Active session found for user {user_id}, robot {robot_type} from {booking['start_time']} to {booking['end_time']}")
                            return True
                    except ValueError as e:
                        logger.error(f"Error parsing booking times: {e}")
                        continue
            
            logger.debug(f"No active session for user {user_id}, robot {robot_type} at {current_time_obj}")
            return False
            
        except Exception as e:
            logger.error(f"Error checking active session: {e}")
            return False
    
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
    
    def get_available_time_slots(self, date: str, robot_type: str) -> List[Dict[str, Any]]:
        """Get available time slots for a specific date and robot type"""
        try:
            # Parse the requested date
            requested_date = datetime.strptime(date, "%Y-%m-%d").date()
            today = datetime.now().date()
            
            # Don't allow booking for past dates
            if requested_date < today:
                return []
            
            # Get existing bookings for this date and robot type
            existing_bookings = self.db.get_bookings_for_date_range(date, date)
            robot_bookings = [
                b for b in existing_bookings 
                if b["robot_type"] == robot_type and b["status"] == "active"
            ]
            
            # Generate potential slots within working hours (9:00-18:00)
            available_slots = []
            working_start = 9  # 9 AM
            working_end = 18   # 6 PM
            slot_duration = 1  # 1 hour slots
            
            for hour in range(working_start, working_end):
                start_time = f"{hour:02d}:00"
                end_time = f"{hour + slot_duration:02d}:00"
                
                # Check if this slot conflicts with existing bookings
                slot_available = True
                for booking in robot_bookings:
                    if self._times_overlap(start_time, end_time, 
                                         booking["start_time"], booking["end_time"]):
                        slot_available = False
                        break
                
                # For today, also check if the slot is not in the past
                if requested_date == today:
                    current_time = datetime.now()
                    slot_start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
                    if slot_start_dt <= current_time + timedelta(minutes=10):
                        slot_available = False
                
                if slot_available:
                    available_slots.append({
                        "date": date,
                        "start_time": start_time,
                        "end_time": end_time,
                        "robot_type": robot_type,
                        "duration_hours": slot_duration
                    })
            
            logger.info(f"Found {len(available_slots)} available slots for {robot_type} on {date}")
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting available time slots: {e}")
            return []

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
