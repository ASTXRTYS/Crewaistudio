"""
Schema Registry client wrapper for AUREN Kafka infrastructure.

Provides compatibility between Pydantic models and schema registry while maintaining
JSON Schema for development and preparing for future Avro migration.
"""

import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class SchemaRegistryClient:
    """
    Wrapper for Schema Registry operations that bridges Pydantic and schema registry.
    
    This implementation uses JSON Schema for development while building infrastructure
    for future Avro migration. No breaking changes to existing event flow.
    """
    
    def __init__(self, schema_registry_url: str = "http://localhost:8081"):
        self.url = schema_registry_url
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._json_schemas: Dict[str, Dict[str, Any]] = {}
        
    def register_pydantic_schema(self, topic: str, pydantic_model: type[BaseModel]) -> None:
        """
        Registers a Pydantic model's JSON schema for topic compatibility.
        
        Args:
            topic: Kafka topic name
            pydantic_model: Pydantic model class
        """
        try:
            # Get JSON schema from Pydantic model
            json_schema = pydantic_model.model_json_schema()
            
            # Store for validation and future use
            schema_key = f"{topic}-value"
            self._json_schemas[schema_key] = json_schema
            
            # Create simplified Avro-compatible schema
            avro_schema = self._json_to_avro_schema(json_schema)
            self._schemas[schema_key] = avro_schema
            
            logger.info(f"Registered schema for topic: {topic}")
            
        except Exception as e:
            logger.error(f"Error registering schema for {topic}: {e}")
            raise
    
    def _json_to_avro_schema(self, json_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Converts JSON Schema to Avro schema format.
        
        This is a simplified conversion that handles common cases.
        Extend as needed for complex nested structures.
        """
        avro_schema = {
            "type": "record",
            "name": json_schema.get("title", "GenericRecord"),
            "namespace": "auren.events",
            "fields": []
        }
        
        properties = json_schema.get("properties", {})
        required_fields = json_schema.get("required", [])
        
        for prop_name, prop_details in properties.items():
            field = {
                "name": prop_name,
                "type": self._map_json_type_to_avro(prop_details, prop_name in required_fields)
            }
            
            # Handle field documentation
            if "description" in prop_details:
                field["doc"] = prop_details["description"]
                
            avro_schema["fields"].append(field)
            
        return avro_schema
    
    def _map_json_type_to_avro(self, json_type_def: Dict[str, Any], is_required: bool = True) -> Any:
        """
        Maps JSON Schema types to Avro types.
        
        Handles primitive types, arrays, and nested objects.
        """
        json_type = json_type_def.get("type", "string")
        
        # Handle union types for optional fields
        if not is_required:
            return ["null", self._get_avro_type(json_type, json_type_def)]
        else:
            return self._get_avro_type(json_type, json_type_def)
    
    def _get_avro_type(self, json_type: str, type_def: Dict[str, Any]) -> Any:
        """Get the base Avro type for a JSON type"""
        type_mapping = {
            "string": "string",
            "integer": "long",
            "number": "double",
            "boolean": "boolean"
        }
        
        if json_type == "array":
            items = type_def.get("items", {})
            if isinstance(items, dict):
                item_type = self._get_avro_type(items.get("type", "string"), items)
            else:
                item_type = "string"
            return {"type": "array", "items": item_type}
            
        elif json_type == "object":
            # Handle nested objects recursively
            return self._json_to_avro_schema(type_def)
            
        elif isinstance(json_type, list):
            # Handle union types
            return [type_mapping.get(t, "string") for t in json_type]
            
        else:
            return type_mapping.get(json_type, "string")
    
    def validate_message(self, topic: str, message: Dict[str, Any]) -> bool:
        """
        Validates a message against the registered schema.
        
        Args:
            topic: Kafka topic name
            message: Message to validate
            
        Returns:
            True if message is valid, False otherwise
        """
        schema_key = f"{topic}-value"
        
        if schema_key not in self._json_schemas:
            logger.warning(f"No schema registered for topic: {topic}")
            return True  # Allow messages without schema
            
        try:
            # Basic validation - could be enhanced with jsonschema
            schema = self._json_schemas[schema_key]
            required_fields = schema.get("required", [])
            
            for field in required_fields:
                if field not in message:
                    logger.error(f"Missing required field: {field}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Validation error for topic {topic}: {e}")
            return False
    
    def get_schema(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get the registered schema for a topic"""
        return self._schemas.get(f"{topic}-value")
    
    def get_json_schema(self, topic: str) -> Optional[Dict[str, Any]]:
        """Get the JSON schema for a topic"""
        return self._json_schemas.get(f"{topic}-value")
    
    def list_registered_topics(self) -> list[str]:
        """List all topics with registered schemas"""
        return [key.replace("-value", "") for key in self._schemas.keys()]


# Global registry instance for convenience
registry = SchemaRegistryClient()
