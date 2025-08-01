"""
Configuration manager for StormShadow.

This module provides a unified configuration management interface
with precedence handling and validation.
"""

from typing import Dict, Any, Optional, Union, List
from pathlib import Path

from .config_loader import ConfigLoader
from .config_validator import ConfigValidator
from .config_types import BaseConfig, LabConfig, AttackConfig


class ConfigManager:
    """
    Unified configuration manager with precedence handling.

    Manages configuration loading with proper precedence:
    1. Default configuration
    2. Local configuration files
    3. Command line overrides
    """

    def __init__(self, config_type: str = "base"):
        """
        Initialize configuration manager.

        Args:
            config_type: Type of configuration (base, lab, attack)
        """
        self.config_type = config_type
        self.loader = ConfigLoader()
        self.validator = ConfigValidator()
        self.config: Dict[str, Any] = {}
        self.sources: List[str] = []

    def load_default_config(self, config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """
        Load default configuration.

        Args:
            config_path: Path to default config file

        Returns:
            Dict[str, Any]: Default configuration
        """
        if config_path is None:
            # Use built-in defaults based on type
            if self.config_type == "lab":
                config_path = Path(__file__).parent.parent / "default-configs" / "default-lab.toml"
            elif self.config_type == "attack":
                config_path = Path(__file__).parent.parent / "default-configs" / "default-attack.toml"
            else:
                config_path = Path(__file__).parent.parent / "default-configs" / "stormshadow.toml"

        if Path(config_path).exists():
            self.config = self.loader.load_config(config_path)
            self.sources.append(f"default:{config_path}")

        return self.config

    def load_local_config(self, local_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load and merge local configuration.

        Args:
            local_path: Path to local config file

        Returns:
            Dict[str, Any]: Merged configuration
        """
        if Path(local_path).exists():
            local_config = self.loader.load_config(local_path)
            self.config = self._merge_configs(self.config, local_config)
            self.sources.append(f"local:{local_path}")

        return self.config

    def apply_overrides(self, overrides: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply command line or runtime overrides.

        Args:
            overrides: Override configuration values

        Returns:
            Dict[str, Any]: Final configuration
        """
        if overrides:
            self.config = self._merge_configs(self.config, overrides)
            self.sources.append("overrides:runtime")

        return self.config

    def validate_config(self) -> bool:
        """
        Validate the current configuration.

        Returns:
            bool: True if configuration is valid
        """
        return self.validator.validate_config(self.config, self.config_type)

    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return self.config.copy()

    def get_sources(self) -> List[str]:
        """Get list of configuration sources in load order."""
        return self.sources.copy()

    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries.

        Args:
            base: Base configuration
            override: Override configuration

        Returns:
            Dict[str, Any]: Merged configuration
        """
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value

        return result


def load_config(
    config_path: Union[str, Path],
    config_type: str = "base",
    local_config: Optional[Union[str, Path]] = None,
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Convenience function for loading configuration with precedence.

    Args:
        config_path: Path to default configuration
        config_type: Type of configuration
        local_config: Optional local configuration path
        overrides: Optional runtime overrides

    Returns:
        Dict[str, Any]: Final configuration
    """
    manager = ConfigManager(config_type)

    # Load default config
    manager.load_default_config(config_path)

    # Load local config if provided
    if local_config:
        manager.load_local_config(local_config)

    # Apply overrides if provided
    if overrides:
        manager.apply_overrides(overrides)

    return manager.get_config()


def validate_config(config: Dict[str, Any], config_type: str = "base") -> bool:
    """
    Convenience function for configuration validation.

    Args:
        config: Configuration to validate
        config_type: Type of configuration

    Returns:
        bool: True if configuration is valid
    """
    validator = ConfigValidator()
    return validator.validate_config(config, config_type)
