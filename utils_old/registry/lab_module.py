"""
Base classes for StormShadow modules.

This module provides base classes that lab modules and attack modules
should inherit from to ensure consistent interfaces.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List


class LabInterface(ABC):
    """
    Interface defining the contract for lab modules.
    
    This interface ensures all lab modules provide consistent functionality
    for creation, parameterization, and management.
    """
    
    @abstractmethod
    async def start(self) -> bool:
        """Start the lab environment."""
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """Stop the lab environment."""
        pass
    
    @abstractmethod
    async def configure(self) -> bool:
        """Configure the lab environment."""
        pass
    
    @abstractmethod
    async def get_status(self) -> Dict[str, Any]:
        """Get lab status information."""
        pass
    
    @abstractmethod
    async def get_endpoints(self) -> List[Dict[str, Any]]:
        """Get lab endpoints for attack targeting."""
        pass
    
    @abstractmethod
    def get_build_info(self) -> Dict[str, Any]:
        """Get information needed to build Docker images."""
        pass
    
    @abstractmethod
    async def open_lab_terminal(self) -> bool:
        """Open a terminal with access to the lab environment."""
        pass
    
    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Check if the lab is currently running."""
        pass


class LabModule(LabInterface):
    """
    Base class for lab modules.

    All lab modules should inherit from this class and implement
    the required abstract methods. This class provides the standard
    interface for StormShadow lab environments.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize the lab module.

        Args:
            name: Module name
            config: Module configuration
        """
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"lab.{name}")
        self._is_running = False
        
        # Standard lab parameters with defaults
        self.container_name = config.get('container_name', f"stormshadow-{name}")
        self.image_name = config.get('image', f"stormshadow-{name}")
        self.network_name = config.get('network', 'bridge')
        
        # Build configuration
        self.dockerfile = config.get('dockerfile')
        self.build_context = config.get('build_context')
        
        # Runtime configuration
        self.port_mappings = config.get('ports', {})
        self.environment = config.get('environment', {})
        self.volumes = config.get('volumes', [])

    @property
    def is_running(self) -> bool:
        """Check if the lab is currently running."""
        return self._is_running

    def get_build_info(self) -> Dict[str, Any]:
        """
        Get information needed to build Docker images.
        
        Returns:
            Dictionary containing build information
        """
        return {
            'image_name': self.image_name,
            'dockerfile': self.dockerfile,
            'build_context': self.build_context,
            'requires_build': bool(self.dockerfile and self.build_context)
        }

    @abstractmethod
    async def start(self) -> bool:
        """
        Start the lab environment.

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the lab environment.

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def configure(self) -> bool:
        """
        Configure the lab environment.

        Returns:
            True if configuration successful, False otherwise
        """
        pass

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the lab.

        Returns:
            Dictionary with health status information
        """
        return {
            'name': self.name,
            'running': self.is_running,
            'status': 'healthy' if self.is_running else 'stopped'
        }

    async def get_info(self) -> Dict[str, Any]:
        """
        Get module information.

        Returns:
            Dictionary with module info
        """
        return {
            'name': self.name,
            'type': 'lab',
            'running': self.is_running,
            'config': self.config
        }


class AttackModule(ABC):
    """
    Base class for attack modules.

    All attack modules should inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize the attack module.

        Args:
            name: Module name
            config: Module configuration
        """
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"attack.{name}")
        self._running = False

    @property
    def is_running(self) -> bool:
        """Check if the attack is currently running."""
        return self._running

    @abstractmethod
    async def start(self) -> bool:
        """
        Start the attack.

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def stop(self) -> bool:
        """
        Stop the attack.

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def configure(self) -> bool:
        """
        Configure the attack.

        Returns:
            True if configuration successful, False otherwise
        """
        pass

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get attack statistics.

        Returns:
            Dictionary with attack statistics
        """
        return {
            'name': self.name,
            'running': self.is_running,
            'packets_sent': 0,  # Override in subclasses
            'duration': 0       # Override in subclasses
        }
