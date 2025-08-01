"""
Orchestration package for StormShadow.

This package provides high-level orchestration functionality:
- StormShadowOrchestrator: Main application workflow management with separated concerns
- InteractiveManager: Interactive mode management
- Component lifecycle coordination
"""

from .orchestrator import StormShadowOrchestrator
from .interactive_manager import InteractiveManager

__all__ = [
    'StormShadowOrchestrator',
    'InteractiveManager'
]
