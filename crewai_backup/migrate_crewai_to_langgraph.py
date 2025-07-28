#!/usr/bin/env python3
"""
MASS MIGRATION SCRIPT: CrewAI → LangGraph
Transforms entire codebase in one pass
"""

import os
import re
from pathlib import Path
import shutil
from typing import Dict, List, Tuple

class CrewAIToLangGraphMigrator:
    """Ultra-fast pattern-based migrator"""
    
    def __init__(self):
        self.files_migrated = 0
        self.backup_dir = Path("crewai_backup")
        self.backup_dir.mkdir(exist_ok=True)
        
    def migrate_imports(self, content: str) -> str:
        """Transform all CrewAI imports to LangGraph equivalents"""
        replacements = [
            # Core imports
            (r'from crewai import Agent\b', 'from typing import TypedDict, Annotated, List\nfrom langgraph.graph import StateGraph, START, END'),
            (r'from crewai import Task\b', 'from langchain_core.messages import BaseMessage'),
            (r'from crewai import Crew\b', 'from langgraph.graph import StateGraph'),
            (r'from crewai import Process\b', 'from langgraph.graph.message import add_messages'),
            (r'from crewai import LLM\b', 'from langchain_openai import ChatOpenAI'),
            
            # Tools imports
            (r'from crewai\.tools import BaseTool\b', 'from langchain.tools import Tool\nfrom langchain_core.pydantic_v1 import BaseModel, Field'),
            (r'from crewai_tools import .*', 'from langchain.tools import Tool'),
            
            # Other imports
            (r'from crewai import TaskOutput\b', 'from typing import Dict, Any'),
            (r'import crewai\b', 'import langgraph'),
        ]
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        return content
    
    def transform_agent_class(self, content: str) -> str:
        """Transform Agent classes to LangGraph pattern"""
        # Find all Agent class definitions
        agent_pattern = r'class\s+(\w+)\s*\(\s*Agent\s*\)\s*:'
        
        def replace_agent(match):
            class_name = match.group(1)
            return f'''class {class_name}:
    """LangGraph-based agent (migrated from CrewAI)"""
    
    def __init__(self, llm=None):
        self.llm = llm or ChatOpenAI(model="gpt-4")
        self.name = "{class_name}"
        
    def create_graph(self):
        """Create LangGraph workflow"""
        workflow = StateGraph(dict)
        
        # Add nodes based on previous agent behavior
        workflow.add_node("process", self.process)
        workflow.add_edge(START, "process")
        workflow.add_edge("process", END)
        
        return workflow.compile()
    
    def process(self, state: dict) -> dict:
        """Main processing logic"""
        # Agent logic here
        return state'''
        
        content = re.sub(agent_pattern, replace_agent, content, flags=re.MULTILINE)
        return content
    
    def transform_task_class(self, content: str) -> str:
        """Transform Task usage to LangGraph nodes"""
        # Replace Task instantiation
        task_pattern = r'Task\s*\(\s*([^)]+)\s*\)'
        
        def replace_task(match):
            params = match.group(1)
            return f'# Task migrated to node in StateGraph\n        # Original params: {params}'
        
        content = re.sub(task_pattern, replace_task, content)
        return content
    
    def transform_crew_class(self, content: str) -> str:
        """Transform Crew to LangGraph orchestrator"""
        crew_pattern = r'Crew\s*\(\s*([^)]+)\s*\)'
        
        def replace_crew(match):
            return '''StateGraph(dict)
        
        # Build graph from agents and tasks
        for agent in self.agents:
            workflow.add_node(agent.name, agent.process)
        
        # Connect nodes
        workflow.add_edge(START, self.agents[0].name)
        for i in range(len(self.agents) - 1):
            workflow.add_edge(self.agents[i].name, self.agents[i+1].name)
        workflow.add_edge(self.agents[-1].name, END)
        
        return workflow.compile()'''
        
        content = re.sub(crew_pattern, replace_crew, content)
        return content
    
    def transform_tool_class(self, content: str) -> str:
        """Transform BaseTool to LangChain Tool"""
        # Find tool classes
        tool_pattern = r'class\s+(\w+)\s*\(\s*BaseTool\s*\)\s*:(.*?)(?=class|\Z)'
        
        def replace_tool(match):
            class_name = match.group(1)
            class_body = match.group(2)
            
            # Extract description if exists
            desc_match = re.search(r'description\s*=\s*["\']([^"\']+)["\']', class_body)
            description = desc_match.group(1) if desc_match else f"{class_name} tool"
            
            # Extract run method
            run_match = re.search(r'def\s+run\s*\([^)]*\)\s*:(.*?)(?=def|\Z)', class_body, re.DOTALL)
            run_body = run_match.group(1) if run_match else 'pass'
            
            return f'''class {class_name}Input(BaseModel):
    """Input for {class_name}"""
    query: str = Field(description="Input query")

def {class_name.lower()}_func(query: str) -> str:
    """{description}"""
    {run_body}

{class_name.lower()}_tool = Tool(
    name="{class_name}",
    func={class_name.lower()}_func,
    description="""{description}""",
    args_schema={class_name}Input
)'''
        
        content = re.sub(tool_pattern, replace_tool, content, flags=re.DOTALL)
        return content
    
    def migrate_file(self, filepath: Path) -> bool:
        """Migrate a single file"""
        try:
            # Read content
            content = filepath.read_text()
            
            # Skip if no CrewAI references
            if 'crewai' not in content.lower():
                return False
            
            # Backup original
            backup_path = self.backup_dir / filepath.name
            shutil.copy2(filepath, backup_path)
            
            # Apply all transformations
            content = self.migrate_imports(content)
            content = self.transform_agent_class(content)
            content = self.transform_task_class(content)
            content = self.transform_crew_class(content)
            content = self.transform_tool_class(content)
            
            # Additional cleanup
            content = re.sub(r'\.get_crewai_\w+\(\)', '', content)
            content = re.sub(r'crewai_', 'langgraph_', content)
            
            # Write back
            filepath.write_text(content)
            self.files_migrated += 1
            print(f"✅ Migrated: {filepath}")
            return True
            
        except Exception as e:
            print(f"❌ Error migrating {filepath}: {e}")
            return False
    
    def migrate_all(self):
        """Migrate entire codebase"""
        print("🚀 Starting mass migration CrewAI → LangGraph")
        
        # Find all Python files
        py_files = list(Path('.').rglob('*.py'))
        print(f"📁 Found {len(py_files)} Python files")
        
        # Migrate in parallel (conceptually - actually sequential but fast)
        for py_file in py_files:
            self.migrate_file(py_file)
        
        # Update requirements.txt
        self.update_requirements()
        
        print(f"\n✅ Migration complete! {self.files_migrated} files transformed")
        print(f"📁 Backups saved in: {self.backup_dir}")
        
    def update_requirements(self):
        """Update requirements.txt to remove CrewAI and add LangGraph"""
        req_file = Path('requirements.txt')
        if req_file.exists():
            lines = req_file.read_text().splitlines()
            
            # Filter out CrewAI
            new_lines = [line for line in lines if 'crewai' not in line.lower()]
            
            # Add LangGraph dependencies
            langgraph_deps = [
                'langgraph==0.2.27',
                'langchain==0.2.16',
                'langchain-openai==0.1.23',
                'langchain-core==0.2.39',
                'langsmith==0.1.93'
            ]
            
            new_lines.extend(langgraph_deps)
            
            # Write back
            req_file.write_text('\n'.join(sorted(set(new_lines))) + '\n')
            print("✅ Updated requirements.txt")

if __name__ == "__main__":
    migrator = CrewAIToLangGraphMigrator()
    migrator.migrate_all() 