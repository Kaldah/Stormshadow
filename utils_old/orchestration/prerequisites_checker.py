"""
Prerequisites checker for StormShadow orchestration.

This module handles checking system prerequisites and requirements
before starting any components.
"""

from typing import Dict, Any
from ..core import print_error, print_warning, print_info, check_root
from ..network import IPTablesManager


class PrerequisitesChecker:
    """
    Handles checking system prerequisites for StormShadow operations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize prerequisites checker.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.force_bypass = config.get('force_bypass', False)
        self.is_root = check_root()
        
        # Determine what components are enabled
        self.role = config.get('role', 'both')
        self.lab_enabled = self.role in ['lab', 'both']
        self.attack_enabled = self.role in ['attack', 'both']
        
        # Determine IPTables requirements
        self.iptables_enabled = IPTablesManager.determine_iptables_requirements(config)
    
    def check_all_prerequisites(self) -> bool:
        """
        Check all system prerequisites.
        
        Returns:
            bool: True if all prerequisites are met
        """
        if not self._check_attack_prerequisites():
            return False
            
        if not self._check_lab_prerequisites():
            return False
            
        if not self._check_iptables_prerequisites():
            return False
            
        return True
    
    def _check_attack_prerequisites(self) -> bool:
        """Check attack-specific prerequisites."""
        if not self.attack_enabled:
            return True
            
        attacks_config = self.config.get('attacks', {})
        attack_modules = attacks_config.get('modules', [])
        
        # Check global attack root requirement
        global_need_root = attacks_config.get('need_root', True)
        
        # Check individual attack modules
        at_least_one_attack_needs_root = False
        if attack_modules:
            for attack_config in attack_modules:
                attack_need_root = attack_config.get('need_root', global_need_root)
                if attack_need_root:
                    at_least_one_attack_needs_root = True
                    break
        else:
            # No specific modules configured, use global setting
            at_least_one_attack_needs_root = global_need_root

        if at_least_one_attack_needs_root and not self.is_root:
            print_error(
                "Root privileges are mandatory for attack operations. "
                "To bypass, set 'need_root = false' in the attack "
                "configuration files."
            )
            return False
        elif not at_least_one_attack_needs_root:
            print_warning("Running attacks without root privileges "
                         "(explicitly allowed in config)")
        
        return True
    
    def _check_lab_prerequisites(self) -> bool:
        """Check lab-specific prerequisites."""
        if not self.lab_enabled:
            return True
            
        lab_config = self.config.get('lab', {})
        need_return_path = lab_config.get('need_return_path', False)
        lab_need_root = lab_config.get('need_root', True)
        
        if not self.is_root and not self.force_bypass:
            if need_return_path:
                print_error("Root privileges required to activate return path "
                           "(because of iptables). Use --force-bypass to override.")
                return False
            elif lab_need_root:
                print_error("Root privileges required for lab operations. "
                           "Use --force-bypass to override or change the config file.")
                return False
        elif not self.force_bypass and not lab_need_root:
            print_info("Running labs without root privileges "
                      "(explicitly allowed in config)")
        elif self.force_bypass:
            print_warning("Running labs without root privileges "
                         "(force-bypass enabled), change 'need_root' in lab "
                         "config to false to avoid this warning if you don't need root.")

        return True
    
    def _check_iptables_prerequisites(self) -> bool:
        """Check IPTables-specific prerequisites."""
        if not self.iptables_enabled:
            return True
            
        if not self.is_root:
            if not self.force_bypass:
                print_error("Root privileges required for iptables "
                           "operations. Use --force-bypass to override.")
                return False
            else:
                print_warning("Trying to use iptables without root privileges "
                             "iptables operations will probably NOT be applied "
                             "(force-bypass enabled)")

        return True
    
    def get_requirements_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all requirements.
        
        Returns:
            Dict containing requirement summary
        """
        return {
            'root_available': self.is_root,
            'force_bypass': self.force_bypass,
            'components': {
                'lab_enabled': self.lab_enabled,
                'attack_enabled': self.attack_enabled,
                'iptables_enabled': self.iptables_enabled
            },
            'requirements': {
                'attack_needs_iptables': IPTablesManager.check_attack_iptables_requirements(self.config),
                'lab_needs_iptables': IPTablesManager.check_lab_iptables_requirements(self.config)
            }
        }
