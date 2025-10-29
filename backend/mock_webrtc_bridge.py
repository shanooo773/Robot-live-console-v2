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

# Track active streams
active_streams: Dict[str, dict] = {}
connected_clients: Set[websockets.WebSocketServerProtocol] = set()

# WebSocket handler
async def handle_websocket(websocket, path):
    """Handle WebSocket connections from viewers"""
    # Extract stream_id from path or query string
    stream_id = None
    if "stream_id=" in path:
        stream_id = path.split("stream_id=")[1].split("&")[0]
    
    logger.info(f"New WebSocket connection: {path}, stream_id: {stream_id}")
    connected_clients.add(websocket)
    
    try:
        # Send initial connection message
        await websocket.send(json.dumps({
            "type": "connected",
            "message": "Connected to WebRTC bridge",
            "stream_id": stream_id,
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
                        "stream_id": stream_id
                    }
                    await websocket.send(json.dumps(response))
                    logger.info(f"Sent SDP answer for stream {stream_id}")
                
                elif msg_type == "ice":
                    # Acknowledge ICE candidate
                    response = {
                        "type": "ice-ack",
                        "stream_id": stream_id
                    }
                    await websocket.send(json.dumps(response))
                    logger.info(f"Acknowledged ICE candidate for stream {stream_id}")
                
                else:
                    logger.warning(f"Unknown message type: {msg_type}")
            
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {message}")
            except Exception as e:
                logger.error(f"Error handling message: {e}")
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"WebSocket connection closed for stream {stream_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connected_clients.remove(websocket)
        logger.info(f"Client disconnected. Active connections: {len(connected_clients)}")

# HTTP Control handlers
async def handle_start_stream(request):
    """Handle stream start control request"""
    try:
        data = await request.json()
        stream_id = data.get("stream_id")
        
        if not stream_id:
            return web.json_response(
                {"error": "stream_id required"},
                status=400
            )
        
        active_streams[stream_id] = {
            "stream_id": stream_id,
            "status": "running",
            "started_at": datetime.utcnow().isoformat()
        }
        
        logger.info(f"Stream started: {stream_id}")
        return web.json_response({
            "message": "Stream started",
            "stream_id": stream_id
        })
    
    except Exception as e:
        logger.error(f"Error starting stream: {e}")
        return web.json_response(
            {"error": str(e)},
            status=500
        )

async def handle_stop_stream(request):
    """Handle stream stop control request"""
    try:
        data = await request.json()
        stream_id = data.get("stream_id")
        
        if not stream_id:
            return web.json_response(
                {"error": "stream_id required"},
                status=400
            )
        
        if stream_id in active_streams:
            del active_streams[stream_id]
            logger.info(f"Stream stopped: {stream_id}")
        
        return web.json_response({
            "message": "Stream stopped",
            "stream_id": stream_id
        })
    
    except Exception as e:
        logger.error(f"Error stopping stream: {e}")
        return web.json_response(
            {"error": str(e)},
            status=500
        )

async def handle_status(request):
    """Handle status check request"""
    return web.json_response({
        "status": "running",
        "active_streams": len(active_streams),
        "connected_clients": len(connected_clients),
        "streams": list(active_streams.keys())
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
