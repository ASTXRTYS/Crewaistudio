"""Protocol-specific tools for AUREN agents."""

from typing import Dict, Any, List, Optional
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.protocols.journal.journal_protocol import JournalProtocol
from src.protocols.mirage.mirage_protocol import MIRAGEProtocol
from src.protocols.visor.visor_protocol import VISORProtocol
from src.biometric.analyzers.facial_analyzer import FacialAnalyzer


class JournalProtocolTool(BaseTool):
    """Tool for accessing Journal protocol data."""
    
    name: str = "journal_protocol_tool"
    description: str = """Access and analyze peptide tracking data from the Journal protocol.
    Use this to get information about peptide doses, weight changes, side effects, and adherence."""
    
    protocol: JournalProtocol = Field(default_factory=JournalProtocol)
    
    def _run(self, query: str) -> str:
        """Execute journal protocol query."""
        try:
            # Parse query to determine what data is needed
            if "current dose" in query.lower():
                data = self.protocol.get_current_dose()
                return f"Current Retatrutide dose: {data['dose']}mg, Last administered: {data['date']}"
            
            elif "weight" in query.lower():
                data = self.protocol.get_weight_trend()
                return f"Weight trend: {data['current']}lbs (Change: {data['change']}lbs over {data['period']})"
            
            elif "side effects" in query.lower():
                effects = self.protocol.get_side_effects()
                return f"Recent side effects: {', '.join(effects) if effects else 'None reported'}"
            
            else:
                # General query - return recent summary
                summary = self.protocol.get_recent_summary()
                return f"Journal Summary: {summary}"
                
        except Exception as e:
            return f"Error accessing Journal protocol: {str(e)}"


class MirageProtocolTool(BaseTool):
    """Tool for accessing MIRAGE visual biometric data."""
    
    name: str = "mirage_protocol_tool"
    description: str = """Access and analyze facial biometric data from the MIRAGE protocol.
    Use this to get information about ptosis scores, inflammation, symmetry, and visual trends."""
    
    protocol: MIRAGEProtocol = Field(default_factory=MIRAGEProtocol)
    
    def _run(self, query: str) -> str:
        """Execute MIRAGE protocol query."""
        try:
            if "ptosis" in query.lower():
                scores = self.protocol.get_latest_scores()
                return f"Ptosis score: {scores.ptosis_score}/10 (Left eye: {scores.left_ptosis}, Right eye: {scores.right_ptosis})"
            
            elif "inflammation" in query.lower():
                scores = self.protocol.get_latest_scores()
                return f"Inflammation score: {scores.inflammation_score}/10"
            
            elif "symmetry" in query.lower():
                scores = self.protocol.get_latest_scores()
                return f"Facial symmetry score: {scores.symmetry_score}/10"
            
            else:
                # Return comprehensive biometric summary
                summary = self.protocol.get_biometric_summary()
                return f"MIRAGE Summary: {summary}"
                
        except Exception as e:
            return f"Error accessing MIRAGE protocol: {str(e)}"


class VisorProtocolTool(BaseTool):
    """Tool for accessing VISOR media registry."""
    
    name: str = "visor_protocol_tool"
    description: str = """Access the VISOR media registry for visual documentation.
    Use this to check media compliance, retrieve MIRIS tags, and track visual progression."""
    
    protocol: VISORProtocol = Field(default_factory=VISORProtocol)
    
    def _run(self, query: str) -> str:
        """Execute VISOR protocol query."""
        try:
            if "compliance" in query.lower():
                compliance = self.protocol.check_daily_compliance()
                return f"Photo compliance: {compliance['percentage']}% ({compliance['days_compliant']}/{compliance['total_days']} days)"
            
            elif "latest" in query.lower():
                latest = self.protocol.get_latest_entry()
                return f"Latest entry: {latest['miris_tag']} - {latest['timestamp']}"
            
            else:
                catalog = self.protocol.generate_catalog_summary()
                return f"VISOR Catalog: {catalog}"
                
        except Exception as e:
            return f"Error accessing VISOR protocol: {str(e)}"


class BiometricAnalysisTool(BaseTool):
    """Tool for performing real-time biometric analysis."""
    
    name: str = "biometric_analysis_tool"
    description: str = """Analyze uploaded images for biometric markers.
    This tool processes facial images to extract ptosis, inflammation, and symmetry scores."""
    
    analyzer: FacialAnalyzer = Field(default_factory=FacialAnalyzer)
    
    def _run(self, image_path: str) -> str:
        """Analyze image for biometrics."""
        try:
            scores = self.analyzer.analyze(image_path)
            
            result = f"""Biometric Analysis Results:
- Ptosis Score: {scores.ptosis_score:.1f}/10
- Inflammation: {scores.inflammation_score:.1f}/10
- Symmetry: {scores.symmetry_score:.1f}/10
- Lymphatic Fullness: {scores.lymphatic_fullness:.1f}/10
- Skin Clarity: {scores.skin_clarity:.1f}/10

Alerts: {self._check_alerts(scores)}"""
            
            return result
            
        except Exception as e:
            return f"Error analyzing image: {str(e)}"
    
    def _check_alerts(self, scores) -> str:
        """Check for biometric alerts."""
        alerts = []
        
        if scores.ptosis_score >= 7.0:
            alerts.append("CRITICAL: Ptosis score exceeds threshold")
        elif scores.ptosis_score >= 6.5:
            alerts.append("WARNING: Ptosis score approaching critical")
            
        if scores.inflammation_score >= 7.0:
            alerts.append("HIGH: Inflammation detected")
            
        return ", ".join(alerts) if alerts else "None"


# Tool Factory for easy instantiation
class ToolFactory:
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