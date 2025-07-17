"""
AUREN Tools Package - Routing and specialist communication tools.

This package provides the routing infrastructure that enables AUREN to:
- Analyze messages and route them to appropriate specialists
- Handle direct specialist requests
- Manage specialist configurations and availability
- Build comprehensive context packets for specialist handoff
"""

from .routing_tools import (
    create_routing_logic_tool,
    create_direct_routing_tool,
    create_specialist_registry,
    create_packet_builder,
    RoutingLogicTool,
    DirectRoutingTool,
    SpecialistRegistry,
    PacketBuilder,
    SpecialistDomain,
    RoutingDecision,
    ContextPacket,
    SpecialistRegistration
)

__all__ = [
    # Factory functions for CrewAI integration
    'create_routing_logic_tool',
    'create_direct_routing_tool',
    'create_specialist_registry',
    'create_packet_builder',
    
    # Tool classes
    'RoutingLogicTool',
    'DirectRoutingTool',
    'SpecialistRegistry',
    'PacketBuilder',
    
    # Data structures
    'SpecialistDomain',
    'RoutingDecision',
    'ContextPacket',
    'SpecialistRegistration'
]
