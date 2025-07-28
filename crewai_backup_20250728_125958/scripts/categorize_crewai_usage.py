#!/usr/bin/env python3
"""
CrewAI Usage Categorization Script
Purpose: Analyze and categorize all CrewAI imports for systematic migration
Author: Senior Engineer
Date: January 29, 2025
"""

import os
import re
from collections import defaultdict
from datetime import datetime

def categorize_crewai_usage():
    categories = defaultdict(list)
    
    # Skip these directories
    skip_dirs = {'node_modules', '.git', 'venv', '__pycache__', '.pytest_cache', 
                 'venv_new', 'crewai_backup', 'recreate', '#'}
    
    for root, dirs, files in os.walk('.'):
        # Remove directories we want to skip
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        
        if any(skip in root for skip in skip_dirs):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                # Skip this script itself
                if 'categorize_crewai_usage.py' in filepath:
                    continue
                    
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')
                        
                    for i, line in enumerate(lines):
                        # Look for actual imports, not just any mention
                        if not line.strip().startswith('#'):
                            # Check for imports
                            if re.search(r'from\s+crewai\s+import\s+Agent', line):
                                categories['agent'].append((filepath, i+1, line.strip()))
                            elif re.search(r'from\s+crewai\.agent\s+import', line):
                                categories['agent'].append((filepath, i+1, line.strip()))
                            elif re.search(r'from\s+crewai\s+import\s+Task', line):
                                categories['task'].append((filepath, i+1, line.strip()))
                            elif re.search(r'from\s+crewai\.task\s+import', line):
                                categories['task'].append((filepath, i+1, line.strip()))
                            elif re.search(r'from\s+crewai\s+import\s+Crew', line):
                                categories['crew'].append((filepath, i+1, line.strip()))
                            elif re.search(r'from\s+crewai\.crew\s+import', line):
                                categories['crew'].append((filepath, i+1, line.strip()))
                            elif re.search(r'from\s+crewai\.tools', line) or re.search(r'from\s+crewai_tools', line):
                                categories['tools'].append((filepath, i+1, line.strip()))
                            elif re.search(r'from\s+crewai\s+import', line):
                                categories['core_imports'].append((filepath, i+1, line.strip()))
                            elif re.search(r'import\s+crewai', line):
                                categories['module_import'].append((filepath, i+1, line.strip()))
                            elif re.search(r'crewai\s*==', line) or re.search(r'crewai-tools\s*==', line):
                                categories['requirements'].append((filepath, i+1, line.strip()))
                            elif 'CrewAI' in line and 'class' in line:
                                categories['class_references'].append((filepath, i+1, line.strip()))
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")
                    continue
    
    # Generate report
    print("=" * 80)
    print("CREWAI USAGE CATEGORIZATION REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    total = 0
    files_affected = set()
    
    for category, items in sorted(categories.items()):
        if not items:  # Skip empty categories
            continue
            
        print(f"\n{category.upper()}: {len(items)} instances")
        print("-" * 40)
        
        # Group by file
        file_groups = defaultdict(list)
        for filepath, line_num, line in items:
            file_groups[filepath].append((line_num, line))
            files_affected.add(filepath)
        
        # Show up to 3 files per category
        for i, (filepath, file_items) in enumerate(file_groups.items()):
            if i >= 3:
                print(f"  ... and {len(file_groups) - 3} more files")
                break
            print(f"  {filepath} ({len(file_items)} instances)")
            for j, (line_num, line) in enumerate(file_items[:2]):
                print(f"    Line {line_num}: {line[:80]}...")
                
        total += len(items)
    
    print(f"\n{'=' * 80}")
    print(f"TOTAL CrewAI references: {total}")
    print(f"Files affected: {len(files_affected)}")
    print(f"{'=' * 80}")
    
    # Save detailed report
    with open('crewai_migration_report.txt', 'w') as f:
        f.write(f"CrewAI Migration Report - {datetime.now()}\n")
        f.write("=" * 80 + "\n\n")
        
        for category, items in sorted(categories.items()):
            if not items:
                continue
            f.write(f"{category.upper()}: {len(items)} instances\n")
            f.write("-" * 40 + "\n")
            for filepath, line_num, line in items:
                f.write(f"{filepath}:{line_num} - {line}\n")
            f.write("\n")
            
        f.write(f"\nTotal references: {total}\n")
        f.write(f"Files affected: {len(files_affected)}\n")
    
    print("\nDetailed report saved to: crewai_migration_report.txt")
    
    return categories, files_affected

if __name__ == "__main__":
    categorize_crewai_usage() 