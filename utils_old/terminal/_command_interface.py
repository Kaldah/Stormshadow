"""
Internal command execution interface for cross-platform terminal operations.

This module provides the internal interface for command execution
across different platforms (Linux, Windows, macOS).
"""

import platform
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple, Union


class CommandInterface(ABC):
    """Abstract interface for command execution operations."""
    
    @abstractmethod
    def run_command(self, command: str, **kwargs) -> Any:
        """Execute a command and return result."""
        pass
    
    @abstractmethod
    def run_command_async(self, command: str, **kwargs) -> Any:
        """Execute a command asynchronously."""
        pass
    
    @abstractmethod
    def kill_process(self, pid: int) -> bool:
        """Kill a process by PID."""
        pass
    
    @abstractmethod
    def get_process_list(self) -> List[Dict[str, Any]]:
        """Get list of running processes."""
        pass
    
    @abstractmethod
    def check_command_exists(self, command: str) -> bool:
        """Check if a command exists on the system."""
        pass
    
    @abstractmethod
    def get_shell_info(self) -> Dict[str, str]:
        """Get information about the current shell."""
        pass


def get_command_executor() -> CommandInterface:
    """Get the appropriate command executor for current platform."""
    system = platform.system().lower()
    
    if system == "linux":
        from ._platforms.linux_cmd import LinuxCommandImplementation
        return LinuxCommandImplementation()
    elif system == "windows":
        from ._platforms.windows_cmd import WindowsCommandImplementation
        return WindowsCommandImplementation()
    elif system == "darwin":
        from ._platforms.macos_cmd import MacOSCommandImplementation
        return MacOSCommandImplementation()
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


# Convenience functions to maintain existing API
def run_command(command: str, **kwargs) -> Any:
    """Execute a command (cross-platform)."""
    executor = get_command_executor()
    return executor.run_command(command, **kwargs)


def run_command_async(command: str, **kwargs) -> Any:
    """Execute a command asynchronously (cross-platform)."""
    executor = get_command_executor()
    return executor.run_command_async(command, **kwargs)


def kill_process(pid: int) -> bool:
    """Kill a process by PID (cross-platform)."""
    executor = get_command_executor()
    return executor.kill_process(pid)


def get_process_list() -> List[Dict[str, Any]]:
    """Get list of running processes (cross-platform)."""
    executor = get_command_executor()
    return executor.get_process_list()


def check_command_exists(command: str) -> bool:
    """Check if a command exists (cross-platform)."""
    executor = get_command_executor()
    return executor.check_command_exists(command)
