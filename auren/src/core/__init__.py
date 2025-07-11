"""
AUREN 2.0 Core Module

This module provides the core functionality for AUREN 2.0,
including configuration management, exception handling,
and dependency verification.
"""

from .config import Config, get_config
from .exceptions import AurenException, ConfigurationError, DependencyError

__version__ = "2.0.0"
__all__ = ["Config", "get_config", "AurenException", "ConfigurationError", "DependencyError"]
