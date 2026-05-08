import os
import http.client
import socket
import subprocess
import json
import logging
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Default images that are always permitted.  Administrators may expand this
# list at deployment time via the ALLOWED_SURVEILLANCE_IMAGES environment
# variable (comma-separated image names).
_DEFAULT_ALLOWED_IMAGES = [
    "elswork/theia",
    "muneeb/theia-ros-humble:v2",
    "hiwonder/theia-ros-humble:v1",
]


def _build_allowed_images() -> List[str]:
    """Return the de-duplicated allowlist of permitted surveillance images."""
    extra_raw = os.getenv("ALLOWED_SURVEILLANCE_IMAGES", "")
    extra = [img.strip() for img in extra_raw.split(",") if img.strip()]
    seen: Dict[str, bool] = {}
    result = []
    for img in _DEFAULT_ALLOWED_IMAGES + extra:
        if img not in seen:
            seen[img] = True
            result.append(img)
    return result


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
        self.theia_image = os.getenv('THEIA_IMAGE', 'elswork/theia')  # Preview mode image
        self.default_theia_image = os.getenv('DEFAULT_THEIA_IMAGE')
        self.theia_booking_image = os.getenv('THEIA_BOOKING_IMAGE')
        self.docker_network = os.getenv('DOCKER_NETWORK', 'robot-console-network')

        # Allowed base images for admin-configurable surveillance
        self.allowed_images = _build_allowed_images()
        
        # Container lifecycle configuration
        self.idle_timeout_hours = int(os.getenv('THEIA_IDLE_TIMEOUT_HOURS', 1))  # 1 hour idle timeout
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
            
        self.container_prefix = "theia-"
        self.preview_container_prefix = "theia-preview-"
        self.booking_container_prefix = "theia-booking-"
        
        # Booking port mapping storage (userid → port) - separate from preview ports
        self._booking_port_mappings = {}
        
        # Admin watch port mapping storage (admin_id → port)
        self._admin_watch_port_mappings = {}
        
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

    def get_allowed_images(self) -> List[str]:
        """Return the allowlist of permitted surveillance base images."""
        return list(self.allowed_images)

    def is_image_allowed(self, image: str) -> bool:
        """Return True if *image* is on the allowlist."""
        return image.strip() in self.allowed_images

    def get_default_surveillance_image(self) -> str:
        """Return the first image in the allowlist (safe fallback)."""
        return self.allowed_images[0]

    def _resolve_image_to_use(self, image_override: Optional[str]) -> str:
        """Normalize an override and return the selected image with fallbacks."""
        if isinstance(image_override, str):
            stripped = image_override.strip()
            normalized_image_override = stripped if stripped else None
        else:
            normalized_image_override = image_override or None
        return (
            normalized_image_override
            or self.default_theia_image
            or self.theia_booking_image
            or self.theia_image
        )

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
                            s.bind(('127.0.0.1', existing_port))
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
                    s.bind(('127.0.0.1', port))
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
                    s.bind(('127.0.0.1', port))
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
        """Release preview port mapping when container is stopped"""
        if user_id in self._port_mappings:
            port = self._port_mappings.pop(user_id)
            logger.info(f"Released preview port {port} for user {user_id}")
            
            # Also clear from database
            if self.db_manager:
                try:
                    self.db_manager.clear_user_theia_port(user_id)
                    logger.info(f"Cleared preview port assignment for user {user_id} from database")
                except Exception as e:
                    logger.error(f"Failed to clear preview port assignment from database: {e}")
    
    def get_user_booking_port(self, user_id: int) -> int:
        """Get dynamic port for user's booking Theia container with database persistence"""
        import socket
        
        # First check database for existing booking port assignment
        if self.db_manager:
            try:
                existing_port = self.db_manager.get_user_theia_booking_port(user_id)
                if existing_port:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        try:
                            s.bind(('127.0.0.1', existing_port))
                            s.close()
                            self._booking_port_mappings[user_id] = existing_port
                            logger.info(f"Reusing booking port {existing_port} for user {user_id} from database")
                            return existing_port
                        except OSError:
                            logger.warning(f"Booking port {existing_port} for user {user_id} is no longer available, finding new port")
                            self.db_manager.clear_user_theia_booking_port(user_id)
                            if user_id in self._booking_port_mappings:
                                del self._booking_port_mappings[user_id]
            except AttributeError:
                # Database manager doesn't support booking ports yet
                logger.warning("Database manager doesn't support booking ports, using memory only")
            except Exception as e:
                logger.error(f"Error checking database booking port for user {user_id}: {e}")
        
        # Check memory cache
        if user_id in self._booking_port_mappings:
            port = self._booking_port_mappings[user_id]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('127.0.0.1', port))
                    s.close()
                    return port
                except OSError:
                    del self._booking_port_mappings[user_id]
        
        # Get all assigned ports to avoid conflicts (preview + booking)
        assigned_ports = set()
        if self.db_manager:
            try:
                assigned_ports = set(self.db_manager.get_all_assigned_ports())
            except Exception as e:
                logger.error(f"Error getting assigned ports from database: {e}")
        assigned_ports.update(self._port_mappings.values())
        assigned_ports.update(self._booking_port_mappings.values())
        
        # Find an available port in the 4000-9000 range
        for port in range(self.base_port, self.max_port + 1):
            if port in assigned_ports:
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('127.0.0.1', port))
                    s.close()
                    self._booking_port_mappings[user_id] = port
                    if self.db_manager:
                        try:
                            self.db_manager.set_user_theia_booking_port(user_id, port)
                            logger.info(f"Assigned booking port {port} to user {user_id} and saved to database")
                        except AttributeError:
                            logger.info(f"Assigned booking port {port} to user {user_id} (memory only, no DB support)")
                        except Exception as e:
                            logger.error(f"Failed to save booking port assignment to database: {e}")
                    else:
                        logger.info(f"Assigned booking port {port} to user {user_id} (no database available)")
                    return port
                except OSError:
                    continue
        
        raise Exception(f"No available ports in range {self.base_port}-{self.max_port} for booking container")
    
    def release_user_booking_port(self, user_id: int) -> None:
        """Release booking port mapping when booking container is stopped"""
        if user_id in self._booking_port_mappings:
            port = self._booking_port_mappings.pop(user_id)
            logger.info(f"Released booking port {port} for user {user_id}")
            if self.db_manager:
                try:
                    self.db_manager.clear_user_theia_booking_port(user_id)
                    logger.info(f"Cleared booking port assignment for user {user_id} from database")
                except AttributeError:
                    pass
                except Exception as e:
                    logger.error(f"Failed to clear booking port assignment from database: {e}")

    def get_admin_watch_container_name(self, admin_id: int) -> str:
        """Get admin watch container name"""
        return f"theia-admin-watch-{admin_id}"

    def get_admin_watch_port(self, admin_id: int) -> int:
        """Get or allocate a port for the admin watch container with database persistence"""
        if self.db_manager:
            try:
                existing_port = self.db_manager.get_user_theia_admin_watch_port(admin_id)
                if existing_port:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        try:
                            s.bind(('127.0.0.1', existing_port))
                            s.close()
                            self._admin_watch_port_mappings[admin_id] = existing_port
                            logger.info(f"Reusing admin watch port {existing_port} for admin {admin_id} from database")
                            return existing_port
                        except OSError:
                            logger.warning(f"Admin watch port {existing_port} for admin {admin_id} is no longer available")
                            self.db_manager.clear_user_theia_admin_watch_port(admin_id)
                            if admin_id in self._admin_watch_port_mappings:
                                del self._admin_watch_port_mappings[admin_id]
            except AttributeError:
                pass
            except Exception as e:
                logger.error(f"Error checking database admin watch port for admin {admin_id}: {e}")

        if admin_id in self._admin_watch_port_mappings:
            port = self._admin_watch_port_mappings[admin_id]
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('127.0.0.1', port))
                    s.close()
                    return port
                except OSError:
                    del self._admin_watch_port_mappings[admin_id]

        assigned_ports = set()
        if self.db_manager:
            try:
                assigned_ports = set(self.db_manager.get_all_assigned_ports())
            except Exception as e:
                logger.error(f"Error getting assigned ports for admin watch: {e}")
        assigned_ports.update(self._port_mappings.values())
        assigned_ports.update(self._booking_port_mappings.values())
        assigned_ports.update(self._admin_watch_port_mappings.values())

        for port in range(self.base_port, self.max_port + 1):
            if port in assigned_ports:
                continue
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('127.0.0.1', port))
                    s.close()
                    self._admin_watch_port_mappings[admin_id] = port
                    if self.db_manager:
                        try:
                            self.db_manager.set_user_theia_admin_watch_port(admin_id, port)
                            logger.info(f"Assigned admin watch port {port} to admin {admin_id} and saved to database")
                        except AttributeError:
                            pass
                        except Exception as e:
                            logger.error(f"Failed to save admin watch port assignment to database: {e}")
                    return port
                except OSError:
                    continue

        raise Exception(f"No available ports in range {self.base_port}-{self.max_port} for admin watch container")

    def release_admin_watch_port(self, admin_id: int) -> None:
        """Release admin watch port mapping when admin watch container is stopped"""
        if admin_id in self._admin_watch_port_mappings:
            port = self._admin_watch_port_mappings.pop(admin_id)
            logger.info(f"Released admin watch port {port} for admin {admin_id}")
        if self.db_manager:
            try:
                self.db_manager.clear_user_theia_admin_watch_port(admin_id)
            except AttributeError:
                pass
            except Exception as e:
                logger.error(f"Failed to clear admin watch port from database: {e}")

    def start_admin_watch_container(self, admin_id: int, target_project_dir: Path, image_override: Optional[str] = None) -> Dict:
        """Start/restart the admin watch container mounting the given workspace directory.
        Uses the booking image (muneeb/theia-ros-humble:v2) so the admin sees the same IDE."""
        try:
            docker_check = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
            if docker_check.returncode != 0:
                return {"success": False, "error": "Docker service is not available."}

            container_name = self.get_admin_watch_container_name(admin_id)
            port = self.get_admin_watch_port(admin_id)

            image_to_use = self._resolve_image_to_use(image_override)
            error = self._pull_image_if_needed(image_to_use)
            if error:
                return {"success": False, "error": error}

            # Stop/remove any existing admin watch container before starting a new one
            subprocess.run(["docker", "rm", "-f", container_name], capture_output=True, text=True, timeout=15)

            logger.info(
                f"Starting admin watch container {container_name} for admin {admin_id} mounting {target_project_dir} "
                f"with image {image_to_use}"
            )
            return self._run_theia_container(container_name, port, target_project_dir, image_to_use)

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Docker operation timed out."}
        except FileNotFoundError:
            return {"success": False, "error": "Docker is not installed or not in PATH"}
        except Exception as e:
            logger.error(f"Error starting admin watch container for admin {admin_id}: {e}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}

    def stop_admin_watch_container(self, admin_id: int) -> Dict:
        """Stop and remove the admin watch container"""
        try:
            container_name = self.get_admin_watch_container_name(admin_id)
            subprocess.run(["docker", "stop", container_name], capture_output=True, text=True, timeout=30)
            subprocess.run(["docker", "rm", container_name], capture_output=True, text=True, timeout=30)
            self.release_admin_watch_port(admin_id)
            logger.info(f"Admin watch container {container_name} stopped for admin {admin_id}")
            return {"success": True, "status": "stopped"}
        except Exception as e:
            logger.error(f"Error stopping admin watch container for admin {admin_id}: {e}")
            return {"success": False, "error": str(e)}

    def get_admin_watch_container_status(self, admin_id: int) -> Dict:
        """Get status of the admin watch container"""
        try:
            docker_check = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
            if docker_check.returncode != 0:
                return {"status": "docker_unavailable", "url": None, "port": None, "ready": False}
            status = self._get_single_container_status(
                admin_id, self.get_admin_watch_container_name(admin_id), self._admin_watch_port_mappings
            )
            return status
        except Exception as e:
            logger.error(f"Error getting admin watch container status for admin {admin_id}: {e}")
            return {"status": "error", "error": str(e), "url": None, "port": None, "ready": False}


    def get_container_name(self, user_id: int) -> str:
        """Get preview container name for user (backward compatibility)"""
        return f"{self.preview_container_prefix}{user_id}"
    
    def get_preview_container_name(self, user_id: int) -> str:
        """Get preview container name for user"""
        return f"{self.preview_container_prefix}{user_id}"
    
    def get_booking_container_name(self, user_id: int) -> str:
        """Get booking container name for user"""
        return f"{self.booking_container_prefix}{user_id}"
    
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
        """Check if user's preview Theia container is running"""
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
                
            container_name = self.get_preview_container_name(user_id)
            # Use docker inspect for exact name matching
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Running}}", container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 and result.stdout.strip() == "true"
        except subprocess.TimeoutExpired:
            logger.warning(f"Docker command timed out when checking container for user {user_id}")
            return False
        except FileNotFoundError:
            logger.warning("Docker command not found - Docker may not be installed")
            return False
        except Exception as e:
            logger.error(f"Error checking container status for user {user_id}: {e}")
            return False
    
    def is_theia_ready(self, port: int) -> bool:
        """Check if Theia's HTTP server is actually serving responses (not just TCP-open)."""
        conn = None
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2)
            conn.request("GET", "/")
            conn.getresponse()
            return True
        except Exception:
            return False
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass

    def _get_single_container_status(self, user_id: int, container_name: str, port_cache: dict) -> Dict:
        """Helper: get status of a single named container using exact name matching via docker inspect"""
        # Use docker inspect for exact name matching (avoids substring issues with docker ps --filter name=)
        inspect_result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Status}}\t{{.State.Running}}", container_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if inspect_result.returncode != 0:
            # Container does not exist
            return {"status": "not_created", "url": None, "port": None, "container_name": container_name, "ready": False}
        
        parts = inspect_result.stdout.strip().split("\t")
        container_state = parts[0] if parts else "unknown"
        is_running = parts[1].lower() == "true" if len(parts) > 1 else False
        
        port = None
        if is_running:
            # Get the port mapping from docker inspect
            port_result = subprocess.run(
                ["docker", "inspect", "--format",
                 "{{range $p, $conf := .NetworkSettings.Ports}}{{if $conf}}{{(index $conf 0).HostPort}}{{end}}{{end}}",
                 container_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            if port_result.returncode == 0 and port_result.stdout.strip():
                try:
                    port = int(port_result.stdout.strip())
                    port_cache[user_id] = port
                except (ValueError, IndexError):
                    logger.warning(f"Could not parse port from docker inspect for {container_name}")
        
        if not port and user_id in port_cache:
            port = port_cache[user_id]
        
        base_url = os.getenv('BASE_URL', f'https://{os.getenv("SERVER_HOST", "172.232.105.47")}')
        
        ready = is_running and port is not None and self.is_theia_ready(port)
        return {
            "status": "running" if is_running else ("stopped" if container_state in ("exited", "created") else container_state),
            "url": f"{base_url}/theia/{port}/" if is_running and port else None,
            "port": port if is_running else None,
            "container_name": container_name,
            "ready": ready
        }
    
    def get_container_status(self, user_id: int) -> Dict:
        """Get status of user's preview container (backward compatibility) and also include booking container info"""
        try:
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
            
            preview_status = self._get_single_container_status(
                user_id, self.get_preview_container_name(user_id), self._port_mappings
            )
            booking_status = self._get_single_container_status(
                user_id, self.get_booking_container_name(user_id), self._booking_port_mappings
            )
            
            # Primary status is the preview container (backward compat)
            result = dict(preview_status)
            result["preview_status"] = preview_status["status"]
            result["preview_url"] = preview_status["url"]
            result["preview_port"] = preview_status["port"]
            result["preview_ready"] = preview_status.get("ready", False)
            result["booking_status"] = booking_status["status"]
            result["booking_url"] = booking_status["url"]
            result["booking_port"] = booking_status["port"]
            result["booking_ready"] = booking_status.get("ready", False)
            return result
            
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
    
    def _pull_image_if_needed(self, image: str) -> Optional[str]:
        """Pull a Docker image if not present locally. Returns error message or None on success."""
        try:
            image_check = subprocess.run(
                ["docker", "images", "-q", image],
                capture_output=True, text=True, timeout=10
            )
            if not image_check.stdout.strip():
                logger.info(f"Pulling {image} image...")
                pull_result = subprocess.run(
                    ["docker", "pull", image],
                    capture_output=True, text=True, timeout=300
                )
                if pull_result.returncode != 0:
                    logger.error(f"Failed to pull {image}: {pull_result.stderr}")
                    return f"Failed to pull Theia image {image}. Please check internet connection."
        except subprocess.TimeoutExpired:
            return "Docker pull operation timed out. Please try again."
        return None
    
    def _run_theia_container(self, container_name: str, port: int, project_dir, image: str) -> Dict:
        """Internal: run a single Theia container. Returns start result dict."""
        # Ensure network exists
        try:
            subprocess.run(
                ["docker", "network", "create", self.docker_network],
                capture_output=True, timeout=10
            )
        except subprocess.TimeoutExpired:
            logger.warning("Docker network creation timed out")
        
        # Remove any stopped container with the same name first
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True, text=True, timeout=15
        )
        
        cmd = [
            "docker", "run", "-d",
            "--name", container_name,
            "-p", f"{port}:3000",
            "-v", f"{project_dir.absolute()}:/home/project",
            "--cap-add", "NET_ADMIN",
            "--device", "/dev/net/tun",
            "--sysctl", "net.ipv6.conf.all.disable_ipv6=0",
            image
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            base_url = os.getenv('BASE_URL', f'https://{os.getenv("SERVER_HOST", "172.232.105.47")}')
            return {
                "success": True,
                "status": "running",
                "url": f"{base_url}/theia/{port}/",
                "port": port,
                "container_name": container_name
            }
        else:
            logger.error(f"Failed to start container {container_name}: {result.stderr}")
            return {"success": False, "error": f"Failed to start Theia container: {result.stderr}"}
    
    def start_preview_container(self, user_id: int) -> Dict:
        """Start the always-on preview IDE container for user (uses preview image, theia-preview-<userid>)"""
        try:
            docker_check = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
            if docker_check.returncode != 0:
                return {"success": False, "error": "Docker service is not available. Please ensure Docker is installed and running."}
            
            if not self.ensure_user_project_dir(user_id):
                return {"success": False, "error": "Failed to create project directory"}
            
            container_name = self.get_preview_container_name(user_id)
            port = self.get_user_port(user_id)
            project_dir = self.get_user_project_dir(user_id)
            
            error = self._pull_image_if_needed(self.theia_image)
            if error:
                return {"success": False, "error": error}
            
            logger.info(f"Starting preview container {container_name} for user {user_id} using image {self.theia_image}")
            return self._run_theia_container(container_name, port, project_dir, self.theia_image)
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Docker operation timed out. Service may be under heavy load."}
        except FileNotFoundError:
            return {"success": False, "error": "Docker is not installed or not in PATH"}
        except Exception as e:
            logger.error(f"Error starting preview container for user {user_id}: {e}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
    
    def start_booking_container(self, user_id: int, image_override: Optional[str] = None) -> Dict:
        """Start the booking IDE container for user (uses booking image, theia-booking-<userid>).
        Shares the same workspace directory as the preview container."""
        try:
            docker_check = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=5)
            if docker_check.returncode != 0:
                return {"success": False, "error": "Docker service is not available. Please ensure Docker is installed and running."}
            
            if not self.ensure_user_project_dir(user_id):
                return {"success": False, "error": "Failed to create project directory"}
            
            container_name = self.get_booking_container_name(user_id)
            port = self.get_user_booking_port(user_id)
            project_dir = self.get_user_project_dir(user_id)  # Same workspace as preview
            
            image_to_use = self._resolve_image_to_use(image_override)
            error = self._pull_image_if_needed(image_to_use)
            if error:
                return {"success": False, "error": error}
            
            logger.info(f"Starting booking container {container_name} for user {user_id} using image {image_to_use}")
            return self._run_theia_container(container_name, port, project_dir, image_to_use)
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Docker operation timed out. Service may be under heavy load."}
        except FileNotFoundError:
            return {"success": False, "error": "Docker is not installed or not in PATH"}
        except Exception as e:
            logger.error(f"Error starting booking container for user {user_id}: {e}")
            return {"success": False, "error": f"Unexpected error: {str(e)}"}
    
    def start_container(self, user_id: int, booking_mode: bool = False, booking_image: Optional[str] = None) -> Dict:
        """Start Theia container(s) for user.
        
        In the dual-container workflow:
        - Always starts/ensures the preview container (always-on, elswork/theia image).
        - When booking_mode=True, also starts the booking container (muneeb/theia-ros-humble:v2 image).
        Both containers share the same user workspace directory.

        Args:
            user_id: The ID of the user.
            booking_mode: When True, additionally starts the booking container.
        """
        # Always ensure the preview container is running
        preview_result = self.start_preview_container(user_id)
        
        if not booking_mode:
            return preview_result
        
        # Also start the booking container
        booking_result = self.start_booking_container(user_id, image_override=booking_image)
        
        if booking_result.get("success"):
            return booking_result  # Return booking container info as primary when in booking mode
        else:
            # Booking container failed but preview may be ok; report the booking error
            logger.error(f"Booking container failed for user {user_id}: {booking_result.get('error')}")
            return booking_result
    
    def stop_container(self, user_id: int) -> Dict:
        """Stop user's preview Theia container"""
        try:
            container_name = self.get_preview_container_name(user_id)
            
            # Stop container
            subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True, text=True, timeout=30
            )
            
            # Remove container to free VPS resources
            subprocess.run(
                ["docker", "rm", container_name],
                capture_output=True, text=True, timeout=30
            )
            
            # Release port mapping
            self.release_user_port(user_id)
            
            logger.info(f"Preview container {container_name} stopped and removed for user {user_id}")
            return {"success": True, "status": "stopped"}
            
        except Exception as e:
            logger.error(f"Error stopping preview container for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def stop_booking_container(self, user_id: int) -> Dict:
        """Stop user's booking Theia container"""
        try:
            container_name = self.get_booking_container_name(user_id)
            
            # Stop container
            subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True, text=True, timeout=30
            )
            
            # Remove container to free VPS resources
            subprocess.run(
                ["docker", "rm", container_name],
                capture_output=True, text=True, timeout=30
            )
            
            # Release booking port mapping
            self.release_user_booking_port(user_id)
            
            logger.info(f"Booking container {container_name} stopped and removed for user {user_id}")
            return {"success": True, "status": "stopped"}
            
        except Exception as e:
            logger.error(f"Error stopping booking container for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_user_container_and_files(self, user_id: int):
        """Delete user's containers (preview and booking) and project files"""
        import shutil
        
        try:
            # Force remove both containers
            for container_name in [
                self.get_preview_container_name(user_id),
                self.get_booking_container_name(user_id)
            ]:
                try:
                    subprocess.run(
                        ["docker", "rm", "-f", container_name],
                        capture_output=True, text=True, timeout=30
                    )
                    logger.info(f"✅ Removed container {container_name} for user {user_id}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to remove container {container_name} (may not exist): {e}")
            
            # Release ports
            self.release_user_port(user_id)
            self.release_user_booking_port(user_id)
            
            # Delete project directory
            user_project_dir = self.projects_dir / str(user_id)
            if user_project_dir.exists():
                shutil.rmtree(user_project_dir)
                logger.info(f"✅ Deleted project directory for user {user_id}: {user_project_dir}")
            else:
                logger.info(f"ℹ️ No project directory found for user {user_id}")
            
            logger.info(f"✅ Successfully deleted all resources for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error deleting resources for user {user_id}: {e}")
            raise
    
    def restart_container(self, user_id: int, booking_mode: bool = False, booking_image: Optional[str] = None) -> Dict:
        """Restart user's Theia container(s) with better error handling for crashed containers"""
        try:
            # Restart preview container
            preview_container_name = self.get_preview_container_name(user_id)
            stop_result = self.stop_container(user_id)
            if not stop_result.get("success"):
                logger.warning(f"Graceful preview stop failed for user {user_id}, forcing removal")
                try:
                    subprocess.run(
                        ["docker", "rm", "-f", preview_container_name],
                        capture_output=True, text=True, timeout=30
                    )
                    self.release_user_port(user_id)
                    logger.info(f"Force removed crashed preview container {preview_container_name} for user {user_id}")
                except Exception as force_error:
                    logger.error(f"Failed to force remove preview container for user {user_id}: {force_error}")
            
            if booking_mode:
                # Also restart the booking container
                booking_container_name = self.get_booking_container_name(user_id)
                stop_booking = self.stop_booking_container(user_id)
                if not stop_booking.get("success"):
                    try:
                        subprocess.run(
                            ["docker", "rm", "-f", booking_container_name],
                            capture_output=True, text=True, timeout=30
                        )
                        self.release_user_booking_port(user_id)
                    except Exception as force_error:
                        logger.error(f"Failed to force remove booking container for user {user_id}: {force_error}")
            
            return self.start_container(user_id, booking_mode=booking_mode, booking_image=booking_image)
        except Exception as e:
            logger.error(f"Error restarting container for user {user_id}: {e}")
            return {"success": False, "error": f"Restart failed: {str(e)}"}
    
    def list_user_containers(self) -> List[Dict]:
        """List all user containers (both preview and booking)"""
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
                        
                        # Extract container type and user ID from container name
                        container_type = None
                        user_id = None
                        if name.startswith(self.preview_container_prefix):
                            container_type = "preview"
                            user_id = name[len(self.preview_container_prefix):]
                        elif name.startswith(self.booking_container_prefix):
                            container_type = "booking"
                            user_id = name[len(self.booking_container_prefix):]
                        elif name.startswith(self.container_prefix):
                            # Legacy container naming
                            container_type = "legacy"
                            user_id = name[len(self.container_prefix):]
                        
                        if user_id is not None:
                            containers.append({
                                "user_id": user_id,
                                "container_name": name,
                                "container_type": container_type,
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
                        container_type = container.get("container_type", "preview")
                        if container_type == "booking":
                            result = self.stop_booking_container(user_id)
                        else:
                            result = self.stop_container(user_id)
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
                        container_type = container.get("container_type", "preview")
                        if container_type == "booking":
                            result = self.stop_booking_container(user_id)
                        else:
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
                
                # Check preview container and stop if running
                preview_status = self._get_single_container_status(
                    user_id, self.get_preview_container_name(user_id), self._port_mappings
                )
                if preview_status.get("status") == "running":
                    logger.info(f"Cleaning up preview container for user {user_id} after logout grace period")
                    self.stop_container(user_id)
                
                # Also stop booking container if running
                booking_status = self._get_single_container_status(
                    user_id, self.get_booking_container_name(user_id), self._booking_port_mappings
                )
                if booking_status.get("status") == "running":
                    logger.info(f"Cleaning up booking container for user {user_id} after logout grace period")
                    self.stop_booking_container(user_id)
            
            # Start cleanup thread
            cleanup_thread = threading.Thread(target=delayed_cleanup)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
            logger.info(f"Scheduled cleanup for user {user_id} in {self.logout_grace_period_minutes} minutes")
            return {"success": True, "message": f"Cleanup scheduled for {self.logout_grace_period_minutes} minutes"}
            
        except Exception as e:
            logger.error(f"Error scheduling cleanup for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def get_container_logs(self, user_id: int, container_type: str = "preview", lines: int = 200) -> Dict:
        """Return the last N log lines from a user's preview or booking container.

        Docker writes Theia output to stderr, so we capture both stdout and stderr
        and merge them.  Lines are returned newest-last (chronological order).
        """
        try:
            docker_check = subprocess.run(
                ["docker", "--version"], capture_output=True, text=True, timeout=5
            )
            if docker_check.returncode != 0:
                return {"logs": [], "error": "Docker service is not available"}

            container_name = (
                self.get_booking_container_name(user_id)
                if container_type == "booking"
                else self.get_preview_container_name(user_id)
            )

            lines = min(max(int(lines), 1), 500)

            result = subprocess.run(
                ["docker", "logs", "--tail", str(lines), "--timestamps", container_name],
                capture_output=True, text=True, timeout=15
            )

            if result.returncode != 0:
                stderr_lower = result.stderr.lower()
                if "no such container" in stderr_lower or "no such object" in stderr_lower:
                    return {
                        "logs": [f"[{container_type} container has not been started yet]"],
                        "container_name": container_name,
                        "container_type": container_type,
                        "lines": 0,
                    }

            # Docker interleaves stdout/stderr — merge both, split on newlines, drop blanks
            raw = (result.stdout or "") + (result.stderr or "")
            log_lines = [ln for ln in raw.splitlines() if ln.strip()]

            logger.info(f"Fetched {len(log_lines)} log lines from {container_name} for user {user_id}")
            return {
                "logs": log_lines,
                "container_name": container_name,
                "container_type": container_type,
                "lines": len(log_lines),
            }

        except subprocess.TimeoutExpired:
            logger.warning(f"docker logs timed out for user {user_id} container_type={container_type}")
            return {"logs": ["[Error: docker logs command timed out]"], "error": "timeout"}
        except FileNotFoundError:
            return {"logs": ["[Error: Docker is not installed or not in PATH]"], "error": "docker_not_found"}
        except Exception as e:
            logger.error(f"Error fetching container logs for user {user_id}: {e}")
            return {"logs": [f"[Error: {str(e)}]"], "error": str(e)}

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
                            container_type = container.get("container_type", "preview")
                            logger.info(f"{container_type.title()} container for user {user_id} idle for {(current_time - last_activity)/3600:.1f} hours - cleaning up")
                            if container_type == "booking":
                                result = self.stop_booking_container(user_id)
                            else:
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
