# AUREN Token Tracking System

## 🎯 Overview

The AUREN Token Tracking System is a production-ready solution for monitoring LLM token usage, tracking costs, and enforcing budget limits in real-time. Built specifically for CrewAI integration with Redis-based tracking.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Redis
```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or using local Redis
redis-server
```

### 3. Run Test Script
```bash
cd auren
python scripts/test_redis_tracking.py
```

## 📊 Features

- **Real-time Token Tracking**: Track every LLM call with precise token counts
- **Cost Calculation**: Automatic cost calculation for multiple models
- **Budget Enforcement**: Prevent users from exceeding daily limits
- **Rate Limiting**: Built-in rate limiting per user/agent
- **CrewAI Integration**: Seamless integration with CrewAI agents
- **Redis Backend**: Fast, persistent storage with TTL management
- **Comprehensive Analytics**: User stats, agent costs, hourly metrics

## 🔧 Usage

### Basic Usage

```python
from auren.monitoring import TokenTracker

async def track_llm_call():
    tracker = TokenTracker()
    async with tracker:
        usage = await tracker.track_usage(
            user_id="user123",
            agent_id="neuroscientist",
            task_id="analyze_hrv",
            conversation_id="conv_abc123",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50
        )
        print(f"Cost: ${usage.cost_usd:.4f}")
```

### CrewAI Integration

```python
from auren.monitoring import track_tokens
from crewai import Agent

class TrackedAgent(Agent):
    @track_tokens(model="gpt-4", agent_id="neuroscientist")
    async def analyze_biometrics(self, prompt: str, user_id: str):
        # Your LLM call here
        return response
```

### Decorator Usage

```python
from auren.monitoring import track_tokens

@track_tokens(model="gpt-4", agent_id="nutritionist")
async def generate_meal_plan(prompt: str, user_id: str):
    # Your LLM call here
    return meal_plan
```

## 📈 Monitoring

### User Statistics
```python
stats = await tracker.get_user_stats("user123")
print(f"Today: ${stats['today']['spent']:.2f} / ${stats['today']['limit']:.2f}")
```

### Budget Management
```python
# Set custom daily limit
await tracker.set_user_limit("user123", 25.0)

# Check if user has budget remaining
try:
    await tracker.track_usage(...)
except BudgetExceededException as e:
    print(f"Budget exceeded: {e}")
```

## 🏗️ Architecture

### Redis Data Structure
- **Usage Records**: `usage:{request_id}` (24hr TTL)
- **Daily Totals**: `daily:{user_id}:{date}` (48hr TTL)
- **Agent Costs**: `agent:{agent_id}:{date}` (48hr TTL)
- **Hourly Metrics**: `hourly:{YYYY-MM-DD:HH}` (1hr TTL)
- **Conversation History**: `conversation:{conversation_id}` (2hr TTL)

### Supported Models
- **OpenAI**: gpt-4, gpt-4-turbo, gpt-3.5-turbo, gpt-4o
- **Anthropic**: claude-3-opus, claude-3-sonnet, claude-3-haiku
- **Self-hosted**: llama-3.1-70b, llama-3.1-8b

### Pricing (per 1K tokens)
- GPT-4: $0.03 prompt / $0.06 completion
- GPT-4-turbo: $0.01 prompt / $0.03 completion
- GPT-3.5-turbo: $0.0005 prompt / $0.0015 completion
- Claude-3-opus: $0.015 prompt / $0.075 completion

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/test_token_tracking.py -v
```

### Manual Testing
```bash
python scripts/test_redis_tracking.py
```

### Redis Verification
```bash
# Connect to Redis
redis-cli

# Check user stats
HGETALL "daily:user123:2024-01-15"

# Check recent usage
KEYS "usage:*"
```

## 🔧 Configuration

### Environment Variables
```bash
# Redis connection
REDIS_URL=redis://localhost:6379

# Default daily limit
DEFAULT_DAILY_LIMIT=10.0

# Warning threshold
BUDGET_WARNING_THRESHOLD=0.8
```

### Custom Pricing
Update `auren/config/token_config.py` to add new models or adjust pricing.

## 🚨 Error Handling

### Budget Exceeded
```python
from auren.monitoring import BudgetExceededException

try:
    await tracker.track_usage(...)
except BudgetExceededException as e:
    # Handle budget exceeded
    logger.warning(f"User exceeded budget: {e}")
```

### Rate Limiting
```python
from auren.monitoring import RateLimitExceededException

@track_tokens(rate_limit=50, rate_limit_window=60)
async def limited_function():
    # Rate limited to 50 requests per minute
    pass
```

## 📊 Dashboard Ideas

Build monitoring dashboards showing:
- Real-time token usage across all agents
- Cost breakdown by user and agent
- Budget utilization warnings
- Hourly usage patterns
- Most expensive prompts
- Failed requests due to budget

## 🔄 Integration Examples

### With Cognitive Twin
```python
from auren.memory import CognitiveTwinProfile
from auren.monitoring import TokenTracker

async def track_with_context(cognitive_profile: CognitiveTwinProfile):
    tracker = TokenTracker()
    async with tracker:
        # Track usage with cognitive context
        usage = await tracker.track_usage(
            user_id=cognitive_profile.user_id,
            agent_id="specialist",
            task_id="biometric_analysis",
            conversation_id=cognitive_profile.get_summary()["conversation_id"],
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            metadata={
                "cognitive_context": cognitive_profile.get_summary()
            }
        )
```

## 📝 Best Practices

1. **Always use async context manager** for automatic connection handling
2. **Set appropriate daily limits** based on user tiers
3. **Use decorators** for automatic tracking in CrewAI agents
4. **Monitor Redis memory usage** with TTL settings
5. **Implement graceful degradation** when budget is exceeded
6. **Log budget warnings** for proactive management

## 🔍 Troubleshooting

### Common Issues

**Redis Connection Failed**
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG
```

**Token Counting Inaccurate**
- Ensure tiktoken is installed: `pip install tiktoken`
- Check model mappings in tokenizer service

**Budget Not Enforced**
- Verify Redis connection is established
- Check user limit is set correctly

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 Production Deployment

### Docker Compose
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  auren:
    build: .
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379
