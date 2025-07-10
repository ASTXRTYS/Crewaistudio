from crewai import Agent
from auren.tools.IntentClassifierTool import IntentClassifierTool
from auren.tools.WhatsAppWebhookTool import WhatsAppWebhookTool
import logging
import os

logger = logging.getLogger(__name__)

class WhatsAppMessageHandler:
    def __init__(self):
        self.intent_classifier = IntentClassifierTool()
        self.whatsapp_tool = WhatsAppWebhookTool()
        self.router_agent = None
        self.response_agent = None
        self.specialist_agents = {}
    
    def create_router_agent(self):
        """Create the router agent for intent classification"""
        self.router_agent = Agent(
            role="Message Router",
            goal="Analyze incoming messages and classify user intent",
            backstory="You are an expert at understanding user messages and routing them to the appropriate specialist agent.",
            tools=[self.intent_classifier],
            verbose=True,
            allow_delegation=True
        )
        return self.router_agent
    
    def create_specialist_agents(self):
        """Create specialist agents for different intents"""
        self.specialist_agents = {
            'nutrition': Agent(
                role="Nutrition Specialist",
                goal="Provide expert nutrition advice and meal planning",
                backstory="You are a certified nutritionist with expertise in healthy eating and meal planning.",
                verbose=True
            ),
            'scheduling': Agent(
                role="Scheduling Specialist", 
                goal="Help users schedule appointments and manage their calendar",
                backstory="You are an expert at scheduling and calendar management.",
                verbose=True
            ),
            'onboarding': Agent(
                role="Onboarding Specialist",
                goal="Welcome new users and guide them through the platform",
                backstory="You are friendly and helpful, specializing in welcoming new users.",
                verbose=True
            ),
            'general': Agent(
                role="General Support",
                goal="Provide helpful responses to general questions",
                backstory="You are knowledgeable and helpful, able to answer a wide range of questions.",
                verbose=True
            )
        }
        return self.specialist_agents
    
    def classify_intent(self, message: str) -> str:
        """Classify the intent of a user message"""
        try:
            # Use the intent classifier tool
            result = self.intent_classifier.run(message)
            logger.info(f"Classified intent: {result}")
            return result
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return "general"
    
    def route_message(self, message: str, user_id: str):
        """Route a message to the appropriate specialist agent"""
        try:
            # Classify the intent
            intent = self.classify_intent(message)
            
            # Get the appropriate specialist agent
            specialist = self.specialist_agents.get(intent, self.specialist_agents['general'])
            
            # Create a simple task for the specialist
            from crewai import Task
            task = Task(
                description=f"User message: {message}\nUser ID: {user_id}\nPlease provide a helpful response.",
                agent=specialist,
                expected_output="A helpful response to the user's message"
            )
            
            # Execute the task
            response = specialist.execute_task(task)
            
            logger.info(f"Routed message to {intent} specialist for user {user_id}")
            return response
            
        except Exception as e:
            logger.error(f"Error routing message: {e}")
            return "I apologize, but I'm having trouble processing your message right now. Please try again later." 