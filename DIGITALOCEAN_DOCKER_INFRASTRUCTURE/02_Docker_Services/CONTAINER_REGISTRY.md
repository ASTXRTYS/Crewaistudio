# CONTAINER REGISTRY DOCUMENTATION

**Version**: 1.0  
**Last Updated**: January 20, 2025  
**Author**: AUREN DevOps Team  
**Review Cycle**: Quarterly  

---

## 📦 Executive Summary

This document outlines container registry strategies for AUREN, including setup, image management, security scanning, and automated build pipelines.

**Registry Options:**
1. **Docker Hub** - Public/Private repositories
2. **DigitalOcean Container Registry** - Integrated with droplets
3. **Self-Hosted Registry** - Complete control
4. **GitHub Container Registry** - CI/CD integration

---

## 🚀 Current Setup

### Local Development
```bash
# Current workflow
docker build -t auren-api:latest .
docker tag auren-api:latest auren-api:v1.0.0
docker-compose up -d

# Images stored locally
docker images | grep auren
```

### Production Deployment
```bash
# Currently building on server
scp -r . root@144.126.215.218:/root/auren-production/
ssh root@144.126.215.218 "cd /root/auren-production && docker-compose build"
```

**Issues with Current Approach:**
- Long deployment times
- Inconsistent builds
- No version control
- No security scanning
- Large transfer sizes

---

## 🏗️ DigitalOcean Container Registry Setup

### 1. Create Registry

```bash
# Using DigitalOcean CLI
doctl registry create auren-registry --region nyc3

# Or via web console:
# 1. Go to Container Registry
# 2. Click "Create Registry"
# 3. Name: auren-registry
# 4. Choose plan (Starter free for 500MB)
```

### 2. Configure Docker Authentication

```bash
# Login to registry
doctl registry login

# Or manual login
docker login registry.digitalocean.com
# Username: <your-do-token>
# Password: <your-do-token>

# Verify authentication
docker pull registry.digitalocean.com/auren-registry/test
```

### 3. Update Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  auren-api:
    image: registry.digitalocean.com/auren-registry/auren-api:${VERSION:-latest}
    # ... rest of config

  nginx:
    image: registry.digitalocean.com/auren-registry/auren-nginx:${VERSION:-latest}
    # ... rest of config
```

---

## 📋 Image Naming Convention

### Tagging Strategy

```
registry.digitalocean.com/auren-registry/[service-name]:[tag]

Tags:
- latest     - Latest stable build
- dev        - Development build
- v1.0.0     - Semantic version
- main-abc123 - Branch and commit
- 20250120   - Date-based
```

### Examples
```bash
# Production release
registry.digitalocean.com/auren-registry/auren-api:v1.2.3

# Development build
registry.digitalocean.com/auren-registry/auren-api:dev-feature-xyz

# Dated build
registry.digitalocean.com/auren-registry/auren-api:20250120-1430
```

---

## 🔄 Build Pipeline

### Local Build & Push

```bash
#!/bin/bash
# build_and_push.sh

# Configuration
REGISTRY="registry.digitalocean.com/auren-registry"
VERSION=${1:-latest}

# Services to build
SERVICES=("auren-api" "auren-nginx" "biometric-bridge")

# Login to registry
doctl registry login

# Build and push each service
for SERVICE in "${SERVICES[@]}"; do
  echo "Building $SERVICE:$VERSION..."
  
  # Build image
  docker build -t $SERVICE:$VERSION -f Dockerfile.$SERVICE .
  
  # Tag for registry
  docker tag $SERVICE:$VERSION $REGISTRY/$SERVICE:$VERSION
  docker tag $SERVICE:$VERSION $REGISTRY/$SERVICE:latest
  
  # Push to registry
  docker push $REGISTRY/$SERVICE:$VERSION
  docker push $REGISTRY/$SERVICE:latest
  
  echo "✓ $SERVICE pushed successfully"
done

echo "All images pushed to registry"
```

### Automated CI/CD Build

```yaml
# .github/workflows/docker-build.yml
name: Build and Push Docker Images

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v2
      
      - name: Login to DO Registry
        uses: docker/login-action@v2
        with:
          registry: registry.digitalocean.com
          username: ${{ secrets.DO_REGISTRY_TOKEN }}
          password: ${{ secrets.DO_REGISTRY_TOKEN }}
      
      - name: Build and push API
        uses: docker/build-push-action@v4
        with:
          context: .
          file: Dockerfile.api
          push: true
          tags: |
            registry.digitalocean.com/auren-registry/auren-api:latest
            registry.digitalocean.com/auren-registry/auren-api:${{ github.sha }}
          cache-from: type=registry,ref=registry.digitalocean.com/auren-registry/auren-api:buildcache
          cache-to: type=registry,ref=registry.digitalocean.com/auren-registry/auren-api:buildcache,mode=max
```

---

## 🔒 Security Scanning

### 1. Trivy Integration

```bash
# Install Trivy
wget https://github.com/aquasecurity/trivy/releases/download/v0.48.0/trivy_0.48.0_Linux-64bit.deb
dpkg -i trivy_0.48.0_Linux-64bit.deb

# Scan image before push
trivy image --severity HIGH,CRITICAL auren-api:latest

# Scan registry image
trivy image registry.digitalocean.com/auren-registry/auren-api:latest

# Generate report
trivy image --format json --output scan-results.json auren-api:latest
```

### 2. Automated Scanning Pipeline

```bash
#!/bin/bash
# security_scan.sh

IMAGE=$1
THRESHOLD=${2:-HIGH}

echo "Scanning $IMAGE for vulnerabilities..."

# Run Trivy scan
trivy image --severity $THRESHOLD --exit-code 1 $IMAGE

if [ $? -eq 0 ]; then
  echo "✓ No $THRESHOLD vulnerabilities found"
  exit 0
else
  echo "✗ Vulnerabilities found! Image push blocked."
  trivy image --severity $THRESHOLD $IMAGE
  exit 1
fi
```

### 3. DigitalOcean Vulnerability Scanning

```bash
# Enable scanning in registry
doctl registry configure vulnerability-scanning --enable

# Check scan results
doctl registry repository list-tags auren-registry/auren-api --format "Tag,Vulnerabilities"
```

---

## 🧹 Registry Maintenance

### 1. Cleanup Old Images

```bash
#!/bin/bash
# cleanup_registry.sh

# Keep last 10 versions
KEEP_LAST=10

# Get all tags
TAGS=$(doctl registry repository list-tags auren-registry/auren-api --format Tag --no-header | sort -V)

# Count tags
TOTAL=$(echo "$TAGS" | wc -l)

if [ $TOTAL -gt $KEEP_LAST ]; then
  # Calculate how many to delete
  DELETE_COUNT=$((TOTAL - KEEP_LAST))
  
  # Get tags to delete (oldest)
  DELETE_TAGS=$(echo "$TAGS" | head -n $DELETE_COUNT)
  
  # Delete old tags
  for TAG in $DELETE_TAGS; do
    echo "Deleting auren-api:$TAG..."
    doctl registry repository delete-tag auren-registry/auren-api $TAG --force
  done
fi
```

### 2. Garbage Collection

```bash
# Run garbage collection
doctl registry garbage-collection start --force

# Check status
doctl registry garbage-collection get-active

# Schedule weekly cleanup (crontab)
0 2 * * 0 /root/scripts/cleanup_registry.sh
```

### 3. Storage Management

```bash
# Check registry usage
doctl registry get

# Monitor image sizes
doctl registry repository list

# Set retention policy
# Via web console: Settings → Retention Policy → 30 days
```

---

## 🔄 Multi-Stage Builds

### Optimize Image Size

```dockerfile
# Dockerfile.api - Multi-stage build
# Stage 1: Build
FROM python:3.11-slim AS builder

WORKDIR /build
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

# Copy only necessary files
COPY --from=builder /root/.local /root/.local
COPY ./auren /app/auren

WORKDIR /app
ENV PATH=/root/.local/bin:$PATH

CMD ["python", "-m", "uvicorn", "auren.api.dashboard_api_minimal:app"]
```

### Build Optimization

```yaml
# docker-compose.build.yml
version: '3.8'

services:
  auren-api:
    build:
      context: .
      dockerfile: Dockerfile.api
      cache_from:
        - registry.digitalocean.com/auren-registry/auren-api:buildcache
      args:
        BUILDKIT_INLINE_CACHE: 1
```

---

## 📊 Registry Monitoring

### Metrics to Track

| Metric | Target | Alert |
|--------|--------|-------|
| Image Size | < 500MB | > 1GB |
| Vulnerabilities | 0 Critical | > 0 |
| Storage Usage | < 80% | > 90% |
| Push Success Rate | > 99% | < 95% |
| Pull Latency | < 30s | > 60s |

### Monitoring Script

```bash
#!/bin/bash
# monitor_registry.sh

echo "=== Registry Health Check ==="

# Check registry status
REGISTRY_STATUS=$(doctl registry get --format Status --no-header)
echo "Registry Status: $REGISTRY_STATUS"

# Check storage usage
STORAGE=$(doctl registry get --format "StorageUsageBytes,SizeBytes" --no-header)
USED=$(echo $STORAGE | awk '{print $1}')
TOTAL=$(echo $STORAGE | awk '{print $2}')
PERCENT=$((USED * 100 / TOTAL))
echo "Storage Usage: ${PERCENT}%"

# Check vulnerabilities
echo -e "\nVulnerability Summary:"
doctl registry repository list | tail -n +2 | while read REPO; do
  NAME=$(echo $REPO | awk '{print $1}')
  echo -n "$NAME: "
  doctl registry repository list-tags $NAME --format "Vulnerabilities" --no-header | sort | uniq -c
done

# Alert if issues
if [ "$REGISTRY_STATUS" != "online" ] || [ $PERCENT -gt 80 ]; then
  echo "⚠️  Registry needs attention!"
fi
```

---

## 🚀 Migration Plan

### Phase 1: Setup Registry (Week 1)
1. Create DigitalOcean registry
2. Configure authentication
3. Test push/pull operations
4. Set up vulnerability scanning

### Phase 2: Update Build Process (Week 2)
1. Implement multi-stage builds
2. Create build scripts
3. Test local builds
4. Document procedures

### Phase 3: CI/CD Integration (Week 3)
1. Set up GitHub Actions
2. Automate builds on commit
3. Implement security scanning
4. Configure caching

### Phase 4: Production Migration (Week 4)
1. Update docker-compose.prod.yml
2. Push all images to registry
3. Test deployment
4. Monitor performance

---

## 🔧 Troubleshooting

### Common Issues

#### Authentication Failed
```bash
# Re-authenticate
doctl auth init
doctl registry login

# Check credentials
docker logout registry.digitalocean.com
docker login registry.digitalocean.com
```

#### Push Timeout
```bash
# Increase timeout
export DOCKER_CLIENT_TIMEOUT=300
export COMPOSE_HTTP_TIMEOUT=300

# Retry with smaller layers
docker push --max-concurrent-uploads 2 $IMAGE
```

#### Storage Full
```bash
# Run garbage collection
doctl registry garbage-collection start --force

# Delete unused repositories
doctl registry repository list
doctl registry repository delete $REPO_NAME --force
```

---

## 📝 Best Practices

### Do's ✅
1. Tag every build with version AND latest
2. Scan images before pushing
3. Use multi-stage builds
4. Implement retention policies
5. Monitor registry health

### Don'ts ❌
1. Push development builds to latest
2. Store secrets in images
3. Push without scanning
4. Ignore size optimization
5. Skip cleanup procedures

---

## 🔗 Additional Resources

- [DigitalOcean Registry Docs](https://docs.digitalocean.com/products/container-registry/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Trivy Documentation](https://aquasecurity.github.io/trivy/)
- [Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)

---

*A well-managed container registry is the foundation of reliable deployments. Invest time in automation and security.* 

---

## 🧬 Biometric Bridge Container Registry

### Biometric Bridge Images
```bash
# Build biometric bridge image
docker build -f Dockerfile.api -t auren-biometric-bridge:latest .
docker tag auren-biometric-bridge:latest auren-biometric-bridge:v1.0.0

# Required base images
- python:3.11-slim (base image)
- timescale/timescaledb:latest-pg16 (database)
- redis:7-alpine (checkpointing)
- confluentinc/cp-kafka:7.4.0 (streaming)
```

### DigitalOcean Container Registry Setup for Biometric Bridge
```bash
# 1. Create registry
doctl registry create auren-biometric --subscription-tier starter

# 2. Login to registry
doctl registry login

# 3. Tag biometric bridge image
docker tag auren-biometric-bridge:latest registry.digitalocean.com/auren-biometric/biometric-bridge:latest

# 4. Push to registry
docker push registry.digitalocean.com/auren-biometric/biometric-bridge:latest

# 5. Configure droplet to pull
doctl registry kubernetes-manifest | kubectl apply -f -
```

### Multi-Architecture Support (ARM64/AMD64)
```bash
# Build for multiple architectures
docker buildx create --name biometric-builder
docker buildx use biometric-builder

docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -t registry.digitalocean.com/auren-biometric/biometric-bridge:latest \
  -f Dockerfile.api \
  --push .
```

### Security Scanning for Biometric Services
```yaml
# .github/workflows/biometric-security.yml
name: Biometric Bridge Security Scan

on:
  push:
    paths:
      - 'auren/biometric/**'
      - 'Dockerfile.api'

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'auren-biometric-bridge:latest'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
``` 