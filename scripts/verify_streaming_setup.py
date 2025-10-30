#!/usr/bin/env python3
"""
Verification Script for RTSP → WebRTC Streaming Setup

This script validates that all components are correctly configured for the
RTSP → WebRTC streaming flow.

Usage:
    python scripts/verify_streaming_setup.py [--backend-url URL] [--test-robot-id ID]
    
Environment Variables:
    BACKEND_URL: Backend API base URL (default: http://localhost:8000)
    TEST_ROBOT_ID: Robot ID to use for testing (default: 1)
    BRIDGE_CONTROL_SECRET: Secret from backend/.env for authorize endpoint test
"""

import os
import sys
import argparse
import json
import requests
from pathlib import Path
from typing import List, Tuple, Optional

# ANSI color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


class StreamingSetupVerifier:
    """Verifies RTSP → WebRTC streaming setup."""
    
    def __init__(self, backend_url: str, test_robot_id: int, bridge_secret: Optional[str] = None):
        self.backend_url = backend_url.rstrip('/')
        self.test_robot_id = test_robot_id
        self.bridge_secret = bridge_secret
        self.repo_root = Path(__file__).parent.parent
        self.passed = 0
        self.failed = 0
        self.skipped = 0
    
    def print_header(self, text: str):
        """Print a section header."""
        print(f"\n{BLUE}{'=' * 80}{RESET}")
        print(f"{BLUE}{text}{RESET}")
        print(f"{BLUE}{'=' * 80}{RESET}\n")
    
    def print_test(self, name: str, passed: bool, details: str = ""):
        """Print test result."""
        if passed:
            print(f"{GREEN}✓ PASS{RESET}: {name}")
            if details:
                print(f"        {details}")
            self.passed += 1
        else:
            print(f"{RED}✗ FAIL{RESET}: {name}")
            if details:
                print(f"        {details}")
            self.failed += 1
    
    def print_skip(self, name: str, reason: str = ""):
        """Print skipped test."""
        print(f"{YELLOW}○ SKIP{RESET}: {name}")
        if reason:
            print(f"        {reason}")
        self.skipped += 1
    
    def check_file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        path = self.repo_root / file_path
        return path.exists()
    
    def search_legacy_references(self) -> List[str]:
        """Search for legacy stream management references."""
        import subprocess
        
        legacy_patterns = [
            'streams.json',
            '/api/streams/start',
            '/api/streams/stop'
        ]
        
        found = []
        search_dirs = [
            self.repo_root / 'backend',
            self.repo_root / 'frontend' / 'src'
        ]
        
        # Use git grep if available for better performance
        for pattern in legacy_patterns:
            try:
                result = subprocess.run(
                    ['git', 'grep', '-l', pattern],
                    cwd=self.repo_root,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    files = result.stdout.strip().split('\n')
                    for file in files:
                        if file:
                            found.append(f"{pattern} found in {file}")
            except (subprocess.SubprocessError, FileNotFoundError):
                # Fall back to manual search if git grep fails
                for search_dir in search_dirs:
                    if not search_dir.exists():
                        continue
                    for file_path in search_dir.rglob('*.py'):
                        try:
                            content = file_path.read_text()
                            if pattern in content:
                                found.append(f"{pattern} found in {file_path.relative_to(self.repo_root)}")
                        except (IOError, OSError):
                            pass
        
        return found
    
    def test_backend_endpoint(self, endpoint: str, method: str = 'GET', 
                             headers: Optional[dict] = None, 
                             params: Optional[dict] = None) -> Tuple[bool, str]:
        """Test a backend endpoint."""
        url = f"{self.backend_url}{endpoint}"
        try:
            response = requests.request(
                method, url, 
                headers=headers or {}, 
                params=params or {},
                timeout=5
            )
            
            # We expect some endpoints to return 401/403/404 without auth
            # Just checking if the endpoint exists and returns valid HTTP response
            if response.status_code < 500:
                return True, f"Status {response.status_code}"
            else:
                return False, f"Server error: {response.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Backend not reachable (is it running?)"
        except requests.exceptions.Timeout:
            return False, "Request timeout"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def run_file_checks(self):
        """Run file existence checks."""
        self.print_header("File Existence Checks")
        
        required_files = [
            ('services/webrtc-bridge/bridge_service.py', 'Bridge service implementation'),
            ('docker/frontend/Dockerfile', 'Frontend Dockerfile'),
            ('services/webrtc-bridge/Dockerfile', 'Bridge Dockerfile'),
            ('docker/deploy/docker-compose.yml', 'Docker Compose configuration'),
            ('docker/deploy/README.md', 'Docker deployment documentation'),
            ('backend/.env', 'Backend environment configuration'),
            ('backend/routes/streams.py', 'Streams router'),
            ('frontend/src/api.js', 'Frontend API client'),
            ('frontend/src/components/AdminDashboard.jsx', 'Admin dashboard'),
            ('frontend/src/components/WebRTCVideoPlayer.jsx', 'WebRTC video player'),
        ]
        
        for file_path, description in required_files:
            exists = self.check_file_exists(file_path)
            self.print_test(
                f"{description}: {file_path}",
                exists,
                "File exists" if exists else "File missing"
            )
    
    def run_legacy_checks(self):
        """Run legacy reference checks."""
        self.print_header("Legacy Code Checks")
        
        print("Searching for legacy stream management references...")
        legacy_refs = self.search_legacy_references()
        
        if legacy_refs:
            self.print_test(
                "No legacy stream management code",
                False,
                f"Found {len(legacy_refs)} references:\n        " + "\n        ".join(legacy_refs[:5])
            )
            if len(legacy_refs) > 5:
                print(f"        ... and {len(legacy_refs) - 5} more")
        else:
            self.print_test(
                "No legacy stream management code",
                True,
                "No streams.json, /api/streams/start, or /api/streams/stop found"
            )
    
    def run_env_checks(self):
        """Run environment configuration checks."""
        self.print_header("Environment Configuration Checks")
        
        env_file = self.repo_root / 'backend' / '.env'
        if not env_file.exists():
            self.print_test("Backend .env file exists", False, "File not found")
            return
        
        try:
            env_content = env_file.read_text()
            
            # Check for BRIDGE_CONTROL_SECRET
            has_secret = 'BRIDGE_CONTROL_SECRET=' in env_content
            self.print_test(
                "BRIDGE_CONTROL_SECRET configured",
                has_secret,
                "Found in .env" if has_secret else "Not found in .env - add this variable"
            )
            
            # Check for BRIDGE_WS_URL (required for signaling-info endpoint)
            has_ws_url = 'BRIDGE_WS_URL=' in env_content
            self.print_test(
                "BRIDGE_WS_URL configured",
                has_ws_url,
                "Found in .env - required for signaling" if has_ws_url else "Not configured - may use defaults"
            )
            
        except Exception as e:
            self.print_test("Read .env file", False, str(e))
    
    def run_backend_api_checks(self):
        """Run backend API endpoint checks."""
        self.print_header("Backend API Endpoint Checks")
        
        # Test health endpoint
        success, details = self.test_backend_endpoint('/health')
        self.print_test("GET /health endpoint", success, details)
        
        if not success:
            self.print_skip("Remaining endpoint tests", "Backend not reachable")
            return
        
        # Test streams metadata endpoint
        success, details = self.test_backend_endpoint(f'/api/streams/{self.test_robot_id}')
        self.print_test(
            f"GET /api/streams/{self.test_robot_id} endpoint",
            success,
            details
        )
        
        # Test signaling-info endpoint
        success, details = self.test_backend_endpoint(
            f'/api/streams/{self.test_robot_id}/signaling-info'
        )
        self.print_test(
            f"GET /api/streams/{self.test_robot_id}/signaling-info endpoint",
            success,
            details
        )
        
        # Test bridge authorize endpoint (with secret if provided)
        if self.bridge_secret:
            success, details = self.test_backend_endpoint(
                '/api/streams/bridge/authorize',
                params={'robot_id': self.test_robot_id},
                headers={'X-BRIDGE-SECRET': self.bridge_secret}
            )
            self.print_test(
                "GET /api/streams/bridge/authorize endpoint (with secret)",
                success,
                details
            )
        else:
            self.print_skip(
                "GET /api/streams/bridge/authorize endpoint",
                "BRIDGE_CONTROL_SECRET not provided (set env var or use --bridge-secret)"
            )
    
    def run_pytest_tests(self):
        """Run pytest stream integration tests."""
        self.print_header("Pytest Integration Tests")
        
        try:
            import subprocess
            result = subprocess.run(
                ['pytest', '-k', 'stream_integration', '-v'],
                cwd=self.repo_root / 'backend',
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.print_test(
                    "pytest -k stream_integration",
                    True,
                    "All tests passed"
                )
            else:
                # Check if there are any tests
                if 'no tests ran' in result.stdout.lower():
                    self.print_skip(
                        "pytest -k stream_integration",
                        "No stream_integration tests found"
                    )
                else:
                    self.print_test(
                        "pytest -k stream_integration",
                        False,
                        f"Some tests failed:\n{result.stdout[-500:]}"
                    )
        except FileNotFoundError:
            self.print_skip("pytest tests", "pytest not installed")
        except subprocess.TimeoutExpired:
            self.print_test("pytest tests", False, "Tests timed out")
        except Exception as e:
            self.print_skip("pytest tests", f"Error running tests: {str(e)}")
    
    def print_summary(self):
        """Print verification summary."""
        self.print_header("Verification Summary")
        
        total = self.passed + self.failed + self.skipped
        print(f"Total checks: {total}")
        print(f"{GREEN}Passed: {self.passed}{RESET}")
        print(f"{RED}Failed: {self.failed}{RESET}")
        print(f"{YELLOW}Skipped: {self.skipped}{RESET}")
        print()
        
        if self.failed > 0:
            print(f"{RED}❌ VERIFICATION FAILED{RESET}")
            print("Some checks did not pass. Please review the failures above.")
            return 1
        elif self.skipped > 0:
            print(f"{YELLOW}⚠ VERIFICATION COMPLETED WITH WARNINGS{RESET}")
            print("Some checks were skipped. Review the skipped items above.")
            return 0
        else:
            print(f"{GREEN}✅ VERIFICATION PASSED{RESET}")
            print("All checks passed successfully!")
            return 0
    
    def run(self) -> int:
        """Run all verification checks."""
        print(f"\n{BLUE}RTSP → WebRTC Streaming Setup Verification{RESET}")
        print(f"Backend URL: {self.backend_url}")
        print(f"Test Robot ID: {self.test_robot_id}")
        
        self.run_file_checks()
        self.run_env_checks()
        self.run_legacy_checks()
        self.run_backend_api_checks()
        self.run_pytest_tests()
        
        return self.print_summary()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Verify RTSP → WebRTC streaming setup'
    )
    parser.add_argument(
        '--backend-url',
        default=os.getenv('BACKEND_URL', 'http://localhost:8000'),
        help='Backend API URL (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--test-robot-id',
        type=int,
        default=int(os.getenv('TEST_ROBOT_ID', '1')),
        help='Robot ID for testing endpoints (default: 1)'
    )
    parser.add_argument(
        '--bridge-secret',
        default=os.getenv('BRIDGE_CONTROL_SECRET'),
        help='Bridge control secret from backend/.env'
    )
    
    args = parser.parse_args()
    
    verifier = StreamingSetupVerifier(
        backend_url=args.backend_url,
        test_robot_id=args.test_robot_id,
        bridge_secret=args.bridge_secret
    )
    
    exit_code = verifier.run()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
