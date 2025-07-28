# SECTION 11 INTEGRATION GUIDE

**Created**: January 29, 2025  
**Author**: Senior Engineer  
**Version**: 1.0  
**Purpose**: Show how to integrate with Section 11's event sourcing and real-time features

---

## 📊 Overview

This guide shows how other AUREN components can integrate with Section 11's database features. This documentation stays within Section 11's scope - it provides patterns and examples without modifying other components.

---

## 🎯 Event Sourcing Integration

### Using the Helper Functions

Section 11 provides three main functions for event sourcing:

#### 1. Appending Events
```python
# Example Python code (not implemented, just documentation)
async def emit_event(user_id: str, event_type: str, data: dict):
    """Example of how to emit an event from Python"""
    await db.execute("""
        SELECT events.append_event(
            p_stream_id := $1,
            p_event_type := $2,
            p_event_data := $3,
            p_created_by := $4
        )
    """, f"user:{user_id}", event_type, json.dumps(data), "biometric_api")
```

#### 2. Replaying Events
```python
# Example: Rebuild user state from events
async def rebuild_user_state(user_id: str):
    """Replay all events for a user to rebuild state"""
    events = await db.fetch("""
        SELECT * FROM events.replay_stream($1)
    """, f"user:{user_id}")
    
    state = {}
    for event in events:
        # Apply each event to rebuild state
        state = apply_event(state, event)
    return state
```

#### 3. Getting Current State
```sql
-- SQL example: Get current state for a user
SELECT events.get_stream_state('user:demo123');
```

---

## 🔔 LISTEN/NOTIFY Integration

### Python Listener Example
```python
# Example: How to listen for real-time events
import asyncpg

async def setup_listeners(conn: asyncpg.Connection):
    """Setup PostgreSQL LISTEN channels"""
    await conn.add_listener('mode_switch', handle_mode_switch)
    await conn.add_listener('memory_tier_change', handle_memory_change)
    
async def handle_mode_switch(conn, pid, channel, payload):
    """Handle mode switch notifications"""
    data = json.loads(payload)
    # Forward to WebSocket clients
    await websocket_manager.broadcast({
        'type': 'mode_switch',
        'data': data
    })
```

### Sending Notifications
```sql
-- From database triggers or functions
PERFORM pg_notify('mode_switch', json_build_object(
    'user_id', NEW.user_id,
    'from_mode', OLD.current_mode,
    'to_mode', NEW.current_mode,
    'timestamp', NOW()
)::text);
```

---

## 📊 Using Materialized Views

Section 11 created `analytics.user_metrics_daily` as an alternative to continuous aggregates:

### Querying Aggregated Data
```sql
-- Get user's average heart rate for last 7 days
SELECT 
    day,
    AVG(avg_value) as avg_hr
FROM analytics.user_metrics_daily
WHERE user_id = 'demo123'
  AND metric_type = 'heart_rate'
  AND day > CURRENT_DATE - INTERVAL '7 days'
GROUP BY day
ORDER BY day;
```

### Refreshing Views
```sql
-- Refresh materialized view (schedule this hourly)
SELECT analytics.refresh_user_metrics();
```

---

## 🔌 Biometric API Integration Points

### 1. Emit Events on State Changes
```python
# When processing webhook data:
await db.execute("""
    SELECT events.append_event(
        'user:' || $1,
        'biometric_received',
        $2::jsonb,
        'webhook_processor'
    )
""", user_id, event_data)
```

### 2. Mode Switch Events
```python
# When NEUROS switches modes:
event_id = await emit_event(
    user_id=user_id,
    event_type='mode_switched',
    data={
        'from_mode': old_mode,
        'to_mode': new_mode,
        'confidence': confidence_score,
        'trigger': trigger_reason
    }
)
```

---

## 🔐 Section 9 Security Integration

When using event sourcing with PHI data:

```python
# Example: Encrypt PHI before storing in events
from app.section_9_security import encrypt_phi_field

# Encrypt sensitive data
encrypted_hr = await encrypt_phi_field(heart_rate, user_id)

# Store encrypted data in event
await emit_event(
    user_id=user_id,
    event_type='vitals_recorded',
    data={
        'heart_rate': encrypted_hr,  # Encrypted
        'timestamp': timestamp,       # Not PHI
        'device': device_type        # Not PHI
    }
)
```

---

## 📈 Performance Optimization Tips

### 1. Use the New Indexes
Section 11 added these indexes for better performance:
- `idx_event_store_created_at` - Time-based queries
- `idx_event_store_event_data_gin` - JSONB searches
- `idx_biometric_events_user_device_time` - User device queries

### 2. Batch Event Writes
```python
# Example: Batch multiple events
async with db.transaction():
    for event in event_batch:
        await emit_event(event['user_id'], event['type'], event['data'])
```

### 3. Use Prepared Statements
```python
# Prepare frequently used queries
stmt = await conn.prepare("""
    SELECT events.append_event($1, $2, $3, $4)
""")
# Use many times
await stmt.fetch(stream_id, event_type, data, created_by)
```

---

## 🎯 WebSocket Integration Pattern

For real-time UI updates:

```python
# Example WebSocket handler
class DashboardWebSocket:
    async def connect(self):
        # Setup DB listener
        self.db_conn = await asyncpg.connect(DATABASE_URL)
        await self.db_conn.add_listener('mode_switch', self.on_mode_switch)
        
    async def on_mode_switch(self, conn, pid, channel, payload):
        # Forward to connected clients
        await self.send_json({
            'event': 'mode_switch',
            'data': json.loads(payload)
        })
```

---

## 📝 Best Practices

1. **Event Naming**: Use consistent event types
   - `user_registered`, `device_connected`, `mode_switched`
   - Not: `UserRegistered`, `device-connected`, `MODESWITCHED`

2. **Stream IDs**: Use prefixes for organization
   - `user:123` - User events
   - `device:abc` - Device events
   - `system:config` - System events

3. **Event Data**: Include enough context
   ```json
   {
       "timestamp": "2025-01-29T10:00:00Z",
       "user_id": "123",
       "previous_value": 65,
       "new_value": 85,
       "reason": "exercise_detected"
   }
   ```

4. **Error Handling**: Events are immutable
   - Don't update events, append corrections
   - Use compensating events for corrections

---

## 🚀 Getting Started Checklist

For teams integrating with Section 11:

- [ ] Review available event types
- [ ] Understand stream ID conventions
- [ ] Setup LISTEN connections for real-time needs
- [ ] Plan event emission points in your code
- [ ] Consider PHI encryption requirements
- [ ] Schedule materialized view refreshes
- [ ] Monitor event store growth

---

*This guide provides integration patterns without modifying components outside Section 11's scope.* 