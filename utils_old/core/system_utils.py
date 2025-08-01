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
import signal
import logging
import time
from typing import Optional, List, Dict, Callable
from pathlib import Path

from .printing import print_error, print_warning


def check_root() -> bool:
    """
    Check if the current process is running with root privileges.

    Returns:
        bool: True if running as root, False otherwise
    """
    return os.geteuid() == 0


def get_local_ip() -> str:
    """
    Get the local IP address of the machine.

    Returns:
        str: Local IP address or '127.0.0.1' if unable to determine
    """
    try:
        # Connect to a remote address to determine local IP
        # This doesn't actually send data
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            return local_ip
    except Exception:
        try:
            # Fallback: get hostname IP
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            return local_ip
        except Exception:
            return "127.0.0.1"


def get_interface_ip(interface: str) -> Optional[str]:
    """
    Get the IP address of a specific network interface.

    Args:
        interface: Network interface name (e.g., 'eth0', 'wlan0')

    Returns:
        Optional[str]: IP address of the interface or None if not found
    """
    try:
        import netifaces

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
        print_warning(f"Error getting interface IP: {e}")

    return None


def wait_for_service(host: str, port: int, timeout: float = 30.0) -> bool:
    """
    Wait for a service to become available on a specific host and port.

    Args:
        host: Hostname or IP address
        port: Port number
        timeout: Maximum time to wait in seconds

    Returns:
        bool: True if service is available, False if timeout reached
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1.0)
                result = sock.connect_ex((host, port))
                if result == 0:
                    return True
        except Exception:
            pass

        time.sleep(0.5)

    return False


def kill_process_tree(pid: int, including_parent: bool = True) -> bool:
    """
    Kill a process and all its children.

    Args:
        pid: Process ID to kill
        including_parent: Whether to kill the parent process as well

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import psutil

        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)

            # Kill children first
            for child in children:
                try:
                    child.kill()
                except psutil.NoSuchProcess:
                    pass

            # Kill parent if requested
            if including_parent:
                try:
                    parent.kill()
                except psutil.NoSuchProcess:
                    pass

            # Wait for processes to die
            _, alive = psutil.wait_procs(
                children + ([parent] if including_parent else []),
                timeout=3
            )

            return len(alive) == 0

        except psutil.NoSuchProcess:
            return True  # Process already gone

    except ImportError:
        # Fallback using os signals
        try:
            if including_parent:
                os.killpg(os.getpgid(pid), signal.SIGTERM)
            else:
                # This is more complex without psutil
                # For now, just kill the main process
                os.kill(pid, signal.SIGTERM)

            # Wait a bit and try SIGKILL if needed
            time.sleep(1)
            try:
                os.kill(pid, 0)  # Check if process still exists
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass  # Process is gone

            return True

        except (ProcessLookupError, PermissionError):
            return True  # Process gone or no permission
        except Exception as e:
            print_error(f"Error killing process tree: {e}")
            return False

    except Exception as e:
        print_error(f"Error killing process tree: {e}")
        return False


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
        'local_ip': str(get_local_ip())
    }

    return info


def check_command_available(command: str) -> bool:
    """
    Check if a command is available in the system PATH.

    Args:
        command: Command name to check

    Returns:
        bool: True if command is available, False otherwise
    """
    try:
        result = subprocess.run(
            ['which', command],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False


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


def wait_for_condition(
    condition_func: Callable[[], bool],
    timeout: float = 30.0,
    interval: float = 1.0,
    description: str = "condition"
) -> bool:
    """
    Wait for a condition function to return True.

    Args:
        condition_func: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds
        interval: Time between condition checks in seconds
        description: Description of the condition for logging

    Returns:
        bool: True if condition was met, False if timeout reached
    """
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            if condition_func():
                return True
        except Exception as e:
            # Log the exception but continue waiting
            print_warning(f"Exception while checking {description}: {e}")

        time.sleep(interval)

    print_error(f"Timeout waiting for {description} after {timeout} seconds")
    return False
