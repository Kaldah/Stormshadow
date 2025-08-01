"""
Network manager for Docker operations.

This module provides Docker network management functionality
including network creation, configuration, and cleanup.
"""

import json
from typing import Dict, List, Optional, Any

from ..core import (
    print_error, print_warning, print_info, print_success, run_command
)


class NetworkManager:
    """
    Manages Docker network operations.

    Provides methods for:
    - Network creation and configuration
    - Network inspection and monitoring
    - Network cleanup and removal
    - IP address management
    """

    def __init__(self):
        """Initialize network manager."""
        self.networks: Dict[str, str] = {}  # name -> network_id mapping

    def create_network(
        self,
        name: str,
        driver: str = "bridge",
        subnet: Optional[str] = None,
        gateway: Optional[str] = None,
        ip_range: Optional[str] = None,
        options: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Create a Docker network.

        Args:
            name: Network name
            driver: Network driver (bridge, overlay, etc.)
            subnet: Network subnet (e.g., "172.20.0.0/16")
            gateway: Gateway IP address
            ip_range: IP range for allocation
            options: Driver-specific options
            labels: Network labels

        Returns:
            bool: True if network created successfully
        """
        cmd = ["docker", "network", "create"]

        # Network driver
        cmd.extend(["--driver", driver])

        # Subnet configuration
        if subnet:
            cmd.extend(["--subnet", subnet])

        if gateway:
            cmd.extend(["--gateway", gateway])

        if ip_range:
            cmd.extend(["--ip-range", ip_range])

        # Driver options
        if options:
            for key, value in options.items():
                cmd.extend(["--opt", f"{key}={value}"])

        # Labels
        if labels:
            for key, value in labels.items():
                cmd.extend(["--label", f"{key}={value}"])

        # Network name
        cmd.append(name)

        # Check if network already exists
        if self.network_exists(name):
            print_info(f"Network '{name}' already exists, skipping creation")
            return True

        print_info(f"Creating network: {name}")

        try:
            result = run_command(' '.join(cmd), capture_output=True)

            if result.returncode == 0:
                network_id = result.stdout.strip() if result.stdout else ""
                self.networks[name] = network_id
                print_success(f"Network created: {name} ({network_id[:12] if network_id else 'unknown'})")
                return True
            else:
                print_error(f"Failed to create network: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error creating network: {e}")
            return False

    def remove_network(self, name: str, force: bool = False) -> bool:
        """
        Remove a Docker network.

        Args:
            name: Network name or ID
            force: Force removal of network

        Returns:
            bool: True if network removed successfully
        """
        cmd = ["docker", "network", "rm"]

        if force:
            cmd.append("-f")

        cmd.append(name)

        print_info(f"Removing network: {name}")

        try:
            result = run_command(' '.join(cmd), capture_output=True)

            if result.returncode == 0:
                # Remove from tracking
                if name in self.networks:
                    del self.networks[name]
                print_success(f"Network removed: {name}")
                return True
            else:
                print_error(f"Failed to remove network: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error removing network: {e}")
            return False

    def connect_container(
        self,
        network: str,
        container: str,
        ip: Optional[str] = None,
        aliases: Optional[List[str]] = None
    ) -> bool:
        """
        Connect container to network.

        Args:
            network: Network name or ID
            container: Container name or ID
            ip: Static IP address for container
            aliases: Network aliases for container

        Returns:
            bool: True if connected successfully
        """
        cmd = ["docker", "network", "connect"]

        if ip:
            cmd.extend(["--ip", ip])

        if aliases:
            for alias in aliases:
                cmd.extend(["--alias", alias])

        cmd.extend([network, container])

        print_info(f"Connecting {container} to network {network}")

        try:
            result = run_command(' '.join(cmd))

            if result.returncode == 0:
                print_success(f"Container connected to network")
                return True
            else:
                print_error(f"Failed to connect container: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error connecting container to network: {e}")
            return False

    def disconnect_container(
            self, network: str, container: str, force: bool = False) -> bool:
        """
        Disconnect container from network.

        Args:
            network: Network name or ID
            container: Container name or ID
            force: Force disconnection

        Returns:
            bool: True if disconnected successfully
        """
        cmd = ["docker", "network", "disconnect"]

        if force:
            cmd.append("-f")

        cmd.extend([network, container])

        print_info(f"Disconnecting {container} from network {network}")

        try:
            result = run_command(' '.join(cmd))

            if result.returncode == 0:
                print_success("Container disconnected from network")
                return True
            else:
                print_error(f"Failed to disconnect container: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error disconnecting container from network: {e}")
            return False

    def network_exists(self, name: str) -> bool:
        """
        Check if network exists.

        Args:
            name: Network name or ID

        Returns:
            bool: True if network exists
        """
        try:
            result = run_command(f"docker network inspect {name}", capture_output=True)
            return result.returncode == 0
        except Exception:
            return False

    def get_network_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a network.

        Args:
            name: Network name or ID

        Returns:
            Optional[Dict[str, Any]]: Network information or None if failed
        """
        try:
            result = run_command(f"docker network inspect {name}", capture_output=True)

            if result.returncode == 0 and result.stdout:
                info = json.loads(result.stdout)
                return info[0] if info else None
            else:
                return None

        except Exception as e:
            print_error(f"Error getting network info: {e}")
            return None

    def list_networks(self) -> List[Dict[str, str]]:
        """
        List all Docker networks.

        Returns:
            List[Dict[str, str]]: List of network information
        """
        try:
            cmd = ('docker network ls --format '
                   '"{{.ID}}\\t{{.Name}}\\t{{.Driver}}\\t{{.Scope}}"')
            result = run_command(cmd, capture_output=True)

            if result.returncode == 0:
                lines = (result.stdout.strip().split('\n')
                         if result.stdout else [])
                networks: List[Dict[str, str]] = []

                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 4:
                            networks.append({
                                'id': parts[0],
                                'name': parts[1],
                                'driver': parts[2],
                                'scope': parts[3]
                            })

                return networks
            else:
                print_error(f"Failed to list networks: {result.stderr}")
                return []

        except Exception as e:
            print_error(f"Error listing networks: {e}")
            return []

    def get_container_networks(self, container: str) -> List[str]:
        """
        Get networks that a container is connected to.

        Args:
            container: Container name or ID

        Returns:
            List[str]: List of network names
        """
        try:
            result = run_command(f"docker inspect {container}")

            if result.returncode == 0:
                info = json.loads(result.stdout)
                if info:
                    networks = info[0].get(
                        'NetworkSettings', {}).get(
                        'Networks', {})
                    return list(networks.keys())

            return []

        except Exception as e:
            print_error(f"Error getting container networks: {e}")
            return []

    def get_network_containers(self, network: str) -> List[Dict[str, str]]:
        """
        Get containers connected to a network.

        Args:
            network: Network name or ID

        Returns:
            List[Dict[str, str]]: List of container information
        """
        network_info = self.get_network_info(network)
        if not network_info:
            return []

        containers: List[Dict[str, str]] = []
        for container_id, container_data in network_info.get(
                'Containers', {}).items():
            containers.append({
                'id': container_id,
                'name': container_data.get('Name', ''),
                'ip': container_data.get('IPv4Address', '').split('/')[0],
                'mac': container_data.get('MacAddress', '')
            })

        return containers

    def prune_networks(self) -> bool:
        """
        Remove unused networks.

        Returns:
            bool: True if pruning successful
        """
        print_info("Pruning unused networks...")

        try:
            result = run_command("docker network prune -f")

            if result.returncode == 0:
                print_success("Unused networks pruned")
                return True
            else:
                print_error(f"Failed to prune networks: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error pruning networks: {e}")
            return False

    def cleanup_all_networks(self) -> bool:
        """
        Clean up all tracked networks.

        Returns:
            bool: True if cleanup successful
        """
        print_info("Cleaning up all tracked networks...")

        success = True
        for name in list(self.networks.keys()):
            if self.network_exists(name):
                if not self.remove_network(name, force=True):
                    success = False

        if success:
            self.networks.clear()
            print_success("All networks cleaned up successfully")
        else:
            print_warning("Some networks could not be cleaned up")

        return success
