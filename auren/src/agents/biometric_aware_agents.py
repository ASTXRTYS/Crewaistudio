"""Updated agent factory with proper tool instantiation."""

from typing import List, Dict, Any, Optional
import yaml
from pathlib import Path
from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool

from src.tools.protocol_tools import ToolFactory


class AurenAgentFactory:
    """Factory for creating AUREN agents with proper configuration."""
    
    def __init__(self, config_path: str = "config/agents/base_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.tool_factory = ToolFactory()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration from YAML."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Agent config not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def create_agent(self, agent_name: str) -> Agent:
        """Create an agent by name with proper tools."""
        if agent_name not in self.config['agents']:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        agent_config = self.config['agents'][agent_name]
        
        # Get tools for this agent
        tools = self.tool_factory.create_tools_for_agent(agent_name)
        
        # Create agent with configuration
        agent = Agent(
            role=agent_config['role'],
            goal=agent_config['goal'],
            backstory=agent_config['backstory'],
            verbose=agent_config.get('verbose', True),
            allow_delegation=agent_config.get('allow_delegation', False),
            max_iter=agent_config.get('max_iter', 5),
            tools=tools
        )
        
        return agent
    
    def create_ui_orchestrator(self) -> Agent:
        """Create the main AUREN UI orchestrator."""
        return self.create_agent('ui_orchestrator')
    
    def create_peptide_specialist(self) -> Agent:
        """Create peptide protocol specialist."""
        return self.create_agent('peptide_specialist')
    
    def create_visual_analyst(self) -> Agent:
        """Create visual biometric analyst."""
        return self.create_agent('visual_analyst')
    
    def create_all_agents(self) -> Dict[str, Agent]:
        """Create all configured agents."""
        agents = {}
        for agent_name in self.config['agents']:
            agents[agent_name] = self.create_agent(agent_name)
        return agents


def create_auren_crew(task_config_path: str = "config/tasks/protocol_tasks.yaml") -> Crew:
    """Create the main AUREN crew with all specialists."""
    # Load task configuration
    with open(task_config_path, 'r') as f:
        task_config = yaml.safe_load(f)
    
    # Create agent factory and agents
    factory = AurenAgentFactory()
    
    orchestrator = factory.create_ui_orchestrator()
    peptide_specialist = factory.create_peptide_specialist()
    visual_analyst = factory.create_visual_analyst()
    
    # Create tasks from configuration
    routing_task = Task(
        description=task_config['tasks']['user_query_routing']['description'],
        expected_output=task_config['tasks']['user_query_routing']['expected_output'],
        agent=orchestrator
    )
    
    protocol_task = Task(
        description=task_config['tasks']['protocol_analysis']['description'],
        expected_output=task_config['tasks']['protocol_analysis']['expected_output'],
        agent=peptide_specialist  # Will be dynamically assigned based on routing
    )
    
    synthesis_task = Task(
        description=task_config['tasks']['synthesis_response']['description'],
        expected_output=task_config['tasks']['synthesis_response']['expected_output'],
        agent=orchestrator
    )
    
    # Create crew
    crew = Crew(
        agents=[orchestrator, peptide_specialist, visual_analyst],
        tasks=[routing_task, protocol_task, synthesis_task],
        process=Process.sequential,
        verbose=True,
        full_output=True
    )
    
    return crew


# Convenience function for tests
def create_test_crew() -> Crew:
    """Create a minimal crew for testing."""
    factory = AurenAgentFactory()
    orchestrator = factory.create_ui_orchestrator()
    
    test_task = Task(
        description="Test task for integration testing",
        expected_output="Test output",
        agent=orchestrator
    )
    
    return Crew(
        agents=[orchestrator],
        tasks=[test_task],
        process=Process.sequential,
        verbose=False
    )
