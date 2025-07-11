"""
Runtime dependency verification for AUREN 2.0
"""

import importlib
import sys
from typing import List, Dict, Tuple
from .core.exceptions import DependencyError


class DependencyChecker:
    """Verifies that all required dependencies are available and compatible"""
    
    REQUIRED_PACKAGES = {
        "fastapi": "0.109.0",
        "uvicorn": "0.27.0",
        "pydantic": "2.6.1",
        "crewai": "0.30.11",
        "crewai-tools": "0.2.6",
        "openai": "1.12.0",
        "numpy": "1.26.3",
        "scipy": "1.11.4",
        "opencv-python-headless": "4.9.0.80",
        "mediapipe": "0.10.9",
        "sqlalchemy": "2.0.25",
        "chromadb": "0.4.22",
    }
    
    OPTIONAL_PACKAGES = {
        "prometheus-client": "0.19.0",
        "structlog": "24.1.0",
    }
    
    @classmethod
    def check_all(cls) -> Tuple[bool, List[str]]:
        """Check all dependencies and return (success, warnings)"""
        warnings = []
        success = True
        
        # Check required packages
        for package, min_version in cls.REQUIRED_PACKAGES.items():
            try:
                module = importlib.import_module(package)
                if hasattr(module, '__version__'):
                    version = module.__version__
                    if cls._version_compare(version, min_version) < 0:
                        warnings.append(f"{package} version {version} is older than required {min_version}")
                        success = False
            except ImportError:
                warnings.append(f"Required package {package} is not installed")
                success = False
        
        # Check optional packages
        for package, min_version in cls.OPTIONAL_PACKAGES.items():
            try:
                module = importlib.import_module(package)
                if hasattr(module, '__version__'):
                    version = module.__version__
                    if cls._version_compare(version, min_version) < 0:
                        warnings.append(f"Optional package {package} version {version} is older than recommended {min_version}")
            except ImportError:
                warnings.append(f"Optional package {package} is not installed")
        
        return success, warnings
    
    @classmethod
    def _version_compare(cls, version1: str, version2: str) -> int:
        """Compare two version strings"""
        from packaging import version
        return version.parse(version1).__cmp__(version.parse(version2))
    
    @classmethod
    def verify_startup(cls) -> None:
        """Verify dependencies on startup"""
        success, warnings = cls.check_all()
        
        if warnings:
            print("⚠️  Dependency warnings:")
            for warning in warnings:
                print(f"   - {warning}")
        
        if not success:
            raise DependencyError("Required dependencies are missing or incompatible")


def verify_dependencies() -> None:
    """Convenience function to verify dependencies"""
    DependencyChecker.verify_startup()
