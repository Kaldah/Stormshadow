"""
Spoofing manager for StormShadow.

Coordinates packet spoofing operations across different protocols and
manages the interaction between attack modules and packet handlers.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Type

from .base_handler import BasePacketHandler, UnsupportedProtocolError, SessionNotFoundError
from .sip_handler import SIPPacketHandler


class SpoofingManager:
    """
    Central manager for packet spoofing operations.

    Coordinates between attack modules and protocol-specific packet handlers
    to provide seamless packet manipulation and session management.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize spoofing manager.

        Args:
            config: Spoofing manager configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Registry of protocol handlers
        self._handlers: Dict[str, BasePacketHandler] = {}
        self._handler_classes: Dict[str, Type[BasePacketHandler]] = {}

        # Configuration
        self.default_protocol = config.get('default_protocol', 'sip')
        self.session_cleanup_interval = config.get('session_cleanup_interval', 300)  # 5 minutes
        self.max_session_age = config.get('max_session_age', 3600)  # 1 hour

        # State
        self._cleanup_task: Optional[asyncio.Task[None]] = None
        self._is_running = False

        # Register built-in handlers
        self._register_builtin_handlers()

    def _register_builtin_handlers(self):
        """Register built-in protocol handlers."""
        self.register_handler_class('sip', SIPPacketHandler)

    def register_handler_class(self, protocol: str, handler_class: Type[BasePacketHandler]):
        """
        Register a protocol handler class.

        Args:
            protocol: Protocol name (e.g., 'sip', 'http')
            handler_class: Handler class to register
        """
        self._handler_classes[protocol.lower()] = handler_class
        self.logger.info(f"Registered handler class for protocol: {protocol}")

    def get_handler(self, protocol: str) -> BasePacketHandler:
        """
        Get or create a handler for the specified protocol.

        Args:
            protocol: Protocol name

        Returns:
            Protocol handler instance

        Raises:
            UnsupportedProtocolError: If protocol is not supported
        """
        protocol = protocol.lower()

        # Return existing handler if available
        if protocol in self._handlers:
            return self._handlers[protocol]

        # Create new handler if class is registered
        if protocol in self._handler_classes:
            handler_config = self.config.get('handlers', {}).get(protocol, {})
            handler = self._handler_classes[protocol](handler_config)
            self._handlers[protocol] = handler
            self.logger.info(f"Created handler for protocol: {protocol}")
            return handler

        raise UnsupportedProtocolError(f"No handler registered for protocol: {protocol}")

    async def start(self):
        """Start the spoofing manager."""
        if self._is_running:
            return

        self.logger.info("Starting spoofing manager")
        self._is_running = True

        # Start session cleanup task
        if self.session_cleanup_interval > 0:
            self._cleanup_task = asyncio.create_task(self._session_cleanup_loop())

    async def stop(self):
        """Stop the spoofing manager."""
        if not self._is_running:
            return

        self.logger.info("Stopping spoofing manager")
        self._is_running = False

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    def process_packet(self, packet_data: bytes,
                      protocol: Optional[str] = None,
                      session_id: Optional[str] = None,
                      modification_params: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Process a packet for spoofing.

        Args:
            packet_data: Original packet data
            protocol: Protocol name (auto-detected if None)
            session_id: Session identifier (extracted if None)
            modification_params: Protocol-specific modification parameters

        Returns:
            Modified packet data

        Raises:
            UnsupportedProtocolError: If protocol is not supported
        """
        # Auto-detect protocol if not specified
        if protocol is None:
            protocol = self._detect_protocol(packet_data)

        handler = self.get_handler(protocol)

        # Extract session ID if not provided
        if session_id is None:
            session_id = handler.get_session_identifier(packet_data)

        if session_id is None:
            # Generate new session ID if we can't extract one
            if hasattr(handler, 'generate_call_id') and callable(getattr(handler, 'generate_call_id')):
                session_id = getattr(handler, 'generate_call_id')()
            else:
                import uuid
                session_id = str(uuid.uuid4())

        # Ensure we have a valid session_id at this point
        assert session_id is not None

        # Cache session information
        handler.cache_session(session_id, packet_data)

        # Modify packet for stickiness
        modified_packet = handler.modify_packet_for_stickiness(
            packet_data, session_id, modification_params
        )

        return modified_packet

    def extract_session_id(self, packet_data: bytes,
                          protocol: Optional[str] = None) -> Optional[str]:
        """
        Extract session identifier from packet.

        Args:
            packet_data: Packet data
            protocol: Protocol name (auto-detected if None)

        Returns:
            Session identifier or None
        """
        if protocol is None:
            protocol = self._detect_protocol(packet_data)

        try:
            handler = self.get_handler(protocol)
            return handler.get_session_identifier(packet_data)
        except UnsupportedProtocolError:
            return None

    def validate_packet(self, packet_data: bytes,
                       protocol: Optional[str] = None) -> tuple[bool, str]:
        """
        Validate packet format.

        Args:
            packet_data: Packet data
            protocol: Protocol name (auto-detected if None)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if protocol is None:
            protocol = self._detect_protocol(packet_data)

        try:
            handler = self.get_handler(protocol)
            return handler.validate_packet(packet_data)
        except UnsupportedProtocolError:
            return False, f"Unsupported protocol: {protocol}"

    def get_session_info(self, session_id: str,
                        protocol: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get session information.

        Args:
            session_id: Session identifier
            protocol: Protocol name (searches all handlers if None)

        Returns:
            Session information dictionary or None
        """
        if protocol:
            try:
                handler = self.get_handler(protocol)
                return handler.get_session_context(session_id)
            except UnsupportedProtocolError:
                return None
        else:
            # Search all handlers
            for handler in self._handlers.values():
                context = handler.get_session_context(session_id)
                if context:
                    return context
            return None

    def create_session_context(self, session_id: str,
                             initial_packet: bytes,
                             protocol: Optional[str] = None) -> Dict[str, Any]:
        """
        Create session context.

        Args:
            session_id: Session identifier
            initial_packet: Initial packet of the session
            protocol: Protocol name (auto-detected if None)

        Returns:
            Session context dictionary
        """
        if protocol is None:
            protocol = self._detect_protocol(initial_packet)

        handler = self.get_handler(protocol)
        return handler.create_session_context(session_id, initial_packet)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get spoofing manager statistics.

        Returns:
            Statistics dictionary
        """
        stats = {
            'active_protocols': list(self._handlers.keys()),
            'registered_protocols': list(self._handler_classes.keys()),
            'total_sessions': 0,
            'protocol_stats': {}
        }

        for protocol, handler in self._handlers.items():
            handler_stats = handler.get_statistics()
            stats['protocol_stats'][protocol] = handler_stats
            stats['total_sessions'] += handler_stats.get('active_sessions', 0)

        return stats

    def _detect_protocol(self, packet_data: bytes) -> str:
        """
        Auto-detect protocol from packet data.

        Args:
            packet_data: Packet data

        Returns:
            Detected protocol name
        """
        # Simple heuristics for protocol detection
        packet_str = packet_data.decode('utf-8', errors='ignore').lower()

        # Check for SIP
        if ('sip/2.0' in packet_str or
            packet_str.startswith(('invite ', 'register ', 'options ', 'bye ', 'cancel ', 'ack '))):
            return 'sip'

        # Check for HTTP
        if ('http/1.' in packet_str or
            packet_str.startswith(('get ', 'post ', 'put ', 'delete ', 'head ', 'options '))):
            return 'http'

        # Default to configured default protocol
        return self.default_protocol

    async def _session_cleanup_loop(self):
        """Background task to clean up old sessions."""
        while self._is_running:
            try:
                await asyncio.sleep(self.session_cleanup_interval)

                if not self._is_running:
                    break

                total_cleaned = 0
                for protocol, handler in self._handlers.items():
                    cleaned = handler.cleanup_old_sessions(self.max_session_age)
                    total_cleaned += cleaned

                if total_cleaned > 0:
                    self.logger.info(f"Cleaned up {total_cleaned} old sessions")

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in session cleanup: {e}")
                # Continue the loop despite errors

    def register_custom_handler(self, protocol: str,
                              handler_module_path: str,
                              handler_class_name: Optional[str] = None):
        """
        Register a custom protocol handler from a module.

        Args:
            protocol: Protocol name
            handler_module_path: Path to module containing handler class
            handler_class_name: Name of handler class (auto-detected if None)
        """
        import importlib.util
        import inspect

        try:
            # Load module
            spec = importlib.util.spec_from_file_location("custom_handler", handler_module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find handler class
            if handler_class_name:
                handler_class = getattr(module, handler_class_name)
            else:
                # Auto-detect by looking for BasePacketHandler subclass
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BasePacketHandler) and
                        obj != BasePacketHandler):
                        handler_class = obj
                        break
                else:
                    raise ValueError("No BasePacketHandler subclass found in module")

            self.register_handler_class(protocol, handler_class)
            self.logger.info(f"Registered custom handler for {protocol} from {handler_module_path}")

        except Exception as e:
            self.logger.error(f"Failed to register custom handler: {e}")
            raise


# Factory function for creating spoofing manager
def create_spoofing_manager(config: Optional[Dict[str, Any]] = None) -> SpoofingManager:
    """
    Factory function to create a spoofing manager.

    Args:
        config: Configuration dictionary

    Returns:
        SpoofingManager instance
    """
    config = config or {}
    return SpoofingManager(config)
