#!/usr/bin/env python3
"""
Test script to validate Theia container configuration for external hostname
"""

import os
import sys
import subprocess
import time
import requests
import json

def test_theia_container_config():
    """Test that Theia containers are configured with external hostname"""
    
    # Load environment
    sys.path.append('/home/runner/work/Robot-live-console-v2/Robot-live-console-v2/backend')
    from services.theia_service import TheiaContainerManager
    
    # Create test manager
    manager = TheiaContainerManager()
    
    # Test user ID for testing
    test_user_id = 9999
    
    print("Testing Theia container configuration...")
    print(f"SERVER_HOST: {os.getenv('SERVER_HOST', 'not set')}")
    
    # Get container status (should show external URL)
    status = manager.get_container_status(test_user_id)
    print(f"\nContainer status before starting: {status}")
    
    # Test container start (this will create the container with external config)
    print(f"\nStarting test container for user {test_user_id}...")
    try:
        result = manager.start_container(test_user_id)
        print(f"Container start result: {result}")
        
        if result.get('success'):
            # Wait a moment for container to be ready
            time.sleep(5)
            
            # Get status again to see the external URL
            status = manager.get_container_status(test_user_id)
            print(f"\nContainer status after starting: {status}")
            
            # Test if the URL contains the external IP instead of localhost
            if status.get('url'):
                if 'localhost' in status['url'] or '127.0.0.1' in status['url']:
                    print("❌ FAIL: Container URL still contains localhost!")
                    return False
                elif '172.232.105.47' in status['url']:
                    print("✅ PASS: Container URL uses external IP!")
                    return True
                else:
                    print(f"⚠️  WARNING: Container URL uses unexpected host: {status['url']}")
                    return False
            else:
                print("❌ FAIL: No URL returned in status")
                return False
        else:
            print(f"❌ FAIL: Could not start container: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: Exception during test: {e}")
        return False
        
    finally:
        # Clean up test container
        try:
            print(f"\nCleaning up test container...")
            subprocess.run([
                "docker", "stop", f"theia-user-{test_user_id}"
            ], capture_output=True, timeout=10)
            subprocess.run([
                "docker", "rm", f"theia-user-{test_user_id}"
            ], capture_output=True, timeout=10)
            print("Test container cleaned up")
        except Exception as e:
            print(f"Warning: Could not clean up test container: {e}")

if __name__ == "__main__":
    # Set up environment
    os.environ['SERVER_HOST'] = '172.232.105.47'
    
    print("🧪 Testing Theia External Hostname Configuration")
    print("=" * 50)
    
    success = test_theia_container_config()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ TEST PASSED: Theia containers configured with external hostname")
        sys.exit(0)
    else:
        print("❌ TEST FAILED: Theia containers still using localhost")
        sys.exit(1)