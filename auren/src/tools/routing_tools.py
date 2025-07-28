"""
AUREN Routing Tools - The specialist communication and collaboration system.

This module implements the routing infrastructure that enables AUREN to analyze
messages, route them to appropriate specialists, and facilitate collaboration
between autonomous AI colleagues. These tools embody the vision of specialists
as living entities who actively collaborate to optimize the user's health.

Key Components:
1. RoutingLogicTool - Analyzes messages for specialist relevance
2. DirectRoutingTool - Handles explicit "talk to my neuroscientist" requests
3. SpecialistRegistry - Configuration and subscription management
4. PacketBuilder - Context preparation for specialist handoff
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
import asyncio

from crewai.tools.agent_tools import StructuredTool as BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class SpecialistDomain(Enum):
    """Domains of expertise for routing decisions."""
    NEUROSCIENCE = "neuroscience"
    NUTRITION = "nutrition"
    FITNESS = "fitness"
    PHYSICAL_THERAPY = "physical_therapy"
    MEDICAL_ESTHETICS = "medical_esthetics"
    GENERAL = "general"


class MessageRelevance(Enum):
    """How relevant a message is to a specialist."""
    PRIMARY = "primary"      # This specialist should lead
    SECONDARY = "secondary"  # This specialist should contribute
    TERTIARY = "tertiary"   # This specialist might have insights
    NONE = "none"           # Not relevant to this specialist


@dataclass
class RoutingDecision:
    """Represents a routing decision for a message."""
    primary_specialist: SpecialistDomain
    secondary_specialists: List[SpecialistDomain]
    confidence: float
    reasoning: str
    requires_collaboration: bool
    urgency_level: str = "normal"  # low, normal, high, critical


@dataclass
class SpecialistRegistration:
    """Registration info for a specialist in the system."""
    domain: SpecialistDomain
    identity: str
    capabilities: List[str]
    subscription_keywords: List[str]
    collaboration_preferences: Dict[str, Any]
    availability_status: str = "available"  # available, busy, offline
    
    def matches_keywords(self, message: str) -> bool:
        """Check if message contains any subscription keywords."""
        message_lower = message.lower()
        return any(keyword.lower() in message_lower for keyword in self.subscription_keywords)


@dataclass
class ContextPacket:
    """Context package prepared for specialist handoff."""
    message_id: str
    original_message: str
    routing_decision: RoutingDecision
    user_context: Dict[str, Any]
    relevant_history: List[Dict[str, Any]]
    collaboration_requests: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for transmission."""
        return {
            "message_id": self.message_id,
            "original_message": self.original_message,
            "routing_decision": asdict(self.routing_decision),
            "user_context": self.user_context,
            "relevant_history": self.relevant_history,
            "collaboration_requests": self.collaboration_requests,
            "timestamp": self.timestamp.isoformat()
        }


class RoutingLogicToolInput(BaseModel):
    """Input for RoutingLogicTool"""
    query: str = Field(description="Input query")

def routinglogictool_func(query: str) -> str:
    """RoutingLogicTool tool"""
    pass

routinglogictool_tool = Tool(
    name="RoutingLogicTool",
    func=routinglogictool_func,
    description="""RoutingLogicTool tool""",
    args_schema=RoutingLogicToolInput
)class DirectRoutingToolInput(BaseModel):
    """Input for DirectRoutingTool"""
    query: str = Field(description="Input query")

def directroutingtool_func(query: str) -> str:
    """DirectRoutingTool tool"""
    pass

directroutingtool_tool = Tool(
    name="DirectRoutingTool",
    func=directroutingtool_func,
    description="""DirectRoutingTool tool""",
    args_schema=DirectRoutingToolInput
)class SpecialistRegistryInput(BaseModel):
    """Input for SpecialistRegistry"""
    query: str = Field(description="Input query")

def specialistregistry_func(query: str) -> str:
    """SpecialistRegistry tool"""
    pass

specialistregistry_tool = Tool(
    name="SpecialistRegistry",
    func=specialistregistry_func,
    description="""SpecialistRegistry tool""",
    args_schema=SpecialistRegistryInput
)class PacketBuilderInput(BaseModel):
    """Input for PacketBuilder"""
    query: str = Field(description="Input query")

def packetbuilder_func(query: str) -> str:
    """PacketBuilder tool"""
    pass

packetbuilder_tool = Tool(
    name="PacketBuilder",
    func=packetbuilder_func,
    description="""PacketBuilder tool""",
    args_schema=PacketBuilderInput
)