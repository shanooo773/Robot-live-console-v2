# 🤖 ROS Noetic + Gazebo Simulation System - Complete Implementation

This repository now includes a **complete Dockerized system** for running ROS Noetic + Gazebo simulations with video recording, replacing the previous mock video system with real simulation capabilities.

## 🎯 What's New

### ✅ Real ROS Noetic + Gazebo Integration
- **Full ROS Noetic Desktop** with Gazebo 11
- **Real robot simulation** with physics
- **Video recording** using ffmpeg + xvfb
- **Headless operation** for server environments

### ✅ Complete API System
- **`POST /simulate`** - Run simulations with custom URDF/world files
- **`POST /upload-files`** - Upload robot descriptions and worlds
- **File validation** and error handling
- **Automatic fallback** to mock system if Docker unavailable

### ✅ Full Frontend Interface
- **Simulation Uploader** tab with drag-and-drop file upload
- **Real-time progress** indicators and status updates
- **Video preview** and download functionality
- **Error handling** with user-friendly messages

## 🚀 Quick Start Guide

### 1. Build the Docker Image (First Time)

```bash
# Build the ROS Noetic + Gazebo simulation container
cd docker
docker build -t robot-simulation:latest .
```

**⏱️ Build Time:** 15-20 minutes (downloads ~2GB of ROS packages)

### 2. Start the System

```bash
# Terminal 1: Start Backend
cd backend
python3 -m pip install -r requirements.txt
python3 main.py

# Terminal 2: Start Frontend  
cd frontend
npm install
npm run dev
```

### 3. Test with Sample Files

```bash
# Use the provided test script
cd sample_files
python3 test_api.py
```

Or use the web interface at **http://localhost:3000**

## 📁 New File Structure

```
Robot-live-console/
├── docker/
│   ├── Dockerfile              # ROS Noetic + Gazebo + ffmpeg
│   ├── launch/
│   │   └── spawn_robot.launch  # Robot spawning system
│   ├── robots/                 # Robot descriptions with controllers
│   │   ├── arm/, hand/, turtlebot/
│   │   └── worlds/            # Gazebo world files
│   ├── scripts/
│   │   ├── record_simulation.sh   # Bash recording script
│   │   └── run_simulation.py      # Python coordinator
│   └── README.md              # Detailed Docker documentation
├── backend/
│   └── main.py                # Updated with /simulate and /upload-files
├── frontend/
│   ├── src/components/
│   │   └── SimulationUploader.jsx  # New upload interface
│   ├── src/api.js             # Updated API calls
│   └── src/App.jsx            # Updated with tabs
├── sample_files/              # Test files and documentation
│   ├── sample_robot.urdf      # Example robot description
│   ├── sample_world.world     # Example Gazebo world
│   ├── test_api.py           # API testing script
│   └── README.md             # Sample files guide
└── IMPLEMENTATION.md          # This file
```

## 🔧 API Reference

### File Upload
```bash
curl -X POST http://localhost:8000/upload-files \
  -F "urdf_file=@robot.urdf" \
  -F "world_file=@world.world"
```

### Run Simulation  
```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "urdf_path": "/path/to/robot.urdf",
    "world_path": "/path/to/world.world", 
    "duration": 10
  }'
```

### Download Video
```bash
curl -O http://localhost:8000/videos/{execution_id}.mp4
```

## 🎬 How Video Recording Works

1. **Container Launch**: Docker container with ROS Noetic + Gazebo starts
2. **Virtual Display**: Xvfb creates headless X11 display (`:99`)  
3. **Robot Spawn**: `roslaunch` loads URDF robot into Gazebo world
4. **Video Capture**: `ffmpeg` records X11 display at 30 FPS
5. **User Code**: Custom Python code runs during simulation
6. **Output**: MP4 video saved to host-accessible directory

## 🛡️ Error Handling & Fallbacks

### Automatic Fallback System
- If Docker image not available → Mock video generated
- If simulation fails → Fallback to mock system  
- If video recording fails → Error logged, mock video created
- All failures are logged with timestamps

### File Validation
- URDF files: `.urdf` or `.xacro` extensions required
- World files: `.world` extension required
- File size limits and content validation
- Temporary file cleanup

## 🧪 Testing Scenarios

### 1. With Docker Image (Real Simulation)
```bash
# Build image first
cd docker && docker build -t robot-simulation:latest .

# Test real simulation
cd sample_files && python3 test_api.py
```

### 2. Without Docker Image (Mock Fallback)
```bash
# Don't build image, test fallback
cd sample_files && python3 test_api.py
```

### 3. Frontend Interface
1. Go to http://localhost:3000  
2. Click "Simulation Uploader" tab
3. Upload `sample_robot.urdf` and `sample_world.world`
4. Set duration and click "Run Gazebo Simulation"
5. Preview or download the generated video

## 🎮 Frontend Features

### Simulation Uploader Interface
- **Drag & Drop**: File upload with validation
- **Progress Tracking**: Real-time simulation status
- **Video Preview**: Embedded video player
- **Download Option**: One-click video download
- **Error Display**: Clear error messages and troubleshooting

### Dual Interface System
- **Code Editor**: Original Python code execution interface
- **Simulation Uploader**: New file-based simulation interface
- **Tabbed Navigation**: Easy switching between modes

## 🔍 Performance & Scaling

### Resource Requirements
- **Minimum RAM**: 4GB (for Docker + Gazebo)
- **Recommended RAM**: 8GB+
- **CPU**: 2+ cores recommended
- **Storage**: ~8GB for Docker image + temporary files

### Container Limits
```bash
# Current settings
--mem-limit=4g          # 4GB RAM limit
--cpu-quota=200000      # 2 CPU cores max
--network=none          # No network access (security)
```

### Video Quality Settings
- **Resolution**: 1024x768 (configurable)
- **Framerate**: 30 FPS
- **Format**: H.264 MP4
- **Duration**: 5-60 seconds (user configurable)

## 🛠️ Development & Customization

### Adding New Robot Types
1. Create URDF file in `docker/robots/{robot_name}/`
2. Add controller config: `controllers.yaml`
3. Create world file in `docker/robots/worlds/`
4. Rebuild Docker image

### Modifying Video Recording
Edit `docker/scripts/record_simulation.sh`:
- Change resolution: `RESOLUTION="1920x1080"`
- Adjust framerate: `FRAMERATE=60`
- Modify codec: `ffmpeg ... -vcodec libx264`

### Custom Simulation Logic
Edit `docker/scripts/run_simulation.py`:
- Add pre-simulation setup
- Customize robot spawning
- Add post-simulation cleanup

## 🚨 Troubleshooting

### Common Issues

1. **Docker Build Fails**
   ```bash
   docker system prune -a
   cd docker && docker build --no-cache -t robot-simulation:latest .
   ```

2. **Simulation Timeout**
   - Increase container memory limits
   - Check Docker system resources
   - Monitor with `docker stats`

3. **Empty Video Files**
   - Check Xvfb startup in container logs
   - Verify ffmpeg installation in container
   - Check volume mount permissions

4. **Frontend Build Issues**
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

### Logging & Debugging
- **Backend logs**: Check terminal output from `python3 main.py`
- **Container logs**: `docker logs {container_name}`
- **Frontend logs**: Check browser console
- **API testing**: Use `sample_files/test_api.py`

## 📈 What's Accomplished

### ✅ Complete Implementation
- **Real ROS Noetic + Gazebo** simulation system
- **Docker containerization** with all dependencies
- **Video recording** with ffmpeg and virtual display
- **Full REST API** with file upload and simulation endpoints
- **React frontend** with file upload interface
- **Error handling** with automatic fallback
- **Documentation** and sample files
- **Testing scripts** for validation

### ✅ Production Ready Features
- **Security**: Sandboxed containers with no network access
- **Resource Limits**: CPU and memory constraints
- **File Validation**: Type checking and sanitization  
- **Cleanup**: Automatic temporary file removal
- **Monitoring**: Health checks and status endpoints
- **Fallback**: Mock system when Docker unavailable

## 🎯 Next Steps for Users

1. **Build Docker Image**: `cd docker && docker build -t robot-simulation:latest .`
2. **Test with Samples**: `cd sample_files && python3 test_api.py`
3. **Use Web Interface**: Upload your own URDF and world files
4. **Customize**: Modify robots, worlds, and recording settings
5. **Deploy**: Use in production with proper resource allocation

---

**🎉 Implementation Complete!** You now have a fully functional ROS Noetic + Gazebo simulation system that records real robot simulations as videos, with a complete web interface for file upload and simulation management.