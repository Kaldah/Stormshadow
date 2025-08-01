"""
Interactive mode manager for StormShadow.

This module provides interactive command-line interface functionality
for real-time attack management and system monitoring.
"""

from typing import TYPE_CHECKING, Dict, Any

from ..core import print_error, print_warning, print_info, print_success
from ..terminal import (
    get_user_input, confirm_action, set_terminal_title, clear_terminal
)

if TYPE_CHECKING:
    from .orchestrator import StormShadowOrchestrator


class InteractiveManager:
    """
    Manages interactive mode operations.
    
    Provides a command-line interface for:
    - Real-time attack management
    - System status monitoring
    - Component control
    """
    
    def __init__(self, orchestrator: 'StormShadowOrchestrator'):
        """
        Initialize interactive manager.
        
        Args:
            orchestrator: Reference to main orchestrator
        """
        self.orchestrator = orchestrator
        self.config = orchestrator.config
        self.running = True
        
        # Setup monitoring sessions
        self.monitoring_sessions = getattr(self.orchestrator, "monitoring_sessions", {})
        
        print_info("Interactive manager initialized")
    
    async def run(self) -> int:
        """
        Run the interactive mode loop.
        
        Returns:
            int: Exit code
        """
        try:
            # Setup terminal
            set_terminal_title("StormShadow Interactive Mode")
            
            # Start lab components in background if enabled
            if not await self._start_background_components():
                return 1
            
            # Show welcome message
            self._show_welcome()
            
            # Start interactive loop
            return await self._interactive_loop()
            
        except Exception as e:
            print_error(f"Error in interactive mode: {e}")
            return 1
        finally:
            await self.orchestrator.cleanup()
    
    async def _start_background_components(self) -> bool:
        """Start background components (labs)."""
        try:
            # Start lab components if enabled
            lab_config = self.config.get('lab', {})
            if lab_config.get('enabled', True):
                if not await self.orchestrator.start_labs():
                    print_error("Failed to start lab components")
                    return False
                print_success("Lab components started in background")
            
            return True
            
        except Exception as e:
            print_error(f"Failed to start background components: {e}")
            return False
    
    def _show_welcome(self):
        """Show welcome message and help."""
        clear_terminal()
        print("=" * 60)
        print("  StormShadow Interactive Attack Console")
        print("=" * 60)
        print("\nAvailable commands:")
        print("  start <attack>  - Start an attack module")
        print("  stop <attack>   - Stop a running attack")
        print("  list            - List available attacks")
        print("  status          - Show status of all components")
        print("  monitor         - Show monitoring information")
        print("  logs <module>   - Show logs for a module")
        print("  config          - Show current configuration")
        print("  cleanup         - Clean up Docker containers")
        print("  help            - Show this help")
        print("  quit/exit       - Exit interactive mode")
        print()
    
    async def _interactive_loop(self) -> int:
        """Main interactive command loop."""
        while self.running:
            try:
                command = get_user_input("stormshadow> ").strip()
                
                if not command:
                    continue
                
                parts = command.split()
                cmd = parts[0].lower()
                
                if cmd in ['quit', 'exit', 'q']:
                    if await self._confirm_exit():
                        break
                elif cmd == 'start' and len(parts) > 1:
                    await self._start_attack_command(parts[1])
                elif cmd == 'stop' and len(parts) > 1:
                    await self._stop_attack_command(parts[1])
                elif cmd == 'list':
                    self._list_available_attacks()
                elif cmd == 'status':
                    await self._show_status_command()
                elif cmd == 'monitor':
                    await self._show_monitoring_command()
                elif cmd == 'logs' and len(parts) > 1:
                    await self._show_logs_command(parts[1])
                elif cmd == 'config':
                    self._show_config_command()
                elif cmd == 'cleanup':
                    await self._cleanup_command()
                elif cmd == 'help':
                    self._show_help_command()
                elif cmd == 'clear':
                    clear_terminal()
                else:
                    print_error(f"Unknown command: {command}")
                    print("Type 'help' for available commands")
                    
            except (EOFError, KeyboardInterrupt):
                print("\nExiting interactive mode...")
                break
            except Exception as e:
                print_error(f"Error in interactive loop: {e}")
        
        return 0
    
    async def _confirm_exit(self) -> bool:
        """Confirm exit with user."""
        if (self.orchestrator.active_labs or 
            self.orchestrator.active_attacks):
            return confirm_action(
                "There are active components. Are you sure you want to exit?"
            )
        return True
    
    async def _start_attack_command(self, attack_name: str):
        """Handle start attack command."""
        try:
            # Check if attack already running
            if attack_name in self.orchestrator.active_attacks:
                print_warning(f"Attack '{attack_name}' is already running")
                return
            
            # Create attack configuration
            attack_config: Dict[str, Any] = {
                'type': attack_name,
                'target_ip': self.config.get('target_ip', '127.0.0.1'),
                'target_port': self.config.get('target_port', 5060)
            }
            
            # Start the attack
            success = await self.orchestrator.start_attack_module(attack_config)
            
            if success:
                print_success(f"Started attack: {attack_name}")
            else:
                print_error(f"Failed to start attack: {attack_name}")
            
        except Exception as e:
            print_error(f"Error starting attack '{attack_name}': {e}")
    
    async def _stop_attack_command(self, attack_name: str):
        """Handle stop attack command."""
        if attack_name in self.orchestrator.active_attacks:
            try:
                success = await self.orchestrator.stop_attack_module(attack_name)
                if success:
                    print_success(f"Stopped attack: {attack_name}")
                else:
                    print_error(f"Failed to stop attack: {attack_name}")
            except Exception as e:
                print_error(f"Failed to stop attack '{attack_name}': {e}")
        else:
            print_warning(f"Attack '{attack_name}' is not running")
    
    def _list_available_attacks(self):
        """List available attack modules."""
        # Get available attacks from configuration or default list
        attack_configs = self.config.get('attacks', {}).get('modules', [])
        
        if attack_configs:
            available_attacks = [cfg.get('type', 'unknown') 
                               for cfg in attack_configs]
        else:
            # Default attacks
            available_attacks = [
                "inviteflood", "registrar", "sip-dos", "udp-flood"
            ]
        
        print("\nAvailable attacks:")
        for attack in available_attacks:
            status = ("RUNNING" if attack in self.orchestrator.active_attacks 
                     else "STOPPED")
            print(f"  {attack:20} [{status}]")
        print()
    
    async def _show_status_command(self):
        """Show system status."""
        status = self.orchestrator.get_system_status()
        
        print("\n" + "=" * 50)
        print("  System Status")
        print("=" * 50)
        
        # Component status
        print(f"\nActive Labs: {status['active_labs']}")
        for lab in self.orchestrator.active_labs:
            print(f"  - {lab}")
        
        print(f"\nActive Attacks: {status['active_attacks']}")
        for attack in self.orchestrator.active_attacks:
            print(f"  - {attack}")
        
        # Docker status
        if status['docker_available']:
            print(f"\nDocker Containers: {len(status['containers'])}")
            for container in status['containers']:
                print(f"  - {container['name']}: {container['status']}")
        else:
            print("\nDocker: Not available")
        
        # Network status
        print(f"\nDocker Networks: {len(status['networks'])}")
        for network in status['networks']:
            if network:  # Skip empty names
                print(f"  - {network}")
        
        print()
    
    async def _show_monitoring_command(self):
        """Show monitoring information."""
        print("\nMonitoring Sessions:")
        
        if self.monitoring_sessions:
            for name, session_id in self.monitoring_sessions.items():
                print(f"  {name:15}: {session_id}")
            
            print("\nTo access monitoring:")
            print("  - Use terminal manager to connect to sessions")
            print("  - Or use dedicated monitoring tools")
        else:
            print("  No monitoring sessions active")
        
        print()
    
    async def _show_logs_command(self, module_name: str):
        """Show logs for a specific module."""
        print(f"\nLogs for {module_name}:")
        print("-" * 30)
        
        # In a full implementation, you would retrieve actual logs
        # For now, show placeholder
        if module_name in self.orchestrator.active_attacks:
            print(f"Attack '{module_name}' is running")
            print("Log retrieval would be implemented here")
        elif module_name in self.orchestrator.active_labs:
            print(f"Lab '{module_name}' is running")
            print("Log retrieval would be implemented here")
        else:
            print(f"Module '{module_name}' is not active")
        
        print()
    
    def _show_config_command(self):
        """Show current configuration."""
        print("\nCurrent Configuration:")
        print("-" * 30)
        
        # Show key configuration items
        config_items = [
            'mode', 'role', 'verbosity', 'target_ip', 'target_port'
        ]
        
        for key in config_items:
            if key in self.config:
                value = self.config[key]
                print(f"{key:15}: {value}")
        
        # Show component status
        lab_enabled = self.config.get('lab', {}).get('enabled', True)
        attacks_enabled = self.config.get('attacks', {}).get('enabled', True)
        
        print(f"{'lab_enabled':15}: {lab_enabled}")
        print(f"{'attacks_enabled':15}: {attacks_enabled}")
        print()
    
    async def _cleanup_command(self):
        """Handle cleanup command."""
        if confirm_action("This will stop all containers. Continue?"):
            try:
                await self.orchestrator.cleanup_docker()
                print_success("Docker cleanup completed")
            except Exception as e:
                print_error(f"Error during cleanup: {e}")
    
    def _show_help_command(self):
        """Show help for interactive commands."""
        print("\nStormShadow Interactive Commands:")
        print("-" * 40)
        print("start <attack>  - Start an attack module")
        print("stop <attack>   - Stop a running attack")
        print("list            - List available attacks")
        print("status          - Show status of all components")
        print("monitor         - Show monitoring information")
        print("logs <module>   - Show logs for a module")
        print("config          - Show current configuration")
        print("cleanup         - Clean up Docker containers")
        print("clear           - Clear terminal screen")
        print("help            - Show this help")
        print("quit/exit       - Exit interactive mode")
        print()
