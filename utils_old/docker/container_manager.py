"""
Container manager for StormShadow Docker operations.

This module provides comprehensive container lifecycle management
including creation, execution, monitoring, and cleanup.
"""

import json
from typing import Dict, List, Optional, Any, cast
from ..core import (
    print_error, print_warning, print_info, print_success, run_command
)


class ContainerManager:
    """
    Manages Docker container operations.

    Provides methods for:
    - Container creation and management
    - Command execution inside containers
    - File operations (copy to/from containers)
    - Container monitoring and logging
    """

    def __init__(self):
        """Initialize container manager."""
        self.containers: Dict[str, str] = {}  # name -> container_id mapping
        self.verify_docker_available()

    def verify_docker_available(self) -> bool:
        """
        Verify Docker is available and running.

        Returns:
            bool: True if Docker is available
        """
        try:
            result = run_command("docker info", timeout=10)
            if result.returncode == 0:
                print_info("Docker is available and running")
                return True
            else:
                print_error("Docker is not running or not accessible")
                return False
        except Exception as e:
            print_error(f"Failed to check Docker availability: {e}")
            return False

    def run_container(
        self,
        image: str,
        name: Optional[str] = None,
        ports: Optional[List[str]] = None,
        volumes: Optional[List[str]] = None,
        environment: Optional[List[str]] = None,
        network: Optional[str] = None,
        command: Optional[str] = None,
        detach: bool = True,
        remove: bool = False,
        interactive: bool = False,
        tty: bool = False,
        **kwargs: Any
    ) -> Optional[str]:
        """
        Run a Docker container.

        Args:
            image: Docker image name
            name: Container name
            ports: Port mappings (e.g., ["8080:80"])
            volumes: Volume mappings (e.g., ["/host/path:/container/path"])
            environment: Environment variables (e.g., ["VAR=value"])
            network: Network to connect to
            command: Command to run in container
            detach: Run container in background
            remove: Remove container when it stops
            interactive: Keep STDIN open
            tty: Allocate pseudo-TTY
            **kwargs: Additional docker run options

        Returns:
            Optional[str]: Container ID if successful, None otherwise
        """
        cmd = ["docker", "run"]

        # Container options
        if detach:
            cmd.append("-d")
        if remove:
            cmd.append("--rm")
        if interactive:
            cmd.append("-i")
        if tty:
            cmd.append("-t")

        # Container name
        if name:
            cmd.extend(["--name", name])

        # Port mappings
        if ports:
            for port in ports:
                cmd.extend(["-p", port])

        # Volume mappings
        if volumes:
            for volume in volumes:
                cmd.extend(["-v", volume])

        # Environment variables
        if environment:
            for env in environment:
                cmd.extend(["-e", env])

        # Network
        if network:
            cmd.extend(["--network", network])

        # Additional options from kwargs
        for key, value in kwargs.items():
            if key.startswith('--'):
                if value is True:
                    cmd.append(key)
                elif value not in [False, None]:
                    if isinstance(value, list):
                        value_list = cast(List[Any], value)
                        for item in value_list:
                            cmd.extend([key, str(item)])
                    else:
                        cmd.extend([key, str(value)])
            else:
                docker_key = f"--{key.replace('_', '-')}"
                if value is True:
                    cmd.append(docker_key)
                elif value not in [False, None]:
                    if isinstance(value, list):
                        value_list = cast(List[Any], value)
                        for item in value_list:
                            cmd.extend([docker_key, str(item)])
                    else:
                        cmd.extend([docker_key, str(value)])

        # Image
        cmd.append(image)

        # Command
        if command:
            cmd.extend(command.split())

        print_info(f"Running container: {' '.join(cmd)}")

        try:
            result = run_command(cmd, capture_output=True, timeout=30)

            if result.returncode == 0:
                container_id = result.stdout.strip() if result.stdout else ""
                if name and container_id:
                    self.containers[name] = container_id
                container_short = (
                    container_id[:12] if container_id and
                    len(container_id) >= 12 else container_id
                )
                print_success(
                    f"Container started successfully: {container_short}"
                )
                return container_id if container_id else None
            else:
                print_error(f"Failed to start container: {result.stderr}")
                return None

        except Exception as e:
            print_error(f"Error starting container: {e}")
            return None

    def stop_container(self, container: str, timeout: int = 10) -> bool:
        """
        Stop a running container.

        Args:
            container: Container ID or name
            timeout: Timeout in seconds

        Returns:
            bool: True if stopped successfully
        """
        print_info(f"Stopping container: {container}")

        try:
            result = run_command(f"docker stop -t {timeout} {container}")

            if result.returncode == 0:
                print_success(f"Container stopped: {container}")
                return True
            else:
                print_error(f"Failed to stop container: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error stopping container: {e}")
            return False

    def remove_container(self, container: str, force: bool = False) -> bool:
        """
        Remove a container.

        Args:
            container: Container ID or name
            force: Force removal of running container

        Returns:
            bool: True if removed successfully
        """
        cmd = ["docker", "rm"]
        if force:
            cmd.append("-f")
        cmd.append(container)

        print_info(f"Removing container: {container}")

        try:
            result = run_command(' '.join(cmd))

            if result.returncode == 0:
                # Remove from tracking
                for name, cid in list(self.containers.items()):
                    if cid == container or name == container:
                        del self.containers[name]
                        break

                print_success(f"Container removed: {container}")
                return True
            else:
                print_error(f"Failed to remove container: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error removing container: {e}")
            return False

    def execute_command(
        self,
        container: str,
        command: str,
        user: Optional[str] = None,
        workdir: Optional[str] = None,
        interactive: bool = False,
        tty: bool = False
    ) -> Optional[str]:
        """
        Execute command in running container.

        Args:
            container: Container ID or name
            command: Command to execute
            user: User to run command as
            workdir: Working directory
            interactive: Keep STDIN open
            tty: Allocate pseudo-TTY

        Returns:
            Optional[str]: Command output or None if failed
        """
        cmd = ["docker", "exec"]

        if interactive:
            cmd.append("-i")
        if tty:
            cmd.append("-t")
        if user:
            cmd.extend(["-u", user])
        if workdir:
            cmd.extend(["-w", workdir])

        cmd.append(container)
        cmd.extend(command.split())

        try:
            result = run_command(' '.join(cmd))

            if result.returncode == 0:
                return result.stdout
            else:
                print_error(f"Command failed in container: {result.stderr}")
                return None

        except Exception as e:
            print_error(f"Error executing command in container: {e}")
            return None

    def copy_to_container(
        self, container: str, src_path: str, dst_path: str
    ) -> bool:
        """
        Copy file/directory to container.

        Args:
            container: Container ID or name
            src_path: Source path on host
            dst_path: Destination path in container

        Returns:
            bool: True if copy successful
        """
        print_info(f"Copying {src_path} to {container}:{dst_path}")

        try:
            cmd = f"docker cp {src_path} {container}:{dst_path}"
            result = run_command(cmd)

            if result.returncode == 0:
                print_success("File copied successfully")
                return True
            else:
                print_error(f"Failed to copy file: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error copying file to container: {e}")
            return False

    def copy_from_container(
        self, container: str, src_path: str, dst_path: str
    ) -> bool:
        """
        Copy file/directory from container.

        Args:
            container: Container ID or name
            src_path: Source path in container
            dst_path: Destination path on host

        Returns:
            bool: True if copy successful
        """
        print_info(f"Copying {container}:{src_path} to {dst_path}")

        try:
            cmd = f"docker cp {container}:{src_path} {dst_path}"
            result = run_command(cmd)

            if result.returncode == 0:
                print_success("File copied successfully")
                return True
            else:
                print_error(f"Failed to copy file: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error copying file from container: {e}")
            return False

    def get_container_info(self, container: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a container.

        Args:
            container: Container ID or name

        Returns:
            Optional[Dict[str, Any]]: Container information or None if failed
        """
        try:
            # First try without sudo
            result = run_command(f"docker inspect {container}", capture_output=True, check=False)

            if result.returncode != 0:
                # If failed, try with sudo (for systems where Docker requires sudo)
                result = run_command(f"sudo docker inspect {container}", capture_output=True, check=False)

            if result.returncode == 0 and result.stdout:
                info = json.loads(result.stdout)
                return info[0] if info else None
            else:
                # Don't print error for silent container existence checks
                return None

        except json.JSONDecodeError as e:
            print_error(f"Error parsing container info JSON: {e}")
            return None
        except Exception as e:
            print_error(f"Error getting container info: {e}")
            return None

    def get_container_logs(
        self,
        container: str,
        tail: int = 100,
        follow: bool = False,
        timestamps: bool = False
    ) -> Optional[str]:
        """
        Get container logs.

        Args:
            container: Container ID or name
            tail: Number of lines to retrieve
            follow: Follow log output
            timestamps: Include timestamps

        Returns:
            Optional[str]: Container logs or None if failed
        """
        cmd = ["docker", "logs"]

        if tail > 0:
            cmd.extend(["--tail", str(tail)])
        if follow:
            cmd.append("-f")
        if timestamps:
            cmd.append("-t")

        cmd.append(container)

        try:
            result = run_command(' '.join(cmd))

            if result.returncode == 0:
                return result.stdout
            else:
                print_error(f"Failed to get container logs: {result.stderr}")
                return None

        except Exception as e:
            print_error(f"Error getting container logs: {e}")
            return None

    def list_containers(
        self, all_containers: bool = False
    ) -> List[Dict[str, str]]:
        """
        List containers.

        Args:
            all_containers: Include stopped containers

        Returns:
            List[Dict[str, str]]: List of container information
        """
        cmd = [
            "docker", "ps", "--format",
            "{{.ID}}\\t{{.Names}}\\t{{.Status}}\\t{{.Image}}"
        ]

        if all_containers:
            cmd.append("-a")

        try:
            result = run_command(' '.join(cmd), capture_output=True)

            if result.returncode == 0:
                containers: List[Dict[str, str]] = []
                
                if result.stdout and result.stdout.strip():
                    lines = result.stdout.strip().split('\n')

                    for line in lines:
                        if line.strip():
                            parts = line.split('\t')
                            if len(parts) >= 4:
                                containers.append({
                                    'id': parts[0],
                                    'name': parts[1],
                                    'status': parts[2],
                                    'image': parts[3]
                                })

                return containers
            else:
                print_error(f"Failed to list containers: {result.stderr}")
                return []

        except Exception as e:
            print_error(f"Error listing containers: {e}")
            return []

    def container_exists(self, container: str) -> bool:
        """
        Check if container exists.

        Args:
            container: Container ID or name

        Returns:
            bool: True if container exists
        """
        try:
            # First try without sudo
            result = run_command(f"docker inspect {container}", check=False, capture_output=True)
            if result.returncode == 0:
                return True
            
            # If failed, try with sudo (for systems where Docker requires sudo)
            result = run_command(f"sudo docker inspect {container}", check=False, capture_output=True)
            return result.returncode == 0
        except Exception:
            return False

    def is_container_running(self, container: str) -> bool:
        """
        Check if container is running.

        Args:
            container: Container ID or name

        Returns:
            bool: True if container is running
        """
        info = self.get_container_info(container)
        if info:
            return info.get('State', {}).get('Running', False)
        return False

    def cleanup_all_containers(self, force: bool = False) -> bool:
        """
        Clean up all tracked containers.

        Args:
            force: Force removal of running containers

        Returns:
            bool: True if cleanup successful
        """
        print_info("Cleaning up all tracked containers...")

        success = True
        for _, container_id in list(self.containers.items()):
            if self.container_exists(container_id):
                if self.is_container_running(container_id):
                    if not self.stop_container(container_id):
                        success = False
                        continue

                if not self.remove_container(container_id, force=force):
                    success = False

        if success:
            self.containers.clear()
            print_success("All containers cleaned up successfully")
        else:
            print_warning("Some containers could not be cleaned up")

        return success

    def cleanup_container(self, container: str, force: bool = False) -> bool:
        """
        Clean up a specific container (stop and remove).
        
        Args:
            container: Container ID or name
            force: Force removal of running container
            
        Returns:
            bool: True if cleanup successful
        """
        try:
            # Stop container if running
            if self.is_container_running(container):
                if not self.stop_container(container):
                    print_warning(f"Failed to stop container {container}")
                    if not force:
                        return False
            
            # Remove container
            if self.container_exists(container):
                return self.remove_container(container, force=force)
            
            return True
            
        except Exception as e:
            print_error(f"Error cleaning up container {container}: {e}")
            return False

    def get_container_ip(self, container: str, network: Optional[str] = None) -> Optional[str]:
        """
        Get container IP address.
        
        Args:
            container: Container ID or name
            network: Specific network name (optional)
            
        Returns:
            Container IP address or None if not found
        """
        try:
            info = self.get_container_info(container)
            if not info:
                return None
            
            networks = info.get('NetworkSettings', {}).get('Networks', {})
            
            if network:
                # Get IP from specific network
                network_info = networks.get(network, {})
                return network_info.get('IPAddress')
            else:
                # Get IP from any network (prefer non-bridge)
                for net_info in networks.values():
                    ip = net_info.get('IPAddress')
                    if ip and ip != '':
                        return ip
                
                return None
                
        except Exception as e:
            print_error(f"Error getting container IP: {e}")
            return None

    def execute_in_container(self, container: str, command: List[str]) -> Optional[Any]:
        """
        Execute command in container (alias for execute_command with list input).
        
        Args:
            container: Container ID or name
            command: Command as list of strings
            
        Returns:
            Command result or None if failed
        """
        try:
            cmd_str = ' '.join(command)
            result = self.execute_command(container, cmd_str)
            
            if result is not None:
                # Create a mock result object similar to subprocess.run
                class MockResult:
                    def __init__(self, stdout: str):
                        self.stdout = stdout
                        self.returncode = 0
                
                return MockResult(result)
            else:
                class FailedResult:
                    def __init__(self):
                        self.stdout = ""
                        self.returncode = 1
                
                return FailedResult()
                
        except Exception as e:
            print_error(f"Error executing command in container: {e}")
            return None

    def execute_in_container_sync(self, container: str, command: List[str]) -> Optional[Any]:
        """
        Synchronous execution in container (for use with wait_for_condition).
        
        Args:
            container: Container ID or name
            command: Command as list of strings
            
        Returns:
            Command result or None if failed
        """
        return self.execute_in_container(container, command)
