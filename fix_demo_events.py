#!/usr/bin/env python3
"""Fix AURENStreamEvent instantiations to include all required parameters"""

import re

# Read the demo file
with open('auren/demo/demo_neuroscientist.py', 'r') as f:
    content = f.read()

# Pattern to find AURENStreamEvent instantiations
pattern = r'event = AURENStreamEvent\(([\s\S]*?)(?=\n\s*\))'

def fix_event(match):
    """Add missing required parameters to event"""
    event_content = match.group(1)
    
    # Check what's missing and add it
    if 'trace_id' not in event_content:
        # Add trace_id after event_id
        event_content = event_content.replace(
            'event_id=str(uuid.uuid4()),',
            'event_id=str(uuid.uuid4()),\n            trace_id=str(uuid.uuid4()),'
        )
    
    if 'target_agent' not in event_content:
        # Add target_agent after source_agent if it exists, otherwise after event_type
        if 'source_agent' in event_content:
            # Find the source_agent line and add target_agent after it
            lines = event_content.split('\n')
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if 'source_agent' in line and 'target_agent' not in event_content:
                    new_lines.append('            target_agent=None,')
            event_content = '\n'.join(new_lines)
        else:
            # Add after event_type
            event_content = event_content.replace(
                'event_type=AURENEventType',
                'event_type=AURENEventType'
            )
            # Actually, let's add it at the end before payload
            if 'payload=' in event_content:
                event_content = event_content.replace(
                    'payload=',
                    'target_agent=None,\n            payload='
                )
    
    if 'metadata' not in event_content:
        # Add metadata after payload
        lines = event_content.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(line)
            if 'payload=' in line and 'metadata' not in event_content:
                # Add metadata on the next line
                new_lines.append('            metadata={},')
        event_content = '\n'.join(new_lines)
    
    return f'event = AURENStreamEvent({event_content}'

# Replace all occurrences
fixed_content = re.sub(pattern, fix_event, content)

# Write back
with open('auren/demo/demo_neuroscientist.py', 'w') as f:
    f.write(fixed_content)

print("✅ Fixed all AURENStreamEvent instantiations!")
print("Added missing: trace_id, target_agent, and metadata parameters") 