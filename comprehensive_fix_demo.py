#!/usr/bin/env python3
"""Comprehensive fix for AURENStreamEvent in demo file"""

import re

# Read the file
with open('auren/demo/demo_neuroscientist.py', 'r') as f:
    lines = f.readlines()

# Process line by line to fix each AURENStreamEvent
in_event = False
event_lines = []
fixed_lines = []
indent = ""

for i, line in enumerate(lines):
    if 'event = AURENStreamEvent(' in line:
        in_event = True
        event_lines = [line]
        indent = line[:line.find('event')]
    elif in_event:
        event_lines.append(line)
        if line.strip() == ')':
            # End of event, check and fix
            event_text = ''.join(event_lines)
            
            # Check what's missing
            needs_trace_id = 'trace_id=' not in event_text
            needs_target_agent = 'target_agent=' not in event_text  
            needs_metadata = 'metadata=' not in event_text
            
            # Find where to insert
            new_lines = []
            for el in event_lines:
                if needs_trace_id and 'event_id=' in el:
                    new_lines.append(el)
                    new_lines.append(f'{indent}    trace_id=str(uuid.uuid4()),\n')
                    needs_trace_id = False
                elif needs_target_agent and 'source_agent=' in el:
                    new_lines.append(el)
                    new_lines.append(f'{indent}    target_agent=None,\n')
                    needs_target_agent = False
                elif needs_metadata and 'payload=' in el and el.strip().endswith('},'):
                    new_lines.append(el)
                    new_lines.append(f'{indent}    metadata={{}},\n')
                    needs_metadata = False
                elif el.strip() == ')' and (needs_target_agent or needs_metadata):
                    # Add missing params before closing
                    if needs_target_agent:
                        new_lines.append(f'{indent}    target_agent=None,\n')
                    if needs_metadata:
                        new_lines.append(f'{indent}    metadata={{}},\n')
                    new_lines.append(el)
                else:
                    new_lines.append(el)
            
            fixed_lines.extend(new_lines)
            in_event = False
            event_lines = []
        else:
            continue
    else:
        if not in_event:
            fixed_lines.append(line)

# Write back
with open('auren/demo/demo_neuroscientist.py', 'w') as f:
    f.writelines(fixed_lines)

print("✅ Comprehensively fixed all AURENStreamEvent instantiations!") 