#!/usr/bin/env python3
"""
Final cleanup of CrewAI backward compatibility aliases
Author: Senior Engineer  
Date: January 29, 2025
"""

import os
import re
import shutil

def cleanup_aliases():
    """Remove CrewAI backward compatibility aliases"""
    
    files_to_update = []
    
    # Find all Python files with the alias
    for root, dirs, files in os.walk('.'):
        # Skip virtual environments
        dirs[:] = [d for d in dirs if d not in ['venv', '.venv', '__pycache__', 'node_modules', '.git']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if 'as LangGraphEventStreamer' in content:
                        files_to_update.append(filepath)
                except:
                    pass
    
    print(f"Found {len(files_to_update)} files with CrewAI aliases to update")
    
    for filepath in files_to_update:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Backup
            shutil.copy2(filepath, filepath + '.aliasback')
            
            # Replace the import alias
            new_content = re.sub(
                r'from auren\.core\.streaming\.langgraph_event_streamer import LangGraphEventStreamer as LangGraphEventStreamer',
                'from auren.core.streaming.langgraph_event_streamer import LangGraphEventStreamer',
                content
            )
            
            # Replace usage of LangGraphEventStreamer with LangGraphEventStreamer
            new_content = re.sub(r'\bCrewAIEventInstrumentation\b', 'LangGraphEventStreamer', new_content)
            
            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            # Remove backup
            os.remove(filepath + '.aliasback')
            
            print(f"✅ Updated: {filepath}")
            
        except Exception as e:
            print(f"❌ Error updating {filepath}: {e}")
    
    # Also remove the alias from the main file
    main_file = 'auren/core/streaming/langgraph_event_streamer.py'
    if os.path.exists(main_file):
        try:
            with open(main_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Remove the alias line
            new_lines = [line for line in lines if 'LangGraphEventStreamer = LangGraphEventStreamer' not in line]
            
            with open(main_file, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            
            print(f"✅ Removed alias from {main_file}")
        except Exception as e:
            print(f"❌ Error updating {main_file}: {e}")
    
    print("\n✨ Alias cleanup complete!")

if __name__ == "__main__":
    cleanup_aliases() 