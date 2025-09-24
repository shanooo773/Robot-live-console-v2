import os
import subprocess
import json
import logging
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class TheiaContainerManager:
    """Manages Eclipse Theia containers for users"""
    
    def __init__(self, base_port: int = None):
        # Get configuration from environment
        self.base_port = base_port or int(os.getenv('THEIA_BASE_PORT', 3001))
        self.max_containers = int(os.getenv('THEIA_MAX_CONTAINERS', 50))
        self.theia_image = os.getenv('THEIA_IMAGE', 'robot-console-theia:latest')
        self.docker_network = os.getenv('DOCKER_NETWORK', 'robot-console-network')
        
        # Paths
        project_path = os.getenv('THEIA_PROJECT_PATH', './projects')
        self.theia_dir = Path(__file__).parent.parent.parent / "theia"
        self.projects_dir = Path(__file__).parent.parent.parent / project_path.lstrip('./')
        self.container_prefix = "theia-user-"
        
        # Ensure directories exist
        self.projects_dir.mkdir(exist_ok=True)
        
        # Ensure demo user directories exist
        self._ensure_demo_user_directories()
        
    def _ensure_demo_user_directories(self):
        """Ensure demo user directories exist with welcome files"""
        demo_users = [-1, -2]  # Demo user and demo admin IDs from auth service
        
        for user_id in demo_users:
            self.ensure_user_project_dir(user_id)
    
    def get_user_port(self, user_id: int) -> int:
        """Get unique port for user's Theia container"""
        return self.base_port + (user_id % 1000)
    
    def get_container_name(self, user_id: int) -> str:
        """Get container name for user"""
        return f"{self.container_prefix}{user_id}"
    
    def get_user_project_dir(self, user_id: int) -> Path:
        """Get project directory path for user"""
        return self.projects_dir / str(user_id)
    
    def ensure_user_project_dir(self, user_id: int) -> bool:
        """Create user project directory if it doesn't exist"""
        try:
            project_dir = self.get_user_project_dir(user_id)
            project_dir.mkdir(exist_ok=True)
            
            # Create welcome files for new users
            welcome_py = project_dir / "welcome.py"
            if not welcome_py.exists():
                welcome_py.write_text('''#!/usr/bin/env python3
"""
Welcome to your Robot Console workspace!

This is your personal development environment for robot programming.
Your work is automatically saved and will persist between sessions.
"""

def main():
    print("Welcome to Robot Console!")
    print("Your development environment is ready.")
    
    # Example robot code snippet
    robot_position = {"x": 0, "y": 0, "angle": 0}
    print(f"Robot position: {robot_position}")
    
    # TODO: Add your robot control code here

if __name__ == "__main__":
    main()
''')
            
            # Create example C++ file
            example_cpp = project_dir / "robot_example.cpp"
            if not example_cpp.exists():
                example_cpp.write_text('''#include <iostream>
#include <cmath>

class Robot {
public:
    double x, y, angle;
    
    Robot(double x = 0, double y = 0, double angle = 0) 
        : x(x), y(y), angle(angle) {}
    
    void move(double distance) {
        x += distance * std::cos(angle);
        y += distance * std::sin(angle);
        std::cout << "Robot moved to (" << x << ", " << y << ")" << std::endl;
    }
    
    void rotate(double angle_change) {
        angle += angle_change;
        std::cout << "Robot rotated to " << angle << " radians" << std::endl;
    }
};

int main() {
    std::cout << "Robot C++ Example" << std::endl;
    Robot robot(0, 0, 0);
    robot.move(1.0);
    robot.rotate(0.5);
    return 0;
}
''')
            
            return True
        except Exception as e:
            logger.error(f"Failed to create project directory for user {user_id}: {e}")
            return False
    
    def is_container_running(self, user_id: int) -> bool:
        """Check if user's Theia container is running"""
        try:
            # First check if Docker is available
            docker_check = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if docker_check.returncode != 0:
                logger.warning("Docker is not available or not running")
                return False
                
            container_name = self.get_container_name(user_id)
            result = subprocess.run(
                ["docker", "ps", "-q", "-f", f"name={container_name}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return bool(result.stdout.strip())
        except subprocess.TimeoutExpired:
            logger.warning(f"Docker command timed out when checking container for user {user_id}")
            return False
        except FileNotFoundError:
            logger.warning("Docker command not found - Docker may not be installed")
            return False
        except Exception as e:
            logger.error(f"Error checking container status for user {user_id}: {e}")
            return False
    
    def get_container_status(self, user_id: int) -> Dict:
        """Get detailed status of user's container"""
        try:
            # First check if Docker is available
            docker_check = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if docker_check.returncode != 0:
                return {
                    "status": "docker_unavailable", 
                    "error": "Docker service is not available",
                    "url": None, 
                    "port": None
                }
                
            container_name = self.get_container_name(user_id)
            
            # Check if container exists
            result = subprocess.run(
                ["docker", "ps", "-a", "-q", "-f", f"name={container_name}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if not result.stdout.strip():
                return {"status": "not_created", "url": None, "port": None}
            
            # Check if container is running
            result = subprocess.run(
                ["docker", "ps", "-q", "-f", f"name={container_name}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            is_running = bool(result.stdout.strip())
            port = self.get_user_port(user_id)
            
            return {
                "status": "running" if is_running else "stopped",
                "url": f"http://localhost:{port}" if is_running else None,
                "port": port if is_running else None,
                "container_name": container_name
            }
            
        except subprocess.TimeoutExpired:
            logger.warning(f"Docker command timed out when getting status for user {user_id}")
            return {
                "status": "docker_timeout", 
                "error": "Docker service timeout - may be under heavy load",
                "url": None, 
                "port": None
            }
        except FileNotFoundError:
            logger.warning("Docker command not found - Docker may not be installed")
            return {
                "status": "docker_not_found", 
                "error": "Docker is not installed or not in PATH",
                "url": None, 
                "port": None
            }
        except Exception as e:
            logger.error(f"Error getting container status for user {user_id}: {e}")
            return {"status": "error", "error": str(e)}
    
    def start_container(self, user_id: int) -> Dict:
        """Start Theia container for user"""
        try:
            # First check if Docker is available
            docker_check = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if docker_check.returncode != 0:
                return {
                    "success": False, 
                    "error": "Docker service is not available. Please ensure Docker is installed and running."
                }
            
            # Ensure project directory exists
            if not self.ensure_user_project_dir(user_id):
                return {"success": False, "error": "Failed to create project directory"}
            
            container_name = self.get_container_name(user_id)
            port = self.get_user_port(user_id)
            project_dir = self.get_user_project_dir(user_id)
            
            # Stop existing container if running
            self.stop_container(user_id)
            
            # Build Theia image if it doesn't exist
            try:
                build_result = subprocess.run(
                    ["docker", "build", "-t", "robot-console-theia:latest", "."],
                    cwd=self.theia_dir,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if build_result.returncode != 0:
                    logger.warning(f"Failed to build Theia image, trying to use existing: {build_result.stderr}")
                    # Check if image exists
                    image_check = subprocess.run(
                        ["docker", "images", "-q", "robot-console-theia:latest"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if not image_check.stdout.strip():
                        return {
                            "success": False, 
                            "error": "Theia Docker image not available and failed to build. Please build manually."
                        }
            except subprocess.TimeoutExpired:
                logger.warning("Docker build timed out, will try to use existing image")
            
            # Create network if it doesn't exist
            try:
                subprocess.run(
                    ["docker", "network", "create", self.docker_network],
                    capture_output=True,
                    timeout=10
                )
            except subprocess.TimeoutExpired:
                logger.warning("Docker network creation timed out")
            
            # Start container
            cmd = [
                "docker", "run", "-d",
                "--name", container_name,
                "--network", self.docker_network,
                "-p", f"{port}:3000",
                "-v", f"{project_dir.absolute()}:/home/project",
                "--restart", "unless-stopped",
                self.theia_image
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "status": "running",
                    "url": f"http://localhost:{port}",
                    "port": port,
                    "container_name": container_name
                }
            else:
                logger.error(f"Failed to start container for user {user_id}: {result.stderr}")
                return {"success": False, "error": f"Failed to start Theia container: {result.stderr}"}
                
        except subprocess.TimeoutExpired:
            logger.error(f"Docker command timed out when starting container for user {user_id}")
            return {"success": False, "error": "Docker operation timed out. Service may be under heavy load."}
        except FileNotFoundError:
            logger.error("Docker command not found when starting container")
            return {"success": False, "error": "Docker is not installed or not in PATH"}
        except Exception as e:
            logger.error(f"Error starting container for user {user_id}: {e}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
    
    def stop_container(self, user_id: int) -> Dict:
        """Stop user's Theia container"""
        try:
            container_name = self.get_container_name(user_id)
            
            # Stop container
            result = subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Remove container
            subprocess.run(
                ["docker", "rm", container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {"success": True, "status": "stopped"}
            
        except Exception as e:
            logger.error(f"Error stopping container for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def restart_container(self, user_id: int) -> Dict:
        """Restart user's Theia container"""
        self.stop_container(user_id)
        return self.start_container(user_id)
    
    def list_user_containers(self) -> List[Dict]:
        """List all user containers"""
        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={self.container_prefix}", "--format", "table {{.Names}}\\t{{.Status}}\\t{{.Ports}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            containers = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        name = parts[0]
                        status = parts[1]
                        ports = parts[2] if len(parts) > 2 else ""
                        
                        # Extract user ID from container name
                        if name.startswith(self.container_prefix):
                            user_id = name[len(self.container_prefix):]
                            containers.append({
                                "user_id": user_id,
                                "container_name": name,
                                "status": status,
                                "ports": ports
                            })
            
            return containers
            
        except Exception as e:
            logger.error(f"Error listing containers: {e}")
            return []