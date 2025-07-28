#!/usr/bin/env python3
"""
Migrate LangGraphGatewayAdapter to LangGraphGatewayAdapter
Author: Senior Engineer
Date: January 29, 2025
"""

import os
import re
import shutil
from datetime import datetime

def migrate_gateway_adapters():
    """Replace all LangGraphGatewayAdapter references with LangGraphGatewayAdapter"""
    
    files_modified = 0
    errors = []
    target_files = []
    
    # Find all Python files that use LangGraphGatewayAdapter
    for root, dirs, files in os.walk('.'):
        # Skip virtual environments and backups
        dirs[:] = [d for d in dirs if d not in ['venv', '.venv', '__pycache__', 'node_modules', 'crewai_backup']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if 'LangGraphGatewayAdapter' in content or 'langgraph_gateway_adapter' in content:
                        target_files.append(filepath)
                except:
                    pass
    
    print(f"Found {len(target_files)} files with gateway adapter references")
    
    # Process each file
    for filepath in target_files:
        print(f"\nProcessing: {filepath}")
        
        try:
            # Backup
            backup_path = filepath + '.gwbak'
            shutil.copy2(filepath, backup_path)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Replace imports
            replacements = [
                # Direct imports
                (r'from auren.src.auren.ai.langgraph_gateway_adapter import LangGraphGatewayAdapter as LangGraphGatewayAdapter',
                 'from auren.src.auren.ai.langgraph_gateway_adapter import LangGraphGatewayAdapter as LangGraphGatewayAdapter'),
                
                # Import module
                (r'from auren.src.auren.ai.langgraph_gateway_adapter import',
                 'from auren.src.auren.ai.langgraph_gateway_adapter import'),
                
                # Direct class references (if not aliased)
                (r'\bCrewAIGatewayAdapter\b(?!\s*=)',
                 'LangGraphGatewayAdapter'),
                
                # File references in strings
                (r'langgraph_gateway_adapter',
                 'langgraph_gateway_adapter'),
                
                # Documentation updates
                (r'LangGraph Gateway Adapter',
                 'LangGraph Gateway Adapter'),
                
                (r'LangGraph gateway adapter',
                 'LangGraph gateway adapter'),
            ]
            
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            # Special handling for the original file
            if 'langgraph_gateway_adapter.py' in filepath:
                # Don't modify the original file, it might still be needed
                print(f"  ⚠️  Skipping original adapter file: {filepath}")
                os.remove(backup_path)
                continue
            
            # Only write if changed
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                files_modified += 1
                print(f"  ✅ Modified: {filepath}")
                
                # Check for remaining references
                remaining = len(re.findall(r'CrewAI.*[Gg]ateway', content))
                if remaining > 0:
                    print(f"    ⚠️  Still has {remaining} gateway references")
                
                # Remove backup
                os.remove(backup_path)
            else:
                # Remove backup if no changes
                os.remove(backup_path)
                print(f"  ⏭️  No changes needed: {filepath}")
                
        except Exception as e:
            errors.append(f"Error processing {filepath}: {str(e)}")
            print(f"  ❌ Error: {filepath} - {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("GATEWAY ADAPTER MIGRATION SUMMARY")
    print("=" * 80)
    print(f"Files processed: {len(target_files)}")
    print(f"Files modified: {files_modified}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    print("\n✅ Gateway adapter migration complete!")
    print("\nNext steps:")
    print("1. Update imports in files that couldn't be automatically migrated")
    print("2. Test that the new adapter works correctly")
    print("3. Remove the old langgraph_gateway_adapter.py file when ready")

if __name__ == "__main__":
    migrate_gateway_adapters() 