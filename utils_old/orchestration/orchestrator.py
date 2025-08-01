"""
Streamlined orchestrator for StormShadow operations.

This orchestrator focuses on pure orchestration by delegating specialized
tasks to the existing utility managers.
"""

import signal
import asyncio
from typing import Dict, Any, Optional, List

from ..core import (print_error, print_warning, print_info, print_success,
                    check_root)
from ..docker import ContainerManager, NetworkManager, ImageManager
from ..network import IPTablesManager
from ..terminal import TerminalManager, ProcessMonitor
from ..lab import LabManager
from ..registry import LabModule
from ..attack import AttackManager
from .prerequisites_checker import PrerequisitesChecker
from .status_manager import SystemStatusManager as StatusManager

class StormShadowOrchestrator:
    """
    Streamlined orchestrator that delegates to specialized utility managers.

    This orchestrator focuses purely on orchestration while letting existing
    utility managers handle their specialized tasks.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the orchestrator with utility managers."""
        self.config = config

        # Initialize core managers
        self.container_manager = ContainerManager()
        self.network_manager = NetworkManager()
        self.image_manager = ImageManager()
        self.iptables_manager = IPTablesManager()
        self.terminal_manager = TerminalManager()
        self.process_monitor = ProcessMonitor()
        self.lab_manager = LabManager()
        self.attack_manager = AttackManager(config.get('attacks', {}))

        # Initialize optional utilities
        self.prerequisites_checker: Optional[Any] = (
            PrerequisitesChecker(config) if PrerequisitesChecker else None
        )
        self.status_manager: Optional[Any] = (
            StatusManager(self) if StatusManager else None
        )

        # Configuration-based properties
        self.dry_run = config.get('dry_run', False)
        self.role = config.get('role', 'both')
        self.mode = config.get('mode', 'local')
        self.lab_enabled = self.role in ['lab', 'both']
        self.attack_enabled = self.role in ['attack', 'both']
        self.isRoot = check_root()

        # Determine IPTables requirements using the manager
        lab_iptables = self.iptables_manager.check_lab_iptables_requirements(
            config.get('lab', {})
        )
        attack_iptables = (
            self.iptables_manager.check_attack_iptables_requirements(
                config.get('attacks', {})
            )
        )
        self.iptables_enabled = lab_iptables or attack_iptables

        # Component state tracking
        self.active_labs: List[Any] = []  # Now stores lab objects
        # Use attack manager for attack tracking
        # self.active_attacks is now provided via property

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        print_info("StormShadow orchestrator initialized")

    @property
    def active_attacks(self) -> List[str]:
        """Get list of active attacks from attack manager."""
        return list(self.attack_manager.active_attacks.keys())

    def _signal_handler(self, signum: int, frame: Optional[Any]) -> None:
        """Handle shutdown signals gracefully."""
        print_info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(self.cleanup())

    async def run(self) -> int:
        """Main orchestration flow."""
        try:
            # Step 1: Check prerequisites
            if not self._check_prerequisites():
                return 1

            # Step 2: Setup environment
            if not await self._setup_environment():
                return 1

            # Step 3: Handle interactive mode
            if self.config.get('interactive', False):
                from .interactive_manager import InteractiveManager
                interactive_manager = InteractiveManager(self)
                return await interactive_manager.run()

            # Step 4: Start components
            print_info(f"Running in {self.mode} mode")

            if self.lab_enabled and not await self._start_labs():
                return 1

            if self.attack_enabled and not await self._start_attacks():
                return 1

            # Step 5: Monitor and wait
            if self._has_persistent_components():
                await self._wait_for_completion()

        except KeyboardInterrupt:
            print_info("Interrupted by user")
            return 130
        except Exception as e:
            print_error(f"Orchestration failed: {e}")
            if self.config.get('verbosity', 'info') in ['debug', 'trace']:
                import traceback
                traceback.print_exc()
            return 1
        finally:
            await self.cleanup()

        return 0

    def _check_prerequisites(self) -> bool:
        """Check prerequisites using specialized checker or fallback."""
        if self.prerequisites_checker:
            return self.prerequisites_checker.check_all_prerequisites()

        # Simple fallback check
        if (self.iptables_enabled and not self.isRoot and
                not self.config.get('force_bypass', False)):
            print_error("Root privileges required for iptables operations")
            return False

        return True

    async def _setup_environment(self) -> bool:
        """Setup environment by delegating to managers."""
        if self.dry_run:
            print_info("[Dry-run] Environment setup simulation")
            return True

        # Setup IPTables using the manager
        if self.iptables_enabled:
            iptables_config = self.config.get('iptables', {'enabled': True})
            if not self.iptables_manager.apply_configuration(iptables_config):
                print_error("Failed to setup iptables")
                return False
            print_success("IPTables configured")

        # Setup Docker networks using network manager
        if self._needs_docker_setup():
            if not await self._setup_docker_environment():
                return False

        print_success("Environment setup completed")
        return True

    def _needs_docker_setup(self) -> bool:
        """Check if Docker setup is needed."""
        lab_config = self.config.get('lab', {})
        return (lab_config.get('type') == 'docker' or
                lab_config.get('containers') or
                lab_config.get('modules', []))

    async def _setup_docker_environment(self) -> bool:
        """Setup Docker environment using managers."""
        try:
            # Check if stormshadow network exists using network manager
            networks = self.network_manager.list_networks()
            if not any(net.get('Name') == 'stormshadow' for net in networks):
                success = self.network_manager.create_network(
                    name="stormshadow",
                    driver="bridge",
                    subnet="172.20.0.0/16"
                )
                if not success:
                    print_error("Failed to create Docker network")
                    return False
                print_info("Created stormshadow Docker network")

            return True
        except Exception as e:
            print_error(f"Docker environment setup failed: {e}")
            return False

    async def _start_labs(self) -> bool:
        """Start labs using the new lab factory system."""
        lab_config = self.config.get('lab', {})

        if not lab_config.get('modules') and lab_config.get('enabled', True):
            # Start default lab with default configuration
            from utils.lab import create_lab
            
            default_config = {
                'container_name': 'stormshadow-default-lab',
                'sip_port': 5060,
                'sip_users': ['200', '201', '202'],
                'network': 'bridge',
                'open_terminal': True  # Enable terminal opening by default
            }
            
            lab = create_lab('default-lab', 'default-lab', default_config)
            if lab and await lab.start():
                self.active_labs.append(lab)
                print_success("Default lab started")
                return True
            else:
                print_error("Failed to start default lab")
                return False

        elif lab_config.get('modules'):
            # Start configured lab modules using new factory system
            lab_modules = lab_config.get('modules', [])
            for module in lab_modules:
                from utils.lab import create_lab
                
                lab_type = module.get('type', 'default-lab')
                lab_name = module.get('name', f'{lab_type}-instance')
                
                # Extract lab configuration from module
                lab_config_dict = {k: v for k, v in module.items() 
                                 if k not in ['type', 'name', 'force_rebuild']}
                
                lab = create_lab(lab_type, lab_name, lab_config_dict)
                if lab and await lab.start():
                    self.active_labs.append(lab)
                    print_success(f"Started lab: {lab_name}")
                else:
                    print_error(f"Failed to start lab module: {lab_type}")
                    return False

            return True
        
        # Lab is disabled or no configuration provided
        return True

    async def _start_attacks(self) -> bool:
        """Start attacks using attack manager."""
        attack_modules = self.config.get('attacks', {}).get('modules', [])

        if not attack_modules:
            print_info("No attack modules configured")
            return True

        for attack_config in attack_modules:
            attack_name = attack_config.get('name', attack_config.get('type', 'unknown'))
            
            # Start attack using attack manager
            success = await self.attack_manager.start_attack(attack_name, attack_config)
            if not success:
                print_error(f"Failed to start attack: {attack_name}")
                return False
            
            print_success(f"Attack started: {attack_name}")

        return True

    def _has_persistent_components(self) -> bool:
        """Check if there are components that need to keep running."""
        has_components = bool(self.active_labs or self.active_attacks or
                            self.config.get('interactive', False))
        print_info(f"Persistent components check: labs={len(self.active_labs)}, attacks={len(self.active_attacks)}, result={has_components}")
        return has_components

    async def _wait_for_completion(self) -> None:
        """Wait for components to complete or user interrupt."""
        print_info("Components running. Press Ctrl+C to stop.")
        print_info(f"Active labs: {[lab.name for lab in self.active_labs]}")
        try:
            while self.active_labs or self.active_attacks:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print_info("Stopping components...")

    async def cleanup(self) -> None:
        """Clean up all components using managers."""
        print_info("Cleaning up components...")

        # Stop labs using new lab system
        for lab in self.active_labs[:]:
            try:
                if await lab.stop():
                    print_success(f"Stopped lab: {lab.name}")
                else:
                    print_warning(f"Failed to stop lab: {lab.name}")
            except Exception as e:
                print_error(f"Error stopping lab {lab.name}: {e}")
                # Try emergency stop if available
                if hasattr(lab, 'emergency_stop'):
                    lab.emergency_stop()
            self.active_labs.remove(lab)

        # Clean up attacks using attack manager
        await self.attack_manager.cleanup()

        # Clean up Docker using container manager
        try:
            containers = self.container_manager.list_containers()
            for container in containers:
                if 'stormshadow' in container.get('Names', []):
                    self.container_manager.stop_container(container['Id'])
                    self.container_manager.remove_container(container['Id'])
        except Exception as e:
            print_warning(f"Docker cleanup issues: {e}")

        # Clean up IPTables
        if self.iptables_enabled:
            try:
                await self.iptables_manager.cleanup()
            except Exception as e:
                print_warning(f"IPTables cleanup issues: {e}")

        # Clean up terminal sessions
        try:
            # Terminal manager should handle session cleanup
            pass
        except Exception as e:
            print_warning(f"Terminal cleanup issues: {e}")

        print_success("Cleanup completed")

    # Public interfaces for external use
    async def start_labs(self) -> bool:
        """Public interface for starting labs."""
        return await self._start_labs()

    async def start_attack_module(self, attack_config: Dict[str, Any]) -> bool:
        """Public interface for starting a specific attack."""
        attack_name = attack_config.get('type', 'unknown')
        return await self.attack_manager.start_attack(attack_name, attack_config)

    async def stop_attack_module(self, attack_name: str) -> bool:
        """Public interface for stopping a specific attack."""
        return await self.attack_manager.stop_attack(attack_name)

    async def cleanup_docker(self) -> None:
        """Clean up Docker containers and networks."""
        try:
            # Clean up containers
            containers = self.container_manager.list_containers()
            for container in containers:
                if 'stormshadow' in container.get('Names', []):
                    self.container_manager.stop_container(container['Id'])
                    self.container_manager.remove_container(container['Id'])
            
            # Clean up networks if needed
            print_success("Docker cleanup completed")
        except Exception as e:
            print_error(f"Docker cleanup error: {e}")
            raise

    def get_system_status(self) -> Any:
        """Get system status using status manager or fallback."""
        if self.status_manager is not None:
            # Type: ignore is used since status_manager and collect_status
            # are dynamically imported
            return self.status_manager.collect_status(  # type: ignore
                config=self.config,
                lab_manager=self.lab_manager,
                iptables_manager=self.iptables_manager,
                metrics_collector=None
            )

        # Fallback status
        return {
            'active_labs': len(self.active_labs),
            'active_attacks': len(self.active_attacks),
            'iptables_enabled': self.iptables_enabled,
            'root_available': self.isRoot,
            'mode': self.mode,
            'role': self.role
        }

    def get_iptables_requirements(self) -> Dict[str, Any]:
        """Get IPTables requirements using the manager."""
        attack_reqs = self.iptables_manager.check_attack_iptables_requirements(
            self.config.get('attacks', {})
        )
        lab_reqs = self.iptables_manager.check_lab_iptables_requirements(
            self.config.get('lab', {})
        )
        return {
            'iptables_enabled': self.iptables_enabled,
            'attack_requirements': attack_reqs,
            'lab_requirements': lab_reqs
        }
