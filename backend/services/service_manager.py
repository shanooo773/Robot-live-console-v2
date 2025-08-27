"""
Admin Service Manager - Coordinates core admin/booking services only
Provides health checks for authentication and booking functionality
"""

import logging
from typing import Dict, Any, List
from .auth_service import AuthService
from .booking_service import BookingService
from database import DatabaseManager

logger = logging.getLogger(__name__)

class AdminServiceManager:
    """
    Manages core admin/booking services for standalone admin backend.
    Provides authentication and booking functionality without simulation dependencies.
    """
    
    def __init__(self, db: DatabaseManager):
        self.db = db
        self.services = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize core admin services"""
        logger.info("🚀 Initializing admin backend services...")
        
        # Initialize core services (must always work)
        try:
            self.auth_service = AuthService(self.db)
            self.services['auth'] = self.auth_service
            logger.info("✅ Auth service initialized")
        except Exception as e:
            logger.error(f"❌ Critical: Auth service failed to initialize: {e}")
            raise
        
        try:
            self.booking_service = BookingService(self.db)
            self.services['booking'] = self.booking_service
            logger.info("✅ Booking service initialized")
        except Exception as e:
            logger.error(f"❌ Critical: Booking service failed to initialize: {e}")
            raise
        
        logger.info("🎉 Admin backend service initialization complete")
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of core admin services"""
        status = {
            "overall_status": "operational",
            "core_services_available": True,
            "services": {}
        }
        
        # Check core services
        core_services = ['auth', 'booking']
        core_available = True
        
        for service_name in core_services:
            service = self.services.get(service_name)
            if service and hasattr(service, 'get_status'):
                service_status = service.get_status()
                status['services'][service_name] = service_status
                if not service_status.get('available', False):
                    core_available = False
            else:
                status['services'][service_name] = {
                    "service": service_name,
                    "available": False,
                    "status": "failed",
                    "error": "Service not initialized"
                }
                core_available = False
        
        status['core_services_available'] = core_available
        
        # Set overall status
        if not core_available:
            status['overall_status'] = "degraded"
        
        return status
    
    def get_available_features(self) -> Dict[str, List[str]]:
        """Get list of available features for admin backend"""
        features = {
            "always_available": [],
            "unavailable": []
        }
        
        # Auth features
        if self.services.get('auth') and self.services['auth'].available:
            features["always_available"].extend([
                "user_registration",
                "user_login", 
                "user_authentication",
                "role_management"
            ])
        else:
            features["unavailable"].extend([
                "user_registration",
                "user_login",
                "user_authentication", 
                "role_management"
            ])
        
        # Booking features
        if self.services.get('booking') and self.services['booking'].available:
            features["always_available"].extend([
                "robot_booking",
                "schedule_management",
                "booking_history",
                "booking_cancellation",
                "admin_dashboard"
            ])
        else:
            features["unavailable"].extend([
                "robot_booking",
                "schedule_management",
                "booking_history",
                "booking_cancellation",
                "admin_dashboard"
            ])
        
        # Simulation features are not available in admin backend
        features["unavailable"].extend([
            "robot_simulation",
            "gazebo_simulation",
            "video_recording"
        ])
        
        return features
    
    def is_core_available(self) -> bool:
        """Check if core services are available"""
        return (self.services.get('auth') and self.services['auth'].available and
                self.services.get('booking') and self.services['booking'].available)
    
    def get_auth_service(self) -> AuthService:
        """Get auth service instance"""
        if not self.services.get('auth'):
            raise RuntimeError("Auth service not available")
        return self.services['auth']
    
    def get_booking_service(self) -> BookingService:
        """Get booking service instance"""
        if not self.services.get('booking'):
            raise RuntimeError("Booking service not available")
        return self.services['booking']