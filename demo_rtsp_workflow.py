#!/usr/bin/env python3
"""
End-to-End Demo: RTSP Streaming Feature

This script demonstrates the complete workflow of the RTSP streaming feature using Robot Registry:
1. Admin creates a robot with RTSP URL
2. User with booking accesses stream
3. Stream metadata is retrieved
4. WebSocket signaling info is obtained
5. Bridge authorizes to get RTSP URL

Run this after starting the backend server to see the feature in action.

NOTE: Legacy streams.json approach has been removed. All RTSP URLs are now managed via Robot Registry.
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
    print("  (Robot Registry Approach)")
    print("="*70)
    print("\nThis demo shows the complete workflow for RTSP camera streaming.")
    print("Prerequisites:")
    print("  - Backend server running: uvicorn main:app --reload --port 8000")
    print("  - Environment variables configured in backend/.env")
    print("  - (Optional) WebRTC bridge running for actual streaming")
    
    # Step 1: Admin creates robot with RTSP URL
    print_step(1, "Admin Creates Robot with RTSP URL")
    
    print("\nThe admin creates a robot with an RTSP URL in the Robot Registry.")
    print("The RTSP URL (rtsp://10.0.0.2:8554) is stored in the database.")
    
    cmd = """curl -X POST http://localhost:8000/admin/robots \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer ADMIN_JWT_TOKEN" \\
  -d '{
    "name": "Security Camera 1",
    "type": "camera",
    "rtsp_url": "rtsp://10.0.0.2:8554",
    "status": "active"
  }'"""
    
    print_command(cmd)
    
    response = {
        "id": 5,
        "name": "Security Camera 1",
        "type": "camera",
        "rtsp_url": "rtsp://10.0.0.2:8554",
        "status": "active",
        "created_at": "2024-01-20T10:00:00"
    }
    print_response(response)
    
    print("\n📝 Note: RTSP URL is visible in admin responses but NOT in client-facing endpoints.")
    
    robot_id = response["id"]
    
    # Step 2: User gets stream metadata (using robot_id as stream_id)
    print_step(2, "User Gets Stream Metadata")
    
    print("\nAny authenticated user can retrieve stream metadata using robot_id.")
    print("This includes robot info and status, but NOT the RTSP URL.")
    
    cmd = f"""curl http://localhost:8000/api/streams/{robot_id} \\
  -H "Authorization: Bearer USER_JWT_TOKEN" """
    
    print_command(cmd)
    
    response = {
        "stream_id": str(robot_id),
        "robot_id": robot_id,
        "robot_name": "Security Camera 1",
        "robot_type": "camera",
        "status": "active"
    }
    print_response(response)
    
    print("\n🔒 Security: RTSP URL is never exposed in client-facing metadata.")
    
    # Step 3: Booked user gets WebSocket signaling info
    print_step(3, "Booked User Gets WebSocket Signaling Info")
    
    print("\nOnly users with an active booking can get the WebSocket URL.")
    print("The backend validates:")
    print("  - User has valid JWT token")
    print("  - User has active booking for the robot")
    print("  - Robot is active")
    
    cmd = f"""curl http://localhost:8000/api/streams/{robot_id}/signaling-info \\
  -H "Authorization: Bearer BOOKED_USER_JWT_TOKEN" """
    
    print_command(cmd)
    
    response = {
        "ws_url": f"ws://localhost:8081/ws/stream?robot_id={robot_id}"
    }
    print_response(response)
    
    print("\n📡 The frontend uses this WebSocket URL to connect to the bridge.")
    print("   The bridge then handles the RTSP-to-WebRTC conversion.")
    
    # Step 4: Bridge authorizes to get RTSP URL
    print_step(4, "Bridge Authorizes to Get RTSP URL")
    
    print("\nThe bridge must authorize with BRIDGE_CONTROL_SECRET to get RTSP URL.")
    print("This is the ONLY endpoint that returns the RTSP URL.")
    
    cmd = f"""curl "http://localhost:8000/api/streams/bridge/authorize?robot_id={robot_id}" \\
  -H "X-BRIDGE-SECRET: dev-bridge-secret-change-in-production" """
    
    print_command(cmd)
    
    response = {
        "rtsp_url": "rtsp://10.0.0.2:8554",
        "robot_id": robot_id,
        "robot_name": "Security Camera 1"
    }
    print_response(response)
    
    print("\n🔒 Security: Only the bridge can access RTSP URLs using the secret.")
    
    # Step 5: Frontend establishes WebRTC connection
    print_step(5, "Frontend Establishes WebRTC Connection")
    
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
    
    # Summary
    print("\n" + "="*70)
    print("  Summary")
    print("="*70)
    
    print("""
✅ Complete Workflow Demonstrated:

1. Admin creates robot with RTSP URL → robot stored in Registry
2. User gets metadata → sees robot info and status (NO RTSP URL)
3. Booked user gets signaling → receives WebSocket URL with robot_id
4. Bridge authorizes → gets RTSP URL using secret
5. Frontend connects → establishes WebRTC session

🔒 Security Features:
- RTSP URL never exposed to clients
- Bridge must authorize with secret
- Booking validation enforced
- Robot status verified

📝 Key Differences from Legacy Approach:
- No more POST /api/streams/start or /api/streams/stop
- RTSP URLs managed in Robot Registry (database)
- stream_id corresponds to robot_id
- Bridge must authorize to get RTSP URL

🚀 Next Steps:
- Deploy external WebRTC bridge (GStreamer)
- Configure BRIDGE_CONTROL_SECRET in production
- Test with real RTSP camera
- Add RTSP URLs to robots via admin dashboard

For complete documentation, see RTSP_STREAMING_GUIDE.md
""")

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
