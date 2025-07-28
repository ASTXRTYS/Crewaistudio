"""AUREN Biometric Bridge Module - Production-ready biometric processing system"""

from .types import (
    BiometricEvent,
    BiometricReading,
    WearableType,
    CognitiveMode,
    NEUROSState
)

from .bridge import (
    BiometricKafkaLangGraphBridge,
    load_biometric_config,
    reload_config
)

from .handlers import (
    AppleHealthKitHandler
)

__all__ = [
    # Types
    "BiometricEvent",
    "BiometricReading",
    "WearableType",
    "CognitiveMode", 
    "NEUROSState",
    
    # Bridge components
    "BiometricKafkaLangGraphBridge",
    "load_biometric_config",
    "reload_config",
    
    # Handlers
    "AppleHealthKitHandler",
]

__version__ = "2.0.0" 