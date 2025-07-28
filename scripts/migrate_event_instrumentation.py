#!/usr/bin/env python3
"""
Migrate CrewAIEventInstrumentation to LangGraphEventStreamer
Author: Senior Engineer
Date: January 29, 2025
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from auren.core.streaming.langgraph_event_streamer import LangGraphEventStreamer as CrewAIEventInstrumentation

def migrate_event_instrumentation():
    """Replace all CrewAIEventInstrumentation with LangGraphEventStreamer"""
    
    files_modified = 0
    errors = []
    
    # Find all Python files that use CrewAIEventInstrumentation
    target_files = []
    
    for root, dirs, files in os.walk('.'):
        # Skip virtual environments
        dirs[:] = [d for d in dirs if d not in ['venv', '.venv', '__pycache__', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if 'CrewAIEventInstrumentation' in content:
                        target_files.append(filepath)
                except:
                    pass
    
    print(f"Found {len(target_files)} files with CrewAIEventInstrumentation")
    
    # Process each file
    for filepath in target_files:
        print(f"\nProcessing: {filepath}")
        
        try:
            # Backup
            backup_path = filepath + '.bak'
            shutil.copy2(filepath, backup_path)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Track if we need to add import
            needs_import = True
            import_added = False
            modified_lines = []
            
            for i, line in enumerate(lines):
                # Check if import already exists
                if 'from auren.core.streaming.langgraph_event_streamer import' in line:
                    needs_import = False
                
                # Replace imports
from auren.core.streaming.langgraph_event_streamer import LangGraphEventStreamer as CrewAIEventInstrumentation
                    modified_lines.append('from auren.core.streaming.langgraph_event_streamer import LangGraphEventStreamer as LangGraphEventStreamer as CrewAIEventInstrumentation')
                    needs_import = False
                    import_added = True
from auren.core.streaming.langgraph_event_streamer import LangGraphEventStreamer as CrewAIEventInstrumentation
                    modified_lines.append('from auren.core.streaming.langgraph_event_streamer import LangGraphEventStreamer as LangGraphEventStreamer as CrewAIEventInstrumentation')
                    needs_import = False
                    import_added = True
                elif 'LangGraphEventStreamer as CrewAIEventInstrumentation' in line and 'import' in line:
                    # Handle other import patterns
                    new_line = line.replace('CrewAIEventInstrumentation', 'LangGraphEventStreamer as CrewAIEventInstrumentation')
                    modified_lines.append(new_line)
                    needs_import = False
                    import_added = True
                else:
                    modified_lines.append(line)
                
                # Add import after the last import if needed
                if needs_import and not import_added and i < len(lines) - 1:
                    next_line = lines[i + 1] if i + 1 < len(lines) else ''
                    if (line.startswith('import ') or line.startswith('from ')) and not (next_line.startswith('import ') or next_line.startswith('from ')):
                        modified_lines.append('from auren.core.streaming.langgraph_event_streamer import LangGraphEventStreamer as LangGraphEventStreamer as CrewAIEventInstrumentation')
                        needs_import = False
                        import_added = True
            
            # Write modified content
            new_content = '\n'.join(modified_lines)
            
            # Only write if changed
            if new_content != content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                files_modified += 1
                print(f"✅ Modified: {filepath}")
                
                # Remove backup
                os.remove(backup_path)
            else:
                # Remove backup if no changes
                os.remove(backup_path)
                print(f"⏭️  No changes needed: {filepath}")
                
        except Exception as e:
            errors.append(f"Error processing {filepath}: {str(e)}")
            print(f"❌ Error: {filepath} - {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("MIGRATION SUMMARY")
    print("=" * 80)
    print(f"Files processed: {len(target_files)}")
    print(f"Files modified: {files_modified}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    print("\n✅ Migration complete!")
    print("Note: You still need to copy langgraph_event_streamer.py to all locations or update imports")

if __name__ == "__main__":
    migrate_event_instrumentation() 