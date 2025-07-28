#!/usr/bin/env python3
"""
Migrate UI strings from AUREN Studio to AUREN Studio
Author: Senior Engineer
Date: January 29, 2025
"""

import os
import re
import shutil
from datetime import datetime

def migrate_ui_strings():
    """Replace all UI references from AUREN Studio to AUREN Studio"""
    
    files_modified = 0
    errors = []
    
    # Define file extensions to check
    target_extensions = ['.py', '.html', '.js', '.jsx', '.ts', '.tsx', '.md', '.yaml', '.yml', '.json']
    
    # Find all files that might contain UI strings
    target_files = []
    for root, dirs, files in os.walk('.'):
        # Skip virtual environments and backups
        dirs[:] = [d for d in dirs if d not in ['venv', '.venv', '__pycache__', 'node_modules', 'crewai_backup', '.git']]
        
        for file in files:
            if any(file.endswith(ext) for ext in target_extensions):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Check if file contains relevant strings
                    if any(pattern in content for pattern in ['AUREN Studio', 'AUREN-Studio', 'AUREN Studio']):
                        target_files.append(filepath)
                except:
                    pass
    
    print(f"Found {len(target_files)} files with UI strings to update")
    
    # Process each file
    for filepath in target_files:
        print(f"\nProcessing: {filepath}")
        
        try:
            # Backup
            backup_path = filepath + '.uibak'
            shutil.copy2(filepath, backup_path)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Replace patterns - order matters!
            replacements = [
                # Exact matches first
                ('AUREN Studio', 'AUREN Studio'),
                ('AUREN-Studio', 'AUREN-Studio'),
                ('AUREN Studio', 'AUREN Studio'),
                ('AUREN Studio', 'AUREN Studio'),
                
                # Window titles and metadata
                ('page_title="AUREN Studio"', 'page_title="AUREN Studio"'),
                ('<title>AUREN Studio</title>', '<title>AUREN Studio</title>'),
                ('"name": "AUREN Studio"', '"name": "AUREN Studio"'),
                
                # In comments and documentation  
                ('# AUREN Studio', '# AUREN Studio'),
                ('// AUREN Studio', '// AUREN Studio'),
                ('/* AUREN Studio', '/* AUREN Studio'),
                
                # Result pages
                ('AUREN-Studio result', 'AUREN-Studio result'),
                
                # Image alt text
                ('alt="AUREN Studio"', 'alt="AUREN Studio"'),
                ('alt="AUREN-Studio"', 'alt="AUREN-Studio"'),
            ]
            
            for old_string, new_string in replacements:
                content = content.replace(old_string, new_string)
            
            # Handle case-insensitive replacements in strings
            # This regex looks for strings containing the pattern
            content = re.sub(
                r'(["\'])([^"\']*?)CrewAI[\s\-]?Studio([^"\']*?)\1',
                lambda m: f'{m.group(1)}{m.group(2)}AUREN Studio{m.group(3)}{m.group(1)}',
                content,
                flags=re.IGNORECASE
            )
            
            # Only write if changed
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                files_modified += 1
                print(f"  ✅ Modified: {filepath}")
                
                # Count how many changes were made
                changes = 0
                for old, new in replacements:
                    changes += original_content.count(old)
                
                if changes > 0:
                    print(f"    📝 Made {changes} replacements")
                
                # Remove backup
                os.remove(backup_path)
            else:
                # Remove backup if no changes
                os.remove(backup_path)
                print(f"  ⏭️  No changes needed")
                
        except Exception as e:
            errors.append(f"Error processing {filepath}: {str(e)}")
            print(f"  ❌ Error: {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("UI STRINGS MIGRATION SUMMARY")
    print("=" * 80)
    print(f"Files processed: {len(target_files)}")
    print(f"Files modified: {files_modified}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    print("\n✅ UI strings migration complete!")
    print("\nAll references to 'AUREN Studio' have been updated to 'AUREN Studio'")

if __name__ == "__main__":
    migrate_ui_strings() 