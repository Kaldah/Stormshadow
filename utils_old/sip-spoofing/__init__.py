"""
Spoofing and packet handling system for StormShadow.

This module provides IP spoofing system using kernel-level
iptables rules for maximum performance in SIP attacks.
"""

from .base_handler import BasePacketHandler
from .sip_handler import SIPPacketHandler
from .spoofing_manager import SpoofingManager as SessionManager
from .spoofing import SpoofingManager, create_sip_spoofer
from .spoofing_integration import enable_sip_spoofing, disable_sip_spoofing, is_spoofing_active

# Cross-platform packet interface
from ._packet_interface import (
    get_packet_handler,
    create_packet,
    send_packet,
    send_packets,
    capture_packets,
    create_sip_packet
)

__all__ = [
    'BasePacketHandler',
    'SIPPacketHandler', 
    'SessionManager',  # Original spoofing manager for sessions
    'SpoofingManager',  # Main IP spoofing manager
    'create_sip_spoofer',
    'enable_sip_spoofing',
    'disable_sip_spoofing',
    'is_spoofing_active',
    # Cross-platform packet functions
    'get_packet_handler',
    'create_packet',
    'send_packet',
    'send_packets',
    'capture_packets',
    'create_sip_packet'
]