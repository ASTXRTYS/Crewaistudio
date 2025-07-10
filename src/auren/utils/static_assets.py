import pkg_resources
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class StaticAssetLoader:
    """Centralized static asset management"""
    
    @staticmethod
    def get_image(filename: str) -> str:
        """Get image path with fallback"""
        try:
            # Try new location first
            return pkg_resources.resource_filename(
                'auren.app', f'static/img/{filename}'
            )
        except:
            # Fallback to legacy location
            legacy_path = Path(f"img/{filename}")
            if legacy_path.exists():
                logger.warning(
                    f"Using legacy path for {filename}. "
                    "Please move to src/auren/app/static/img/"
                )
                return str(legacy_path)
            raise FileNotFoundError(f"Asset not found: {filename}")
    
    @staticmethod
    def get_static_file(filename: str, subdirectory: str = "") -> str:
        """Get any static file with fallback"""
        try:
            # Try new location first
            path = f'static/{subdirectory}/{filename}' if subdirectory else f'static/{filename}'
            return pkg_resources.resource_filename('auren.app', path)
        except:
            # Fallback to legacy location
            legacy_path = Path(f"{subdirectory}/{filename}" if subdirectory else filename)
            if legacy_path.exists():
                logger.warning(
                    f"Using legacy path for {filename}. "
                    f"Please move to src/auren/app/static/{subdirectory}/"
                )
                return str(legacy_path)
            raise FileNotFoundError(f"Asset not found: {filename}")

# Global instance
asset_loader = StaticAssetLoader() 