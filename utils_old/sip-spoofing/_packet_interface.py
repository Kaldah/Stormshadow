"""
Internal packet spoofing interface for cross-platform packet operations.

This module provides the internal interface for packet spoofing
across different platforms (Linux, Windows, macOS).
"""

import platform
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple


class PacketInterface(ABC):
    """Abstract interface for packet spoofing operations."""
    
    @abstractmethod
    def create_packet(self, packet_config: Dict[str, Any]) -> Any:
        """Create a packet based on configuration."""
        pass
    
    @abstractmethod
    def send_packet(self, packet: Any, interface: str = None) -> bool:
        """Send a packet through specified interface."""
        pass
    
    @abstractmethod
    def send_packets(self, packets: List[Any], interface: str = None) -> bool:
        """Send multiple packets."""
        pass
    
    @abstractmethod
    def capture_packets(self, interface: str, filter_expr: str = None) -> List[Any]:
        """Capture packets from interface."""
        pass
    
    @abstractmethod
    def get_available_interfaces(self) -> List[str]:
        """Get list of available network interfaces."""
        pass
    
    @abstractmethod
    def supports_raw_sockets(self) -> bool:
        """Check if platform supports raw sockets."""
        pass
    
    @abstractmethod
    def create_sip_packet(self, sip_config: Dict[str, Any]) -> Any:
        """Create a SIP packet."""
        pass


def get_packet_handler() -> PacketInterface:
    """Get the appropriate packet handler for current platform."""
    system = platform.system().lower()
    
    if system == "linux":
        from ._platforms.linux_packets import LinuxPacketImplementation
        return LinuxPacketImplementation()
    elif system == "windows":
        from ._platforms.windows_packets import WindowsPacketImplementation
        return WindowsPacketImplementation()
    elif system == "darwin":
        from ._platforms.macos_packets import MacOSPacketImplementation
        return MacOSPacketImplementation()
    else:
        raise RuntimeError(f"Unsupported platform: {system}")


# Convenience functions to maintain existing API
def create_packet(packet_config: Dict[str, Any]) -> Any:
    """Create a packet (cross-platform)."""
    handler = get_packet_handler()
    return handler.create_packet(packet_config)


def send_packet(packet: Any, interface: str = None) -> bool:
    """Send a packet (cross-platform)."""
    handler = get_packet_handler()
    return handler.send_packet(packet, interface)


def send_packets(packets: List[Any], interface: str = None) -> bool:
    """Send multiple packets (cross-platform)."""
    handler = get_packet_handler()
    return handler.send_packets(packets, interface)


def capture_packets(interface: str, filter_expr: str = None) -> List[Any]:
    """Capture packets (cross-platform)."""
    handler = get_packet_handler()
    return handler.capture_packets(interface, filter_expr)


def create_sip_packet(sip_config: Dict[str, Any]) -> Any:
    """Create a SIP packet (cross-platform)."""
    handler = get_packet_handler()
    return handler.create_sip_packet(sip_config)
