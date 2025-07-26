"""
Load Neuroscientist Level 1 Knowledge into Memory System

This script ingests all 15 knowledge files and stores them in the three-tier memory system
with appropriate tagging and high importance scores.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict
import re
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from auren.src.agents.neuroscientist import NeuroscientistAgent
from auren.core.memory import MemoryType
from auren.core.logging_config import get_logger

logger = get_logger(__name__)


class NeuroscientistKnowledgeLoader:
    """Loads Level 1 knowledge files into the neuroscientist's memory"""
    
    def __init__(self):
        self.knowledge_dir = Path("auren/src/agents/Level 1 knowledge")
        self.neuroscientist = None
        self.loaded_count = 0
        self.failed_count = 0
    
    async def initialize(self):
        """Initialize the neuroscientist agent"""
        logger.info("Initializing Neuroscientist agent...")
        self.neuroscientist = NeuroscientistAgent()
        await self.neuroscientist.initialize()
        logger.info("Neuroscientist agent initialized successfully")
    
    def extract_sections(self, content: str) -> List[Dict[str, str]]:
        """Extract meaningful sections from markdown content"""
        sections = []
        
        # Split by headers
        header_pattern = r'^#{1,3}\s+(.+)$'
        parts = re.split(header_pattern, content, flags=re.MULTILINE)
        
        # Process each section
        current_title = "Introduction"
        for i in range(0, len(parts)):
            if i % 2 == 0 and parts[i].strip():
                # This is content
                section_content = parts[i].strip()
                if len(section_content) > 100:  # Meaningful content
                    sections.append({
                        "title": current_title,
                        "content": section_content
                    })
            else:
                # This is a header
                current_title = parts[i] if i < len(parts) else "Unknown"
        
        return sections
    
    async def load_file(self, file_path: Path) -> int:
        """Load a single knowledge file into memory"""
        try:
            logger.info(f"Loading knowledge file: {file_path.name}")
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                full_content = f.read()
            
            # Extract topic from filename
            topic = file_path.stem.replace("neuroscientist_", "").replace("_", " ").title()
            
            # Extract sections for granular storage
            sections = self.extract_sections(full_content)
            
            # Store the full document as foundational knowledge
            memory_id = await self.neuroscientist.remember(
                content=f"Level 1 Knowledge - {topic}: {full_content[:500]}...",
                memory_type=MemoryType.KNOWLEDGE,
                importance=0.95,  # Very high importance for foundational knowledge
                tags=["level1", "foundational", topic.lower(), "complete_document"],
                metadata={
                    "source_file": file_path.name,
                    "topic": topic,
                    "sections": len(sections),
                    "total_length": len(full_content),
                    "ingested_at": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(f"Stored complete document with memory ID: {memory_id}")
            memories_stored = 1
            
            # Store individual sections for better retrieval
            for section in sections:
                section_memory_id = await self.neuroscientist.remember(
                    content=f"{topic} - {section['title']}: {section['content'][:300]}...",
                    memory_type=MemoryType.KNOWLEDGE,
                    importance=0.85,  # High importance for sections
                    tags=["level1", "section", topic.lower(), section['title'].lower()],
                    metadata={
                        "source_file": file_path.name,
                        "topic": topic,
                        "section_title": section['title'],
                        "parent_memory_id": memory_id,
                        "content_length": len(section['content'])
                    },
                    ttl_seconds=None  # No TTL for foundational knowledge
                )
                memories_stored += 1
            
            logger.info(f"Successfully loaded {file_path.name}: {memories_stored} memories created")
            return memories_stored
            
        except Exception as e:
            logger.error(f"Failed to load {file_path.name}: {e}")
            return 0
    
    async def load_all_knowledge(self):
        """Load all knowledge files from the Level 1 knowledge directory"""
        logger.info(f"Scanning knowledge directory: {self.knowledge_dir}")
        
        # Find all markdown files
        knowledge_files = list(self.knowledge_dir.glob("*.md"))
        logger.info(f"Found {len(knowledge_files)} knowledge files to load")
        
        # Load each file
        total_memories = 0
        for file_path in knowledge_files:
            memories_created = await self.load_file(file_path)
            if memories_created > 0:
                self.loaded_count += 1
                total_memories += memories_created
            else:
                self.failed_count += 1
        
        # Summary
        logger.info(f"""
Knowledge Loading Complete:
- Files processed: {len(knowledge_files)}
- Files loaded successfully: {self.loaded_count}
- Files failed: {self.failed_count}
- Total memories created: {total_memories}
        """)
        
        # Verify memories were stored
        stats = await self.neuroscientist.get_memory_stats()
        logger.info(f"Agent memory stats after loading: {stats}")
        
        return {
            "files_processed": len(knowledge_files),
            "files_loaded": self.loaded_count,
            "files_failed": self.failed_count,
            "total_memories": total_memories,
            "agent_stats": stats
        }
    
    async def verify_knowledge(self):
        """Verify knowledge was loaded correctly by testing recall"""
        logger.info("Verifying knowledge recall...")
        
        # Test queries
        test_queries = [
            "HRV analysis patterns",
            "stress assessment protocols",
            "sleep recovery correlation",
            "vagal nerve optimization",
            "emergency response procedures"
        ]
        
        for query in test_queries:
            logger.info(f"\nTesting recall for: '{query}'")
            results = await self.neuroscientist.recall(
                query=query,
                memory_types=[MemoryType.KNOWLEDGE],
                limit=3
            )
            
            if results:
                logger.info(f"Found {len(results)} relevant memories:")
                for i, result in enumerate(results, 1):
                    logger.info(f"  {i}. {result.content[:100]}... (confidence: {result.confidence:.2f})")
            else:
                logger.warning(f"No memories found for query: {query}")
    
    async def cleanup(self):
        """Clean up resources"""
        if self.neuroscientist:
            await self.neuroscientist.cleanup()


async def main():
    """Main execution function"""
    loader = NeuroscientistKnowledgeLoader()
    
    try:
        # Initialize
        await loader.initialize()
        
        # Load all knowledge
        results = await loader.load_all_knowledge()
        
        # Verify knowledge was loaded
        await loader.verify_knowledge()
        
        print("\n✅ Knowledge loading complete!")
        print(f"Total memories created: {results['total_memories']}")
        print("\nThe neuroscientist now has access to all Level 1 knowledge through the memory system.")
        
    except Exception as e:
        logger.error(f"Knowledge loading failed: {e}")
        raise
    finally:
        await loader.cleanup()


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 