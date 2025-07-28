#!/usr/bin/env python3
"""
Smart CrewAI to LangGraph Migration Tool
Handles complex patterns and preserves functionality
Author: Senior Engineer  
Date: January 29, 2025
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from auren.core.streaming.langgraph_event_streamer import LangGraphEventStreamer as CrewAIEventInstrumentation

class SmartCrewAIMigrator:
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
        
    def restore_file(self, filepath: str):
        """Restore file from backup if migration failed"""
        backup_path = os.path.join(self.backup_dir, filepath)
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, filepath)
            
    def migrate_crewai_event_instrumentation(self, content: str) -> str:
        """Replace CrewAIEventInstrumentation with proper LangGraph pattern"""
        
        # First, add necessary imports at the top if not present
        if 'LangGraphEventStreamer as CrewAIEventInstrumentation' in content and 'from datetime import datetime' not in content:
            # Find the last import line
            import_lines = []
            lines = content.split('\n')
            last_import_idx = 0
            
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    last_import_idx = i
                    
            # Add datetime import after last import
            lines.insert(last_import_idx + 1, 'from datetime import datetime')
            content = '\n'.join(lines)
        
        # Replace the class name and instantiation
        content = re.sub(
            r'CrewAIEventInstrumentation',
            'LangGraphEventStreamer',
            content
        )
        
        # Add the LangGraphEventStreamer class definition if needed
        if 'class LangGraphEventStreamer' not in content and 'LangGraphEventStreamer(' in content:
            # Add class definition at the top of the file after imports
            class_def = '''
class LangGraphEventStreamer:
    """LangGraph event streaming for real-time updates"""
    
    def __init__(self, *args, **kwargs):
        self.event_stream = []
        
    async def stream_event(self, event_type: str, data: dict):
        """Stream events to connected clients"""
        self.event_stream.append({
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
    def get_events(self):
        return self.event_stream
'''
            # Find where to insert (after imports)
            lines = content.split('\n')
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    insert_idx = i + 1
                elif line.strip() and not line.startswith('#'):
                    break
                    
            lines.insert(insert_idx + 1, class_def)
            content = '\n'.join(lines)
            
        return content
    
    def migrate_langgraph_integration_files(self, content: str, filepath: str) -> str:
        """Special handling for files named langgraph_integration.py"""
        
        if 'langgraph_integration' in filepath:
            # These files are adapters - rename the class but keep the file
            content = re.sub(
                r'class LangGraphIntelligenceAdapter',
                'class LangGraphIntelligenceAdapter',
                content
            )
            
            content = re.sub(
                r'LangGraph Integration',
                'LangGraph Integration',
                content
            )
            
            content = re.sub(
                r'LangGraph agents',
                'LangGraph agents',
                content
            )
            
        return content
    
    def migrate_imports_carefully(self, content: str) -> str:
        """Carefully migrate imports without breaking syntax"""
        
        # Handle combined imports first
        lines = content.split('\n')
        new_lines = []
        
        for line in lines:
            if 'from crewai import' in line:
                # Extract what's being imported
                match = re.match(r'from crewai import (.+)', line)
                if match:
                    imports = match.group(1)
                    
                    # Map CrewAI imports to LangGraph equivalents
                    import_mapping = {
                        'Agent': 'from langgraph.prebuilt import create_react_agent',
                        'Task': 'from langgraph.graph import StateGraph',
                        'Crew': 'from langgraph.graph import StateGraph',
                        'tool': 'from langchain.tools import Tool',
                    }
                    
                    # Check which imports we need
                    new_imports = []
                    for crewai_import, langgraph_import in import_mapping.items():
                        if crewai_import in imports:
                            if langgraph_import not in '\n'.join(new_lines):
                                new_imports.append(langgraph_import)
                    
                    # Add the new imports
                    new_lines.extend(new_imports)
                    
                    # Add typing imports if needed
                    if 'Agent' in imports or 'Task' in imports:
                        if 'from typing import' not in content:
                            new_lines.append('from typing import TypedDict, Annotated, List, Optional')
                else:
                    new_lines.append(line)
            elif 'from crewai_tools' in line:
                new_lines.append('from langchain.tools import Tool')
            elif 'import crewai' in line:
                new_lines.append('import langgraph')
            else:
                new_lines.append(line)
                
        return '\n'.join(new_lines)
    
    def migrate_gateway_adapter(self, content: str) -> str:
        """Migrate LangGraph gateway adapter patterns"""
        
        # Replace class names
        content = re.sub(
            r'LangGraphGatewayAdapter',
            'LangGraphGatewayAdapter',
            content
        )
        
        content = re.sub(
            r'CrewAIGateway',
            'LangGraphGateway',
            content
        )
        
        return content
    
    def migrate_ui_strings(self, content: str) -> str:
        """Update UI strings"""
        
        # Replace in strings only
        content = re.sub(
            r'(["\'`])AUREN Studio(["\'`])',
            r'\1AUREN Studio\2',
            content
        )
        
        content = re.sub(
            r'(["\'`])AUREN-Studio(["\'`])',
            r'\1AUREN-Studio\2',
            content
        )
        
        return content
        
    def migrate_file(self, filepath: str) -> bool:
        """Migrate a single file with smart pattern recognition"""
        
        try:
            # Read file
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()
                
            # Skip if no CrewAI references
            if 'crewai' not in original_content.lower():
                return True
                
            # Backup original
            self.backup_file(filepath)
            
            # Apply migrations in specific order
            content = original_content
            
            # 1. Handle imports carefully
            content = self.migrate_imports_carefully(content)
            
            # 2. Handle CrewAIEventInstrumentation
            content = self.migrate_crewai_event_instrumentation(content)
            
            # 3. Handle integration files
            content = self.migrate_langgraph_integration_files(content, filepath)
            
            # 4. Handle gateway adapters
            content = self.migrate_gateway_adapter(content)
            
            # 5. Update UI strings
            content = self.migrate_ui_strings(content)
            
            # Validate Python syntax before writing
            try:
                compile(content, filepath, 'exec')
            except SyntaxError as e:
                self.errors.append(f"❌ Would create syntax error in {filepath}: {e}")
                return False
                
            # Write migrated content
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                self.files_migrated += 1
                self.report.append(f"✅ Migrated: {filepath}")
                
                # Check for remaining references
                remaining = len(re.findall(r'crewai', content, re.IGNORECASE))
                if remaining > 0:
                    self.report.append(f"  ⚠️  Still has {remaining} CrewAI references")
                    
            return True
            
        except Exception as e:
            self.errors.append(f"❌ Error in {filepath}: {str(e)}")
            # Restore from backup
            self.restore_file(filepath)
            return False
            
    def migrate_directory(self, directory: str):
        """Migrate all Python files in a directory"""
        
        # Get all Python files
        python_files = []
        for root, dirs, files in os.walk(directory):
            # Skip virtual environments and backups
            dirs[:] = [d for d in dirs if d not in ['venv', '.venv', '__pycache__', 'node_modules', 'crewai_backup']]
            
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
                    
        # Process files
        print(f"Found {len(python_files)} Python files in {directory}")
        
        for i, filepath in enumerate(python_files, 1):
            print(f"[{i}/{len(python_files)}] Processing: {filepath}")
            self.migrate_file(filepath)
            
    def generate_report(self):
        """Generate detailed migration report"""
        
        print("\n" + "=" * 80)
        print("SMART CREWAI TO LANGGRAPH MIGRATION REPORT")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        print(f"\nFiles migrated: {self.files_migrated}")
        print(f"Errors: {len(self.errors)}")
        
        if self.report:
            print("\nMigration Log:")
            for entry in self.report[:20]:  # Show first 20
                print(f"  {entry}")
            if len(self.report) > 20:
                print(f"  ... and {len(self.report) - 20} more")
                
        if self.errors:
            print("\nErrors:")
            for error in self.errors[:10]:  # Show first 10
                print(f"  {error}")
            if len(self.errors) > 10:
                print(f"  ... and {len(self.errors) - 10} more")
                
        # Save detailed report
        with open('smart_migration_report.txt', 'w') as f:
            f.write(f"Smart CrewAI to LangGraph Migration Report\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"Files migrated: {self.files_migrated}\n")
            f.write(f"Backup directory: {self.backup_dir}\n\n")
            
            if self.report:
                f.write("Migration Log:\n")
                for entry in self.report:
                    f.write(f"{entry}\n")
                    
            if self.errors:
                f.write("\n\nErrors:\n")
                for error in self.errors:
                    f.write(f"{error}\n")

def main():
    import sys
    
    # Allow specific directory or default to project directories
    if len(sys.argv) > 1:
        target_dirs = sys.argv[1:]
    else:
        target_dirs = ['auren/core/streaming', 'auren/realtime']  # Start with a subset
    
    migrator = SmartCrewAIMigrator()
    
    print("Starting SMART CrewAI to LangGraph migration...")
    print(f"Backup directory: {migrator.backup_dir}")
    
    for directory in target_dirs:
        if os.path.exists(directory):
            print(f"\nMigrating {directory}...")
            migrator.migrate_directory(directory)
        else:
            print(f"Directory not found: {directory}")
    
    migrator.generate_report()
    
    print(f"\n✅ Migration complete!")
    print(f"Backup saved to: {migrator.backup_dir}")
    print("Review smart_migration_report.txt for details")

if __name__ == "__main__":
    main() 