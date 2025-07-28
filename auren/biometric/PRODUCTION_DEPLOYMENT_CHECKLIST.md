# AUREN Biometric Bridge - Production Deployment Checklist

**Version**: 2.0  
**Date**: January 27, 2025  
**Approved By**: Lead Architect

---

## Pre-Deployment Tasks

### Code Preparation ⏰ (2 hours before deployment)

- [ ] **Apply Metric Namespace Prefix**
  ```bash
  # Update all Prometheus metrics to include "auren_" prefix
  sed -i 's/Counter("webhook_/Counter("auren_webhook_/g' bridge.py
  sed -i 's/Histogram("webhook_/Histogram("auren_webhook_/g' bridge.py
  sed -i 's/Gauge("active_/Gauge("auren_active_/g' bridge.py
  sed -i 's/Histogram("biometric_/Histogram("auren_biometric_/g' bridge.py
  sed -i 's/Histogram("semaphore_/Histogram("auren_semaphore_/g' bridge.py
  ```

- [ ] **Tag Release**
  ```bash
  git tag -a v2.0 -m "Production release - Biometric Bridge"
  git push origin v2.0
  ```

- [ ] **Build Docker Image**
  ```bash
  docker build -t auren/biometric-bridge:v2.0 .
  docker push auren/biometric-bridge:v2.0
  ```

### Infrastructure Verification ⏰ (1 hour before)

- [ ] **PostgreSQL Setup**
  - Verify RDS instance: db.r5.xlarge
  - Run schema migration: `psql -f schema.sql`
  - Verify tables created: `biometric_events`, `user_oauth_tokens`, `kafka_dlq`

- [ ] **Redis Setup**
  - Verify ElastiCache instance: cache.r6g.large
  - Test connectivity: `redis-cli ping`
  - Verify memory available: >4GB

- [ ] **Kafka Setup**
  - Verify MSK cluster: 3 nodes running
  - Create topic: `kafka-topics.sh --create --topic biometric-events --partitions 6`
  - Create DLQ topic: `kafka-topics.sh --create --topic biometric-events.dlq --partitions 3`

### Environment Configuration ⏰ (30 minutes before)

- [ ] **Production Secrets**
  ```bash
  # Verify all secrets are in place
  kubectl get secret biometric-bridge-secrets -o yaml
  ```

- [ ] **Required Environment Variables**
  ```yaml
  MAX_CONCURRENT_WEBHOOKS: "40"
  REDIS_TTL_SECONDS: "300"
  MAX_TIMESERIES_ENTRIES: "5000"
  PG_POOL_MIN_SIZE: "10"
  PG_POOL_MAX_SIZE: "30"
  AIOHTTP_CONNECTOR_LIMIT: "100"
  ```

- [ ] **API Credentials**
  - [ ] OURA_ACCESS_TOKEN set
  - [ ] WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET set
  - [ ] HEALTHKIT_API_KEY set
  - [ ] Webhook secrets configured (if using signature validation)

---

## Deployment Steps

### Initial Deployment (2 nodes)

1. [ ] **Deploy First Node**
   ```bash
   kubectl apply -f biometric-bridge-deployment.yaml
   kubectl scale deployment biometric-bridge --replicas=1
   kubectl rollout status deployment/biometric-bridge
   ```

2. [ ] **Verify Health**
   ```bash
   # Check pod is running
   kubectl get pods -l app=biometric-bridge
   
   # Check health endpoint
   kubectl port-forward deployment/biometric-bridge 8000:8000
   curl http://localhost:8000/health
   curl http://localhost:8000/ready
   ```

3. [ ] **Deploy Second Node**
   ```bash
   kubectl scale deployment biometric-bridge --replicas=2
   kubectl rollout status deployment/biometric-bridge
   ```

4. [ ] **Configure Load Balancer**
   ```bash
   kubectl apply -f biometric-bridge-service.yaml
   kubectl get service biometric-bridge
   ```

### Monitoring Setup

5. [ ] **Prometheus Configuration**
   ```yaml
   # Add to prometheus.yml
   - job_name: 'biometric-bridge'
     kubernetes_sd_configs:
       - role: pod
         namespaces:
           names: ['production']
     relabel_configs:
       - source_labels: [__meta_kubernetes_pod_label_app]
         action: keep
         regex: biometric-bridge
   ```

6. [ ] **Import Grafana Dashboard**
   - Import dashboard JSON from `monitoring/grafana-dashboard.json`
   - Verify all panels showing data
   - Set up alert rules

7. [ ] **Configure Alerts**
   ```yaml
   # Critical alerts to configure
   - Service health check failures
   - Error rate > 5%
   - P99 latency > 150ms
   - Semaphore wait time > 5s
   ```

---

## Post-Deployment Validation

### Functional Testing (First 30 minutes)

- [ ] **Send Test Webhooks**
  ```bash
  # Oura test
  curl -X POST https://api.auren.health/webhooks/oura \
    -H "Content-Type: application/json" \
    -H "X-Oura-Signature: test_sig" \
    -d '{"event_type":"sleep.updated","user_id":"test_prod_001"}'
  
  # Whoop test
  curl -X POST https://api.auren.health/webhooks/whoop \
    -H "Content-Type: application/json" \
    -H "X-Whoop-Signature-256: test_sig" \
    -d '{"type":"recovery.updated","user_id":"test_prod_002"}'
  
  # HealthKit test
  curl -X POST https://api.auren.health/webhooks/healthkit \
    -H "Authorization: Bearer ${HEALTHKIT_API_KEY}" \
    -d '{"user_id":"test_prod_003","samples":[...]}'
  ```

- [ ] **Verify Kafka Messages**
  ```bash
  kafka-console-consumer.sh \
    --bootstrap-server kafka:9092 \
    --topic biometric-events \
    --from-beginning \
    --max-messages 3
  ```

- [ ] **Check PostgreSQL**
  ```sql
  SELECT COUNT(*) FROM biometric_events WHERE user_id LIKE 'test_prod_%';
  -- Should return 3
  ```

### Performance Baseline (First 2 hours)

- [ ] **Record Initial Metrics**
  - P50 latency: _______ ms
  - P99 latency: _______ ms (target < 100ms)
  - Throughput: _______ req/min
  - Error rate: _______ %

- [ ] **Memory Usage**
  - Pod 1: _______ MB
  - Pod 2: _______ MB
  - Redis: _______ MB

### 48-Hour Monitoring Period

- [ ] **Hour 1-4**: Watch for startup issues
- [ ] **Hour 4-8**: Monitor during peak traffic
- [ ] **Hour 8-24**: Check overnight stability
- [ ] **Hour 24-48**: Verify no memory leaks

---

## Rollback Plan

If critical issues occur:

1. [ ] **Immediate Rollback**
   ```bash
   kubectl rollout undo deployment/biometric-bridge
   ```

2. [ ] **Verify Rollback**
   ```bash
   kubectl rollout status deployment/biometric-bridge
   kubectl get pods -l app=biometric-bridge
   ```

3. [ ] **Check for Data Loss**
   - Review Kafka DLQ for unprocessed messages
   - Check PostgreSQL for incomplete transactions

---

## Success Criteria

Deployment is successful when:

- [ ] Both nodes healthy and receiving traffic
- [ ] P99 latency < 100ms sustained
- [ ] Zero critical errors in first 2 hours
- [ ] All test webhooks processed successfully
- [ ] Monitoring dashboards fully operational
- [ ] No memory leaks after 48 hours

---

## Contacts

- **On-Call Engineer**: [Name] - [Phone]
- **Lead Architect**: Available via Slack #biometric-bridge
- **Infrastructure Team**: #infrastructure-support
- **Escalation**: Platform Team Lead

---

## Post-Deployment Actions

After successful 48-hour period:

- [ ] Document any production-specific behaviors
- [ ] Update runbook with production learnings
- [ ] Schedule v2.1 planning meeting
- [ ] Celebrate with team! 🎉

---

**Remember**: This is exactly the caliber of engineering we need to transform how humans understand their health. Deploy with confidence! 