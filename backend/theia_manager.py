"""
Docker container management for Theia IDE instances
"""
import docker
import os
import logging
import time
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

class TheiaDockerManager:
    def __init__(self):
        """Initialize Docker client and set up configuration"""
        try:
            self.client = docker.from_env()
            self.image_name = "robot-theia-ide:latest"
            self.container_prefix = "theia-user-"
            self.network_name = "robot-network"
            self.user_data_path = Path("data/users")
            self.theia_port_start = 3001  # Start from 3001 to avoid conflicts
            
            # Ensure user data directory exists
            self.user_data_path.mkdir(parents=True, exist_ok=True)
            
            # Ensure Docker network exists
            self._ensure_network()
            
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise

    def _ensure_network(self):
        """Ensure the robot network exists"""
        try:
            networks = self.client.networks.list(names=[self.network_name])
            if not networks:
                self.client.networks.create(self.network_name, driver="bridge")
                logger.info(f"Created Docker network: {self.network_name}")
            else:
                logger.info(f"Docker network {self.network_name} already exists")
        except Exception as e:
            logger.error(f"Failed to ensure network: {e}")

    def _get_user_data_dir(self, user_id: str) -> Path:
        """Get or create user-specific data directory"""
        user_dir = self.user_data_path / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Create initial project structure if it doesn't exist
        if not (user_dir / "README.md").exists():
            readme_content = f"""# Robot Programming Workspace for User {user_id}

Welcome to your personal robot programming environment!

## Available Tools
- Python 3 with robotics libraries (numpy, opencv, etc.)
- C++ compiler (g++/gcc)
- Git for version control
- Various text editors (nano, vim)

## Getting Started
1. Create your robot control scripts in this workspace
2. Use the integrated terminal for running commands
3. Your work is automatically saved and persistent

Happy coding! 🤖
"""
            (user_dir / "README.md").write_text(readme_content)
            
            # Create sample Python script
            sample_py = user_dir / "robot_sample.py"
            sample_py.write_text('''#!/usr/bin/env python3
"""
Sample robot control script
"""

import time
import math

def robot_move_forward(distance):
    """Simulate moving robot forward"""
    print(f"Moving robot forward {distance} units")
    time.sleep(1)
    
def robot_turn(angle):
    """Simulate turning robot"""
    print(f"Turning robot {angle} degrees")
    time.sleep(0.5)

def main():
    print("Starting robot control sequence...")
    
    # Simple square pattern
    for i in range(4):
        robot_move_forward(10)
        robot_turn(90)
    
    print("Robot control sequence completed!")

if __name__ == "__main__":
    main()
''')
        
        return user_dir

    def _find_available_port(self) -> int:
        """Find an available port for the Theia container"""
        used_ports = set()
        
        # Check existing containers for used ports
        containers = self.client.containers.list(
            filters={"name": self.container_prefix}
        )
        
        for container in containers:
            for port_binding in container.attrs.get('NetworkSettings', {}).get('Ports', {}).values():
                if port_binding:
                    for binding in port_binding:
                        used_ports.add(int(binding['HostPort']))
        
        # Find first available port
        port = self.theia_port_start
        while port in used_ports:
            port += 1
        
        return port

    def get_or_create_container(self, user_id: str) -> Dict[str, str]:
        """Get existing container or create new one for user"""
        container_name = f"{self.container_prefix}{user_id}"
        
        try:
            # Check if container already exists
            try:
                container = self.client.containers.get(container_name)
                
                # Check if container is running
                if container.status == "running":
                    # Get the port mapping
                    port_bindings = container.attrs['NetworkSettings']['Ports']
                    host_port = None
                    for port_binding in port_bindings.get('3000/tcp', []):
                        if port_binding:
                            host_port = port_binding['HostPort']
                            break
                    
                    if host_port:
                        return {
                            "container_id": container.id,
                            "container_name": container_name,
                            "status": "running",
                            "url": f"http://localhost:{host_port}",
                            "port": host_port
                        }
                
                # Container exists but not running, start it
                elif container.status == "exited":
                    container.start()
                    time.sleep(3)  # Wait for container to start
                    
                    # Get updated port info
                    container.reload()
                    port_bindings = container.attrs['NetworkSettings']['Ports']
                    host_port = None
                    for port_binding in port_bindings.get('3000/tcp', []):
                        if port_binding:
                            host_port = port_binding['HostPort']
                            break
                    
                    if host_port:
                        return {
                            "container_id": container.id,
                            "container_name": container_name,
                            "status": "started",
                            "url": f"http://localhost:{host_port}",
                            "port": host_port
                        }
                        
            except docker.errors.NotFound:
                # Container doesn't exist, create new one
                pass
            
            # Create new container
            user_data_dir = self._get_user_data_dir(user_id)
            host_port = self._find_available_port()
            
            # Build image if it doesn't exist
            try:
                self.client.images.get(self.image_name)
            except docker.errors.ImageNotFound:
                logger.info(f"Building Theia image: {self.image_name}")
                self.client.images.build(
                    path=".",
                    dockerfile="Dockerfile.theia",
                    tag=self.image_name,
                    rm=True
                )
            
            container = self.client.containers.run(
                self.image_name,
                name=container_name,
                ports={'3000/tcp': host_port},
                volumes={
                    str(user_data_dir.absolute()): {
                        'bind': '/home/project',
                        'mode': 'rw'
                    }
                },
                environment={
                    'THEIA_WORKSPACE_ROOT': '/home/project'
                },
                network=self.network_name,
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            # Wait for container to start
            time.sleep(5)
            
            return {
                "container_id": container.id,
                "container_name": container_name,
                "status": "created",
                "url": f"http://localhost:{host_port}",
                "port": str(host_port)
            }
            
        except Exception as e:
            logger.error(f"Failed to create/get container for user {user_id}: {e}")
            raise

    def stop_container(self, user_id: str) -> bool:
        """Stop user's Theia container"""
        container_name = f"{self.container_prefix}{user_id}"
        
        try:
            container = self.client.containers.get(container_name)
            container.stop()
            logger.info(f"Stopped container {container_name}")
            return True
        except docker.errors.NotFound:
            logger.warning(f"Container {container_name} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to stop container {container_name}: {e}")
            return False

    def remove_container(self, user_id: str) -> bool:
        """Remove user's Theia container"""
        container_name = f"{self.container_prefix}{user_id}"
        
        try:
            container = self.client.containers.get(container_name)
            container.stop()
            container.remove()
            logger.info(f"Removed container {container_name}")
            return True
        except docker.errors.NotFound:
            logger.warning(f"Container {container_name} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to remove container {container_name}: {e}")
            return False

    def list_user_containers(self) -> list:
        """List all user Theia containers"""
        try:
            containers = self.client.containers.list(
                all=True,
                filters={"name": self.container_prefix}
            )
            
            result = []
            for container in containers:
                user_id = container.name.replace(self.container_prefix, "")
                
                # Get port info
                host_port = None
                if container.status == "running":
                    port_bindings = container.attrs.get('NetworkSettings', {}).get('Ports', {})
                    for port_binding in port_bindings.get('3000/tcp', []):
                        if port_binding:
                            host_port = port_binding['HostPort']
                            break
                
                result.append({
                    "user_id": user_id,
                    "container_name": container.name,
                    "container_id": container.short_id,
                    "status": container.status,
                    "url": f"http://localhost:{host_port}" if host_port else None,
                    "port": host_port
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to list containers: {e}")
            return []

    def cleanup_stopped_containers(self) -> int:
        """Remove all stopped user containers"""
        try:
            containers = self.client.containers.list(
                filters={"name": self.container_prefix, "status": "exited"}
            )
            
            count = 0
            for container in containers:
                container.remove()
                count += 1
            
            logger.info(f"Cleaned up {count} stopped containers")
            return count
            
        except Exception as e:
            logger.error(f"Failed to cleanup containers: {e}")
            return 0

    def get_container_logs(self, user_id: str, lines: int = 100) -> str:
        """Get logs from user's container"""
        container_name = f"{self.container_prefix}{user_id}"
        
        try:
            container = self.client.containers.get(container_name)
            logs = container.logs(tail=lines).decode('utf-8')
            return logs
        except docker.errors.NotFound:
            return f"Container {container_name} not found"
        except Exception as e:
            logger.error(f"Failed to get logs for container {container_name}: {e}")
            return f"Error getting logs: {e}"