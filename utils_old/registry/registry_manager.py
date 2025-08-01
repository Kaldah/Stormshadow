"""
Registry manager for Docker registry operations.

This module provides Docker registry management functionality
including registry operations, authentication, and image management.
"""

import json
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse

from ..core import print_error, print_warning, print_info, print_success, run_command


class RegistryManager:
    """
    Manages Docker registry operations.

    Provides methods for:
    - Registry authentication and configuration
    - Image pushing and pulling
    - Registry catalog and tag management
    - Local registry setup and management
    """

    def __init__(self, default_registry: Optional[str] = None):
        """
        Initialize registry manager.

        Args:
            default_registry: Default registry URL
        """
        self.default_registry = default_registry or "docker.io"
        self.auth_configs: Dict[str, Dict[str, str]] = {}
        self.load_docker_config()

    def load_docker_config(self) -> None:
        """Load Docker configuration including registry auth."""
        docker_config_path = Path.home() / ".docker" / "config.json"

        if docker_config_path.exists():
            try:
                with open(docker_config_path, 'r') as f:
                    config = json.load(f)

                # Load authentication configurations
                auths = config.get('auths', {})
                for registry, auth_data in auths.items():
                    self.auth_configs[registry] = auth_data

                print_info(f"Loaded Docker config with {len(auths)} registry auths")

            except Exception as e:
                print_warning(f"Failed to load Docker config: {e}")

    def login_registry(
        self,
        registry: str,
        username: str,
        password: str,
        email: Optional[str] = None
    ) -> bool:
        """
        Login to a Docker registry.

        Args:
            registry: Registry URL
            username: Username
            password: Password or token
            email: Email address (optional)

        Returns:
            bool: True if login successful
        """
        print_info(f"Logging into registry: {registry}")

        cmd = ["docker", "login"]

        if email:
            cmd.extend(["--email", email])

        cmd.extend(["-u", username, "-p", password, registry])

        try:
            result = run_command(' '.join(cmd))

            if result.returncode == 0:
                # Store auth config
                auth_string = base64.b64encode(f"{username}:{password}".encode()).decode()
                self.auth_configs[registry] = {
                    "username": username,
                    "password": password,
                    "auth": auth_string
                }
                if email:
                    self.auth_configs[registry]["email"] = email

                print_success(f"Successfully logged into {registry}")
                return True
            else:
                print_error(f"Failed to login to registry: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error logging into registry: {e}")
            return False

    def logout_registry(self, registry: str) -> bool:
        """
        Logout from a Docker registry.

        Args:
            registry: Registry URL

        Returns:
            bool: True if logout successful
        """
        print_info(f"Logging out from registry: {registry}")

        try:
            result = run_command(f"docker logout {registry}")

            if result.returncode == 0:
                # Remove auth config
                if registry in self.auth_configs:
                    del self.auth_configs[registry]

                print_success(f"Successfully logged out from {registry}")
                return True
            else:
                print_error(f"Failed to logout from registry: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error logging out from registry: {e}")
            return False

    def push_image(
        self,
        image: str,
        registry: Optional[str] = None,
        tag: Optional[str] = None
    ) -> bool:
        """
        Push an image to registry.

        Args:
            image: Image name
            registry: Target registry (uses default if None)
            tag: Image tag (uses latest if None)

        Returns:
            bool: True if push successful
        """
        if registry is None:
            registry = self.default_registry

        if tag is None:
            tag = "latest"

        # Build full image name
        if registry == "docker.io":
            full_image = f"{image}:{tag}"
        else:
            full_image = f"{registry}/{image}:{tag}"

        print_info(f"Pushing image: {full_image}")

        try:
            result = run_command(f"docker push {full_image}", timeout=300)

            if result.returncode == 0:
                print_success(f"Successfully pushed {full_image}")
                return True
            else:
                print_error(f"Failed to push image: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error pushing image: {e}")
            return False

    def pull_image(
        self,
        image: str,
        registry: Optional[str] = None,
        tag: Optional[str] = None
    ) -> bool:
        """
        Pull an image from registry.

        Args:
            image: Image name
            registry: Source registry (uses default if None)
            tag: Image tag (uses latest if None)

        Returns:
            bool: True if pull successful
        """
        if registry is None:
            registry = self.default_registry

        if tag is None:
            tag = "latest"

        # Build full image name
        if registry == "docker.io":
            full_image = f"{image}:{tag}"
        else:
            full_image = f"{registry}/{image}:{tag}"

        print_info(f"Pulling image: {full_image}")

        try:
            result = run_command(f"docker pull {full_image}", timeout=300)

            if result.returncode == 0:
                print_success(f"Successfully pulled {full_image}")
                return True
            else:
                print_error(f"Failed to pull image: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error pulling image: {e}")
            return False

    def tag_for_registry(
        self,
        source_image: str,
        target_image: str,
        registry: Optional[str] = None,
        tag: Optional[str] = None
    ) -> bool:
        """
        Tag an image for registry push.

        Args:
            source_image: Source image name
            target_image: Target image name
            registry: Target registry
            tag: Target tag

        Returns:
            bool: True if tagging successful
        """
        if registry is None:
            registry = self.default_registry

        if tag is None:
            tag = "latest"

        # Build target image name
        if registry == "docker.io":
            full_target = f"{target_image}:{tag}"
        else:
            full_target = f"{registry}/{target_image}:{tag}"

        print_info(f"Tagging image: {source_image} -> {full_target}")

        try:
            result = run_command(f"docker tag {source_image} {full_target}")

            if result.returncode == 0:
                print_success(f"Successfully tagged image: {full_target}")
                return True
            else:
                print_error(f"Failed to tag image: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error tagging image: {e}")
            return False

    def list_registry_catalog(self, registry: str) -> Optional[List[str]]:
        """
        List repositories in a registry.

        Args:
            registry: Registry URL

        Returns:
            Optional[List[str]]: List of repositories or None if failed
        """
        print_info(f"Listing catalog for registry: {registry}")

        # This requires direct API access to the registry
        # For now, we'll use a simpler approach with docker search
        # In a full implementation, you'd use the Docker Registry HTTP API

        try:
            # For Docker Hub, we can use docker search
            if registry in ["docker.io", "index.docker.io"]:
                print_warning("Use 'docker search <term>' for Docker Hub catalog")
                return None

            # For other registries, this would require HTTP API calls
            print_warning("Registry catalog listing requires direct API access")
            return None

        except Exception as e:
            print_error(f"Error listing registry catalog: {e}")
            return None

    def get_image_tags(self, image: str, registry: Optional[str] = None) -> Optional[List[str]]:
        """
        Get available tags for an image.

        Args:
            image: Image name
            registry: Registry URL

        Returns:
            Optional[List[str]]: List of tags or None if failed
        """
        if registry is None:
            registry = self.default_registry

        print_info(f"Getting tags for image: {registry}/{image}")

        # This would typically require registry API access
        # For now, return None and suggest manual checking
        print_warning("Image tag listing requires registry API access")
        return None

    def start_local_registry(
        self,
        port: int = 5000,
        volume: Optional[str] = None,
        container_name: str = "local-registry"
    ) -> bool:
        """
        Start a local Docker registry.

        Args:
            port: Registry port
            volume: Volume for registry data
            container_name: Registry container name

        Returns:
            bool: True if registry started successfully
        """
        print_info(f"Starting local registry on port {port}")

        cmd = ["docker", "run", "-d"]

        # Container name
        cmd.extend(["--name", container_name])

        # Port mapping
        cmd.extend(["-p", f"{port}:5000"])

        # Volume mapping
        if volume:
            cmd.extend(["-v", f"{volume}:/var/lib/registry"])

        # Restart policy
        cmd.extend(["--restart", "unless-stopped"])

        # Registry image
        cmd.append("registry:2")

        try:
            result = run_command(' '.join(cmd))

            if result.returncode == 0:
                registry_url = f"localhost:{port}"
                print_success(f"Local registry started at {registry_url}")

                # Wait a moment for registry to be ready
                import time
                time.sleep(2)

                return True
            else:
                print_error(f"Failed to start local registry: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error starting local registry: {e}")
            return False

    def stop_local_registry(self, container_name: str = "local-registry") -> bool:
        """
        Stop the local Docker registry.

        Args:
            container_name: Registry container name

        Returns:
            bool: True if registry stopped successfully
        """
        print_info(f"Stopping local registry: {container_name}")

        try:
            # Stop container
            result = run_command(f"docker stop {container_name}")

            if result.returncode == 0:
                # Remove container
                run_command(f"docker rm {container_name}")
                print_success("Local registry stopped and removed")
                return True
            else:
                print_error(f"Failed to stop local registry: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error stopping local registry: {e}")
            return False

    def test_registry_connection(self, registry: str) -> bool:
        """
        Test connection to a registry.

        Args:
            registry: Registry URL

        Returns:
            bool: True if connection successful
        """
        print_info(f"Testing connection to registry: {registry}")

        try:
            # Try to pull a minimal image to test connectivity
            test_image = "hello-world:latest"
            if registry != "docker.io":
                test_image = f"{registry}/{test_image}"

            result = run_command(f"docker pull {test_image}", timeout=30)

            if result.returncode == 0:
                print_success(f"Registry connection successful: {registry}")
                # Clean up test image
                run_command(f"docker rmi {test_image}")
                return True
            else:
                print_error(f"Registry connection failed: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error testing registry connection: {e}")
            return False

    def get_registry_info(self) -> Dict[str, Any]:
        """
        Get information about configured registries.

        Returns:
            Dict[str, Any]: Registry information
        """
        return {
            'default_registry': self.default_registry,
            'configured_auths': list(self.auth_configs.keys()),
            'auth_count': len(self.auth_configs)
        }

    def cleanup_auth_configs(self) -> None:
        """Clear all stored authentication configurations."""
        self.auth_configs.clear()
        print_info("Cleared all registry authentication configurations")
