"""
AUREN 2.0 Main Application

Enhanced with dependency checking and improved architecture
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from utils.dependency_check import verify_dependencies
    from core.config import get_config
    from core.exceptions import AurenException, ConfigurationError
    
    # Verify dependencies on startup
    verify_dependencies()
    print("✅ All dependencies verified successfully")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please run: pip install -r requirements/prod.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Startup error: {e}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    try:
        config = get_config()
        logger.info(f"Starting {config.app_name} v{config.app_version}")
        logger.info(f"Debug mode: {config.debug}")
        
        # Import and start the actual application
        from app import create_app
        app = create_app()
        
        import uvicorn
        uvicorn.run(
            app,
            host=config.api_host,
            port=config.api_port,
            log_level=config.log_level.lower()
        )
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
