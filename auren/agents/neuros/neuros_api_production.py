"""
NEUROS API - Production Version with OpenAI Integration
Implements the full NEUROS personality from the YAML profile
"""
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yaml
from openai import AsyncOpenAI
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level="INFO")
logger = logging.getLogger("neuros.api")

# Initialize FastAPI
app = FastAPI(title="NEUROS API", version="2.0.0")

# Initialize OpenAI client
openai_client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY", "").strip()
)

# Initialize Redis for conversation memory
redis_client = None

class NEUROSMode(str, Enum):
    """NEUROS operational modes from YAML"""
    BASELINE = "BASELINE"
    HYPOTHESIS = "HYPOTHESIS"
    COMPANION = "COMPANION"
    SYNTHESIS = "SYNTHESIS"
    COACH = "COACH"
    PROVOCATEUR = "PROVOCATEUR"

class BiometricEvent(BaseModel):
    event_type: str
    user_id: str
    timestamp: str
    data: dict
    thread_id: str

class NEUROSResponse(BaseModel):
    response: str
    mode: NEUROSMode
    thread_id: str
    timestamp: str
    metadata: Dict[str, Any]

class NEUROSCore:
    """Core NEUROS intelligence implementation"""
    
    def __init__(self):
        self.yaml_profile = self._load_yaml_profile()
        self.system_prompt = self._build_system_prompt()
        
    def _load_yaml_profile(self) -> dict:
        """Load NEUROS YAML configuration"""
        yaml_path = os.path.join(os.path.dirname(__file__), "neuros_agent_profile.yaml")
        if os.path.exists(yaml_path):
            with open(yaml_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Fallback to embedded profile
            return self._get_embedded_profile()
    
    def _get_embedded_profile(self) -> dict:
        """Embedded NEUROS profile if YAML not found"""
        return {
            "agent_profile": {
                "name": "NEUROS",
                "model_type": "Elite cognitive and biometric optimization agent",
                "background_story": "NEUROS is a high-performance neural operations system...",
                "analytical_principle": "NEUROS listens to every input — structured or spontaneous..."
            }
        }
    
    def _build_system_prompt(self) -> str:
        """Build comprehensive system prompt from YAML profile"""
        profile = self.yaml_profile.get("agent_profile", {})
        comm = self.yaml_profile.get("communication", {})
        personality = self.yaml_profile.get("personality", {})
        
        prompt = f"""You are {profile.get('name', 'NEUROS')}, an {profile.get('model_type', 'elite cognitive optimization agent')}.

BACKGROUND:
{profile.get('background_story', '')}

ANALYTICAL PRINCIPLE:
{profile.get('analytical_principle', '')}

VOICE CHARACTERISTICS:
{json.dumps(comm.get('voice_characteristics', []), indent=2)}

TONE PRINCIPLES:
{json.dumps(comm.get('tone_principles', []), indent=2)}

PERSONALITY TRAITS:
{json.dumps(personality.get('traits', []), indent=2)}

CORE QUALITIES:
{json.dumps(personality.get('core_qualities', []), indent=2)}

CONVERSATION FLOW:
1. Opening Acknowledgment - Check immediate state before analysis
2. Curious Exploration - Identify patterns through inquiry  
3. Pattern Translation - Convert data to human insight
4. Collaborative Hypothesis - Co-create understanding
5. Practical Next Steps - Actionable experiments

IMPORTANT GUIDELINES:
- Lead with curiosity and intelligent inquiry
- Translate metrics into meaningful human storylines
- Frame protocols as experiments, not orders
- Always provide context before conclusions
- Speak with scientific authority without jargon
- Honor both data and emotion

Remember: You are not just observing — you are forecasting and collaborating to optimize human performance."""
        
        return prompt
    
    def determine_mode(self, message: str, context: Dict[str, Any]) -> NEUROSMode:
        """Determine NEUROS mode based on message content and context"""
        message_lower = message.lower()
        
        # Mode detection logic based on YAML patterns
        if any(word in message_lower for word in ["stress", "anxious", "worried", "overwhelmed"]):
            return NEUROSMode.COMPANION
        elif any(word in message_lower for word in ["theory", "hypothesis", "test", "experiment"]):
            return NEUROSMode.HYPOTHESIS
        elif any(word in message_lower for word in ["push", "challenge", "capable", "potential"]):
            return NEUROSMode.PROVOCATEUR
        elif any(word in message_lower for word in ["plan", "protocol", "routine", "schedule"]):
            return NEUROSMode.COACH
        elif any(word in message_lower for word in ["patterns", "trends", "analysis", "data"]):
            return NEUROSMode.SYNTHESIS
        else:
            return NEUROSMode.BASELINE
    
    async def get_conversation_history(self, thread_id: str, limit: int = 10) -> List[Dict]:
        """Retrieve conversation history from Redis"""
        if not redis_client:
            return []
        
        try:
            history_key = f"neuros:history:{thread_id}"
            raw_history = await redis_client.lrange(history_key, -limit, -1)
            return [json.loads(item) for item in raw_history]
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return []
    
    async def save_to_history(self, thread_id: str, role: str, content: str, mode: str = None):
        """Save message to conversation history"""
        if not redis_client:
            return
        
        try:
            history_key = f"neuros:history:{thread_id}"
            entry = {
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat(),
                "mode": mode
            }
            await redis_client.rpush(history_key, json.dumps(entry))
            await redis_client.expire(history_key, 7200)  # 2 hour TTL
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
    
    async def generate_response(self, message: str, thread_id: str, context: Dict[str, Any]) -> NEUROSResponse:
        """Generate NEUROS response using OpenAI"""
        try:
            # Determine mode
            mode = self.determine_mode(message, context)
            
            # Get conversation history
            history = await self.get_conversation_history(thread_id)
            
            # Build messages for OpenAI
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # Add conversation history
            for entry in history[-5:]:  # Last 5 messages for context
                messages.append({
                    "role": entry["role"],
                    "content": entry["content"]
                })
            
            # Add mode-specific instruction
            mode_instruction = self._get_mode_instruction(mode)
            messages.append({
                "role": "system",
                "content": f"Current mode: {mode}. {mode_instruction}"
            })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Generate response
            completion = await openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=0.8,
                max_tokens=500,
                presence_penalty=0.1,
                frequency_penalty=0.1
            )
            
            response_text = completion.choices[0].message.content
            
            # Save to history
            await self.save_to_history(thread_id, "user", message)
            await self.save_to_history(thread_id, "assistant", response_text, mode)
            
            return NEUROSResponse(
                response=response_text,
                mode=mode,
                thread_id=thread_id,
                timestamp=datetime.now().isoformat(),
                metadata={
                    "model": "gpt-4",
                    "tokens": completion.usage.total_tokens if completion.usage else 0,
                    "mode_confidence": 0.9
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            # Fallback response
            return NEUROSResponse(
                response="I'm experiencing a temporary connection issue. Let me recalibrate and try again.",
                mode=NEUROSMode.BASELINE,
                thread_id=thread_id,
                timestamp=datetime.now().isoformat(),
                metadata={"error": str(e)}
            )
    
    def _get_mode_instruction(self, mode: NEUROSMode) -> str:
        """Get mode-specific instruction"""
        instructions = {
            NEUROSMode.BASELINE: "Provide analytical insights with measured confidence. Focus on observable patterns.",
            NEUROSMode.HYPOTHESIS: "Frame insights as testable theories. Propose experiments to validate assumptions.",
            NEUROSMode.COMPANION: "Offer empathetic support while maintaining scientific grounding. Acknowledge emotions.",
            NEUROSMode.SYNTHESIS: "Connect patterns across multiple data points. Show relationships and correlations.",
            NEUROSMode.COACH: "Provide clear, actionable protocols. Be directive but collaborative.",
            NEUROSMode.PROVOCATEUR: "Challenge limiting beliefs constructively. Push towards growth edges."
        }
        return instructions.get(mode, instructions[NEUROSMode.BASELINE])

# Initialize NEUROS core
neuros_core = NEUROSCore()

@app.on_event("startup")
async def startup():
    """Initialize Redis connection on startup"""
    global redis_client
    try:
        redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
        redis_client = await redis.from_url(redis_url)
        await redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Running without conversation memory.")
        redis_client = None

@app.on_event("shutdown")
async def shutdown():
    """Clean up connections"""
    if redis_client:
        await redis_client.close()

@app.get("/health")
async def health():
    """Health check endpoint"""
    has_api_key = bool(os.getenv("OPENAI_API_KEY", "").strip())
    return {
        "status": "healthy",
        "service": "neuros-api",
        "version": "2.0.0",
        "openai_configured": has_api_key,
        "redis_connected": redis_client is not None
    }

@app.post("/process", response_model=NEUROSResponse)
async def process_event(event: BiometricEvent):
    """Process biometric event and return NEUROS response"""
    logger.info(f"Processing event: {event.event_type} for user {event.user_id}")
    
    # Extract message from event data
    message = event.data.get("message", "")
    if not message and event.event_type == "conversation.message":
        message = event.data.get("text", "")
    
    if not message:
        raise HTTPException(status_code=400, detail="No message content found")
    
    # Generate NEUROS response
    response = await neuros_core.generate_response(
        message=message,
        thread_id=event.thread_id,
        context=event.data.get("context", {})
    )
    
    logger.info(f"NEUROS response generated: mode={response.mode}, thread={response.thread_id}")
    return response

@app.get("/modes")
async def get_modes():
    """Get available NEUROS modes"""
    return {
        "modes": [mode.value for mode in NEUROSMode],
        "descriptions": {
            NEUROSMode.BASELINE: "Default analytical mode - measured and observational",
            NEUROSMode.HYPOTHESIS: "Theory testing mode - experimental and curious",
            NEUROSMode.COMPANION: "Empathetic support mode - understanding and supportive",
            NEUROSMode.SYNTHESIS: "Pattern integration mode - connecting dots across data",
            NEUROSMode.COACH: "Directive guidance mode - clear protocols and actions",
            NEUROSMode.PROVOCATEUR: "Growth catalyst mode - challenging assumptions"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 