#!/usr/bin/env python3
"""
CrewAI to LangGraph Migration Script
Handles the actual 30 CrewAI references in the project
"""

import os
import re
import shutil
from pathlib import Path
from datetime import datetime

class CrewAIToLangGraphMigrator:
    def __init__(self):
        self.migrated_files = []
        self.backup_dir = Path("crewai_backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        self.errors = []
        
    def backup_file(self, filepath):
        """Create backup of file before migration"""
        backup_path = self.backup_dir / filepath
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(filepath, backup_path)
        print(f"  📁 Backed up: {filepath}")
        
    def migrate_knowledge_source_imports(self, content):
        """Migrate CrewAI knowledge source imports to LangGraph equivalents"""
        replacements = [
            # Knowledge source imports
            (r'from crewai\.knowledge\.source\.string_knowledge_source import StringKnowledgeSource',
             'from langchain.memory import ConversationStringBufferMemory as StringKnowledgeSource'),
            
            (r'from crewai\.knowledge\.source\.text_file_knowledge_source import TextFileKnowledgeSource',
             'from langchain.document_loaders import TextLoader as TextFileKnowledgeSource'),
            
            (r'from crewai\.knowledge\.source\.pdf_knowledge_source import PDFKnowledgeSource',
             'from langchain.document_loaders import PyPDFLoader as PDFKnowledgeSource'),
            
            (r'from crewai\.knowledge\.source\.csv_knowledge_source import CSVKnowledgeSource',
             'from langchain.document_loaders import CSVLoader as CSVKnowledgeSource'),
            
            (r'from crewai\.knowledge\.source\.excel_knowledge_source import ExcelKnowledgeSource',
             'from langchain.document_loaders import UnstructuredExcelLoader as ExcelKnowledgeSource'),
            
            (r'from crewai\.knowledge\.source\.json_knowledge_source import JSONKnowledgeSource',
             'from langchain.document_loaders import JSONLoader as JSONKnowledgeSource'),
            
            (r'from crewai\.knowledge\.source\.crew_docling_source import CrewDoclingSource',
             '# TODO: Implement custom docling source using LangChain\n# from langchain.document_loaders import BaseLoader as CrewDoclingSource'),
        ]
        
        for old, new in replacements:
            content = re.sub(old, new, content)
            
        return content
    
    def migrate_tool_imports(self, content):
        """Migrate CrewAI tool imports to LangChain tools"""
        replacements = [
            # Tool imports
            (r'from crewai\.tools\.agent_tools import StructuredTool as BaseTool',
             'from langchain.tools import Tool as BaseTool'),
        ]
        
        for old, new in replacements:
            content = re.sub(old, new, content)
            
        return content
    
    def update_setup_py(self, content):
        """Remove crewai from setup.py dependencies"""
        # Remove the line containing crewai
        lines = content.split('\n')
        filtered_lines = [line for line in lines if 'crewai' not in line.lower() or '#' in line]
        
        # Add LangGraph dependencies if not present
        langgraph_deps = [
            '    "langgraph>=0.2.14",',
            '    "langchain>=0.2.16",',
            '    "langchain-openai>=0.1.23",',
        ]
        
        # Find install_requires section and add dependencies
        for i, line in enumerate(filtered_lines):
            if 'install_requires' in line:
                # Find the list start
                j = i
                while j < len(filtered_lines) and '[' not in filtered_lines[j]:
                    j += 1
                if j < len(filtered_lines):
                    # Insert after the opening bracket
                    for dep in langgraph_deps:
                        if dep.strip().strip('",') not in ''.join(filtered_lines):
                            filtered_lines.insert(j + 1, dep)
                break
                
        return '\n'.join(filtered_lines)
    
    def migrate_file(self, filepath):
        """Migrate a single file from CrewAI to LangGraph"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Skip if no crewai references
            if 'crewai' not in content.lower():
                return True
                
            # Backup original
            self.backup_file(filepath)
            
            # Apply migrations based on file type
            if 'knowledge_source' in filepath:
                content = self.migrate_knowledge_source_imports(content)
            elif 'routing_tools' in filepath or 'ui_orchestrator' in filepath:
                content = self.migrate_tool_imports(content)
            elif 'setup.py' in filepath:
                content = self.update_setup_py(content)
            
            # Write migrated content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
                
            self.migrated_files.append(filepath)
            print(f"✅ Migrated: {filepath}")
            return True
            
        except Exception as e:
            self.errors.append((filepath, str(e)))
            print(f"❌ Error migrating {filepath}: {e}")
            return False
    
    def run_migration(self):
        """Run the complete migration"""
        print("=" * 60)
        print("🚀 Starting CrewAI to LangGraph Migration")
        print("=" * 60)
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        print(f"\n📁 Backup directory: {self.backup_dir}")
        
        # Files to migrate based on our analysis
        files_to_migrate = [
            "./setup.py",
            "./auren/src/tools/routing_tools.py",
            "./auren/src/agents/ui_orchestrator.py",
            "./src/auren/app/app/my_knowledge_source.py",
            "./src/auren/app/my_knowledge_source.py",
        ]
        
        print(f"\n📋 Files to migrate: {len(files_to_migrate)}")
        
        # Migrate each file
        for filepath in files_to_migrate:
            if os.path.exists(filepath):
                print(f"\n🔄 Processing: {filepath}")
                self.migrate_file(filepath)
            else:
                print(f"\n⚠️  File not found: {filepath}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Migration Summary")
        print("=" * 60)
        print(f"✅ Successfully migrated: {len(self.migrated_files)} files")
        print(f"❌ Errors encountered: {len(self.errors)} files")
        
        if self.errors:
            print("\n⚠️  Files with errors:")
            for filepath, error in self.errors:
                print(f"  - {filepath}: {error}")
        
        # Validate no CrewAI imports remain
        print("\n🔍 Validating migration...")
        remaining = self.check_remaining_crewai()
        
        if remaining == 0:
            print("✅ Migration complete! No CrewAI imports remain.")
        else:
            print(f"⚠️  {remaining} CrewAI references still found. Manual review needed.")
            
        return len(self.errors) == 0
    
    def check_remaining_crewai(self):
        """Check for any remaining CrewAI imports"""
        count = 0
        for root, dirs, files in os.walk('.'):
            if any(skip in root for skip in ['.git', 'venv', 'node_modules', 'crewai_backup']):
                continue
                
            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if 'crewai' in content.lower() and 'from crewai' in content:
                                count += 1
                    except:
                        pass
        return count

if __name__ == "__main__":
    migrator = CrewAIToLangGraphMigrator()
    success = migrator.run_migration()
    exit(0 if success else 1) 