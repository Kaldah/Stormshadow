"""
System utilities for StormShadow.

This module provides system-level utility functions including:
- Root permission checking
- Network interface and IP management
- Service availability checking
- Process management
- Logging setup
"""

import os
import sys
import socket
import subprocess
import logging
from typing import Optional, List, Dict
from pathlib import Path
import netifaces

from .printing import print_warning

def check_root() -> bool:
    """
    Check if the current process is running with root privileges.

    Returns:
        bool: True if running as root, False otherwise
    """
    return os.geteuid() == 0

def get_interface() -> str:
    """Get the default network interface."""
    try:
        return netifaces.gateways()['default'][netifaces.AF_INET][1]
    except Exception:
        return "lo"

def get_interface_ip(interface: str) -> Optional[str]:
    """
    Get the IP address of a specific network interface.

    Args:
        interface: Network interface name (e.g., 'eth0', 'wlan0')

    Returns:
        Optional[str]: IP address of the interface or None if not found
    """
    try:
        if interface in netifaces.interfaces():
            addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addresses:
                return addresses[netifaces.AF_INET][0]['addr']
    except ImportError:
        # Fallback using ip command
        try:
            result = subprocess.run(
                ['ip', 'addr', 'show', interface],
                capture_output=True,
                text=True,
                check=True
            )

            for line in result.stdout.split('\n'):
                if 'inet ' in line and 'scope global' in line:
                    ip = line.strip().split()[1].split('/')[0]
                    return ip
        except (subprocess.CalledProcessError, IndexError):
            pass

    except Exception as e:
        print_warning(f"Error getting IP for {interface}. Falling back to localhost IP: {e}")

    return "127.0.1"  # Fallback to localhost if interface not found

def check_current_queue_num() -> int:
    """
    Placeholder function to check the current queue number.
    This should be implemented to return the actual queue number of the machine.
    """
    return 1

def get_available_ports(start_port: int = 8000, count: int = 10) -> List[int]:
    """
    Get a list of available ports starting from a given port.

    Args:
        start_port: Starting port number
        count: Number of ports to check

    Returns:
        List[int]: List of available port numbers
    """
    available_ports: List[int] = []

    for port in range(start_port, start_port + count * 10):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('', port))
                available_ports.append(port)

                if len(available_ports) >= count:
                    break

        except OSError:
            continue  # Port is busy

    return available_ports

def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        format_string: Optional custom format string

    Returns:
        logging.Logger: Configured logger instance
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[]
    )

    logger = logging.getLogger('stormshadow')

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(format_string))
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        try:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(logging.Formatter(format_string))
            logger.addHandler(file_handler)

        except Exception as e:
            print_warning(f"Failed to setup file logging: {e}")

    logger.setLevel(getattr(logging, level.upper()))

    return logger


def get_system_info() -> Dict[str, str]:
    """
    Get system information.

    Returns:
        Dict[str, str]: System information dictionary
    """
    import platform

    info: Dict[str, str] = {
        'platform': str(platform.platform()),
        'system': str(platform.system()),
        'release': str(platform.release()),
        'version': str(platform.version()),
        'machine': str(platform.machine()),
        'processor': str(platform.processor()),
        'python_version': str(platform.python_version()),
        'is_root': str(check_root()),
        'local_ip': str(get_interface_ip(get_interface()))
    }

    return info
