#!/usr/bin/env python3
"""
Integration tests for RTSP streaming through WebRTC bridge.

This test suite validates:
1. Admin can register RTSP streams
2. Authenticated users with active bookings can access streams
3. WebSocket signaling info is properly returned
4. Security: RTSP URLs are never exposed
5. No regression for existing functionality
"""

import os
import sys
import json
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Set test environment variables
os.environ["ADMIN_API_KEY"] = "test-admin-key-integration"
os.environ["BRIDGE_WS_URL"] = "ws://localhost:8081/ws/stream"
os.environ["BRIDGE_CONTROL_URL"] = "http://localhost:8081"
os.environ["ENVIRONMENT"] = "development"

from fastapi.testclient import TestClient

# Import app after setting environment variables
from main import app

# Test client
client = TestClient(app)

# Test data
TEST_RTSP_URL = "rtsp://10.0.0.2:8554/stream"
TEST_BOOKING_ID = "booking-123"

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
    """Clean up test data files"""
    streams_file = Path(__file__).parent / "data" / "streams.json"
    if streams_file.exists():
        streams_file.unlink()
        print("🧹 Cleaned up test data")

def test_admin_register_rtsp_stream():
    """Test that admin can register an RTSP stream"""
    print_test("Admin can register RTSP stream")
    
    response = client.post(
        "/api/streams/start",
        json={
            "rtsp_url": TEST_RTSP_URL,
            "booking_id": TEST_BOOKING_ID,
            "stream_id": "test-stream-001",
            "type": "rtsp"
        },
        headers={"X-ADMIN-KEY": "test-admin-key-integration"}
    )
    
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    data = response.json()
    
    # Verify response structure
    assert "stream_id" in data, "Response should include stream_id"
    assert data["stream_id"] == "test-stream-001", "Stream ID should match request"
    
    # Security: Ensure RTSP URL is NOT in response
    assert "rtsp_url" not in data, "RTSP URL should NOT be exposed in response"
    
    print_test("Admin can register RTSP stream", "PASSED")
    return data["stream_id"]

def test_get_stream_metadata(stream_id):
    """Test getting stream metadata without RTSP URL"""
    print_test("Get stream metadata (no RTSP URL)")
    
    response = client.get(f"/api/streams/{stream_id}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    
    # Verify metadata structure
    assert data["stream_id"] == stream_id, "Stream ID should match"
    assert data["type"] == "rtsp", "Type should be rtsp"
    assert data["booking_id"] == TEST_BOOKING_ID, "Booking ID should match"
    assert data["status"] == "running", "Status should be running"
    assert "created_at" in data, "Should include created_at timestamp"
    
    # Security: Ensure RTSP URL is NOT exposed
    assert "rtsp_url" not in data, "RTSP URL should NOT be in metadata"
    
    print_test("Get stream metadata (no RTSP URL)", "PASSED")

def test_get_signaling_info(stream_id):
    """Test getting WebSocket signaling info for stream"""
    print_test("Get WebSocket signaling info")
    
    response = client.get(f"/api/streams/{stream_id}/signaling-info")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    
    # Verify signaling info structure
    assert "ws_url" in data, "Should include ws_url"
    assert data["ws_url"].startswith("ws://"), "WebSocket URL should use ws:// protocol"
    assert "stream_id" in data["ws_url"], "WebSocket URL should include stream_id parameter"
    
    # Security: Ensure RTSP URL is NOT exposed
    assert "rtsp_url" not in data, "RTSP URL should NOT be in signaling info"
    assert TEST_RTSP_URL not in data["ws_url"], "RTSP URL should NOT be in WebSocket URL"
    
    print(f"   WebSocket URL: {data['ws_url']}")
    print_test("Get WebSocket signaling info", "PASSED")

def test_stop_stream(stream_id):
    """Test stopping a stream"""
    print_test("Admin can stop stream")
    
    response = client.post(
        "/api/streams/stop",
        json={"stream_id": stream_id},
        headers={"X-ADMIN-KEY": "test-admin-key-integration"}
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    
    assert data["stream_id"] == stream_id, "Stream ID should match"
    
    # Verify status was updated
    metadata_response = client.get(f"/api/streams/{stream_id}")
    assert metadata_response.status_code == 200
    metadata = metadata_response.json()
    assert metadata["status"] == "stopped", "Status should be updated to stopped"
    
    print_test("Admin can stop stream", "PASSED")

def test_invalid_rtsp_url():
    """Test that invalid RTSP URLs are rejected"""
    print_test("Invalid RTSP URL is rejected")
    
    response = client.post(
        "/api/streams/start",
        json={
            "rtsp_url": "http://10.0.0.2:8554/stream",  # Wrong protocol
            "booking_id": "booking-invalid",
            "type": "rtsp"
        },
        headers={"X-ADMIN-KEY": "test-admin-key-integration"}
    )
    
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    assert "Invalid RTSP URL" in response.json()["detail"]
    
    print_test("Invalid RTSP URL is rejected", "PASSED")

def test_unauthorized_access():
    """Test that unauthorized requests are rejected"""
    print_test("Unauthorized access is rejected")
    
    response = client.post(
        "/api/streams/start",
        json={
            "rtsp_url": TEST_RTSP_URL,
            "booking_id": "booking-unauth",
            "type": "rtsp"
        },
        headers={"X-ADMIN-KEY": "wrong-key"}
    )
    
    assert response.status_code == 401, f"Expected 401, got {response.status_code}"
    
    print_test("Unauthorized access is rejected", "PASSED")

def test_nonexistent_stream():
    """Test accessing non-existent stream"""
    print_test("Non-existent stream returns 404")
    
    response = client.get("/api/streams/nonexistent-stream-xyz")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    print_test("Non-existent stream returns 404", "PASSED")

def test_stopped_stream_signaling():
    """Test that stopped streams cannot be accessed"""
    print_test("Stopped stream denies signaling access")
    
    # Create and stop a stream
    create_response = client.post(
        "/api/streams/start",
        json={
            "rtsp_url": TEST_RTSP_URL,
            "booking_id": "booking-stopped",
            "stream_id": "stopped-stream",
            "type": "rtsp"
        },
        headers={"X-ADMIN-KEY": "test-admin-key-integration"}
    )
    assert create_response.status_code == 201
    
    stop_response = client.post(
        "/api/streams/stop",
        json={"stream_id": "stopped-stream"},
        headers={"X-ADMIN-KEY": "test-admin-key-integration"}
    )
    assert stop_response.status_code == 200
    
    # Try to get signaling info for stopped stream
    signaling_response = client.get("/api/streams/stopped-stream/signaling-info")
    assert signaling_response.status_code == 403, f"Expected 403, got {signaling_response.status_code}"
    assert "not running" in signaling_response.json()["detail"].lower()
    
    print_test("Stopped stream denies signaling access", "PASSED")

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
    print_section("RTSP Streaming Integration Tests")
    
    # Clean up before tests
    cleanup_test_data()
    
    tests_passed = 0
    tests_failed = 0
    
    try:
        # Test 1: Admin registers stream
        stream_id = test_admin_register_rtsp_stream()
        tests_passed += 1
        
        # Test 2: Get metadata
        test_get_stream_metadata(stream_id)
        tests_passed += 1
        
        # Test 3: Get signaling info
        test_get_signaling_info(stream_id)
        tests_passed += 1
        
        # Test 4: Stop stream
        test_stop_stream(stream_id)
        tests_passed += 1
        
        # Test 5: Invalid RTSP URL
        test_invalid_rtsp_url()
        tests_passed += 1
        
        # Test 6: Unauthorized access
        test_unauthorized_access()
        tests_passed += 1
        
        # Test 7: Non-existent stream
        test_nonexistent_stream()
        tests_passed += 1
        
        # Test 8: Stopped stream signaling
        test_stopped_stream_signaling()
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
