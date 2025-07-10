from typing import Optional, Dict, Any, List
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import re
from datetime import datetime
import json


class HealthDataParserToolInputSchema(BaseModel):
    message: str = Field(..., description="Raw health message to parse")
    user_id: Optional[str] = Field(None, description="User ID for tracking")


class HealthDataParserTool(BaseTool):
    name: str = "Health Data Parser"
    description: str = "Parse natural language health messages into structured data (weight, calories, macros, workouts, fasting)"
    args_schema = HealthDataParserToolInputSchema

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Define patterns for different health metrics
        self.patterns = {
            'weight': [
                r'weight[:\s]*(\d+\.?\d*)\s*(kg|lb|lbs|pounds?)',
                r'(\d+\.?\d*)\s*(kg|lb|lbs|pounds?)\s*weight',
                r'i\s*weigh[:\s]*(\d+\.?\d*)\s*(kg|lb|lbs|pounds?)'
            ],
            'calories': [
                r'calories[:\s]*(\d+)',
                r'(\d+)\s*calories',
                r'kcal[:\s]*(\d+)',
                r'(\d+)\s*kcal'
            ],
            'protein': [
                r'protein[:\s]*(\d+\.?\d*)\s*(g|grams?)',
                r'(\d+\.?\d*)\s*(g|grams?)\s*protein'
            ],
            'carbs': [
                r'carbs[:\s]*(\d+\.?\d*)\s*(g|grams?)',
                r'carbohydrates[:\s]*(\d+\.?\d*)\s*(g|grams?)',
                r'(\d+\.?\d*)\s*(g|grams?)\s*carbs',
                r'(\d+\.?\d*)\s*(g|grams?)\s*carbohydrates'
            ],
            'fat': [
                r'fat[:\s]*(\d+\.?\d*)\s*(g|grams?)',
                r'(\d+\.?\d*)\s*(g|grams?)\s*fat'
            ],
            'workout': [
                r'workout[:\s]*(.+)',
                r'exercise[:\s]*(.+)',
                r'trained[:\s]*(.+)',
                r'gym[:\s]*(.+)'
            ],
            'fasting_hours': [
                r'fast[:\s]*(\d+)\s*hours?',
                r'fasted[:\s]*(\d+)\s*hours?',
                r'(\d+)\s*hours?\s*fast',
                r'(\d+)\s*hours?\s*fasted'
            ],
            'sleep_hours': [
                r'sleep[:\s]*(\d+\.?\d*)\s*hours?',
                r'slept[:\s]*(\d+\.?\d*)\s*hours?',
                r'(\d+\.?\d*)\s*hours?\s*sleep',
                r'(\d+\.?\d*)\s*hours?\s*slept'
            ],
            'steps': [
                r'steps[:\s]*(\d+)',
                r'(\d+)\s*steps',
                r'walked[:\s]*(\d+)\s*steps'
            ],
            'water': [
                r'water[:\s]*(\d+\.?\d*)\s*(l|liters?|ml|oz)',
                r'(\d+\.?\d*)\s*(l|liters?|ml|oz)\s*water',
                r'drank[:\s]*(\d+\.?\d*)\s*(l|liters?|ml|oz)'
            ]
        }

    def _run(self, message: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse health data from natural language message
        """
        try:
            # Convert to lowercase for better matching
            message_lower = message.lower()
            
            # Initialize result structure
            parsed_data = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "raw_message": message,
                "parsed_data": {}
            }
            
            # Extract data for each metric type
            for metric, patterns in self.patterns.items():
                value = self._extract_metric(message_lower, patterns)
                if value is not None:
                    parsed_data["parsed_data"][metric] = value
            
            # Add confidence score
            parsed_data["confidence_score"] = self._calculate_confidence(parsed_data["parsed_data"])
            
            return {
                "success": True,
                "parsed_data": parsed_data,
                "extracted_metrics": list(parsed_data["parsed_data"].keys())
            }
            
        except Exception as e:
            return {"error": str(e)}

    def _extract_metric(self, message: str, patterns: List[str]) -> Optional[Any]:
        """Extract a specific metric using regex patterns"""
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                # Handle different capture groups
                if len(match.groups()) == 1:
                    return match.group(1)
                elif len(match.groups()) == 2:
                    # Return value with unit
                    return f"{match.group(1)} {match.group(2)}"
                else:
                    # For workout descriptions, return the full match
                    return match.group(0)
        return None

    def _calculate_confidence(self, parsed_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on number of extracted metrics"""
        if not parsed_data:
            return 0.0
        
        # Simple confidence calculation
        # Higher score for more metrics extracted
        confidence = min(len(parsed_data) / 5.0, 1.0)  # Max 5 metrics = 100% confidence
        
        # Bonus for having key metrics
        key_metrics = ['weight', 'calories', 'workout']
        key_metrics_found = sum(1 for metric in key_metrics if metric in parsed_data)
        confidence += (key_metrics_found / len(key_metrics)) * 0.2
        
        return min(confidence, 1.0)

    def _normalize_units(self, value: str, unit: str) -> Any:
        """Normalize units to standard format"""
        try:
            num_value = float(value)
            unit_lower = unit.lower()
            
            # Weight conversions
            if unit_lower in ['lb', 'lbs', 'pound', 'pounds']:
                return num_value * 0.453592  # Convert to kg
            elif unit_lower in ['kg', 'kgs', 'kilogram', 'kilograms']:
                return num_value
            
            # Volume conversions
            elif unit_lower in ['oz', 'ounce', 'ounces']:
                return num_value * 0.0295735  # Convert to liters
            elif unit_lower in ['ml', 'milliliter', 'milliliters']:
                return num_value / 1000  # Convert to liters
            elif unit_lower in ['l', 'liter', 'liters']:
                return num_value
            
            return num_value
        except:
            return value

    def run(self, input_data: HealthDataParserToolInputSchema) -> Dict[str, Any]:
        return self._run(
            message=input_data.message,
            user_id=input_data.user_id
        ) 