"""Protocol-specific tools for AUREN agents."""

from typing import Dict, Any, List, Optional
from langchain.tools import Tool
from langchain_core.pydantic_v1 import BaseModel, Field
from pydantic import BaseModel, Field

from src.protocols.journal.journal_protocol import JournalProtocol
from src.protocols.mirage.mirage_protocol import MIRAGEProtocol
from src.protocols.visor.visor_protocol import VISORProtocol
from src.biometric.analyzers.facial_analyzer import FacialAnalyzer


class JournalProtocolToolInput(BaseModel):
    """Input for JournalProtocolTool"""
    query: str = Field(description="Input query")

def journalprotocoltool_func(query: str) -> str:
    """JournalProtocolTool tool"""
    pass

journalprotocoltool_tool = Tool(
    name="JournalProtocolTool",
    func=journalprotocoltool_func,
    description="""JournalProtocolTool tool""",
    args_schema=JournalProtocolToolInput
)class MirageProtocolToolInput(BaseModel):
    """Input for MirageProtocolTool"""
    query: str = Field(description="Input query")

def mirageprotocoltool_func(query: str) -> str:
    """MirageProtocolTool tool"""
    pass

mirageprotocoltool_tool = Tool(
    name="MirageProtocolTool",
    func=mirageprotocoltool_func,
    description="""MirageProtocolTool tool""",
    args_schema=MirageProtocolToolInput
)class VisorProtocolToolInput(BaseModel):
    """Input for VisorProtocolTool"""
    query: str = Field(description="Input query")

def visorprotocoltool_func(query: str) -> str:
    """VisorProtocolTool tool"""
    pass

visorprotocoltool_tool = Tool(
    name="VisorProtocolTool",
    func=visorprotocoltool_func,
    description="""VisorProtocolTool tool""",
    args_schema=VisorProtocolToolInput
)class BiometricAnalysisToolInput(BaseModel):
    """Input for BiometricAnalysisTool"""
    query: str = Field(description="Input query")

def biometricanalysistool_func(query: str) -> str:
    """BiometricAnalysisTool tool"""
    pass

biometricanalysistool_tool = Tool(
    name="BiometricAnalysisTool",
    func=biometricanalysistool_func,
    description="""BiometricAnalysisTool tool""",
    args_schema=BiometricAnalysisToolInput
)class ToolFactory:
    """Factory for creating tool instances."""
    
    @staticmethod
    def create_all_tools() -> Dict[str, BaseTool]:
        """Create all available tools."""
        return {
            "journal_protocol_tool": JournalProtocolTool(),
            "mirage_protocol_tool": MirageProtocolTool(),
            "visor_protocol_tool": VisorProtocolTool(),
            "biometric_analysis_tool": BiometricAnalysisTool(),
        }
    
    @staticmethod
    def create_tools_for_agent(agent_role: str) -> List[BaseTool]:
        """Create tools appropriate for a specific agent role."""
        tool_mapping = {
            "peptide_specialist": [
                JournalProtocolTool(),
            ],
            "visual_analyst": [
                MirageProtocolTool(),
                VisorProtocolTool(),
                BiometricAnalysisTool(),
            ],
            "ui_orchestrator": [
                # Orchestrator can access all protocols for routing
                JournalProtocolTool(),
                MirageProtocolTool(),
                VisorProtocolTool(),
            ]
        }
        
        return tool_mapping.get(agent_role, []) 