"""
Windows command implementation for StormShadow terminal interface.

This module implements Windows-specific command execution using
cmd.exe and PowerShell.
"""

import subprocess
import shutil
import os
from typing import Dict, List, Optional, Any

from .._command_interface import CommandInterface
from ...core import print_error, print_info, print_success


class WindowsCommandImplementation(CommandInterface):
    """Windows implementation of command interface."""
    
    def __init__(self):
        """Initialize Windows command implementation."""
        self.default_shell = "cmd.exe"
        print_info("Initialized Windows command executor")
    
    def run_command(self, command: str, **kwargs) -> Any:
        """Execute a command and return result."""
        try:
            # Extract parameters
            cwd = kwargs.get('cwd')
            env = kwargs.get('env')
            shell = kwargs.get('shell', True)
            capture_output = kwargs.get('capture_output', False)
            text = kwargs.get('text', True)
            timeout = kwargs.get('timeout')
            
            # Run command using subprocess
            result = subprocess.run(
                command,
                shell=shell,
                cwd=cwd,
                env=env,
                capture_output=capture_output,
                text=text,
                timeout=timeout
            )
            
            return result
            
        except subprocess.TimeoutExpired as e:
            print_error(f"Command timed out: '{command}'")
            return None
        except Exception as e:
            print_error(f"Error executing command '{command}': {e}")
            return None
    
    def run_command_async(self, command: str, **kwargs) -> Any:
        """Execute a command asynchronously."""
        try:
            # Extract parameters
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
            # Use taskkill command
            result = self.run_command(f"taskkill /F /PID {pid}", capture_output=True)
            return result and result.returncode == 0
            
        except Exception as e:
            print_error(f"Error killing process {pid}: {e}")
            return False
    
    def get_process_list(self) -> List[Dict[str, Any]]:
        """Get list of running processes."""
        try:
            # Use tasklist command
            result = self.run_command("tasklist /FO CSV", capture_output=True)
            
            if not result or result.returncode != 0:
                return []
            
            processes = []
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip():
                    # Parse CSV format
                    parts = line.split('","')
                    if len(parts) >= 5:
                        name = parts[0].strip('"')
                        pid = parts[1].strip('"')
                        session = parts[2].strip('"')
                        memory = parts[4].strip('"')
                        
                        processes.append({
                            'name': name,
                            'pid': int(pid) if pid.isdigit() else 0,
                            'session': session,
                            'memory': memory
                        })
            
            return processes
            
        except Exception as e:
            print_error(f"Error getting process list: {e}")
            return []
    
    def check_command_exists(self, command: str) -> bool:
        """Check if a command exists on the system."""
        try:
            # Check in PATH
            if shutil.which(command):
                return True
            
            # Check as Windows command
            result = self.run_command(f"where {command}", capture_output=True)
            return result and result.returncode == 0
            
        except Exception as e:
            print_error(f"Error checking command existence '{command}': {e}")
            return False
    
    def get_shell_info(self) -> Dict[str, str]:
        """Get information about the current shell."""
        try:
            shell_info = {
                'shell': os.environ.get('COMSPEC', 'cmd.exe'),
                'platform': 'windows',
                'user': os.environ.get('USERNAME', 'unknown'),
                'home': os.environ.get('USERPROFILE', 'C:\\'),
                'path': os.environ.get('PATH', ''),
                'os_version': os.environ.get('OS', 'Windows'),
                'processor': os.environ.get('PROCESSOR_ARCHITECTURE', 'unknown')
            }
            
            return shell_info
            
        except Exception as e:
            print_error(f"Error getting shell info: {e}")
            return {'platform': 'windows', 'error': str(e)}
    
    def run_powershell_command(self, command: str, **kwargs) -> Any:
        """Execute a PowerShell command (Windows-specific)."""
        try:
            ps_command = f"powershell.exe -Command \"{command}\""
            return self.run_command(ps_command, **kwargs)
            
        except Exception as e:
            print_error(f"Error executing PowerShell command '{command}': {e}")
            return None
    
    def check_admin_privileges(self) -> bool:
        """Check if running with administrator privileges."""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
            
        except Exception as e:
            print_error(f"Error checking admin privileges: {e}")
            return False
    
    def get_windows_services(self) -> List[str]:
        """Get list of Windows services."""
        try:
            result = self.run_command("sc query state= running", capture_output=True)
            
            if not result or result.returncode != 0:
                return []
            
            services = []
            lines = result.stdout.split('\n')
            
            for line in lines:
                if 'SERVICE_NAME:' in line:
                    service_name = line.split(':', 1)[1].strip()
                    services.append(service_name)
            
            return services
            
        except Exception as e:
            print_error(f"Error getting Windows services: {e}")
            return []
    
    def enable_windows_firewall_rule(self, rule_name: str) -> bool:
        """Enable a Windows firewall rule (Windows-specific)."""
        try:
            cmd = f'netsh advfirewall firewall set rule name="{rule_name}" new enable=yes'
            result = self.run_command(cmd, capture_output=True)
            return result and result.returncode == 0
            
        except Exception as e:
            print_error(f"Error enabling firewall rule '{rule_name}': {e}")
            return False
    
    def disable_windows_firewall_rule(self, rule_name: str) -> bool:
        """Disable a Windows firewall rule (Windows-specific)."""
        try:
            cmd = f'netsh advfirewall firewall set rule name="{rule_name}" new enable=no'
            result = self.run_command(cmd, capture_output=True)
            return result and result.returncode == 0
            
        except Exception as e:
            print_error(f"Error disabling firewall rule '{rule_name}': {e}")
            return False
