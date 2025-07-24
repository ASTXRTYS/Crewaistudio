#!/usr/bin/env python3
"""
Knowledge Base Loader for AUREN Neuroscientist MVP
Loads all Level 1 knowledge markdown files into the Neuroscientist's knowledge base

IMPORTANT: For the MVP, there is only ONE agent - the Neuroscientist.
The files named "CNS Optimization Specialist", "Health Orchestration Coordinator", 
"Metabolic Optimization Specialist", etc. are all different aspects of the SAME 
Neuroscientist agent's expertise.

This script:
1. Uses the existing ClinicalMarkdownParser to parse markdown files
2. Creates KnowledgeItem objects all assigned to the Neuroscientist
3. Loads via KnowledgeManager to maintain event sourcing
4. Preserves all architectural patterns from Modules A & B
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional
import sys
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from intelligence.knowledge_manager import KnowledgeManager
from intelligence.markdown_parser import ClinicalMarkdownParser
from intelligence.data_structures import (
    KnowledgeItem, KnowledgeType, KnowledgeStatus,
    create_knowledge_id, SpecialistDomain
)
from data_layer.memory_backend import PostgreSQLMemoryBackend
from data_layer.event_store import EventStore, EventStreamType
from data_layer.connection import get_database_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KnowledgeLoader:
    """
    Loads clinical knowledge from markdown files into AUREN's knowledge base
    using the existing Module A & B infrastructure
    """
    
    def __init__(self):
        self.parser = ClinicalMarkdownParser()
        self.db_connection = None
        self.memory_backend = None
        self.event_store = None
        self.knowledge_manager = None
        
        # ALL knowledge files belong to the Neuroscientist
        # The Neuroscientist IS the CNS Specialist, Health Coordinator, etc.
        # They are all the same agent with different aspects of expertise
        self.domain_mapping = {
            'neuroscientist': SpecialistDomain.NEUROSCIENCE.value,
            'cns': SpecialistDomain.NEUROSCIENCE.value,
            'health': SpecialistDomain.NEUROSCIENCE.value,
            'metabolic': SpecialistDomain.NEUROSCIENCE.value,
            'movement': SpecialistDomain.NEUROSCIENCE.value,
            'hrv': SpecialistDomain.NEUROSCIENCE.value,
            'vagal': SpecialistDomain.NEUROSCIENCE.value,
            'stress': SpecialistDomain.NEUROSCIENCE.value,
            'sleep': SpecialistDomain.NEUROSCIENCE.value,
            'recovery': SpecialistDomain.NEUROSCIENCE.value,
            'fatigue': SpecialistDomain.NEUROSCIENCE.value,
            'assessment': SpecialistDomain.NEUROSCIENCE.value,
            'emergency': SpecialistDomain.NEUROSCIENCE.value,
            'optimization': SpecialistDomain.NEUROSCIENCE.value
        }
    
    async def initialize(self):
        """Initialize database connections and managers"""
        logger.info("Initializing knowledge loader...")
        
        # Get database connection
        self.db_connection = get_database_connection()
        await self.db_connection.initialize()
        
        # Initialize memory backend
        self.memory_backend = PostgreSQLMemoryBackend(
            self.db_connection.pool,
            agent_type="knowledge_loader",
            user_id="system"
        )
        await self.memory_backend.initialize()
        
        # Initialize event store
        self.event_store = EventStore(self.db_connection)
        await self.event_store.initialize()
        
        # Initialize knowledge manager
        self.knowledge_manager = KnowledgeManager(
            self.memory_backend,
            self.event_store
        )
        
        logger.info("✅ Knowledge loader initialized")
    
    def determine_domain(self, filename: str, parsed_content: Dict) -> str:
        """
        Determine the specialist domain from filename and content
        
        NOTE: For the MVP, ALL knowledge belongs to the Neuroscientist.
        The Neuroscientist IS the CNS Specialist, Health Coordinator, etc.
        
        Args:
            filename: The markdown filename
            parsed_content: Parsed content from ClinicalMarkdownParser
            
        Returns:
            The specialist domain string (always NEUROSCIENCE for MVP)
        """
        # For MVP: ALL knowledge goes to the Neuroscientist
        logger.info(f"Loading '{filename}' into Neuroscientist knowledge base")
        return SpecialistDomain.NEUROSCIENCE.value
    
    def determine_agent_id(self, domain: str) -> str:
        """
        Determine the agent ID from domain
        
        NOTE: For the MVP, there is only ONE agent - the Neuroscientist.
        All knowledge belongs to this single agent.
        
        Args:
            domain: The specialist domain
            
        Returns:
            The agent ID (always "neuroscientist" for MVP)
        """
        # For MVP: There is only ONE agent - the Neuroscientist
        return "neuroscientist"
    
    def _serialize_parsed_content(self, parsed_content: Dict) -> Dict:
        """
        Convert parsed content to JSON-serializable format
        
        Args:
            parsed_content: The parsed content from ClinicalMarkdownParser
            
        Returns:
            JSON-serializable dictionary
        """
        # Handle sections which contain ParsedSection objects
        if 'sections' in parsed_content:
            serialized_sections = []
            for section in parsed_content['sections']:
                # If it's a ParsedSection object, convert to dict
                if hasattr(section, '__dict__'):
                    section_dict = {
                        'title': section.title,
                        'content': section.content,
                        'metadata': section.metadata,
                        'confidence_score': section.confidence_score,
                        'evidence_level': section.evidence_level,
                        'section_type': section.section_type
                    }
                    serialized_sections.append(section_dict)
                else:
                    serialized_sections.append(section)
            
            parsed_content['sections'] = serialized_sections
        
        return parsed_content
    
    async def load_single_file(self, file_path: Path) -> bool:
        """
        Load a single markdown file into the knowledge base
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"📄 Loading: {file_path.name}")
            
            # Parse the markdown file
            parsed_content = self.parser.parse_file(file_path)
            
            if not parsed_content:
                logger.error(f"Failed to parse {file_path.name}")
                return False
            
            # Determine domain and agent
            domain = self.determine_domain(file_path.stem, parsed_content)
            agent_id = self.determine_agent_id(domain)
            
            # Extract key information
            title = parsed_content.get('title', file_path.stem.replace('_', ' ').title())
            description = parsed_content.get('description', f"Knowledge from {file_path.name}")
            confidence = parsed_content.get('confidence_score', 0.8)
            
            # Determine knowledge type based on content
            knowledge_type = KnowledgeType.PATTERN  # Default
            if 'protocol' in title.lower() or 'protocol' in description.lower():
                knowledge_type = KnowledgeType.BEST_PRACTICE
            elif 'correlation' in title.lower() or 'relationship' in title.lower():
                knowledge_type = KnowledgeType.CORRELATION
            
            # Create KnowledgeItem
            knowledge_item = KnowledgeItem(
                knowledge_id=create_knowledge_id(),
                agent_id=agent_id,
                domain=domain,
                knowledge_type=knowledge_type,
                title=title,
                description=description,
                content=self._serialize_parsed_content(parsed_content),
                confidence=confidence,
                evidence_sources=list(parsed_content.get('evidence_levels', {}).keys()),
                validation_status=KnowledgeStatus.VALIDATED if confidence > 0.7 else KnowledgeStatus.PROVISIONAL,
                related_knowledge=[],  # Will be populated later
                conflicts_with=[],
                supports=[],
                application_count=0,
                success_rate=0.0,
                last_applied=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                metadata={
                    'source_file': file_path.name,
                    'parsing_version': '2.0',
                    'emergency_protocols': len(parsed_content.get('emergency_protocols', [])),
                    'cross_references': len(parsed_content.get('cross_references', [])),
                    **parsed_content.get('metadata', {})
                }
            )
            
            # Store directly in memory backend since KnowledgeManager has inconsistencies
            # The add_knowledge method expects user_id but KnowledgeItem doesn't have it
            knowledge_id = await self.memory_backend.store(
                memory_type="knowledge",
                content={
                    "knowledge_id": knowledge_item.knowledge_id,
                    "agent_id": knowledge_item.agent_id,
                    "domain": knowledge_item.domain,
                    "knowledge_type": knowledge_item.knowledge_type.value,
                    "title": knowledge_item.title,
                    "description": knowledge_item.description,
                    "content": knowledge_item.content,  # Already serialized
                    "confidence": knowledge_item.confidence,
                    "evidence_sources": knowledge_item.evidence_sources,
                    "validation_status": knowledge_item.validation_status.value,
                    "related_knowledge": knowledge_item.related_knowledge,
                    "conflicts_with": knowledge_item.conflicts_with,
                    "supports": knowledge_item.supports,
                    "application_count": knowledge_item.application_count,
                    "success_rate": knowledge_item.success_rate,
                    "last_applied": knowledge_item.last_applied.isoformat() if knowledge_item.last_applied else None,
                    "created_at": knowledge_item.created_at.isoformat(),
                    "updated_at": knowledge_item.updated_at.isoformat(),
                    "metadata": knowledge_item.metadata
                },
                confidence=knowledge_item.confidence,
                metadata={
                    "source": "knowledge_loader",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            # Log the event
            await self.event_store.append_event(
                stream_id="system",
                stream_type=EventStreamType.KNOWLEDGE,
                event_type="knowledge_added",
                event_data={
                    "knowledge_id": knowledge_item.knowledge_id,
                    "agent_id": knowledge_item.agent_id,
                    "domain": knowledge_item.domain,
                    "title": knowledge_item.title
                }
            )
            
            logger.info(f"✅ Loaded '{title}' to {domain} domain (confidence: {confidence:.2f})")
            
            # Log emergency protocols if present
            emergency_protocols = parsed_content.get('emergency_protocols', [])
            if emergency_protocols:
                logger.warning(f"⚠️  Found {len(emergency_protocols)} emergency protocols in {file_path.name}")
                for protocol in emergency_protocols:
                    logger.warning(f"   - {protocol.get('title', 'Unknown')}: {protocol.get('urgency_level', 'unknown')} urgency")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading {file_path.name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def load_all_knowledge(self) -> Dict[str, int]:
        """
        Load all knowledge files from the Level 1 knowledge directory
        
        Returns:
            Dictionary with loading statistics
        """
        knowledge_dir = Path("auren/src/agents/Level 1 knowledge /")
        
        if not knowledge_dir.exists():
            logger.error(f"Knowledge directory not found: {knowledge_dir}")
            return {"error": "Directory not found"}
        
        # Get all markdown files
        md_files = list(knowledge_dir.glob("*.md"))
        logger.info(f"Found {len(md_files)} knowledge files to load")
        
        # Statistics
        stats = {
            "total_files": len(md_files),
            "loaded": 0,
            "failed": 0,
            "by_domain": {}
        }
        
        # Load each file
        for md_file in md_files:
            success = await self.load_single_file(md_file)
            if success:
                stats["loaded"] += 1
            else:
                stats["failed"] += 1
        
        # Get domain statistics
        logger.info("\n📊 Loading Summary:")
        logger.info(f"Total files: {stats['total_files']}")
        logger.info(f"Successfully loaded: {stats['loaded']}")
        logger.info(f"Failed: {stats['failed']}")
        
        # For MVP: All knowledge is in the neuroscience domain
        # Using direct memory backend due to KnowledgeManager inconsistencies
        neuroscience_knowledge = await self.memory_backend.retrieve(
            memory_type="knowledge",
            limit=1000
        )
        count = len(neuroscience_knowledge)
        stats["by_domain"][SpecialistDomain.NEUROSCIENCE.value] = count
        logger.info(f"\n  Neuroscientist knowledge base: {count} knowledge items")
        logger.info("  (All knowledge belongs to the single Neuroscientist agent)")
        
        return stats
    
    async def verify_loaded_knowledge(self):
        """Verify that knowledge was loaded correctly"""
        logger.info("\n🔍 Verifying loaded knowledge...")
        
        # Get all knowledge directly from memory backend
        all_knowledge = await self.memory_backend.retrieve(
            memory_type="knowledge",
            limit=1000
        )
        
        logger.info(f"Total knowledge items in database: {len(all_knowledge)}")
        
        # Sample a few items
        if all_knowledge:
            logger.info("\n📝 Sample knowledge items:")
            for item in all_knowledge[:3]:
                content = item.get('content', {})
                title = content.get('title', 'Unknown')
                domain = content.get('domain', 'Unknown')
                confidence = content.get('confidence', 0.0)
                logger.info(f"  - {title} ({domain}) - Confidence: {confidence:.2f}")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.db_connection:
            await self.db_connection.cleanup()


async def main():
    """Main entry point"""
    loader = KnowledgeLoader()
    
    try:
        # Initialize
        await loader.initialize()
        
        # Load all knowledge
        logger.info("\n🚀 Starting knowledge base loading...")
        stats = await loader.load_all_knowledge()
        
        # Verify loading
        await loader.verify_loaded_knowledge()
        
        # Print final summary
        logger.info("\n✅ Knowledge base loading complete!")
        logger.info(f"Successfully loaded {stats.get('loaded', 0)} out of {stats.get('total_files', 0)} files")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        await loader.cleanup()


if __name__ == "__main__":
    asyncio.run(main()) 