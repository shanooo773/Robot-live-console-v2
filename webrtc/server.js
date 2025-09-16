const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const cors = require('cors');

// Configuration
const PORT = process.env.SIGNALING_PORT || 8080;
const STUN_PORT = process.env.STUN_PORT || 3478;
const TURN_PORT = process.env.TURN_PORT || 5349;
const CORS_ORIGINS = process.env.CORS_ORIGINS ? 
    process.env.CORS_ORIGINS.split(',') : 
    ['http://localhost:3000', 'http://localhost:5173'];

console.log('🚀 Starting Robot WebRTC Signaling Server...');
console.log(`📡 Signaling Port: ${PORT}`);
console.log(`🔄 STUN Port: ${STUN_PORT}`);
console.log(`🔄 TURN Port: ${TURN_PORT}`);
console.log(`🌐 CORS Origins: ${CORS_ORIGINS.join(', ')}`);

// Create Express app
const app = express();
const server = http.createServer(app);

// Configure CORS
app.use(cors({
    origin: CORS_ORIGINS,
    methods: ['GET', 'POST'],
    credentials: true
}));

app.use(express.json());

// Socket.IO setup with CORS
const io = socketIo(server, {
    cors: {
        origin: CORS_ORIGINS,
        methods: ['GET', 'POST'],
        credentials: true
    }
});

// In-memory store for active connections
const users = new Map();
const rooms = new Map();

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'webrtc-signaling',
        timestamp: new Date().toISOString(),
        connections: users.size,
        rooms: rooms.size
    });
});

// WebRTC configuration endpoint
app.get('/config', (req, res) => {
    res.json({
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
            // Add custom STUN/TURN servers when available
            // { urls: 'turn:localhost:5349', username: 'robot-console', credential: 'robot-turn-secret' }
        ]
    });
});

// Socket.IO connection handling
io.on('connection', (socket) => {
    console.log(`🔌 User connected: ${socket.id}`);
    
    // Handle user registration
    socket.on('register', (data) => {
        const { userId, userType } = data; // userType: 'viewer' or 'robot'
        
        users.set(socket.id, {
            userId,
            userType,
            socketId: socket.id
        });
        
        socket.userId = userId;
        socket.userType = userType;
        
        console.log(`👤 User registered: ${userId} as ${userType}`);
        
        // Notify about successful registration
        socket.emit('registered', {
            success: true,
            userId,
            userType
        });
        
        // If robot, notify waiting viewers
        if (userType === 'robot') {
            socket.broadcast.emit('robot-available', { userId });
        }
    });
    
    // Handle joining a room (robot session)
    socket.on('join-room', (data) => {
        const { roomId } = data;
        
        if (!rooms.has(roomId)) {
            rooms.set(roomId, new Set());
        }
        
        rooms.get(roomId).add(socket.id);
        socket.join(roomId);
        socket.roomId = roomId;
        
        console.log(`🏠 User ${socket.userId} joined room: ${roomId}`);
        
        // Notify others in the room
        socket.to(roomId).emit('user-joined', {
            userId: socket.userId,
            userType: socket.userType
        });
        
        socket.emit('joined-room', { roomId });
    });
    
    // Handle WebRTC signaling
    socket.on('offer', (data) => {
        const { to, offer } = data;
        console.log(`📤 Relaying offer from ${socket.userId} to ${to}`);
        
        socket.to(socket.roomId).emit('offer', {
            from: socket.userId,
            offer
        });
    });
    
    socket.on('answer', (data) => {
        const { to, answer } = data;
        console.log(`📤 Relaying answer from ${socket.userId} to ${to}`);
        
        socket.to(socket.roomId).emit('answer', {
            from: socket.userId,
            answer
        });
    });
    
    socket.on('ice-candidate', (data) => {
        const { to, candidate } = data;
        console.log(`🧊 Relaying ICE candidate from ${socket.userId} to ${to}`);
        
        socket.to(socket.roomId).emit('ice-candidate', {
            from: socket.userId,
            candidate
        });
    });
    
    // Handle disconnection
    socket.on('disconnect', () => {
        console.log(`🔌 User disconnected: ${socket.id}`);
        
        // Clean up user data
        users.delete(socket.id);
        
        // Clean up room data
        if (socket.roomId && rooms.has(socket.roomId)) {
            rooms.get(socket.roomId).delete(socket.id);
            
            // Notify others in room about user leaving
            socket.to(socket.roomId).emit('user-left', {
                userId: socket.userId,
                userType: socket.userType
            });
            
            // Remove empty rooms
            if (rooms.get(socket.roomId).size === 0) {
                rooms.delete(socket.roomId);
            }
        }
    });
    
    // Handle errors
    socket.on('error', (error) => {
        console.error(`❌ Socket error for ${socket.id}:`, error);
    });
});

// Start the signaling server
server.listen(PORT, '0.0.0.0', () => {
    console.log(`✅ WebRTC Signaling Server running on port ${PORT}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('🛑 Shutting down WebRTC Signaling Server...');
    server.close();
});

process.on('SIGINT', () => {
    console.log('🛑 Shutting down WebRTC Signaling Server...');
    server.close();
    process.exit(0);
});