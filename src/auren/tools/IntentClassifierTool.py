import re
import json
from typing import Dict, Any, Optional, List, ClassVar, Type
from datetime import datetime

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class IntentClassifierInput(BaseModel):
    """Input schema for IntentClassifierTool."""
    message: str = Field(..., description="Message text to classify")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for classification")
    confidence_threshold: Optional[float] = Field(0.7, description="Minimum confidence threshold")


class IntentClassifierOutput(BaseModel):
    """Output schema for IntentClassifierTool."""
    intent_category: str = Field(description="Classified intent category")
    confidence_score: float = Field(description="Confidence score (0.0 to 1.0)")
    keywords_matched: List[str] = Field(description="Keywords that influenced the classification")
    subcategory: Optional[str] = Field(description="More specific subcategory if applicable")
    requires_followup: bool = Field(description="Whether this intent requires follow-up questions")


class IntentClassifierTool(BaseTool):
    name: str = "Intent Classifier Tool"
    description: str = "Classify athlete messages into intent categories (TRAINING_LOG, NUTRITION_QUERY, etc.)"
    args_schema: Type[BaseModel] = IntentClassifierInput
    intent_patterns: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Intent classification patterns")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.intent_patterns = self._load_intent_patterns()
        
    def _load_intent_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load intent classification patterns and keywords."""
        return {
            "TRAINING_LOG": {
                "keywords": [
                    "workout", "training", "exercise", "gym", "lifted", "ran", "cycling",
                    "cardio", "strength", "reps", "sets", "weight", "pr", "personal record",
                    "squat", "deadlift", "bench", "press", "pull", "push", "run", "mile",
                    "km", "lbs", "kg", "minutes", "hours", "finished", "completed"
                ],
                "patterns": [
                    r"(?i)\b(did|finished|completed|just)\s+\w*\s*(workout|training|exercise)",
                    r"(?i)\b(lifted|squatted|deadlifted|benched|pressed)\s+\d+",
                    r"(?i)\b(ran|running|jogged)\s+\d+",
                    r"(?i)\b(sets?|reps?)\s+of\s+\d+",
                    r"(?i)\b\d+\s*(lbs?|kg|pounds?|kilograms?)",
                    r"(?i)\b(pr|personal\s+record|new\s+max)"
                ],
                "confidence_boost": 0.2
            },
            "NUTRITION_QUERY": {
                "keywords": [
                    "eat", "food", "meal", "calories", "protein", "carbs", "fat", "nutrition",
                    "diet", "hungry", "snack", "breakfast", "lunch", "dinner", "macro",
                    "supplement", "vitamin", "drink", "water", "hydration", "recipe",
                    "should i eat", "what to eat", "how much", "grams", "serving"
                ],
                "patterns": [
                    r"(?i)\b(what|should|can)\s+i\s+(eat|drink|have)",
                    r"(?i)\b(how\s+much|how\s+many)\s+\w*\s*(protein|carbs|calories)",
                    r"(?i)\b(ate|eating|consumed)\s+\d+",
                    r"(?i)\b\d+\s*(calories|grams?|g|kcal)",
                    r"(?i)\b(macro|macros|nutrition)\s+(help|advice|question)"
                ],
                "confidence_boost": 0.15
            },
            "RECOVERY_STATUS": {
                "keywords": [
                    "tired", "sore", "pain", "recovery", "rest", "sleep", "fatigue",
                    "muscle", "joint", "ache", "stiff", "inflammation", "massage",
                    "stretch", "mobility", "foam roll", "ice", "heat", "therapy",
                    "feeling", "energy", "exhausted", "recovered", "rested"
                ],
                "patterns": [
                    r"(?i)\b(feeling|feel)\s+(tired|sore|pain|good|bad|recovered)",
                    r"(?i)\b(slept|sleep)\s+\d+\s*(hours?|hrs?)",
                    r"(?i)\b(muscle|joint)\s+(pain|ache|sore)",
                    r"(?i)\b(recovery|rest)\s+(day|time|needed)",
                    r"(?i)\b(energy\s+level|fatigue\s+level)"
                ],
                "confidence_boost": 0.1
            },
            "BODY_COMPOSITION": {
                "keywords": [
                    "weight", "weigh", "scale", "body fat", "muscle mass", "lean",
                    "measurements", "inches", "cm", "size", "waist", "chest", "arms",
                    "legs", "progress", "photos", "mirror", "fit", "clothes", "bf%",
                    "composition", "mass", "gained", "lost", "heavier", "lighter"
                ],
                "patterns": [
                    r"(?i)\b(weigh|weight)\s+\d+",
                    r"(?i)\b\d+\s*(lbs?|kg|pounds?)",
                    r"(?i)\b(body\s+fat|bf)\s*%?\s*\d*",
                    r"(?i)\b(gained|lost)\s+\d+\s*(lbs?|kg)",
                    r"(?i)\b(measurements?|measured)\s+\d+",
                    r"(?i)\b\d+\s*(inches?|cm|centimeters?)"
                ],
                "confidence_boost": 0.25
            },
            "SUPPLEMENT_PROTOCOL": {
                "keywords": [
                    "supplement", "protein powder", "creatine", "vitamins", "pre workout",
                    "post workout", "bcaa", "glutamine", "fish oil", "multivitamin",
                    "stack", "dosage", "timing", "when to take", "how much", "pills",
                    "capsules", "powder", "liquid", "brand", "recommend"
                ],
                "patterns": [
                    r"(?i)\b(supplement|protein|creatine|vitamin)\s+(help|advice|question)",
                    r"(?i)\b(when|how)\s+to\s+take\s+\w*\s*(supplement|protein|creatine)",
                    r"(?i)\b(dosage|dose|amount)\s+of\s+\w*\s*(supplement|protein)",
                    r"(?i)\b(pre|post)\s+workout\s+(supplement|nutrition)",
                    r"(?i)\b(stack|protocol|routine)\s+for\s+\w*\s*(supplement|nutrition)"
                ],
                "confidence_boost": 0.2
            },
            "GENERAL_INQUIRY": {
                "keywords": [
                    "help", "question", "advice", "how", "what", "when", "where", "why",
                    "coach", "trainer", "guidance", "support", "confused", "unsure",
                    "recommend", "suggest", "opinion", "thoughts", "feedback", "tips"
                ],
                "patterns": [
                    r"(?i)\b(can\s+you\s+help|need\s+help|help\s+me)",
                    r"(?i)\b(what\s+do\s+you\s+think|your\s+opinion|thoughts\s+on)",
                    r"(?i)\b(any\s+advice|advice\s+on|recommend|suggest)",
                    r"(?i)\b(how\s+do\s+i|what\s+should\s+i|when\s+should\s+i)",
                    r"(?i)\b(confused|unsure|not\s+sure)\s+about"
                ],
                "confidence_boost": 0.05
            }
        }

    def _run(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        confidence_threshold: Optional[float] = 0.7
    ) -> IntentClassifierOutput:
        """Classify message intent based on patterns and keywords."""
        try:
            message_lower = message.lower()
            intent_scores = {}
            matched_keywords = {}
            
            # Score each intent category
            for intent, config in self.intent_patterns.items():
                score = 0.0
                keywords_found = []
                
                # Check keywords
                for keyword in config["keywords"]:
                    if keyword.lower() in message_lower:
                        score += 0.1
                        keywords_found.append(keyword)
                
                # Check patterns
                for pattern in config["patterns"]:
                    if re.search(pattern, message):
                        score += 0.3
                        keywords_found.append(f"pattern_match")
                
                # Apply confidence boost
                if score > 0:
                    score += config.get("confidence_boost", 0)
                
                # Normalize score to 0-1 range
                score = min(score, 1.0)
                
                intent_scores[intent] = score
                matched_keywords[intent] = keywords_found
            
            # Find the best intent
            if intent_scores:
                best_intent = max(intent_scores.keys(), key=lambda x: intent_scores[x])
                best_score = intent_scores[best_intent]
            else:
                best_intent = "GENERAL_INQUIRY"
                best_score = 0.5
            
            # Check if confidence threshold is met
            threshold = confidence_threshold or 0.7
            if best_score < threshold:
                best_intent = "GENERAL_INQUIRY"
                best_score = 0.5  # Default confidence for general inquiries
            
            # Determine subcategory and follow-up requirements
            subcategory = self._determine_subcategory(best_intent, message)
            requires_followup = self._requires_followup(best_intent, message, context)
            
            return IntentClassifierOutput(
                intent_category=best_intent,
                confidence_score=best_score,
                keywords_matched=matched_keywords.get(best_intent, []),
                subcategory=subcategory,
                requires_followup=requires_followup
            )
            
        except Exception as e:
            # Return default classification on error
            return IntentClassifierOutput(
                intent_category="GENERAL_INQUIRY",
                confidence_score=0.3,
                keywords_matched=[],
                subcategory=None,
                requires_followup=True
            )

    def _determine_subcategory(self, intent: str, message: str) -> Optional[str]:
        """Determine more specific subcategory based on intent and message."""
        message_lower = message.lower()
        
        subcategories = {
            "TRAINING_LOG": {
                "strength": ["weight", "lift", "squat", "deadlift", "bench", "press"],
                "cardio": ["run", "bike", "swim", "cardio", "treadmill", "elliptical"],
                "flexibility": ["stretch", "yoga", "mobility", "foam roll"]
            },
            "NUTRITION_QUERY": {
                "meal_planning": ["meal", "plan", "prep", "recipe", "cook"],
                "macros": ["protein", "carbs", "fat", "calories", "macro"],
                "supplements": ["supplement", "protein powder", "creatine", "vitamin"]
            },
            "RECOVERY_STATUS": {
                "sleep": ["sleep", "rest", "tired", "fatigue"],
                "soreness": ["sore", "pain", "ache", "muscle"],
                "energy": ["energy", "exhausted", "recovered", "feeling"]
            },
            "BODY_COMPOSITION": {
                "weight": ["weight", "scale", "weigh", "gained", "lost"],
                "measurements": ["inches", "cm", "waist", "chest", "arms"],
                "progress": ["progress", "photos", "mirror", "fit"]
            }
        }
        
        if intent in subcategories:
            for subcat, keywords in subcategories[intent].items():
                if any(keyword in message_lower for keyword in keywords):
                    return subcat
        
        return None

    def _requires_followup(self, intent: str, message: str, context: Optional[Dict[str, Any]]) -> bool:
        """Determine if this intent requires follow-up questions."""
        message_lower = message.lower()
        
        # Always require follow-up for general inquiries
        if intent == "GENERAL_INQUIRY":
            return True
        
        # Check for incomplete information indicators
        incomplete_indicators = [
            "help", "advice", "what should", "how do", "when should",
            "confused", "unsure", "not sure", "?"
        ]
        
        if any(indicator in message_lower for indicator in incomplete_indicators):
            return True
        
        # Intent-specific follow-up logic
        followup_rules = {
            "TRAINING_LOG": lambda msg: not any(word in msg for word in ["finished", "completed", "did"]),
            "NUTRITION_QUERY": lambda msg: any(word in msg for word in ["should", "what", "how much", "when"]),
            "RECOVERY_STATUS": lambda msg: "?" in msg or "how" in msg,
            "BODY_COMPOSITION": lambda msg: "?" in msg or not any(word in msg for word in ["weigh", "measured"]),
            "SUPPLEMENT_PROTOCOL": lambda msg: any(word in msg for word in ["should", "when", "how", "recommend"])
        }
        
        if intent in followup_rules:
            return followup_rules[intent](message_lower)
        
        return False 