"""
Base packet handler interface for StormShadow spoofing system.

Provides an abstract interface that protocol-specific handlers must implement
to support session management and packet manipulation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
import logging


class BasePacketHandler(ABC):
    """
    Abstract base class for protocol-specific packet handlers.

    This class defines the interface that all packet handlers must implement
    to provide protocol-specific packet manipulation capabilities.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the packet handler.

        Args:
            config: Handler-specific configuration
        """
        self.config = config
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self._session_cache: Dict[str, Dict[str, Any]] = {}

    @abstractmethod
    def get_protocol_name(self) -> str:
        """
        Get the name of the protocol this handler supports.

        Returns:
            Protocol name (e.g., 'sip', 'http', 'rtsp')
        """
        pass

    @abstractmethod
    def get_session_identifier(self, packet_data: bytes) -> Optional[str]:
        """
        Extract the session identifier from a packet.

        For SIP this would be the Call-ID, for HTTP it might be a session cookie,
        for custom protocols it could be any unique session identifier.

        Args:
            packet_data: Raw packet data

        Returns:
            Session identifier string, or None if not found/applicable
        """
        pass

    @abstractmethod
    def modify_packet_for_stickiness(self, original_packet: bytes,
                                   session_id: str,
                                   modification_params: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Modify a packet to maintain session stickiness.

        This method modifies packet contents to ensure that packets belonging
        to the same session maintain consistent identifiers and any other
        protocol-specific requirements.

        Args:
            original_packet: Original packet data
            session_id: Session identifier to maintain
            modification_params: Protocol-specific modification parameters

        Returns:
            Modified packet data
        """
        pass

    @abstractmethod
    def extract_target_info(self, packet_data: bytes) -> Dict[str, Any]:
        """
        Extract target information from a packet.

        This should extract relevant targeting information like destination
        addresses, ports, URIs, etc. that are useful for attack coordination.

        Args:
            packet_data: Raw packet data

        Returns:
            Dictionary containing target information
        """
        pass

    @abstractmethod
    def validate_packet(self, packet_data: bytes) -> Tuple[bool, str]:
        """
        Validate that a packet is properly formatted for this protocol.

        Args:
            packet_data: Raw packet data

        Returns:
            Tuple of (is_valid, error_message)
        """
        pass

    def create_session_context(self, session_id: str,
                             initial_packet: bytes) -> Dict[str, Any]:
        """
        Create session context information.

        This method can be overridden to store protocol-specific session
        state that might be needed for future packet modifications.

        Args:
            session_id: Session identifier
            initial_packet: First packet of the session

        Returns:
            Session context dictionary
        """
        context = {
            'session_id': session_id,
            'created_at': self._get_timestamp(),
            'packet_count': 0,
            'protocol': self.get_protocol_name()
        }

        # Extract and store target info
        try:
            target_info = self.extract_target_info(initial_packet)
            context['target_info'] = target_info
        except Exception as e:
            self.logger.warning(f"Failed to extract target info: {e}")
            context['target_info'] = {}

        return context

    def update_session_context(self, session_id: str,
                             packet_data: bytes) -> None:
        """
        Update session context with information from a new packet.

        Args:
            session_id: Session identifier
            packet_data: New packet data
        """
        if session_id in self._session_cache:
            self._session_cache[session_id]['packet_count'] += 1
            self._session_cache[session_id]['last_seen'] = self._get_timestamp()

    def get_session_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session context information.

        Args:
            session_id: Session identifier

        Returns:
            Session context dictionary or None if not found
        """
        return self._session_cache.get(session_id)

    def cleanup_old_sessions(self, max_age_seconds: int = 3600) -> int:
        """
        Clean up old session entries.

        Args:
            max_age_seconds: Maximum age of sessions to keep

        Returns:
            Number of sessions cleaned up
        """
        current_time = self._get_timestamp()
        old_sessions = []

        for session_id, context in self._session_cache.items():
            age = current_time - context.get('last_seen', context.get('created_at', 0))
            if age > max_age_seconds:
                old_sessions.append(session_id)

        for session_id in old_sessions:
            del self._session_cache[session_id]

        if old_sessions:
            self.logger.info(f"Cleaned up {len(old_sessions)} old sessions")

        return len(old_sessions)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get handler statistics.

        Returns:
            Statistics dictionary
        """
        return {
            'protocol': self.get_protocol_name(),
            'active_sessions': len(self._session_cache),
            'total_packets_processed': sum(
                ctx.get('packet_count', 0) for ctx in self._session_cache.values()
            )
        }

    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()

    def cache_session(self, session_id: str, packet_data: bytes) -> Dict[str, Any]:
        """
        Public method to cache session information.

        Args:
            session_id: Session identifier
            packet_data: Packet data

        Returns:
            Session context
        """
        return self._cache_session(session_id, packet_data)

    def _cache_session(self, session_id: str, packet_data: bytes) -> Dict[str, Any]:
        """
        Cache session information.

        Args:
            session_id: Session identifier
            packet_data: Packet data

        Returns:
            Session context
        """
        if session_id not in self._session_cache:
            context = self.create_session_context(session_id, packet_data)
            self._session_cache[session_id] = context
        else:
            context = self._session_cache[session_id]
            self.update_session_context(session_id, packet_data)

        return context


class PacketHandlerError(Exception):
    """Base exception for packet handler errors."""
    pass


class UnsupportedProtocolError(PacketHandlerError):
    """Raised when an unsupported protocol is encountered."""
    pass


class PacketValidationError(PacketHandlerError):
    """Raised when packet validation fails."""
    pass


class SessionNotFoundError(PacketHandlerError):
    """Raised when a requested session is not found."""
    pass
