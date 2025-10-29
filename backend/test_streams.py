"""
Tests for Streams Router

Legacy streams.json support removed — Robot Registry is now single source of truth for RTSP.

This test suite validates the streams endpoints functionality using Robot Registry.
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set test environment variables
os.environ["BRIDGE_WS_URL"] = "ws://localhost:8081/ws/stream"
os.environ["BRIDGE_CONTROL_SECRET"] = "test-bridge-secret-123"
os.environ["ENVIRONMENT"] = "development"
os.environ["DATABASE_TYPE"] = "mock"

from fastapi.testclient import TestClient
from main import app, db

# Test client
client = TestClient(app)


def test_get_robot_metadata():
    """Test getting stream metadata using robot_id (no rtsp_url in response)"""
    # First create a robot with RTSP
    robot = db.create_robot(
        name="Test Robot for Metadata",
        robot_type="turtlebot",
        rtsp_url="rtsp://example.com:554/test",
        status='active'
    )
    robot_id = robot["id"]
    
    # Get the metadata using robot_id as stream_id
    response = client.get(f"/api/streams/{robot_id}")
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["stream_id"] == str(robot_id)
    assert data["robot_id"] == robot_id
    assert data["robot_name"] == "Test Robot for Metadata"
    assert data["robot_type"] == "turtlebot"
    assert data["status"] == "active"
    # Ensure rtsp_url is NOT in response
    assert "rtsp_url" not in data
    print("✅ Test passed: get_robot_metadata")


def test_get_signaling_info():
    """Test getting signaling info for robot with RTSP"""
    # First create a robot with RTSP
    robot = db.create_robot(
        name="Test Robot for Signaling",
        robot_type="arm",
        rtsp_url="rtsp://example.com:554/signaling-test",
        status='active'
    )
    robot_id = robot["id"]
    
    # Get the signaling info
    response = client.get(f"/api/streams/{robot_id}/signaling-info")
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert "ws_url" in data
    assert f"robot_id={robot_id}" in data["ws_url"]
    # Ensure rtsp_url is NOT in response
    assert "rtsp_url" not in data
    print("✅ Test passed: get_signaling_info")


def test_bridge_authorization():
    """Test bridge authorization with secret"""
    # First create a robot with RTSP
    robot = db.create_robot(
        name="Test Robot for Bridge",
        robot_type="hand",
        rtsp_url="rtsp://example.com:554/bridge-test",
        status='active'
    )
    robot_id = robot["id"]
    
    # Authorize with bridge secret
    response = client.get(
        f"/api/streams/bridge/authorize?robot_id={robot_id}",
        headers={"X-BRIDGE-SECRET": "test-bridge-secret-123"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    # Bridge should get rtsp_url
    assert "rtsp_url" in data
    assert data["rtsp_url"] == "rtsp://example.com:554/bridge-test"
    assert data["robot_id"] == robot_id
    print("✅ Test passed: bridge_authorization")


def test_bridge_authorization_fails_without_secret():
    """Test that bridge authorization fails without secret"""
    # Create a robot
    robot = db.create_robot(
        name="Test Robot for Bridge Auth Fail",
        robot_type="turtlebot",
        rtsp_url="rtsp://example.com:554/fail-test",
        status='active'
    )
    robot_id = robot["id"]
    
    # Try to authorize without secret
    response = client.get(f"/api/streams/bridge/authorize?robot_id={robot_id}")
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 401
    print("✅ Test passed: bridge_authorization_fails_without_secret")


def test_robot_without_rtsp():
    """Test getting signaling info for robot without RTSP returns 404"""
    # Create a robot without RTSP
    robot = db.create_robot(
        name="Test Robot No RTSP",
        robot_type="arm",
        status='active'
    )
    robot_id = robot["id"]
    
    # Try to get signaling info
    response = client.get(f"/api/streams/{robot_id}/signaling-info")
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 404
    assert "not configured" in response.json()["detail"].lower()
    print("✅ Test passed: robot_without_rtsp")


def test_inactive_robot():
    """Test getting signaling info for inactive robot returns 403"""
    # Create an inactive robot with RTSP
    robot = db.create_robot(
        name="Test Inactive Robot",
        robot_type="hand",
        rtsp_url="rtsp://example.com:554/inactive",
        status='inactive'
    )
    robot_id = robot["id"]
    
    # Try to get signaling info
    response = client.get(f"/api/streams/{robot_id}/signaling-info")
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 403
    assert "not active" in response.json()["detail"].lower()
    print("✅ Test passed: inactive_robot")


def test_nonexistent_robot():
    """Test getting stream info for non-existent robot returns 404"""
    response = client.get("/api/streams/999999")
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 404
    print("✅ Test passed: nonexistent_robot")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("Running Streams Router Tests (Robot Registry)")
    print("="*70 + "\n")
    
    # Clean up any existing test robots
    if hasattr(db, '_robots'):
        db._robots = [r for r in db._robots if not r.get('name', '').startswith('Test Robot')]
        print("🧹 Cleaned up existing test data\n")
    
    tests = [
        test_get_robot_metadata,
        test_get_signaling_info,
        test_bridge_authorization,
        test_bridge_authorization_fails_without_secret,
        test_robot_without_rtsp,
        test_inactive_robot,
        test_nonexistent_robot,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            print(f"\n▶️  Running: {test.__name__}")
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ Test failed: {test.__name__}")
            print(f"   Error: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ Test error: {test.__name__}")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)
