#!/usr/bin/env python3
"""
Mock WebRTC Bridge Server for Testing

This is a simple mock server that simulates the WebRTC bridge for testing purposes.
In production, this would be replaced with a real GStreamer-based bridge.

Usage:
    python mock_webrtc_bridge.py

This will start:
- WebSocket server on ws://localhost:8081/ws/stream
- Control HTTP server on http://localhost:8081
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set
import signal
import sys

try:
    import websockets
    from aiohttp import web
    DEPS_AVAILABLE = True
except ImportError:
    DEPS_AVAILABLE = False
    print("⚠️  Missing dependencies. Install with:")
    print("   pip install websockets aiohttp")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Track active robots (robot_id based)
active_robots: Dict[int, dict] = {}
connected_clients: Set[websockets.WebSocketServerProtocol] = set()

# WebSocket handler
async def handle_websocket(websocket, path):
    """Handle WebSocket connections from viewers"""
    # Extract robot_id from path or query string (updated from stream_id)
    robot_id = None
    if "robot_id=" in path:
        robot_id = int(path.split("robot_id=")[1].split("&")[0])
    
    logger.info(f"New WebSocket connection: {path}, robot_id: {robot_id}")
    connected_clients.add(websocket)
    
    try:
        # Send initial connection message
        await websocket.send(json.dumps({
            "type": "connected",
            "message": "Connected to WebRTC bridge",
            "robot_id": robot_id,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        # Handle incoming messages
        async for message in websocket:
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                
                logger.info(f"Received message type: {msg_type}")
                
                if msg_type == "offer":
                    # Simulate SDP answer
                    response = {
                        "type": "answer",
                        "sdp": "v=0\r\no=- 123456 2 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\na=group:BUNDLE 0\r\nm=video 9 UDP/TLS/RTP/SAVPF 96\r\nc=IN IP4 0.0.0.0\r\na=rtcp:9 IN IP4 0.0.0.0\r\na=ice-ufrag:mock\r\na=ice-pwd:mockpassword\r\na=fingerprint:sha-256 00:11:22:33:44:55:66:77:88:99:AA:BB:CC:DD:EE:FF\r\na=setup:active\r\na=mid:0\r\na=sendonly\r\na=rtcp-mux\r\na=rtpmap:96 H264/90000\r\n",
                        "robot_id": robot_id
                    }
                    await websocket.send(json.dumps(response))
                    logger.info(f"Sent SDP answer for robot {robot_id}")
                
                elif msg_type == "ice":
                    # Acknowledge ICE candidate
                    response = {
                        "type": "ice-ack",
                        "robot_id": robot_id
                    }
                    await websocket.send(json.dumps(response))
                    logger.info(f"Acknowledged ICE candidate for robot {robot_id}")
                
                else:
                    logger.warning(f"Unknown message type: {msg_type}")
            
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {message}")
            except Exception as e:
                logger.error(f"Error handling message: {e}")
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"WebSocket connection closed for robot {robot_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client disconnected. Active connections: {len(connected_clients)}")

# HTTP Control handlers
# NOTE: Start/stop control handlers are deprecated - robots are managed via Robot Registry
async def handle_start_stream(request):
    """Handle stream start control request (deprecated - kept for backward compatibility)"""
    try:
        data = await request.json()
        robot_id = data.get("robot_id") or data.get("stream_id")  # Accept both for compatibility
        
        if not robot_id:
            return web.json_response(
                {"error": "robot_id required"},
                status=400
            )
        
        try:
            robot_id = int(robot_id)
        except ValueError:
            return web.json_response(
                {"error": "robot_id must be an integer"},
                status=400
            )
        
        active_robots[robot_id] = {
            "robot_id": robot_id,
            "status": "running",
            "started_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Robot stream started: {robot_id}")
        return web.json_response({
            "message": "Robot stream started",
            "robot_id": robot_id
        })
    
    except Exception as e:
        logger.error(f"Error starting robot stream: {e}")
        return web.json_response(
            {"error": str(e)},
            status=500
        )

async def handle_stop_stream(request):
    """Handle stream stop control request (deprecated - kept for backward compatibility)"""
    try:
        data = await request.json()
        robot_id = data.get("robot_id") or data.get("stream_id")  # Accept both for compatibility
        
        if not robot_id:
            return web.json_response(
                {"error": "robot_id required"},
                status=400
            )
        
        try:
            robot_id = int(robot_id)
        except ValueError:
            pass
        
        if robot_id in active_robots:
            del active_robots[robot_id]
            logger.info(f"Robot stream stopped: {robot_id}")
        
        return web.json_response({
            "message": "Robot stream stopped",
            "robot_id": robot_id
        })
    
    except Exception as e:
        logger.error(f"Error stopping robot stream: {e}")
        return web.json_response(
            {"error": str(e)},
            status=500
        )

async def handle_status(request):
    """Handle status check request"""
    return web.json_response({
        "status": "running",
        "active_robots": len(active_robots),
        "connected_clients": len(connected_clients),
        "robots": list(active_robots.keys())
    })

async def start_http_server():
    """Start HTTP control server"""
    app = web.Application()
    app.router.add_post('/control/start', handle_start_stream)
    app.router.add_post('/control/stop', handle_stop_stream)
    app.router.add_get('/status', handle_status)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8081)
    await site.start()
    
    logger.info("HTTP control server started on http://localhost:8081")
    return runner

async def start_websocket_server():
    """Start WebSocket server"""
    server = await websockets.serve(
        handle_websocket,
        "localhost",
        8081,
        subprotocols=["webrtc"]
    )
    
    logger.info("WebSocket server started on ws://localhost:8081/ws/stream")
    return server

async def main():
    """Main server loop"""
    logger.info("="*70)
    logger.info("  Mock WebRTC Bridge Server")
    logger.info("="*70)
    logger.info("")
    logger.info("This is a testing mock. In production, use a real GStreamer bridge.")
    logger.info("")
    logger.info("Endpoints:")
    logger.info("  - WebSocket: ws://localhost:8081/ws/stream")
    logger.info("  - HTTP Control: http://localhost:8081")
    logger.info("  - Status: http://localhost:8081/status")
    logger.info("")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*70)
    
    # Start servers
    try:
        # Note: We can only bind one service per port, so we'll use WebSocket
        ws_server = await start_websocket_server()
        
        # Keep running
        await asyncio.Future()  # Run forever
    
    except asyncio.CancelledError:
        logger.info("Server shutdown requested")
    finally:
        logger.info("Shutting down servers...")
        ws_server.close()
        await ws_server.wait_closed()
        logger.info("Servers stopped")

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    logger.info("\nReceived interrupt signal, shutting down...")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run server
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
