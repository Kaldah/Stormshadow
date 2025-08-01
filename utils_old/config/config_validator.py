"""
Configuration validator for StormShadow.

This module provides validation utilities for configuration objects,
ensuring they meet required criteria and have valid values.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple

from ..core import print_error, print_warning, print_info, file_exists
from .config_types import BaseConfig, LabConfig, AttackConfig, DockerConfig, NetworkConfig


class ValidationError(Exception):
    """Custom exception for configuration validation errors."""
    pass


class ConfigValidator:
    """
    Configuration validator with comprehensive validation rules.

    Validates configurations for:
    - Required fields
    - Value ranges and formats
    - Network configurations
    - Docker configurations
    - File and directory paths
    """

    def __init__(self):
        """Initialize configuration validator."""
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_lab_config(self, config: LabConfig) -> bool:
        """
        Validate lab configuration.

        Args:
            config: Lab configuration to validate

        Returns:
            bool: True if valid, False otherwise
        """
        self._reset_validation_state()
        print_info("Validating lab configuration...")

        # Validate base configuration
        self._validate_base_config(config)

        # Validate lab-specific fields
        self._validate_lab_name(config.lab_name)
        self._validate_lab_type(config.lab_type)

        # Validate docker configuration
        if config.docker:
            self._validate_docker_config(config.docker)

        # Validate network configuration
        if config.network:
            self._validate_network_config(config.network)

        # Report validation results
        return self._report_validation_results()

    def validate_attack_config(self, config: AttackConfig) -> bool:
        """
        Validate attack configuration.

        Args:
            config: Attack configuration to validate

        Returns:
            bool: True if valid, False otherwise
        """
        self._reset_validation_state()
        print_info("Validating attack configuration...")

        # Validate base configuration
        self._validate_base_config(config)

        # Validate attack-specific fields
        self._validate_attack_type(config.attack_type)
        self._validate_attack_parameters(config.parameters)

        # Validate target configuration
        self._validate_target_config(config)

        # Report validation results
        return self._report_validation_results()

    def _reset_validation_state(self) -> None:
        """Reset validation state for new validation."""
        self.errors.clear()
        self.warnings.clear()

    def _validate_base_config(self, config: BaseConfig) -> None:
        """
        Validate base configuration fields.

        Args:
            config: Configuration to validate
        """
        # Validate name
        if not config.name or not config.name.strip():
            self.errors.append("Configuration name is required")
        elif not self._is_valid_name(config.name):
            self.errors.append(f"Invalid configuration name: {config.name}")

        # Validate version
        if config.version and not self._is_valid_version(config.version):
            self.warnings.append(f"Invalid version format: {config.version}")

        # Validate paths
        if config.working_directory:
            self._validate_path(config.working_directory, "working_directory")

        if config.log_directory:
            self._validate_path(config.log_directory, "log_directory", create_if_missing=True)

    def _validate_lab_name(self, lab_name: Optional[str]) -> None:
        """
        Validate lab name.

        Args:
            lab_name: Lab name to validate
        """
        if not lab_name:
            self.errors.append("Lab name is required")
            return

        if not self._is_valid_name(lab_name):
            self.errors.append(f"Invalid lab name: {lab_name}")

    def _validate_lab_type(self, lab_type: Optional[str]) -> None:
        """
        Validate lab type.

        Args:
            lab_type: Lab type to validate
        """
        valid_lab_types = ["sip", "network", "custom", "default"]

        if not lab_type:
            self.warnings.append("Lab type not specified, using 'default'")
            return

        if lab_type not in valid_lab_types:
            self.warnings.append(f"Unknown lab type: {lab_type}. Valid types: {valid_lab_types}")

    def _validate_attack_type(self, attack_type: Optional[str]) -> None:
        """
        Validate attack type.

        Args:
            attack_type: Attack type to validate
        """
        valid_attack_types = ["inviteflood", "basic", "dos", "custom"]

        if not attack_type:
            self.errors.append("Attack type is required")
            return

        if attack_type not in valid_attack_types:
            self.warnings.append(f"Unknown attack type: {attack_type}. Valid types: {valid_attack_types}")

    def _validate_attack_parameters(self, parameters: Optional[Dict[str, Any]]) -> None:
        """
        Validate attack parameters.

        Args:
            parameters: Attack parameters to validate
        """
        if not parameters:
            self.warnings.append("No attack parameters specified")
            return

        # Validate common parameters
        if "duration" in parameters:
            duration = parameters["duration"]
            if not isinstance(duration, (int, float)) or duration <= 0:
                self.errors.append("Attack duration must be a positive number")

        if "rate" in parameters:
            rate = parameters["rate"]
            if not isinstance(rate, (int, float)) or rate <= 0:
                self.errors.append("Attack rate must be a positive number")

        if "target_count" in parameters:
            count = parameters["target_count"]
            if not isinstance(count, int) or count <= 0:
                self.errors.append("Target count must be a positive integer")

    def _validate_target_config(self, config: AttackConfig) -> None:
        """
        Validate target configuration.

        Args:
            config: Attack configuration with target info
        """
        # Validate target host
        if hasattr(config, 'target_host') and config.target_host:
            if not self._is_valid_ip_or_hostname(config.target_host):
                self.errors.append(f"Invalid target host: {config.target_host}")

        # Validate target port
        if hasattr(config, 'target_port') and config.target_port:
            if not self._is_valid_port(config.target_port):
                self.errors.append(f"Invalid target port: {config.target_port}")

    def _validate_docker_config(self, docker_config: DockerConfig) -> None:
        """
        Validate Docker configuration.

        Args:
            docker_config: Docker configuration to validate
        """
        # Validate image name
        if not docker_config.image_name:
            self.errors.append("Docker image name is required")
        elif not self._is_valid_docker_image(docker_config.image_name):
            self.errors.append(f"Invalid Docker image name: {docker_config.image_name}")

        # Validate container name
        if docker_config.container_name and not self._is_valid_container_name(docker_config.container_name):
            self.errors.append(f"Invalid container name: {docker_config.container_name}")

        # Validate ports
        for port_mapping in docker_config.port_mappings:
            if not self._is_valid_port_mapping(port_mapping):
                self.errors.append(f"Invalid port mapping: {port_mapping}")

        # Validate volumes
        for volume in docker_config.volumes:
            if not self._is_valid_volume_mapping(volume):
                self.errors.append(f"Invalid volume mapping: {volume}")

        # Validate environment variables
        for env_var in docker_config.environment:
            if not self._is_valid_env_var(env_var):
                self.warnings.append(f"Potentially invalid environment variable: {env_var}")

    def _validate_network_config(self, network_config: NetworkConfig) -> None:
        """
        Validate network configuration.

        Args:
            network_config: Network configuration to validate
        """
        # Validate network name
        if network_config.network_name and not self._is_valid_network_name(network_config.network_name):
            self.errors.append(f"Invalid network name: {network_config.network_name}")

        # Validate subnet
        if network_config.subnet and not self._is_valid_subnet(network_config.subnet):
            self.errors.append(f"Invalid subnet: {network_config.subnet}")

        # Validate gateway
        if network_config.gateway and not self._is_valid_ip_address(network_config.gateway):
            self.errors.append(f"Invalid gateway IP: {network_config.gateway}")

        # Validate IP range
        if network_config.ip_range and not self._is_valid_ip_range(network_config.ip_range):
            self.errors.append(f"Invalid IP range: {network_config.ip_range}")

    def _validate_path(self, path: str, field_name: str, create_if_missing: bool = False) -> None:
        """
        Validate file system path.

        Args:
            path: Path to validate
            field_name: Name of the field being validated
            create_if_missing: Whether to create missing directories
        """
        path_obj = Path(path)

        if not path_obj.exists():
            if create_if_missing:
                try:
                    path_obj.mkdir(parents=True, exist_ok=True)
                    self.warnings.append(f"Created missing directory: {path}")
                except Exception as e:
                    self.errors.append(f"Cannot create {field_name} directory: {path} ({e})")
            else:
                self.warnings.append(f"{field_name} path does not exist: {path}")

        elif not path_obj.is_dir():
            self.errors.append(f"{field_name} must be a directory: {path}")

    def _is_valid_name(self, name: str) -> bool:
        """Check if name is valid (alphanumeric, hyphens, underscores)."""
        return bool(re.match(r'^[a-zA-Z0-9_-]+$', name))

    def _is_valid_version(self, version: str) -> bool:
        """Check if version follows semantic versioning."""
        return bool(re.match(r'^\d+\.\d+(\.\d+)?(-\w+)?$', version))

    def _is_valid_ip_address(self, ip: str) -> bool:
        """Check if string is a valid IP address."""
        try:
            parts = ip.split('.')
            return len(parts) == 4 and all(0 <= int(part) <= 255 for part in parts)
        except (ValueError, AttributeError):
            return False

    def _is_valid_ip_or_hostname(self, host: str) -> bool:
        """Check if string is a valid IP address or hostname."""
        # Check IP address
        if self._is_valid_ip_address(host):
            return True

        # Check hostname
        hostname_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$'
        return bool(re.match(hostname_pattern, host))

    def _is_valid_port(self, port: Union[int, str]) -> bool:
        """Check if port number is valid."""
        try:
            port_num = int(port)
            return 1 <= port_num <= 65535
        except (ValueError, TypeError):
            return False

    def _is_valid_subnet(self, subnet: str) -> bool:
        """Check if subnet is valid CIDR notation."""
        try:
            ip, prefix = subnet.split('/')
            return self._is_valid_ip_address(ip) and 0 <= int(prefix) <= 32
        except (ValueError, AttributeError):
            return False

    def _is_valid_ip_range(self, ip_range: str) -> bool:
        """Check if IP range is valid."""
        if '-' in ip_range:
            # Range format: "192.168.1.10-192.168.1.20"
            try:
                start_ip, end_ip = ip_range.split('-')
                return self._is_valid_ip_address(start_ip.strip()) and self._is_valid_ip_address(end_ip.strip())
            except ValueError:
                return False
        else:
            # Single IP or CIDR
            return self._is_valid_ip_address(ip_range) or self._is_valid_subnet(ip_range)

    def _is_valid_docker_image(self, image: str) -> bool:
        """Check if Docker image name is valid."""
        # Basic Docker image name validation
        image_pattern = r'^[a-z0-9]+([._-][a-z0-9]+)*(/[a-z0-9]+([._-][a-z0-9]+)*)*(:[a-zA-Z0-9._-]+)?$'
        return bool(re.match(image_pattern, image.lower()))

    def _is_valid_container_name(self, name: str) -> bool:
        """Check if container name is valid."""
        # Docker container names: alphanumeric, hyphens, underscores
        return bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$', name))

    def _is_valid_network_name(self, name: str) -> bool:
        """Check if Docker network name is valid."""
        return bool(re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$', name))

    def _is_valid_port_mapping(self, mapping: str) -> bool:
        """Check if port mapping is valid (e.g., "8080:80")."""
        try:
            if ':' in mapping:
                host_port, container_port = mapping.split(':')
                return self._is_valid_port(host_port) and self._is_valid_port(container_port)
            else:
                return self._is_valid_port(mapping)
        except ValueError:
            return False

    def _is_valid_volume_mapping(self, mapping: str) -> bool:
        """Check if volume mapping is valid."""
        if ':' not in mapping:
            return False

        parts = mapping.split(':')
        if len(parts) < 2:
            return False

        # Basic validation - host path should be absolute
        host_path = parts[0]
        return host_path.startswith('/') or (len(host_path) > 1 and host_path[1] == ':')

    def _is_valid_env_var(self, env_var: str) -> bool:
        """Check if environment variable is valid."""
        if '=' not in env_var:
            return False

        name, _ = env_var.split('=', 1)
        return bool(re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name))

    def _report_validation_results(self) -> bool:
        """
        Report validation results.

        Returns:
            bool: True if no errors, False otherwise
        """
        # Report warnings
        for warning in self.warnings:
            print_warning(f"Validation warning: {warning}")

        # Report errors
        for error in self.errors:
            print_error(f"Validation error: {error}")

        # Return validation status
        is_valid = len(self.errors) == 0

        if is_valid:
            print_info("Configuration validation passed")
        else:
            print_error(f"Configuration validation failed with {len(self.errors)} error(s)")

        return is_valid

    def get_validation_summary(self) -> Dict[str, Any]:
        """
        Get validation summary.

        Returns:
            Dict[str, Any]: Validation summary with errors and warnings
        """
        return {
            'valid': len(self.errors) == 0,
            'error_count': len(self.errors),
            'warning_count': len(self.warnings),
            'errors': self.errors.copy(),
            'warnings': self.warnings.copy()
        }
