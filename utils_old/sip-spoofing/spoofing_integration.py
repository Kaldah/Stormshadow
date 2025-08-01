"""
High-level integration layer for StormShadow spoofing capabilities.

This module provides simple enable/disable functions for SIP spoofing
using the high-performance kernel-level spoofing system.
"""

from typing import Dict, Any, Optional
from .spoofing import create_sip_spoofer
from ..core import print_success, print_error, print_warning, print_info

# Global spoofing instance
_global_spoofing: Optional['SpoofingIntegration'] = None


class SpoofingIntegration:
    """Integration layer for managing spoofing state in StormShadow."""
    
    def __init__(self, spoofed_subnet: str = "10.10.123.0/25", 
                 attacker_ip: str = "143.53.142.93"):
        """Initialize the spoofing integration."""
        self.spoofed_subnet = spoofed_subnet
        self.attacker_ip = attacker_ip
        self.spoofer = None
        self.is_active = False
        
    def enable_spoofing(self) -> bool:
        """Enable high-performance SIP spoofing."""
        try:
            if self.is_active:
                print_warning("Spoofing is already active")
                return True
                
            print_info("Enabling IP spoofing...")
            self.spoofer = create_sip_spoofer(
                spoofed_subnet=self.spoofed_subnet,
                attacker_ip=self.attacker_ip
            )
            
            if self.spoofer.enable_spoofing():
                self.is_active = True
                print_success("✓ High-performance spoofing enabled successfully")
                return True
            else:
                print_error("✗ Failed to enable spoofing")
                return False
                
        except Exception as e:
            print_error(f"Error enabling spoofing: {e}")
            return False
    
    def disable_spoofing(self) -> bool:
        """Disable SIP spoofing."""
        try:
            if not self.is_active:
                print_warning("Spoofing is not active")
                return True
                
            print_info("Disabling SIP spoofing...")
            if self.spoofer and self.spoofer.disable_spoofing():
                self.is_active = False
                self.spoofer = None
                print_success("✓ Spoofing disabled successfully")
                return True
            else:
                print_error("✗ Failed to disable spoofing")
                return False
                
        except Exception as e:
            print_error(f"Error disabling spoofing: {e}")
            return False
    
    def get_spoofing_status(self) -> Dict[str, Any]:
        """Get current spoofing status."""
        if not self.is_active or not self.spoofer:
            return {
                'active': False,
                'spoofed_subnet': self.spoofed_subnet,
                'attacker_ip': self.attacker_ip
            }
        
        # Create basic stats since get_spoofing_stats doesn't exist yet
        stats = {
            'active': True,
            'spoofed_subnet': self.spoofed_subnet,
            'attacker_ip': self.attacker_ip,
            'performance_mode': 'kernel-level'
        }
        return stats


# Global functions for easy integration
def enable_sip_spoofing(spoofed_subnet: str = "10.10.123.0/25",
                       attacker_ip: str = "143.53.142.93") -> bool:
    """
    Enable high-performance SIP spoofing globally.
    
    Args:
        spoofed_subnet: The subnet to spoof (CIDR notation)
        attacker_ip: The attacker's IP address
        
    Returns:
        bool: True if spoofing was enabled successfully
    """
    global _global_spoofing
    
    try:
        if _global_spoofing is None:
            _global_spoofing = SpoofingIntegration(spoofed_subnet, attacker_ip)
        
        return _global_spoofing.enable_spoofing()
    except Exception as e:
        print_error(f"Failed to enable global spoofing: {e}")
        return False


def disable_sip_spoofing() -> bool:
    """
    Disable SIP spoofing globally.
    
    Returns:
        bool: True if spoofing was disabled successfully
    """
    global _global_spoofing
    
    if _global_spoofing is None:
        return True
        
    return _global_spoofing.disable_spoofing()


def get_spoofing_status() -> Dict[str, Any]:
    """Get current global spoofing status."""
    global _global_spoofing
    
    if _global_spoofing is not None:
        return _global_spoofing.get_spoofing_status()
    
    return {'active': False}


def is_spoofing_active() -> bool:
    """Check if spoofing is currently active."""
    status = get_spoofing_status()
    return status.get('active', False)


def print_spoofing_status():
    """Print current spoofing status to console."""
    try:
        status = get_spoofing_status()
        
        print_info("StormShadow Spoofing Status")
        print_info("=" * 30)
        
        if status['active']:
            print_success("Status: ACTIVE")
            if 'spoofed_subnet' in status:
                print_info(f"Spoofed Subnet: {status['spoofed_subnet']}")
            if 'attacker_ip' in status:
                print_info(f"Attacker IP: {status['attacker_ip']}")
            if 'performance_mode' in status:
                print_info(f"Mode: {status['performance_mode']}")
        else:
            print_error("Status: INACTIVE")
            
    except Exception as e:
        print_error(f"Error getting spoofing status: {e}")
