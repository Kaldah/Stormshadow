"""
Lab Manager for StormShadow.

This module provides centralized lab environment management by managing
Docker containers and lab infrastructure.
"""

import os
import time

from .core.printing import print_info, print_error, print_debug
from .config.config import Config
from utils.core.command_runner import run_process, run_command

class LabManager:
    """
    Manages lab module lifecycle and coordination.

    This manager provides:
    - Lab module discovery and loading
    - Lab lifecycle management (start/stop/status)
    - Coordination with other system components
    """

    def __init__(self, config: Config, keep_lab_open: bool = False) -> None:
        """
        Initialize lab manager.
        
        Args:
            config: Lab configuration
        """
        self.config = config
        self.container_process = None
        self.container_name = "sip-victim"
        self.docker_image = "asterisk-sip-server"
        
        # Get the project root directory (assuming lab manager is in utils/)
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.lab_script_path = os.path.join(self.project_root, "sip-lab", "run_victim.sh")
        self.keep_lab_open = keep_lab_open
        print_info("Lab manager initialized")

    def _cleanup_container(self) -> None:
        """
        Clean up any existing Docker container.
        """
        try:
            print_info("Cleaning up existing containers...")
            
            # Check if container exists
            result = run_command(
                f"sudo docker ps -a --format '{{{{.Names}}}}' | grep -q '^{self.container_name}$'",
                check=False,
                capture_output=True
            )
            
            if result.returncode == 0:
                print_info(f"Removing existing container '{self.container_name}'...")
                run_command(f"sudo docker rm -f {self.container_name}")
                print_info("Container cleanup complete")
            else:
                print_debug("No existing container found")
                
        except Exception as e:
            print_error(f"Error during container cleanup: {e}")

    def _build_docker_image(self) -> bool:
        """
        Build the Docker image if it doesn't exist.
        
        Returns:
            bool: True if image exists or was built successfully, False otherwise
        """
        try:
            # Check if image exists
            result = run_command(
                f"sudo docker images -q {self.docker_image}",
                capture_output=True,
                check=False
            )
            
            if result.stdout.strip():
                print_debug(f"Docker image '{self.docker_image}' already exists")
                return True
            
            print_info(f"Building Docker image '{self.docker_image}'...")
            dockerfile_path = os.path.join(self.project_root, "sip-lab", "sip_server")
            
            build_result = run_command(
                f"sudo docker build -t {self.docker_image} .",
                cwd=dockerfile_path,
                capture_output=False
            )
            
            if build_result.returncode == 0:
                print_info("Docker image built successfully")
                return True
            else:
                print_error("Failed to build Docker image")
                return False
                
        except Exception as e:
            print_error(f"Error building Docker image: {e}")
            return False

    def start(self) -> None:
        """
        Start the lab manager.
        
        This method initializes and starts the SIP lab Docker container.
        """
        print_info("Starting lab manager...")
        
        try:
            # Clean up any existing containers
            self._cleanup_container()
            
            # Build Docker image if needed
            if not self._build_docker_image():
                print_error("Failed to build Docker image, cannot start lab")
                return
            
            # Start the Docker container
            print_info("Starting Docker container...")
            
            docker_command = (
                f"sudo docker run --rm -it "
                f"--network host "
                f"--cap-add=NET_ADMIN "
                f"--cap-add=NET_RAW "
                f"-e SPOOFED_SUBNET=10.10.123.0/25 "
                f"-e RETURN_ADDR=10.135.97.2 "
                f"--name {self.container_name} "
                f"{self.docker_image}"
            )
            
            # Start the container in a new terminal so it can be interactive
            self.container_process = run_process(
                command=docker_command,
                new_terminal=True,
                keep_alive=False
            )
            
            print_info(f"Lab container '{self.container_name}' started successfully")
            print_info("Container is running in a new terminal window")
            
        except Exception as e:
            print_error(f"Error starting lab: {e}")
            self.stop()

    def stop(self) -> None:
        """
        Stop the lab manager.
        
        This method stops the running Docker container and cleans up resources.
        """
        print_info("Stopping lab manager...")
        
        try:
            # Terminate the container process if it exists
            if self.container_process and not self.keep_lab_open:
                try:
                    print_info(f"Terminating container process '{self.container_name}'...")
                    self.container_process.terminate()
                    time.sleep(2)  # Give it time to terminate gracefully
                    
                    if self.container_process.poll() is None:
                        self.container_process.kill()
                    # Clean dnat rules if any
                    # run_command(f"sudo iptables -t nat -D OUTPUT -d {self.spoofed_subnet} -p udp -m udp --sport 5060 -m comment --comment asterisk-dnat -j DNAT --to-destination {self.return_addr}")
                except Exception as e:
                    print_debug(f"Error terminating container process: {e}")
                finally:
                    self.container_process = None
                
                # Clean up the container
                self._cleanup_container()
                
                print_info("Lab manager stopped successfully")
            
        except Exception as e:
            print_error(f"Error stopping lab: {e}")

    def status(self) -> bool:
        """
        Check if the lab is running.
        
        Returns:
            bool: True if lab is running, False otherwise
        """
        try:
            result = run_command(
                f"sudo docker ps --format '{{{{.Names}}}}' | grep -q '^{self.container_name}$'",
                check=False,
                capture_output=True
            )
            
            is_running = result.returncode == 0
            
            if is_running:
                print_info(f"Lab container '{self.container_name}' is running")
            else:
                print_info(f"Lab container '{self.container_name}' is not running")
                
            return is_running
            
        except Exception as e:
            print_error(f"Error checking lab status: {e}")
            return False

    def restart(self) -> None:
        """
        Restart the lab manager.
        """
        print_info("Restarting lab manager...")
        self.stop()
        time.sleep(1)  # Brief pause between stop and start
        self.start()