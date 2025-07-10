import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from crewai import Agent, Task


class AURENAgent:
    """Simplified AUREN implementation using only core CrewAI"""

    def __init__(self, tenant_id: str = "default"):
        self.tenant_id = tenant_id
        self.conversation_history = []

        # Create agent with basic configuration
        self.agent = Agent(
            role="AUREN - Adaptive User Relationship Engine",
            goal="Build meaningful relationships while orchestrating AI workflows",
            backstory="""You are AUREN, a sophisticated AI interface designed to understand 
            and adapt to each user's unique communication style and needs.""",
            verbose=True,
            memory=True,
            max_iter=5,  # Reduced for cost control
        )

    def process_message(self, message: str, phone_number: str) -> Dict:
        """Process incoming message with basic functionality"""
        # Simple in-memory context storage
        self.conversation_history.append(
            {"phone": phone_number, "message": message, "timestamp": str(datetime.now())}
        )

        # Create a task for the agent
        task = Task(
            description=f"Process user message: {message}",
            expected_output="A helpful, concise response to the user's message.",
            agent=self.agent,
        )

        # Process with agent using the task
        response = self.agent.execute_task(task)

        # Store response
        self.conversation_history.append(
            {"phone": phone_number, "response": response, "timestamp": str(datetime.now())}
        )

        return {"response": response, "tenant_id": self.tenant_id}
