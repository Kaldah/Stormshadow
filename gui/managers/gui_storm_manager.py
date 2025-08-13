"""
GUI Storm Manager

This module manages StormShadow instances for the GUI application,
providing a clean interface between the GUI and the core StormShadow functionality.
"""

import threading
from pathlib import Path
from typing import Dict, Optional, Callable
from dataclasses import dataclass
import subprocess

from utils.config.config import Parameters
from utils.core.stormshadow import StormShadow
from utils.core.printing import print_info, print_error, print_debug, print_success
from utils.attack.attack_modules_finder import find_attack_modules


@dataclass
class StormShadowInstance:
    """Represents a managed StormShadow instance."""
    name: str
    instance: StormShadow
    thread: Optional[threading.Thread] = None
    is_running: bool = False
    instance_type: str = "unknown"  # "lab", "attack", "both"


class GUIStormManager:
    """
    Manages StormShadow instances for the GUI application.
    
    This manager provides:
    - Creation and management of StormShadow instances
    - Thread management for non-blocking operations
    - Status tracking and monitoring
    - Configuration management for GUI operations
    """
    
    def __init__(self):
        """Initialize the GUI storm manager."""
        print_debug("Initializing GUI Storm Manager...")
        
        self.instances: Dict[str, StormShadowInstance] = {}
        self.available_attacks: Dict[str, Path] = {}
        self.status_callbacks: Dict[str, Callable[[str, str], None]] = {}
        
        # Discover available attack modules
        self._discover_attacks()
        
        print_success("GUI Storm Manager initialized")
    
    def _discover_attacks(self):
        """Discover available attack modules."""
        print_debug("Discovering available attack modules...")
        try:
            # Use absolute path relative to the project root
            from utils.core.system_utils import get_project_root
            project_root = get_project_root()
            attack_modules_path = project_root / "sip_attacks"
            self.available_attacks = find_attack_modules(attack_modules_path)
            print_info(f"Found {len(self.available_attacks)} attack modules: {list(self.available_attacks.keys())}")
        except Exception as e:
            print_error(f"Failed to discover attack modules: {e}")
            self.available_attacks = {}
    
    def get_available_attacks(self) -> Dict[str, Path]:
        """Get the list of available attack modules."""
        return self.available_attacks.copy()
    
    def create_attack_instance(self, attack_name: str, config_params: Parameters) -> bool:
        """
        Create a new StormShadow instance configured for attack mode.
        
        Args:
            attack_name: Name of the attack to configure
            config_params: Additional configuration parameters
            
        Returns:
            bool: True if instance was created successfully
        """
        instance_name = f"attack_{attack_name}"
        
        # If instance already exists, remove it first
        if instance_name in self.instances:
            print_debug(f"Instance {instance_name} already exists, removing it first")
            self.stop_instance(instance_name)
            self.remove_instance(instance_name)
        
        try:
            # Get default IP address
            from utils.core.system_utils import get_default_ip
            default_ip = get_default_ip()
            
            # Create parameters for attack mode
            attack_params = Parameters({
                "mode": "attack",
                "attack_name": attack_name,
                "attack": True,
                "lab": False,
                "gui": True,
                "open_window": True,
                "spoofing_enabled": config_params.get("spoofing_enabled", True),
                "return_path_enabled": config_params.get("return_path_enabled", True),
                "target_ip": config_params.get("target_ip", default_ip),
                "target_port": config_params.get("target_port", 5060),
                "max_count": config_params.get("max_count", 100),
                "dry_run": config_params.get("dry_run", False)
            })
            
            # Merge with additional parameters
            for key, value in config_params.items():
                if key not in attack_params:
                    attack_params[key] = value
            
            # Create StormShadow instance
            storm_instance = StormShadow(CLI_Args=attack_params)
            storm_instance.setup()
            
            # Create managed instance
            managed_instance = StormShadowInstance(
                name=instance_name,
                instance=storm_instance,
                instance_type="attack"
            )
            
            self.instances[instance_name] = managed_instance
            print_success(f"Created attack instance: {instance_name}")
            return True
            
        except Exception as e:
            print_error(f"Failed to create attack instance {instance_name}: {e}")
            return False
    
    def create_lab_instance(self, config_params: Optional[Parameters] = None) -> bool:
        """
        Create a new StormShadow instance configured for lab mode.
        
        Args:
            config_params: Optional configuration parameters
            
        Returns:
            bool: True if instance was created successfully
        """
        instance_name = "lab_manager"
        
        # If instance already exists, remove it first
        if instance_name in self.instances:
            print_debug(f"Instance {instance_name} already exists, removing it first")
            self.stop_instance(instance_name)
            self.remove_instance(instance_name)
        
        try:
            # Create parameters for lab mode
            lab_params = Parameters({
                "mode": "lab",
                "attack": False,
                "lab": True,
                "gui": True
            })
            
            # Merge with additional parameters
            if config_params:
                for key, value in config_params.items():
                    lab_params[key] = value
            
            # Create StormShadow instance
            storm_instance = StormShadow(CLI_Args=lab_params)
            storm_instance.setup()
            
            # Create managed instance
            managed_instance = StormShadowInstance(
                name=instance_name,
                instance=storm_instance,
                instance_type="lab"
            )
            
            self.instances[instance_name] = managed_instance
            print_success(f"Created lab instance: {instance_name}")
            return True
            
        except Exception as e:
            print_error(f"Failed to create lab instance {instance_name}: {e}")
            return False
    
    def start_instance(self, instance_name: str) -> bool:
        """
        Start a StormShadow instance in a separate thread.
        
        Args:
            instance_name: Name of the instance to start
            
        Returns:
            bool: True if started successfully
        """
        if instance_name not in self.instances:
            print_error(f"Instance {instance_name} not found")
            return False
        
        instance = self.instances[instance_name]
        
        if instance.is_running:
            print_error(f"Instance {instance_name} is already running")
            return False
        
        try:
            def run_instance():
                try:
                    print_info(f"Starting instance {instance_name}...")
                    instance.is_running = True
                    self._notify_status_change(instance_name, "starting")
                    
                    # Run the StormShadow instance
                    instance.instance.run()
                    
                    self._notify_status_change(instance_name, "running")
                    print_success(f"Instance {instance_name} started successfully")
                    
                except subprocess.CalledProcessError as e:
                    # Handle sudo permission errors specifically
                    if "password is required" in str(e) or e.returncode == 1:
                        print_error(f"Permission error running instance {instance_name}: {e}")
                        self._notify_status_change(instance_name, "permission_error")
                        
                        # Try to handle permission error
                        try:
                            from gui.utils.sudo_utils import handle_permission_error
                            operation_name = f"running {instance_name}"
                            handle_permission_error(operation_name, auto_restart=True)
                        except ImportError:
                            print_error("Could not import sudo utilities")
                    else:
                        print_error(f"Command error running instance {instance_name}: {e}")
                        self._notify_status_change(instance_name, "error")
                        
                except Exception as e:
                    print_error(f"Error running instance {instance_name}: {e}")
                    self._notify_status_change(instance_name, "error")
                finally:
                    instance.is_running = False
                    self._notify_status_change(instance_name, "stopped")
            
            # Create and start thread
            instance.thread = threading.Thread(target=run_instance, daemon=True)
            instance.thread.start()
            
            return True
            
        except Exception as e:
            print_error(f"Failed to start instance {instance_name}: {e}")
            instance.is_running = False
            return False
    
    def stop_instance(self, instance_name: str) -> bool:
        """
        Stop a running StormShadow instance.
        
        Args:
            instance_name: Name of the instance to stop
            
        Returns:
            bool: True if stopped successfully
        """
        if instance_name not in self.instances:
            print_error(f"Instance {instance_name} not found")
            return False
        
        instance = self.instances[instance_name]
        
        if not instance.is_running:
            print_error(f"Instance {instance_name} is not running")
            return False
        
        try:
            print_info(f"Stopping instance {instance_name}...")
            self._notify_status_change(instance_name, "stopping")
            
            # Stop the StormShadow instance
            instance.instance.stop()
            
            # Wait for thread to finish (with timeout)
            if instance.thread and instance.thread.is_alive():
                instance.thread.join(timeout=5.0)
            
            instance.is_running = False
            self._notify_status_change(instance_name, "stopped")
            print_success(f"Instance {instance_name} stopped successfully")
            return True
            
        except Exception as e:
            print_error(f"Failed to stop instance {instance_name}: {e}")
            return False
    
    def remove_instance(self, instance_name: str) -> bool:
        """
        Remove a StormShadow instance.
        
        Args:
            instance_name: Name of the instance to remove
            
        Returns:
            bool: True if removed successfully
        """
        if instance_name not in self.instances:
            print_error(f"Instance {instance_name} not found")
            return False
        
        instance = self.instances[instance_name]
        
        # Stop the instance if it's running
        if instance.is_running:
            if not self.stop_instance(instance_name):
                print_error(f"Failed to stop instance {instance_name} before removal")
                return False
        
        try:
            # Remove the instance
            del self.instances[instance_name]
            print_success(f"Instance {instance_name} removed successfully")
            return True
            
        except Exception as e:
            print_error(f"Failed to remove instance {instance_name}: {e}")
            return False
    
    def get_instance_status(self, instance_name: str) -> Optional[str]:
        """
        Get the status of a StormShadow instance.
        
        Args:
            instance_name: Name of the instance
            
        Returns:
            Optional[str]: Status string or None if instance not found
        """
        if instance_name not in self.instances:
            return None
        
        instance = self.instances[instance_name]
        if instance.is_running:
            return "running"
        else:
            return "stopped"
    
    def get_all_instances(self) -> Dict[str, str]:
        """
        Get all instances and their statuses.
        
        Returns:
            Dict[str, str]: Instance name to status mapping
        """
        return {
            name: "running" if instance.is_running else "stopped"
            for name, instance in self.instances.items()
        }
    
    def register_status_callback(self, callback_id: str, callback: Callable[[str, str], None]):
        """
        Register a callback for status changes.
        
        Args:
            callback_id: Unique identifier for the callback
            callback: Function to call on status changes (instance_name, status)
        """
        self.status_callbacks[callback_id] = callback
    
    def unregister_status_callback(self, callback_id: str):
        """
        Unregister a status callback.
        
        Args:
            callback_id: Identifier of the callback to remove
        """
        if callback_id in self.status_callbacks:
            del self.status_callbacks[callback_id]
    
    def _notify_status_change(self, instance_name: str, status: str):
        """
        Notify all registered callbacks about a status change.
        
        Args:
            instance_name: Name of the instance that changed status
            status: New status
        """
        for callback in self.status_callbacks.values():
            try:
                callback(instance_name, status)
            except Exception as e:
                print_error(f"Error in status callback: {e}")
    
    def cleanup(self):
        """Clean up all instances and resources."""
        print_info("Cleaning up GUI Storm Manager...")
        
        # Stop all running instances
        for instance_name in list(self.instances.keys()):
            if self.instances[instance_name].is_running:
                self.stop_instance(instance_name)
        
        # Clear all instances
        self.instances.clear()
        
        # Clear callbacks
        self.status_callbacks.clear()
        
        print_success("GUI Storm Manager cleanup completed")
