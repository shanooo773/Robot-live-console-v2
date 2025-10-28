#!/usr/bin/env python3
"""
Quick validation script to verify RTSP streaming implementation.

This script checks:
1. Environment configuration
2. File structure
3. API endpoint availability (if server is running)
4. Documentation exists
"""

import os
import sys
from pathlib import Path

def print_header(title):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def check_mark(condition):
    """Return checkmark or X based on condition"""
    return "✅" if condition else "❌"

def check_environment():
    """
    Check environment configuration.
    
    Returns:
        bool: True if all required environment variables are configured, False otherwise.
    """
    print_header("Environment Configuration")
    
    required_vars = {
        "BRIDGE_WS_URL": "ws://localhost:8081/ws/stream",
        "BRIDGE_CONTROL_URL": "http://localhost:8081",
        "ADMIN_API_KEY": "dev-admin-key-change-in-production"
    }
    
    env_file = Path(__file__).parent / "backend" / ".env"
    
    if not env_file.exists():
        print("❌ .env file not found at backend/.env")
        return False
    
    print(f"✅ .env file found at {env_file}")
    
    # Read .env file
    env_content = env_file.read_text()
    
    all_found = True
    for var, default in required_vars.items():
        if var in env_content:
            print(f"✅ {var} configured")
        else:
            print(f"❌ {var} NOT configured")
            all_found = False
    
    return all_found

def check_files():
    """
    Check required files exist.
    
    Returns:
        bool: True if all required files exist, False otherwise.
    """
    print_header("File Structure")
    
    required_files = {
        "backend/routes/streams.py": "Streams router",
        "backend/test_streams.py": "Unit tests",
        "backend/test_stream_integration.py": "Integration tests",
        "backend/mock_webrtc_bridge.py": "Mock bridge for testing",
        "RTSP_STREAMING_GUIDE.md": "Implementation guide"
    }
    
    all_found = True
    for file_path, description in required_files.items():
        full_path = Path(__file__).parent / file_path
        exists = full_path.exists()
        print(f"{check_mark(exists)} {description}: {file_path}")
        if not exists:
            all_found = False
    
    return all_found

def check_api_endpoints():
    """
    Check if API endpoints are available (if server is running).
    
    Returns:
        bool: True if server is running and endpoints are accessible, 
              or if server is not running (allowing validation to continue).
    """
    print_header("API Endpoints")
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        endpoints = [
            ("/", "Root"),
            ("/health", "Health check"),
            ("/api/streams/nonexistent", "Stream metadata (404 expected)")
        ]
        
        server_running = False
        for endpoint, description in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=2)
                server_running = True
                print(f"✅ {description}: {endpoint} [{response.status_code}]")
            except requests.exceptions.RequestException:
                if not server_running:
                    print(f"⚠️  Server not running at {base_url}")
                    print("   Start server with: cd backend && uvicorn main:app --reload --port 8000")
                    return False
                print(f"❌ {description}: {endpoint} [ERROR]")
        
        return True
    
    except ImportError:
        print("⚠️  'requests' not installed, skipping API checks")
        print("   Install with: pip install requests")
        return True

def check_imports():
    """
    Check that streams router can be imported.
    
    Returns:
        bool: True if streams router and all required functions/objects exist, False otherwise.
    """
    print_header("Python Imports")
    
    backend_path = Path(__file__).parent / "backend"
    sys.path.insert(0, str(backend_path))
    
    try:
        # Try importing the router
        import routes.streams
        print("✅ Streams router imports successfully")
        
        # Check key functions exist
        required_attrs = [
            "router",
            "get_stream_by_id",
            "add_stream",
            "update_stream_status",
            "user_has_active_booking"
        ]
        
        all_found = True
        for attr in required_attrs:
            if hasattr(routes.streams, attr):
                print(f"✅ Function/object '{attr}' exists")
            else:
                print(f"❌ Function/object '{attr}' NOT found")
                all_found = False
        
        return all_found
    
    except ImportError as e:
        print(f"❌ Failed to import streams router: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking imports: {e}")
        return False

def check_documentation():
    """
    Check documentation quality.
    
    Returns:
        bool: True if all required documentation sections are present, False otherwise.
    """
    print_header("Documentation")
    
    guide_path = Path(__file__).parent / "RTSP_STREAMING_GUIDE.md"
    
    if not guide_path.exists():
        print("❌ Implementation guide not found")
        return False
    
    content = guide_path.read_text()
    
    required_sections = [
        "## Overview",
        "## Architecture",
        "## Configuration",
        "## Usage",
        "## Security Features",
        "## Testing",
        "## Troubleshooting",
        "## API Reference"
    ]
    
    all_found = True
    for section in required_sections:
        if section in content:
            print(f"✅ Section '{section}' present")
        else:
            print(f"❌ Section '{section}' missing")
            all_found = False
    
    return all_found

def main():
    """Run all validation checks"""
    print("="*70)
    print("  RTSP Streaming Implementation Validation")
    print("="*70)
    
    results = {
        "Environment": check_environment(),
        "Files": check_files(),
        "Imports": check_imports(),
        "Documentation": check_documentation(),
        "API": check_api_endpoints()
    }
    
    print_header("Summary")
    
    for check, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{check:20} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("🎉 All validation checks passed!")
        print("\nNext steps:")
        print("1. Start backend: cd backend && uvicorn main:app --reload --port 8000")
        print("2. Run tests: cd backend && python test_stream_integration.py")
        print("3. Review guide: cat RTSP_STREAMING_GUIDE.md")
    else:
        print("⚠️  Some validation checks failed. Review the output above.")
        print("\nCommon fixes:")
        print("- Install dependencies: pip install -r backend/requirements.txt")
        print("- Check .env configuration")
        print("- Ensure all files are present")
    print("="*70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
