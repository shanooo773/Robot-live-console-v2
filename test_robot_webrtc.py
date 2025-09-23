#!/usr/bin/env python3
"""
Test script for the Robot WebRTC Server

This script demonstrates how to run and test the robot WebRTC server.
It can be used to verify that the server starts correctly and responds to requests.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the current directory to Python path so we can import robot_webrtc_server
sys.path.insert(0, str(Path(__file__).parent))

from robot_webrtc_server import RobotWebRTCServer

async def test_robot_webrtc_server():
    """Test the robot WebRTC server functionality"""
    print("🤖 Testing Robot WebRTC Server")
    print("=" * 50)
    
    # Create server instance
    server = RobotWebRTCServer(port=8080, camera_id=0)
    
    print("✅ Created robot WebRTC server instance")
    
    # Test server creation
    app = server.create_app()
    print("✅ Created web application with routes:")
    for route in app.router.routes():
        print(f"   {route.method} {route.resource.canonical}")
    
    print("\n🚀 Starting server test...")
    print("Note: This test will start a server on port 8080")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Start the server
        runner = await server.start_server()
        
        print("✅ Server started successfully!")
        print("📡 WebRTC signaling endpoints available:")
        print("   POST http://localhost:8080/offer")
        print("   POST http://localhost:8080/ice-candidate") 
        print("   GET  http://localhost:8080/status")
        
        print("\n🎥 Test camera stream initialization...")
        # Test camera stream creation
        if server.camera_stream is None:
            from robot_webrtc_server import CameraStream
            test_stream = CameraStream(0)
            print("✅ Camera stream created (using dummy stream if no camera)")
            test_stream.stop()
        
        print("\n📊 Server status:")
        status = {
            "status": "running",
            "active_connections": len(server.peer_connections),
            "camera_stream": server.camera_stream is not None,
            "port": server.port
        }
        print(json.dumps(status, indent=2))
        
        print("\n🔄 Server is running... Press Ctrl+C to stop")
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Stopping server...")
        await runner.cleanup()
        print("✅ Server stopped successfully")
    except Exception as e:
        print(f"❌ Server error: {e}")
        raise

async def test_basic_functionality():
    """Test basic functionality without starting the server"""
    print("🧪 Testing Basic Robot WebRTC Functionality")
    print("=" * 50)
    
    # Test server creation
    server = RobotWebRTCServer(port=8081, camera_id=0)
    print("✅ Server instance created")
    
    # Test app creation
    app = server.create_app()
    print("✅ Web application created")
    
    # Test camera stream creation
    from robot_webrtc_server import CameraStream
    camera_stream = CameraStream(0)
    print("✅ Camera stream created")
    
    # Test basic camera stream functionality
    try:
        # Test next timestamp method
        pts, time_base = await camera_stream.next_timestamp()
        print(f"✅ Camera stream timestamp: pts={pts}, time_base={time_base}")
    except Exception as e:
        print(f"⚠️  Camera stream warning: {e}")
    
    # Cleanup
    camera_stream.stop()
    print("✅ Camera stream cleaned up")
    
    print("\n🎉 Basic functionality test completed successfully!")

def main():
    """Main function to run tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Robot WebRTC Server')
    parser.add_argument('--basic', action='store_true',
                       help='Run basic functionality test only (no server start)')
    parser.add_argument('--server', action='store_true', 
                       help='Start server for interactive testing')
    
    args = parser.parse_args()
    
    if args.basic:
        asyncio.run(test_basic_functionality())
    elif args.server:
        asyncio.run(test_robot_webrtc_server())
    else:
        print("Robot WebRTC Server Test")
        print("Usage:")
        print("  python test_robot_webrtc.py --basic   # Basic functionality test")
        print("  python test_robot_webrtc.py --server  # Start server test")
        print("\nRunning basic test by default...")
        asyncio.run(test_basic_functionality())

if __name__ == "__main__":
    main()