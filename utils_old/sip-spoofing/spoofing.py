"""
IP spoofing system for StormShadow.

This module provides kernel-level IP spoofing by leveraging the existing
IPTablesManager for maximum performance, avoiding userspace packet processing.
"""

import random
import ipaddress
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

# Use existing StormShadow utilities
from ..network import IPTablesManager
from ..core import print_error, print_warning, print_info, print_success


@dataclass
class SpoofingConfig:
    """Configuration for spoofing."""
    spoofed_subnet: str = "10.10.123.0/25"
    target_port: int = 5060
    protocol: str = "udp"
    attacker_ip: str = "143.53.142.93"
    ack_port: int = 4000
    enable_return_path: bool = True


class SpoofingManager:
    """
    IP spoofing using kernel-level iptables rules.
    
    Uses the existing StormShadow IPTablesManager for maximum performance
    by handling spoofing entirely at the kernel level.
    """

    def __init__(self, config: Optional[SpoofingConfig] = None):
        """Initialize spoofing manager."""
        self.config = config or SpoofingConfig()
        self.logger = logging.getLogger(__name__)
        
        # Use existing StormShadow IPTablesManager
        self.iptables = IPTablesManager(require_root=True)
        
        # Initialize IP pools
        self._init_spoofed_ips()
        
        # Track active rules for cleanup
        self.active_rules: List[str] = []
        self.active_snat_ip: Optional[str] = None  # Store the actual IP used in SNAT
        self.is_active = False

    def _init_spoofed_ips(self):
        """Initialize spoofed IP pool."""
        try:
            network = ipaddress.ip_network(self.config.spoofed_subnet, strict=False)
            self.spoofed_ips = list(network.hosts())
            print_info(f"Initialized {len(self.spoofed_ips)} spoofed IPs from {self.config.spoofed_subnet}")
        except Exception as e:
            print_error(f"Failed to initialize spoofed IPs: {e}")
            self.spoofed_ips = []

    def enable_spoofing(self) -> bool:
        """Enable spoofing using kernel-level iptables rules."""
        if self.is_active:
            print_warning("Spoofing already active")
            return True
        
        try:
            print_info("Enabling IP spoofing...")
            
            # Setup SNAT rules for outgoing packet spoofing
            success = self._setup_snat_rules()
            if not success:
                print_error("Failed to setup SNAT rules")
                return False
            
            # Setup DNAT rules for return path (if enabled)
            if self.config.enable_return_path:
                success = self._setup_dnat_rules()
                if not success:
                    print_error("Failed to setup DNAT rules")
                    self._cleanup_snat_rules()
                    return False
            
            self.is_active = True
            print_success("✓ IP spoofing enabled")
            return True
            
        except Exception as e:
            print_error(f"Failed to enable spoofing: {e}")
            return False

    def disable_spoofing(self) -> bool:
        """Disable spoofing and cleanup all rules."""
        if not self.is_active:
            return True
        
        try:
            print_info("Disabling IP spoofing...")
            
            # Use the enhanced cleanup if available
            try:
                from ..network.cleanup import IPTablesCleanup
                cleanup = IPTablesCleanup(self.iptables)
                success = cleanup.cleanup_tracked_rules()
                
                if success:
                    self.is_active = False
                    self.active_rules.clear()
                    self.active_snat_ip = None
                    print_success("✓ IP spoofing disabled successfully")
                    return True
                else:
                    print_warning("Enhanced cleanup had issues, trying manual cleanup...")
                    # Fall back to manual cleanup
                    return self._manual_cleanup()
                    
            except ImportError:
                # Fall back to manual cleanup if enhanced cleanup not available
                return self._manual_cleanup()
            
        except Exception as e:
            print_error(f"Error disabling spoofing: {e}")
            return False
    
    def _manual_cleanup(self) -> bool:
        """Manual cleanup fallback method."""
        success = True
        
        # Cleanup SNAT rules
        if not self._cleanup_snat_rules():
            success = False
        
        # Cleanup DNAT rules
        if self.config.enable_return_path:
            if not self._cleanup_dnat_rules():
                success = False
        
        self.is_active = False
        
        if success:
            print_success("✓ IP spoofing disabled successfully")
        else:
            print_warning("Some cleanup operations failed")
        
        return success

    def _setup_snat_rules(self) -> bool:
        """Setup SNAT rules for outgoing packet spoofing."""
        try:
            # Use a single random IP instead of a range for better compatibility
            spoofed_ip = self.get_random_spoofed_ip()
            self.active_snat_ip = spoofed_ip  # Store for cleanup
            
            rule = (
                f"-p {self.config.protocol} "
                f"--dport {self.config.target_port} "
                f"-j SNAT --to-source {spoofed_ip}"
            )
            
            print_info(f"Adding SNAT rule for port {self.config.target_port} (spoofed IP: {spoofed_ip})")
            success = self.iptables.add_rule(
                table="nat",
                chain="POSTROUTING", 
                rule=rule,
                comment="StormShadow-spoofing"
            )
            
            if success:
                self.active_rules.append("snat_main")
                print_success("✓ SNAT rule added successfully")
                return True
            else:
                print_error("Failed to add SNAT rule")
                return False
                
        except Exception as e:
            print_error(f"Failed to setup SNAT rules: {e}")
            return False

    def _setup_dnat_rules(self) -> bool:
        """Setup DNAT rules for return path routing."""
        try:
            rule = (
                f"-p {self.config.protocol} "
                f"--sport {self.config.target_port} "
                f"-d {self.config.spoofed_subnet} "
                f"-j DNAT --to-destination {self.config.attacker_ip}:{self.config.ack_port}"
            )
            
            print_info(f"Adding DNAT rule for return path")
            success = self.iptables.add_rule(
                table="nat",
                chain="OUTPUT",
                rule=rule,
                comment="StormShadow-return-path"
            )
            
            if success:
                self.active_rules.append("dnat_main")
                print_success("✓ DNAT rule added successfully")
                return True
            else:
                print_error("Failed to add DNAT rule")
                return False
                
        except Exception as e:
            print_error(f"Failed to setup DNAT rules: {e}")
            return False

    def _get_snat_range(self) -> str:
        """Get SNAT range for source IP spoofing."""
        if len(self.spoofed_ips) < 2:
            return str(self.spoofed_ips[0]) if self.spoofed_ips else "192.168.1.100"
        else:
            first_ip = str(self.spoofed_ips[0])
            last_ip = str(self.spoofed_ips[-1])
            return f"{first_ip}-{last_ip}"

    def _cleanup_snat_rules(self) -> bool:
        """Cleanup SNAT rules."""
        try:
            if "snat_main" not in self.active_rules:
                return True
            
            # Clean up by line numbers
            print_info("Cleaning up SNAT rules...")
            
            from ..core import run_command
            result = run_command(
                ['iptables', '-t', 'nat', '-L', 'POSTROUTING', '--line-numbers', '-n'],
                capture_output=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[2:]  # Skip headers
                
                # Find StormShadow rules (in reverse order to maintain line numbers)
                for line in reversed(lines):
                    if 'StormShadow-spoofing' in line:
                        parts = line.split()
                        if parts:
                            line_num = parts[0]
                            delete_result = run_command(
                                ['iptables', '-t', 'nat', '-D', 'POSTROUTING', line_num],
                                capture_output=True
                            )
                            
                            if delete_result.returncode == 0:
                                print_success(f"✓ SNAT rule #{line_num} removed")
                            else:
                                print_warning(f"Failed to remove SNAT rule #{line_num}")
            
            self.active_rules.remove("snat_main")
            self.active_snat_ip = None
            return True
                
        except Exception as e:
            print_error(f"Error removing SNAT rules: {e}")
            return False

    def _cleanup_dnat_rules(self) -> bool:
        """Cleanup DNAT rules."""
        try:
            if "dnat_main" not in self.active_rules:
                return True
            
            # Clean up by line numbers
            print_info("Cleaning up DNAT rules...")
            
            from ..core import run_command
            result = run_command(
                ['iptables', '-t', 'nat', '-L', 'OUTPUT', '--line-numbers', '-n'],
                capture_output=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[2:]  # Skip headers
                
                # Find StormShadow rules (in reverse order to maintain line numbers)
                for line in reversed(lines):
                    if 'StormShadow-return-path' in line:
                        parts = line.split()
                        if parts:
                            line_num = parts[0]
                            delete_result = run_command(
                                ['iptables', '-t', 'nat', '-D', 'OUTPUT', line_num],
                                capture_output=True
                            )
                            
                            if delete_result.returncode == 0:
                                print_success(f"✓ DNAT rule #{line_num} removed")
                            else:
                                print_warning(f"Failed to remove DNAT rule #{line_num}")
            
            self.active_rules.remove("dnat_main")
            return True
                
        except Exception as e:
            print_error(f"Error removing DNAT rules: {e}")
            return False

    def get_random_spoofed_ip(self) -> str:
        """Get a random IP from the spoofed pool."""
        if not self.spoofed_ips:
            return "192.168.1.100"
        return str(random.choice(self.spoofed_ips))

    def get_statistics(self) -> Dict[str, str]:
        """Get spoofing statistics."""
        return {
            'active': str(self.is_active),
            'spoofed_subnet': self.config.spoofed_subnet,
            'available_spoofed_ips': str(len(self.spoofed_ips)),
            'target_port': str(self.config.target_port),
            'protocol': self.config.protocol,
            'active_rules': str(len(self.active_rules)),
            'return_path_enabled': str(self.config.enable_return_path)
        }


def create_sip_spoofer(
    spoofed_subnet: str = "10.10.123.0/25",
    attacker_ip: str = "143.53.142.93"
) -> SpoofingManager:
    """Create SIP spoofer using existing StormShadow infrastructure."""
    config = SpoofingConfig(
        spoofed_subnet=spoofed_subnet,
        target_port=5060,
        protocol="udp",
        attacker_ip=attacker_ip,
        ack_port=4000,
        enable_return_path=True
    )
    
    return SpoofingManager(config)
