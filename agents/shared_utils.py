"""
Shared utilities for AUREN agent system.
Contains reusable functions for configuration merging, validation, and common operations.
"""
from typing import Dict, Any


def deep_merge(a: dict, b: dict) -> dict:
    """
    Recursive deep merge for YAML configurations.
    Follows Stack Overflow community recommendations for hierarchical config merging.
    
    Args:
        a: Base dictionary to merge into
        b: Dictionary to merge from
        
    Returns:
        Merged dictionary with b's values taking precedence
        
    Examples:
        >>> a = {"config": {"temp": 0.1, "tools": {"tool1": "enabled"}}}
        >>> b = {"config": {"temp": 0.3, "tools": {"tool2": "enabled"}}}
        >>> result = deep_merge(a, b)
        >>> result["config"]["temp"]  # 0.3 (overwritten)
        >>> result["config"]["tools"]  # {"tool1": "enabled", "tool2": "enabled"}
    """
    for k, v in b.items():
        if k in a and isinstance(a[k], dict) and isinstance(v, dict):
            deep_merge(a[k], v)
        else:
            a[k] = v
    return a


def validate_kafka_topic_name(topic: str) -> bool:
    """
    Validate Kafka topic name follows Confluent naming conventions.
    
    Args:
        topic: Topic name to validate
        
    Returns:
        True if valid, False otherwise
        
    Rules:
        - Must match pattern: {agent}.{domain}.{verb}
        - Use underscores for multi-word names
        - Lowercase only
        - No special characters except dots and underscores
    """
    import re
    pattern = r'^[a-z_]+\.[a-z_]+\.[a-z_]+$'
    return bool(re.match(pattern, topic))


def generate_kafka_topics(agent_role: str, domain: str = "biometric") -> Dict[str, str]:
    """
    Generate Confluent-style Kafka topic names for an agent.
    
    Args:
        agent_role: Agent role (e.g., "NEUROS CNS Specialist")
        domain: Domain category (default: "biometric")
        
    Returns:
        Dictionary with ingest, output, and status topic names
        
    Examples:
        >>> topics = generate_kafka_topics("NEUROS & HRV Specialist", "testing")
        >>> topics["ingest"]  # "neuros_and_hrv_specialist.testing.analyze"
    """
    agent_name = agent_role.lower().replace(' ', '_').replace('&', 'and')
    
    return {
        'ingest': f"{agent_name}.{domain}.analyze",
        'output': f"{agent_name}.recommendation.publish", 
        'status': f"{agent_name}.status.update"
    } 