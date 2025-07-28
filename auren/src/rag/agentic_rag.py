"""Agentic RAG implementation based on knowledge base patterns"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, START, END, Crew, Task

from ..agents.biometric_aware_agents import BiometricAwareAgentFactory
from .vector_store import BiometricVectorStore

logger = logging.getLogger(__name__)


class RetrievalStrategy(Enum):
    """RAG retrieval strategies"""

    NAIVE = "naive"  # Simple one-shot retrieval
    ADVANCED = "advanced"  # With re-ranking
    CORRECTIVE = "corrective"  # With quality checking
    AGENTIC = "agentic"  # Full agent-driven


@dataclass
class RetrievalContext:
    """Context for retrieval operations"""

    query: str
    intent: str
    protocols: List[str]
    urgency: str
    user_context: Dict


class AgenticRAG:
    """
    Implements Agentic RAG based on the evolution from knowledge base:
    Naive → Advanced → Modular → Corrective → Agentic
    """

    def __init__(self, strategy: RetrievalStrategy = RetrievalStrategy.AGENTIC):
        self.strategy = strategy
        self.vector_store = BiometricVectorStore()
        self.retrieval_agent = self._create_retrieval_agent()
        self.quality_threshold = 0.7

    def _create_retrieval_agent(self) -> Agent:
        """Create agent for retrieval decisions"""

        return Agent(
            role="Information Retrieval Specialist",
            goal="Retrieve the most relevant information for answering queries",
            backstory="""You are an expert at information retrieval, particularly 
            skilled at understanding user intent and finding relevant data across 
            multiple protocols. You know when to search broadly versus deeply, 
            and can identify when retrieved information is insufficient.""",
            tools=[],  # Will use programmatic retrieval
            verbose=True,
        )

    async def retrieve(self, context: RetrievalContext) -> List[Dict]:
        """Main retrieval method that adapts based on strategy"""

        if self.strategy == RetrievalStrategy.NAIVE:
            return await self._naive_retrieval(context)
        elif self.strategy == RetrievalStrategy.ADVANCED:
            return await self._advanced_retrieval(context)
        elif self.strategy == RetrievalStrategy.CORRECTIVE:
            return await self._corrective_retrieval(context)
        else:  # AGENTIC
            return await self._agentic_retrieval(context)

    async def _naive_retrieval(self, context: RetrievalContext) -> List[Dict]:
        """Simple one-shot retrieval"""

        results = self.vector_store.search(
            query=context.query,
            protocol=context.protocols[0] if context.protocols else None,
            top_k=5,
        )

        return results

    async def _advanced_retrieval(self, context: RetrievalContext) -> List[Dict]:
        """Retrieval with query expansion and re-ranking"""

        # Query expansion
        expanded_queries = await self._expand_query(context.query)

        all_results = []
        for query in expanded_queries:
            results = self.vector_store.search(query, top_k=3)
            all_results.extend(results)

        # Re-rank results
        reranked = await self._rerank_results(all_results, context.query)

        return reranked[:5]

    async def _corrective_retrieval(self, context: RetrievalContext) -> List[Dict]:
        """Retrieval with quality checking and correction"""

        # Initial retrieval
        results = await self._advanced_retrieval(context)

        # Evaluate quality
        quality_scores = await self._evaluate_retrieval_quality(results, context)

        # If quality is low, try alternative strategies
        if max(quality_scores) < self.quality_threshold:
            logger.info("Low quality retrieval, attempting correction")

            # Try different protocols
            corrected_results = []
            for protocol in ["journal", "mirage", "convergence"]:
                if protocol not in context.protocols:
                    additional = self.vector_store.search(context.query, protocol=protocol, top_k=2)
                    corrected_results.extend(additional)

            # Re-evaluate
            all_results = results + corrected_results
            quality_scores = await self._evaluate_retrieval_quality(all_results, context)

            # Select best results
            scored_results = list(zip(all_results, quality_scores))
            scored_results.sort(key=lambda x: x[1], reverse=True)

            return [r[0] for r in scored_results[:5]]

        return results

    async def _agentic_retrieval(self, context: RetrievalContext) -> List[Dict]:
        """Full agentic retrieval with reasoning loop"""

        logger.info("Starting agentic retrieval")

        # Step 1: Plan - Agent decomposes the query
        planning_task = # Task migrated to node in StateGraph
        # Original params: description=f"""
            Analyze this query and create a retrieval plan:
            Query: {context.query}
            Intent: {context.intent}
            Urgency: {context.urgency}
            
            Break down what information is needed and from which protocols.
            Consider if multiple retrieval passes might be needed.
            """,
            agent=self.retrieval_agent,
            expected_output="Retrieval plan with specific information needs",
        

        planning_crew = StateGraph(dict)
        
        # Build graph from agents and tasks
        for agent in self.agents:
            workflow.add_node(agent.name, agent.process)
        
        # Connect nodes
        workflow.add_edge(START, self.agents[0].name)
        for i in range(len(self.agents) - 1):
            workflow.add_edge(self.agents[i].name, self.agents[i+1].name)
        workflow.add_edge(self.agents[-1].name, END)
        
        return workflow.compile()

        plan = await planning_crew.kickoff_async()

        # Step 2: Retrieve - Execute retrieval based on plan
        results = []

        # Determine protocols to search
        if "journal" in plan.lower() or "peptide" in plan.lower():
            journal_results = self.vector_store.search(context.query, protocol="journal", top_k=3)
            results.extend(journal_results)

        if "mirage" in plan.lower() or "visual" in plan.lower() or "biometric" in plan.lower():
            mirage_results = self.vector_store.search(context.query, protocol="mirage", top_k=3)
            results.extend(mirage_results)

        if "convergence" in plan.lower() or "correlation" in plan.lower():
            convergence_results = self.vector_store.search(
                context.query, protocol="convergence", top_k=2
            )
            results.extend(convergence_results)

        # Step 3: Reason - Analyze retrieved information
        analysis_task = # Task migrated to node in StateGraph
        # Original params: description=f"""
            Analyze these retrieved documents for relevance to the query:
            Query: {context.query}
            
            Retrieved documents:
            {self._format_results_for_agent(results}
            
            Identify:
            1. Which documents are most relevant
            2. What information is still missing
            3. Whether we need additional retrieval
            """,
            agent=self.retrieval_agent,
            expected_output="Analysis of retrieval quality and gaps",
        )

        analysis_crew = StateGraph(dict)
        
        # Build graph from agents and tasks
        for agent in self.agents:
            workflow.add_node(agent.name, agent.process)
        
        # Connect nodes
        workflow.add_edge(START, self.agents[0].name)
        for i in range(len(self.agents) - 1):
            workflow.add_edge(self.agents[i].name, self.agents[i+1].name)
        workflow.add_edge(self.agents[-1].name, END)
        
        return workflow.compile()

        analysis = await analysis_crew.kickoff_async()

        # Step 4: Refine - If needed, perform additional retrieval
        if "additional retrieval" in analysis.lower() or "missing" in analysis.lower():
            logger.info("Agent requested additional retrieval")

            # Perform targeted retrieval based on gaps
            refinement_task = # Task migrated to node in StateGraph
        # Original params: description=f"""
                Based on the gaps identified, create a refined search query:
                Original query: {context.query}
                Gaps: {analysis}
                
                Generate a more specific query to find the missing information.
                """,
                agent=self.retrieval_agent,
                expected_output="Refined search query",
            

            refinement_crew = StateGraph(dict)
        
        # Build graph from agents and tasks
        for agent in self.agents:
            workflow.add_node(agent.name, agent.process)
        
        # Connect nodes
        workflow.add_edge(START, self.agents[0].name)
        for i in range(len(self.agents) - 1):
            workflow.add_edge(self.agents[i].name, self.agents[i+1].name)
        workflow.add_edge(self.agents[-1].name, END)
        
        return workflow.compile()

            refined_query = await refinement_crew.kickoff_async()

            # Execute refined search
            additional_results = self.vector_store.search(refined_query.strip(), top_k=3)
            results.extend(additional_results)

        # Step 5: Final ranking and selection
        final_results = await self._rerank_results(results, context.query)

        return final_results[:5]

    async def _expand_query(self, query: str) -> List[str]:
        """Expand query for better retrieval"""

        # Simple expansion for now
        expansions = [query]

        # Add protocol-specific expansions
        if "ptosis" in query.lower():
            expansions.append("eye drooping eyelid asymmetry")
        if "inflammation" in query.lower():
            expansions.append("facial puffiness swelling edema")
        if "peptide" in query.lower():
            expansions.append("compound dosing protocol cycle")

        return expansions

    async def _rerank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Re-rank results based on relevance"""

        # Simple re-ranking by distance
        # In production, use cross-encoder or more sophisticated ranking

        unique_results = []
        seen_ids = set()

        for result in sorted(results, key=lambda x: x["distance"]):
            if result["id"] not in seen_ids:
                unique_results.append(result)
                seen_ids.add(result["id"])

        return unique_results

    async def _evaluate_retrieval_quality(
        self, results: List[Dict], context: RetrievalContext
    ) -> List[float]:
        """Evaluate quality of retrieved documents"""

        scores = []

        for result in results:
            # Simple scoring based on distance and metadata
            distance_score = 1 - result["distance"]

            # Boost score if protocol matches intent
            protocol_match = 0
            if context.intent == "peptide" and result["metadata"].get("protocol") == "journal":
                protocol_match = 0.2
            elif context.intent == "visual" and result["metadata"].get("protocol") == "mirage":
                protocol_match = 0.2

            # Recency boost
            try:
                timestamp = datetime.fromisoformat(result["metadata"].get("timestamp", ""))
                age_days = (datetime.now() - timestamp).days
                recency_score = max(0, 1 - (age_days / 30))  # Decay over 30 days
            except:
                recency_score = 0.5

            # Combine scores
            total_score = (distance_score * 0.6) + (protocol_match * 0.2) + (recency_score * 0.2)
            scores.append(total_score)

        return scores

    def _format_results_for_agent(self, results: List[Dict]) -> str:
        """Format retrieval results for agent consumption"""

        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(
                f"""
Document {i}:
Protocol: {result['metadata'].get('protocol', 'unknown')}
Type: {result['metadata'].get('entry_type', 'unknown')}
Content: {result['document'][:200]}...
"""
            )

        return "\n".join(formatted)

    async def retrieve_with_context(
        self, query: str, user_context: Dict, urgency: str = "normal"
    ) -> Dict:
        """High-level retrieval with full context"""

        # Determine intent from query
        intent = self._determine_intent(query)

        # Determine relevant protocols
        protocols = self._determine_protocols(query, intent)

        # Create retrieval context
        context = RetrievalContext(
            query=query,
            intent=intent,
            protocols=protocols,
            urgency=urgency,
            user_context=user_context,
        )

        # Perform retrieval
        results = await self.retrieve(context)

        # Format response
        return {
            "query": query,
            "intent": intent,
            "results": results,
            "metadata": {
                "strategy": self.strategy.value,
                "protocols_searched": protocols,
                "result_count": len(results),
            },
        }

    def _determine_intent(self, query: str) -> str:
        """Determine query intent"""

        query_lower = query.lower()

        if any(word in query_lower for word in ["peptide", "dose", "compound", "cycle"]):
            return "peptide"
        elif any(word in query_lower for word in ["ptosis", "inflammation", "facial", "visual"]):
            return "visual"
        elif any(word in query_lower for word in ["correlation", "relationship", "impact"]):
            return "convergence"
        else:
            return "general"

    def _determine_protocols(self, query: str, intent: str) -> List[str]:
        """Determine which protocols to search"""

        if intent == "peptide":
            return ["journal", "convergence"]
        elif intent == "visual":
            return ["mirage", "visor", "convergence"]
        elif intent == "convergence":
            return ["convergence", "journal", "mirage"]
        else:
            return ["journal", "mirage", "convergence"]
