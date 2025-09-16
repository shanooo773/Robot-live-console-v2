FROM node:18-slim

# Create app directory and set working directory
WORKDIR /app

# Create package.json for WebRTC signaling server
RUN echo '{\
  "name": "robot-webrtc-signaling",\
  "version": "1.0.0",\
  "description": "WebRTC signaling server for robot video streaming",\
  "main": "server.js",\
  "scripts": {\
    "start": "node server.js"\
  },\
  "dependencies": {\
    "ws": "^8.14.2",\
    "cors": "^2.8.5",\
    "express": "^4.18.2",\
    "socket.io": "^4.7.2"\
  }\
}' > package.json

# Install dependencies
RUN npm install

# Copy server files
COPY server.js ./

# Create logs directory
RUN mkdir -p logs

# Expose ports
EXPOSE 8080 3478 5349

# Create non-root user
RUN groupadd -g 1001 webrtc && \
    useradd -u 1001 -g webrtc -s /bin/bash webrtc && \
    chown -R webrtc:webrtc /app

USER webrtc

CMD ["npm", "start"]