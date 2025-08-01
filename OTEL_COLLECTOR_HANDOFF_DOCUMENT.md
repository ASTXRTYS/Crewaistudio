# 📋 OpenTelemetry Collector Setup - Engineering Handoff Document

**Date**: August 1, 2025  
**From**: Senior Engineer (Claude Opus 4)  
**To**: Next Engineer  
**Priority**: Medium  
**Estimated Time**: 30-45 minutes

---

## 🎯 Executive Summary

The OpenTelemetry (OTel) Collector is partially deployed but needs configuration fixes to properly route traces from NEUROS to Tempo. Once completed, AUREN will have full distributed tracing capabilities, allowing trace-to-metrics correlation and service dependency visualization.

**Current Status**: 🟡 Partially Complete
- ✅ Tempo is deployed and running
- ✅ NEUROS is configured to send traces
- ❌ OTel Collector needs configuration fixes
- ❌ Integration between components pending

---

## 📍 Current State

### What's Working:
1. **Tempo** (Trace Storage)
   - Container: `auren-tempo`
   - Port: 3200
   - Status: ✅ Running
   - Config: `/opt/tempo/tempo-simple.yaml`

2. **NEUROS** (Trace Producer)
   - Container: `neuros-advanced`
   - Configured with: `OTEL_EXPORTER_OTLP_ENDPOINT=http://auren-otel-collector:4318/v1/traces`
   - OpenTelemetry instrumentation: ✅ Enabled

3. **Prometheus** (Metrics)
   - Container: `auren-prometheus`
   - Port: 9090
   - Status: ✅ Running and collecting metrics

### What Needs Fixing:
1. **OTel Collector**
   - Container keeps restarting
   - Config syntax issues in the original file
   - Simplified config created but not deployed

---

## 🔧 Step-by-Step Fix Instructions

### Step 1: Remove Failed OTel Collector Container
```bash
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 \
  'docker rm -f auren-otel-collector 2>/dev/null || true'
```

### Step 2: Deploy OTel Collector with Simplified Config
```bash
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 'docker run -d \
  --name auren-otel-collector \
  --network auren-network \
  -v /opt/otel/otel-collector-simple.yaml:/etc/otel-collector-config.yaml \
  -p 4317:4317 \
  -p 4318:4318 \
  -p 9464:9464 \
  --restart unless-stopped \
  otel/opentelemetry-collector:latest \
  --config=/etc/otel-collector-config.yaml'
```

### Step 3: Verify OTel Collector is Running
```bash
# Check container status
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 \
  'docker ps | grep otel-collector'

# Check logs (should see "Everything is ready. Begin running and processing data."
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 \
  'docker logs auren-otel-collector --tail 20'
```

### Step 4: Test Trace Flow
```bash
# Generate a trace by calling NEUROS
curl -X POST http://144.126.215.218:8000/api/agents/neuros/analyze \
  -H "Content-Type: application/json" \
  -d '{"message": "OTel trace test", "user_id": "test-traces"}'

# Check if OTel Collector received the trace
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 \
  'docker logs auren-otel-collector 2>&1 | grep -i "trace"'
```

### Step 5: Configure Tempo Datasource in Grafana

1. Open Grafana: http://144.126.215.218:3000 (admin/admin)
2. Go to Configuration → Data Sources
3. Click "Add data source"
4. Select "Tempo"
5. Configure:
   - Name: `AUREN-Tempo`
   - URL: `http://auren-tempo:3200`
   - Click "Save & Test"

### Step 6: Create Tempo Provisioning File
```bash
# Create Tempo datasource provisioning
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 'cat > /opt/grafana/provisioning/datasources/tempo.yaml << EOF
apiVersion: 1

datasources:
  - name: AUREN-Tempo
    type: tempo
    access: proxy
    url: http://auren-tempo:3200
    isDefault: false
    editable: false
    jsonData:
      httpMethod: GET
      serviceMap:
        datasourceUid: AUREN-Prometheus
EOF'

# Restart Grafana to load new datasource
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 \
  'docker restart auren-grafana'
```

---

## 📁 Configuration Files Reference

### 1. OTel Collector Config (`/opt/otel/otel-collector-simple.yaml`)
```yaml
# Simplified config that should work
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s

exporters:
  otlp/tempo:
    endpoint: auren-tempo:4317
    tls:
      insecure: true
  
  prometheus:
    endpoint: "0.0.0.0:9464"

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [otlp/tempo]
    
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus]
```

### 2. Alternative: Use Official OTel Collector Image
If the above doesn't work, try the contrib image which has more receivers/exporters:
```bash
otel/opentelemetry-collector-contrib:latest
```

---

## 🐛 Troubleshooting Guide

### Issue: OTel Collector keeps restarting
**Solution**: Check logs for config errors
```bash
docker logs auren-otel-collector --tail 50
```

### Issue: "Error: cannot unmarshal config"
**Solution**: The YAML formatting is critical. Ensure:
- Proper indentation (2 spaces)
- No tabs
- Correct nesting of sections

### Issue: Traces not appearing in Tempo
**Check**:
1. NEUROS is sending traces: `docker logs neuros-advanced | grep -i otlp`
2. OTel Collector is receiving: `docker logs auren-otel-collector | grep -i trace`
3. Tempo is receiving: `docker logs auren-tempo | grep -i received`

### Issue: Connection refused errors
**Solution**: Ensure all containers are on the same network:
```bash
docker network inspect auren-network
```

---

## ✅ Success Criteria

You'll know the setup is complete when:

1. **OTel Collector Status**
   ```bash
   docker ps | grep otel-collector
   # Should show "Up X minutes" not "Restarting"
   ```

2. **Trace Pipeline Test**
   - Make a request to NEUROS
   - Check Grafana → Explore → Select "AUREN-Tempo" datasource
   - Search for traces in the last hour
   - You should see traces with service name "auren-neuros"

3. **Metrics from OTel**
   - Check Prometheus targets: http://144.126.215.218:9090/targets
   - `otel-collector:9464` should be UP

---

## 🎯 Expected Outcome

Once properly configured, the data flow will be:

```
NEUROS (Port 8000)
    ↓ [OTLP/HTTP on port 4318]
OTel Collector
    ↓ [OTLP/gRPC on port 4317]
Tempo (Port 3200)
    ↓
Grafana (Port 3000) → Visualize traces
```

This enables:
- Full request tracing across services
- Trace-to-metrics correlation
- Service dependency mapping
- Latency breakdown analysis

---

## 🚀 Advanced Configuration (Optional)

Once basic setup works, consider adding:

1. **Trace Sampling** (reduce volume)
   ```yaml
   processors:
     probabilistic_sampler:
       sampling_percentage: 10  # Keep 10% of traces
   ```

2. **Resource Attributes**
   ```yaml
   processors:
     resource:
       attributes:
         - key: environment
           value: production
           action: insert
   ```

3. **Tail Sampling** (smart sampling)
   ```yaml
   processors:
     tail_sampling:
       policies:
         - name: errors
           type: status_code
           status_code: {status_codes: [ERROR]}
         - name: slow
           type: latency
           latency: {threshold_ms: 1000}
   ```

---

## 📞 Context & Support

- **Previous Work**: See `OPENTELEMETRY_INFRASTRUCTURE_HANDOFF_REPORT.md`
- **Full Observability Summary**: See `ENTERPRISE_OBSERVABILITY_COMPLETE_SUMMARY.md`
- **Server Access**: `root@144.126.215.218` (password in CREDENTIALS_VAULT.md)
- **Network**: All containers use `auren-network`

---

## 📝 Final Notes

The OTel Collector is the last piece needed for complete observability. Once running, AUREN will have:
- ✅ Metrics (Prometheus)
- ✅ Logs (Docker logs)
- ✅ Traces (Tempo via OTel)
- ✅ Dashboards (Grafana)

This completes the "three pillars of observability" and puts AUREN's monitoring on par with major tech companies.

Good luck! The setup should take 30-45 minutes if following the steps above.

---

*"Traces complete the observability story."*  
*- AUREN Platform Team*