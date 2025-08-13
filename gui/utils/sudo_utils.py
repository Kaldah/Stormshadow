"""
Sudo utilities for GUI operations that require elevated privileges.

This module provides utilities to detect when operations need sudo privileges
and automatically restart the application with proper permissions.
"""

import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from typing import Optional, List
from utils.core.printing import print_info, print_error, print_warning


def check_sudo_available() -> bool:
    """Check if sudo is available and configured."""
    try:
        result = subprocess.run(['sudo', '-n', 'true'], 
                              capture_output=True, 
                              timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def is_running_as_root() -> bool:
    """Check if the current process is running with root privileges."""
    return os.geteuid() == 0


def check_command_needs_sudo(command: List[str]) -> bool:
    """
    Check if a command typically requires sudo privileges.
    
    Args:
        command: List of command arguments
        
    Returns:
        bool: True if command likely needs sudo
    """
    sudo_commands = {
        'iptables', 'ip6tables', 'docker', 'inviteflood', 
        'netfilterqueue', 'tcpdump', 'nmap'
    }
    
    if not command:
        return False
        
    cmd_name = Path(command[0]).name
    return cmd_name in sudo_commands


def request_sudo_restart() -> bool:
    """
    Ask user if they want to restart the application with sudo privileges.
    
    Returns:
        bool: True if user agreed to restart with sudo
    """
    try:
        # Create a simple dialog
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        message = (
            "StormShadow GUI requires administrator privileges for network operations.\n\n"
            "This includes:\n"
            "• iptables configuration for packet spoofing\n"
            "• Docker container management for lab mode\n"
            "• Network interface operations\n\n"
            "Would you like to restart with administrator privileges?"
        )
        
        result = messagebox.askyesno(
            "Administrator Privileges Required",
            message,
            icon='warning'
        )
        
        root.destroy()
        return result
        
    except Exception as e:
        print_error(f"Failed to show sudo dialog: {e}")
        return False


def restart_with_sudo() -> None:
    """Restart the current application with sudo privileges."""
    try:
        # Get the current Python executable path
        python_executable = sys.executable
        
        # Get the current script path
        script_path = os.path.abspath(sys.argv[0])
        
        # Prepare the command with original arguments
        sudo_command = ['sudo', python_executable, script_path] + sys.argv[1:]
        
        print_info(f"Restarting with sudo: {' '.join(sudo_command)}")
        
        # Execute the command with sudo
        os.execvp('sudo', sudo_command)
        
    except Exception as e:
        print_error(f"Failed to restart with sudo: {e}")
        sys.exit(1)


def handle_permission_error(operation_name: str, auto_restart: bool = True) -> bool:
    """
    Handle permission errors by optionally restarting with sudo.
    
    Args:
        operation_name: Name of the operation that failed
        auto_restart: If True, automatically restart with sudo after user confirmation
        
    Returns:
        bool: True if restarting with sudo, False otherwise
    """
    print_warning(f"Permission denied for operation: {operation_name}")
    
    if is_running_as_root():
        print_error("Already running as root, but still getting permission errors")
        return False
    
    if not auto_restart:
        print_info("Auto-restart disabled, user must manually restart with sudo")
        return False
    
    # Check if we can use sudo
    if not check_sudo_available():
        print_error("Sudo not available or not configured properly")
        messagebox.showerror(
            "Permission Error",
            f"Operation '{operation_name}' requires administrator privileges, "
            "but sudo is not available.\n\n"
            "Please run the application manually with: sudo python main.py --gui"
        )
        return False
    
    # Ask user for permission to restart
    if request_sudo_restart():
        print_info("User agreed to restart with sudo privileges")
        restart_with_sudo()
        return True  # This won't actually return as process is replaced
    else:
        print_info("User declined to restart with sudo privileges")
        messagebox.showwarning(
            "Limited Functionality",
            f"Operation '{operation_name}' was cancelled.\n\n"
            "Some features may not work without administrator privileges.\n"
            "To enable full functionality, restart with: sudo python main.py --gui"
        )
        return False


def run_with_sudo_check(command: List[str], operation_name: str = "network operation") -> subprocess.CompletedProcess:
    """
    Run a command with automatic sudo privilege checking.
    
    Args:
        command: Command to execute
        operation_name: Human-readable name of the operation
        
    Returns:
        subprocess.CompletedProcess: Result of the command
        
    Raises:
        PermissionError: If command requires sudo but user declined restart
    """
    try:
        # First try without sudo
        if not check_command_needs_sudo(command):
            return subprocess.run(command, check=True, capture_output=True, text=True)
        
        # Try with sudo -n (non-interactive)
        sudo_command = ['sudo', '-n'] + command
        result = subprocess.run(sudo_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            return result
        
        # If sudo failed and we're not running as root, try to get sudo
        if not is_running_as_root() and "password is required" in result.stderr:
            if handle_permission_error(operation_name):
                # This will restart the process, so we shouldn't reach here
                pass
            else:
                # User declined, raise permission error
                raise PermissionError(f"Sudo required for {operation_name}, but user declined")
        
        # Return the failed result for other types of errors
        return result
        
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        raise
    except Exception as e:
        print_error(f"Unexpected error running command: {e}")
        raise


def create_sudo_launcher_script() -> Optional[Path]:
    """
    Create a launcher script that automatically runs the GUI with sudo.
    
    Returns:
        Path: Path to the created launcher script, or None if failed
    """
    try:
        launcher_content = f"""#!/bin/bash
# StormShadow GUI Launcher with Sudo
# Auto-generated launcher script

cd "{os.getcwd()}"
sudo {sys.executable} {os.path.abspath(sys.argv[0])} --gui "$@"
"""
        
        launcher_path = Path.cwd() / "launch_gui_sudo.sh"
        
        with open(launcher_path, 'w') as f:
            f.write(launcher_content)
        
        # Make executable
        os.chmod(launcher_path, 0o755)
        
        print_info(f"Created sudo launcher script: {launcher_path}")
        return launcher_path
        
    except Exception as e:
        print_error(f"Failed to create launcher script: {e}")
        return None
