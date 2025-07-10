#!/usr/bin/env python3
# scripts/fix_missing_imports.py
import os
import re
from pathlib import Path

def check_and_fix_imports(file_path: Path) -> bool:
    """Check if file uses 'os' and add import if missing"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check if 'os.' is used in the file
    if 'os.' in content or 'os.environ' in content or 'os.getenv' in content:
        # Check if 'import os' already exists
        if not re.search(r'^import os\s*$', content, re.MULTILINE):
            # Add import os after the first line (usually module docstring or comment)
            lines = content.split('\n')
            
            # Find the right place to insert (after initial comments/docstrings)
            insert_pos = 0
            in_docstring = False
            docstring_char = None
            
            for i, line in enumerate(lines):
                # Handle docstrings
                if line.strip().startswith('"""') or line.strip().startswith("'''"):
                    if not in_docstring:
                        in_docstring = True
                        docstring_char = '"""' if '"""' in line else "'''"
                        if line.count(docstring_char) >= 2:  # Single line docstring
                            in_docstring = False
                    elif docstring_char in line:
                        in_docstring = False
                    continue
                
                # Skip empty lines and comments at the start
                if not in_docstring and line.strip() and not line.strip().startswith('#'):
                    insert_pos = i
                    break
            
            # Insert 'import os' at the appropriate position
            lines.insert(insert_pos, 'import os')
            
            # Write back to file
            with open(file_path, 'w') as f:
                f.write('\n'.join(lines))
            
            print(f"✅ Fixed: {file_path}")
            return True
    
    return False

def fix_all_files():
    """Fix missing os imports in all Python files"""
    root = Path('src/auren')
    fixed_count = 0
    
    # Check all Python files
    for py_file in root.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
        
        if check_and_fix_imports(py_file):
            fixed_count += 1
    
    # Also check scripts directory
    scripts_dir = Path('scripts')
    if scripts_dir.exists():
        for py_file in scripts_dir.glob('*.py'):
            if check_and_fix_imports(py_file):
                fixed_count += 1
    
    print(f"\n🎯 Total files fixed: {fixed_count}")
    
    # Additional check for other common missing imports
    print("\n🔍 Checking for other common missing imports...")
    check_common_imports(root)

def check_common_imports(root: Path):
    """Check for other commonly missing imports"""
    patterns = {
        'json.': 'import json',
        'logging.': 'import logging',
        'datetime.': 'from datetime import datetime',
        're.': 'import re',
        'Path(': 'from pathlib import Path',
        'uuid.': 'import uuid',
        'asyncio.': 'import asyncio',
    }
    
    issues = []
    
    for py_file in root.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue
            
        with open(py_file, 'r') as f:
            content = f.read()
        
        for pattern, required_import in patterns.items():
            if pattern in content:
                # Check if the import exists (simple check)
                import_module = required_import.split()[-1]
                if not re.search(rf'import\s+{import_module}', content) and \
                   not re.search(rf'from\s+\S+\s+import.*{import_module}', content):
                    issues.append(f"{py_file}: Missing '{required_import}' for '{pattern}'")
    
    if issues:
        print("\n⚠️  Potential missing imports found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ No other missing imports detected")

if __name__ == "__main__":
    fix_all_files() 