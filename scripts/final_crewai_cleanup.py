#!/usr/bin/env python3
"""
Final CrewAI Cleanup - Remove remaining references
Author: Senior Engineer
Date: January 29, 2025
"""

import os
import re
import shutil
from datetime import datetime

def final_cleanup():
    """Clean up final CrewAI references"""
    
    # Specific files and their replacements
    cleanup_targets = [
        # Database references
        {
            'file': 'src/auren/app/db_utils.py',
            'old': '# or fallback to: "sqlite:///crewai.db"',
            'new': '# or fallback to: "sqlite:///auren.db"'
        },
        {
            'file': 'src/auren/app/app/db_utils.py',
            'old': '# or fallback to: "sqlite:///crewai.db"',
            'new': '# or fallback to: "sqlite:///auren.db"'
        },
        # Agent comments
        {
            'file': 'agents/my_agent.py',
            'old': '# --- CrewAI glue ---',
            'new': '# --- LangGraph integration ---'
        },
        {
            'file': 'src/auren/agents/my_agent.py',
            'old': '# --- CrewAI glue ---',
            'new': '# --- LangGraph integration ---'
        },
        # Tool comments
        {
            'file': 'src/auren/app/my_tools.py',
            'old': 'def __call__(self, *args, **kwargs):  # Streamlit and CrewAI expect tools to be callable',
            'new': 'def __call__(self, *args, **kwargs):  # Streamlit and LangGraph expect tools to be callable'
        },
        {
            'file': 'src/auren/app/my_tools.py',
            'old': '# CrewAI tools may look for a run() method – alias it to __call__ for safety',
            'new': '# LangGraph tools may look for a run() method – alias it to __call__ for safety'
        },
        {
            'file': 'src/auren/app/my_tools.py',
            'old': '"Connect to an MCP server and expose its tools inside CrewAI."',
            'new': '"Connect to an MCP server and expose its tools inside LangGraph."'
        },
        # Test data
        {
            'file': 'scripts/test_whatsapp_flow.py',
            'old': '"text": {"body": "Hello, CrewAI!"}',
            'new': '"text": {"body": "Hello, AUREN!"}'
        },
        {
            'file': 'scripts/test_whatsapp_flow.py',
            'old': 'result = tool._run(webhook_payload=webhook_payload, response_message="Hi! This is CrewAI responding.")',
            'new': 'result = tool._run(webhook_payload=webhook_payload, response_message="Hi! This is AUREN responding.")'
        }
    ]
    
    files_modified = 0
    errors = []
    
    print("🧹 Final CrewAI Cleanup")
    print("=" * 80)
    
    for target in cleanup_targets:
        filepath = target['file']
        
        if not os.path.exists(filepath):
            print(f"⚠️  File not found: {filepath}")
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if target['old'] in content:
                # Backup
                backup_path = filepath + '.finalbak'
                shutil.copy2(filepath, backup_path)
                
                # Replace
                new_content = content.replace(target['old'], target['new'])
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                os.remove(backup_path)
                files_modified += 1
                print(f"✅ Updated: {filepath}")
                print(f"   Changed: '{target['old'][:50]}...'")
                print(f"   To: '{target['new'][:50]}...'")
            else:
                print(f"⏭️  Already clean: {filepath}")
                
        except Exception as e:
            errors.append(f"Error in {filepath}: {str(e)}")
            print(f"❌ Error: {filepath} - {str(e)}")
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL CLEANUP SUMMARY")
    print("=" * 80)
    print(f"Files modified: {files_modified}")
    print(f"Errors: {len(errors)}")
    
    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
    
    print("\n✨ Final cleanup complete!")
    
    # Note about migration scripts
    print("\n📝 Note: Migration scripts still contain 'CrewAI' references, which is expected.")
    print("   These scripts document the migration process and should be kept for reference.")

if __name__ == "__main__":
    final_cleanup() 