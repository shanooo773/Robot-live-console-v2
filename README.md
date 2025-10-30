# 🤖 Robot Live Console App

A modern web application for robot control and simulation with secure user authentication, booking system, and **Eclipse Theia IDE** for development.

## 🏗️ Architecture

The application is organized in a clean, maintainable structure:

```
app/
├── frontend/           # React + Eclipse Theia IDE interface
├── backend/            # Python FastAPI (authentication, booking, container management)
├── theia/              # Eclipse Theia Docker configuration
├── projects/           # Per-user project directories  
├── videos/             # Pre-saved simulation videos
├── scripts/            # Setup and deployment scripts
├── other-docs/         # Documentation files
├── .env.template       # Environment configuration template
└── README.md           # This file
```

## ✨ Features

### 🔐 Secure User Flow
- **Home Page**: Landing page for first-time visitors
- **Authentication**: Secure sign-in/sign-up system
- **Booking System**: Time slot booking for robot access
- **Access Control**: Theia IDE and video feed only accessible after completed booking

### 💻 Development Interface  
- **Two-Panel Layout**:
  - **Left Panel**: Eclipse Theia IDE (containerized per user)
  - **Right Panel**: Robot video feed (RTSP/WebRTC support)
- **"Get Real Result" Button**: Shows pre-saved simulation videos
- **Robot Selection**: Support for TurtleBot3, Robot Arm, and Robot Hand

### 🎥 Video System
- **RTSP/WebRTC Video Player**: Ready for robot camera integration
- **Test Streams**: Development mode with sample videos
- **Future Robot Integration**: Marked locations for Raspberry Pi camera
- **Secure video serving** with access control

### 🐳 Eclipse Theia IDE
- **Per-User Containers**: Each user gets isolated development environment
- **Pre-installed Extensions**: Python, C++, Git, Terminal, File Explorer
- **Project Persistence**: Files saved in `/projects/<user_id>/`
- **Container Management**: Start/stop/restart via API

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
- Build Eclipse Theia Docker image
- Install all dependencies
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

> **⚠️ IMPORTANT**: The Docker setup requires `services/webrtc-bridge/bridge_service.py` to exist. This file must implement the GStreamer webrtcbin pipeline for WebRTC streaming. If this file doesn't exist, the Docker Compose build will fail.

**What's included:**
- Frontend: React dev server in Docker with hot-reload
- WebRTC Bridge: GStreamer-based bridge with hardware acceleration support (NVENC/VAAPI)

**What's NOT included:**
- Backend: Must run separately on host (see "Quick Start" above)
- Editor/Theia: Use existing Theia setup (not part of this Docker compose)

For detailed Docker setup instructions, hardware acceleration configuration, and troubleshooting, see [`docker/deploy/README.md`](docker/deploy/README.md).

## 🛠️ Configuration

### Environment Variables

Copy `.env.template` to `backend/.env` and configure:

```bash
cp .env.template backend/.env
```

Key configurations:
- `SECRET_KEY`: JWT token secret
- `VPS_URL`: VPS iframe URL
- `CORS_ORIGINS`: Allowed frontend URLs
- `VIDEO_STORAGE_PATH`: Video files directory

### VPS Configuration

⚠️ **REPLACED**: The VPS iframe has been replaced with a modern video streaming system.

The application now features:
- **RTSP/WebRTC Video Player**: Ready for robot camera integration
- **Test Stream Mode**: Development with sample videos
- **Future Robot Integration**: Raspberry Pi camera support planned

### Container Configuration

Eclipse Theia containers are managed automatically:
- **Base Port**: 3001+ (auto-assigned per user)
- **Project Mounting**: `/projects/<user_id>/ → /home/project`
- **Security**: Isolated containers per user
- **Persistence**: Project files survive container restarts

## 📝 User Guide

### For Users

1. **Visit Homepage**: Navigate to the application
2. **Sign Up/Sign In**: Create account or log in
3. **Book Time Slot**: Select robot type and time slot
4. **Access Console**: After booking completion, access Eclipse Theia IDE
5. **Develop & Control**: Write code in full IDE environment
6. **View Video Feed**: Monitor robot through live video stream
7. **Get Results**: Click "Get Real Result" to view simulation videos

### For Administrators

1. **Admin Login**: Use admin credentials
2. **Dashboard Access**: View user and booking statistics
3. **Booking Management**: Approve/modify bookings
4. **User Management**: View and manage users
5. **Container Management**: Monitor Theia containers

## 🔧 Development

### Manual Setup

```bash
# Backend setup
cd app/backend
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Frontend setup  
cd app/frontend
npm install

# Start services
cd app/backend && python main.py &
cd app/frontend && npm run dev &
```

### Adding Videos

1. Place MP4 files in `app/videos/`
2. Update video mapping in backend if needed
3. Ensure file names match robot types:
   - `turtlebot_simulation.mp4`
   - `arm_simulation.mp4`
   - `hand_simulation.mp4`

## 🚀 Deployment

### Production Deployment

```bash
cd app/scripts
./deploy.sh --production
```

### With Additional Services

```bash
cd app/scripts
./deploy.sh --production --nginx --systemd
```

This creates:
- Nginx configuration
- Systemd service files
- Production optimized builds

## 🏗️ Project Structure Details

### Backend (`app/backend/`)
- **FastAPI application** with authentication, booking, and container management
- **JWT-based authentication** for secure access
- **SQLite database** for user and booking data
- **Video serving** with access control
- **Theia container management** with Docker integration
- **WebSocket support** for future robot communication
- **CORS configuration** for frontend integration

### Frontend (`app/frontend/`)
- **React application** with modern UI components
- **Eclipse Theia IDE** embedded via iframe
- **RTSP/WebRTC Video Player** for robot camera feeds
- **Chakra UI** for consistent design
- **Axios** for API communication
- **Responsive design** for various screen sizes

### Theia (`app/theia/`)
- **Docker configuration** for Eclipse Theia IDE
- **Per-user containers** with isolated environments
- **Pre-installed extensions**: Python, C++, Git, Terminal
- **Project persistence** with volume mounting

### Projects (`app/projects/`)
- **Per-user directories** for code and files
- **Automatic initialization** with welcome examples
- **Persistent storage** across container restarts

### Scripts (`app/scripts/`)
- **build.sh**: Complete build automation
- **setup.sh**: Development environment setup (legacy)
- **deploy.sh**: Production deployment automation
- **Cross-platform support** for Windows/Linux/macOS

## 🔒 Security Features

- **JWT authentication** with secure token handling
- **Access control** preventing unauthorized editor access
- **Booking verification** before video access
- **CORS protection** for API endpoints
- **Input validation** on all API endpoints

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   ./scripts/setup.sh stop
   ./scripts/setup.sh start
   ```

2. **VPS connection issues**:
   - Check VPS_URL in environment variables
   - Verify VPS server is accessible

3. **Video playback issues**:
   - Ensure video files exist in `videos/` directory
   - Check file permissions and formats

4. **Authentication issues**:
   - Verify SECRET_KEY is set
   - Check token expiration settings

### Logs

- **Backend logs**: `backend/logs/backend.log`
- **Frontend logs**: `frontend/logs/frontend.log`
- **Setup logs**: Console output from scripts

## 📚 API Documentation

Visit http://localhost:8000/docs for interactive API documentation with:
- Authentication endpoints
- Booking management
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