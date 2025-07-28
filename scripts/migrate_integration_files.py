#!/usr/bin/env python3
"""
Migrate langgraph_integration files to langgraph_integration
Author: Senior Engineer
Date: January 29, 2025
"""

import os
import re
import shutil
from datetime import datetime

def migrate_integration_files():
    """Migrate all langgraph_integration patterns to langgraph_integration"""
    
    files_modified = 0
    files_renamed = 0
    errors = []
    
    # Find all files with langgraph_integration
    target_files = []
    for root, dirs, files in os.walk('.'):
        # Skip virtual environments and backups
        dirs[:] = [d for d in dirs if d not in ['venv', '.venv', '__pycache__', 'node_modules']]
        
        for file in files:
            if 'langgraph_integration' in file.lower():
                filepath = os.path.join(root, file)
                target_files.append(filepath)
            elif file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if 'langgraph_integration' in content.lower() or 'LangGraphIntelligenceAdapter' in content:
                        target_files.append(filepath)
                except:
                    pass
    
    # Remove duplicates
    target_files = list(set(target_files))
    print(f"Found {len(target_files)} files related to integration")
    
    # Process each file
    for filepath in target_files:
        print(f"\nProcessing: {filepath}")
        
        # Skip backup directories
        if 'crewai_backup' in filepath:
            print(f"  ⏭️  Skipping backup file")
            continue
        
        try:
            # Check if this is a file that should be renamed
            if 'langgraph_integration' in os.path.basename(filepath):
                # Rename the file
                new_filename = os.path.basename(filepath).replace('langgraph_integration', 'langgraph_integration')
                new_filepath = os.path.join(os.path.dirname(filepath), new_filename)
                
                print(f"  📝 Renaming to: {new_filename}")
                shutil.move(filepath, new_filepath)
                files_renamed += 1
                filepath = new_filepath  # Continue processing with new path
            
            # Now modify the content
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Replace patterns
            replacements = [
                # Class names
                (r'LangGraphIntelligenceAdapter', 'LangGraphIntelligenceAdapter'),
                (r'LangGraph Intelligence Adapter', 'LangGraph Intelligence Adapter'),
                
                # Module names
                (r'langgraph_integration', 'langgraph_integration'),
                (r'LangGraph Integration', 'LangGraph Integration'),
                (r'LangGraph integration', 'LangGraph integration'),
                
                # Documentation
                (r'LangGraph agents', 'LangGraph agents'),
                (r'LangGraph-based', 'LangGraph-based'),
                (r'LangGraph framework', 'LangGraph framework'),
                
                # Comments
                (r'# LangGraph', '# LangGraph'),
                (r'# langgraph', '# langgraph'),
            ]
            
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            # Update imports that reference integration modules
            content = re.sub(
                r'from (.*)\.langgraph_integration import',
                r'from \1.langgraph_integration import',
                content
            )
            
            # Only write if changed
            if content != original_content:
                # Backup first
                backup_path = filepath + '.intbak'
                shutil.copy2(filepath, backup_path)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                files_modified += 1
                print(f"  ✅ Modified content")
                
                # Check for remaining references
                remaining_crewai = len(re.findall(r'crewai', content, re.IGNORECASE))
                if remaining_crewai > 0:
                    print(f"    ⚠️  Still has {remaining_crewai} CrewAI references")
                
                # Remove backup
                os.remove(backup_path)
            else:
                print(f"  ⏭️  No content changes needed")
                
        except Exception as e:
            errors.append(f"Error processing {filepath}: {str(e)}")
            print(f"  ❌ Error: {str(e)}")
    
    # Update any imports in other files
    print("\n\nUpdating imports in other files...")
    import_files_updated = 0
    
    for root, dirs, files in os.walk('.'):
        dirs[:] = [d for d in dirs if d not in ['venv', '.venv', '__pycache__', 'node_modules', 'crewai_backup']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if 'langgraph_integration' in content:
                        original = content
                        content = content.replace('langgraph_integration', 'langgraph_integration')
                        
                        if content != original:
                            with open(filepath, 'w', encoding='utf-8') as f:
                                f.write(content)
                            import_files_updated += 1
                            print(f"  ✅ Updated imports in: {filepath}")
                except:
                    pass
    
    # Summary
    print("\n" + "=" * 80)
    print("INTEGRATION FILES MIGRATION SUMMARY")
    print("=" * 80)
    print(f"Files renamed: {files_renamed}")
    print(f"Files modified: {files_modified}")
    print(f"Import statements updated: {import_files_updated}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    print("\n✅ Integration files migration complete!")

if __name__ == "__main__":
    migrate_integration_files() 