# Service Architecture Documentation

## Overview

The Robot Live Console backend has been restructured with a service-oriented architecture that provides complete separation between Docker-dependent simulation features and core application services (authentication and booking system).

## Service Architecture

### Core Services (Always Available)
These services are essential and must always work, regardless of Docker availability:

1. **Authentication Service** (`services/auth_service.py`)
   - User registration and login
   - JWT token management
   - Role-based access control
   - Independent of external dependencies

2. **Booking Service** (`services/booking_service.py`)
   - Robot booking and scheduling
   - Booking management and history
   - Conflict detection
   - Time slot validation

### Optional Services (Can Fail Gracefully)
These services provide enhanced functionality but the application remains functional without them:

1. **Docker Service** (`services/docker_service.py`)
   - Robot simulation via Gazebo
   - Video recording of simulations
   - Real-time robot control
   - Falls back to mock simulation when unavailable

## Service Manager

The `ServiceManager` class (`services/service_manager.py`) coordinates all services and provides:

- **Health checks** for individual services
- **Feature availability** reporting
- **Graceful degradation** when optional services fail
- **Service status** monitoring

## API Endpoints

### Health Check Endpoints

- `GET /health` - Overall system health
- `GET /health/services` - Detailed service status
- `GET /health/features` - Available features based on service status

### Service Behaviors

#### When Docker is Available
- Status: `"operational"`
- All features available including real robot simulation
- Full Gazebo simulation with video recording

#### When Docker is Unavailable
- Status: `"limited"` 
- Core services (auth, booking) remain fully functional
- Simulation falls back to mock mode with clear error messages
- Users can still register, login, and book robot sessions

## Error Handling

### Docker Service Failures
- **Initialization failure**: Service marked as unavailable, core services continue
- **Runtime failure**: Graceful fallback to mock simulation
- **Clear error messages**: Users informed about service limitations

### Core Service Failures
- **Authentication failure**: Application cannot start (critical error)
- **Booking failure**: Application cannot start (critical error)
- **Database failure**: Application cannot start (critical error)

## Configuration

No configuration changes required. The system automatically detects Docker availability through:

1. Docker SDK connection test
2. Docker CLI availability test
3. Container runtime verification

## Monitoring

### Service Status Response Example

```json
{
  "overall_status": "operational|limited|degraded",
  "core_services_available": true,
  "services": {
    "auth": {
      "service": "auth",
      "available": true,
      "status": "available",
      "features": ["registration", "login", "jwt_tokens", "role_management"]
    },
    "booking": {
      "service": "booking", 
      "available": true,
      "status": "available",
      "features": ["create_booking", "view_bookings", "cancel_booking", "admin_management"]
    },
    "docker": {
      "service": "docker",
      "available": false,
      "status": "unavailable",
      "error": "Docker not available"
    }
  }
}
```

### Feature Availability Response

```json
{
  "always_available": [
    "user_registration",
    "user_login", 
    "robot_booking",
    "schedule_management"
  ],
  "conditionally_available": [
    "mock_robot_simulation"
  ],
  "unavailable": [
    "real_robot_simulation",
    "gazebo_simulation",
    "video_recording"
  ]
}
```

## Benefits

1. **Improved Reliability**: Core features work even when Docker fails
2. **Better User Experience**: Clear indication of available features
3. **Easier Debugging**: Service-specific health checks and error messages
4. **Scalability**: Services can be moved to separate containers/servers
5. **Maintainability**: Clear separation of concerns and responsibilities

## Migration Impact

- **Existing APIs**: All endpoints remain compatible
- **Frontend**: No changes required for basic functionality
- **Database**: No schema changes required
- **Docker**: Optional - application works without it