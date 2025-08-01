"""
Environment setup utilities for Docker operations.

This module handles Docker-specific environment setup including
networks, containers, and related infrastructure.
"""

import subprocess
from typing import Dict, Any

from ..core import print_error, print_info, print_success


class DockerEnvironmentSetup:
    """
    Handles Docker environment setup for StormShadow.
    """
    
    def __init__(self, network_manager, dry_run: bool = False):
        """
        Initialize Docker environment setup.
        
        Args:
            network_manager: NetworkManager instance
            dry_run: Whether to run in dry-run mode
        """
        self.network_manager = network_manager
        self.dry_run = dry_run
    
    async def setup_docker_networks(self) -> bool:
        """Setup Docker networks using the network manager."""
        if self.dry_run:
            print_info("[Dry‑run] Docker networks would be created")
            return True
            
        try:
            # Check if stormshadow network exists
            networks = self.network_manager.list_networks()
            
            if "stormshadow" not in [n.get('Name', '') for n in networks]:
                # Create stormshadow network
                success = self.network_manager.create_network(
                    name="stormshadow",
                    driver="bridge",
                    subnet="172.20.0.0/16"
                )
                
                if success:
                    print_info("Created stormshadow Docker network")
                else:
                    print_error("Failed to create stormshadow network")
                    return False
            else:
                print_info("Docker network 'stormshadow' already exists")
            
            return True
            
        except Exception as e:
            print_error(f"Error setting up networks: {e}")
            return False
    
    async def check_docker_available(self) -> bool:
        """Check if Docker is available and running."""
        try:
            # Try to run a simple Docker command
            result = subprocess.run(
                ["docker", "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                print_info(f"Docker available: {result.stdout.strip()}")
                
                # Also check if Docker daemon is running
                result = subprocess.run(
                    ["docker", "info"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                if result.returncode == 0:
                    print_info("Docker daemon is running")
                    return True
                else:
                    print_error("Docker is installed but daemon is not running")
                    return False
            else:
                print_error("Docker command failed")
                return False
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            print_error(f"Docker not available: {e}")
            return False
    
    async def cleanup_docker_containers(self) -> bool:
        """Clean up Docker containers with stormshadow label."""
        if self.dry_run:
            print_info("[Dry‑run] Docker containers would be cleaned up")
            return True
            
        try:
            # Stop all StormShadow containers
            result = subprocess.run([
                'docker', 'ps', '-q', '--filter', 'label=stormshadow'
            ], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                container_ids = result.stdout.strip().split('\n')
                subprocess.run(['docker', 'stop'] + container_ids)
                subprocess.run(['docker', 'rm'] + container_ids)
                print_success(f"Cleaned up {len(container_ids)} Docker containers")
                return True
            else:
                print_info("No StormShadow containers to clean up")
                return True
            
        except Exception as e:
            print_error(f"Error cleaning up Docker containers: {e}")
            return False
