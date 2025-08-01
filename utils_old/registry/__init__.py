"""
Registry management package for StormShadow.

This package provides Docker registry operations and management,
as well as base classes for lab and attack modules.
"""

from .registry_manager import RegistryManager
from .lab_module import LabModule, AttackModule

__all__ = ['RegistryManager', 'LabModule', 'AttackModule']
