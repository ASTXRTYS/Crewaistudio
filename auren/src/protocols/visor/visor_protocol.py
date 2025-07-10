"""Updated VISOR protocol with secure hashing."""

import hashlib
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json

class VISORProtocol:
    """Visual Index System for Ongoing Reference - Secure Version."""
    
    def __init__(self, storage_path: str = "data/media"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.storage_path / "miris_registry.json"
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for integrity verification."""
        sha256_hash = hashlib.sha256()
        
        # Read file in chunks to handle large files efficiently
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        
        return sha256_hash.hexdigest()
    
    def verify_integrity(self, file_path: Path, expected_hash: str) -> bool:
        """Verify file integrity using SHA-256."""
        actual_hash = self.calculate_file_hash(file_path)
        return actual_hash == expected_hash
    
    def generate_miris_tag(self, timestamp: datetime, index: int) -> str:
        """Generate MIRIS tag with secure format."""
        return f"MIRIS-{timestamp.strftime('%Y%m%d')}-{index:04d}"
