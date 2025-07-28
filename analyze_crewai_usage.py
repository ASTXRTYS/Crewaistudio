#!/usr/bin/env python3
"""
CrewAI Usage Analysis Script
Categorizes all 906 CrewAI imports for systematic migration
"""

import os
import re
from collections import defaultdict
from pathlib import Path

def categorize_crewai_usage():
    categories = defaultdict(list)
    
    # Skip these directories
    skip_dirs = {'.git', 'node_modules', 'venv', '.venv', '__pycache__', 
                 'crewai_backup', '.pytest_cache', 'htmlcov'}
    
    for root, dirs, files in os.walk('.'):
        # Remove skip directories from traversal
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        if any(skip in root for skip in skip_dirs):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                    for i, line in enumerate(lines):
                        if 'crewai' in line.lower():
                            # Categorize by import type
                            if 'from crewai import Agent' in line:
                                categories['agent'].append((filepath, i+1, line))
                            elif 'from crewai import Task' in line:
                                categories['task'].append((filepath, i+1, line))
                            elif 'from crewai import Crew' in line:
                                categories['crew'].append((filepath, i+1, line))
                            elif 'from crewai.tools' in line:
                                categories['tools'].append((filepath, i+1, line))
                            elif 'BaseTool' in line and 'crewai' in line:
                                categories['tools'].append((filepath, i+1, line))
                            elif 'crewai' in line:
                                categories['other'].append((filepath, i+1, line))
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
                    continue
    
    # Generate detailed report
    print("=" * 60)
    print("=== CrewAI Usage Analysis Report ===")
    print("=" * 60)
    
    total = 0
    for category, items in categories.items():
        print(f"\n{category.upper()}: {len(items)} instances")
        total += len(items)
        
        # Group by file
        files_in_category = defaultdict(list)
        for filepath, line_num, line in items:
            files_in_category[filepath].append((line_num, line))
        
        print(f"  Affected files: {len(files_in_category)}")
        
        # Show first 5 files as examples
        for filepath, occurrences in list(files_in_category.items())[:5]:
            print(f"\n  📄 {filepath}")
            for line_num, line in occurrences[:2]:  # Show first 2 lines per file
                print(f"     Line {line_num}: {line.strip()}")
            if len(occurrences) > 2:
                print(f"     ... and {len(occurrences) - 2} more occurrences")
    
    print(f"\n{'=' * 60}")
    print(f"TOTAL: {total} CrewAI references")
    print(f"TOTAL FILES: {len(set(fp for items in categories.values() for fp, _, _ in items))}")
    print("=" * 60)
    
    # Save results to file for reference
    with open('crewai_migration_analysis.txt', 'w') as f:
        f.write(f"CrewAI Migration Analysis\n")
        f.write(f"{'=' * 60}\n\n")
        for category, items in categories.items():
            f.write(f"{category.upper()}: {len(items)} instances\n")
            for filepath, line_num, line in items:
                f.write(f"  {filepath}:{line_num} - {line.strip()}\n")
        f.write(f"\nTOTAL: {total} CrewAI references\n")
    
    print("\n✅ Analysis saved to crewai_migration_analysis.txt")
    
    return categories

if __name__ == "__main__":
    categories = categorize_crewai_usage() 