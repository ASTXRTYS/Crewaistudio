#!/usr/bin/env python3
"""
Find actual CrewAI usage in project files only
"""
import os
import re

# Directories to check (project code only)
TARGET_DIRS = ['app', 'auren', 'src', 'agents', 'config', 'scripts', 'tests']

# Files/patterns to skip
SKIP_PATTERNS = [
    'venv', '.venv', '__pycache__', '.git', 
    'node_modules', 'crewai_backup', 'find_crewai'
]

def find_crewai_usage():
    results = []
    
    for target_dir in TARGET_DIRS:
        if not os.path.exists(target_dir):
            continue
            
        for root, dirs, files in os.walk(target_dir):
            # Skip unwanted directories
            dirs[:] = [d for d in dirs if not any(skip in d for skip in SKIP_PATTERNS)]
            
            if any(skip in root for skip in SKIP_PATTERNS):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            
                        for i, line in enumerate(lines, 1):
                            if 'crewai' in line.lower() and not line.strip().startswith('#'):
                                # Check if it's an actual import or usage
                                if any(pattern in line for pattern in [
                                    'from crewai', 'import crewai', 'CrewAI',
                                    'crewai.', 'crewai_tools'
                                ]):
                                    results.append((filepath, i, line.strip()))
                    except Exception as e:
                        print(f"Error reading {filepath}: {e}")
    
    # Display results
    print(f"Found {len(results)} CrewAI references in project files:\n")
    
    # Group by file
    from collections import defaultdict
    by_file = defaultdict(list)
    for filepath, line_num, line in results:
        by_file[filepath].append((line_num, line))
    
    for filepath, items in sorted(by_file.items()):
        print(f"\n{filepath}: ({len(items)} references)")
        for line_num, line in items[:3]:  # Show first 3
            print(f"  Line {line_num}: {line[:80]}...")
        if len(items) > 3:
            print(f"  ... and {len(items) - 3} more")
    
    print(f"\n\nTotal files affected: {len(by_file)}")
    print(f"Total references: {len(results)}")

if __name__ == "__main__":
    find_crewai_usage() 