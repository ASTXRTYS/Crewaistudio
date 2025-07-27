#!/usr/bin/env python3
"""
=============================================================================
AUREN PIONEER'S BIOMETRIC BRIDGE - ENHANCED IMPLEMENTATION v2.0
=============================================================================
The World's First Kafka → LangGraph Real-Time Biometric Cognitive System

Created by: AUREN Co-Founders (ASTxRTYS & Claude)
Date: January 2025
Version: 2.0 - Enhanced with Expert Recommendations
=============================================================================
"""

import os
import json
import asyncio
import signal
import logging
from typing import TypedDict, Annotated, Literal, Dict, Any, List, Optional, Sequence
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

import uvloop
import aiohttp
import asyncpg
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import prometheus_client
from pydantic import BaseSettings, Field

from kafka.errors import KafkaError
from langchain_core.messages import BaseMessage, add_messages
from langgraph.graph import StateGraph, Command
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.redis import RedisSaver
from langgraph.pregel import Channel

# =============================================================================
# 0) Use uvloop for better async performance
# =============================================================================
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

# =============================================================================
# 1) Structured logging
# =============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger("AUREN.BIOMETRIC.BRIDGE")

# =============================================================================
# 2) Prometheus metrics
# =============================================================================
EVENTS_PROCESSED = prometheus_client.Counter(
    "biometric_events_total", "Total biometric events processed", ["mode"]
)
EVENTS_FAILED = prometheus_client.Counter(
    "biometric_failures_total", "Failed biometric events"
)

# =============================================================================
# 3) Configuration via Pydantic
# =============================================================================
class Settings(BaseSettings):
    # Use default values based on docker-compose.yml
    OPENAI_API_KEY: str = Field(
        default=os.getenv("OPENAI_API_KEY", ""),
        env="OPENAI_API_KEY"
    )
    KAFKA_BOOTSTRAP_SERVERS: str = Field(
        default="localhost:9092",
        env="KAFKA_BOOTSTRAP_SERVERS"
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        env="REDIS_URL"
    )
    POSTGRES_URL: str = Field(
        default="postgresql://auren_user:auren_password_2024@localhost:5432/auren_db",
        env="POSTGRES_URL"
    )
    CHECKPOINT_POSTGRES_URL: str = Field(
        default="postgresql://auren_user:auren_password_2024@localhost:5432/auren_db",
        env="CHECKPOINT_POSTGRES_URL"
    )
    OURA_ACCESS_TOKEN: str = Field(
        default="mock_oura_token",
        env="OURA_ACCESS_TOKEN"
    )
    WHOOP_CLIENT_ID: str = Field(
        default="mock_whoop_client",
        env="WHOOP_CLIENT_ID"
    )
    WHOOP_CLIENT_SECRET: str = Field(
        default="mock_whoop_secret",
        env="WHOOP_CLIENT_SECRET"
    )
    WEBSOCKET_URL: str = Field(
        default="ws://localhost:8080/ws",
        env="WEBSOCKET_URL"
    )
    PROMETHEUS_PORT: int = Field(
        default=8002,
        env="PROMETHEUS_PORT"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()

# =============================================================================
# 4) Your original QuickBiometricNEUROS demo, unchanged except signature
# =============================================================================
from crewai import Crew, Agent
import yaml

class QuickBiometricNEUROS:
    def __init__(self, neuros_yaml_path: str):
        with open(neuros_yaml_path) as f:
            self.config = yaml.safe_load(f)
        self.modes = {
            'reflex':  Agent(role="Crisis Responder", temperature=0.1),
            'pattern': Agent(role="Pattern Analyzer",  temperature=0.5)
        }

    async def process_biometric_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        if event.get('hrv_drop', 0) > 25:
            mode = 'reflex'
            response = "I notice your HRV dropped significantly. Let's reset together."
        else:
            mode = 'pattern'
            response = "Your biometrics look stable. How are you feeling?"
        crew = Crew(agents=[self.modes[mode]], tasks=[])
        return {'mode': mode, 'response': response}

# =============================================================================
# 5) Full Type-Safe Wearable Classes
# =============================================================================
class WearableType(str, Enum):
    APPLE_HEALTH = "apple_health"
    OURA_RING    = "oura_ring"
    WHOOP_BAND   = "whoop_band"
    GARMIN       = "garmin"
    FITBIT       = "fitbit"
    EIGHT_SLEEP  = "eight_sleep"

@dataclass(frozen=True)
class BiometricReading:
    metric:     str
    value:      float
    timestamp:  datetime
    confidence: float = 1.0
    def __post_init__(self):
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        if self.value < 0:
            raise ValueError(f"Biometric value cannot be negative: {self.metric}")

@dataclass
class BiometricEvent:
    device_type: WearableType
    user_id:      str
    timestamp:    datetime
    readings:     List[BiometricReading] = field(default_factory=list)

    @property
    def hrv(self) -> Optional[float]:
        for r in self.readings:
            if r.metric == "hrv":
                return r.value
        return None

    @property
    def heart_rate(self) -> Optional[int]:
        for r in self.readings:
            if r.metric == "heart_rate":
                return int(r.value)
        return None

    @property
    def stress_level(self) -> Optional[float]:
        for r in self.readings:
            if r.metric == "stress_level":
                return r.value
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_type": self.device_type.value,
            "user_id":      self.user_id,
            "timestamp":    self.timestamp.isoformat(),
            "readings": [
                {"metric":r.metric, "value":r.value, "timestamp":r.timestamp.isoformat(), "confidence":r.confidence}
                for r in self.readings
            ]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BiometricEvent':
        return cls(
            device_type=WearableType(data["device_type"]),
            user_id=data["user_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            readings=[
                BiometricReading(
                    metric=r["metric"],
                    value=r["value"],
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                    confidence=r.get("confidence",1.0)
                ) for r in data.get("readings",[])
            ]
        )

# =============================================================================
# 6) Full Cognitive State TypedDict
# =============================================================================
class CognitiveMode(str, Enum):
    REFLEX     = "reflex"
    PATTERN    = "pattern"
    HYPOTHESIS = "hypothesis"
    GUARDIAN   = "guardian"

class NEUROSState(TypedDict):
    messages:             Annotated[Sequence[BaseMessage], add_messages]
    current_mode:         CognitiveMode
    previous_mode:        Optional[CognitiveMode]
    mode_confidence:      float
    mode_history:         List[Dict[str, Any]]
    latest_biometric_event: Optional[Dict[str, Any]]
    hrv_current:          Optional[float]
    hrv_baseline:         Optional[float]
    hrv_drop:             Optional[float]
    heart_rate:           Optional[int]
    stress_level:         Optional[float]
    recovery_score:       Optional[float]
    user_id:              str
    session_id:           str
    last_biometric_trigger: Optional[str]
    trigger_timestamp:    Optional[str]
    active_hypothesis:    Optional[Dict[str, Any]]
    pattern_detections:   List[str]
    checkpoint_id:        Optional[str]
    last_checkpoint:      Optional[str]
    checkpoint_version:   int
    error_count:          int
    last_error:           Optional[str]
    processing_lock:      bool
    parallel_tasks:       List[str]

# =============================================================================
# 7) Checkpoint Saver Factory (Postgres + optional Redis fallback)
# =============================================================================
async def make_checkpoint_saver() -> List:
    """
    Returns list of savers: PostgresSaver (required)
    + RedisSaver (optional fallback for ultra-low latency)
    """
    pg_pool = await asyncpg.create_pool(
        settings.CHECKPOINT_POSTGRES_URL,
        min_size=2, 
        max_size=10, 
        timeout=60
    )
    pg_saver = PostgresSaver(
        pool=pg_pool,
        table="neuros_checkpoints",
        max_retries=3
    )
    # optional Redis fallback
    redis_saver = RedisSaver.from_url(settings.REDIS_URL)
    return [pg_saver, redis_saver]

# =============================================================================
# 8) Kafka ↔ WebSocket Bridge
# =============================================================================
class BiometricBridge:
    def __init__(self, neuros: QuickBiometricNEUROS, savers: List):
        loop = asyncio.get_event_loop()
        self.consumer = AIOKafkaConsumer(
            "biometric-events",
            loop=loop,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id="neuros-bridge",
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )
        self.producer = AIOKafkaProducer(
            loop=loop,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        )
        self.neuros = neuros
        self.graph = StateGraph(state_schema=NEUROSState)
        self.ws_url = settings.WEBSOCKET_URL
        self.savers = savers

    async def start(self):
        await self.consumer.start()
        await self.producer.start()
        prometheus_client.start_http_server(settings.PROMETHEUS_PORT)
        logger.info("Bridge started; consuming on biometric-events, metrics on :%d", settings.PROMETHEUS_PORT)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(self.ws_url) as ws:
                    self.ws = ws
                    async for msg in self.consumer:
                        await self.handle(msg)
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            # Continue without WebSocket for development
            async for msg in self.consumer:
                await self.handle(msg)

    async def handle(self, msg):
        try:
            # 1) Deserialize & type-convert
            raw = json.loads(msg.value)
            event = BiometricEvent.from_dict(raw)

            # 2) Trigger your cognitive graph
            result = await self.neuros.process_biometric_event(raw)
            
            # TODO: Integrate with LangGraph state management
            # await self.graph.ainvoke({"latest_biometric_event": raw})

            # 3) Metrics & logging
            EVENTS_PROCESSED.labels(mode=result["mode"]).inc()
            logger.info("Processed offset %s → mode=%s", msg.offset, result["mode"])

            # 4) Publish results
            payload = json.dumps(result).encode()
            await self.producer.send_and_wait("neuros-mode-switches", payload)
            
            # Send to WebSocket if connected
            if hasattr(self, 'ws') and not self.ws.closed:
                await self.ws.send_str(payload.decode())

            # 5) Commit Kafka offset
            await self.consumer.commit()
        except Exception as e:
            EVENTS_FAILED.inc()
            logger.exception("Error handling offset %s", msg.offset)

    async def shutdown(self):
        logger.info("Shutting down bridge...")
        await self.consumer.stop()
        await self.producer.stop()

# =============================================================================
# 9) Entrypoint + Graceful Shutdown
# =============================================================================
async def main():
    # Use relative path from project root
    neuros_yaml_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "auren", "config", "neuros.yaml"
    )
    
    savers = await make_checkpoint_saver()
    neuros = QuickBiometricNEUROS(neuros_yaml_path)
    bridge = BiometricBridge(neuros, savers)

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(bridge.shutdown()))

    await bridge.start()

if __name__ == "__main__":
    asyncio.run(main()) 