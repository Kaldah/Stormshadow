"""
Configuration loader for StormShadow.

This module handles loading configurations from various sources with proper precedence:
1. Default configuration
2. Local configuration (lab/attack folder)
3. Command line parameters
"""

import json
import yaml
try:
    import tomllib  # Python 3.11+
    TOMLLIB_AVAILABLE = True
except ImportError:
    TOMLLIB_AVAILABLE = False
    tomllib = None

try:
    import toml
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False
    toml = None
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from ..core import print_error, print_warning, print_info, file_exists
from .config_types import BaseConfig, LabConfig, AttackConfig


class ConfigLoader:
    """
    Configuration loader with precedence support.

    Loads configurations in the following order:
    1. Default configuration
    2. Local configuration files
    3. Command line overrides
    """

    def __init__(self, default_config_dir: Optional[str] = None):
        """
        Initialize configuration loader.

        Args:
            default_config_dir: Directory containing default configurations
        """
        self.default_config_dir = Path(default_config_dir) if default_config_dir else None
        self.supported_formats = ['.toml', '.yaml', '.yml', '.json']

    def load_config(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from a file.

        Args:
            config_path: Path to configuration file

        Returns:
            Dict[str, Any]: Configuration data
        """
        return self._load_config_file(Path(config_path))

    def load_lab_config(
        self,
        lab_path: Optional[str] = None,
        config_name: str = "lab",
        cli_overrides: Optional[Dict[str, Any]] = None
    ) -> LabConfig:
        """
        Load lab configuration with proper precedence.

        Args:
            lab_path: Path to lab directory
            config_name: Base name for config files
            cli_overrides: Command line parameter overrides

        Returns:
            LabConfig: Merged configuration
        """
        print_info("Loading lab configuration...")

        # 1. Load default configuration
        default_config = self._load_default_config("lab")

        # 2. Load local configuration
        local_config = self._load_local_config(lab_path, config_name)

        # 3. Apply CLI overrides
        final_config = self._apply_cli_overrides(
            self._merge_configs(default_config, local_config),
            cli_overrides or {}
        )

        # Convert to LabConfig
        return self._dict_to_lab_config(final_config)

    def load_attack_config(
        self,
        attack_path: Optional[str] = None,
        config_name: str = "attack",
        cli_overrides: Optional[Dict[str, Any]] = None
    ) -> AttackConfig:
        """
        Load attack configuration with proper precedence.

        Args:
            attack_path: Path to attack directory
            config_name: Base name for config files
            cli_overrides: Command line parameter overrides

        Returns:
            AttackConfig: Merged configuration
        """
        print_info("Loading attack configuration...")

        # 1. Load default configuration
        default_config = self._load_default_config("attack")

        # 2. Load local configuration
        local_config = self._load_local_config(attack_path, config_name)

        # 3. Apply CLI overrides
        final_config = self._apply_cli_overrides(
            self._merge_configs(default_config, local_config),
            cli_overrides or {}
        )

        # Convert to AttackConfig
        return self._dict_to_attack_config(final_config)

    def _load_default_config(self, config_type: str) -> Dict[str, Any]:
        """
        Load default configuration for a given type.

        Args:
            config_type: Type of configuration ("lab" or "attack")

        Returns:
            Dict[str, Any]: Default configuration
        """
        if not self.default_config_dir:
            print_warning("No default config directory specified")
            return {}

        # Try different file formats
        for ext in self.supported_formats:
            config_file = self.default_config_dir / f"default-{config_type}{ext}"
            if file_exists(config_file):
                print_info(f"Loading default config: {config_file}")
                return self._load_config_file(config_file)

        print_warning(f"No default {config_type} configuration found")
        return {}

    def _load_local_config(
        self,
        base_path: Optional[str],
        config_name: str
    ) -> Dict[str, Any]:
        """
        Load local configuration from specified path.

        Args:
            base_path: Base directory to search for config
            config_name: Base name for config files

        Returns:
            Dict[str, Any]: Local configuration
        """
        if not base_path:
            return {}

        base_dir = Path(base_path)
        if not base_dir.exists():
            print_warning(f"Local config path does not exist: {base_path}")
            return {}

        # Try different file formats and names
        config_names = [
            f"local-{config_name}-config",
            f"{config_name}-config",
            f"local-{config_name}",
            config_name
        ]

        for name in config_names:
            for ext in self.supported_formats:
                config_file = base_dir / f"{name}{ext}"
                if file_exists(config_file):
                    print_info(f"Loading local config: {config_file}")
                    return self._load_config_file(config_file)

        print_info(f"No local configuration found in: {base_path}")
        return {}

    def _load_config_file(self, file_path: Path) -> Dict[str, Any]:
        """
        Load configuration from a file based on its extension.

        Args:
            file_path: Path to configuration file

        Returns:
            Dict[str, Any]: Configuration data
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() == '.json':
                    return json.load(f)
                elif file_path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif file_path.suffix.lower() == '.toml':
                    if TOMLLIB_AVAILABLE:
                        # Using built-in tomllib (read binary mode)
                        with open(file_path, 'rb') as f_bin:
                            return tomllib.load(f_bin)
                    elif TOML_AVAILABLE:
                        # Using toml package
                        return toml.load(f)
                    else:
                        print_error("TOML support not available. Install 'toml' package or use Python 3.11+")
                        return {}
                else:
                    print_error(f"Unsupported config format: {file_path.suffix}")
                    return {}

        except Exception as e:
            print_error(f"Failed to load config file {file_path}: {e}")
            return {}

    def _merge_configs(
        self,
        base: Dict[str, Any],
        override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries.

        Args:
            base: Base configuration
            override: Override configuration

        Returns:
            Dict[str, Any]: Merged configuration
        """
        if not override:
            return base.copy()

        if not base:
            return override.copy()

        merged = base.copy()
        self._deep_merge_dict(merged, override)
        return merged

    def _deep_merge_dict(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """
        Recursively merge dictionaries.

        Args:
            base: Base dictionary (modified in place)
            override: Override dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge_dict(base[key], value)
            else:
                base[key] = value

    def _apply_cli_overrides(
        self,
        config: Dict[str, Any],
        overrides: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply command line overrides to configuration.

        Args:
            config: Base configuration
            overrides: CLI parameter overrides

        Returns:
            Dict[str, Any]: Configuration with CLI overrides applied
        """
        if not overrides:
            return config

        print_info("Applying command line overrides...")
        final_config = config.copy()

        # Handle nested overrides (e.g., docker.image_name)
        for key, value in overrides.items():
            if '.' in key:
                self._set_nested_value(final_config, key, value)
            else:
                final_config[key] = value

        return final_config

    def _set_nested_value(
        self,
        config: Dict[str, Any],
        key_path: str,
        value: Any
    ) -> None:
        """
        Set a nested value in a configuration dictionary.

        Args:
            config: Configuration dictionary
            key_path: Dot-separated key path (e.g., "docker.image_name")
            value: Value to set
        """
        keys = key_path.split('.')
        current = config

        # Navigate to the parent dictionary
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set the final value
        current[keys[-1]] = value

    def _dict_to_lab_config(self, config_dict: Dict[str, Any]) -> LabConfig:
        """
        Convert dictionary to LabConfig object.

        Args:
            config_dict: Configuration dictionary

        Returns:
            LabConfig: Lab configuration object
        """
        try:
            return LabConfig(**config_dict)
        except Exception as e:
            print_warning(f"Failed to convert to LabConfig: {e}")
            return LabConfig()

    def _dict_to_attack_config(self, config_dict: Dict[str, Any]) -> AttackConfig:
        """
        Convert dictionary to AttackConfig object.

        Args:
            config_dict: Configuration dictionary

        Returns:
            AttackConfig: Attack configuration object
        """
        try:
            return AttackConfig(**config_dict)
        except Exception as e:
            print_warning(f"Failed to convert to AttackConfig: {e}")
            return AttackConfig()

    def save_config(
        self,
        config: Union[LabConfig, AttackConfig, BaseConfig],
        file_path: str,
        format_type: str = "toml"
    ) -> bool:
        """
        Save configuration to file.

        Args:
            config: Configuration object to save
            file_path: Path to save the configuration
            format_type: Format to save in ("toml", "yaml", "json")

        Returns:
            bool: True if save successful
        """
        try:
            config_dict = self._config_to_dict(config)

            with open(file_path, 'w', encoding='utf-8') as f:
                if format_type.lower() == 'json':
                    json.dump(config_dict, f, indent=2)
                elif format_type.lower() in ['yaml', 'yml']:
                    yaml.dump(config_dict, f, default_flow_style=False)
                elif format_type.lower() == 'toml':
                    if TOML_AVAILABLE and toml:
                        toml.dump(config_dict, f)
                    else:
                        print_error("TOML support not available for writing. Install 'toml' package.")
                        return False
                else:
                    print_error(f"Unsupported format: {format_type}")
                    return False

            print_info(f"Configuration saved to: {file_path}")
            return True

        except Exception as e:
            print_error(f"Failed to save configuration: {e}")
            return False

    def _config_to_dict(self, config: BaseConfig) -> Dict[str, Any]:
        """
        Convert configuration object to dictionary.

        Args:
            config: Configuration object

        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        if hasattr(config, '__dict__'):
            result = {}
            for key, value in config.__dict__.items():
                if hasattr(value, '__dict__'):
                    result[key] = self._config_to_dict(value)
                else:
                    result[key] = value
            return result
        return {}

    def list_available_configs(self, config_type: str) -> List[str]:
        """
        List available configuration files of a given type.

        Args:
            config_type: Type of configuration to list

        Returns:
            List[str]: List of available configuration files
        """
        configs = []

        if self.default_config_dir and self.default_config_dir.exists():
            for ext in self.supported_formats:
                pattern = f"*{config_type}*{ext}"
                configs.extend([
                    str(f.name) for f in self.default_config_dir.glob(pattern)
                ])

        return sorted(configs)
