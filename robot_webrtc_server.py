#!/usr/bin/env python3
"""
Robot-side WebRTC Server

This is a lightweight WebRTC server that runs on each robot to provide direct
video streaming to the frontend. It replaces the RTSP → WebRTC conversion
in the backend.

Features:
- Direct SDP offer/answer signaling over HTTP
- Camera stream using OpenCV + aiortc 
- Compatible with existing frontend WebRTC client
- No authentication required (robots trusted within network)
"""

import asyncio
import json
import logging
import os
from pathlib import Path

import cv2
from aiohttp import web, web_response
from aiohttp.web_request import Request
from aiortc import RTCPeerConnection, VideoStreamTrack
from aiortc.contrib.media import MediaPlayer
from av import VideoFrame

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CameraStream(VideoStreamTrack):
    """
    Video track that captures from camera using OpenCV
    """
    def __init__(self, camera_id=0):
        super().__init__()
        self.camera_id = camera_id
        self.cap = cv2.VideoCapture(camera_id)
        
        # Set camera properties for better performance
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        if not self.cap.isOpened():
            logger.warning(f"Failed to open camera {camera_id}, creating dummy stream")
            self.cap = None
            
    async def recv(self):
        """Get next video frame"""
        pts, time_base = await self.next_timestamp()
        
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Convert BGR to RGB
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
            else:
                # Create a black frame if camera read fails
                video_frame = VideoFrame.from_ndarray(
                    cv2.zeros((480, 640, 3), dtype=cv2.uint8), format="rgb24"
                )
        else:
            # Create a colored test pattern for dummy stream
            import numpy as np
            test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            test_frame[:, :, 0] = 128  # Red channel
            test_frame[:, :, 1] = 64   # Green channel  
            test_frame[:, :, 2] = 192  # Blue channel
            
            # Add some movement
            import time
            t = int(time.time() * 2) % 640
            test_frame[:, t:t+5] = [255, 255, 255]  # White moving line
            
            video_frame = VideoFrame.from_ndarray(test_frame, format="rgb24")
        
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame
    
    def stop(self):
        """Cleanup camera resources"""
        if self.cap:
            self.cap.release()

class RobotWebRTCServer:
    def __init__(self, port=8080, camera_id=0):
        self.port = port
        self.camera_id = camera_id
        self.peer_connections = {}
        self.camera_stream = None
        
    async def offer_handler(self, request: Request):
        """Handle WebRTC SDP offer from frontend"""
        try:
            params = await request.json()
            logger.info(f"Received WebRTC offer: {params.get('type', 'unknown')}")
            
            # Create new peer connection
            pc = RTCPeerConnection()
            peer_id = f"robot_peer_{len(self.peer_connections)}"
            self.peer_connections[peer_id] = pc
            
            # Add video track (camera stream)
            if not self.camera_stream:
                self.camera_stream = CameraStream(self.camera_id)
                
            pc.addTrack(self.camera_stream)
            
            # Set up connection monitoring
            @pc.on("connectionstatechange")
            async def on_connectionstatechange():
                logger.info(f"Peer connection state changed: {pc.connectionState}")
                if pc.connectionState == "closed":
                    await self.cleanup_peer_connection(peer_id)
            
            @pc.on("iceconnectionstatechange")
            async def on_iceconnectionstatechange():
                logger.info(f"ICE connection state changed: {pc.iceConnectionState}")
            
            # Process SDP offer
            offer_sdp = params.get("sdp")
            offer_type = params.get("type", "offer")
            
            if not offer_sdp:
                return web.json_response(
                    {"error": "Missing SDP in offer"}, 
                    status=400
                )
            
            # Set remote description
            from aiortc import RTCSessionDescription
            await pc.setRemoteDescription(RTCSessionDescription(
                sdp=offer_sdp,
                type=offer_type
            ))
            
            # Create answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            
            logger.info(f"Created WebRTC answer for peer {peer_id}")
            
            return web.json_response({
                "sdp": pc.localDescription.sdp,
                "type": pc.localDescription.type,
                "peer_id": peer_id
            })
            
        except Exception as e:
            logger.error(f"Error handling WebRTC offer: {e}")
            return web.json_response(
                {"error": f"Failed to process offer: {str(e)}"}, 
                status=500
            )
    
    async def ice_candidate_handler(self, request: Request):
        """Handle ICE candidate from frontend"""
        try:
            params = await request.json()
            peer_id = params.get("peer_id")
            candidate_data = params.get("candidate")
            
            if not peer_id or peer_id not in self.peer_connections:
                return web.json_response(
                    {"error": "Invalid peer_id"}, 
                    status=400
                )
            
            pc = self.peer_connections[peer_id]
            
            # Add ICE candidate
            from aiortc import RTCIceCandidate
            if candidate_data:
                candidate = RTCIceCandidate(
                    candidate=candidate_data.get("candidate"),
                    sdpMLineIndex=candidate_data.get("sdpMLineIndex"),
                    sdpMid=candidate_data.get("sdpMid")
                )
                await pc.addIceCandidate(candidate)
                logger.info(f"Added ICE candidate for peer {peer_id}")
            
            return web.json_response({"success": True})
            
        except Exception as e:
            logger.error(f"Error handling ICE candidate: {e}")
            return web.json_response(
                {"error": f"Failed to process ICE candidate: {str(e)}"}, 
                status=500
            )
    
    async def status_handler(self, request: Request):
        """Get robot WebRTC server status"""
        return web.json_response({
            "status": "running",
            "active_connections": len(self.peer_connections),
            "camera_stream": self.camera_stream is not None,
            "port": self.port
        })
    
    async def cleanup_peer_connection(self, peer_id: str):
        """Clean up a peer connection"""
        if peer_id in self.peer_connections:
            pc = self.peer_connections[peer_id]
            await pc.close()
            del self.peer_connections[peer_id]
            logger.info(f"Cleaned up peer connection {peer_id}")
    
    async def cleanup_all_connections(self):
        """Clean up all peer connections"""
        for peer_id in list(self.peer_connections.keys()):
            await self.cleanup_peer_connection(peer_id)
        
        if self.camera_stream:
            self.camera_stream.stop()
            self.camera_stream = None
    
    def create_app(self):
        """Create aiohttp web application"""
        app = web.Application()
        
        # WebRTC signaling endpoints
        app.router.add_post("/offer", self.offer_handler)
        app.router.add_post("/ice-candidate", self.ice_candidate_handler)
        app.router.add_get("/status", self.status_handler)
        
        # CORS middleware for cross-origin requests
        async def cors_middleware(request, handler):
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        app.middlewares.append(cors_middleware)
        
        # Handle OPTIONS requests for CORS preflight
        async def handle_options(request):
            return web.Response(
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
                }
            )
        
        app.router.add_route("OPTIONS", "/{path:.*}", handle_options)
        
        return app
    
    async def start_server(self):
        """Start the WebRTC signaling server"""
        app = self.create_app()
        
        # Cleanup handler for graceful shutdown
        async def cleanup_handler(app):
            logger.info("Shutting down robot WebRTC server...")
            await self.cleanup_all_connections()
        
        app.on_cleanup.append(cleanup_handler)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"Robot WebRTC server started on port {self.port}")
        logger.info(f"Signaling endpoints available at:")
        logger.info(f"  POST http://localhost:{self.port}/offer")
        logger.info(f"  POST http://localhost:{self.port}/ice-candidate")
        logger.info(f"  GET  http://localhost:{self.port}/status")
        
        return runner

async def main():
    """Main function to run the robot WebRTC server"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Robot WebRTC Server')
    parser.add_argument('--port', type=int, default=8080, 
                       help='Port to run server on (default: 8080)')
    parser.add_argument('--camera', type=int, default=0,
                       help='Camera device ID (default: 0)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create and start server
    server = RobotWebRTCServer(port=args.port, camera_id=args.camera)
    runner = await server.start_server()
    
    try:
        # Keep server running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())