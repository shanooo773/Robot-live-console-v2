# 🤖 Robot Live Console App

A modern web application for robot control and simulation with secure user authentication, booking system, and real-time VPS interaction.

## 🏗️ Architecture

The application is organized in a clean, maintainable structure:

```
app/
├── frontend/           # React + Monaco Editor interface
├── backend/            # Python FastAPI (authentication, booking, video serving)
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
- **Access Control**: Monaco Editor and VPS iframe only accessible after completed booking

### 💻 Development Interface  
- **Two-Panel Layout**:
  - **Left Panel**: Monaco Editor for code input (Python/C++)
  - **Right Panel**: Live VPS iframe (`http://172.104.207.139`)
- **"Get Real Result" Button**: Replaces iframe with pre-saved simulation videos
- **Robot Selection**: Support for TurtleBot3, Robot Arm, and Robot Hand

### 🎥 Video System
- Pre-saved simulation videos for each robot type
- Secure video serving with access control
- Automatic video playback when requested
- Support for MP4 format videos

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
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

### 2. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 3. Default Admin Account

- **Email**: admin@example.com  
- **Password**: admin123

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

The application connects to a VPS interface at:
- Default: `http://172.104.207.139`
- Configurable via `VPS_URL` environment variable

## 📝 User Guide

### For Users

1. **Visit Homepage**: Navigate to the application
2. **Sign Up/Sign In**: Create account or log in
3. **Book Time Slot**: Select robot type and time slot
4. **Access Console**: After booking completion, access Monaco Editor
5. **Code & Control**: Write code and interact with VPS
6. **Get Results**: Click "Get Real Result" to view simulation videos

### For Administrators

1. **Admin Login**: Use admin credentials
2. **Dashboard Access**: View user and booking statistics
3. **Booking Management**: Approve/modify bookings
4. **User Management**: View and manage users

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
- **FastAPI application** with authentication and booking
- **JWT-based authentication** for secure access
- **SQLite database** for user and booking data
- **Video serving** with access control
- **CORS configuration** for frontend integration

### Frontend (`app/frontend/`)
- **React application** with modern UI components
- **Monaco Editor** for code editing
- **Chakra UI** for consistent design
- **Axios** for API communication
- **Responsive design** for various screen sizes

### Scripts (`app/scripts/`)
- **setup.sh**: Development environment setup
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