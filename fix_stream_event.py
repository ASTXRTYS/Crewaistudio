#!/usr/bin/env python3
"""Fix stream_event method calls in demo file"""

# Read the file
with open('auren/demo/demo_neuroscientist.py', 'r') as f:
    content = f.read()

# Replace all occurrences of the incorrect method call
content = content.replace(
    'await self.event_instrumentation.stream_event(event)',
    '''# Stream event directly through the event streamer
        if self.event_streamer:
            await self.event_streamer.stream_event(event)'''
)

# Write back
with open('auren/demo/demo_neuroscientist.py', 'w') as f:
    f.write(content)

print("✅ Fixed all stream_event method calls!") 