"""
Configuration type definitions for StormShadow.

This module defines the data structures for different configuration types.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from pathlib import Path


@dataclass
class DockerConfig:
    """Docker-specific configuration."""
    image_name: str = "asterisk-sip-server"
    container_name: str = "sip-victim"
    network_mode: str = "host"
    capabilities: List[str] = field(default_factory=lambda: ["NET_ADMIN", "NET_RAW"])
    volumes: Dict[str, str] = field(default_factory=dict)
    environment: Dict[str, str] = field(default_factory=dict)
    ports: Dict[str, str] = field(default_factory=dict)
    detached: bool = False
    auto_remove: bool = True
    privileged: bool = False
    restart_policy: str = "no"


@dataclass
class NetworkConfig:
    """Network-specific configuration."""
    interface: str = "any"
    capture_filter: str = ""
    iptables_rules: List[str] = field(default_factory=list)
    spoofing_enabled: bool = False
    source_ip: str = ""
    target_ip: str = ""
    target_port: int = 5060
    protocol: str = "udp"


@dataclass
class BaseConfig:
    """Base configuration shared across all components."""
    name: str = ""
    description: str = ""
    author: str = ""
    version: str = "1.0.0"

    # Logging configuration
    log_level: str = "INFO"
    log_file: Optional[str] = None

    # Output configuration
    output_dir: str = "output"
    save_pcap: bool = True
    save_logs: bool = True

    # Terminal configuration
    run_in_terminal: bool = False
    terminal_title: str = ""

    # Timing configuration
    timeout: int = 300  # 5 minutes default
    delay: float = 0.0

    # Docker configuration
    docker: DockerConfig = field(default_factory=DockerConfig)

    # Network configuration
    network: NetworkConfig = field(default_factory=NetworkConfig)


@dataclass
class LabConfig(BaseConfig):
    """Configuration for lab environments."""
    lab_type: str = "sip"

    # Container configuration
    containers: List[DockerConfig] = field(default_factory=list)

    # Lab-specific settings
    victim_image: str = "asterisk-sip-server"
    victim_container: str = "sip-victim"
    scripts_dir: str = "./scripts"
    setup_script: Optional[str] = None
    cleanup_script: Optional[str] = None

    # Multiple victim support
    multi_victim: bool = False
    victim_count: int = 1
    victim_prefix: str = "victim-"

    # Network setup
    create_network: bool = False
    network_name: str = "stormshadow-lab"
    subnet: str = "172.20.0.0/16"

    # Health checks
    health_check_enabled: bool = True
    health_check_command: List[str] = field(
        default_factory=lambda: ["asterisk", "-rx", "core show version"]
    )
    health_check_timeout: int = 30


@dataclass
class AttackConfig(BaseConfig):
    """Configuration for attack algorithms."""
    attack_type: str = ""
    target_host: str = "127.0.0.1"
    target_port: int = 5060

    # Attack parameters
    rate: float = 1.0  # requests per second
    duration: int = 60  # seconds
    threads: int = 1

    # SIP-specific parameters
    from_user: str = "attacker"
    to_user: str = "victim"
    call_id_prefix: str = "stormshadow"
    user_agent: str = "StormShadow/1.0"

    # Authentication
    auth_user: str = ""
    auth_password: str = ""

    # Payload configuration
    payload_file: Optional[str] = None
    custom_headers: Dict[str, str] = field(default_factory=dict)

    # Metrics and monitoring
    capture_traffic: bool = True
    capture_interface: str = "any"
    capture_filter: str = "udp port 5060"

    # Output and reporting
    real_time_stats: bool = True
    stats_interval: int = 5  # seconds
    generate_report: bool = True
    report_format: str = "html"


def merge_configs(*configs: BaseConfig) -> BaseConfig:
    """
    Merge multiple configurations with later configs taking precedence.

    Args:
        *configs: Configuration objects to merge

    Returns:
        BaseConfig: Merged configuration
    """
    if not configs:
        return BaseConfig()

    # Start with the first config
    merged = configs[0]

    # Merge each subsequent config
    for config in configs[1:]:
        merged = _merge_two_configs(merged, config)

    return merged


def _merge_two_configs(base: BaseConfig, override: BaseConfig) -> BaseConfig:
    """
    Merge two configuration objects.

    Args:
        base: Base configuration
        override: Override configuration

    Returns:
        BaseConfig: Merged configuration
    """
    # Create a copy of the base config
    merged_dict = _config_to_dict(base)
    override_dict = _config_to_dict(override)

    # Recursively merge dictionaries
    _deep_merge_dict(merged_dict, override_dict)

    # Convert back to config object
    return _dict_to_config(merged_dict, type(base))


def _config_to_dict(config: BaseConfig) -> Dict[str, Any]:
    """Convert config object to dictionary."""
    if hasattr(config, '__dict__'):
        result = {}
        for key, value in config.__dict__.items():
            if hasattr(value, '__dict__'):
                result[key] = _config_to_dict(value)
            else:
                result[key] = value
        return result
    return config


def _dict_to_config(data: Dict[str, Any], config_type: type) -> BaseConfig:
    """Convert dictionary back to config object."""
    # This is a simplified implementation
    # In practice, you might want to use a more robust serialization library
    try:
        return config_type(**data)
    except Exception:
        # Fallback to base config if conversion fails
        return BaseConfig()


def _deep_merge_dict(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    """
    Recursively merge two dictionaries.

    Args:
        base: Base dictionary (modified in place)
        override: Override dictionary
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge_dict(base[key], value)
        else:
            base[key] = value


def create_default_lab_config() -> LabConfig:
    """Create a default lab configuration."""
    return LabConfig(
        name="Default SIP Lab",
        description="Default SIP testing environment",
        lab_type="sip",
        victim_image="asterisk-sip-server",
        victim_container="sip-victim"
    )


def create_default_attack_config() -> AttackConfig:
    """Create a default attack configuration."""
    return AttackConfig(
        name="Default SIP Attack",
        description="Default SIP attack configuration",
        attack_type="invite_flood",
        target_host="127.0.0.1",
        target_port=5060
    )
