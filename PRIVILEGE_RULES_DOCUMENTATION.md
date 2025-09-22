# Privilege Rules and Access Control Documentation

## Overview

This document defines the privilege rules and expected behaviors for the Robot Live Console system, addressing all requirements from the problem statement for strict control, accurate data visibility, and comprehensive access management.

## Privilege Levels

### 1. Demo User Accounts
**Purpose**: Demonstration and testing of user-level features

**Access Rights**:
- ✅ Create bookings for robot sessions
- ✅ View their own booking history
- ✅ Access development console during booked times
- ✅ Check available time slots
- ✅ Submit contact messages
- ✅ View public announcements
- ✅ Direct console access in demo mode (bypasses booking requirements)

**Restrictions**:
- ❌ Cannot access admin dashboard
- ❌ Cannot view other users' bookings
- ❌ Cannot manage robots or system settings
- ❌ Cannot view admin statistics
- ❌ Cannot manage announcements

**Implementation Details**:
- Identified by email patterns containing: 'demo', 'test', 'example'
- Frontend shows "DEMO MODE" badge
- Can use unrestricted access features for demonstration
- Data is filtered out from admin views to maintain clean production data

### 2. Demo Admin Accounts
**Purpose**: Demonstration of administrative capabilities

**Access Rights**:
- ✅ All user-level features
- ✅ Full admin dashboard access
- ✅ User management capabilities
- ✅ Booking management and oversight
- ✅ System monitoring and statistics
- ✅ Robot/device management
- ✅ Announcement management
- ✅ Container management (Theia)
- ✅ All administrative endpoints

**Special Handling**:
- Tracked separately in audit logs with "🎯 DEMO ADMIN ACCESS" marker
- Maintains full admin privileges for demonstration purposes
- Data may be filtered from production admin views depending on configuration

**Implementation Details**:
- Identified by role='admin' AND email containing demo indicators
- Frontend shows both "Admin" and "DEMO MODE" badges
- Logged distinctly for audit purposes

### 3. Real Admin Accounts
**Purpose**: Production system administration

**Access Rights**:
- ✅ All user-level features
- ✅ Full admin dashboard access with real data only
- ✅ Comprehensive user management
- ✅ Full booking system oversight
- ✅ System monitoring and analytics
- ✅ Robot/device lifecycle management
- ✅ Announcement and communication management
- ✅ Infrastructure management (containers, services)
- ✅ Audit log access

**Data Visibility**:
- Only real user data (demo/test data filtered out)
- Only admin-managed robots visible
- Real-time system status and metrics
- Actionable insights and analytics

**Implementation Details**:
- Identified by role='admin' AND email NOT containing demo indicators
- All admin actions logged with "✅ ADMIN ACCESS GRANTED" marker
- Database connection required (no fallback demo data)

### 4. Regular Users
**Purpose**: Standard system usage

**Access Rights**:
- ✅ Create and manage their own bookings
- ✅ Access development console during booked times
- ✅ View available time slots
- ✅ Submit contact messages
- ✅ View public announcements

**Restrictions**:
- ❌ Cannot access admin features
- ❌ Cannot view other users' data
- ❌ Cannot manage system resources

## Authentication and Authorization

### Authentication Requirements
- All API endpoints require valid JWT token
- Session-based authentication for web interface
- Enhanced logging for all authentication attempts

### Authorization Matrix

| Feature | Demo User | Demo Admin | Real Admin | Regular User |
|---------|-----------|------------|------------|--------------|
| View own bookings | ✅ | ✅ | ✅ | ✅ |
| Create bookings | ✅ | ✅ | ✅ | ✅ |
| Direct console access | ✅ (demo mode) | ✅ | ✅ | ❌ |
| View all bookings | ❌ | ✅ | ✅ | ❌ |
| Admin dashboard | ❌ | ✅ | ✅ | ❌ |
| User management | ❌ | ✅ | ✅ | ❌ |
| Robot management | ❌ | ✅ | ✅ | ❌ |
| System statistics | ❌ | ✅ | ✅ (real data) | ❌ |
| Audit logs | ❌ | Limited | ✅ | ❌ |

## Data Filtering and Visibility

### Admin Dashboard Data Filtering
Real admin accounts see only:
- Real users (excluding demo/test accounts)
- Real bookings (excluding demo/test bookings)
- Admin-managed robots (status: active/inactive)
- Real messages and communications
- Accurate system statistics

### Demo Data Handling
- Demo data is filtered out of production admin views
- Demo accounts maintain full functional access
- No demo fallback data in admin endpoints
- Database unavailability results in proper error responses, not demo data

## Booking System Controls

### Double Booking Prevention
- Strict overlap detection for all booking requests
- Real-time conflict checking
- Enhanced validation for time ranges
- Comprehensive audit logging for all attempts

### Authentication Checks
- User ID validation for all booking operations
- Session verification for console access
- Time-based access control (only during booked slots)
- Enhanced logging: "🔒 BOOKING ATTEMPT", "✅ BOOKING CREATED", "❌ BOOKING REJECTED"

### Audit Logging
All booking activities logged with:
- User identification
- Timestamp
- Action performed
- Result (success/failure)
- Conflict details (if applicable)
- Admin actions (if applicable)

## Robot and Device Visibility

### Visibility Rules
- Only admin-managed robots are visible in admin interfaces
- Robot status must be 'active' or 'inactive' to be shown
- Demo robots filtered out of production views
- Real-time status updates only

### Management Controls
- Only admins can add/modify robots
- Status changes logged with admin identification
- Device lifecycle managed through admin actions only

## Security Measures

### Endpoint Protection
- All admin endpoints require admin role validation
- Enhanced privilege checking with audit logging
- Proper error responses for unauthorized access
- Session-based access control

### Audit Trail
- All admin access logged: "🔐 ADMIN ACCESS ATTEMPT"
- Privilege escalation attempts recorded
- Failed authentication attempts tracked
- System modifications logged with user identification

### Error Handling
- No demo data fallbacks in production
- Proper HTTP error codes (503 for service unavailable)
- Clear error messages for privilege violations
- Database unavailability handled gracefully

## Expected Behaviors

### Normal Operations
1. **Demo Users**: Can book, access console, test features without restrictions
2. **Demo Admins**: Full admin access with demo tracking in logs
3. **Real Admins**: Full admin access with real data only, comprehensive logging
4. **Regular Users**: Standard booking and console access during booked times

### Error Conditions
1. **Database Unavailable**: Admin endpoints return 503, no demo fallbacks
2. **Invalid Authentication**: 401/403 responses with proper error messages
3. **Privilege Violations**: Logged and denied with appropriate responses
4. **Booking Conflicts**: Detailed conflict information and resolution guidance

### Monitoring and Alerts
1. **Admin Access**: All attempts logged for audit
2. **Privilege Escalation**: Failed admin access attempts flagged
3. **System Health**: Real-time monitoring without demo data pollution
4. **Booking Conflicts**: Detailed logging for conflict resolution

## Validation and Testing

### Automated Tests
- Demo user privilege validation
- Admin privilege verification
- Booking control enforcement
- Authentication requirement testing
- Data filtering validation

### Manual Testing
- Admin dashboard real data verification
- Demo mode functionality testing
- Privilege escalation prevention
- Cross-user data access prevention

### Continuous Monitoring
- Audit log analysis
- Privilege structure integrity
- Access pattern monitoring
- Security violation detection

## Implementation Notes

### Code Locations
- **Authentication**: `backend/auth.py`
- **Booking Service**: `backend/services/booking_service.py`
- **Admin Endpoints**: `backend/main.py`
- **Frontend Privileges**: `frontend/src/components/BookingPage.jsx`

### Configuration
- Demo user patterns: configurable email indicators
- Admin access logging: comprehensive audit trail
- Data filtering: automatic based on user type
- Error handling: strict no-fallback policy for admin data

This documentation ensures all stakeholders understand the privilege structure and can verify proper implementation of the security and access control requirements specified in the problem statement.