"""
macOS command implementation for StormShadow terminal interface.

This module provides placeholder implementation for macOS command operations.
Currently returns "MACOS UNAVAILABLE" messages as requested.
"""

from typing import Dict, List, Optional, Any

from .._command_interface import CommandInterface
from ...core import print_warning


class MacOSCommandImplementation(CommandInterface):
    """macOS implementation of command interface."""
    
    def __init__(self):
        """Initialize macOS command implementation."""
        print_warning("macOS command execution support is not available yet")
    
    def run_command(self, command: str, **kwargs) -> Any:
        """Execute a command and return result."""
        print_warning("MACOS UNAVAILABLE: run_command not implemented yet")
        return None
    
    def run_command_async(self, command: str, **kwargs) -> Any:
        """Execute a command asynchronously."""
        print_warning("MACOS UNAVAILABLE: run_command_async not implemented yet")
        return None
    
    def kill_process(self, pid: int) -> bool:
        """Kill a process by PID."""
        print_warning("MACOS UNAVAILABLE: kill_process not implemented yet")
        return False
    
    def get_process_list(self) -> List[Dict[str, Any]]:
        """Get list of running processes."""
        print_warning("MACOS UNAVAILABLE: get_process_list not implemented yet")
        return []
    
    def check_command_exists(self, command: str) -> bool:
        """Check if a command exists on the system."""
        print_warning("MACOS UNAVAILABLE: check_command_exists not implemented yet")
        return False
    
    def get_shell_info(self) -> Dict[str, str]:
        """Get information about the current shell."""
        print_warning("MACOS UNAVAILABLE: get_shell_info not implemented yet")
        return {'platform': 'macos', 'status': 'unavailable'}
