# WebRTC Signaling Service Configuration

## Overview
This directory contains the WebRTC signaling server for real-time video streaming between robots and users.

## Files
- `Dockerfile`: Container configuration for the signaling server
- `server.js`: Node.js WebRTC signaling server with Socket.IO
- `config/`: Configuration files for different environments

## Features
- **WebRTC Signaling**: Real-time peer-to-peer connection establishment
- **TURN/STUN Server**: NAT traversal support for connections behind firewalls
- **Room Management**: Multiple robot sessions with isolated streams
- **CORS Support**: Configured for frontend integration
- **Health Monitoring**: Health check endpoints for monitoring

## Ports
- `8080`: WebRTC signaling server (WebSocket)
- `3478`: STUN server (UDP)
- `5349`: TURN server (UDP/TCP)
- `49152-65535`: ICE candidate range (UDP)

## Usage
The service is automatically started with docker-compose and provides:
- WebRTC configuration at `/config`
- Health status at `/health`
- WebSocket signaling at `/socket.io/`

## Environment Variables
- `SIGNALING_PORT`: WebRTC signaling port (default: 8080)
- `STUN_PORT`: STUN server port (default: 3478)
- `TURN_PORT`: TURN server port (default: 5349)
- `CORS_ORIGINS`: Allowed origins for CORS (comma-separated)

## Integration
The frontend components can connect to this service for:
- Real-time robot video streaming
- Bidirectional communication with robots
- Low-latency control commands