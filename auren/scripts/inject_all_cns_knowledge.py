#!/usr/bin/env python3
"""
Corrected CNS Knowledge Injection System
Uses existing PostgreSQL event-sourced architecture per Module A specifications
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Any
import logging
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from data_layer.event_store import EventStore
from data_layer.memory_backend import PostgreSQLMemoryBackend
from data_layer.connection import DatabaseConnection, initialize_schema

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CNSKnowledgeInjector:
    """
    Corrected knowledge injection using existing PostgreSQL infrastructure
    Follows Module A Section 3.4 & 3.7 specifications
    """
    
    def __init__(self):
        self.knowledge_folder = Path("./src/agents/level1_knowledge")
        
        # Specialist mapping from Master Control Document
        self.specialist_mapping = {
            "neuroscientist": ["cns_optimization", "neuroscience"],
            "nutritionist": ["metabolic_optimization", "nutrition"], 
            "training": ["movement_optimization", "training"],
            "recovery": ["recovery", "sleep"],
            "sleep": ["sleep", "recovery"],
            "mental_health": ["mental_health", "stress_management"]
        }
        
        self.event_store = None
        self.memory_backends = {}
        
    async def initialize_infrastructure(self):
        """Initialize existing PostgreSQL infrastructure"""
        logger.info("🔌 Initializing PostgreSQL infrastructure...")
        
        # Initialize database connection
        db_conn = DatabaseConnection()
        success = await db_conn.initialize()
        if not success:
            raise RuntimeError("Failed to initialize database connection")
        
        # Initialize schema
        await initialize_schema()
        
        # Initialize event store
        self.event_store = EventStore(db_conn)
        
        # Initialize memory backends for each specialist
        for specialist_type in self.specialist_mapping.keys():
            self.memory_backends[specialist_type] = PostgreSQLMemoryBackend(
                pool=db_conn.pool,
                specialist_type=specialist_type,
                user_id="system"  # System-level knowledge
            )
            await self.memory_backends[specialist_type].initialize()
        
        logger.info("✅ PostgreSQL infrastructure initialized")
        
    async def parse_knowledge_file(self, file_path: Path) -> Dict[str, Any]:
        """Parse a knowledge file into structured content"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata from filename
            parts = file_path.stem.split('_', 1)
            if len(parts) != 2:
                return None
                
            specialist_type, knowledge_type = parts
            
            # Map to correct specialist
            actual_specialist = None
            for specialist, domains in self.specialist_mapping.items():
                if specialist_type in domains or specialist_type == specialist:
                    actual_specialist = specialist
                    break
            
            if not actual_specialist:
                actual_specialist = "neuroscientist"  # Default fallback
                
            return {
                "specialist_type": actual_specialist,
                "knowledge_type": knowledge_type,
                "title": f"{actual_specialist.capitalize()} {knowledge_type.replace('_', ' ').title()}",
                "content": content,
                "source_file": str(file_path),
                "confidence": 0.9,
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing {file_path}: {e}")
            return None
    
    async def inject_knowledge_as_event(self, knowledge: Dict[str, Any]) -> str:
        """Store knowledge as event in EventStore"""
        event_data = {
            "knowledge_type": knowledge["knowledge_type"],
            "title": knowledge["title"],
            "content": knowledge["content"],
            "specialist_type": knowledge["specialist_type"],
            "confidence": knowledge["confidence"],
            "source_file": knowledge["source_file"]
        }
        
        event_id = await self.event_store.append_event(
            stream_id=f"knowledge_{knowledge['specialist_type']}",
            stream_type="specialist_knowledge",
            event_type="knowledge_added",
            event_data=event_data
        )
        
        return event_id
    
    async def inject_knowledge_to_memory(self, knowledge: Dict[str, Any]) -> int:
        """Store knowledge in specialist memory backend"""
        backend = self.memory_backends[knowledge["specialist_type"]]
        
        memory_id = await backend.add_memory(
            memory_type="knowledge_base",
            content={
                "title": knowledge["title"],
                "content": knowledge["content"],
                "source_file": knowledge["source_file"],
                "knowledge_type": knowledge["knowledge_type"]
            },
            confidence=knowledge["confidence"]
        )
        
        return memory_id
    
    async def inject_specialist_knowledge(self, specialist_type: str) -> int:
        """Inject knowledge for a specific specialist"""
        pattern = f"*{specialist_type}*.md"
        files = list(self.knowledge_folder.glob(pattern))
        
        if not files:
            # Try broader patterns
            for domain in self.specialist_mapping.get(specialist_type, []):
                pattern = f"{domain}_*.md"
                files.extend(list(self.knowledge_folder.glob(pattern)))
        
        if not files:
            logger.warning(f"⚠️  No files found for {specialist_type}")
            return 0
        
        injected_count = 0
        
        for file_path in files:
            knowledge = await self.parse_knowledge_file(file_path)
            if not knowledge:
                continue
            
            # Store as event (immutable record)
            event_id = await self.inject_knowledge_as_event(knowledge)
            
            # Store in memory backend (fast access)
            memory_id = await self.inject_knowledge_to_memory(knowledge)
            
            logger.info(f"✅ Injected {knowledge['title']} (event: {event_id}, memory: {memory_id})")
            injected_count += 1
        
        return injected_count
    
    async def inject_all_knowledge(self) -> bool:
        """Inject all specialist knowledge using correct architecture"""
        logger.info("🧠 Starting CNS Knowledge Injection (PostgreSQL Architecture)")
        logger.info("=" * 60)
        
        # Ensure knowledge folder exists
        if not self.knowledge_folder.exists():
            alt_paths = [
                "./src/agents/Level 1 knowledge",
                "src/agents/Level 1 knowledge ",
                "src/agents/Level 1 knowledge/"
            ]
            for alt_path in alt_paths:
                if Path(alt_path).exists():
                    self.knowledge_folder = Path(alt_path)
                    break
            else:
                logger.error(f"❌ Knowledge folder not found: {self.knowledge_folder}")
                return False
        
        # Initialize infrastructure
        await self.initialize_infrastructure()
        
        # Inject knowledge for each specialist
        total_injected = 0
        
        for specialist_type in self.specialist_mapping.keys():
            count = await self.inject_specialist_knowledge(specialist_type)
            total_injected += count
            logger.info(f"✅ {specialist_type}: {count} knowledge items injected")
        
        # Verify injection
        await self.verify_injection()
        
        logger.info(f"\n🎉 INJECTION COMPLETE!")
        logger.info(f"📊 Total knowledge items injected: {total_injected}")
        
        return True
    
    async def verify_injection(self):
        """Verify knowledge injection across all systems"""
        logger.info("🔍 Verifying knowledge injection...")
        
        # Check event store
        for specialist_type in self.specialist_mapping.keys():
            events = await self.event_store.get_events(
                stream_id=f"knowledge_{specialist_type}",
                stream_type="specialist_knowledge"
            )
            logger.info(f"📊 {specialist_type}: {len(events)} events in EventStore")
        
        # Check memory backends
        for specialist_type, backend in self.memory_backends.items():
            summary = await backend.get_memory_summary()
            logger.info(f"📊 {specialist_type}: {summary['memory']['total_memories']} memories")
        
        logger.info("✅ Verification complete")


async def main():
    """Main execution"""
    injector = CNSKnowledgeInjector()
    
    try:
        success = await injector.inject_all_knowledge()
        
        if success:
            logger.info("\n🚀 All CNS knowledge successfully injected into PostgreSQL!")
            logger.info("System is ready for agent activation")
        else:
            logger.error("\n❌ Injection failed")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fatal error during injection: {e}")
        raise
    
    return True


if __name__ == "__main__":
    asyncio.run(main())
