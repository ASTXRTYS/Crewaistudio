#!/usr/bin/env python3
"""
CrewAI to LangGraph Migration Tool
Author: Senior Engineer
Date: January 29, 2025
Purpose: Systematically migrate all CrewAI dependencies to LangGraph
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
from auren.core.streaming.langgraph_event_streamer import LangGraphEventStreamer

class CrewAIToLangGraphMigrator:
    def __init__(self):
        self.backup_dir = f"crewai_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.report = []
        self.files_migrated = 0
        self.errors = []
        
    def backup_file(self, filepath: str):
        """Create backup of file before migration"""
        backup_path = os.path.join(self.backup_dir, filepath)
        os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(filepath, backup_path)
        
    def migrate_imports(self, content: str) -> str:
        """Convert CrewAI imports to LangGraph imports"""
        replacements = [
            # Basic imports
            (r'from crewai import Agent', 
             'from typing import TypedDict, Annotated\nfrom langgraph.graph import StateGraph, START, END'),
            
            (r'from crewai import Task',
             'from langgraph.graph import StateGraph'),
            
            (r'from crewai import Crew',
             'from langgraph.graph import StateGraph'),
            
            (r'from crewai\.tools import tool',
             'from langchain.tools import Tool'),
            
            (r'from crewai_tools import .*',
             'from langchain.tools import Tool'),
            
            # Replace CrewAI gateway with LangGraph patterns
            (r'from auren.src.auren.ai.langgraph_gateway_adapter import LangGraphGatewayAdapter as LangGraphGatewayAdapter',
             'from langgraph.prebuilt import ToolExecutor'),
            
            (r'import crewai',
             'import langgraph'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            
        return content
    
    def migrate_event_instrumentation(self, content: str) -> str:
        """Replace LangGraphEventStreamer with LangGraph equivalent"""
        
        # Replace class definition
        content = re.sub(
            r'class LangGraphEventStreamer:.*?(?=\nclass|\n\n|\Z)',
            '''class LangGraphEventStreamer:
    """LangGraph event streaming for real-time updates"""
    
    def __init__(self):
        self.event_stream = []
        
    async def stream_event(self, event_type: str, data: dict):
        """Stream events to connected clients"""
        self.event_stream.append({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    def get_events(self):
        return self.event_stream''',
            content,
            flags=re.DOTALL
        )
        
        # Replace instantiation
        content = re.sub(
            r'LangGraphEventStreamer\(',
            'LangGraphEventStreamer(',
            content
        )
        
        return content
    
    def migrate_agent_patterns(self, content: str) -> str:
        """Convert CrewAI Agent patterns to LangGraph StateGraph"""
        
        # Pattern for agent class that extends Agent
        agent_class_pattern = r'class\s+(\w+)\s*\(\s*Agent\s*\):'
        
        def replace_agent_class(match):
            class_name = match.group(1)
            return f'''class {class_name}:
    """LangGraph-based agent implementation"""
    
    def __init__(self, *args, **kwargs):
        self.graph = StateGraph(AgentState)
        self._build_graph()
        
    def _build_graph(self):
        """Build the LangGraph state machine"""
        pass'''
        
        content = re.sub(agent_class_pattern, replace_agent_class, content)
        
        return content
    
    def migrate_ui_references(self, content: str) -> str:
        """Update UI strings from CrewAI to AUREN"""
        replacements = [
            ('AUREN Studio', 'AUREN Studio'),
            ('AUREN-Studio', 'AUREN-Studio'),
            ('crewai', 'langgraph'),  # Only in strings/comments
        ]
        
        for old, new in replacements:
            # Only replace in strings and comments
            content = re.sub(
                f'(["\']).*?{re.escape(old)}.*?\\1',
                lambda m: m.group(0).replace(old, new),
                content
            )
            
        return content
    
    def migrate_file(self, filepath: str) -> bool:
        """Migrate a single file from CrewAI to LangGraph"""
        try:
            # Skip if already migrated
            if filepath.endswith('.langgraph_migrated'):
                return True
                
            # Read file
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check if file needs migration
            if 'crewai' not in content.lower():
                return True
                
            # Backup original
            self.backup_file(filepath)
            
            # Apply migrations in order
            original_content = content
            content = self.migrate_imports(content)
            content = self.migrate_event_instrumentation(content)
            content = self.migrate_agent_patterns(content)
            content = self.migrate_ui_references(content)
            
            # Only write if changed
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                self.files_migrated += 1
                self.report.append(f"✅ Migrated: {filepath}")
                
            return True
            
        except Exception as e:
            self.errors.append(f"❌ Error in {filepath}: {str(e)}")
            return False
    
    def validate_migration(self, filepath: str) -> bool:
        """Validate that migration was successful"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Check for remaining CrewAI references
            crewai_refs = re.findall(r'crewai', content, re.IGNORECASE)
            
            # Filter out false positives (comments, strings)
            actual_refs = []
            for ref in crewai_refs:
                line_with_ref = [line for line in content.split('\n') if ref in line][0]
                if not line_with_ref.strip().startswith('#'):
                    actual_refs.append(ref)
                    
            if actual_refs:
                self.report.append(f"⚠️  {filepath} still has {len(actual_refs)} CrewAI references")
                return False
                
            # Try to compile the Python file
            compile(content, filepath, 'exec')
            
            return True
            
        except SyntaxError as e:
            self.errors.append(f"❌ Syntax error in {filepath}: {e}")
            return False
        except Exception as e:
            self.errors.append(f"❌ Validation error in {filepath}: {e}")
            return False
    
    def migrate_directory(self, directory: str):
        """Migrate all Python files in a directory"""
        for root, dirs, files in os.walk(directory):
            # Skip backup and virtual env directories
            dirs[:] = [d for d in dirs if d not in ['venv', '.venv', '__pycache__', 'node_modules']]
            
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    print(f"Processing: {filepath}")
                    
                    if self.migrate_file(filepath):
                        self.validate_migration(filepath)
    
    def generate_report(self):
        """Generate migration report"""
        print("\n" + "=" * 80)
        print("CREWAI TO LANGGRAPH MIGRATION REPORT")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        print(f"\nFiles migrated: {self.files_migrated}")
        print(f"Errors: {len(self.errors)}")
        
        if self.report:
            print("\nMigration Log:")
            for entry in self.report:
                print(f"  {entry}")
                
        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  {error}")
                
        # Save detailed report
        with open('migration_report.txt', 'w') as f:
            f.write(f"CrewAI to LangGraph Migration Report\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Files migrated: {self.files_migrated}\n")
            f.write(f"Backup directory: {self.backup_dir}\n\n")
            
            f.write("Migration Log:\n")
            for entry in self.report:
                f.write(f"{entry}\n")
                
            if self.errors:
                f.write("\nErrors:\n")
                for error in self.errors:
                    f.write(f"{error}\n")

def main():
    # Target directories based on our analysis
    TARGET_DIRS = ['app', 'auren', 'src', 'agents', 'config', 'scripts', 'tests']
    
    migrator = CrewAIToLangGraphMigrator()
    
    print("Starting CrewAI to LangGraph migration...")
    print(f"Backup directory: {migrator.backup_dir}")
    
    for directory in TARGET_DIRS:
        if os.path.exists(directory):
            print(f"\nMigrating {directory}...")
            migrator.migrate_directory(directory)
    
    migrator.generate_report()
    
    print("\n✅ Migration complete!")
    print(f"Backup saved to: {migrator.backup_dir}")
    print("Review migration_report.txt for details")

if __name__ == "__main__":
    main() 