# AUREN Intelligence System - API Documentation

## 🚀 External API Endpoints

### Hypothesis Validator API

#### `POST /api/v1/intelligence/hypotheses`
**Create a new hypothesis**
```json
{
  "agent_id": "neuroscientist",
  "user_id": "user_123",
  "domain": "neuroscience",
  "description": "HRV drops after intense workouts",
  "prediction": {
    "metric": "hrv",
    "expected_change": -15,
    "timeframe": "24h"
  },
  "evidence_criteria": [
    {
      "type": "biometric",
      "metric": "hrv",
      "required_samples": 5,
      "confidence_threshold": 0.8
    }
  ],
  "confidence": 0.75
}
```

**Response:**
```json
{
  "hypothesis_id": "hyp_123abc",
  "status": "formed",
  "confidence": 0.75,
  "expires_at": "2024-07-25T10:00:00Z"
}
```

#### `GET /api/v1/intelligence/hypotheses/{hypothesis_id}`
**Retrieve hypothesis details**
```json
{
  "hypothesis_id": "hyp_123abc",
  "status": "validated",
  "confidence": 0.92,
  "evidence": {
    "supporting": 8,
    "contradicting": 1,
    "confidence_multiplier": 1.23
  },
  "validation_history": [...]
}
```

### Cross-Agent Insights API

#### `GET /api/v1/intelligence/insights/{user_id}`
**Retrieve cross-agent insights**
```json
{
  "insights": [
    {
      "insight_id": "ins_456def",
      "contributing_agents": ["neuroscientist", "training"],
      "content": "Neuroscience and training insights: HRV optimization and recovery protocols work together to improve performance by 23%",
      "confidence": 0.89,
      "impact_score": 0.94,
      "evidence_sources": ["knowledge_123", "knowledge_456"]
    }
  ],
  "generated_at": "2024-07-24T14:30:00Z"
}
```

### Emergency Protocol API

#### `POST /api/v1/intelligence/emergency/trigger`
**Trigger emergency protocol**
```json
{
  "user_id": "user_123",
  "symptoms": ["severe_fatigue", "hrv_drop_30_percent"],
  "severity": "red_zone",
  "timestamp": "2024-07-24T14:30:00Z"
}
```

**Response:**
```json
{
  "emergency_id": "em_789ghi",
  "protocol_triggered": "emergency_hrv_protocol",
  "response_time_ms": 42,
  "actions": [
    "immediate_rest_recommended",
    "healthcare_provider_notified",
    "emergency_contact_alerted"
  ]
}
```

### Knowledge Management API

#### `GET /api/v1/intelligence/knowledge/{user_id}`
**Retrieve user knowledge**
```json
{
  "knowledge": [
    {
      "knowledge_id": "know_123",
      "domain": "neuroscience",
      "type": "pattern",
      "title": "HRV recovery pattern",
      "confidence": 0.92,
      "application_count": 15,
      "success_rate": 0.87
    }
  ],
  "total_count": 47,
  "domains": ["neuroscience", "training", "nutrition"]
}
```

## 🔧 Integration Examples

### HealthKit Integration Flow

```python
# Entry point for biometric data
async def process_healthkit_data(user_id: str, healthkit_data: dict):
    """Process incoming HealthKit data and trigger intelligence"""
    
    # 1. Validate and normalize data
    normalized_data = await normalize_healthkit_data(healthkit_data)
    
    # 2. Check for emergency conditions
    emergency_check = await check_emergency_conditions(normalized_data)
    if emergency_check.is_emergency:
        await trigger_emergency_protocol(emergency_check)
    
    # 3. Update hypothesis validation
    await update_hypothesis_evidence(user_id, normalized_data)
    
    # 4. Generate new insights
    insights = await generate_cross_agent_insights(user_id)
    
    return insights
```

### Data Flow Visualization

```
HealthKit Data → [Normalization] → [Emergency Check] → [Hypothesis Validation] → [Knowledge Update] → [Cross-Agent Insights] → [User Recommendations]
```

## 📊 Configuration Management

### Environment Variables
```bash
# Database Configuration
AUREN_DB_HOST=localhost
AUREN_DB_PORT=5432
AUREN_DB_NAME=auren_intelligence
AUREN_DB_USER=auren_user
AUREN_DB_PASSWORD=secure_password

# Performance Tuning
AUREN_CACHE_SIZE=1000
AUREN_CONNECTION_POOL_SIZE=20
AUREN_EMERGENCY_TIMEOUT_MS=50

# Monitoring
AUREN_LOG_LEVEL=INFO
AUREN_METRICS_ENABLED=true
AUREN_ALERT_WEBHOOK=https://alerts.auren.com/webhook
```

### Production Configuration Template
```yaml
# config/production.yaml
intelligence:
  database:
    pool_size: 20
    max_overflow: 30
    pool_timeout: 30
    
  cache:
    size: 1000
    ttl: 3600
    
  performance:
    emergency_timeout_ms: 50
    hypothesis_validation_timeout_ms: 100
    knowledge_retrieval_timeout_ms: 50
    
  monitoring:
    metrics_interval: 60
    health_check_interval: 30
    alert_thresholds:
      response_time_ms: 100
      error_rate: 0.01
      memory_usage: 0.8
```

## 🚨 Error Handling Examples

### PostgreSQL Unavailable
```python
async def handle_db_unavailable(error: Exception):
    """Handle PostgreSQL connection failures"""
    
    # 1. Log the error
    logger.error(f"Database unavailable: {error}")
    
    # 2. Switch to fallback mode
    fallback_memory = InMemoryCache()
    
    # 3. Queue critical operations
    await queue_emergency_operations()
    
    # 4. Alert operations team
    await send_alert({
        "type": "database_unavailable",
        "severity": "high",
        "action": "fallback_mode_activated"
    })
    
    # 5. Return cached responses
    return await get_cached_insights()
```

### Hypothesis Conflict Resolution
```python
async def resolve_hypothesis_conflicts(conflicts: List[HypothesisConflict]):
    """Resolve conflicting hypotheses between agents"""
    
    for conflict in conflicts:
        # 1. Analyze evidence strength
        evidence_analysis = await analyze_evidence_strength(conflict)
        
        # 2. Apply statistical validation
        validation_result = await validate_statistically(evidence_analysis)
        
        # 3. Weight by confidence and evidence quality
        weighted_decision = await apply_weighted_decision(validation_result)
        
        # 4. Generate unified recommendation
        unified_insight = await generate_unified_insight(weighted_decision)
        
        # 5. Update knowledge base
        await update_knowledge_with_resolution(unified_insight)
```

### Agent Failure Recovery
```python
async def handle_agent_failure(agent_id: str, error: Exception):
    """Handle agent failure during collaboration"""
    
    # 1. Isolate failed agent
    await isolate_agent(agent_id)
    
    # 2. Redistribute pending work
    await redistribute_workload(agent_id)
    
    # 3. Use cached knowledge
    cached_insights = await get_cached_agent_knowledge(agent_id)
    
    # 4. Alert for manual intervention
    await alert_operations_team({
        "agent_id": agent_id,
        "error": str(error),
        "recovery_action": "using_cached_knowledge"
    })
```

## 📈 Monitoring and Observability

### Key Performance Indicators (KPIs)
```python
# Metrics to monitor
MONITORING_METRICS = {
    "system_health": {
        "response_time_p95": "<100ms",
        "error_rate": "<1%",
        "availability": ">99.9%"
    },
    "intelligence_quality": {
        "hypothesis_validation_rate": ">95%",
        "knowledge_accuracy": ">85%",
        "cross_agent_insights": ">75%"
    },
    "emergency_response": {
        "detection_time": "<50ms",
        "response_time": "<100ms",
        "false_positive_rate": "<5%"
    }
}
```

### Alert Thresholds
```yaml
alerts:
  - name: "high_response_time"
    condition: "response_time > 100ms"
    severity: "warning"
    action: "scale_up"
    
  - name: "database_unavailable"
    condition: "db_connection_failures > 5"
    severity: "critical"
    action: "fallback_mode"
    
  - name: "emergency_detection"
    condition: "emergency_detected"
    severity: "critical"
    action: "immediate_notification"
```

## 🔄 Rollback Strategy

### Knowledge Preservation
```python
class RollbackManager:
    """Handle system rollback while preserving knowledge"""
    
    async def create_rollback_point(self):
        """Create rollback point with knowledge preservation"""
        
        # 1. Export knowledge base
        knowledge_snapshot = await export_knowledge_base()
        
        # 2. Export hypothesis states
        hypothesis_states = await export_hypothesis_states()
        
        # 3. Export validation history
        validation_history = await export_validation_history()
        
        # 4. Create rollback manifest
        rollback_manifest = {
            "timestamp": datetime.now(timezone.utc),
            "knowledge_count": len(knowledge_snapshot),
            "hypothesis_count": len(hypothesis_states),
            "version": "1.0.0"
        }
        
        return rollback_manifest
    
    async def rollback_to_point(self, manifest: dict):
        """Rollback to previous point while preserving knowledge"""
        
        # 1. Restore knowledge base
        await restore_knowledge_base(manifest["knowledge_snapshot"])
        
        # 2. Restore hypothesis states
        await restore_hypothesis_states(manifest["hypothesis_states"])
        
        # 3. Resume validation
        await resume_validation_pipeline()
        
        # 4. Verify integrity
        await verify_system_integrity()
```

## 🎯 HealthKit Integration Example

### Complete Integration Flow
```python
# auren/integrations/healthkit_integration.py

class HealthKitIntegration:
    """Complete HealthKit integration with intelligence system"""
    
    async def process_hrv_data(self, user_id: str, hrv_data: dict):
        """Process HRV data and generate insights"""
        
        # 1. Normalize HealthKit format
        normalized = {
            "timestamp": hrv_data["startDate"],
            "value": hrv_data["value"],
            "unit": "ms",
            "quality": hrv_data["metadata"]["HKMetadataKeyHeartRateMotionContext"]
        }
        
        # 2. Check for emergency conditions
        emergency_check = await self.check_emergency_hrv(normalized)
        if emergency_check.is_critical:
            await self.trigger_emergency_protocol(user_id, emergency_check)
        
        # 3. Update hypothesis validation
        await self.intelligence_system.update_hypothesis_evidence(
            user_id=user_id,
            metric="hrv",
            value=normalized["value"],
            timestamp=normalized["timestamp"]
        )
        
        # 4. Generate new insights
        insights = await self.intelligence_system.generate_insights(user_id)
        
        # 5. Return actionable recommendations
        return {
            "insights": insights,
            "emergency_status": emergency_check.status,
            "next_check": datetime.now(timezone.utc) + timedelta(hours=1)
        }
    
    async def check_emergency_hrv(self, hrv_data: dict) -> EmergencyCheck:
        """Check if HRV indicates emergency condition"""
        
        # Critical thresholds
        CRITICAL_HRV_DROP = 0.30  # 30% drop
        BASELINE_HRV = 50.0
        
        current_hrv = hrv_data["value"]
        drop_percentage = (BASELINE_HRV - current_hrv) / BASELINE_HRV
        
        if drop_percentage > CRITICAL_HRV_DROP:
            return EmergencyCheck(
                is_critical=True,
                severity="red_zone",
                message=f"HRV dropped {drop_percentage*100:.1f}% - immediate attention required",
                actions=["immediate_rest", "healthcare_notification"]
            )
        
        return EmergencyCheck(is_critical=False, severity="normal")
```

This comprehensive documentation package provides everything needed for production deployment, including API specifications, error handling, monitoring, and real-world integration examples.
