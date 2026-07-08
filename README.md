# 🤖 Anybot — Robot Live Console

A modern web application for robot control and simulation with secure user authentication, a booking system, and a dual-container **Eclipse Theia IDE** (always-on preview + robot-connected booking sessions).

## 🏗️ Architecture

The repository root is the project root — there is no `app/` wrapper directory:

```
.
├── frontend/           # React + Vite app (Theia IDE embed, video panel, booking UI)
├── backend/            # Python FastAPI (auth, booking, Theia container management, video)
├── theia/              # Legacy Theia container scripts (superseded by backend/services/theia_service.py)
├── projects/           # Per-user workspace directories, shared by preview & booking containers
├── docker/             # docker/deploy (frontend + WebRTC bridge compose), docker/frontend
├── services/           # services/webrtc-bridge (GStreamer WebRTC signaling bridge)
├── scripts/            # setup.sh / deploy.sh automation
├── docs/               # ADMIN_GUIDE.md, PRODUCTION_DEPLOYMENT.md
├── migrations/         # Database migrations
├── build.sh            # Local build/setup helper
├── deploy_vps.sh       # Production VPS deployment script
└── README.md           # This file
```

## ✨ Features

### 🔐 Secure User Flow
- **Home Page**: Landing page for first-time visitors
- **Authentication**: Secure sign-in/sign-up system
- **Booking System**: Time slot booking for robot access
- **Access Control**: Live robot video and robot-connected code execution require an active booking; the IDE itself is always available

### 💻 Development Interface — Preview & Booking containers

Every user gets **two independent Eclipse Theia containers**, both mounting the same workspace so code carries over between them:

| | Preview (`theia-preview-<user_id>`) | Booking (`theia-booking-<user_id>`) |
|---|---|---|
| **Image** | `elswork/theia` (env: `THEIA_IMAGE`) | Robot-specific ROS 2 image (env: `THEIA_BOOKING_IMAGE`, per-robot override in admin dashboard) |
| **Lifetime** | Always-on — pre-warmed in the background as soon as the user logs in | Only while a booking is active |
| **Purpose** | Write/edit code anytime, no booking needed | Run code against the real/simulated robot over the built-in P2P VPN |
| **Workspace** | `/projects/<user_id>/` → `/home/project` | Same directory — shared with preview |

- **Two-Panel Layout**:
  - **Left Panel**: Embedded Theia IDE — automatically points at the booking container while a booking is active, otherwise at the preview container
  - **Right Panel**: Live robot video (WebRTC), only available during an active booking; shows a "Book a Session" prompt otherwise
- **"Get Result Video"**: Fetches a pre-saved simulation clip for the booked robot type
- **Robot Selection**: Support for TurtleBot3, Robot Arm, and Robot Hand (extensible via the admin robot registry)

### 🌐 Built-in P2P VPN
Each Theia container (preview and booking) is started with `--cap-add NET_ADMIN --device /dev/net/tun`, and the P2P VPN client itself is **baked into the Docker image** (`elswork/theia` for preview, the robot-specific ROS 2 image for booking) — it connects automatically on container start with no extra configuration. There is no separate VPN bridge service to run.

### 🎥 Video System
- **WebRTC video player**: Streams live from the robot's camera, gated by an active booking
- **Pre-saved simulation clips**: "Get Result Video" for offline/demo viewing
- **Signaling bridge**: Optional `services/webrtc-bridge` Docker service relays RTSP → WebRTC (see [Docker Deployment](#-docker-deployment-optional))

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Docker & Docker Compose
- npm

### 1. Setup and Build

```bash
./build.sh
```

This will:
- Pull the Eclipse Theia preview image (`elswork/theia`)
- Install backend and frontend dependencies
- Build the frontend

### 2. Start Services

**Backend:**
```bash
cd backend
source venv/bin/activate
python main.py
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 4. Default Admin Account

- **Email**: admin@example.com  
- **Password**: admin123

## 🐳 Docker Deployment (Optional)

Docker support is available for the **frontend** and **WebRTC bridge** services:

```bash
cd docker/deploy
docker compose up -d --build
```

> **⚠️ IMPORTANT**: 
> 1. The Docker setup requires `services/webrtc-bridge/bridge_service.py` to exist. This file must implement the GStreamer webrtcbin pipeline for WebRTC streaming. If this file doesn't exist, the Docker Compose build will fail.
> 2. You must add `BRIDGE_CONTROL_SECRET` to `backend/.env` for bridge authorization to work.

**What's included:**
- Frontend: React dev server in Docker with hot-reload
- WebRTC Bridge: GStreamer-based bridge with hardware acceleration support (NVENC/VAAPI)

**What's NOT included:**
- Backend: Must run separately on host (see "Quick Start" above)
- Theia containers: Managed by the backend directly via the Docker CLI, not part of this compose file

For detailed Docker setup instructions, hardware acceleration configuration, and troubleshooting, see [`docker/deploy/README.md`](docker/deploy/README.md).

## 🛠️ Configuration

### Environment Variables

There is no `.env.template` file — create `backend/.env` directly with the variables you need. Everything has a sane default for local development except `SECRET_KEY`.

Key configurations:
- `SECRET_KEY`: JWT token secret
- `CORS_ORIGINS`: Allowed frontend URLs
- `BASE_URL` / `SERVER_HOST`: Public base URL used to build Theia IDE links (`{BASE_URL}/theia/{port}/`)
- `MIN_BOOKING_LEAD_TIME_MINUTES`: Minimum minutes a booking must start in the future (default 0)
- `BOOKING_MAX_DAYS_AHEAD`: Maximum number of days ahead a booking can be made, counting from today (default 7)
- `THEIA_IMAGE`: Preview container image (default `elswork/theia`)
- `THEIA_BOOKING_IMAGE`: Booking container image, used when a robot has no per-robot `container_image` set
- `DEFAULT_THEIA_IMAGE`: Fallback image for booking/admin-watch containers when neither of the above resolves
- `ALLOWED_SURVEILLANCE_IMAGES`: Comma-separated list of **additional** Docker images admins may choose for booking/surveillance containers (e.g. `my-custom/ros:humble,another/image:latest`). The built-in defaults (`elswork/theia`, `muneeb/theia-ros-humble:v2`, `hiwonder/theia-ros-humble:v1`) are always included.
- `THEIA_BASE_PORT` / `THEIA_MAX_PORT`: Port range auto-assigned to containers (default `4000`–`9000`)
- `THEIA_MAX_CONTAINERS`: Cap on concurrent Theia containers (default 50)
- `THEIA_IDLE_TIMEOUT_HOURS`: Hours of inactivity before a container is stopped (default 1)
- `THEIA_LOGOUT_GRACE_MINUTES`: Grace period after logout before the preview container is stopped (default 5)
- `THEIA_PROJECT_PATH`: Root directory for per-user workspaces (default `./projects`)
- `DOCKER_NETWORK`: Docker network Theia containers are attached to (default `robot-console-network`)

### Admin-configurable Booking Base Image

Administrators can choose which Docker image is used when a robot's booking container is started (also used for the admin watch/surveillance container).

**How it works:**
1. Go to the Admin Dashboard → **Surveillance Settings** card.
2. Select an image from the approved dropdown (populated from the allowlist).
3. Click **Save Settings** – the choice is persisted in the database and survives restarts.
4. When starting a booking container, image priority is:
   1. Per-robot `container_image` (highest priority)
   2. Admin-configured `surveillance_base_image` (set via the UI)
   3. Environment-variable defaults (`DEFAULT_THEIA_IMAGE`, `THEIA_BOOKING_IMAGE`, `THEIA_IMAGE`)

**Configuring the allowlist:**
- The default allowlist contains `elswork/theia`, `muneeb/theia-ros-humble:v2`, and `hiwonder/theia-ros-humble:v1`.
- To add more images set `ALLOWED_SURVEILLANCE_IMAGES` in `.env`:
  ```
  ALLOWED_SURVEILLANCE_IMAGES=my-org/custom-ros:humble,another/image:v1
  ```
- Arbitrary free-form image names entered by the admin are rejected; only images already on the allowlist can be selected.

**Fallback behaviour:**
- If the stored image is removed from the allowlist, the system falls back to the first image in the allowlist and logs a warning.
- If the database is unavailable at startup, the env-variable defaults are used as before.

### Container Configuration

Preview and booking Theia containers are managed automatically by `backend/services/theia_service.py`:
- **Ports**: Auto-assigned from the `THEIA_BASE_PORT`–`THEIA_MAX_PORT` range, tracked separately for preview and booking containers
- **Workspace mounting**: `/projects/<user_id>/ → /home/project`, shared between a user's preview and booking container
- **Networking**: Every container runs with `NET_ADMIN` + `/dev/net/tun` so the P2P VPN client baked into the image can bring up its tunnel automatically
- **Isolation**: Each user gets their own preview and booking container, named `theia-preview-<user_id>` / `theia-booking-<user_id>`
- **Persistence**: Workspace files survive container restarts and outlive bookings

## 📝 User Guide

### For Users

1. **Visit Homepage**: Navigate to the application
2. **Sign Up/Sign In**: On login, your preview container starts warming up automatically — no booking required
3. **Write Code Anytime**: Use the always-on preview IDE to write and edit code
4. **Book Time Slot**: Select robot type and time slot when you're ready to run against a real/simulated robot
5. **Run on the Robot**: During an active booking, the console switches to your booking container (same workspace, ROS 2 image, P2P VPN to the robot) and unlocks live video
6. **View Video Feed**: Monitor the robot through the live WebRTC stream
7. **Get Results**: Click "Get Result Video" to view a pre-saved simulation clip for your robot type

### For Administrators

1. **Admin Login**: Use admin credentials
2. **Dashboard Access**: View user and booking statistics
3. **Booking Management**: Approve/modify bookings
4. **User Management**: View and manage users
5. **Container Management**: Monitor preview/booking Theia containers, configure the booking base image allowlist

## 🔧 Development

### Manual Setup

```bash
# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend setup  
cd frontend
npm install

# Start services
cd backend && python main.py &
cd frontend && npm run dev &
```

### Backend booking tests

From the repository root:

```bash
python -m pip install pytest requests
python -m pytest backend/test_booking_lead_time.py -q
```

Optional API booking flow test (against a running backend) requires:

- `BASE_URL` (example: `http://localhost:8000`)
- `TOKEN` (Bearer JWT for an authenticated user)
- `ROBOT_ID` (active robot id)

Run:

```bash
BASE_URL=http://localhost:8000 TOKEN=<jwt> ROBOT_ID=1 python -m pytest backend/test_booking_e2e_api.py -q
```

### Adding Videos

1. Place MP4 files in `backend/videos/`
2. Update video mapping in backend if needed
3. Ensure file names match robot types:
   - `turtlebot_simulation.mp4`
   - `arm_simulation.mp4`
   - `hand_simulation.mp4`

## 🚀 Deployment

### Production Deployment

```bash
cd scripts
./deploy.sh --production
```

### With Additional Services

```bash
cd scripts
./deploy.sh --production --nginx --systemd
```

This creates:
- Nginx configuration
- Systemd service files
- Production optimized builds

For a full VPS deployment (including Theia/Docker network setup, MySQL, SSL), see [`deploy_vps.sh`](deploy_vps.sh) and [`docs/PRODUCTION_DEPLOYMENT.md`](docs/PRODUCTION_DEPLOYMENT.md).

## 🏗️ Project Structure Details

### Backend (`backend/`)
- **FastAPI application** with authentication, booking, and container management
- **JWT-based authentication** for secure access
- **Database** for user and booking data (SQLite by default; MySQL supported, see `setup_mysql.sh`)
- **Video serving** with booking-gated access control
- **Theia container management** (`services/theia_service.py`) — starts/stops paired preview + booking containers per user
- **WebSocket/WebRTC signaling** (`routes/streams.py`) for live robot video
- **CORS configuration** for frontend integration

### Frontend (`frontend/`)
- **React + Vite application** with modern UI components
- **Eclipse Theia IDE** embedded via iframe, switching between preview and booking containers automatically
- **WebRTC video player** for robot camera feeds, gated by booking state
- **Chakra UI** for consistent design
- **Axios** for API communication
- **Responsive design** for various screen sizes

### Theia (`theia/`)
- Legacy single-container scripts (`start-theia.sh`, `start-user-container.sh`) kept for reference
- Actual preview/booking container lifecycle is handled by `backend/services/theia_service.py`, which pulls prebuilt images (`elswork/theia`, `muneeb/theia-ros-humble:v2`, `hiwonder/theia-ros-humble:v1`) rather than building one locally

### Projects (`projects/`)
- **Per-user directories** for code and files, shared between a user's preview and booking containers
- **Automatic initialization** with welcome examples
- **Persistent storage** across container restarts and bookings

### Scripts (`scripts/`)
- **setup.sh**: Development environment setup (legacy)
- **deploy.sh**: Production deployment automation
- **Cross-platform support** for Windows/Linux/macOS

## 🔒 Security Features

- **JWT authentication** with secure token handling
- **Access control** gating live video and robot-connected execution behind an active booking
- **P2P VPN per container**, isolated per user, baked into the Theia image
- **CORS protection** for API endpoints
- **Input validation** on all API endpoints

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   cd scripts
   ./setup.sh stop
   ./setup.sh start
   ```

2. **Preview/booking container not starting**:
   - Check `docker ps` for `theia-preview-<user_id>` / `theia-booking-<user_id>`
   - Verify the configured image (`THEIA_IMAGE` / `THEIA_BOOKING_IMAGE`) can be pulled
   - Check `THEIA_BASE_PORT`–`THEIA_MAX_PORT` isn't exhausted

3. **Video playback issues**:
   - Ensure video files exist in `backend/videos/`
   - Check file permissions and formats
   - For live WebRTC video, confirm the booking is active and the `webrtc-bridge` service is running

4. **Authentication issues**:
   - Verify `SECRET_KEY` is set
   - Check token expiration settings

### Logs

- **Backend logs**: `backend/logs/backend.log`
- **Frontend logs**: `frontend/logs/frontend.log`
- **Setup logs**: Console output from scripts

## 📚 API Documentation

Visit http://localhost:8000/docs for interactive API documentation with:
- Authentication endpoints
- Booking management
- Theia container management (`/theia/*`)
- Video serving
- Access control
- Health checks

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the existing code style
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 📞 Support

For support and questions:
- Check the troubleshooting section above
- Review API documentation at `/docs`
- Check application logs for error details
- Verify configuration in `.env` files
