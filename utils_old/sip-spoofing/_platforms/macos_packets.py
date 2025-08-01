"""
macOS packet spoofing implementation for StormShadow packet interface.

This module provides placeholder implementation for macOS packet operations.
Currently returns "MACOS UNAVAILABLE" messages as requested.
"""

from typing import Dict, List, Any

from .._packet_interface import PacketInterface
from ...core import print_warning


class MacOSPacketImplementation(PacketInterface):
    """macOS implementation of packet interface."""
    
    def __init__(self):
        """Initialize macOS packet implementation."""
        print_warning("macOS packet operations are not available yet")
    
    def create_packet(self, packet_config: Dict[str, Any]) -> Any:
        """Create a packet based on configuration."""
        print_warning("MACOS UNAVAILABLE: create_packet not implemented yet")
        return None
    
    def send_packet(self, packet: Any, interface: str = None) -> bool:
        """Send a packet through specified interface."""
        print_warning("MACOS UNAVAILABLE: send_packet not implemented yet")
        return False
    
    def send_packets(self, packets: List[Any], interface: str = None) -> bool:
        """Send multiple packets."""
        print_warning("MACOS UNAVAILABLE: send_packets not implemented yet")
        return False
    
    def capture_packets(self, interface: str, filter_expr: str = None) -> List[Any]:
        """Capture packets from interface."""
        print_warning("MACOS UNAVAILABLE: capture_packets not implemented yet")
        return []
    
    def get_available_interfaces(self) -> List[str]:
        """Get list of available network interfaces."""
        print_warning("MACOS UNAVAILABLE: get_available_interfaces not implemented yet")
        return []
    
    def supports_raw_sockets(self) -> bool:
        """Check if platform supports raw sockets."""
        print_warning("MACOS UNAVAILABLE: supports_raw_sockets not implemented yet")
        return False
    
    def create_sip_packet(self, sip_config: Dict[str, Any]) -> Any:
        """Create a SIP packet."""
        print_warning("MACOS UNAVAILABLE: create_sip_packet not implemented yet")
        return None
