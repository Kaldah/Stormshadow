"""
Linux command implementation for StormShadow terminal interface.

This module wraps the existing core command execution functionality
to implement the cross-platform command interface.
"""

import subprocess
import signal
import psutil
import shutil
from typing import Dict, List, Optional, Any

from .._command_interface import CommandInterface
from ...core import run_command as core_run_command, print_error, print_info, print_success


class LinuxCommandImplementation(CommandInterface):
    """Linux implementation of command interface."""
    
    def __init__(self):
        """Initialize Linux command implementation."""
        print_info("Initialized Linux command executor")
    
    def run_command(self, command: str, **kwargs) -> Any:
        """Execute a command and return result."""
        try:
            # Use existing core run_command functionality
            return core_run_command(command, **kwargs)
            
        except Exception as e:
            print_error(f"Error executing command '{command}': {e}")
            return None
    
    def run_command_async(self, command: str, **kwargs) -> Any:
        """Execute a command asynchronously."""
        try:
            # Extract common parameters
            cwd = kwargs.get('cwd')
            env = kwargs.get('env')
            shell = kwargs.get('shell', True)
            
            # Start process asynchronously
            process = subprocess.Popen(
                command,
                shell=shell,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            return process
            
        except Exception as e:
            print_error(f"Error executing async command '{command}': {e}")
            return None
    
    def kill_process(self, pid: int) -> bool:
        """Kill a process by PID."""
        try:
            process = psutil.Process(pid)
            process.terminate()
            
            # Wait for termination, then force kill if needed
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                process.kill()
            
            return True
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print_error(f"Error killing process {pid}: {e}")
            return False
        except Exception as e:
            print_error(f"Unexpected error killing process {pid}: {e}")
            return False
    
    def get_process_list(self) -> List[Dict[str, Any]]:
        """Get list of running processes."""
        try:
            processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process disappeared or access denied
                    continue
            
            return processes
            
        except Exception as e:
            print_error(f"Error getting process list: {e}")
            return []
    
    def check_command_exists(self, command: str) -> bool:
        """Check if a command exists on the system."""
        try:
            return shutil.which(command) is not None
            
        except Exception as e:
            print_error(f"Error checking command existence '{command}': {e}")
            return False
    
    def get_shell_info(self) -> Dict[str, str]:
        """Get information about the current shell."""
        try:
            import os
            
            shell_info = {
                'shell': os.environ.get('SHELL', '/bin/bash'),
                'term': os.environ.get('TERM', 'unknown'),
                'platform': 'linux',
                'user': os.environ.get('USER', 'unknown'),
                'home': os.environ.get('HOME', '/'),
                'path': os.environ.get('PATH', '')
            }
            
            return shell_info
            
        except Exception as e:
            print_error(f"Error getting shell info: {e}")
            return {'platform': 'linux', 'error': str(e)}
    
    def execute_sudo_command(self, command: str, **kwargs) -> Any:
        """Execute a command with sudo (Linux-specific)."""
        try:
            sudo_command = f"sudo {command}"
            return self.run_command(sudo_command, **kwargs)
            
        except Exception as e:
            print_error(f"Error executing sudo command '{command}': {e}")
            return None
    
    def check_root_privileges(self) -> bool:
        """Check if running with root privileges."""
        try:
            import os
            return os.geteuid() == 0
            
        except Exception as e:
            print_error(f"Error checking root privileges: {e}")
            return False
    
    def get_system_services(self) -> List[str]:
        """Get list of system services (Linux-specific)."""
        try:
            result = self.run_command("systemctl list-units --type=service --state=running", capture_output=True)
            
            if result and hasattr(result, 'stdout'):
                services = []
                lines = result.stdout.split('\n')[1:]  # Skip header
                
                for line in lines:
                    if line.strip() and '.service' in line:
                        service_name = line.split()[0]
                        services.append(service_name)
                
                return services
            
            return []
            
        except Exception as e:
            print_error(f"Error getting system services: {e}")
            return []
