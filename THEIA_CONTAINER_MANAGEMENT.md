# Automatic Docker Container Management for Eclipse Theia IDE

## Overview

This implementation provides comprehensive automatic Docker container management for Eclipse Theia IDE with the following features:

- **Per-user containers**: Each user gets their own container named `theia-<userid>`
- **Persistent user directories**: Maps `/data/users/<userid>` to `/home/project` inside containers
- **Unique port allocation**: Dynamic port assignment in the 4000-9000 range with database persistence
- **Container lifecycle management**: Automatic startup, cleanup on logout/timeout
- **Frontend integration**: Iframe loads IDE from correct user-specific port

## Requirements Compliance

### ✅ Per-user containers
- Container naming: `theia-<userid>` (e.g., `theia-123` for user ID 123)
- Each user gets an isolated container environment

### ✅ User directory mounting  
- Host directory: `/data/users/<userid>`
- Container mount: `/home/project`
- Auto-creates directories on first login
- Files persist between container restarts

### ✅ Unique port allocation
- Port range: 4000-9000 (configurable)
- Database-backed persistence for consistent reuse
- Conflict detection and resolution
- Automatic port release on container cleanup

### ✅ Container startup command
```bash
docker run -d \
  --name theia-${USERID} \
  -p ${ASSIGNED_PORT}:3000 \
  -v /data/users/${USERID}:/home/project \
  theiaide/theia:latest
```

### ✅ Frontend integration
- React component loads IDE via iframe from `http://<server-ip>:${ASSIGNED_PORT}`
- Automatic status checking and container startup
- Error handling and user feedback

### ✅ Container lifecycle
- Starts on user login (if not already running)
- Stops and removes after inactivity timeout or logout
- Recreates on next login with same directory and port
- Database persistence ensures consistent port assignments

## Database Schema

The implementation adds a `theia_port` column to the `users` table:

```sql
ALTER TABLE users ADD COLUMN theia_port INTEGER DEFAULT NULL;
```

New database methods:
- `get_user_theia_port(user_id)` - Get stored port for user
- `set_user_theia_port(user_id, port)` - Store port assignment
- `clear_user_theia_port(user_id)` - Remove port assignment
- `get_all_assigned_ports()` - Get all currently assigned ports

## Configuration

### Environment Variables

For production deployment, set these environment variables:

```bash
# Directory Configuration
THEIA_PROJECT_PATH=/data/users

# Port Configuration  
THEIA_BASE_PORT=4000
THEIA_MAX_PORT=9000
THEIA_MAX_CONTAINERS=100

# Container Configuration
THEIA_IMAGE=theiaide/theia:latest
DOCKER_NETWORK=robot-console-network

# Lifecycle Configuration
THEIA_IDLE_TIMEOUT_HOURS=4
THEIA_LOGOUT_GRACE_MINUTES=10

# Network Configuration
SERVER_HOST=172.232.105.47  # Or your server IP
```

### Development vs Production

**Development** (default settings):
- Project path: `./projects` (relative to backend directory)
- Graceful fallback if `/data/users` is not accessible
- Server host: `localhost`

**Production** (with environment variables):
- Project path: `/data/users` (absolute path)
- Server host: Configured IP address
- Extended timeouts for production use

## File Structure

```
/data/users/
├── 123/                    # User ID 123's workspace
│   ├── welcome.py         # Auto-generated welcome file
│   ├── robot_example.cpp  # Auto-generated C++ example
│   └── ...                # User's files persist here
├── 456/                   # User ID 456's workspace
│   └── ...
└── -1/                    # Demo user workspace
    └── ...
```

## API Endpoints

The following endpoints manage Theia containers:

- `POST /theia/start` - Start user's container
- `GET /theia/status` - Get container status (auto-starts if needed)
- `POST /theia/stop` - Stop user's container
- `POST /theia/restart` - Restart user's container

Admin endpoints:
- `POST /theia/admin/restart/{user_id}` - Restart any user's container
- `GET /theia/admin/status/{user_id}` - Get any user's container status

## Frontend Integration

The `TheiaIDE` React component:
1. Checks container status via `/theia/status`
2. Auto-starts container if not running
3. Loads IDE in iframe from returned URL
4. Handles errors and provides user feedback
5. Supports container management controls

## Security Considerations

- Each user's container is isolated
- User directories are mounted with appropriate permissions
- Port allocation prevents conflicts between users
- Database persistence prevents port hijacking
- Container cleanup prevents resource leaks

## Deployment Instructions

1. **Create data directory:**
   ```bash
   sudo mkdir -p /data/users
   sudo chown -R www-data:www-data /data/users  # Or appropriate user
   ```

2. **Set environment variables:**
   ```bash
   export THEIA_PROJECT_PATH=/data/users
   export SERVER_HOST=your-server-ip
   # ... other variables as needed
   ```

3. **Ensure Docker is installed and running:**
   ```bash
   docker --version
   docker pull theiaide/theia:latest
   ```

4. **Database migration:**
   The database will automatically add the `theia_port` column on startup.

5. **Start the backend:**
   The Theia service will initialize with database persistence.

## Monitoring and Maintenance

- Monitor container count: `docker ps | grep theia- | wc -l`
- Check resource usage: `docker stats`
- Clean up stale containers: Built-in automatic cleanup
- Port allocation status: Available via admin endpoints

## Troubleshooting

**Container won't start:**
- Check Docker is running: `docker --version`
- Verify image exists: `docker images | grep theia`
- Check port availability: `netstat -tlnp | grep :4000`

**Permission issues:**
- Ensure `/data/users` is writable by application user
- Check directory ownership and permissions

**Port conflicts:**
- Database tracks port assignments automatically
- Use admin endpoints to check user port status
- Restart backend to reload port mappings from database

**Database issues:**
- Service falls back to memory-only port allocation
- Port assignments may not persist across restarts without database