"""
Tests for Streams Router

This test suite validates the streams endpoints functionality.
"""

import os
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from main import app

# Test client
client = TestClient(app)

# Test admin API key for fallback auth
os.environ["ADMIN_API_KEY"] = "test-admin-key-123"


def test_start_stream_with_admin_key():
    """Test starting a stream with admin key authentication"""
    response = client.post(
        "/api/streams/start",
        json={
            "rtsp_url": "rtsp://example.com:554/stream",
            "booking_id": "booking-123",
            "stream_id": "test-stream-001",
            "type": "rtsp"
        },
        headers={"X-ADMIN-KEY": "test-admin-key-123"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 201
    data = response.json()
    assert "stream_id" in data
    assert data["stream_id"] == "test-stream-001"
    # Ensure rtsp_url is NOT in response
    assert "rtsp_url" not in data
    print("✅ Test passed: start_stream_with_admin_key")


def test_start_stream_invalid_rtsp_url():
    """Test that invalid RTSP URLs are rejected"""
    response = client.post(
        "/api/streams/start",
        json={
            "rtsp_url": "http://example.com/stream",  # Should be rtsp://
            "booking_id": "booking-456",
            "type": "rtsp"
        },
        headers={"X-ADMIN-KEY": "test-admin-key-123"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 400
    assert "Invalid RTSP URL" in response.json()["detail"]
    print("✅ Test passed: start_stream_invalid_rtsp_url")


def test_start_stream_unauthorized():
    """Test that unauthorized requests are rejected"""
    response = client.post(
        "/api/streams/start",
        json={
            "rtsp_url": "rtsp://example.com:554/stream",
            "booking_id": "booking-789",
            "type": "rtsp"
        },
        headers={"X-ADMIN-KEY": "wrong-key"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 401
    print("✅ Test passed: start_stream_unauthorized")


def test_get_stream_metadata():
    """Test getting stream metadata (no rtsp_url in response)"""
    # First create a stream
    create_response = client.post(
        "/api/streams/start",
        json={
            "rtsp_url": "rtsp://example.com:554/test",
            "booking_id": "booking-meta-test",
            "stream_id": "meta-test-stream",
            "type": "rtsp"
        },
        headers={"X-ADMIN-KEY": "test-admin-key-123"}
    )
    assert create_response.status_code == 201
    
    # Get the metadata
    response = client.get("/api/streams/meta-test-stream")
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["stream_id"] == "meta-test-stream"
    assert data["type"] == "rtsp"
    assert data["booking_id"] == "booking-meta-test"
    assert data["status"] == "running"
    assert "created_at" in data
    # Ensure rtsp_url is NOT in response
    assert "rtsp_url" not in data
    print("✅ Test passed: get_stream_metadata")


def test_stop_stream():
    """Test stopping a stream"""
    # First create a stream
    create_response = client.post(
        "/api/streams/start",
        json={
            "rtsp_url": "rtsp://example.com:554/stop-test",
            "booking_id": "booking-stop-test",
            "stream_id": "stop-test-stream",
            "type": "rtsp"
        },
        headers={"X-ADMIN-KEY": "test-admin-key-123"}
    )
    assert create_response.status_code == 201
    
    # Stop the stream
    response = client.post(
        "/api/streams/stop",
        json={"stream_id": "stop-test-stream"},
        headers={"X-ADMIN-KEY": "test-admin-key-123"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["stream_id"] == "stop-test-stream"
    
    # Verify status is updated
    metadata_response = client.get("/api/streams/stop-test-stream")
    assert metadata_response.status_code == 200
    metadata = metadata_response.json()
    assert metadata["status"] == "stopped"
    print("✅ Test passed: stop_stream")


def test_get_stream_not_found():
    """Test getting a non-existent stream"""
    response = client.get("/api/streams/non-existent-stream")
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 404
    print("✅ Test passed: get_stream_not_found")


def test_stop_stream_not_found():
    """Test stopping a non-existent stream"""
    response = client.post(
        "/api/streams/stop",
        json={"stream_id": "non-existent-stream"},
        headers={"X-ADMIN-KEY": "test-admin-key-123"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 404
    print("✅ Test passed: stop_stream_not_found")


def test_webrtc_stream_type():
    """Test creating a WebRTC stream (no RTSP URL validation)"""
    response = client.post(
        "/api/streams/start",
        json={
            "rtsp_url": "http://example.com/webrtc",  # Not rtsp:// but type is webrtc
            "booking_id": "booking-webrtc",
            "stream_id": "webrtc-test-stream",
            "type": "webrtc"
        },
        headers={"X-ADMIN-KEY": "test-admin-key-123"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    # Should succeed because validation only applies to type='rtsp'
    assert response.status_code == 201
    print("✅ Test passed: webrtc_stream_type")


def test_duplicate_stream_id():
    """Test creating a stream with duplicate stream_id"""
    # Create first stream
    response1 = client.post(
        "/api/streams/start",
        json={
            "rtsp_url": "rtsp://example.com:554/dup",
            "booking_id": "booking-dup",
            "stream_id": "duplicate-stream",
            "type": "rtsp"
        },
        headers={"X-ADMIN-KEY": "test-admin-key-123"}
    )
    assert response1.status_code == 201
    
    # Try to create another with same stream_id
    response2 = client.post(
        "/api/streams/start",
        json={
            "rtsp_url": "rtsp://example.com:554/dup2",
            "booking_id": "booking-dup2",
            "stream_id": "duplicate-stream",
            "type": "rtsp"
        },
        headers={"X-ADMIN-KEY": "test-admin-key-123"}
    )
    
    print(f"Response status: {response2.status_code}")
    print(f"Response body: {response2.json()}")
    
    assert response2.status_code == 409
    assert "already exists" in response2.json()["detail"]
    print("✅ Test passed: duplicate_stream_id")


def test_auto_generated_stream_id():
    """Test that stream_id is auto-generated when not provided"""
    response = client.post(
        "/api/streams/start",
        json={
            "rtsp_url": "rtsp://example.com:554/auto",
            "booking_id": "booking-auto",
            "type": "rtsp"
            # No stream_id provided
        },
        headers={"X-ADMIN-KEY": "test-admin-key-123"}
    )
    
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    
    assert response.status_code == 201
    data = response.json()
    assert "stream_id" in data
    assert len(data["stream_id"]) > 0  # Should be a UUID
    print("✅ Test passed: auto_generated_stream_id")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("Running Streams Router Tests")
    print("="*70 + "\n")
    
    # Clean up any existing test data
    streams_file = Path(__file__).parent / "data" / "streams.json"
    if streams_file.exists():
        streams_file.unlink()
        print("🧹 Cleaned up existing test data\n")
    
    tests = [
        test_start_stream_with_admin_key,
        test_start_stream_invalid_rtsp_url,
        test_start_stream_unauthorized,
        test_get_stream_metadata,
        test_stop_stream,
        test_get_stream_not_found,
        test_stop_stream_not_found,
        test_webrtc_stream_type,
        test_duplicate_stream_id,
        test_auto_generated_stream_id,
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
            failed += 1
    
    print("\n" + "="*70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)
