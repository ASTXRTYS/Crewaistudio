# DIGITALOCEAN & DOCKER INFRASTRUCTURE DOCUMENTATION

## Complete Infrastructure Documentation for AUREN on DigitalOcean

This folder contains comprehensive documentation for the entire server infrastructure, Docker services, and deployment architecture running on DigitalOcean.

---

## 🚀 Quick Reference

- **Server IP**: 144.126.215.218
- **Domain**: aupex.ai
- **Provider**: DigitalOcean
- **OS**: Ubuntu (latest LTS)
- **Architecture**: Docker Compose orchestration
- **Services**: 10+ containerized services

---

## 📂 Folder Structure

### [01_Infrastructure_Overview/](01_Infrastructure_Overview/)
High-level architecture and system design documentation.

- **INFRASTRUCTURE_ARCHITECTURE.md** - Complete system architecture
- **DIGITALOCEAN_SETUP.md** - DigitalOcean droplet configuration
- **NETWORK_TOPOLOGY.md** - Network design and service communication
- **SECURITY_ARCHITECTURE.md** - Infrastructure security layers

### [02_Docker_Services/](02_Docker_Services/)
Docker configurations and service documentation.

- **docker-compose.yml** - Development compose file
- **docker-compose.prod.yml** - Production compose file
- **Dockerfile** - Main application Dockerfile
- **Dockerfile.api** - API service Dockerfile
- **SERVICES_DOCUMENTATION.md** - Detailed service descriptions
- **DOCKER_BEST_PRACTICES.md** - Container optimization guide

### [03_Server_Configuration/](03_Server_Configuration/)
Server setup and system configuration.

- **SERVER_SETUP_GUIDE.md** - Initial server configuration
- **NGINX_CONFIGURATION.md** - Web server and reverse proxy
- **FIREWALL_RULES.md** - UFW and security configuration
- **SSH_HARDENING.md** - Secure shell configuration
- **BACKUP_STRATEGY.md** - Backup procedures and recovery

### [04_Deployment_Scripts/](04_Deployment_Scripts/)
Deployment automation and scripts.

- **DEPLOY_NOW.sh** - One-command deployment
- **master_deploy.sh** - Master deployment orchestration
- **remote_deploy.sh** - Remote execution script
- **setup_production.sh** - Production environment setup
- **DEPLOYMENT_PROCEDURES.md** - Step-by-step deployment guide

### [05_Monitoring_Maintenance/](05_Monitoring_Maintenance/)
Monitoring, logging, and maintenance procedures.

- **MONITORING_SETUP.md** - Prometheus, Grafana, health checks
- **LOG_MANAGEMENT.md** - Centralized logging strategy
- **MAINTENANCE_PROCEDURES.md** - Regular maintenance tasks
- **DISASTER_RECOVERY.md** - Recovery procedures
- **PERFORMANCE_TUNING.md** - Optimization guidelines

---

## 🏗️ Infrastructure Overview

### Current Architecture
```
┌─────────────────────────────────────────┐
│         DigitalOcean Droplet            │
│         144.126.215.218                 │
├─────────────────────────────────────────┤
│  Ubuntu LTS + Docker Engine             │
├─────────────────────────────────────────┤
│         Docker Compose Stack            │
│  ┌────────────┐    ┌────────────┐     │
│  │   Nginx    │    │  AUREN API │     │
│  │  (Port 80) │    │ (Port 8080)│     │
│  └────────────┘    └────────────┘     │
│  ┌────────────┐    ┌────────────┐     │
│  │ PostgreSQL │    │   Redis    │     │
│  │ (Port 5432)│    │(Port 6379) │     │
│  └────────────┘    └────────────┘     │
│  ┌────────────┐    ┌────────────┐     │
│  │  ChromaDB  │    │   Kafka    │     │
│  │ (Port 8000)│    │(Port 9092) │     │
│  └────────────┘    └────────────┘     │
│         + 4 more services               │
└─────────────────────────────────────────┘
```

---

## 🐳 Docker Services Summary

### Core Services (Always Running)
1. **PostgreSQL** - Primary database with TimescaleDB
2. **Redis** - Cache and hot memory tier
3. **ChromaDB** - Vector database for semantic search
4. **AUREN API** - FastAPI backend service
5. **Nginx** - Reverse proxy and static file server

### Streaming Services
6. **Kafka** - Event streaming platform
7. **Zookeeper** - Kafka coordination
8. **Kafka UI** - Monitoring interface

### Monitoring (Optional)
9. **Prometheus** - Metrics collection
10. **Grafana** - Visualization dashboards

### Special Services
11. **Biometric Bridge** - LangGraph integration (new)

---

## 🚀 Quick Start Commands

### SSH Access
```bash
ssh root@144.126.215.218
```

### View All Services
```bash
cd /root/auren-production
docker-compose -f docker-compose.prod.yml ps
```

### Deploy Updates
```bash
./DEPLOY_NOW.sh  # From local machine
```

### View Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f [service-name]
```

### Restart Service
```bash
docker-compose -f docker-compose.prod.yml restart [service-name]
```

---

## 📊 Resource Allocation

### Droplet Specifications
- **Type**: Premium AMD
- **CPU**: 2 vCPUs
- **RAM**: 4 GB
- **Storage**: 80 GB NVMe SSD
- **Network**: 4 TB transfer

### Service Resource Usage
| Service | CPU | Memory | Storage |
|---------|-----|--------|---------|
| PostgreSQL | ~20% | 800MB | 20GB |
| Redis | ~5% | 200MB | 1GB |
| ChromaDB | ~15% | 600MB | 30GB |
| API | ~25% | 400MB | 1GB |
| Nginx | ~5% | 100MB | 1GB |
| Kafka | ~20% | 800MB | 5GB |
| Others | ~10% | 1.1GB | 2GB |

---

## 🔒 Security Measures

### Network Security
- Firewall (UFW) configured
- Only necessary ports exposed
- SSH key authentication only
- Fail2ban for intrusion prevention

### Container Security
- No privileged containers
- Read-only root filesystems where possible
- User namespaces configured
- Secrets management via environment variables

### Data Security
- Encrypted volumes for sensitive data
- Regular security updates
- Database access restricted to Docker network
- API authentication ready (not enforced)

---

## 🔧 Maintenance Schedule

### Daily
- Automated backups (3 AM UTC)
- Log rotation
- Health check monitoring

### Weekly
- Docker image updates check
- Disk space cleanup
- Security patches review

### Monthly
- Full system backup
- Performance review
- Security audit

---

## 📈 Monitoring Access

### Available Endpoints
- **Main Site**: http://aupex.ai
- **API Health**: http://aupex.ai/api/health
- **Kafka UI**: http://aupex.ai:8081
- **Prometheus**: http://aupex.ai:9090 (when enabled)
- **Grafana**: http://aupex.ai:3000 (when enabled)

---

## 🚨 Emergency Procedures

### Service Down
1. Check service status: `docker-compose ps`
2. Check logs: `docker-compose logs [service]`
3. Restart service: `docker-compose restart [service]`
4. Check system resources: `htop`

### Out of Disk Space
1. Check usage: `df -h`
2. Clean Docker: `docker system prune -af`
3. Truncate logs: `truncate -s 0 /var/log/**/*.log`
4. Remove old backups if necessary

### High CPU/Memory
1. Identify process: `htop`
2. Check container stats: `docker stats`
3. Restart problematic service
4. Scale horizontally if needed

---

## 📝 Documentation Standards

All documentation in this folder follows these standards:
1. **Markdown format** for all docs
2. **Version tracking** with last updated dates
3. **Code examples** where applicable
4. **Troubleshooting sections** in each guide
5. **Security considerations** highlighted

---

## 🔗 Related Documentation

### Internal Docs
- [AUREN State of Readiness](../auren/AUREN_STATE_OF_READINESS_REPORT.md)
- [Website Documentation](../AUPEX_WEBSITE_DOCUMENTATION/)
- [LangGraph Pivot](../LANGRAF%20Pivot/)

### External Resources
- [DigitalOcean Documentation](https://docs.digitalocean.com)
- [Docker Documentation](https://docs.docker.com)
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

*Last Updated: January 20, 2025*  
*Maintained by: AUREN Infrastructure Team*  
*Server Status: OPERATIONAL* 