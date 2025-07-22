#!/usr/bin/env python3
"""
Fix incorrect import paths in MVPNEAR branch files.
Replaces 'from src.' with 'from src.' throughout the codebase.
"""

import os
import re
from pathlib import Path


def fix_imports_in_file(file_path):
    """Fix import statements in a single file."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Count replacements for reporting
        original_content = content
        
        # Replace 'from src.' with 'from src.'
        content = re.sub(r'from auren\.src\.', 'from src.', content)
        
        # Replace 'import src.' with 'import src.'
        content = re.sub(r'import auren\.src\.', 'import src.', content)
        
        if content != original_content:
            with open(file_path, 'w') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main function to fix imports across the project."""
    # Start from auren directory
    auren_dir = Path(__file__).parent.parent
    
    fixed_files = []
    
    # Walk through all Python files
    for root, dirs, files in os.walk(auren_dir):
        # Skip __pycache__ and .git directories
        dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', '.pytest_cache']]
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                if fix_imports_in_file(file_path):
                    fixed_files.append(file_path)
    
    # Report results
    print(f"Fixed imports in {len(fixed_files)} files:")
    for file in fixed_files:
        print(f"  - {file.relative_to(auren_dir)}")
    
    if not fixed_files:
        print("No files needed import fixes.")


if __name__ == "__main__":
    main() 