"""
Image manager for Docker operations.

This module provides Docker image management functionality
including building, pulling, pushing, and cleanup.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..core import (
    print_error, print_warning, print_info, print_success, run_command
)


class ImageManager:
    """
    Manages Docker image operations.

    Provides methods for:
    - Image building from Dockerfile
    - Image pulling and pushing
    - Image inspection and management
    - Image cleanup and pruning
    """

    def __init__(self):
        """Initialize image manager."""
        self.built_images: List[str] = []  # Track built images

    def build_image(
        self,
        image_name: str,
        dockerfile_path: str,
        build_context: Optional[str] = None,
        build_args: Optional[Dict[str, str]] = None,
        labels: Optional[Dict[str, str]] = None,
        no_cache: bool = False,
        pull: bool = False,
        quiet: bool = False
    ) -> bool:
        """
        Build a Docker image from Dockerfile.

        Args:
            image_name: Name and tag for the image
            dockerfile_path: Path to Dockerfile
            build_context: Build context directory
                (defaults to dockerfile directory)
            build_args: Build arguments
            labels: Image labels
            no_cache: Disable build cache
            pull: Always pull base images
            quiet: Suppress build output

        Returns:
            bool: True if build successful
        """
        dockerfile = Path(dockerfile_path)
        if not dockerfile.exists():
            print_error(f"Dockerfile not found: {dockerfile_path}")
            return False

        # Use dockerfile directory as build context if not specified
        if build_context is None:
            build_context = str(dockerfile.parent)

        cmd = ["docker", "build"]

        # Build options
        if no_cache:
            cmd.append("--no-cache")
        if pull:
            cmd.append("--pull")
        if quiet:
            cmd.append("--quiet")

        # Dockerfile path
        cmd.extend(["-f", str(dockerfile)])

        # Build arguments
        if build_args:
            for key, value in build_args.items():
                cmd.extend(["--build-arg", f"{key}={value}"])

        # Labels
        if labels:
            for key, value in labels.items():
                cmd.extend(["--label", f"{key}={value}"])

        # Image tag
        cmd.extend(["-t", image_name])

        # Build context
        cmd.append(build_context)

        print_info(f"Building image: {image_name}")
        print_info(f"Using Dockerfile: {dockerfile_path}")
        print_info(f"Build context: {build_context}")

        try:
            result = run_command(
                ' '.join(cmd),
                timeout=300)  # 5 minute timeout

            if result.returncode == 0:
                self.built_images.append(image_name)
                print_success(f"Image built successfully: {image_name}")
                return True
            else:
                print_error(f"Failed to build image: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error building image: {e}")
            return False

    def pull_image(self, image: str, platform: Optional[str] = None) -> bool:
        """
        Pull a Docker image from registry.

        Args:
            image: Image name and tag
            platform: Target platform (e.g., "linux/amd64")

        Returns:
            bool: True if pull successful
        """
        cmd = ["docker", "pull"]

        if platform:
            cmd.extend(["--platform", platform])

        cmd.append(image)

        print_info(f"Pulling image: {image}")

        try:
            result = run_command(' '.join(cmd), timeout=300)

            if result.returncode == 0:
                print_success(f"Image pulled successfully: {image}")
                return True
            else:
                print_error(f"Failed to pull image: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error pulling image: {e}")
            return False

    def push_image(self, image: str) -> bool:
        """
        Push a Docker image to registry.

        Args:
            image: Image name and tag

        Returns:
            bool: True if push successful
        """
        print_info(f"Pushing image: {image}")

        try:
            result = run_command(f"docker push {image}", timeout=300)

            if result.returncode == 0:
                print_success(f"Image pushed successfully: {image}")
                return True
            else:
                print_error(f"Failed to push image: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error pushing image: {e}")
            return False

    def tag_image(self, source: str, target: str) -> bool:
        """
        Tag a Docker image.

        Args:
            source: Source image name
            target: Target image name and tag

        Returns:
            bool: True if tag successful
        """
        print_info(f"Tagging image: {source} -> {target}")

        try:
            result = run_command(f"docker tag {source} {target}")

            if result.returncode == 0:
                print_success(f"Image tagged successfully: {target}")
                return True
            else:
                print_error(f"Failed to tag image: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error tagging image: {e}")
            return False

    def remove_image(self, image: str, force: bool = False) -> bool:
        """
        Remove a Docker image.

        Args:
            image: Image name, tag, or ID
            force: Force removal of image

        Returns:
            bool: True if removal successful
        """
        cmd = ["docker", "rmi"]

        if force:
            cmd.append("-f")

        cmd.append(image)

        print_info(f"Removing image: {image}")

        try:
            result = run_command(' '.join(cmd))

            if result.returncode == 0:
                # Remove from tracking
                if image in self.built_images:
                    self.built_images.remove(image)
                print_success(f"Image removed: {image}")
                return True
            else:
                print_error(f"Failed to remove image: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error removing image: {e}")
            return False

    def image_exists(self, image: str) -> bool:
        """
        Check if image exists locally.

        Args:
            image: Image name, tag, or ID

        Returns:
            bool: True if image exists
        """
        try:
            result = run_command(f"docker image inspect {image}")
            return result.returncode == 0
        except Exception:
            return False

    def get_image_info(self, image: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about an image.

        Args:
            image: Image name, tag, or ID

        Returns:
            Optional[Dict[str, Any]]: Image information or None if failed
        """
        try:
            result = run_command(f"docker image inspect {image}")

            if result.returncode == 0:
                info = json.loads(result.stdout)
                return info[0] if info else None
            else:
                return None

        except Exception as e:
            print_error(f"Error getting image info: {e}")
            return None

    def list_images(self, all_images: bool = False) -> List[Dict[str, str]]:
        """
        List Docker images.

        Args:
            all_images: Include intermediate images

        Returns:
            List[Dict[str, str]]: List of image information
        """
        cmd = [
            'docker',
            'images',
            '--format',
            ('table {{.Repository}}\\t{{.Tag}}\\t{{.ID}}\\t'
             '{{.Size}}\\t{{.CreatedAt}}')]

        if all_images:
            cmd.append('-a')

        try:
            result = run_command(' '.join(cmd))

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                images: List[Dict[str, str]] = []

                for line in lines:
                    if line.strip():
                        parts = line.split('\t')
                        if len(parts) >= 5:
                            images.append({
                                'repository': parts[0],
                                'tag': parts[1],
                                'id': parts[2],
                                'size': parts[3],
                                'created': parts[4]
                            })

                return images
            else:
                print_error(f"Failed to list images: {result.stderr}")
                return []

        except Exception as e:
            print_error(f"Error listing images: {e}")
            return []

    def get_image_history(self, image: str) -> List[Dict[str, str]]:
        """
        Get image build history.

        Args:
            image: Image name, tag, or ID

        Returns:
            List[Dict[str, str]]: List of history entries
        """
        try:
            cmd = ('docker history {} --format '
                   '"table {{.ID}}\\t{{.CreatedBy}}\\t{{.Size}}"'
                   ).format(image)
            result = run_command(cmd)

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                history: List[Dict[str, str]] = []

                for line in lines:
                    if line.strip():
                        parts = line.split('\t', 2)
                        if len(parts) >= 3:
                            history.append({
                                'id': parts[0],
                                'created_by': parts[1],
                                'size': parts[2]
                            })

                return history
            else:
                print_error(f"Failed to get image history: {result.stderr}")
                return []

        except Exception as e:
            print_error(f"Error getting image history: {e}")
            return []

    def prune_images(self, all_images: bool = False) -> bool:
        """
        Remove unused images.

        Args:
            all_images: Remove all unused images, not just dangling ones

        Returns:
            bool: True if pruning successful
        """
        cmd = ["docker", "image", "prune", "-f"]

        if all_images:
            cmd.append("-a")

        print_info("Pruning unused images...")

        try:
            result = run_command(' '.join(cmd))

            if result.returncode == 0:
                print_success("Unused images pruned")
                return True
            else:
                print_error(f"Failed to prune images: {result.stderr}")
                return False

        except Exception as e:
            print_error(f"Error pruning images: {e}")
            return False

    def get_image_size(self, image: str) -> Optional[str]:
        """
        Get the size of an image.

        Args:
            image: Image name, tag, or ID

        Returns:
            Optional[str]: Image size or None if failed
        """
        try:
            result = run_command(
                f'docker image inspect {image} --format "{{{{.Size}}}}"')

            if result.returncode == 0:
                size_bytes = int(result.stdout.strip())

                # Convert to human readable format
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size_bytes < 1024.0:
                        return f"{size_bytes:.1f}{unit}"
                    size_bytes /= 1024.0

                return f"{size_bytes:.1f}TB"
            else:
                return None

        except Exception as e:
            print_error(f"Error getting image size: {e}")
            return None

    def cleanup_built_images(self, force: bool = False) -> bool:
        """
        Clean up all images built by this manager.

        Args:
            force: Force removal of images

        Returns:
            bool: True if cleanup successful
        """
        print_info("Cleaning up all built images...")

        success = True
        for image in list(self.built_images):
            if self.image_exists(image):
                if not self.remove_image(image, force=force):
                    success = False

        if success:
            self.built_images.clear()
            print_success("All built images cleaned up successfully")
        else:
            print_warning("Some images could not be cleaned up")

        return success
