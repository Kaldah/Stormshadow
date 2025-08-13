"""
GUI startup checks for StormShadow.

This module performs various checks when the GUI starts to ensure
the environment is properly configured for network operations.
"""

import os
import subprocess
import tkinter as tk
from tkinter import messagebox
from utils.core.printing import print_info, print_warning, print_error


def check_sudo_access() -> tuple[bool, str]:
    """
    Check if sudo access is available for network operations.
    
    Returns:
        tuple: (has_access, message)
    """
    if os.geteuid() == 0:
        return True, "Running with administrator privileges"
    
    try:
        # Test sudo access with a simple command
        result = subprocess.run(['sudo', '-n', 'true'], 
                              capture_output=True, 
                              timeout=5)
        if result.returncode == 0:
            return True, "Sudo access available"
        else:
            return False, "Sudo access requires password"
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, "Sudo not available"


def check_required_commands() -> list[str]:
    """
    Check if required network commands are available.
    
    Returns:
        list: List of missing commands
    """
    required_commands = ['iptables', 'docker']
    missing_commands = []
    
    for cmd in required_commands:
        try:
            result = subprocess.run(['which', cmd], 
                                  capture_output=True, 
                                  timeout=5)
            if result.returncode != 0:
                missing_commands.append(cmd)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            missing_commands.append(cmd)
    
    return missing_commands


def show_permission_warning() -> bool:
    """
    Show a warning dialog about permission requirements.
    
    Returns:
        bool: True if user wants to continue, False to exit
    """
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        message = (
            "StormShadow GUI detected limited permissions.\n\n"
            "⚠️  Some features may not work properly:\n"
            "• Attack spoofing (requires iptables access)\n"
            "• Lab management (requires Docker access)\n"
            "• Network configuration\n\n"
            "To enable full functionality:\n"
            "• Close this application\n"
            "• Run: sudo python main.py --gui\n\n"
            "Continue with limited functionality?"
        )
        
        result = messagebox.askquestion(
            "Limited Permissions Detected",
            message,
            icon='warning'
        )
        
        root.destroy()
        return result == 'yes'
        
    except Exception as e:
        print_error(f"Failed to show permission warning: {e}")
        return True  # Continue by default if dialog fails


def show_missing_commands_warning(missing_commands: list[str]) -> bool:
    """
    Show a warning dialog about missing required commands.
    
    Args:
        missing_commands: List of missing command names
        
    Returns:
        bool: True if user wants to continue, False to exit
    """
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        cmd_list = "\n".join(f"• {cmd}" for cmd in missing_commands)
        
        message = (
            f"Missing required commands:\n\n{cmd_list}\n\n"
            "These commands are needed for full functionality.\n"
            "Please install the missing packages and restart.\n\n"
            "Continue anyway?"
        )
        
        result = messagebox.askquestion(
            "Missing Commands",
            message,
            icon='warning'
        )
        
        root.destroy()
        return result == 'yes'
        
    except Exception as e:
        print_error(f"Failed to show missing commands warning: {e}")
        return True  # Continue by default if dialog fails


def perform_startup_checks() -> bool:
    """
    Perform all startup checks and show appropriate warnings.
    
    Returns:
        bool: True if GUI should continue to start, False to exit
    """
    print_info("Performing startup checks...")
    
    # Check for missing commands
    missing_commands = check_required_commands()
    if missing_commands:
        print_warning(f"Missing commands: {missing_commands}")
        if not show_missing_commands_warning(missing_commands):
            return False
    
    # Check sudo access
    has_sudo, sudo_message = check_sudo_access()
    print_info(f"Sudo check: {sudo_message}")
    
    if not has_sudo:
        print_warning("Limited permissions detected")
        if not show_permission_warning():
            return False
    
    print_info("Startup checks completed")
    return True


def show_sudo_restart_dialog() -> bool:
    """
    Show a dialog asking user if they want to restart with sudo.
    
    Returns:
        bool: True if user agreed to restart
    """
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        message = (
            "A network operation failed due to insufficient permissions.\n\n"
            "This typically happens when:\n"
            "• Configuring iptables rules for packet spoofing\n"
            "• Managing Docker containers for lab mode\n"
            "• Accessing network interfaces\n\n"
            "Would you like to restart StormShadow with administrator privileges?\n"
            "(This will close the current window and ask for your password)"
        )
        
        result = messagebox.askyesno(
            "Administrator Privileges Required",
            message,
            icon='warning'
        )
        
        root.destroy()
        return result
        
    except Exception as e:
        print_error(f"Failed to show sudo restart dialog: {e}")
        return False
