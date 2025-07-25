#!/usr/bin/env python3
"""Fix all AURENStreamEvent metadata placement issues"""

# Read the file
with open('auren/demo/demo_neuroscientist.py', 'r') as f:
    lines = f.readlines()

# Find and fix problematic patterns
fixed_lines = []
skip_next = False

for i, line in enumerate(lines):
    if skip_next:
        skip_next = False
        continue
        
    # Check if this is a misplaced metadata line
    if i > 0 and 'metadata={},' in line.strip() and 'payload={' in lines[i-1]:
        # Skip this line - it will be added in the right place later
        continue
    
    # Check if we need to add metadata after payload closing
    if '},' in line and i > 0 and 'payload=' in lines[i-5:i]:
        # This is likely the end of a payload dict
        fixed_lines.append(line)
        # Check if metadata is missing in the next few lines
        has_metadata = False
        for j in range(i+1, min(i+5, len(lines))):
            if 'metadata=' in lines[j]:
                has_metadata = True
                break
        
        if not has_metadata:
            # Add metadata with same indentation as the line
            indent = line[:len(line) - len(line.lstrip())]
            fixed_lines.append(f'{indent}metadata={{}},\n')
    else:
        fixed_lines.append(line)

# Write back
with open('auren/demo/demo_neuroscientist.py', 'w') as f:
    f.writelines(fixed_lines)

print("✅ Fixed all AURENStreamEvent metadata placements!") 