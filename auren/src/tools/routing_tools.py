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


class RoutingLogicTool(BaseTool):
    """
    Analyzes messages to determine which specialists should handle them.
    
    This tool embodies AUREN's ability to understand user intent and route
    messages to the appropriate living specialists who can best help.
    """
    
    name: str = "routing_logic_tool"
    description: str = """
    Analyzes user messages to determine which specialist(s) should handle them.
    Returns a routing decision with primary and secondary specialists, confidence,
    and reasoning. Considers message content, keywords, context, and urgency.
    """
    
    # Domain keyword mappings
    DOMAIN_KEYWORDS = {
        SpecialistDomain.NEUROSCIENCE: [
            "sleep", "cognitive", "brain", "focus", "memory", "ptosis", 
            "fatigue", "cns", "nervous", "mental", "clarity", "fog"
        ],
        SpecialistDomain.NUTRITION: [
            "eat", "food", "diet", "nutrition", "meal", "calorie", "macro",
            "protein", "carb", "fat", "supplement", "vitamin", "fasting"
        ],
        SpecialistDomain.FITNESS: [
            "workout", "exercise", "training", "gym", "lift", "cardio",
            "muscle", "strength", "recovery", "performance", "movement"
        ],
        SpecialistDomain.PHYSICAL_THERAPY: [
            "pain", "injury", "mobility", "flexibility", "posture",
            "rehabilitation", "movement quality", "dysfunction", "imbalance"
        ],
        SpecialistDomain.MEDICAL_ESTHETICS: [
            "skin", "appearance", "aesthetic", "inflammation", "hydration",
            "collagen", "aging", "complexion", "facial", "cosmetic"
        ]
    }
    
    def _analyze_message_content(self, message: str) -> Dict[SpecialistDomain, float]:
        """Analyze message content and return relevance scores for each domain."""
        scores = {}
        message_lower = message.lower()
        
        for domain, keywords in self.DOMAIN_KEYWORDS.items():
            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword in message_lower)
            # Calculate relevance score (0-1)
            scores[domain] = min(matches / 3.0, 1.0)  # Cap at 1.0
            
        return scores
    
    def _determine_urgency(self, message: str) -> str:
        """Determine message urgency level."""
        urgent_keywords = ["emergency", "urgent", "immediately", "asap", "critical"]
        high_keywords = ["important", "concern", "worried", "issue", "problem"]
        
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in urgent_keywords):
            return "critical"
        elif any(keyword in message_lower for keyword in high_keywords):
            return "high"
        else:
            return "normal"
    
    def _determine_collaboration_need(self, scores: Dict[SpecialistDomain, float]) -> bool:
        """Determine if multiple specialists need to collaborate."""
        # Count domains with significant relevance
        relevant_domains = sum(1 for score in scores.values() if score > 0.3)
        return relevant_domains > 1
    
    def _run(self, message: str, user_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Analyze a message and return routing decision.
        
        Args:
            message: The user's message to analyze
            user_context: Optional context about the user
            
        Returns:
            JSON string with routing decision
        """
        try:
            # Analyze message
            domain_scores = self._analyze_message_content(message)
            
            # Sort domains by relevance
            sorted_domains = sorted(
                domain_scores.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Determine primary specialist
            primary_domain, primary_score = sorted_domains[0]
            
            # If no strong match, default to general
            if primary_score < 0.2:
                primary_domain = SpecialistDomain.GENERAL
                secondary_domains = []
                confidence = 0.5
                reasoning = "No specific domain keywords detected, routing to general support."
            else:
                # Determine secondary specialists
                secondary_domains = [
                    domain for domain, score in sorted_domains[1:]
                    if score > 0.3 and score > primary_score * 0.5
                ]
                
                confidence = min(primary_score + 0.3, 0.95)
                
                # Build reasoning
                reasoning = f"Primary match with {primary_domain.value} (score: {primary_score:.2f})"
                if secondary_domains:
                    secondary_names = [d.value for d in secondary_domains]
                    reasoning += f". Secondary relevance: {', '.join(secondary_names)}"
            
            # Create routing decision
            decision = RoutingDecision(
                primary_specialist=primary_domain,
                secondary_specialists=secondary_domains,
                confidence=confidence,
                reasoning=reasoning,
                requires_collaboration=self._determine_collaboration_need(domain_scores),
                urgency_level=self._determine_urgency(message)
            )
            
            return json.dumps(asdict(decision), indent=2)
            
        except Exception as e:
            logger.error(f"Error in routing logic: {e}")
            # Fallback routing
            fallback = RoutingDecision(
                primary_specialist=SpecialistDomain.GENERAL,
                secondary_specialists=[],
                confidence=0.3,
                reasoning=f"Error in analysis: {str(e)}. Defaulting to general support.",
                requires_collaboration=False,
                urgency_level="normal"
            )
            return json.dumps(asdict(fallback), indent=2)


class DirectRoutingTool(BaseTool):
    """
    Handles explicit specialist requests like 'talk to my neuroscientist'.
    
    This tool recognizes when users want to speak with a specific specialist
    and routes the message accordingly, maintaining the metaphor of specialists
    as individual entities the user has relationships with.
    """
    
    name: str = "direct_routing_tool"
    description: str = """
    Handles direct specialist requests when users explicitly ask to talk to a
    specific specialist (e.g., 'ask my nutritionist about...', 'what does my
    neuroscientist think about...'). Returns routing decision with high confidence.
    """
    
    # Direct reference patterns
    SPECIALIST_REFERENCES = {
        SpecialistDomain.NEUROSCIENCE: [
            "neuroscientist", "brain specialist", "sleep doctor", "cognitive expert"
        ],
        SpecialistDomain.NUTRITION: [
            "nutritionist", "dietitian", "nutrition expert", "food specialist"
        ],
        SpecialistDomain.FITNESS: [
            "trainer", "fitness coach", "workout specialist", "exercise expert"
        ],
        SpecialistDomain.PHYSICAL_THERAPY: [
            "physical therapist", "pt", "movement specialist", "rehab expert"
        ],
        SpecialistDomain.MEDICAL_ESTHETICS: [
            "esthetician", "skin specialist", "aesthetic expert", "skin doctor"
        ]
    }
    
    def _extract_specialist_reference(self, message: str) -> Optional[SpecialistDomain]:
        """Extract direct specialist reference from message."""
        message_lower = message.lower()
        
        # Common patterns
        patterns = [
            "talk to my", "ask my", "what does my", "tell my",
            "connect me with my", "i want to speak with my"
        ]
        
        for domain, references in self.SPECIALIST_REFERENCES.items():
            for reference in references:
                for pattern in patterns:
                    if f"{pattern} {reference}" in message_lower:
                        return domain
                # Also check without possessive
                if reference in message_lower and any(
                    action in message_lower for action in 
                    ["talk", "ask", "speak", "connect", "consult"]
                ):
                    return domain
        
        return None
    
    def _run(self, message: str) -> str:
        """
        Check for direct specialist requests and return routing decision.
        
        Args:
            message: The user's message to analyze
            
        Returns:
            JSON string with routing decision or None if no direct request
        """
        try:
            # Check for direct specialist reference
            specialist = self._extract_specialist_reference(message)
            
            if specialist is None:
                return json.dumps({"status": "no_direct_request"})
            
            # Create high-confidence routing decision
            decision = RoutingDecision(
                primary_specialist=specialist,
                secondary_specialists=[],
                confidence=0.95,
                reasoning=f"User explicitly requested to speak with their {specialist.value}.",
                requires_collaboration=False,
                urgency_level="normal"
            )
            
            return json.dumps(asdict(decision), indent=2)
            
        except Exception as e:
            logger.error(f"Error in direct routing: {e}")
            return json.dumps({"status": "error", "message": str(e)})


class SpecialistRegistry(BaseTool):
    """
    Manages specialist registrations and availability.
    
    This tool maintains the registry of all active specialists, their capabilities,
    and availability status. It supports the vision of specialists as autonomous
    entities that can come online/offline and have varying availability.
    """
    
    name: str = "specialist_registry"
    description: str = """
    Manages the registry of available specialists, their capabilities, and
    subscription preferences. Can query specialist availability, update status,
    and find specialists by capability or keyword subscription.
    """
    
    def __init__(self, registry_path: Optional[Path] = None):
        super().__init__()
        self.registry_path = registry_path or Path("data/specialist_registry.json")
        self.registry: Dict[str, SpecialistRegistration] = {}
        self._load_registry()
    
    def _load_registry(self):
        """Load registry from persistent storage."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r') as f:
                    data = json.load(f)
                    for domain, reg_data in data.items():
                        self.registry[domain] = SpecialistRegistration(
                            domain=SpecialistDomain(reg_data['domain']),
                            identity=reg_data['identity'],
                            capabilities=reg_data['capabilities'],
                            subscription_keywords=reg_data['subscription_keywords'],
                            collaboration_preferences=reg_data['collaboration_preferences'],
                            availability_status=reg_data.get('availability_status', 'available')
                        )
            except Exception as e:
                logger.error(f"Error loading registry: {e}")
    
    def _save_registry(self):
        """Save registry to persistent storage."""
        try:
            self.registry_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                domain: asdict(registration)
                for domain, registration in self.registry.items()
            }
            with open(self.registry_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving registry: {e}")
    
    def register_specialist(self, registration: SpecialistRegistration):
        """Register a new specialist or update existing."""
        self.registry[registration.domain.value] = registration
        self._save_registry()
    
    def get_specialist(self, domain: SpecialistDomain) -> Optional[SpecialistRegistration]:
        """Get specialist registration by domain."""
        return self.registry.get(domain.value)
    
    def find_by_keyword(self, message: str) -> List[SpecialistRegistration]:
        """Find all specialists subscribed to keywords in the message."""
        matches = []
        for registration in self.registry.values():
            if registration.matches_keywords(message):
                matches.append(registration)
        return matches
    
    def get_available_specialists(self) -> List[SpecialistRegistration]:
        """Get all available specialists."""
        return [
            reg for reg in self.registry.values()
            if reg.availability_status == "available"
        ]
    
    def update_availability(self, domain: SpecialistDomain, status: str):
        """Update specialist availability status."""
        if domain.value in self.registry:
            self.registry[domain.value].availability_status = status
            self._save_registry()
    
    def _run(self, action: str, domain: Optional[str] = None, **kwargs) -> str:
        """
        Execute registry operations.
        
        Args:
            action: The action to perform (query, update, find)
            domain: The specialist domain (if applicable)
            **kwargs: Additional parameters for the action
            
        Returns:
            JSON string with operation result
        """
        try:
            if action == "query":
                if domain:
                    specialist = self.get_specialist(SpecialistDomain(domain))
                    if specialist:
                        return json.dumps(asdict(specialist), indent=2)
                    else:
                        return json.dumps({"status": "not_found"})
                else:
                    # Return all available
                    available = self.get_available_specialists()
                    return json.dumps([asdict(s) for s in available], indent=2)
            
            elif action == "update_availability":
                if domain and "status" in kwargs:
                    self.update_availability(SpecialistDomain(domain), kwargs["status"])
                    return json.dumps({"status": "updated"})
                else:
                    return json.dumps({"error": "Missing domain or status"})
            
            elif action == "find_by_keyword":
                if "message" in kwargs:
                    matches = self.find_by_keyword(kwargs["message"])
                    return json.dumps([asdict(m) for m in matches], indent=2)
                else:
                    return json.dumps({"error": "Missing message"})
            
            else:
                return json.dumps({"error": f"Unknown action: {action}"})
                
        except Exception as e:
            logger.error(f"Registry error: {e}")
            return json.dumps({"error": str(e)})


class PacketBuilder(BaseTool):
    """
    Builds context packets for specialist handoff.
    
    This tool prepares comprehensive context packages that enable specialists
    to understand the full situation and collaborate effectively. It embodies
    the principle that specialists need rich context to provide personalized,
    valuable insights.
    """
    
    name: str = "packet_builder"
    description: str = """
    Builds comprehensive context packets for specialist handoff. Includes the
    original message, routing decision, user context, relevant history, and
    collaboration requests. Ensures specialists have everything they need.
    """
    
    def __init__(self, history_limit: int = 10):
        super().__init__()
        self.history_limit = history_limit
    
    def _extract_relevant_history(
        self,
        user_id: str,
        domain: SpecialistDomain,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """Extract relevant historical data for the specialist."""
        # In production, this would query the temporal memory system
        # For now, return a placeholder
        return [
            {
                "type": "placeholder",
                "message": "Historical data extraction will connect to temporal memory",
                "domain": domain.value,
                "user_id": user_id,
                "days_back": days_back
            }
        ]
    
    def _identify_collaboration_needs(
        self,
        routing_decision: RoutingDecision
    ) -> List[str]:
        """Identify specific collaboration requests based on routing."""
        requests = []
        
        if routing_decision.requires_collaboration:
            # Generate specific collaboration requests
            primary = routing_decision.primary_specialist.value
            
            for secondary in routing_decision.secondary_specialists:
                requests.append(
                    f"Request input from {secondary.value} specialist on "
                    f"aspects related to their domain"
                )
            
            if routing_decision.urgency_level in ["high", "critical"]:
                requests.append("Prioritize rapid consensus building due to urgency")
        
        return requests
    
    def _run(
        self,
        message: str,
        routing_decision: Dict[str, Any],
        user_context: Dict[str, Any]
    ) -> str:
        """
        Build a context packet for specialist handoff.
        
        Args:
            message: The original user message
            routing_decision: The routing decision (as dict)
            user_context: Current user context
            
        Returns:
            JSON string with complete context packet
        """
        try:
            # Reconstruct routing decision
            decision = RoutingDecision(
                primary_specialist=SpecialistDomain(routing_decision['primary_specialist']),
                secondary_specialists=[
                    SpecialistDomain(s) for s in routing_decision.get('secondary_specialists', [])
                ],
                confidence=routing_decision['confidence'],
                reasoning=routing_decision['reasoning'],
                requires_collaboration=routing_decision['requires_collaboration'],
                urgency_level=routing_decision.get('urgency_level', 'normal')
            )
            
            # Extract relevant history
            history = self._extract_relevant_history(
                user_id=user_context.get('user_id', 'unknown'),
                domain=decision.primary_specialist
            )
            
            # Identify collaboration needs
            collaboration_requests = self._identify_collaboration_needs(decision)
            
            # Build packet
            packet = ContextPacket(
                message_id=f"msg_{datetime.now().timestamp()}",
                original_message=message,
                routing_decision=decision,
                user_context=user_context,
                relevant_history=history,
                collaboration_requests=collaboration_requests,
                timestamp=datetime.now()
            )
            
            return json.dumps(packet.to_dict(), indent=2)
            
        except Exception as e:
            logger.error(f"Error building packet: {e}")
            return json.dumps({"error": str(e)})


# Tool factory functions for CrewAI integration
def create_routing_logic_tool() -> RoutingLogicTool:
    """Create a routing logic tool instance."""
    return RoutingLogicTool()

def create_direct_routing_tool() -> DirectRoutingTool:
    """Create a direct routing tool instance."""
    return DirectRoutingTool()

def create_specialist_registry(registry_path: Optional[Path] = None) -> SpecialistRegistry:
    """Create a specialist registry instance."""
    return SpecialistRegistry(registry_path)

def create_packet_builder(history_limit: int = 10) -> PacketBuilder:
    """Create a packet builder instance."""
    return PacketBuilder(history_limit)


# Example usage and testing
if __name__ == "__main__":
    # Test routing logic
    routing_tool = create_routing_logic_tool()
    
    test_messages = [
        "I've been having trouble sleeping and feel cognitively foggy",
        "What should I eat before my workout?",
        "Talk to my neuroscientist about my sleep issues",
        "My knee hurts during squats",
        "How can I improve my skin's appearance?"
    ]
    
    print("Testing Routing Logic Tool:")
    print("-" * 50)
    for msg in test_messages:
        result = routing_tool._run(msg)
        decision = json.loads(result)
        print(f"Message: {msg}")
        print(f"Primary: {decision['primary_specialist']}")
        print(f"Confidence: {decision['confidence']:.2f}")
        print(f"Reasoning: {decision['reasoning']}")
        print("-" * 50)
    
    # Test direct routing
    direct_tool = create_direct_routing_tool()
    
    print("\nTesting Direct Routing Tool:")
    print("-" * 50)
    direct_messages = [
        "I want to talk to my nutritionist about my macros",
        "Ask my trainer about recovery",
        "What's the weather like?",  # No direct request
    ]
    
    for msg in direct_messages:
        result = direct_tool._run(msg)
        print(f"Message: {msg}")
        print(f"Result: {result}")
        print("-" * 50)
