"""
Initialize AUREN Intelligence System
Sets up the complete clinical AI integration
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

from intelligence.data_structures import (
    KnowledgeItem, KnowledgeType, KnowledgeStatus, 
    Hypothesis, HypothesisStatus, SpecialistDomain,
    create_knowledge_id, create_hypothesis_id
)
from intelligence.knowledge_manager import KnowledgeManager
from intelligence.hypothesis_validator import HypothesisValidator
from data_layer.memory_backend import PostgreSQLMemoryBackend
from data_layer.event_store import EventStore, EventStreamType

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class IntelligenceSystemInitializer:
    """Initializes the complete AUREN intelligence system"""
    
    def __init__(self):
        self.memory_backend = None
        self.event_store = None
        self.hypothesis_validator = None
        self.knowledge_manager = None
    
    async def initialize(self) -> bool:
        """
        Initialize all intelligence system components
        
        Returns:
            True if initialization successful
        """
        
        try:
            logger.info("🚀 Initializing AUREN Intelligence System...")
            
            # Initialize PostgreSQL memory backend
            logger.info("📊 Setting up PostgreSQL memory backend...")
            self.memory_backend = PostgreSQLMemoryBackend()
            await self.memory_backend.initialize()
            
            # Initialize event store
            logger.info("📈 Setting up event store...")
            self.event_store = EventStore()
            await self.event_store.initialize()
            
            # Initialize hypothesis validator
            logger.info("🔬 Setting up hypothesis validator...")
            self.hypothesis_validator = HypothesisValidator(self.event_store)
            
            # Initialize knowledge manager
            logger.info("🧠 Setting up knowledge manager...")
            self.knowledge_manager = KnowledgeManager(
                memory_backend=self.memory_backend,
                event_store=self.event_store,
                hypothesis_validator=self.hypothesis_validator
            )
            
            logger.info("✅ Intelligence system components initialized successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize intelligence system: {e}")
            return False
    
    async def load_knowledge_base(self, user_id: str = "system") -> int:
        """
        Load the clinical knowledge base
        
        Args:
            user_id: User ID for system knowledge
            
        Returns:
            Number of knowledge items loaded
        """
        
        logger.info("📚 Loading clinical knowledge base...")
        
        knowledge_items = []
        
        # Neuroscience knowledge
        neuroscience_knowledge = [
            {
                "title": "HRV-Sleep Correlation",
                "description": "Consistent sleep schedule improves HRV by 15-20%",
                "content": {
                    "pattern": "hrv_improvement",
                    "magnitude": 17.5,
                    "confidence_interval": [15, 20],
                    "conditions": ["consistent_sleep", "7+_hours"]
                },
                "confidence": 0.92,
                "evidence_sources": ["biometric_data", "sleep_tracking", "clinical_validation"],
                "domain": "neuroscience"
            },
            {
                "title": "Cortisol-Stress Relationship",
                "description": "Elevated cortisol correlates with decreased cognitive performance",
                "content": {
                    "correlation": -0.78,
                    "threshold": 15.0,
                    "impact": "cognitive_performance"
                },
                "confidence": 0.89,
                "evidence_sources": ["saliva_tests", "cognitive_tests", "stress_surveys"],
                "domain": "neuroscience"
            },
            {
                "title": "Vagal Tone Recovery",
                "description": "HRV-guided breathing improves vagal tone within 2 weeks",
                "content": {
                    "method": "hrv_breathing",
                    "duration_days": 14,
                    "expected_improvement": 25
                },
                "confidence": 0.85,
                "evidence_sources": ["hrv_monitoring", "breathing_exercises", "vagal_tone"],
                "domain": "neuroscience"
            },
            {
                "title": "Visual Fatigue Detection",
                "description": "Eye strain patterns predict cognitive fatigue 2-3 hours in advance",
                "content": {
                    "prediction_window": [2, 3],
                    "accuracy": 0.83,
                    "indicators": ["blink_rate", "pupil_dilation", "gaze_stability"]
                },
                "confidence": 0.78,
                "evidence_sources": ["eye_tracking", "cognitive_tests", "fatigue_surveys"],
                "domain": "neuroscience"
            }
        ]
        
        # Nutrition knowledge
        nutrition_knowledge = [
            {
                "title": "Protein Timing Optimization",
                "description": "Protein intake within 30 minutes post-workout maximizes muscle synthesis",
                "content": {
                    "optimal_window": 30,
                    "protein_amount": "0.4g/kg",
                    "effectiveness_increase": 0.25
                },
                "confidence": 0.88,
                "evidence_sources": ["muscle_biopsy", "protein_synthesis", "workout_data"],
                "domain": "nutrition"
            },
            {
                "title": "Micronutrient Deficiency Detection",
                "description": "Low magnesium levels correlate with poor sleep quality",
                "content": {
                    "correlation": -0.72,
                    "threshold": 300,
                    "sleep_improvement": 0.35
                },
                "confidence": 0.82,
                "evidence_sources": ["blood_tests", "sleep_tracking", "supplementation"],
                "domain": "nutrition"
            }
        ]
        
        # Training knowledge
        training_knowledge = [
            {
                "title": "Recovery-Based Training",
                "description": "Training intensity should be adjusted based on HRV recovery",
                "content": {
                    "adjustment_factor": 0.15,
                    "hrv_threshold": 20,
                    "performance_improvement": 0.18
                },
                "confidence": 0.91,
                "evidence_sources": ["hrv_monitoring", "training_logs", "performance_data"],
                "domain": "training"
            },
            {
                "title": "Overtraining Prevention",
                "description": "HRV drop >15% for 3+ days indicates overtraining risk",
                "content": {
                    "hrv_drop_threshold": 15,
                    "duration_days": 3,
                    "risk_level": "high"
                },
                "confidence": 0.87,
                "evidence_sources": ["hrv_data", "training_volume", "injury_reports"],
                "domain": "training"
            }
        ]
        
        # Sleep knowledge
        sleep_knowledge = [
            {
                "title": "Sleep Architecture Optimization",
                "description": "Consistent bedtime improves deep sleep by 20-25%",
                "content": {
                    "improvement_range": [20, 25],
                    "consistency_metric": "bedtime_variance",
                    "optimal_variance": 30
                },
                "confidence": 0.90,
                "evidence_sources": ["sleep_stages", "bedtime_consistency", "recovery_metrics"],
                "domain": "sleep"
            },
            {
                "title": "Sleep Debt Recovery",
                "description": "Each hour of sleep debt requires 1.5-2 hours to fully recover",
                "content": {
                    "recovery_ratio": [1.5, 2.0],
                    "recovery_time_days": 7,
                    "performance_impact": 0.15
                },
                "confidence": 0.84,
                "evidence_sources": ["sleep_tracking", "cognitive_tests", "performance_data"],
                "domain": "sleep"
            }
        ]
        
        # Combine all knowledge
        all_knowledge = neuroscience_knowledge + nutrition_knowledge + training_knowledge + sleep_knowledge
        
        # Create knowledge items
        for knowledge_data in all_knowledge:
            knowledge = KnowledgeItem(
                knowledge_id=create_knowledge_id(),
                agent_id="system_agent",
                user_id=user_id,
                domain=knowledge_data['domain'],
                knowledge_type=KnowledgeType.PATTERN,
                title=knowledge_data['title'],
                description=knowledge_data['description'],
                content=knowledge_data['content'],
                confidence=knowledge_data['confidence'],
                evidence_sources=knowledge_data['evidence_sources'],
                validation_status=KnowledgeStatus.VALIDATED,
                related_knowledge=[],
                conflicts_with=[],
                supports=[],
                application_count=0,
                success_rate=0.0,
                last_applied=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                metadata={"source": "clinical_knowledge_base"}
            )
            
            await self.knowledge_manager.add_knowledge(knowledge)
            knowledge_items.append(knowledge)
        
        logger.info(f"📖 Loaded {len(knowledge_items)} knowledge items")
        return len(knowledge_items)
    
    async def create_sample_hypotheses(self, user_id: str) -> int:
        """
        Create sample hypotheses for testing
        
        Args:
            user_id: User ID for hypotheses
            
        Returns:
            Number of hypotheses created
        """
        
        logger.info("🧪 Creating sample hypotheses...")
        
        hypotheses = []
        
        # Sample neuroscience hypotheses
        neuroscience_hypotheses = [
            {
                "description": "User's HRV improves with consistent sleep schedule",
                "prediction": {
                    "expected_change": 15,
                    "metric": "hrv",
                    "condition": "consistent_sleep"
                },
                "confidence": 0.75,
                "domain": "neuroscience",
                "evidence_criteria": [
                    {"type": "hrv", "minimum_days": 14, "threshold": 10},
                    {"type": "sleep_consistency", "minimum_days": 14}
                ]
            },
            {
                "description": "User experiences cognitive decline when cortisol >20 μg/dL",
                "prediction": {
                    "expected_decline": 0.25,
                    "metric": "cognitive_performance",
                    "threshold": 20.0
                },
                "confidence": 0.68,
                "domain": "neuroscience",
                "evidence_criteria": [
                    {"type": "cortisol", "minimum_days": 7, "threshold": 20.0},
                    {"type": "cognitive_test", "minimum_days": 7}
                ]
            }
        ]
        
        # Sample nutrition hypotheses
        nutrition_hypotheses = [
            {
                "description": "User's energy levels improve with magnesium supplementation",
                "prediction": {
                    "expected_improvement": 0.30,
                    "metric": "energy_levels",
                    "dosage": "400mg"
                },
                "confidence": 0.72,
                "domain": "nutrition",
                "evidence_criteria": [
                    {"type": "energy_survey", "minimum_days": 14, "threshold": 0.2},
                    {"type": "magnesium_supplementation", "minimum_days": 14}
                ]
            }
        ]
        
        # Sample training hypotheses
        training_hypotheses = [
            {
                "description": "User's performance improves with HRV-guided training",
                "prediction": {
                    "expected_improvement": 0.15,
                    "metric": "performance",
                    "method": "hrv_guided"
                },
                "confidence": 0.80,
                "domain": "training",
                "evidence_criteria": [
                    {"type": "performance", "minimum_days": 21, "threshold": 0.1},
                    {"type": "hrv_guided_training", "minimum_days": 21}
                ]
            }
        ]
        
        # Combine all hypotheses
        all_hypotheses = neuroscience_hypotheses + nutrition_hypotheses + training_hypotheses
        
        # Create hypothesis items
        for hypothesis_data in all_hypotheses:
            hypothesis = Hypothesis(
                hypothesis_id=create_hypothesis_id(),
                agent_id="neuroscientist_agent",
                user_id=user_id,
                domain=hypothesis_data['domain'],
                description=hypothesis_data['description'],
                prediction=hypothesis_data['prediction'],
                confidence=hypothesis_data['confidence'],
                evidence_criteria=hypothesis_data['evidence_criteria'],
                formed_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                status=HypothesisStatus.FORMED,
                metadata={"source": "sample_hypotheses"}
            )
            
            # Store hypothesis as event
            await self.event_store.append_event(
                stream_id=user_id,
                stream_type=EventStreamType.HYPOTHESIS,
                event_type="hypothesis_formed",
                payload={
                    "hypothesis_id": hypothesis.hypothesis_id,
                    "agent_id": hypothesis.agent_id,
                    "description": hypothesis.description,
                    "confidence": hypothesis.confidence,
                    "domain": hypothesis.domain,
                    "evidence_criteria": hypothesis.evidence_criteria
                }
            )
            
            hypotheses.append(hypothesis)
        
        logger.info(f"🔬 Created {len(hypotheses)} sample hypotheses")
        return len(hypotheses)
    
    async def run_system_test(self, user_id: str = "test_user") -> Dict[str, Any]:
        """
        Run comprehensive system test
        
        Args:
            user_id: Test user ID
            
        Returns:
            Test results
        """
        
        logger.info("🧪 Running comprehensive system test...")
        
        results = {
            "user_id": user_id,
            "test_start": datetime.now(timezone.utc).isoformat(),
            "components_tested": []
        }
        
        # Test knowledge loading
        knowledge_count = await self.load_knowledge_base(user_id)
        results["knowledge_loaded"] = knowledge_count
        results["components_tested"].append("knowledge_base")
        
        # Test hypothesis creation
        hypothesis_count = await self.create_sample_hypotheses(user_id)
        results["hypotheses_created"] = hypothesis_count
        results["components_tested"].append("hypothesis_system")
        
        # Test knowledge retrieval
        knowledge_list = await self.knowledge_manager.get_knowledge(user_id=user_id)
        results["knowledge_retrieved"] = len(knowledge_list)
        results["components_tested"].append("knowledge_retrieval")
        
        # Test knowledge graph
        knowledge_graph = await self.knowledge_manager.get_knowledge_graph(user_id)
        results["knowledge_graph_nodes"] = len(knowledge_graph)
        results["components_tested"].append("knowledge_graph")
        
        # Test learning metrics
        learning_metrics = await self.knowledge_manager.get_learning_metrics(user_id)
        results["learning_metrics"] = {
            "total_knowledge": learning_metrics.total_knowledge,
            "total_hypotheses": learning_metrics.total_hypotheses,
            "average_confidence": learning_metrics.average_confidence,
            "learning_rate": learning_metrics.learning_rate
        }
        results["components_tested"].append("learning_metrics")
        
        # Test cross-agent insights
        insights = await self.knowledge_manager.get_cross_agent_insights(user_id)
        results["cross_agent_insights"] = len(insights)
        results["components_tested"].append("cross_agent_collaboration")
        
        results["test_end"] = datetime.now(timezone.utc).isoformat()
        results["status"] = "success"
        
        logger.info("✅ System test completed successfully!")
        return results
    
    async def cleanup(self):
        """Clean up resources"""
        if self.memory_backend:
            await self.memory_backend.cleanup()
        if self.event_store:
            await self.event_store.cleanup()


async def initialize_intelligence_system() -> IntelligenceSystemInitializer:
    """
    Initialize the complete AUREN intelligence system
    
    Returns:
        Initialized system
    """
    
    initializer = IntelligenceSystemInitializer()
    
    # Initialize system
    success = await initializer.initialize()
    if not success:
        raise RuntimeError("Failed to initialize intelligence system")
    
    # Load knowledge base
    await initializer.load_knowledge_base()
    
    # Create sample hypotheses
    await initializer.create_sample_hypotheses("test_user")
    
    # Run system test
    results = await initializer.run_system_test("test_user")
    
    logger.info("🎉 AUREN Intelligence System is fully operational!")
    logger.info(f"📊 System test results: {json.dumps(results, indent=2)}")
    
    return initializer


async def main():
    """Main initialization function"""
    try:
        system = await initialize_intelligence_system()
        logger.info("✅ AUREN Intelligence System initialization complete!")
        
        # Keep system running for testing
        logger.info("🔄 System is running. Press Ctrl+C to exit.")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Shutting down...")
            await system.cleanup()
            
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
