"""
Attack Manager for StormShadow.

This module provides centralized attack lifecycle management by directly
working with attack modules and a simple discovery mechanism.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from ..core import print_error, print_warning, print_info, print_success
from ..registry.lab_module import AttackModule
from ..terminal import TerminalManager, run_in_new_terminal


class AttackManager:
    """
    Manages attack module lifecycle and coordination.
    
    This manager provides:
    - Attack module discovery and loading
    - Attack lifecycle management (start/stop/status)
    - Coordination with other system components
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize attack manager.
        
        Args:
            config: Optional attack configuration
        """
        self.config = config or {}
        self.active_attacks: Dict[str, Union[AttackModule, 'TerminalAttackPlaceholder']] = {}
        self.terminal_manager = TerminalManager()
        
        # Try to find attack modules directory
        self.attack_modules_path = self._find_attack_modules_path()
        
        print_info("Attack manager initialized")
    
    def _find_attack_modules_path(self) -> Optional[Path]:
        """Find the attack modules directory."""
        try:
            # Look for attack directory relative to this file
            current_file = Path(__file__)
            project_root = current_file.parent.parent.parent
            attack_path = project_root / "attack"
            
            if attack_path.exists():
                return attack_path
            
            return None
        except Exception as e:
            print_warning(f"Could not locate attack modules: {e}")
            return None
    
    def discover_attacks(self) -> List[str]:
        """
        Discover available attack modules.
        
        Returns:
            List of available attack module names
        """
        available_attacks = []
        
        # Add hardcoded known attacks for now
        known_attacks = ["inviteflood", "basic", "your_attack"]
        available_attacks.extend(known_attacks)
        
        # If we have access to attack modules path, scan for more
        if self.attack_modules_path:
            try:
                # Look for attack algorithms
                algo_path = self.attack_modules_path / "attack_algorithms"
                if algo_path.exists():
                    for item in algo_path.iterdir():
                        if item.is_dir() and not item.name.startswith('_'):
                            if item.name not in available_attacks:
                                available_attacks.append(item.name)
            except Exception as e:
                print_warning(f"Error discovering attacks: {e}")
        
        return available_attacks
    
    async def start_attack(self, attack_name: str, attack_config: Dict[str, Any]) -> bool:
        """
        Start a specific attack module.
        
        Args:
            attack_name: Name of the attack to start
            attack_config: Configuration for the attack
            
        Returns:
            True if attack started successfully
        """
        try:
            # Check if attack is already running
            if attack_name in self.active_attacks:
                print_warning(f"Attack '{attack_name}' is already running")
                return False
            
            # Check if we should run in new terminal
            run_in_terminal = attack_config.get('run_in_terminal', True)
            dry_run = self.config.get('dry_run', False)
            
            if run_in_terminal and not dry_run:
                # Start attack in new terminal
                attack_command = self._build_attack_command(attack_name, attack_config)
                terminal_title = f"StormShadow - {attack_name}"
                
                success = run_in_new_terminal(
                    command=attack_command,
                    title=terminal_title,
                    persistent=True
                )
                
                if success:
                    # Create a placeholder to track the attack
                    attack_instance = TerminalAttackPlaceholder(attack_name, attack_config, terminal_title)
                    self.active_attacks[attack_name] = attack_instance
                    print_success(f"Started attack '{attack_name}' in new terminal")
                    return True
                else:
                    print_error(f"Failed to open terminal for attack: {attack_name}")
                    return False
            else:
                # Run attack module directly inline (not in new terminal)
                try:
                    # Load the actual attack module
                    if attack_config.get('type') == 'inviteflood':
                        # Import and create the InviteFloodAttackModule
                        import sys
                        from pathlib import Path
                        
                        # Add the attack module path
                        project_root = Path(__file__).parent.parent.parent
                        attack_path = project_root / "attack" / "inviteflood"
                        if str(attack_path) not in sys.path:
                            sys.path.insert(0, str(attack_path))
                        
                        from attack_inviteflood import InviteFloodAttackModule
                        attack_instance = InviteFloodAttackModule(attack_name, attack_config)
                    else:
                        # Fallback to placeholder for other types
                        attack_instance = SimpleAttackPlaceholder(attack_name, attack_config)
                    
                    # Start the attack
                    if await attack_instance.start():
                        self.active_attacks[attack_name] = attack_instance
                        print_success(f"Started attack: {attack_name}")
                        return True
                    else:
                        print_error(f"Failed to start attack: {attack_name}")
                        return False
                        
                except ImportError as e:
                    print_error(f"Failed to import attack module: {e}")
                    # Fallback to placeholder
                    attack_instance = SimpleAttackPlaceholder(attack_name, attack_config)
                    if await attack_instance.start():
                        self.active_attacks[attack_name] = attack_instance
                        print_success(f"Started placeholder attack: {attack_name}")
                        return True
                    else:
                        print_error(f"Failed to start attack: {attack_name}")
                        return False
                
        except Exception as e:
            print_error(f"Error starting attack '{attack_name}': {e}")
            return False
    
    def _build_attack_command(self, attack_name: str, attack_config: Dict[str, Any]) -> str:
        """
        Build the command to run the attack.
        
        Args:
            attack_name: Name of the attack
            attack_config: Attack configuration
            
        Returns:
            Command string to execute
        """
        attack_type = attack_config.get('type', 'inviteflood')
        target_ip = attack_config.get('target_ip', '127.0.0.1')
        target_port = attack_config.get('target_port', 5060)
        count = attack_config.get('count', 100)
        rate = attack_config.get('rate', '10/s')
        sip_user = attack_config.get('sip_user', '200')
        
        if attack_type == 'inviteflood':
            # Get all attack configuration
            source_ip = attack_config.get('source_ip', '')
            source_port = attack_config.get('source_port', '')
            interface = attack_config.get('interface', 'wlan0')
            timeout = attack_config.get('timeout', 60)
            use_spoofing = attack_config.get('use_spoofing', False)
            
            # Build command to run the attack directly
            command = f"cd /home/kaldah/Documents/Projets/StormShadow/Python"
            command += f" && echo 'Starting {attack_name} attack...'"
            command += f" && echo 'Target: {target_ip}:{target_port}'"
            command += f" && echo 'Spoofing: {'ENABLED' if use_spoofing else 'DISABLED'}'"
            if use_spoofing and source_ip:
                command += f" && echo 'Source IP: {source_ip}:{source_port or 4000}'"
            command += f" && echo '========================'"
            command += f" && echo ''"
            
            # Run the attack module directly - this will be interactive and stay open
            command += f" && sudo python3 -m attack.inviteflood.attack_inviteflood"
            command += f"; echo 'Attack finished. Press Enter to close...'; read"
        else:
            # Generic attack command
            command = f"echo 'Running {attack_type} attack: {attack_name}'"
            command += f" && echo 'Configuration: {attack_config}'"
            command += " && sleep 5"
            command += f" && echo 'Attack {attack_name} finished'"
        
        return command
    
    async def stop_attack(self, attack_name: str) -> bool:
        """
        Stop a specific attack module.
        
        Args:
            attack_name: Name of the attack to stop
            
        Returns:
            True if attack stopped successfully
        """
        try:
            if attack_name not in self.active_attacks:
                print_warning(f"Attack '{attack_name}' is not running")
                return False
            
            attack_instance = self.active_attacks[attack_name]
            
            # Stop the attack
            if await attack_instance.stop():
                del self.active_attacks[attack_name]
                print_success(f"Stopped attack: {attack_name}")
                return True
            else:
                print_error(f"Failed to stop attack: {attack_name}")
                return False
                
        except Exception as e:
            print_error(f"Error stopping attack '{attack_name}': {e}")
            return False
    
    async def stop_all_attacks(self) -> bool:
        """
        Stop all running attacks.
        
        Returns:
            True if all attacks stopped successfully
        """
        if not self.active_attacks:
            print_info("No attacks running")
            return True
        
        success = True
        for attack_name in list(self.active_attacks.keys()):
            if not await self.stop_attack(attack_name):
                success = False
        
        return success
    
    def get_attack_status(self, attack_name: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific attack.
        
        Args:
            attack_name: Name of the attack
            
        Returns:
            Attack status dict or None if not found
        """
        if attack_name not in self.active_attacks:
            return None
        
        try:
            attack_instance = self.active_attacks[attack_name]
            # Use get_stats instead of get_status
            return asyncio.run(attack_instance.get_stats())
        except Exception as e:
            print_error(f"Error getting status for attack '{attack_name}': {e}")
            return None
    
    def get_all_attack_status(self) -> Dict[str, Any]:
        """
        Get status of all attacks.
        
        Returns:
            Dict with status of all attacks
        """
        status = {
            'active_count': len(self.active_attacks),
            'active_attacks': list(self.active_attacks.keys()),
            'available_attacks': self.discover_attacks()
        }
        
        # Get detailed status for each active attack
        for attack_name in self.active_attacks:
            attack_status = self.get_attack_status(attack_name)
            if attack_status:
                status[f'{attack_name}_status'] = attack_status
        
        return status
    
    def is_attack_running(self, attack_name: str) -> bool:
        """
        Check if an attack is currently running.
        
        Args:
            attack_name: Name of the attack to check
            
        Returns:
            True if attack is running
        """
        return attack_name in self.active_attacks
    
    async def cleanup(self) -> None:
        """Clean up all attack resources."""
        try:
            await self.stop_all_attacks()
            print_success("Attack manager cleanup completed")
        except Exception as e:
            print_error(f"Error during attack cleanup: {e}")


class SimpleAttackPlaceholder(AttackModule):
    """
    Simple placeholder attack module for basic functionality.
    
    This is a temporary implementation until proper attack module
    loading is implemented.
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        """Initialize placeholder attack."""
        super().__init__(name, config)
        self.start_time = None
    
    async def start(self) -> bool:
        """Start the placeholder attack."""
        try:
            print_info(f"Starting placeholder attack: {self.name}")
            self._running = True
            self.start_time = asyncio.get_event_loop().time()
            return True
        except Exception as e:
            print_error(f"Error starting placeholder attack: {e}")
            return False
    
    async def stop(self) -> bool:
        """Stop the placeholder attack."""
        try:
            print_info(f"Stopping placeholder attack: {self.name}")
            self._running = False
            return True
        except Exception as e:
            print_error(f"Error stopping placeholder attack: {e}")
            return False
    
    async def configure(self) -> bool:
        """Configure the placeholder attack."""
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get placeholder attack statistics."""
        duration = 0
        if self.start_time and self._running:
            duration = asyncio.get_event_loop().time() - self.start_time
        
        return {
            'name': self.name,
            'running': self.is_running,
            'packets_sent': 0,
            'duration': duration,
            'config': self.config
        }


class TerminalAttackPlaceholder:
    """Placeholder for attacks running in separate terminals."""
    
    def __init__(self, name: str, config: Dict[str, Any], terminal_title: str):
        self.name = name
        self.config = config
        self.terminal_title = terminal_title
        self.is_running = True
        self.start_time = time.time()
    
    async def stop(self) -> bool:
        """Stop the attack (in terminal)."""
        print_info(f"Attack '{self.name}' is running in terminal '{self.terminal_title}'")
        print_info("Please close the terminal or stop the attack manually")
        self.is_running = False
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get attack status."""
        return {
            'name': self.name,
            'running': self.is_running,
            'start_time': self.start_time,
            'terminal': self.terminal_title,
            'config': self.config
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get attack statistics (compatible with AttackModule interface)."""
        duration = 0
        if self.start_time and self.is_running:
            duration = time.time() - self.start_time
        
        return {
            'name': self.name,
            'running': self.is_running,
            'packets_sent': 0,  # Not available for terminal attacks
            'duration': duration,
            'terminal': self.terminal_title,
            'config': self.config
        }
