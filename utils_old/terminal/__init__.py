"""
Terminal management package for StormShadow.

This package provides terminal operations and process management:
- TerminalManager: High-level terminal operations
- Terminal utilities: Terminal detection and configuration
- Process monitoring: Background process management and output capture
"""

from .terminal_manager import TerminalManager
from .terminal_utils import (
    get_terminal_info,
    is_terminal_available,
    setup_terminal_environment,
    get_terminal_size,
    clear_terminal,
    set_terminal_title,
    get_user_input,
    confirm_action,
    get_command_path,
    is_command_available,
    open_new_terminal,
    run_in_new_terminal
)
from .process_monitor import ProcessMonitor

# Cross-platform command interface
from ._command_interface import (
    get_command_executor,
    run_command,
    run_command_async,
    kill_process,
    get_process_list,
    check_command_exists
)

# Aliases for common functions
def supports_color() -> bool:
    """Check if terminal supports color."""
    return True  # Simplified for now

clear_screen = clear_terminal

__all__ = [
    'TerminalManager',
    'ProcessMonitor',
    'get_terminal_info',
    'is_terminal_available',
    'setup_terminal_environment',
    'get_terminal_size',
    'clear_terminal',
    'clear_screen',
    'set_terminal_title',
    'get_user_input',
    'confirm_action',
    'supports_color',
    'get_command_path',
    'is_command_available',
    'open_new_terminal',
    'run_in_new_terminal',
    # Cross-platform command functions
    'get_command_executor',
    'run_command',
    'run_command_async',
    'kill_process',
    'get_process_list',
    'check_command_exists'
]
