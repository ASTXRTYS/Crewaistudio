"""AUREN 2.0 - Main Application Entry Point"""
import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .agents.biometric_aware_agents import ProtocolAwareCrew
from .biometric.alerts.alert_manager import AlertManager
from .biometric.analyzers.facial_analyzer import BiometricAnalyzer
from .biometric.correlators.convergence_analyzer import ConvergenceAnalyzer
from .integrations.biometric_whatsapp import BiometricWhatsAppConnector
# Import our core components
from .protocols.journal.journal_protocol import JournalProtocol
from .protocols.mirage.mirage_protocol import MIRAGEProtocol
from .protocols.visor.visor_protocol import VISORProtocol
from .rag.agentic_rag import AgenticRAG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("logs/system/auren.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


class AUREN2App:
    """Main AUREN 2.0 application"""

    def __init__(self):
        self.app = FastAPI(
            title="AUREN 2.0 - Biometric Optimization System",
            description="Advanced AI system for biometric optimization and protocol management",
            version="2.0.0",
        )

        # Initialize core components
        self.protocols = {
            "journal": JournalProtocol(),
            "mirage": MIRAGEProtocol(),
            "visor": VISORProtocol(),
        }

        self.analyzer = BiometricAnalyzer()
        self.convergence = ConvergenceAnalyzer()
        self.alert_manager = AlertManager()
        self.crew = ProtocolAwareCrew()
        self.rag = AgenticRAG()

        # Initialize WhatsApp connector if credentials available
        try:
            self.whatsapp = BiometricWhatsAppConnector()
            self.whatsapp_available = True
        except ValueError as e:
            logger.warning(f"WhatsApp not available: {e}")
            self.whatsapp_available = False

        # Setup routes
        self._setup_routes()

    def _setup_routes(self):
        """Setup FastAPI routes"""

        @self.app.get("/")
        async def root():
            return {
                "message": "AUREN 2.0 - Biometric Optimization System",
                "version": "2.0.0",
                "status": "operational",
                "timestamp": datetime.now().isoformat(),
            }

        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "components": {
                    "protocols": "operational",
                    "analyzer": "operational",
                    "crew": "operational",
                    "rag": "operational",
                    "whatsapp": "operational" if self.whatsapp_available else "unavailable",
                },
                "timestamp": datetime.now().isoformat(),
            }

        @self.app.post("/api/protocols/{protocol}/entry")
        async def create_protocol_entry(protocol: str, data: Dict[str, Any]):
            """Create entry in specified protocol"""

            if protocol not in self.protocols:
                raise HTTPException(status_code=400, detail=f"Unknown protocol: {protocol}")

            try:
                entry = self.protocols[protocol].create_entry(data)
                return {"status": "success", "entry": entry, "protocol": protocol}
            except Exception as e:
                logger.error(f"Failed to create {protocol} entry: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/biometric/analyze")
        async def analyze_biometric(data: Dict[str, Any]):
            """Analyze biometric data"""

            try:
                image_path = data.get("image_path")
                if not image_path:
                    raise HTTPException(status_code=400, detail="image_path required")

                result = self.analyzer.analyze_image(image_path)

                # Check for alerts
                alerts = self.alert_manager.check_scores(result["scores"])

                return {
                    "status": "success",
                    "analysis": result,
                    "alerts": [alert.to_dict() for alert in alerts],
                }
            except Exception as e:
                logger.error(f"Biometric analysis failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/convergence/analyze")
        async def analyze_convergence(data: Dict[str, Any]):
            """Perform convergence analysis"""

            try:
                # Add data to convergence analyzer
                source = data.get("source", "unknown")
                self.convergence.add_data(source, data)

                # Perform analysis
                peptide_visual = self.convergence.analyze_peptide_visual_correlation()
                lifestyle = self.convergence.analyze_lifestyle_impact()

                return {
                    "status": "success",
                    "peptide_visual_correlation": peptide_visual,
                    "lifestyle_impact": lifestyle,
                }
            except Exception as e:
                logger.error(f"Convergence analysis failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/crew/process")
        async def process_with_crew(data: Dict[str, Any]):
            """Process data through the agent crew"""

            try:
                result = await self.crew.process_daily_update(data)
                return {"status": "success", "crew_analysis": result}
            except Exception as e:
                logger.error(f"Crew processing failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/rag/query")
        async def query_rag(data: Dict[str, Any]):
            """Query the RAG system"""

            try:
                query = data.get("query")
                user_context = data.get("context", {})
                urgency = data.get("urgency", "normal")

                if not query:
                    raise HTTPException(status_code=400, detail="query required")

                result = await self.rag.retrieve_with_context(query, user_context, urgency)

                return {"status": "success", "query": query, "results": result}
            except Exception as e:
                logger.error(f"RAG query failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/whatsapp/webhook")
        async def whatsapp_webhook(request: Request):
            """Handle WhatsApp webhook"""

            if not self.whatsapp_available:
                raise HTTPException(status_code=503, detail="WhatsApp not configured")

            try:
                body = await request.json()

                # Verify webhook (simplified)
                if body.get("object") != "whatsapp_business_account":
                    raise HTTPException(status_code=400, detail="Invalid webhook object")

                # Extract message data
                message_data = self.whatsapp.extract_message_data(body)
                if not message_data:
                    return JSONResponse(content={"status": "no_message"})

                # Process based on intent
                response = await self._process_whatsapp_message(message_data)

                # Send response
                if response:
                    await self.whatsapp.send_message(message_data["from"], response)

                return JSONResponse(content={"status": "processed"})

            except Exception as e:
                logger.error(f"WhatsApp webhook failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/whatsapp/send")
        async def send_whatsapp_message(data: Dict[str, Any]):
            """Send WhatsApp message"""

            if not self.whatsapp_available:
                raise HTTPException(status_code=503, detail="WhatsApp not configured")

            try:
                to_number = data.get("to")
                message = data.get("message")
                message_type = data.get("type", "text")

                if not to_number or not message:
                    raise HTTPException(status_code=400, detail="to and message required")

                result = await self.whatsapp.send_message(to_number, message)

                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"WhatsApp send failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def _process_whatsapp_message(self, message_data: Dict) -> Optional[str]:
        """Process incoming WhatsApp message"""

        intent = message_data.get("intent", "unknown")
        text = message_data.get("text", "")

        logger.info(f"Processing WhatsApp message: {intent} - {text}")

        if intent == "biometric_photo":
            # Handle photo upload
            return "📸 Photo received! Analyzing your biometrics..."

        elif intent == "weight_log":
            # Handle weight logging
            return "⚖️ Weight logged successfully. Keep up the consistency!"

        elif intent == "peptide_log":
            # Handle peptide logging
            return "💉 Peptide dose logged. Tracking your protocol progress..."

        elif intent == "nutrition_log":
            # Handle nutrition logging
            return "🍽️ Nutrition logged. Monitoring your macro balance..."

        elif intent == "report_request":
            # Generate and send report
            return "📊 Generating your report... This may take a moment."

        elif intent == "help_request":
            # Send help menu
            return """🤖 *AUREN 2.0 Help*

Available commands:
• Send photos for biometric analysis
• "weight X" to log weight
• "peptide X" to log peptide dose
• "report" for daily summary
• "menu" for full options

Need more help? Just ask!"""

        else:
            # Default response
            return "👋 Thanks for your message! I'm here to help with your biometric optimization. Send 'help' for available commands."

    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the application"""

        logger.info("Starting AUREN 2.0...")
        logger.info(f"Server will run on {host}:{port}")

        uvicorn.run(self.app, host=host, port=port, log_level="info")


def main():
    """Main entry point"""

    # Create and run the application
    app = AUREN2App()
    app.run()


if __name__ == "__main__":
    main()
