# WebRTC Bridge Dockerfile with GStreamer support
# This is an additive file - does not modify existing editor/backend Docker assets
# NOTE: bridge_service.py must implement GStreamer webrtcbin pipeline and call backend 
# authorize endpoint using BRIDGE_CONTROL_SECRET; no mock stage provided.

FROM ubuntu:22.04 AS gst-base

ENV DEBIAN_FRONTEND=noninteractive

# Install GStreamer and Python dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-gi \
    python3-gst-1.0 \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    build-essential \
    pkg-config \
    libcairo2-dev \
    libgirepository1.0-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy bridge service code
# This will fail if bridge_service.py doesn't exist (as required)
COPY services/webrtc-bridge/ /app/

# Verify bridge_service.py exists, fail build if not
RUN test -f /app/bridge_service.py || \
    (echo "ERROR: bridge_service.py is REQUIRED but not found!" && \
     echo "This file must implement the GStreamer webrtcbin pipeline." && \
     echo "Please create services/webrtc-bridge/bridge_service.py before building." && \
     exit 1)

# Install Python runtime dependencies required by bridge_service.py
RUN pip install --no-cache-dir aiohttp websockets pyjwt requests

# Expose WebRTC bridge port
EXPOSE 8081

# Run the bridge service
# This file MUST exist and implement the GStreamer webrtcbin pipeline
CMD ["python3", "/app/bridge_service.py"]
