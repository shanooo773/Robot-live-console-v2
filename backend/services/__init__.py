"""
Admin Backend Services - Core authentication and booking services only

Note: TheiaContainerManager is imported separately to avoid database dependencies
during isolated testing.
"""

# Core services with database dependencies
# from .auth_service import AuthService
# from .booking_service import BookingService  
# from .service_manager import AdminServiceManager

# Import only when needed to avoid circular dependencies
__all__ = ["AuthService", "BookingService", "AdminServiceManager", "TheiaContainerManager"]

def get_auth_service():
    from .auth_service import AuthService
    return AuthService

def get_booking_service():
    from .booking_service import BookingService
    return BookingService

def get_service_manager():
    from .service_manager import AdminServiceManager
    return AdminServiceManager

def get_theia_manager():
    from .theia_service import TheiaContainerManager
    return TheiaContainerManager