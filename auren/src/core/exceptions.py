"""
Custom exception classes for AUREN 2.0
"""


class AurenException(Exception):
    """Base exception for AUREN 2.0"""
    pass


class ConfigurationError(AurenException):
    """Raised when configuration is invalid or missing"""
    pass


class DependencyError(AurenException):
    """Raised when required dependencies are missing or incompatible"""
    pass


class ValidationError(AurenException):
    """Raised when data validation fails"""
    pass


class DatabaseError(AurenException):
    """Raised when database operations fail"""
    pass


class AIError(AurenException):
    """Raised when AI/ML operations fail"""
    pass
