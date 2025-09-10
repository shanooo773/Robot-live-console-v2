# 🤖 Robot Live Console App - Eclipse Theia Edition

A modern web application for robot control and simulation with secure user authentication, booking system, Eclipse Theia IDE, and real-time robot camera integration.

## 🏗️ Architecture

The application is organized in a clean, maintainable structure:

```
app/
├── frontend/             # React + Theia IDE integration interface
├── backend/              # Python FastAPI (authentication, booking, Docker management)
├── data/users/           # User-specific project directories for Theia containers
├── Dockerfile.theia      # Eclipse Theia IDE container configuration
├── docker-compose.yml    # Container orchestration for user sessions
├── scripts/              # Setup and deployment scripts
├── other-docs/           # Documentation files
├── .env.template         # Environment configuration template
└── README.md             # This file
```

## ✨ Features

### 🔐 Secure User Flow
- **Home Page**: Landing page for first-time visitors
- **Authentication**: Secure sign-in/sign-up system
- **Booking System**: Time slot booking for robot access
- **Access Control**: Theia IDE and robot camera only accessible after completed booking

### 💻 Development Interface  
- **Two-Panel Layout**:
  - **Left Panel**: Eclipse Theia IDE running in Docker container with persistent workspace
  - **Right Panel**: Live robot camera feed (placeholder ready for integration)
- **Per-User Containers**: Each user gets their own isolated Theia development environment
- **Persistent Workspace**: Code and files persist across sessions in user-specific directories
- **Robot Selection**: Support for TurtleBot3, Robot Arm, and Robot Hand

### 🐳 Docker Integration
- Eclipse Theia IDE runs in isolated Docker containers
- Automatic container management and lifecycle
- User-specific data persistence
- Network isolation and security

### 🎥 Camera System
- Placeholder iframe ready for live robot camera integration
- Support for multiple robot types
- Real-time streaming capability (hardware integration pending)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Docker 20.10+
- npm

### 1. Setup and Run (Development)

```bash
cd app/scripts
./setup.sh
```

This will:
- Install all dependencies
- Start the backend server (port 8000)
- Start the frontend server (port 3000)
- Set up Docker network for Theia containers

### 2. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Theia IDE**: Automatically launched for each user session

### 3. Default Admin Account

- **Email**: admin@example.com  
- **Password**: admin123

## 🐳 Docker Setup

### Theia IDE Container

The application uses Eclipse Theia running in Docker containers for the development environment:

```bash
# Build Theia image
docker build -f Dockerfile.theia -t robot-theia-ide:latest .

# Each user gets their own container with persistent workspace
# Containers are managed automatically by the backend
```

### User Data Persistence

- User workspaces are stored in `data/users/<user_id>/`
- Each directory is mounted as `/home/project` in the container
- Code and files persist across sessions
- Isolated environments prevent user conflicts

## 🛠️ Configuration

### Environment Variables

Copy `.env.template` to `backend/.env` and configure:

```bash
cp .env.template backend/.env
```

Key configurations:
- `SECRET_KEY`: JWT token secret
- `CORS_ORIGINS`: Allowed frontend URLs
- `THEIA_BASE_PORT`: Starting port for Theia containers (default: 3001)

### Container Management

The application automatically manages Docker containers:
- Creates containers on-demand when users access the IDE
- Maps user-specific directories for persistence
- Handles container lifecycle (start/stop/cleanup)
- Provides admin tools for container management

## 📝 User Guide

### For Users

1. **Visit Homepage**: Navigate to the application
2. **Sign Up/Sign In**: Create account or log in
3. **Book Time Slot**: Select robot type and time slot
4. **Access Console**: After booking completion, access Theia IDE
5. **Code & Develop**: Write code in your persistent workspace
6. **Robot Control**: View live camera feed from selected robot

### For Administrators

1. **Admin Login**: Use admin credentials
2. **Dashboard Access**: View user and booking statistics
3. **Booking Management**: Approve/modify bookings
4. **User Management**: View and manage users
5. **Container Management**: Monitor and manage Theia containers

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

# Docker setup
docker build -f Dockerfile.theia -t robot-theia-ide:latest .

# Start services
cd app/backend && python main.py &
cd app/frontend && npm run dev &
```

### Container Management Commands

```bash
# View running containers
docker ps --filter name=theia-user-

# Stop user container
docker stop theia-user-<user_id>

# Clean up stopped containers
docker container prune

# View container logs
docker logs theia-user-<user_id>
```

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
- **FastAPI application** with authentication and booking
- **JWT-based authentication** for secure access
- **SQLite database** for user and booking data
- **Docker container management** for Theia IDE instances
- **Theia lifecycle management** (start/stop/cleanup)
- **CORS configuration** for frontend integration

### Frontend (`app/frontend/`)
- **React application** with modern UI components
- **Theia IDE integration** via iframe embedding
- **Chakra UI** for consistent design
- **Axios** for API communication
- **Real-time container status** updates
- **Responsive design** for various screen sizes

### Docker Infrastructure
- **Theia IDE containers** with pre-installed development tools
- **User workspace persistence** via volume mounts
- **Isolated environments** for security and multi-tenancy
- **Automatic container orchestration** by backend services

### Scripts (`app/scripts/`)
- **setup.sh**: Development environment setup
- **deploy.sh**: Production deployment automation
- **Cross-platform support** for Windows/Linux/macOS

## 🔒 Security Features

- **JWT authentication** with secure token handling
- **Access control** preventing unauthorized IDE access
- **Booking verification** before Theia container access
- **Container isolation** preventing cross-user interference
- **CORS protection** for API endpoints
- **Input validation** on all API endpoints

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   ./scripts/setup.sh stop
   ./scripts/setup.sh start
   ```

2. **Theia container issues**:
   - Check Docker daemon is running: `docker ps`
   - Verify image exists: `docker images | grep theia`
   - Check container logs: `docker logs theia-user-<user_id>`

3. **Camera feed issues**:
   - Hardware integration is in progress
   - Placeholder shows current robot selection
   - Full camera integration will be available soon

4. **Authentication issues**:
   - Verify SECRET_KEY is set
   - Check token expiration settings

### Logs

- **Backend logs**: `backend/logs/backend.log`
- **Frontend logs**: `frontend/logs/frontend.log`
- **Container logs**: `docker logs theia-user-<user_id>`
- **Setup logs**: Console output from scripts

## 📚 API Documentation

Visit http://localhost:8000/docs for interactive API documentation with:
- Authentication endpoints
- Booking management
- Theia container management
- Container lifecycle operations
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