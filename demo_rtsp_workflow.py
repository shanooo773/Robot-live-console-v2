#!/usr/bin/env python3
"""
End-to-End Demo: RTSP Streaming Feature

This script demonstrates the complete workflow of the RTSP streaming feature:
1. Admin registers an RTSP stream
2. User with booking accesses stream
3. Stream metadata is retrieved
4. WebSocket signaling info is obtained
5. Stream is stopped by admin

Run this after starting the backend server to see the feature in action.
"""

import json
import sys

def print_step(step, title):
    """Print a formatted step header"""
    print(f"\n{'='*70}")
    print(f"Step {step}: {title}")
    print('='*70)

def print_command(cmd):
    """Print a command to execute"""
    print(f"\n💻 Command:")
    print(f"   {cmd}")

def print_response(response):
    """Print a formatted response"""
    print(f"\n✅ Response:")
    print(f"   {json.dumps(response, indent=2)}")

def main():
    """Demonstrate the RTSP streaming feature workflow"""
    
    print("\n" + "="*70)
    print("  RTSP Streaming Feature - End-to-End Demo")
    print("="*70)
    print("\nThis demo shows the complete workflow for RTSP camera streaming.")
    print("Prerequisites:")
    print("  - Backend server running: uvicorn main:app --reload --port 8000")
    print("  - Environment variables configured in backend/.env")
    print("  - (Optional) WebRTC bridge running for actual streaming")
    
    # Step 1: Admin registers RTSP stream
    print_step(1, "Admin Registers RTSP Stream")
    
    print("\nThe admin uses their API key to register a new RTSP camera stream.")
    print("The RTSP URL (rtsp://10.0.0.2:8554) is stored server-side only.")
    
    cmd = """curl -X POST http://localhost:8000/api/streams/start \\
  -H "Content-Type: application/json" \\
  -H "X-ADMIN-KEY: dev-admin-key-change-in-production" \\
  -d '{
    "rtsp_url": "rtsp://10.0.0.2:8554",
    "booking_id": "booking-123",
    "type": "rtsp"
  }'"""
    
    print_command(cmd)
    
    response = {
        "stream_id": "550e8400-e29b-41d4-a716-446655440000"
    }
    print_response(response)
    
    print("\n📝 Note: The RTSP URL is NOT returned for security reasons.")
    
    stream_id = response["stream_id"]
    
    # Step 2: User gets stream metadata
    print_step(2, "User Gets Stream Metadata")
    
    print("\nAny authenticated user can retrieve basic stream metadata.")
    print("This includes type, status, and booking_id, but NOT the RTSP URL.")
    
    cmd = f"""curl http://localhost:8000/api/streams/{stream_id} \\
  -H "Authorization: Bearer USER_JWT_TOKEN" """
    
    print_command(cmd)
    
    response = {
        "stream_id": stream_id,
        "type": "rtsp",
        "booking_id": "booking-123",
        "status": "running",
        "created_at": "2024-01-15T10:30:00Z"
    }
    print_response(response)
    
    print("\n🔒 Security: RTSP URL is never exposed in metadata.")
    
    # Step 3: Booked user gets WebSocket signaling info
    print_step(3, "Booked User Gets WebSocket Signaling Info")
    
    print("\nOnly users with an active booking can get the WebSocket URL.")
    print("The backend validates:")
    print("  - User has valid JWT token")
    print("  - User has active booking for booking-123")
    print("  - Stream status is 'running'")
    
    cmd = f"""curl http://localhost:8000/api/streams/{stream_id}/signaling-info \\
  -H "Authorization: Bearer BOOKED_USER_JWT_TOKEN" """
    
    print_command(cmd)
    
    response = {
        "ws_url": f"ws://localhost:8081/ws/stream?stream_id={stream_id}"
    }
    print_response(response)
    
    print("\n📡 The frontend uses this WebSocket URL to connect to the bridge.")
    print("   The bridge then handles the RTSP-to-WebRTC conversion.")
    
    # Step 4: Frontend establishes WebRTC connection
    print_step(4, "Frontend Establishes WebRTC Connection")
    
    print("\nThe frontend JavaScript code:")
    print("  1. Opens WebSocket connection to the bridge")
    print("  2. Sends SDP offer")
    print("  3. Receives SDP answer")
    print("  4. Exchanges ICE candidates")
    print("  5. Displays video stream")
    
    js_code = f"""// Frontend JavaScript (example)
const ws = new WebSocket('{response["ws_url"]}');

ws.onopen = () => {{
  // Create RTCPeerConnection
  const pc = new RTCPeerConnection({{
    iceServers: [{{ urls: 'stun:stun.l.google.com:19302' }}]
  }});
  
  // Create offer
  pc.createOffer().then(offer => {{
    pc.setLocalDescription(offer);
    ws.send(JSON.stringify({{ type: 'offer', sdp: offer.sdp }}));
  }});
  
  // Handle answer
  ws.onmessage = (event) => {{
    const msg = JSON.parse(event.data);
    if (msg.type === 'answer') {{
      pc.setRemoteDescription(new RTCSessionDescription(msg));
    }}
  }};
  
  // Display video
  pc.ontrack = (event) => {{
    videoElement.srcObject = event.streams[0];
  }};
}};"""
    
    print(f"\n💻 Example Code:")
    for line in js_code.split('\n'):
        print(f"   {line}")
    
    # Step 5: Admin stops stream
    print_step(5, "Admin Stops Stream")
    
    print("\nWhen the session ends, the admin can stop the stream.")
    
    cmd = f"""curl -X POST http://localhost:8000/api/streams/stop \\
  -H "Content-Type: application/json" \\
  -H "X-ADMIN-KEY: dev-admin-key-change-in-production" \\
  -d '{{"stream_id": "{stream_id}"}}'"""
    
    print_command(cmd)
    
    response = {
        "message": "Stream stopped successfully",
        "stream_id": stream_id
    }
    print_response(response)
    
    print("\n🛑 The stream status is now 'stopped' and can no longer be accessed.")
    
    # Summary
    print("\n" + "="*70)
    print("  Summary")
    print("="*70)
    
    print("""
✅ Complete Workflow Demonstrated:

1. Admin registers RTSP stream → receives stream_id
2. User gets metadata → sees status, type, booking_id (NO RTSP URL)
3. Booked user gets signaling → receives WebSocket URL
4. Frontend connects → establishes WebRTC session
5. Admin stops stream → status updated to 'stopped'

🔒 Security Features:
   - RTSP URL never exposed in any response
   - Admin-only registration and control
   - JWT authentication required
   - Active booking validation
   - Stream status verification

📚 Documentation:
   - Implementation Guide: RTSP_STREAMING_GUIDE.md
   - Quick Reference: RTSP_FEATURE_SUMMARY.md
   - API Tests: backend/test_stream_integration.py

🚀 Next Steps:
   1. Deploy GStreamer WebRTC bridge
   2. Test with real RTSP camera
   3. Configure production environment variables
""")
    
    print("="*70)
    print("For more details, see RTSP_STREAMING_GUIDE.md")
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
