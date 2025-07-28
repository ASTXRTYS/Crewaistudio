# AUREN DOCKER REDUNDANCY CLEANUP & CONFIGURATION GUIDE
## Eliminating Confusion and Establishing Single Source of Truth

*Created: July 28, 2025*  
*Author: Senior Engineer*  
*Purpose: Clean up redundant Docker configurations and establish clear deployment standards*

---

## 🚨 CURRENT PROBLEM ANALYSIS

### Redundancy Statistics:
- **16** Docker images with overlapping functionality
- **12** stopped containers wasting resources
- **8** docker-compose files causing confusion
- **95%** disk usage (critical!)
- **Multiple** entry points (api.py, main.py, complete_biometric_system.py)

### Root Causes:
1. No single source of truth for deployment
2. Multiple attempts at fixing issues created new images
3. Backup directories never cleaned
4. Different team members using different configurations

---

## ✅ THE WORKING CONFIGURATION

After extensive testing, here's what ACTUALLY works:

### Container Configuration:
```yaml
Service Name: biometric-production
Image: auren_deploy_biometric-bridge:latest
Port Mapping: 8888:8888 (external:internal)
Network: auren-network
```

### Required Environment Variables:
```bash
POSTGRES_HOST=auren-postgres
POSTGRES_USER=auren_user
POSTGRES_PASSWORD=auren_password_2024  # NOT auren_secure_2025!
POSTGRES_DB=auren_production
REDIS_HOST=auren-redis
KAFKA_BOOTSTRAP_SERVERS=auren-kafka:9092
OPENAI_API_KEY=<your-key>
ENVIRONMENT=production
DISABLE_TEST_EVENTS=false
```

### Working Command:
```bash
docker run -d \
  --name biometric-production \
  --network auren-network \
  -p 8888:8888 \
  -e POSTGRES_HOST=auren-postgres \
  -e POSTGRES_USER=auren_user \
  -e POSTGRES_PASSWORD=auren_password_2024 \
  -e POSTGRES_DB=auren_production \
  -e REDIS_HOST=auren-redis \
  -e KAFKA_BOOTSTRAP_SERVERS=auren-kafka:9092 \
  -e OPENAI_API_KEY="<your-key>" \
  -e DISABLE_TEST_EVENTS=false \
  -e ENVIRONMENT=production \
  auren_deploy_biometric-bridge:latest
```

---

## 🧹 CLEANUP PLAN

### Phase 1: Stop All Conflicting Services
```bash
# Stop all biometric-related containers
docker stop $(docker ps -a | grep -E "biometric|auren" | grep -v "postgres\|redis\|kafka\|grafana\|prometheus" | awk '{print $1}')

# Remove stopped containers
docker rm $(docker ps -a -f status=exited | grep -E "biometric|auren" | awk '{print $1}')
```

### Phase 2: Clean Docker Images
```bash
# List images to review
docker images | grep -E "(biometric|auren)" | grep -v "latest"

# Remove old/unused images (keep only latest)
docker rmi $(docker images | grep -E "biometric-backup|section-12" | grep -v "latest" | awk '{print $3}')

# Clean dangling images
docker image prune -f
```

### Phase 3: Consolidate Docker Compose Files
```bash
# Move extra compose files to archive
mkdir -p /opt/auren_deploy/archive/docker-compose
mv /opt/auren_deploy/docker-compose.dev.yml /opt/auren_deploy/archive/docker-compose/
mv /opt/auren_deploy/auren/docker/docker-compose.yml /opt/auren_deploy/archive/docker-compose/
# Keep only docker-compose.prod.yml as the source of truth
```

### Phase 4: Clean Backup Directories
```bash
# Archive old backups
mkdir -p /opt/archive
mv /opt/auren_deploy_backup_* /opt/archive/

# Or remove if not needed (saves ~2GB)
rm -rf /opt/auren_deploy_backup_*
```

### Phase 5: Docker System Cleanup
```bash
# Clean build cache
docker builder prune -f

# Clean volumes not in use
docker volume prune -f

# Full system prune (careful!)
docker system prune -a --volumes -f
```

---

## 📋 STANDARD DEPLOYMENT PROCEDURE

### 1. Pre-deployment Checklist:
- [ ] Verify PostgreSQL password: `auren_password_2024`
- [ ] Ensure support services running: postgres, redis, kafka
- [ ] Check disk space: `df -h /`
- [ ] Stop any existing biometric services

### 2. Deploy Command:
```bash
# Always use this exact command
docker run -d \
  --name biometric-production \
  --network auren-network \
  -p 8888:8888 \
  --env-file /opt/auren_deploy/.env.production \
  auren_deploy_biometric-bridge:latest
```

### 3. Verify Deployment:
```bash
# Check health
curl -s http://localhost:8888/health | jq .

# Test webhook
curl -X POST http://localhost:8888/webhooks/oura \
  -H "Content-Type: application/json" \
  -d '{"event_type":"test","user_id":"test","data":{"readiness":85}}' \
  -s | jq .
```

---

## 🏗️ PROPER DOCKER STRUCTURE

### Recommended Directory Structure:
```
/opt/auren_deploy/
├── docker-compose.prod.yml     # SINGLE compose file
├── .env.production             # Production environment
├── Dockerfile                  # SINGLE Dockerfile
├── complete_biometric_system.py # Main application
└── requirements.txt            # Python dependencies
```

### Docker Compose Template:
```yaml
version: '3.8'

services:
  biometric-production:
    image: auren_deploy_biometric-bridge:latest
    container_name: biometric-production
    networks:
      - auren-network
    ports:
      - "8888:8888"
    env_file:
      - .env.production
    depends_on:
      - postgres
      - redis
      - kafka
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8888/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  postgres:
    image: timescale/timescaledb:latest-pg16
    container_name: auren-postgres
    # ... rest of config

  redis:
    image: redis:7-alpine
    container_name: auren-redis
    # ... rest of config

  kafka:
    image: bitnami/kafka:3.5
    container_name: auren-kafka
    # ... rest of config

networks:
  auren-network:
    external: true
```

---

## 🚀 QUICK START AFTER CLEANUP

```bash
# 1. Ensure network exists
docker network create auren-network 2>/dev/null || true

# 2. Start support services
docker-compose -f docker-compose.prod.yml up -d postgres redis kafka

# 3. Wait for services
sleep 30

# 4. Start biometric service
docker-compose -f docker-compose.prod.yml up -d biometric-production

# 5. Verify
curl -s http://localhost:8888/health | jq .
```

---

## ⚠️ COMMON MISTAKES TO AVOID

1. **Wrong PostgreSQL Password**: Use `auren_password_2024`, NOT `auren_secure_2025`
2. **Multiple Images**: Don't create new images for fixes, update the existing one
3. **Port Confusion**: Always use 8888 externally
4. **Network Issues**: All services must be on `auren-network`
5. **Missing Dependencies**: The working image is `auren_deploy_biometric-bridge:latest`

---

## 📊 EXPECTED RESULTS AFTER CLEANUP

- Docker images: 5-6 (one per service)
- Running containers: 5 (postgres, redis, kafka, biometric, grafana/prometheus)
- Disk usage: < 70%
- Response time: < 300ms
- Memory usage: < 4GB total

---

## 🔍 MONITORING & MAINTENANCE

### Daily Checks:
```bash
# Check disk space
df -h /

# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Check logs for errors
docker logs biometric-production --tail 50 | grep -i error
```

### Weekly Cleanup:
```bash
# Remove old logs
docker logs biometric-production 2>&1 | tail -10000 > /var/log/biometric.log
docker logs biometric-production --since 7d > /dev/null

# Clean unused images
docker image prune -f
```

---

## 📝 DOCUMENTATION STANDARDS

Going forward:
1. ONE docker-compose.prod.yml file
2. ONE Dockerfile per service
3. Environment variables in .env files
4. Document ANY changes in this guide
5. Tag images with dates: `auren-biometric:20250728`

---

*This guide ensures consistent, clean deployments without the confusion of multiple overlapping configurations.* 