# AUREN OBSERVABILITY RUNBOOK

**Created**: January 28, 2025  
**Author**: Senior Engineer  
**Version**: 1.0  
**Purpose**: Operational procedures for monitoring AUREN

---

## 🚨 Quick Reference

### Emergency Contacts
- **On-Call**: Check CREDENTIALS_VAULT.md for contact info
- **Prometheus**: http://144.126.215.218:9090
- **Grafana**: http://144.126.215.218:3000 (admin/auren_grafana_2025)
- **Server SSH**: 144.126.215.218 (use sshpass per SSH_ACCESS_STANDARD.md)

### Critical Dashboards
1. [System Health](http://144.126.215.218:3000/d/auren-system-health)
2. [Webhook Processing](http://144.126.215.218:3000/d/auren-webhooks-events)
3. [Memory Tier Operations](http://144.126.215.218:3000/d/auren-memory-tiers-enhanced)
4. [NEUROS Modes](http://144.126.215.218:3000/d/auren-neuros-modes)

---

## 📋 Daily Monitoring Checklist

### Morning Check (9 AM)
```bash
# 1. Check system health
curl -s http://144.126.215.218:8888/health | jq '.'

# 2. Check Prometheus targets
curl -s http://144.126.215.218:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'

# 3. Check container status
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker ps --format "table {{.Names}}\t{{.Status}}"'

# 4. Review overnight alerts
# Check Grafana alert panel
```

### Midday Check (1 PM)
- Review webhook processing rates in Grafana
- Check memory tier hit rates
- Monitor active connections

### Evening Check (5 PM)
- Review daily error rates
- Check disk usage trends
- Verify backup completion

---

## 🔍 Common Issues & Solutions

### Issue 1: High Webhook Error Rate

**Symptoms**: 
- Error rate > 5% on webhook dashboard
- Alert: "High webhook error rate"

**Investigation**:
```bash
# Check recent errors
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker logs --tail 100 biometric-production | grep ERROR'

# Check specific device errors in Grafana
sum by (device_type, error_type) (rate(auren_webhook_errors_total[5m]))
```

**Resolution**:
1. Identify error type (validation, timeout, internal)
2. Check webhook payload format changes
3. Verify external service availability
4. Scale up if load-related

### Issue 2: Memory Tier Latency

**Symptoms**:
- P95 latency > 1 second
- Alert: "High memory tier latency"

**Investigation**:
```bash
# Check Redis performance
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker exec auren-redis redis-cli --latency'

# Check PostgreSQL connections
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker exec auren-postgres psql -U auren_user -d auren_production -c "SELECT count(*) FROM pg_stat_activity;"'
```

**Resolution**:
1. Check connection pool exhaustion
2. Analyze slow queries
3. Consider cache warming
4. Review tier promotion logic

### Issue 3: Container Restart Loop

**Symptoms**:
- Container showing "Restarting" status
- Services unavailable

**Investigation**:
```bash
# Check container logs
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker logs --tail 50 biometric-production 2>&1'

# Check resource usage
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker stats --no-stream'
```

**Resolution**:
1. Check for syntax errors in logs
2. Verify environment variables
3. Check disk space
4. Restore from backup if needed

### Issue 4: Prometheus Target Down

**Symptoms**:
- Target showing "down" in Prometheus
- Missing metrics in Grafana

**Investigation**:
```bash
# Test endpoint directly
curl -s http://144.126.215.218:8888/metrics | head -10

# Check network connectivity
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker exec auren-prometheus wget -O- http://biometric-production:8888/metrics'
```

**Resolution**:
1. Verify container is running
2. Check network connectivity
3. Verify metrics endpoint exists
4. Restart Prometheus if needed

---

## 📊 Performance Baselines

### Normal Operating Ranges

| Metric | Normal Range | Warning | Critical |
|--------|-------------|---------|----------|
| Webhook Request Rate | 10-100/min | >200/min | >500/min |
| Error Rate | <2% | 2-5% | >5% |
| P95 Latency | <500ms | 500ms-1s | >1s |
| Memory Hot Tier Hit Rate | >85% | 70-85% | <70% |
| Database Connections | <50 | 50-80 | >80 |
| CPU Usage | <50% | 50-80% | >80% |
| Memory Usage | <2GB | 2-3GB | >3GB |

### Peak Traffic Patterns
- **Morning Peak**: 7-9 AM (device syncs)
- **Evening Peak**: 6-8 PM (activity uploads)
- **Weekend**: 20% lower volume

---

## 🚨 Alert Response Procedures

### Severity Levels
- **P1 (Critical)**: Service down, data loss risk
- **P2 (High)**: Performance degraded, errors increasing
- **P3 (Medium)**: Non-critical issues, monitoring
- **P4 (Low)**: Informational, trends

### P1: Service Down

**Response Time**: Immediate

1. **Verify**:
   ```bash
   curl -f http://144.126.215.218:8888/health || echo "Service Down"
   ```

2. **Restart**:
   ```bash
   sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker restart biometric-production'
   ```

3. **Monitor**:
   - Watch container logs
   - Check Grafana for recovery

4. **Escalate** if not resolved in 15 minutes

### P2: High Error Rate

**Response Time**: 30 minutes

1. **Identify** error patterns in Grafana
2. **Check** recent deployments
3. **Scale** if load-related
4. **Rollback** if deployment-related

### P3: Performance Degradation

**Response Time**: 2 hours

1. **Analyze** trends in Grafana
2. **Optimize** slow queries
3. **Adjust** cache settings
4. **Plan** capacity increase

---

## 📈 Capacity Planning

### Monitoring Growth Indicators

```promql
# Weekly growth rate
increase(auren_biometric_events_processed_total[7d]) / increase(auren_biometric_events_processed_total[7d] offset 7d)

# Storage growth projection
predict_linear(auren_memory_tier_size_bytes[7d], 86400 * 30)  # 30 day projection
```

### Scaling Triggers
- Sustained CPU >70% → Add compute
- Memory usage >80% → Increase RAM
- Storage >80% → Expand volumes
- Connection pool >80% → Increase limits

---

## 🔧 Maintenance Procedures

### Weekly Maintenance

**Every Monday at 2 AM**:
1. Backup Prometheus data
2. Rotate logs
3. Clean up old metrics
4. Update dashboards

```bash
# Backup script
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 << 'EOF'
docker exec auren-prometheus tar -czf /prometheus/backup-$(date +%Y%m%d).tar.gz /prometheus/data
docker exec auren-postgres pg_dump -U auren_user auren_production > /backup/db-$(date +%Y%m%d).sql
EOF
```

### Monthly Reviews
- Analyze performance trends
- Review alert thresholds
- Update capacity plans
- Clean old data

---

## 📊 Dashboard Management

### Creating New Dashboards
1. Start with existing template
2. Use queries from GRAFANA_QUERY_LIBRARY.md
3. Set appropriate refresh rates
4. Add to documentation

### Dashboard Best Practices
- Group related metrics
- Use consistent time ranges
- Include data source variables
- Add helpful tooltips

---

## 🚀 Deployment Monitoring

### Pre-Deployment Checklist
- [ ] Backup current metrics
- [ ] Note baseline performance
- [ ] Prepare rollback plan
- [ ] Alert team of deployment

### During Deployment
```bash
# Watch metrics in real-time
watch -n 5 'curl -s http://144.126.215.218:8888/metrics | grep auren_webhook_requests_total'

# Monitor logs
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'docker logs -f biometric-production'
```

### Post-Deployment Verification
- [ ] All targets UP in Prometheus
- [ ] Error rate normal
- [ ] Latency acceptable
- [ ] New metrics visible

---

## 📝 Troubleshooting Tools

### Useful Commands
```bash
# Check all container logs
for container in biometric-production auren-prometheus auren-grafana; do
  echo "=== $container ==="
  sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 "docker logs --tail 20 $container 2>&1"
done

# Export metrics for analysis
curl -s http://144.126.215.218:9090/api/v1/query_range?query=auren_webhook_requests_total&start=$(date -u -d '1 hour ago' +%s)&end=$(date +%s)&step=60

# Check disk usage
sshpass -p '.HvddX+@6dArsKd' ssh root@144.126.215.218 'df -h'
```

### Debug Endpoints
- `/health` - Basic health check
- `/metrics` - Prometheus metrics
- `/ready` - Readiness probe (if implemented)
- `/debug/vars` - Internal state (if implemented)

---

## 📞 Escalation Matrix

| Issue | First Responder | Escalation | Time Limit |
|-------|----------------|------------|------------|
| Service Down | On-Call Engineer | Executive Engineer | 30 min |
| Data Loss | Senior Engineer | Founder | Immediate |
| Performance | On-Call Engineer | Senior Engineer | 2 hours |
| Security | Senior Engineer | Founder | Immediate |

---

## 📚 Additional Resources

- [Metrics Catalog](METRICS_CATALOG.md) - All metric definitions
- [Grafana Query Library](GRAFANA_QUERY_LIBRARY.md) - PromQL queries
- [Docker Navigation Guide](DOCKER_NAVIGATION_GUIDE.md) - Container details
- [Monitoring Guide](../03_DEVELOPMENT/MONITORING_GUIDE.md) - Setup details

---

*This runbook should be reviewed monthly and updated after any major incident.* 