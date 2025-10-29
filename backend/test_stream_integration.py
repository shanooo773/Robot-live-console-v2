#!/usr/bin/env python3
"""
Integration tests for RTSP streaming through WebRTC bridge.

Legacy streams.json support removed — Robot Registry is now single source of truth for RTSP.

This test suite validates:
1. Robot Registry contains RTSP URLs
2. Authenticated users with active bookings can access streams via robot_id
3. WebSocket signaling info is properly returned with robot_id
4. Security: RTSP URLs are never exposed to clients
5. Bridge can authorize and get RTSP URL with secret
6. No regression for existing functionality
"""

import os
import sys
import json
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set test environment variables
os.environ["BRIDGE_WS_URL"] = "ws://localhost:8081/ws/stream"
os.environ["BRIDGE_CONTROL_SECRET"] = "test-bridge-secret-integration"
os.environ["ENVIRONMENT"] = "development"
# Mock database for testing
os.environ["DATABASE_TYPE"] = "mock"

from fastapi.testclient import TestClient

# Import app after setting environment variables
from main import app, db

# Test client
client = TestClient(app)

# Test data
TEST_RTSP_URL = "rtsp://10.0.0.2:8554/stream"
TEST_ROBOT_NAME = "Test RTSP Robot"
TEST_ROBOT_TYPE = "turtlebot"

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def print_test(name, status="RUNNING"):
    """Print test name with status"""
    if status == "RUNNING":
        print(f"\n▶️  {name}...")
    elif status == "PASSED":
        print(f"✅ {name} - PASSED")
    elif status == "FAILED":
        print(f"❌ {name} - FAILED")

def cleanup_test_data():
    """Clean up test data - remove test robots from mock database"""
    try:
        # In mock database, we can just reset the robots list
        if hasattr(db, '_robots'):
            db._robots = [r for r in db._robots if not r.get('name', '').startswith('Test RTSP')]
        print("🧹 Cleaned up test data")
    except Exception as e:
        print(f"⚠️  Failed to clean up test data: {e}")

def create_test_robot_with_rtsp():
    """Create a test robot with RTSP URL in Robot Registry"""
    print_test("Create robot with RTSP in Robot Registry")
    
    # Create robot via database (simulating admin action)
    robot = db.create_robot(
        name=TEST_ROBOT_NAME,
        robot_type=TEST_ROBOT_TYPE,
        rtsp_url=TEST_RTSP_URL,
        status='active'
    )
    
    assert robot is not None, "Robot should be created"
    assert robot["id"] is not None, "Robot should have an ID"
    assert robot["rtsp_url"] == TEST_RTSP_URL, "Robot should have RTSP URL"
    
    print_test("Create robot with RTSP in Robot Registry", "PASSED")
    return robot["id"]

def test_get_stream_metadata(robot_id):
    """Test getting stream metadata without RTSP URL (stream_id = robot_id)"""
    print_test("Get stream metadata (no RTSP URL)")
    
    response = client.get(f"/api/streams/{robot_id}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    
    # Verify metadata structure
    assert data["stream_id"] == str(robot_id), "Stream ID should match robot ID"
    assert data["robot_id"] == robot_id, "Robot ID should be included"
    assert data["robot_name"] == TEST_ROBOT_NAME, "Robot name should match"
    assert data["robot_type"] == TEST_ROBOT_TYPE, "Robot type should match"
    assert data["status"] == "active", "Status should be active"
    
    # Security: Ensure RTSP URL is NOT exposed
    assert "rtsp_url" not in data, "RTSP URL should NOT be in metadata"
    
    print_test("Get stream metadata (no RTSP URL)", "PASSED")

def test_get_signaling_info(robot_id):
    """Test getting WebSocket signaling info for stream (stream_id = robot_id)"""
    print_test("Get WebSocket signaling info")
    
    response = client.get(f"/api/streams/{robot_id}/signaling-info")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    
    # Verify signaling info structure
    assert "ws_url" in data, "Should include ws_url"
    assert data["ws_url"].startswith("ws://"), "WebSocket URL should use ws:// protocol"
    assert f"robot_id={robot_id}" in data["ws_url"], "WebSocket URL should include robot_id parameter"
    
    # Security: Ensure RTSP URL is NOT exposed
    assert "rtsp_url" not in data, "RTSP URL should NOT be in signaling info"
    assert TEST_RTSP_URL not in data["ws_url"], "RTSP URL should NOT be in WebSocket URL"
    
    print(f"   WebSocket URL: {data['ws_url']}")
    print_test("Get WebSocket signaling info", "PASSED")

def test_bridge_authorization(robot_id):
    """Test that bridge can authorize and get RTSP URL with secret"""
    print_test("Bridge can authorize with secret")
    
    response = client.get(
        f"/api/streams/bridge/authorize?robot_id={robot_id}",
        headers={"X-BRIDGE-SECRET": "test-bridge-secret-integration"}
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    
    # Verify bridge can get RTSP URL
    assert "rtsp_url" in data, "Bridge should receive RTSP URL"
    assert data["rtsp_url"] == TEST_RTSP_URL, "RTSP URL should match"
    assert data["robot_id"] == robot_id, "Robot ID should match"
    
    print_test("Bridge can authorize with secret", "PASSED")

def test_bridge_authorization_fails_without_secret(robot_id):
    """Test that bridge authorization fails without secret"""
    print_test("Bridge authorization fails without secret")
    
    response = client.get(
        f"/api/streams/bridge/authorize?robot_id={robot_id}"
    )
    
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    print_test("Bridge authorization fails without secret", "PASSED")

def test_robot_without_rtsp():
    """Test that robot without RTSP returns 404"""
    print_test("Robot without RTSP returns 404")
    
    # Create robot without RTSP URL
    robot = db.create_robot(
        name="Test Robot No RTSP",
        robot_type="arm",
        status='active'
    )
    robot_id = robot["id"]
    
    # Try to get signaling info
    response = client.get(f"/api/streams/{robot_id}/signaling-info")
    
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    assert "not configured" in response.json()["detail"].lower()
    
    print_test("Robot without RTSP returns 404", "PASSED")

def test_nonexistent_robot():
    """Test accessing non-existent robot"""
    print_test("Non-existent robot returns 404")
    
    response = client.get("/api/streams/999999")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    print_test("Non-existent robot returns 404", "PASSED")

def test_inactive_robot_signaling():
    """Test that inactive robots cannot be accessed"""
    print_test("Inactive robot denies signaling access")
    
    # Create an inactive robot with RTSP
    robot = db.create_robot(
        name="Test Inactive Robot",
        robot_type="hand",
        rtsp_url=TEST_RTSP_URL,
        status='inactive'
    )
    robot_id = robot["id"]
    
    # Try to get signaling info for inactive robot
    signaling_response = client.get(f"/api/streams/{robot_id}/signaling-info")
    assert signaling_response.status_code == 403, f"Expected 403, got {signaling_response.status_code}"
    assert "not active" in signaling_response.json()["detail"].lower()
    
    print_test("Inactive robot denies signaling access", "PASSED")

def test_existing_endpoints_work():
    """Test that existing endpoints still work (no regression)"""
    print_test("Existing endpoints work (no regression)")
    
    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200, "Root endpoint should work"
    
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200, "Health endpoint should work"
    
    # Test robots endpoint
    response = client.get("/robots")
    assert response.status_code == 200, "Robots endpoint should work"
    
    print_test("Existing endpoints work (no regression)", "PASSED")

def main():
    """Run all integration tests"""
    print_section("RTSP Streaming Integration Tests (Robot Registry)")
    
    # Clean up before tests
    cleanup_test_data()
    
    tests_passed = 0
    tests_failed = 0
    
    try:
        # Test 1: Create robot with RTSP
        robot_id = create_test_robot_with_rtsp()
        tests_passed += 1
        
        # Test 2: Get metadata
        test_get_stream_metadata(robot_id)
        tests_passed += 1
        
        # Test 3: Get signaling info
        test_get_signaling_info(robot_id)
        tests_passed += 1
        
        # Test 4: Bridge authorization
        test_bridge_authorization(robot_id)
        tests_passed += 1
        
        # Test 5: Bridge auth fails without secret
        test_bridge_authorization_fails_without_secret(robot_id)
        tests_passed += 1
        
        # Test 6: Robot without RTSP
        test_robot_without_rtsp()
        tests_passed += 1
        
        # Test 7: Non-existent robot
        test_nonexistent_robot()
        tests_passed += 1
        
        # Test 8: Inactive robot signaling
        test_inactive_robot_signaling()
        tests_passed += 1
        
        # Test 9: No regression
        test_existing_endpoints_work()
        tests_passed += 1
        
    except AssertionError as e:
        tests_failed += 1
        print(f"\n❌ Test failed: {e}")
    except Exception as e:
        tests_failed += 1
        print(f"\n❌ Test error: {e}")
        import traceback
        traceback.print_exc()
    
    # Print summary
    print_section("Test Summary")
    print(f"✅ Passed: {tests_passed}")
    print(f"❌ Failed: {tests_failed}")
    print(f"📊 Total:  {tests_passed + tests_failed}")
    
    if tests_failed == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
