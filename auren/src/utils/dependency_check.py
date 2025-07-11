"""Runtime dependency verification for AUREN 2.0"""

import importlib
import sys
from typing import List, Tuple, Dict
import logging

logger = logging.getLogger(__name__)

class DependencyChecker:
    """Check and verify runtime dependencies"""
    
    REQUIRED_MODULES = {
        "fastapi": "FastAPI web framework",
        "pydantic": "Data validation",
        "uvicorn": "ASGI server",
        "crewai": "Multi-agent framework",
        "openai": "OpenAI API",
        "sentence_transformers": "Text embeddings",
        "chromadb": "Vector database",
        "sqlalchemy": "SQL toolkit",
        "cv2": "OpenCV for image processing",
        "mediapipe": "Face detection",
        "yaml": "YAML configuration",
        "structlog": "Structured logging",
    }
    
    @classmethod
    def check_required(cls) -> Tuple[bool, List[str]]:
        """Check required dependencies"""
        missing = []
        
        for module, description in cls.REQUIRED_MODULES.items():
            try:
                importlib.import_module(module)
                logger.debug(f"✅ {module}: {description}")
            except ImportError:
                missing.append(f"{module} ({description})")
                logger.error(f"❌ Missing required: {module}")
        
        return len(missing) == 0, missing
    
    @classmethod
    def verify_all(cls) -> bool:
        """Verify all dependencies"""
        print("🔍 Checking AUREN dependencies...")
        
        success, missing = cls.check_required()
        
        if not success:
            print("\n❌ Missing required dependencies:")
            for dep in missing:
                print(f"   - {dep}")
            print("\nInstall with: pip install -r requirements.txt")
            return False
        
        print("\n✅ All required dependencies installed")
        return True
