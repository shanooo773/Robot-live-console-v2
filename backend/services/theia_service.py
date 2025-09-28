import os
import subprocess
import json
import logging
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

class TheiaContainerManager:
    """Manages Eclipse Theia containers for users"""
    
    def __init__(self, base_port: int = None, db_manager=None):
        # Database manager for port persistence
        self.db_manager = db_manager
        
        # Get configuration from environment
        # Use 4000-9000 range as specified in requirements
        self.base_port = base_port or int(os.getenv('THEIA_BASE_PORT', 4000))
        self.max_port = int(os.getenv('THEIA_MAX_PORT', 9000))
        self.max_containers = int(os.getenv('THEIA_MAX_CONTAINERS', 50))
        self.theia_image = os.getenv('THEIA_IMAGE', 'theiaide/theia:latest')  # Use official image as per requirement
        self.docker_network = os.getenv('DOCKER_NETWORK', 'robot-console-network')
        
        # Container lifecycle configuration
        self.idle_timeout_hours = int(os.getenv('THEIA_IDLE_TIMEOUT_HOURS', 2))  # 2 hours idle timeout
        self.logout_grace_period_minutes = int(os.getenv('THEIA_LOGOUT_GRACE_MINUTES', 5))  # 5 minutes grace period
        
        # Port mapping storage (userid → port) - now backed by database
        self._port_mappings = {}
        
        # Container activity tracking (userid → last_activity_timestamp)
        self._last_activity = {}
        
        # Paths
        project_path = os.getenv('THEIA_PROJECT_PATH', './projects')  # Default to local for development
        self.theia_dir = Path(__file__).parent.parent.parent / "theia"
        
        # Handle absolute vs relative paths
        if project_path.startswith('/'):
            self.projects_dir = Path(project_path)
        else:
            self.projects_dir = Path(__file__).parent.parent.parent / project_path.lstrip('./')
            
        self.container_prefix = "theia-"  # Changed to match problem statement format
        
        # Ensure directories exist
        try:
            self.projects_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            logger.error(f"Permission denied creating directory {self.projects_dir}. Using fallback.")
            # Fallback to local directory if can't create the configured path
            self.projects_dir = Path(__file__).parent.parent.parent / "projects"
            self.projects_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing port mappings from database on startup
        self._load_port_mappings_from_db()
        
        # Ensure demo user directories exist
        self._ensure_demo_user_directories()
        
    def _load_port_mappings_from_db(self):
        """Load existing port mappings from database on startup"""
        if not self.db_manager:
            logger.warning("No database manager available for port persistence")
            return
            
        try:
            assigned_ports = self.db_manager.get_all_assigned_ports()
            logger.info(f"Loaded {len(assigned_ports)} port assignments from database")
            
            # We don't load the full mapping here because we need to verify ports are still available
            # The get_user_port method will check database first and validate availability
            
        except Exception as e:
            logger.error(f"Failed to load port mappings from database: {e}")
    
    def _ensure_demo_user_directories(self):
        """Ensure demo user directories exist with welcome files"""
        demo_users = [-1, -2]  # Demo user and demo admin IDs from auth service
        
        for user_id in demo_users:
            self.ensure_user_project_dir(user_id)
    
    def get_user_port(self, user_id: int) -> int:
        """Get dynamic port for user's Theia container (4000-9000 range) with database persistence"""
        import socket
        
        # First check database for existing port assignment
        if self.db_manager:
            try:
                existing_port = self.db_manager.get_user_theia_port(user_id)
                if existing_port:
                    # Verify the port is still available
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        try:
                            s.bind(('0.0.0.0', existing_port))  # Use 0.0.0.0 to bind all interfaces
                            s.close()
                            # Port is available, update cache and return
                            self._port_mappings[user_id] = existing_port
                            logger.info(f"Reusing port {existing_port} for user {user_id} from database")
                            return existing_port
                        except OSError:
                            # Port is in use, clear from database and find a new one
                            logger.warning(f"Port {existing_port} for user {user_id} is no longer available, finding new port")
                            self.db_manager.clear_user_theia_port(user_id)
                            if user_id in self._port_mappings:
                                del self._port_mappings[user_id]
            except Exception as e:
                logger.error(f"Error checking database port for user {user_id}: {e}")
        
        # Check if user already has a port assigned in memory cache
        if user_id in self._port_mappings:
            # Verify the port is still available
            port = self._port_mappings[user_id]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('0.0.0.0', port))
                    s.close()
                    return port
                except OSError:
                    # Port is in use, remove from mapping and find a new one
                    del self._port_mappings[user_id]
        
        # Get all assigned ports from database to avoid conflicts
        assigned_ports = set()
        if self.db_manager:
            try:
                assigned_ports = set(self.db_manager.get_all_assigned_ports())
            except Exception as e:
                logger.error(f"Error getting assigned ports from database: {e}")
        
        # Also add ports from memory cache
        assigned_ports.update(self._port_mappings.values())
        
        # Find an available port in the 4000-9000 range
        for port in range(self.base_port, self.max_port + 1):
            # Skip ports already assigned to other users
            if port in assigned_ports:
                continue
                
            # Check if port is available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('0.0.0.0', port))
                    s.close()
                    # Store the mapping in both memory and database
                    self._port_mappings[user_id] = port
                    if self.db_manager:
                        try:
                            self.db_manager.set_user_theia_port(user_id, port)
                            logger.info(f"Assigned port {port} to user {user_id} and saved to database")
                        except Exception as e:
                            logger.error(f"Failed to save port assignment to database: {e}")
                            # Continue with memory-only assignment
                            logger.info(f"Assigned port {port} to user {user_id} (memory only)")
                    else:
                        logger.info(f"Assigned port {port} to user {user_id} (no database available)")
                    return port
                except OSError:
                    continue
        
        # Fallback if no port found in range
        raise Exception(f"No available ports in range {self.base_port}-{self.max_port}")
    
    def ensure_user_port_assigned(self, user_id: int) -> bool:
        """Ensure user has a theia_port assigned in database (doesn't need to be available right now)"""
        if not self.db_manager:
            logger.warning(f"No database manager available to assign port for user {user_id}")
            return False
            
        try:
            # Check if user already has a port in database
            existing_port = self.db_manager.get_user_theia_port(user_id)
            if existing_port:
                logger.info(f"User {user_id} already has theia_port assigned: {existing_port}")
                return True
            
            # User doesn't have a port, assign one
            logger.info(f"Assigning new theia_port for user {user_id}")
            port = self.get_user_port(user_id)  # This will find and assign a port
            logger.info(f"✅ Successfully assigned theia_port {port} to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to ensure port assignment for user {user_id}: {e}")
            return False
    
    def release_user_port(self, user_id: int) -> None:
        """Release port mapping when container is stopped"""
        if user_id in self._port_mappings:
            port = self._port_mappings.pop(user_id)
            logger.info(f"Released port {port} for user {user_id}")
            
            # Also clear from database
            if self.db_manager:
                try:
                    self.db_manager.clear_user_theia_port(user_id)
                    logger.info(f"Cleared port assignment for user {user_id} from database")
                except Exception as e:
                    logger.error(f"Failed to clear port assignment from database: {e}")
    
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
            
            # Check if container exists and get its port
            result = subprocess.run(
                ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Ports}}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if not result.stdout.strip():
                return {"status": "not_created", "url": None, "port": None}
            
            # Check if container is running
            is_running_result = subprocess.run(
                ["docker", "ps", "-q", "-f", f"name={container_name}"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            is_running = bool(is_running_result.stdout.strip())
            
            # Extract port from docker ps output (format: 0.0.0.0:4000->3000/tcp)
            port = None
            if is_running and result.stdout.strip():
                port_mapping = result.stdout.strip()
                if "->" in port_mapping:
                    try:
                        # Extract host port from mapping like "0.0.0.0:4000->3000/tcp"
                        host_part = port_mapping.split("->")[0]
                        port = int(host_part.split(":")[-1])
                        # Update our port mapping cache
                        self._port_mappings[user_id] = port
                    except (ValueError, IndexError):
                        logger.warning(f"Could not parse port mapping: {port_mapping}")
            
            # If we couldn't get port from docker ps, try the cached mapping
            if not port and user_id in self._port_mappings:
                port = self._port_mappings[user_id]
            
            # Get server host from environment or use localhost
            server_host = os.getenv('SERVER_HOST', '172.232.105.47')
            
            return {
                "status": "running" if is_running else "stopped",
                "url": f"http://172.232.105.47:{port}" if is_running and port else None,
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
            
            # Pull the prebuilt Theia image if not available locally
            try:
                # Check if image exists locally
                image_check = subprocess.run(
                    ["docker", "images", "-q", self.theia_image],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if not image_check.stdout.strip():
                    logger.info(f"Pulling {self.theia_image} image...")
                    pull_result = subprocess.run(
                        ["docker", "pull", self.theia_image],
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    
                    if pull_result.returncode != 0:
                        logger.error(f"Failed to pull {self.theia_image}: {pull_result.stderr}")
                        return {
                            "success": False, 
                            "error": f"Failed to pull Theia image {self.theia_image}. Please check internet connection."
                        }
                    
            except subprocess.TimeoutExpired:
                logger.warning("Docker pull timed out, will try to use existing image")
                return {
                    "success": False,
                    "error": "Docker pull operation timed out. Please try again."
                }
            
            # Create network if it doesn't exist
            try:
                subprocess.run(
                    ["docker", "network", "create", self.docker_network],
                    capture_output=True,
                    timeout=10
                )
            except subprocess.TimeoutExpired:
                logger.warning("Docker network creation timed out")
            
            # Start container using the exact command format from requirements
            # docker run -d --name theia-${USERID} -p ${ASSIGNED_PORT}:3000 -v /data/users/${USERID}:/home/project theiaide/theia:latest
            cmd = [
                "docker", "run", "-d",
                "--name", container_name,
                "-p", f"{port}:3000",
                "-v", f"{project_dir.absolute()}:/home/project",
                self.theia_image
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Get server host from environment or use localhost  
                server_host = os.getenv('SERVER_HOST', '172.232.105.47')
                
                return {
                    "success": True,
                    "status": "running",
                    "url": f"http://{server_host}:{port}",
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
            
            # Remove container to free VPS resources
            subprocess.run(
                ["docker", "rm", container_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Release port mapping
            self.release_user_port(user_id)
            
            logger.info(f"Container {container_name} stopped and removed for user {user_id}")
            return {"success": True, "status": "stopped"}
            
        except Exception as e:
            logger.error(f"Error stopping container for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def restart_container(self, user_id: int) -> Dict:
        """Restart user's Theia container with better error handling for crashed containers"""
        try:
            container_name = self.get_container_name(user_id)
            
            # First, try to stop the container gracefully
            stop_result = self.stop_container(user_id)
            
            # If stop failed, force remove the container to handle crashed state
            if not stop_result.get("success"):
                logger.warning(f"Graceful stop failed for user {user_id}, forcing container removal")
                try:
                    # Force remove the container (handles crashed/stuck containers)
                    subprocess.run(
                        ["docker", "rm", "-f", container_name],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    # Release port mapping after force removal
                    self.release_user_port(user_id)
                    logger.info(f"Force removed crashed container {container_name} for user {user_id}")
                except Exception as force_error:
                    logger.error(f"Failed to force remove container for user {user_id}: {force_error}")
            
            # Start the container
            return self.start_container(user_id)
        except Exception as e:
            logger.error(f"Error restarting container for user {user_id}: {e}")
            return {"success": False, "error": f"Restart failed: {str(e)}"}
    
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
    
    def cleanup_stale_containers(self) -> Dict:
        """Clean up stale containers that should not be running"""
        try:
            containers = self.list_user_containers()
            stale_containers = []
            cleaned_count = 0
            
            for container in containers:
                # A container is considered stale if it's been stopped but not removed
                if "Exited" in container["status"]:
                    try:
                        user_id = int(container["user_id"])
                        result = self.stop_container(user_id)  # This will remove the container
                        if result.get("success"):
                            cleaned_count += 1
                        stale_containers.append({
                            "user_id": user_id,
                            "container_name": container["container_name"],
                            "status": "cleaned" if result.get("success") else "failed"
                        })
                    except ValueError:
                        # Skip if user_id is not a valid integer
                        continue
            
            logger.info(f"Cleanup completed: {cleaned_count} stale containers removed")
            return {
                "success": True,
                "cleaned_count": cleaned_count,
                "containers": stale_containers
            }
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return {"success": False, "error": str(e)}
    
    def stop_all_user_containers(self) -> Dict:
        """Stop all running user containers (admin function)"""
        try:
            containers = self.list_user_containers()
            stopped_count = 0
            results = []
            
            for container in containers:
                if "Up" in container["status"]:  # Only stop running containers
                    try:
                        user_id = int(container["user_id"])
                        result = self.stop_container(user_id)
                        if result.get("success"):
                            stopped_count += 1
                        results.append({
                            "user_id": user_id,
                            "container_name": container["container_name"],
                            "status": "stopped" if result.get("success") else "failed"
                        })
                    except ValueError:
                        continue
            
            logger.info(f"Stopped {stopped_count} running containers")
            return {
                "success": True,
                "stopped_count": stopped_count,
                "containers": results
            }
            
        except Exception as e:
            logger.error(f"Error stopping all containers: {e}")
            return {"success": False, "error": str(e)}
    
    def update_user_activity(self, user_id: int) -> None:
        """Update last activity timestamp for user (called when user accesses their container)"""
        import time
        self._last_activity[user_id] = time.time()
        logger.debug(f"Updated activity for user {user_id}")
    
    def schedule_logout_cleanup(self, user_id: int) -> Dict:
        """Schedule container cleanup after logout grace period"""
        try:
            import threading
            import time
            
            def delayed_cleanup():
                # Wait for grace period
                time.sleep(self.logout_grace_period_minutes * 60)
                
                # Check if user is still inactive and container exists
                container_name = self.get_container_name(user_id)
                status = self.get_container_status(user_id)
                
                if status.get("status") == "running":
                    logger.info(f"Cleaning up container for user {user_id} after logout grace period")
                    self.stop_container(user_id)
            
            # Start cleanup thread
            cleanup_thread = threading.Thread(target=delayed_cleanup)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
            logger.info(f"Scheduled cleanup for user {user_id} in {self.logout_grace_period_minutes} minutes")
            return {"success": True, "message": f"Cleanup scheduled for {self.logout_grace_period_minutes} minutes"}
            
        except Exception as e:
            logger.error(f"Error scheduling cleanup for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def cleanup_idle_containers(self) -> Dict:
        """Clean up containers that have been idle for longer than the configured timeout"""
        try:
            import time
            current_time = time.time()
            timeout_seconds = self.idle_timeout_hours * 3600
            
            containers = self.list_user_containers()
            cleaned_count = 0
            results = []
            
            for container in containers:
                if "Up" in container["status"]:  # Only check running containers
                    try:
                        user_id = int(container["user_id"])
                        last_activity = self._last_activity.get(user_id, 0)
                        
                        # If no activity recorded or idle for too long
                        if current_time - last_activity > timeout_seconds:
                            logger.info(f"Container for user {user_id} idle for {(current_time - last_activity)/3600:.1f} hours - cleaning up")
                            result = self.stop_container(user_id)
                            if result.get("success"):
                                cleaned_count += 1
                            results.append({
                                "user_id": user_id,
                                "idle_hours": (current_time - last_activity) / 3600,
                                "status": "cleaned" if result.get("success") else "failed"
                            })
                    except ValueError:
                        continue
            
            logger.info(f"Idle cleanup completed: {cleaned_count} containers cleaned")
            return {
                "success": True,
                "cleaned_count": cleaned_count,
                "containers": results
            }
            
        except Exception as e:
            logger.error(f"Error during idle cleanup: {e}")
            return {"success": False, "error": str(e)}
