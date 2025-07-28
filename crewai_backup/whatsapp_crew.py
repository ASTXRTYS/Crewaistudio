from crewai import Crew
from auren.agents.whatsapp_message_handler import WhatsAppMessageHandler
from auren.repositories import Database, AgentRepository, TaskRepository, CrewRepository
import logging

logger = logging.getLogger(__name__)

class WhatsAppCrew:
    def __init__(self):
        self.db = Database()
        self.agent_repo = AgentRepository(self.db)
        self.task_repo = TaskRepository(self.db)
        self.crew_repo = CrewRepository(self.db)
        self.handler = WhatsAppMessageHandler()
    
    def create_crew(self, user_id: str, message: str):
        """Create a crew for handling WhatsApp messages"""
        try:
            # Create router agent for intent classification
            router_agent = self.handler.create_router_agent()
            
            # Create specialist agents
            specialist_agents = self.handler.create_specialist_agents()
            
            # Create tasks
            tasks = self._create_tasks(user_id, message)
            
            # Create and return crew
            crew = Crew(
                agents=[router_agent] + list(specialist_agents.values()),
                tasks=tasks,
                verbose=True
            )
            
            logger.info(f"Created WhatsApp crew for user {user_id}")
            return crew
            
        except Exception as e:
            logger.error(f"Error creating WhatsApp crew: {e}")
            raise
    
    def _create_tasks(self, user_id: str, message: str):
        """Create tasks for the crew based on the message"""
        from crewai import Task
        
        tasks = [
            Task(
                description=f"Analyze the user message and classify intent: {message}",
                agent=self.handler.router_agent,
                expected_output="Intent classification and routing decision"
            ),
            Task(
                description="Generate appropriate response based on classified intent",
                agent=self.handler.response_agent,
                expected_output="Natural, helpful response to user message"
            )
        ]
        
        return tasks
    
    def process_message(self, user_id: str, message: str):
        """Process a WhatsApp message through the crew"""
        try:
            # Create crew for this message
            crew = self.create_crew(user_id, message)
            
            # Execute crew
            result = crew.kickoff()
            
            # Convert CrewOutput to string
            response_text = str(result) if result else "No response generated"
            
            # Log the interaction
            self._log_interaction(user_id, message, response_text)
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I apologize, but I'm having trouble processing your message right now. Please try again later."
    
    def _log_interaction(self, user_id: str, message: str, response: str):
        """Log the interaction for analytics"""
        interaction = {
            "user_id": user_id,
            "message": message,
            "response": response,
            "timestamp": "now()"  # Will be handled by database
        }
        
        # Save to database (implement based on your schema)
        logger.info(f"Logged interaction for user {user_id}") 