# AUREN Biometric Bridge - Operational Runbook

**Version**: 1.0  
**Last Updated**: January 27, 2025  
**Service**: Biometric Bridge API

---

## Service Overview

The Biometric Bridge processes webhook data from wearable devices (Oura, Whoop, Apple HealthKit) and streams it to Kafka for LangGraph consumption.

**Key Components:**
- FastAPI webhook endpoints
- Concurrent processor with semaphore control
- PostgreSQL event storage
- Redis caching layer
- Kafka event streaming

---

## Common Operations

### Starting the Service

**Docker:**
```bash
docker-compose up -d biometric-bridge
```

**Kubernetes:**
```bash
kubectl apply -f biometric-bridge-deployment.yaml
kubectl rollout status deployment/biometric-bridge
```

**Local Development:**
```bash
python3 -m uvicorn api:app --host 0.0.0.0 --port 8000
```

### Health Checks

**Liveness:**
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"biometric-bridge"}
```

**Readiness:**
```bash
curl http://localhost:8000/ready
# Expected: All dependencies "healthy"
```

### Monitoring

**Prometheus Metrics:**
```
http://localhost:9000/metrics
```

**Key Metrics to Watch:**
- `webhook_events_total` - Processing rate
- `webhook_events_failed_total` - Error rate
- `active_webhook_tasks` - Current load
- `semaphore_wait_seconds` - Back-pressure indicator

---

## Troubleshooting

### High Semaphore Wait Times

**Symptoms:**
- `semaphore_wait_seconds` > 1s
- Webhook response times increasing

**Resolution:**
1. Check `active_webhook_tasks` metric
2. If consistently near 50, scale horizontally:
   ```bash
   kubectl scale deployment biometric-bridge --replicas=3
   ```
3. Consider increasing `MAX_CONCURRENT_WEBHOOKS` (carefully)

### Kafka Queue Backing Up

**Symptoms:**
- AsyncKafkaQueue depth > 100
- Logs show "Kafka queue full"

**Resolution:**
1. Check Kafka broker health:
   ```bash
   kafka-topics.sh --bootstrap-server localhost:9092 --list
   ```
2. Verify topic exists:
   ```bash
   kafka-topics.sh --create --topic biometric-events --partitions 6
   ```
3. Check for consumer lag

### OAuth Token Refresh Failures

**Symptoms:**
- `authentication_error` in logs
- Whoop webhooks failing

**Resolution:**
1. Check Redis connectivity:
   ```bash
   redis-cli ping
   ```
2. Verify refresh token in database:
   ```sql
   SELECT user_id, updated_at FROM user_oauth_tokens 
   WHERE provider='whoop' AND user_id='affected_user';
   ```
3. Manually refresh if needed (see procedures)

### Rate Limiting

**Symptoms:**
- `rate_limit_error` in metrics
- "Rate limited, waiting Xs" in logs

**Resolution:**
1. Check rate limit headers in responses
2. Verify backoff is working (should see retry logs)
3. Contact wearable API support if persistent
4. Consider implementing request queuing

---

## Emergency Procedures

### Service Outage

1. **Immediate Actions:**
   - Check service health: `/health` endpoint
   - Review recent deployments
   - Check infrastructure dependencies

2. **Rollback if Needed:**
   ```bash
   kubectl rollout undo deployment/biometric-bridge
   ```

3. **Verify Recovery:**
   - Monitor error rates returning to normal
   - Check for message loss in DLQ

### Database Connection Loss

**PostgreSQL Down:**
1. Service will return 503s automatically
2. Check RDS status in AWS console
3. Verify connection string is correct
4. No manual intervention needed - auto-reconnects

### Redis Failure

**Service Behavior:**
- Continues operating without cache
- Performance degradation expected
- OAuth tokens may need more refreshes

**Recovery:**
1. Service auto-recovers when Redis returns
2. Cache will rebuild automatically
3. Monitor cache hit rates returning to normal

### Kafka Broker Failure

**Service Behavior:**
- Messages queue in memory (max 1000)
- After queue full, webhooks return 503
- No data loss - webhooks will retry

**Recovery:**
1. Fix Kafka cluster
2. Service auto-resumes publishing
3. Monitor queue depth returning to zero

---

## Maintenance Procedures

### Rotating API Credentials

**Oura Token:**
```bash
# Update environment variable
kubectl set env deployment/biometric-bridge OURA_ACCESS_TOKEN=new_token
# Deployment auto-restarts
```

**Whoop OAuth:**
```bash
# Update both client ID and secret
kubectl create secret generic whoop-oauth \
  --from-literal=client_id=new_id \
  --from-literal=client_secret=new_secret \
  --dry-run=client -o yaml | kubectl apply -f -
```

### Database Maintenance

**Cleanup Old Events (monthly):**
```sql
DELETE FROM biometric_events 
WHERE created_at < NOW() - INTERVAL '90 days';

VACUUM ANALYZE biometric_events;
```

**DLQ Processing:**
```sql
-- Review failed messages
SELECT topic, error_message, COUNT(*) 
FROM kafka_dlq 
WHERE processed_at IS NULL 
GROUP BY topic, error_message;

-- Retry specific messages
UPDATE kafka_dlq 
SET retry_count = 0, processed_at = NULL 
WHERE id IN (select_ids);
```

### Scaling Guidelines

**When to Scale:**
- Sustained `active_webhook_tasks` > 40
- P99 latency > 150ms
- Semaphore wait times > 2s

**Horizontal Scaling:**
```bash
# Add nodes
kubectl scale deployment biometric-bridge --replicas=N

# Verify even distribution
kubectl get pods -o wide
```

---

## Monitoring Alerts

### Critical Alerts

1. **Service Down**
   - Condition: Health check fails 3x
   - Action: Check logs, restart if needed

2. **High Error Rate**
   - Condition: Error rate > 5% for 5 min
   - Action: Check error types, review recent changes

3. **Database Connection Pool Exhausted**
   - Condition: No available connections
   - Action: Scale service or increase pool size

### Warning Alerts

1. **High Semaphore Wait**
   - Condition: P95 > 5s
   - Action: Consider scaling

2. **Kafka Queue Depth**
   - Condition: > 500 messages
   - Action: Check Kafka health

3. **Low Cache Hit Rate**
   - Condition: < 50%
   - Action: Check Redis memory/evictions

---

## Performance Tuning

### Optimal Settings

```env
# Production tested values
MAX_CONCURRENT_WEBHOOKS=40
REDIS_TTL_SECONDS=300
MAX_TIMESERIES_ENTRIES=5000
PG_POOL_MIN_SIZE=10
PG_POOL_MAX_SIZE=30
AIOHTTP_CONNECTOR_LIMIT=100
```

### Batch Size Optimization

**HealthKit Processing:**
- Optimal: 100-500 samples per batch
- Max throughput at ~200 samples
- Diminishing returns > 500

### Redis Memory Management

**Monitor Usage:**
```bash
redis-cli info memory
```

**If Memory Pressure:**
1. Reduce `MAX_TIMESERIES_ENTRIES`
2. Lower `REDIS_TTL_SECONDS`
3. Add Redis nodes (cluster mode)

---

## Integration Testing

### Webhook Testing

**Send Test Webhook:**
```bash
# Oura test
curl -X POST http://localhost:8000/webhooks/oura \
  -H "Content-Type: application/json" \
  -d '{"event_type":"sleep.updated","user_id":"test_123"}'

# Check processing
curl http://localhost:8000/ready
```

### Load Testing

**Using Locust:**
```bash
locust -f tests/load/locustfile.py \
  --host=http://localhost:8000 \
  --users=50 \
  --spawn-rate=5
```

**Expected Results:**
- 50 users: < 100ms response time
- 100 users: Some semaphore waiting
- 200 users: Back-pressure activated

---

## Contact Information

**On-Call Rotation:** #biometric-bridge-oncall  
**Escalation:** Platform Team Lead  
**Vendor Support:**
- Oura API: support@ouraring.com
- Whoop API: api-support@whoop.com
- Apple HealthKit: developer.apple.com/contact

---

**Remember:** The service is designed to fail safely. When in doubt, let it recover automatically before manual intervention. 