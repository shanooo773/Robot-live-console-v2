import os
import subprocess
import json
import logging
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class TheiaContainerManager:
    """Manages Eclipse Theia containers for users"""
    
    def __init__(self, base_port: int = 3001):
        self.base_port = base_port
        self.theia_dir = Path(__file__).parent.parent.parent / "theia"
        self.projects_dir = Path(__file__).parent.parent.parent / "projects"
        self.container_prefix = "theia-user-"
        
        # Ensure directories exist
        self.projects_dir.mkdir(exist_ok=True)
        
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
            container_name = self.get_container_name(user_id)
            result = subprocess.run(
                ["docker", "ps", "-q", "-f", f"name={container_name}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return bool(result.stdout.strip())
        except Exception as e:
            logger.error(f"Error checking container status for user {user_id}: {e}")
            return False
    
    def get_container_status(self, user_id: int) -> Dict:
        """Get detailed status of user's container"""
        try:
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
            
        except Exception as e:
            logger.error(f"Error getting container status for user {user_id}: {e}")
            return {"status": "error", "error": str(e)}
    
    def start_container(self, user_id: int) -> Dict:
        """Start Theia container for user"""
        try:
            # Ensure project directory exists
            if not self.ensure_user_project_dir(user_id):
                return {"success": False, "error": "Failed to create project directory"}
            
            container_name = self.get_container_name(user_id)
            port = self.get_user_port(user_id)
            project_dir = self.get_user_project_dir(user_id)
            
            # Stop existing container if running
            self.stop_container(user_id)
            
            # Build Theia image if it doesn't exist
            build_result = subprocess.run(
                ["docker", "build", "-t", "robot-console-theia:latest", "."],
                cwd=self.theia_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if build_result.returncode != 0:
                logger.error(f"Failed to build Theia image: {build_result.stderr}")
                # Try to continue with existing image
            
            # Create network if it doesn't exist
            subprocess.run(
                ["docker", "network", "create", "robot-console-network"],
                capture_output=True,
                timeout=10
            )
            
            # Start container
            cmd = [
                "docker", "run", "-d",
                "--name", container_name,
                "--network", "robot-console-network",
                "-p", f"{port}:3000",
                "-v", f"{project_dir.absolute()}:/home/project",
                "--restart", "unless-stopped",
                "robot-console-theia:latest"
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
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            logger.error(f"Error starting container for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
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