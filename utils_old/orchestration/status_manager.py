"""
System status manager for StormShadow orchestration.

This module handles collecting and providing system status information
for monitoring, GUI interfaces, and diagnostics.
"""

import subprocess
from typing import Dict, Any, List, TYPE_CHECKING
from ..core import print_error

if TYPE_CHECKING:
    from .orchestrator import StormShadowOrchestrator


class SystemStatusManager:
    """
    Manages system status information for StormShadow.
    """
    
    def __init__(self, orchestrator: "StormShadowOrchestrator"):
        """
        Initialize status manager.
        
        Args:
            orchestrator: Reference to the orchestrator instance
        """
        self.orchestrator = orchestrator
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            Dict containing complete system status
        """
        status: Dict[str, Any] = {
            'components': self._get_component_status(),
            'docker': self._get_docker_status(),
            'iptables': self._get_iptables_status(),
            'networks': self._get_network_status()
        }
        
        return status
    
    def _get_component_status(self) -> Dict[str, Any]:
        """Get status of StormShadow components."""
        return {
            'active_labs': len(self.orchestrator.active_labs),
            'active_attacks': len(self.orchestrator.active_attacks),
            'lab_enabled': self.orchestrator.lab_enabled,
            'attack_enabled': self.orchestrator.attack_enabled,
            'monitoring_sessions': len(getattr(self.orchestrator, 'monitoring_sessions', []))
        }
    
    def _get_docker_status(self) -> Dict[str, Any]:
        """Get Docker system status."""
        docker_status: Dict[str, Any] = {
            'available': False,
            'daemon_running': False,
            'containers': [],
            'stormshadow_containers': 0
        }
        
        try:
            # Check Docker availability
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                docker_status['available'] = True
                
                # Check daemon status
                result = subprocess.run(['docker', 'info'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    docker_status['daemon_running'] = True
                    
                    # Get container information
                    result = subprocess.run(['docker', 'ps', '--format', 
                                           'table {{.Names}}\\t{{.Status}}'], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\\n')[1:]  # Skip header
                        for line in lines:
                            if line.strip():
                                parts = line.split('\\t')
                                if len(parts) >= 2:
                                    container_info = {
                                        'name': parts[0],
                                        'status': parts[1]
                                    }
                                    docker_status['containers'].append(container_info)
                                    
                                    # Count StormShadow containers
                                    if 'stormshadow' in parts[0].lower():
                                        docker_status['stormshadow_containers'] += 1
                                        
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            pass  # Docker not available
        
        return docker_status
    
    def _get_iptables_status(self) -> Dict[str, Any]:
        """Get IPTables status and requirements."""
        return {
            'enabled': self.orchestrator.iptables_enabled,
            'attack_requirements': getattr(self.orchestrator, 'attack_iptables_enabled', False),
            'lab_requirements': getattr(self.orchestrator, 'lab_iptables_enabled', False),
            'root_available': getattr(self.orchestrator, 'isRoot', False),
            'requirements_breakdown': self._get_iptables_requirements_breakdown()
        }
    
    def _get_iptables_requirements_breakdown(self) -> Dict[str, Any]:
        """Get detailed IPTables requirements breakdown."""
        breakdown = {
            'attack_details': self._get_attack_iptables_details(),
            'lab_details': self._get_lab_iptables_details()
        }
        return breakdown
    
    def _get_attack_iptables_details(self) -> Dict[str, Any]:
        """Get detailed attack IPTables requirements."""
        if not self.orchestrator.attack_enabled:
            return {'enabled': False, 'reason': 'attacks_disabled'}
            
        attacks_config = self.orchestrator.config.get('attacks', {})
        details: Dict[str, Any] = {
            'global_need_iptables': attacks_config.get('need_iptables', False),
            'global_need_return_path': attacks_config.get('need_return_path', False),
            'modules': []
        }
        
        # Check individual attack modules
        attack_modules = attacks_config.get('modules', [])
        for attack_config in attack_modules:
            module_details: Dict[str, Any] = {
                'type': attack_config.get('type', 'unknown'),
                'name': attack_config.get('name', attack_config.get('type', 'unknown')),
                'need_iptables': attack_config.get('need_iptables', False),
                'need_return_path': attack_config.get('need_return_path', False)
            }
            details['modules'].append(module_details)
            
        return details
    
    def _get_lab_iptables_details(self) -> Dict[str, Any]:
        """Get detailed lab IPTables requirements."""
        if not self.orchestrator.lab_enabled:
            return {'enabled': False, 'reason': 'labs_disabled'}
            
        lab_config = self.orchestrator.config.get('lab', {})
        details: Dict[str, Any] = {
            'global_need_iptables': lab_config.get('need_iptables', False),
            'global_need_return_path': lab_config.get('need_return_path', False),
            'modules': []
        }
        
        # Check individual lab modules
        lab_modules = lab_config.get('modules', [])
        for lab_module in lab_modules:
            module_details: Dict[str, Any] = {
                'type': lab_module.get('type', 'unknown'),
                'name': lab_module.get('name', lab_module.get('type', 'unknown')),
                'need_iptables': lab_module.get('need_iptables', False),
                'need_return_path': lab_module.get('need_return_path', False),
                'is_docker_lab': self._is_docker_lab(lab_module)
            }
            details['modules'].append(module_details)
            
        return details
    
    def _get_network_status(self) -> List[str]:
        """Get network status."""
        try:
            networks = self.orchestrator.network_manager.list_networks()
            return [n.get('Name', '') for n in networks]
        except Exception as e:
            print_error(f"Error getting network status: {e}")
            return []
    
    def _is_docker_lab(self, lab_module: Dict[str, Any]) -> bool:
        """
        Determine if a lab module requires Docker.
        
        Args:
            lab_module: Lab module configuration
            
        Returns:
            bool: True if lab requires Docker
        """
        # Check if lab explicitly specifies Docker requirement
        if 'use_docker' in lab_module:
            return lab_module['use_docker']
        
        # Check for Docker-specific configuration
        docker_indicators = [
            'container_name', 'image', 'network', 
            'ports', 'environment', 'volumes'
        ]
        
        return any(key in lab_module for key in docker_indicators)
    
    def get_component_details(self, component_type: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific component type.
        
        Args:
            component_type: 'lab' or 'attack'
            
        Returns:
            Dict containing component details
        """
        if component_type == 'lab':
            return self._get_lab_component_details()
        elif component_type == 'attack':
            return self._get_attack_component_details()
        else:
            return {}
    
    def _get_lab_component_details(self) -> Dict[str, Any]:
        """Get detailed lab component information."""
        lab_config = self.orchestrator.config.get('lab', {})
        lab_modules = lab_config.get('modules', [])
        
        docker_labs = [module for module in lab_modules 
                      if self._is_docker_lab(module)]
        script_labs = [module for module in lab_modules 
                      if not self._is_docker_lab(module)]
        
        return {
            'total_modules': len(lab_modules),
            'docker_labs': len(docker_labs),
            'script_labs': len(script_labs),
            'active_labs': self.orchestrator.active_labs,
            'modules': lab_modules
        }
    
    def _get_attack_component_details(self) -> Dict[str, Any]:
        """Get detailed attack component information."""
        attacks_config = self.orchestrator.config.get('attacks', {})
        attack_modules = attacks_config.get('modules', [])
        
        return {
            'total_modules': len(attack_modules),
            'active_attacks': self.orchestrator.active_attacks,
            'modules': attack_modules
        }
