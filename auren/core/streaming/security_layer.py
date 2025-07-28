"""
Security Layer for AUREN Event Streaming
Sanitizes sensitive data, encrypts financial information, and implements role-based filtering
"""

import hashlib
import json
import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
from cryptography.fernet import Fernet
import re
from enum import Enum

logger = logging.getLogger(__name__)

class EventAccessLevel(Enum):
    """Access levels for event visibility"""
    PUBLIC = "public"           # System metrics only
    INTERNAL = "internal"       # Includes performance data
    PRIVILEGED = "privileged"   # Includes sanitized user data
    ADMIN = "admin"            # Full access including costs

@dataclass
class SecurityPolicy:
    """Security policy for event processing"""
    sanitize_user_ids: bool = True
    sanitize_biometrics: bool = True
    sanitize_conversations: bool = True
    encrypt_costs: bool = True
    encrypt_queries: bool = True
    hash_algorithm: str = "sha256"
    max_content_length: int = 500

class SecureEventStreamer:
    """
    Security layer for event streaming
    Protects sensitive data while maintaining observability
    """
    
    def __init__(self, 
                 base_streamer,
                 encryption_key: Optional[bytes] = None,
                 security_policy: Optional[SecurityPolicy] = None):
        self.base_streamer = base_streamer
        self.security_policy = security_policy or SecurityPolicy()
        
        # Initialize encryption
        if encryption_key:
            self.cipher_suite = Fernet(encryption_key)
        else:
            # Generate new key for session
            self.cipher_suite = Fernet(Fernet.generate_key())
            logger.warning("Using auto-generated encryption key. Set explicit key for production!")
        
        # Sensitive field patterns
        self.sensitive_patterns = {
            'user_id': re.compile(r'(user_id|userId|user)[\"\']?\s*[:=]\s*[\"\']?([^\"\'}\s,]+)'),
            'email': re.compile(r'[\w\.-]+@[\w\.-]+\.\w+'),
            'phone': re.compile(r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{4,6}'),
            'biometric': re.compile(r'(hrv|heart_rate|blood_pressure|sleep_quality|stress_level)[\"\']?\s*[:=]\s*([0-9\.]+)')
        }
        
        # Biometric value ranges for sanitization
        self.biometric_ranges = {
            'hrv': (20, 100),
            'heart_rate': (40, 200),
            'blood_pressure_systolic': (80, 200),
            'blood_pressure_diastolic': (40, 120),
            'sleep_efficiency': (0, 1),
            'stress_level': (0, 10)
        }
        
        # Fields to encrypt
        self.encrypt_fields = {
            'token_cost', 'cost', 'estimated_cost', 'cost_accumulated',
            'query', 'user_query', 'search_query', 'question'
        }
        
        # Track sanitization metrics
        self.sanitization_stats = {
            'total_events': 0,
            'sanitized_events': 0,
            'encrypted_fields': 0,
            'filtered_events': 0
        }
    
    async def stream_event(self, event: 'AURENStreamEvent') -> bool:
        """
        Stream event with security processing
        """
        try:
            self.sanitization_stats['total_events'] += 1
            
            # Create a deep copy to avoid modifying original
            secure_event = self._deep_copy_event(event)
            
            # Apply security transformations
            if self.security_policy.sanitize_user_ids:
                secure_event = self._sanitize_user_ids(secure_event)
            
            if self.security_policy.sanitize_biometrics:
                secure_event = self._sanitize_biometric_values(secure_event)
            
            if self.security_policy.sanitize_conversations:
                secure_event = self._sanitize_conversation_content(secure_event)
            
            if self.security_policy.encrypt_costs:
                secure_event = self._encrypt_cost_data(secure_event)
            
            if self.security_policy.encrypt_queries:
                secure_event = self._encrypt_query_data(secure_event)
            
            # Add security metadata
            secure_event = self._add_security_metadata(secure_event)
            
            # Stream the secured event
            result = await self.base_streamer.stream_event(secure_event)
            
            if result:
                self.sanitization_stats['sanitized_events'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Security layer error: {e}")
            return False
    
    def _deep_copy_event(self, event: 'AURENStreamEvent') -> 'AURENStreamEvent':
        """Create a deep copy of the event for modification"""
        from auren.realtime.langgraph_instrumentation import AURENStreamEvent, AURENPerformanceMetrics
        
        # Copy performance metrics if present
        perf_metrics = None
        if event.performance_metrics:
            perf_metrics = AURENPerformanceMetrics(**asdict(event.performance_metrics))
        
        # Create new event with copied data
        return AURENStreamEvent(
            event_id=event.event_id,
            trace_id=event.trace_id,
            session_id=event.session_id,
            timestamp=event.timestamp,
            event_type=event.event_type,
            source_agent=dict(event.source_agent) if event.source_agent else None,
            target_agent=dict(event.target_agent) if event.target_agent else None,
            payload=dict(event.payload),
            metadata=dict(event.metadata),
            performance_metrics=perf_metrics,
            user_id=event.user_id
        )
    
    def _sanitize_user_ids(self, event: 'AURENStreamEvent') -> 'AURENStreamEvent':
        """Sanitize user IDs throughout the event"""
        
        # Sanitize main user_id
        if event.user_id:
            event.user_id = self._hash_value(event.user_id)
        
        # Sanitize in payload
        event.payload = self._sanitize_dict_field(event.payload, 'user_id')
        event.payload = self._sanitize_dict_field(event.payload, 'userId')
        
        # Sanitize in metadata
        event.metadata = self._sanitize_dict_field(event.metadata, 'user_id')
        event.metadata = self._sanitize_dict_field(event.metadata, 'userId')
        
        # Sanitize in agent data
        if event.source_agent:
            event.source_agent = self._sanitize_dict_field(event.source_agent, 'user_id')
        if event.target_agent:
            event.target_agent = self._sanitize_dict_field(event.target_agent, 'user_id')
        
        return event
    
    def _sanitize_biometric_values(self, event: 'AURENStreamEvent') -> 'AURENStreamEvent':
        """Sanitize biometric values to ranges instead of exact values"""
        
        # Check payload for biometric data
        for key, value in list(event.payload.items()):
            if self._is_biometric_field(key) and isinstance(value, (int, float)):
                event.payload[key] = self._sanitize_biometric_value(key, value)
        
        # Check nested biometric data
        if 'biometric_data' in event.payload:
            bio_data = event.payload['biometric_data']
            if isinstance(bio_data, dict):
                for key, value in bio_data.items():
                    if isinstance(value, (int, float)):
                        bio_data[key] = self._sanitize_biometric_value(key, value)
        
        # Sanitize in performance metrics
        if event.performance_metrics and hasattr(event.performance_metrics, 'biometric_correlation'):
            # Replace exact correlation with range
            corr = getattr(event.performance_metrics, 'biometric_correlation', 0)
            if corr > 0.8:
                setattr(event.performance_metrics, 'biometric_correlation', 'high')
            elif corr > 0.5:
                setattr(event.performance_metrics, 'biometric_correlation', 'medium')
            else:
                setattr(event.performance_metrics, 'biometric_correlation', 'low')
        
        return event
    
    def _sanitize_conversation_content(self, event: 'AURENStreamEvent') -> 'AURENStreamEvent':
        """Sanitize conversation content while preserving intent"""
        
        # Truncate long messages
        if 'message' in event.payload:
            event.payload['message'] = self._sanitize_text_content(event.payload['message'])
        
        if 'response' in event.payload:
            event.payload['response'] = self._sanitize_text_content(event.payload['response'])
        
        # Sanitize conversation history
        if 'conversation' in event.payload:
            event.payload['conversation'] = self._sanitize_text_content(event.payload['conversation'])
        
        # Remove any PII from text fields
        for key in ['description', 'task_description', 'goal', 'backstory']:
            if key in event.payload:
                event.payload[key] = self._remove_pii_from_text(event.payload[key])
        
        return event
    
    def _encrypt_cost_data(self, event: 'AURENStreamEvent') -> 'AURENStreamEvent':
        """Encrypt all cost-related data"""
        
        # Encrypt in payload
        for field in self.encrypt_fields:
            if field in event.payload and 'cost' in field:
                original_value = event.payload[field]
                event.payload[field] = self._encrypt_value(original_value)
                event.payload[f"{field}_encrypted"] = True
                self.sanitization_stats['encrypted_fields'] += 1
        
        # Encrypt in performance metrics
        if event.performance_metrics and hasattr(event.performance_metrics, 'token_cost'):
            original_cost = event.performance_metrics.token_cost
            encrypted_cost = self._encrypt_value(original_cost)
            event.performance_metrics.token_cost = 0.0  # Zero out
            if not hasattr(event.metadata, 'encrypted_data'):
                event.metadata['encrypted_data'] = {}
            event.metadata['encrypted_data']['token_cost'] = encrypted_cost
        
        return event
    
    def _encrypt_query_data(self, event: 'AURENStreamEvent') -> 'AURENStreamEvent':
        """Encrypt user queries and search terms"""
        
        query_fields = ['query', 'user_query', 'search_query', 'question', 'prompt']
        
        for field in query_fields:
            if field in event.payload:
                original_value = str(event.payload[field])
                if len(original_value) > 10:  # Only encrypt substantial queries
                    event.payload[field] = self._encrypt_value(original_value)
                    event.payload[f"{field}_encrypted"] = True
                    self.sanitization_stats['encrypted_fields'] += 1
        
        return event
    
    def _add_security_metadata(self, event: 'AURENStreamEvent') -> 'AURENStreamEvent':
        """Add security metadata to event"""
        
        # Determine access level based on content
        access_level = self._determine_access_level(event)
        
        # Add security metadata
        event.metadata['security'] = {
            'sanitized': True,
            'sanitization_version': '1.0',
            'access_level': access_level.value,
            'sanitized_fields': self._get_sanitized_fields(event),
            'encryption_applied': self._has_encrypted_fields(event),
            'timestamp': datetime.now().isoformat()
        }
        
        return event
    
    def _hash_value(self, value: str) -> str:
        """Hash a value using configured algorithm"""
        if not value:
            return value
        
        hash_func = hashlib.sha256()
        hash_func.update(value.encode('utf-8'))
        # Keep first 12 chars for some uniqueness while maintaining privacy
        return f"hash_{hash_func.hexdigest()[:12]}"
    
    def _sanitize_biometric_value(self, field_name: str, value: float) -> str:
        """Convert exact biometric value to range"""
        
        # Normalize field name
        normalized_field = field_name.lower().replace('_', '').replace('-', '')
        
        # Find matching range
        for biometric, (min_val, max_val) in self.biometric_ranges.items():
            if biometric in normalized_field:
                if value < min_val:
                    return f"below_normal"
                elif value > max_val:
                    return f"above_normal"
                else:
                    # Divide into quartiles
                    range_size = max_val - min_val
                    quartile = int((value - min_val) / range_size * 4)
                    quartiles = ['low', 'normal_low', 'normal_high', 'high']
                    return quartiles[min(quartile, 3)]
        
        # Default for unknown biometrics
        return "measured"
    
    def _sanitize_text_content(self, text: str) -> str:
        """Sanitize text content while preserving meaning"""
        if not text:
            return text
        
        # Truncate to max length
        if len(text) > self.security_policy.max_content_length:
            text = text[:self.security_policy.max_content_length] + "...[truncated]"
        
        # Remove potential PII patterns
        text = self._remove_pii_from_text(text)
        
        return text
    
    def _remove_pii_from_text(self, text: str) -> str:
        """Remove PII patterns from text"""
        if not text:
            return text
        
        # Remove emails
        text = self.sensitive_patterns['email'].sub('[email]', text)
        
        # Remove phone numbers
        text = self.sensitive_patterns['phone'].sub('[phone]', text)
        
        # Remove user IDs in text
        text = self.sensitive_patterns['user_id'].sub(r'\1: [user_id]', text)
        
        return text
    
    def _encrypt_value(self, value: Any) -> str:
        """Encrypt a value"""
        try:
            # Convert to string
            str_value = json.dumps(value) if not isinstance(value, str) else value
            
            # Encrypt
            encrypted = self.cipher_suite.encrypt(str_value.encode())
            
            # Return base64 encoded
            return encrypted.decode()
            
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            return "[encryption_error]"
    
    def decrypt_value(self, encrypted_value: str) -> Any:
        """Decrypt a value (for authorized access)"""
        try:
            decrypted = self.cipher_suite.decrypt(encrypted_value.encode())
            str_value = decrypted.decode()
            
            # Try to parse as JSON
            try:
                return json.loads(str_value)
            except:
                return str_value
                
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            return None
    
    def _is_biometric_field(self, field_name: str) -> bool:
        """Check if field contains biometric data"""
        biometric_keywords = [
            'hrv', 'heart_rate', 'heartrate', 'blood_pressure', 'bp',
            'sleep', 'stress', 'temperature', 'spo2', 'oxygen',
            'glucose', 'weight', 'bmi', 'body_fat'
        ]
        
        field_lower = field_name.lower()
        return any(keyword in field_lower for keyword in biometric_keywords)
    
    def _sanitize_dict_field(self, data: Dict[str, Any], field_name: str) -> Dict[str, Any]:
        """Recursively sanitize a field in a dictionary"""
        if field_name in data:
            data[field_name] = self._hash_value(str(data[field_name]))
        
        # Recurse into nested dicts
        for key, value in data.items():
            if isinstance(value, dict):
                data[key] = self._sanitize_dict_field(value, field_name)
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        value[i] = self._sanitize_dict_field(item, field_name)
        
        return data
    
    def _determine_access_level(self, event: 'AURENStreamEvent') -> EventAccessLevel:
        """Determine appropriate access level for event"""
        
        # Admin level for system events without user data
        from auren.realtime.langgraph_instrumentation import AURENEventType
        if event.event_type == AURENEventType.SYSTEM_HEALTH:
            return EventAccessLevel.PUBLIC
        
        # Check for encrypted data
        if self._has_encrypted_fields(event):
            return EventAccessLevel.ADMIN
        
        # Check for user-specific data
        if event.user_id or 'user' in str(event.payload):
            return EventAccessLevel.PRIVILEGED
        
        # Default to internal
        return EventAccessLevel.INTERNAL
    
    def _get_sanitized_fields(self, event: 'AURENStreamEvent') -> List[str]:
        """Get list of fields that were sanitized"""
        sanitized = []
        
        if event.user_id and 'hash_' in str(event.user_id):
            sanitized.append('user_id')
        
        # Check for sanitized biometrics
        for key, value in event.payload.items():
            if isinstance(value, str) and value in ['below_normal', 'above_normal', 'low', 'normal_low', 'normal_high', 'high', 'measured']:
                sanitized.append(key)
        
        # Check for truncated content
        for key, value in event.payload.items():
            if isinstance(value, str) and value.endswith('[truncated]'):
                sanitized.append(key)
        
        return sanitized
    
    def _has_encrypted_fields(self, event: 'AURENStreamEvent') -> bool:
        """Check if event has encrypted fields"""
        
        # Check payload for encryption flags
        for key in event.payload:
            if key.endswith('_encrypted') and event.payload[key] is True:
                return True
        
        # Check metadata for encrypted data
        if 'encrypted_data' in event.metadata:
            return True
        
        return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get security layer statistics"""
        
        return {
            'total_events': self.sanitization_stats['total_events'],
            'sanitized_events': self.sanitization_stats['sanitized_events'],
            'encrypted_fields': self.sanitization_stats['encrypted_fields'],
            'filtered_events': self.sanitization_stats['filtered_events'],
            'sanitization_rate': self.sanitization_stats['sanitized_events'] / max(1, self.sanitization_stats['total_events']),
            'encryption_rate': self.sanitization_stats['encrypted_fields'] / max(1, self.sanitization_stats['total_events'])
        }


class RoleBasedEventFilter:
    """
    Filter events based on user roles
    Controls what events different dashboard users can see
    """
    
    def __init__(self):
        self.role_permissions = {
            'admin': {
                'allowed_access_levels': [EventAccessLevel.PUBLIC, EventAccessLevel.INTERNAL, 
                                        EventAccessLevel.PRIVILEGED, EventAccessLevel.ADMIN],
                'can_see_costs': True,
                'can_see_user_data': True,
                'can_decrypt': True
            },
            'developer': {
                'allowed_access_levels': [EventAccessLevel.PUBLIC, EventAccessLevel.INTERNAL, 
                                        EventAccessLevel.PRIVILEGED],
                'can_see_costs': False,
                'can_see_user_data': False,
                'can_decrypt': False
            },
            'analyst': {
                'allowed_access_levels': [EventAccessLevel.PUBLIC, EventAccessLevel.INTERNAL],
                'can_see_costs': False,
                'can_see_user_data': False,
                'can_decrypt': False
            },
            'viewer': {
                'allowed_access_levels': [EventAccessLevel.PUBLIC],
                'can_see_costs': False,
                'can_see_user_data': False,
                'can_decrypt': False
            }
        }
    
    def filter_event_for_role(self, event: Dict[str, Any], user_role: str) -> Optional[Dict[str, Any]]:
        """
        Filter event based on user role
        Returns None if user shouldn't see this event
        """
        
        # Get role permissions
        permissions = self.role_permissions.get(user_role, self.role_permissions['viewer'])
        
        # Check access level
        event_access_level = EventAccessLevel(event.get('metadata', {}).get('security', {}).get('access_level', 'public'))
        if event_access_level not in permissions['allowed_access_levels']:
            return None
        
        # Filter out cost data if not allowed
        if not permissions['can_see_costs']:
            filtered_event = dict(event)
            if 'payload' in filtered_event:
                filtered_payload = dict(filtered_event['payload'])
                for key in list(filtered_payload.keys()):
                    if 'cost' in key or key in ['token_cost', 'estimated_cost']:
                        filtered_payload[key] = '[hidden]'
                filtered_event['payload'] = filtered_payload
            
            return filtered_event
        
        return event
    
    def get_role_permissions(self, user_role: str) -> Dict[str, Any]:
        """Get permissions for a role"""
        return self.role_permissions.get(user_role, self.role_permissions['viewer']) 