"""Updated startup utilities with secure permissions."""

import os
import logging
from pathlib import Path
from typing import List

def ensure_directories() -> None:
    """Create required directories with secure permissions."""
    required_dirs = [
        ("logs/system", 0o750),      # rwxr-x---
        ("logs/protocols", 0o750),   # rwxr-x---
        ("logs/agents", 0o750),      # rwxr-x---
        ("data/protocols", 0o750),   # rwxr-x---
        ("data/media", 0o750),       # rwxr-x---
        ("data/db", 0o700),          # rwx------  (most restrictive for DB)
        ("data/cache", 0o750),       # rwxr-x---
        ("tmp", 0o750)               # rwxr-x---
    ]
    
    for dir_path, permissions in required_dirs:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        
        # Set secure permissions
        os.chmod(path, permissions)
    
    # Ensure parent directories also have appropriate permissions
    os.chmod("logs", 0o750)
    os.chmod("data", 0o750)
    
    logging.info(f"✅ Created {len(required_dirs)} directories with secure permissions")


def setup_logging(log_level: str = "INFO") -> None:
    """Configure logging for the application."""
    import logging.config

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
            "detailed": {"format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": "logs/system/auren.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": "logs/system/errors.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file", "error_file"],
                "level": log_level,
                "propagate": False,
            },
            "src": {"handlers": ["console", "file"], "level": log_level, "propagate": False},
            "auren": {"handlers": ["console", "file"], "level": log_level, "propagate": False},
        },
    }

    logging.config.dictConfig(logging_config)
    logging.info("✅ Logging configured successfully")


def validate_environment() -> bool:
    """Validate that all required environment variables are set."""
    required_vars = ["OPENAI_API_KEY", "WHATSAPP_ACCESS_TOKEN", "WHATSAPP_PHONE_ID"]

    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logging.error(f"❌ Missing required environment variables: {missing_vars}")
        return False

    logging.info("✅ Environment validation passed")
    return True


def initialize_app() -> bool:
    """Initialize the AUREN application."""
    try:
        # 1. Create directories
        ensure_directories()

        # 2. Setup logging
        setup_logging()

        # 3. Validate environment
        if not validate_environment():
            return False

        logging.info("🚀 AUREN application initialized successfully")
        return True

    except Exception as e:
        print(f"❌ Failed to initialize AUREN: {e}")
        return False
