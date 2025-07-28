#!/usr/bin/env python3
"""
Clean up remaining CrewAI string references
"""

import os
import shutil
from datetime import datetime

def clean_file(filepath, replacements):
    """Clean CrewAI references from a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        for old, new in replacements:
            content = content.replace(old, new)
        
        if content != original_content:
            # Backup
            backup_path = filepath + '.pre_clean_backup'
            shutil.copy2(filepath, backup_path)
            
            # Write cleaned content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Cleaned: {filepath}")
            return True
        return False
        
    except Exception as e:
        print(f"❌ Error cleaning {filepath}: {e}")
        return False

def main():
    print("🧹 Cleaning remaining CrewAI references...")
    
    # Define replacements
    files_to_clean = {
        "./auren/main_clean.py": [
            ('"implementation": "clean-no-crewai"', '"implementation": "langgraph"'),
            ('return {"status": "ready", "implementation": "clean-no-crewai"}', 
             'return {"status": "ready", "implementation": "langgraph"}'),
        ],
        "./auren/core/streaming/crewai_instrumentation.py": [
            ('"platform": "crewai"', '"platform": "langgraph"'),
        ],
        "./auren/core/streaming/test_live_events.py": [
            ('metadata={"platform": "crewai", "version": "2.0"}', 
             'metadata={"platform": "langgraph", "version": "0.2.27"}'),
        ],
        "./auren/utils/check_system_health.py": [
            ('"crewai"', '"langgraph"'),
        ],
        "./auren/docs/context/auren-launch-system.py": [
            ('"crewai"', '"langgraph"'),
        ],
        "./auren/realtime/crewai_instrumentation.py": [
            ('"platform": "crewai"', '"platform": "langgraph"'),
        ],
        "./auren/realtime/test_live_events.py": [
            ('metadata={"platform": "crewai", "version": "2.0"}', 
             'metadata={"platform": "langgraph", "version": "0.2.27"}'),
        ],
        "./src/auren/app/pg_knowledge.py": [
            ('home_dir / ".crewai"', 'home_dir / ".langgraph"'),
        ],
        "./src/auren/app/app/pg_knowledge.py": [
            ('home_dir / ".crewai"', 'home_dir / ".langgraph"'),
        ],
        "./src/auren/app/app/db_utils.py": [
            ("'sqlite:///crewai.db'", "'sqlite:///langgraph.db'"),
        ],
        "./src/auren/app/db_utils.py": [
            ("'sqlite:///crewai.db'", "'sqlite:///langgraph.db'"),
        ],
    }
    
    # Also rename crewai_instrumentation.py files
    rename_files = [
        ("./auren/core/streaming/crewai_instrumentation.py", 
         "./auren/core/streaming/langgraph_instrumentation.py"),
        ("./auren/realtime/crewai_instrumentation.py", 
         "./auren/realtime/langgraph_instrumentation.py"),
    ]
    
    cleaned_count = 0
    
    # Clean files
    for filepath, replacements in files_to_clean.items():
        if os.path.exists(filepath):
            if clean_file(filepath, replacements):
                cleaned_count += 1
        else:
            print(f"⚠️  File not found: {filepath}")
    
    # Rename files
    for old_path, new_path in rename_files:
        if os.path.exists(old_path) and not os.path.exists(new_path):
            shutil.move(old_path, new_path)
            print(f"📝 Renamed: {old_path} → {new_path}")
            cleaned_count += 1
    
    print(f"\n✅ Cleaned {cleaned_count} files")
    print("🎉 CrewAI cleanup complete!")

if __name__ == "__main__":
    main() 