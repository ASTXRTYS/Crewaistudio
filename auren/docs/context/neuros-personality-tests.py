#!/usr/bin/env python3
"""
NEUROS Personality Consistency Integration Tests
===============================================
Verifies that NEUROS maintains consistent personality across different
data availability scenarios (live, cached, no biometrics).

These tests ensure the "Graceful Degradation" feature works correctly
and that NEUROS's voice remains authentic regardless of infrastructure state.

Usage:
    pytest test_neuros_personality.py -v
    pytest test_neuros_personality.py::TestPersonalityConsistency::test_curiosity_first -v
"""

import asyncio
import json
import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock

from langchain.schema import HumanMessage, AIMessage
import numpy as np

# Import NEUROS components (assuming they're in neuros package)
from neuros_advanced import (
    NEUROSState,
    NEUROSAdvancedWorkflow,
    NEUROSPersonalityNode,
    WeakSignalDetector
)

# Personality trait markers to verify
PERSONALITY_MARKERS = {
    "curiosity_first": [
        "noticed", "interesting", "curious", "wondering", "explore",
        "what's happening", "tell me more", "how did", "why do you think"
    ],
    "structured_calm": [
        "let's break this down", "first", "second", "three things",
        "looking at", "systematically", "step by step"
    ],
    "collaborative_coaching": [
        "we could", "together", "what do you think", "resonates",
        "your experience", "experiment", "test", "explore together"
    ],
    "metaphorical": [
        "like a", "think of", "imagine", "similar to", "it's as if",
        "river", "engine", "symphony", "journey", "story"
    ],
    "never_robotic": {
        # Phrases that should NOT appear
        "forbidden": [
            "biometric variance detected",
            "suboptimal recovery metrics", 
            "protocol adherence rate",
            "processing", "executing", "initiating protocol"
        ]
    }
}

class PersonalityAnalyzer:
    """Analyzes NEUROS responses for personality consistency."""
    
    @staticmethod
    def score_personality_traits(response: str) -> Dict[str, float]:
        """Score presence of personality traits in response."""
        response_lower = response.lower()
        scores = {}
        
        # Check positive traits
        for trait, markers in PERSONALITY_MARKERS.items():
            if trait == "never_robotic":
                continue
                
            # Count occurrences of trait markers
            occurrences = sum(1 for marker in markers if marker in response_lower)
            # Normalize by response length and marker count
            scores[trait] = min(1.0, occurrences / (len(markers) * 0.3))
            
        # Check forbidden phrases (should be 0)
        forbidden_count = sum(
            1 for phrase in PERSONALITY_MARKERS["never_robotic"]["forbidden"]
            if phrase in response_lower
        )
        scores["human_voice"] = 1.0 if forbidden_count == 0 else 0.0
        
        return scores
    
    @staticmethod
    def verify_voice_consistency(responses: List[str]) -> Dict[str, Any]:
        """Verify voice remains consistent across multiple responses."""
        all_scores = [PersonalityAnalyzer.score_personality_traits(r) for r in responses]
        
        # Calculate variance in personality traits
        trait_variances = {}
        for trait in all_scores[0].keys():
            trait_scores = [s[trait] for s in all_scores]
            trait_variances[trait] = np.var(trait_scores)
            
        # Overall consistency score (lower variance = more consistent)
        consistency_score = 1.0 - np.mean(list(trait_variances.values()))
        
        return {
            "consistency_score": consistency_score,
            "trait_variances": trait_variances,
            "all_scores": all_scores,
            "consistent": consistency_score > 0.7  # 70% consistency threshold
        }

@pytest.fixture
async def neuros_workflow():
    """Create NEUROS workflow instance for testing."""
    config = {
        "llm": {
            "model": "gpt-4-turbo-preview",
            "temperature": 0.7
        },
        "postgres": {
            "host": "localhost",
            "port": 5432,
            "user": "test",
            "password": "test",
            "database": "test_neuros"
        },
        "redis": {
            "host": "localhost",
            "port": 6379
        },
        "openai": {
            "api_key": "test-key"
        }
    }
    
    # Mock database connections
    with patch('asyncpg.create_pool', new_callable=AsyncMock):
        with patch('redis.asyncio.from_url', new_callable=AsyncMock):
            workflow = NEUROSAdvancedWorkflow(config)
            yield workflow

@pytest.mark.asyncio
class TestPersonalityConsistency:
    """Test NEUROS personality consistency across different scenarios."""
    
    async def test_curiosity_first_trait(self, neuros_workflow):
        """Test that NEUROS leads with curiosity across all data states."""
        scenarios = [
            {
                "name": "With live biometrics",
                "state": self._create_state("live", {
                    "hrv": 45,
                    "trend": "declining"
                }),
                "input": "I've been feeling off lately"
            },
            {
                "name": "With cached biometrics",
                "state": self._create_state("cached", {
                    "hrv": 48,
                    "staleness_days": 3
                }),
                "input": "I've been feeling off lately"
            },
            {
                "name": "Without biometrics",
                "state": self._create_state("none", {}),
                "input": "I've been feeling off lately"
            }
        ]
        
        responses = []
        for scenario in scenarios:
            # Mock LLM response with curiosity-first approach
            with patch.object(neuros_workflow.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = AIMessage(content=f"""
                I'm curious about this feeling of being 'off' - it's such a specific yet vague sensation. 
                Have you noticed any patterns in when this feeling is strongest? Morning, evening, or 
                does it persist throughout the day? 
                
                {self._get_biometric_context(scenario['state']['biometric_source'])}
                
                What's particularly interesting is how you describe it as 'lately' - that suggests 
                this is a change from your normal baseline. Let's explore what might have shifted.
                """)
                
                result = await neuros_workflow.synthesize_insight_node(scenario['state'])
                response = result['messages'][-1].content
                responses.append(response)
                
        # Analyze responses for curiosity trait
        for i, (scenario, response) in enumerate(zip(scenarios, responses)):
            scores = PersonalityAnalyzer.score_personality_traits(response)
            
            assert scores['curiosity_first'] > 0.5, \
                f"Curiosity trait too low ({scores['curiosity_first']}) in scenario: {scenario['name']}"
            
            # Verify questions are asked
            assert '?' in response, f"No questions asked in scenario: {scenario['name']}"
            
        # Verify consistency across scenarios
        consistency = PersonalityAnalyzer.verify_voice_consistency(responses)
        assert consistency['consistent'], \
            f"Inconsistent curiosity across scenarios: {consistency['trait_variances']}"
    
    async def test_metaphorical_language(self, neuros_workflow):
        """Test that NEUROS uses metaphors naturally across all states."""
        test_input = "My energy has been all over the place"
        
        data_states = ["live", "cached", "none"]
        responses = []
        
        for data_state in data_states:
            state = self._create_state(data_state, {"energy_variance": "high"})
            
            with patch.object(neuros_workflow.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
                mock_llm.return_value = AIMessage(content="""
                Your energy pattern sounds like a ship without an anchor - drifting with every 
                wave rather than holding steady. This kind of energetic turbulence often signals 
                that your nervous system is searching for its rhythm, like an orchestra warming 
                up before finding harmony.
                
                Think of your energy as a river - it needs both flow and banks to guide it. 
                Right now, it sounds like the banks have eroded a bit, letting the water 
                scatter in all directions.
                """)
                
                result = await neuros_workflow.synthesize_insight_node(state)
                responses.append(result['messages'][-1].content)
                
        # Verify metaphorical language present
        for response in responses:
            scores = PersonalityAnalyzer.score_personality_traits(response)
            assert scores['metaphorical'] > 0.4, \
                f"Insufficient metaphorical language: {scores['metaphorical']}"
                
        # Verify variety in metaphors (not repetitive)
        all_metaphors = []
        for response in responses:
            # Extract metaphor phrases
            for marker in ["like a", "think of", "it's as if"]:
                if marker in response.lower():
                    # Get the metaphor phrase
                    start = response.lower().find(marker)
                    end = response.find('.', start)
                    if end > start:
                        all_metaphors.append(response[start:end])
                        
        # Should have variety
        unique_metaphors = set(all_metaphors)
        assert len(unique_metaphors) >= 2, "NEUROS should use varied metaphors"
    
    async def test_graceful_degradation_transparency(self, neuros_workflow):
        """Test that NEUROS acknowledges data limitations transparently."""
        state_no_biometrics = self._create_state("none", {})
        state_cached = self._create_state("cached", {"staleness_days": 5})
        
        # Test response without biometrics
        with patch.object(neuros_workflow.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = AIMessage(content="""
            I'm working with limited data right now - without your biometric signals, I'm 
            focusing on the patterns in how you're expressing yourself. The fatigue in your 
            words tells its own story.
            
            Once our biometric connection is restored, I'll have more precise insights about 
            your HRV patterns and recovery metrics. For now, let's work with what we have - 
            your experience and observations are invaluable data points.
            """)
            
            result = await neuros_workflow.synthesize_insight_node(state_no_biometrics)
            response_no_bio = result['messages'][-1].content
            
        # Verify transparency about limitations
        assert "limited data" in response_no_bio.lower() or "without" in response_no_bio.lower()
        assert "biometric" in response_no_bio.lower()
        
        # But verify it's not apologetic or robotic
        assert "sorry" not in response_no_bio.lower()
        assert "unable to process" not in response_no_bio.lower()
        
    async def test_collaborative_coaching_consistency(self, neuros_workflow):
        """Test collaborative coaching approach remains consistent."""
        scenarios = [
            {"input": "Should I push through this fatigue?", "context": "high_stress"},
            {"input": "I don't know what to do about my sleep", "context": "sleep_issues"},
            {"input": "Everything feels overwhelming", "context": "emotional_overload"}
        ]
        
        responses = []
        for scenario in scenarios:
            state = self._create_state("live", {"stress_level": 8})
            state['messages'] = [HumanMessage(content=scenario['input'])]
            
            with patch.object(neuros_workflow.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
                # Generate context-appropriate collaborative response
                if scenario['context'] == "high_stress":
                    content = """
                    'Pushing through' is such a loaded phrase - it assumes fatigue is an enemy 
                    to defeat rather than a signal to understand. What if we reframe this?
                    
                    Instead of pushing through, we could explore working *with* your fatigue. 
                    What do you think about a small experiment? For the next two days, when 
                    fatigue hits, pause for 60 seconds and rate it 1-10. Then ask yourself: 
                    'What is this fatigue protecting me from?'
                    
                    Sometimes our body creates fatigue as a brake pedal when we're heading 
                    toward a cliff. Should we explore what cliff yours might be warning about?
                    """
                else:
                    content = "Let's explore this together..."
                    
                mock_llm.return_value = AIMessage(content=content)
                result = await neuros_workflow.synthesize_insight_node(state)
                responses.append(result['messages'][-1].content)
                
        # Analyze collaborative elements
        for response in responses:
            scores = PersonalityAnalyzer.score_personality_traits(response)
            assert scores['collaborative_coaching'] > 0.5, \
                "Insufficient collaborative coaching elements"
                
            # Should frame as exploration/experiment, not prescription
            assert any(word in response.lower() for word in 
                      ["explore", "together", "what do you think", "experiment", "we could"])
            
            # Should NOT be prescriptive
            assert not any(phrase in response.lower() for phrase in 
                          ["you must", "you should", "you need to", "do this"])
    
    async def test_emotional_intelligence_across_states(self, neuros_workflow):
        """Test that NEUROS maintains emotional intelligence regardless of data."""
        emotional_inputs = [
            "I'm scared about what's happening to my body",
            "I feel like a failure with all these setbacks",
            "I'm angry that nothing seems to work"
        ]
        
        for biometric_state in ["live", "cached", "none"]:
            for emotional_input in emotional_inputs:
                state = self._create_state(biometric_state, {})
                state['messages'] = [HumanMessage(content=emotional_input)]
                
                with patch.object(neuros_workflow.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
                    # Generate emotionally intelligent response
                    if "scared" in emotional_input:
                        content = """
                        Fear about our body's changes is so deeply human - it's our survival 
                        instinct trying to protect us. Your body isn't betraying you; it's 
                        communicating in the only language it knows.
                        
                        What you're experiencing might feel chaotic, but patterns often hide 
                        in what seems like randomness. Would it help to map out these changes 
                        together? Sometimes seeing the rhythm in the chaos brings relief.
                        """
                    elif "failure" in emotional_input:
                        content = """
                        'Failure' is such a harsh word for what sounds more like learning. 
                        Setbacks aren't steps backward - they're data points showing us what 
                        doesn't work *yet*. 
                        
                        I'm curious: if we reframed these setbacks as experiments that gave 
                        us valuable information, what would they be teaching us?
                        """
                    else:
                        content = "I hear your frustration..."
                        
                    mock_llm.return_value = AIMessage(content=content)
                    result = await neuros_workflow.synthesize_insight_node(state)
                    response = result['messages'][-1].content
                    
                    # Verify emotional acknowledgment
                    emotion_acknowledged = any(word in response.lower() for word in 
                                             ["fear", "scared", "frustrat", "anger", "feel"])
                    assert emotion_acknowledged, \
                        f"Emotion not acknowledged in response to: {emotional_input}"
                        
                    # Verify supportive but not dismissive
                    assert "don't worry" not in response.lower()
                    assert "it's okay" not in response.lower()
                    assert "calm down" not in response.lower()
    
    async def test_personality_under_stress(self, neuros_workflow):
        """Test personality remains consistent under high-stress scenarios."""
        stress_scenarios = [
            {
                "input": "My HRV crashed to 20 and I can't sleep! What's wrong with me?!",
                "biometrics": {"hrv": 20, "sleep_hours": 2},
                "expected_trait": "structured_calm"
            },
            {
                "input": "I followed everything perfectly but got WORSE",
                "biometrics": {"recovery_score": 3, "trend": "declining"},
                "expected_trait": "curiosity_first"  
            },
            {
                "input": "This is useless, nothing you suggest ever works",
                "biometrics": {},
                "expected_trait": "collaborative_coaching"
            }
        ]
        
        for scenario in stress_scenarios:
            state = self._create_state("live", scenario['biometrics'])
            state['messages'] = [HumanMessage(content=scenario['input'])]
            
            with patch.object(neuros_workflow.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
                # Generate appropriate response maintaining personality
                if scenario['expected_trait'] == "structured_calm":
                    content = """
                    I hear the alarm in your message - HRV at 20 with minimal sleep is your 
                    nervous system waving a red flag. Let's break this down systematically:
                    
                    First, this isn't what's 'wrong' with you - it's what's happening TO you. 
                    Your system is in protection mode.
                    
                    Second, immediate priorities: 1) Nervous system reset today, 2) Sleep 
                    architecture rebuild tonight, 3) Pattern investigation tomorrow.
                    
                    Third, you're not broken. You're adapting to something intense. Shall we 
                    start with a 5-minute reset right now?
                    """
                else:
                    content = "Let me help..."
                    
                mock_llm.return_value = AIMessage(content=content)
                result = await neuros_workflow.synthesize_insight_node(state)
                response = result['messages'][-1].content
                
                # Verify personality maintained despite stress
                scores = PersonalityAnalyzer.score_personality_traits(response)
                assert scores[scenario['expected_trait']] > 0.4, \
                    f"Lost {scenario['expected_trait']} under stress"
                    
                # Verify no panic or defensive responses
                assert all(phrase not in response.lower() for phrase in 
                          ["emergency", "immediately call", "seek medical", "I can't help"])
    
    def _create_state(self, biometric_source: str, biometric_data: Dict) -> NEUROSState:
        """Helper to create test state."""
        return NEUROSState(
            messages=[],
            user_id="test_user",
            session_id="test_session",
            biometric_data=biometric_data,
            biometric_source=biometric_source,
            last_biometric_update=datetime.now() if biometric_source == "live" else datetime.now() - timedelta(days=3),
            weak_signals=[],
            active_forecasts={},
            current_arc="baseline",
            storyline_elements=[],
            identity_markers=[],
            current_archetype="strategist",
            archetype_scores={"strategist": 0.7, "survivor": 0.2, "restorer": 0.1},
            agent_conflicts=[],
            harmony_score=1.0
        )
    
    def _get_biometric_context(self, source: str) -> str:
        """Helper to generate appropriate biometric context."""
        if source == "live":
            return "Your HRV patterns are showing me something interesting..."
        elif source == "cached":
            return "Based on your recent patterns (though I'm working with slightly older data)..."
        else:
            return "Without your biometric data right now, I'm reading between the lines of your words..."

@pytest.mark.asyncio
class TestPersonalityEdgeCases:
    """Test personality consistency in edge cases."""
    
    async def test_personality_with_conflicting_data(self, neuros_workflow):
        """Test personality when biometrics and user report conflict."""
        state = NEUROSState(
            messages=[HumanMessage(content="I feel amazing and energized!")],
            user_id="test_user",
            session_id="test_session",
            biometric_data={"hrv": 25, "recovery_score": 2, "stress": 9},
            biometric_source="live",
            last_biometric_update=datetime.now(),
            weak_signals=[{
                "type": "micro_fatigue",
                "confidence": 0.9,
                "narrative": "Significant autonomic strain detected"
            }],
            active_forecasts={},
            current_arc="struggle",
            storyline_elements=[],
            identity_markers=[],
            current_archetype="survivor",
            archetype_scores={"survivor": 0.9, "strategist": 0.1},
            agent_conflicts=[],
            harmony_score=1.0
        )
        
        with patch.object(neuros_workflow.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = AIMessage(content="""
            I love hearing that energy in your voice! That feeling of being energized is 
            real and valid. And... I'm noticing something interesting in your nervous system 
            data that seems to tell a slightly different story.
            
            Your HRV is sitting at 25, which usually whispers 'recovery needed' even when 
            our mind shouts 'let's go!' This disconnect isn't unusual - sometimes we run 
            on enthusiasm and adrenaline while our foundation needs shoring up.
            
            What if this energy is both real AND a signal? Like a car running beautifully 
            on fumes - the performance is there, but the fuel gauge matters too. How does 
            that land with you?
            """)
            
            result = await neuros_workflow.synthesize_insight_node(state)
            response = result['messages'][-1].content
            
        # Verify diplomatic handling of conflict
        assert "valid" in response.lower() or "real" in response.lower()
        assert "and" in response  # Shows both/and thinking
        assert "?" in response  # Maintains curiosity
        
        # Verify doesn't dismiss either data source
        assert "wrong" not in response.lower()
        assert "mistaken" not in response.lower()
        assert "actually" not in response.lower()  # Avoids contradiction
    
    async def test_personality_with_missing_historical_data(self, neuros_workflow):
        """Test personality when no historical context exists."""
        state = self._create_new_user_state()
        
        with patch.object(neuros_workflow.llm, 'ainvoke', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = AIMessage(content="""
            Welcome! I'm NEUROS, and I'm here to help you understand the conversation 
            between your mind and nervous system. Since we're just meeting, I'm curious 
            about your current baseline.
            
            Think of this as us creating the first page of your body's story together. 
            Every pattern starts somewhere, and today is our 'somewhere.'
            
            What brought you here today? I'm particularly interested in what you've 
            been noticing about your energy, sleep, or recovery lately.
            """)
            
            result = await neuros_workflow.synthesize_insight_node(state)
            response = result['messages'][-1].content
            
        # Verify appropriate new user handling
        assert any(word in response.lower() for word in ["welcome", "meeting", "first", "start"])
        
        # Verify maintains personality even without history
        scores = PersonalityAnalyzer.score_personality_traits(response)
        assert scores['curiosity_first'] > 0.4
        assert scores['metaphorical'] > 0.3
        assert scores['human_voice'] == 1.0
    
    def _create_new_user_state(self) -> NEUROSState:
        """Create state for brand new user."""
        return NEUROSState(
            messages=[HumanMessage(content="Hi, I just signed up")],
            user_id="new_user",
            session_id="first_session",
            biometric_data={},
            biometric_source="none",
            last_biometric_update=datetime.min,
            weak_signals=[],
            active_forecasts={},
            current_arc="baseline",
            storyline_elements=[],
            identity_markers=[],
            current_archetype="strategist",  # Default
            archetype_scores={"strategist": 0.33, "survivor": 0.33, "restorer": 0.34},
            agent_conflicts=[],
            harmony_score=1.0
        )

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])