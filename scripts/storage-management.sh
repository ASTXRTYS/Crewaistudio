#!/bin/bash
# AUREN Storage Management Script
# Manages Prometheus data retention and disk usage

set -e

# Configuration
SERVER_IP="144.126.215.218"
SSH_PASS=".HvddX+@6dArsKd"
PROMETHEUS_DATA="/var/lib/prometheus"
DOCKER_DATA="/var/lib/docker"
ALERT_THRESHOLD=80  # Alert when disk usage exceeds 80%

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# SSH helper
run_ssh() {
    sshpass -p "$SSH_PASS" ssh -o StrictHostKeyChecking=no root@$SERVER_IP "$1"
}

# Check disk usage
check_disk_usage() {
    echo -e "${GREEN}📊 Disk Usage Report${NC}"
    echo "====================="
    
    # Overall disk usage
    DISK_USAGE=$(run_ssh "df -h / | awk 'NR==2 {print \$5}' | sed 's/%//'")
    echo "Root partition usage: ${DISK_USAGE}%"
    
    if [ "$DISK_USAGE" -gt "$ALERT_THRESHOLD" ]; then
        echo -e "${RED}⚠️  WARNING: Disk usage exceeds ${ALERT_THRESHOLD}%${NC}"
    fi
    
    # Docker space
    echo -e "\nDocker space usage:"
    run_ssh "docker system df"
    
    # Prometheus data size
    PROM_SIZE=$(run_ssh "du -sh $PROMETHEUS_DATA 2>/dev/null || echo '0'")
    echo -e "\nPrometheus data: $PROM_SIZE"
}

# Clean up old data
cleanup_storage() {
    echo -e "\n${YELLOW}🧹 Running storage cleanup...${NC}"
    
    # 1. Prune Docker resources
    echo "Pruning Docker resources..."
    run_ssh "docker system prune -af --volumes" || true
    
    # 2. Clean old Prometheus data (keep last 7 days)
    echo "Cleaning old Prometheus data..."
    run_ssh "find $PROMETHEUS_DATA -name '*.tmp' -delete 2>/dev/null || true"
    
    # 3. Rotate logs
    echo "Rotating container logs..."
    run_ssh "truncate -s 0 /var/lib/docker/containers/*/*-json.log 2>/dev/null || true"
    
    # 4. Clean package cache
    echo "Cleaning package cache..."
    run_ssh "apt-get clean && rm -rf /var/lib/apt/lists/* 2>/dev/null || true"
    
    echo -e "${GREEN}✓ Cleanup completed${NC}"
}

# Configure Prometheus remote write
configure_remote_write() {
    echo -e "\n${GREEN}🔄 Configuring Prometheus Remote Write${NC}"
    
    # Create updated Prometheus config with remote write
    cat > /tmp/prometheus-remote-write.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    cluster: 'auren-prod'
    region: 'us-east'

# Remote write configuration
remote_write:
  - url: http://localhost:9090/api/v1/write  # Placeholder - replace with actual endpoint
    remote_timeout: 30s
    write_relabel_configs:
      - source_labels: [__name__]
        regex: 'go_.*'
        action: drop  # Drop Go runtime metrics to save space
    queue_config:
      capacity: 10000
      max_shards: 5
      min_shards: 1
      max_samples_per_send: 1000
      batch_send_deadline: 5s
      min_backoff: 30ms
      max_backoff: 100ms

# Alert rules
rule_files:
  - "/opt/prometheus/alerts/*.yml"

# Local storage settings
storage:
  tsdb:
    path: /prometheus
    retention.time: 7d  # Keep local data for 7 days
    retention.size: 10GB  # Max 10GB local storage

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  - job_name: "neuros-advanced-prod"
    metrics_path: /metrics
    static_configs:
      - targets: ["neuros-advanced:8000"]

  - job_name: "biometric-bridge"
    static_configs:
      - targets: ["localhost:8888"]

  - job_name: "otel-collector"
    static_configs:
      - targets: ["otel-collector:9464"]
EOF

    # Copy to server
    sshpass -p "$SSH_PASS" scp -o StrictHostKeyChecking=no /tmp/prometheus-remote-write.yml root@$SERVER_IP:/opt/prometheus-remote-write.yml
    
    echo -e "${GREEN}✓ Remote write configuration created${NC}"
    echo -e "${YELLOW}Note: Update the remote_write URL with your actual endpoint${NC}"
}

# Set up automated cleanup cron job
setup_cron_cleanup() {
    echo -e "\n${GREEN}⏰ Setting up automated cleanup${NC}"
    
    # Create cleanup script on server
    run_ssh "cat > /opt/cleanup-storage.sh << 'EOF'
#!/bin/bash
# Daily storage cleanup
docker image prune -af
docker container prune -f
docker volume prune -f
find /var/lib/docker/containers -name '*-json.log' -size +100M -exec truncate -s 0 {} \;
EOF"
    
    run_ssh "chmod +x /opt/cleanup-storage.sh"
    
    # Add to crontab (daily at 3 AM)
    run_ssh "(crontab -l 2>/dev/null; echo '0 3 * * * /opt/cleanup-storage.sh > /var/log/cleanup.log 2>&1') | crontab -"
    
    echo -e "${GREEN}✓ Daily cleanup cron job configured${NC}"
}

# Main menu
main() {
    echo -e "${GREEN}🗄️  AUREN Storage Management${NC}"
    echo "=============================="
    
    case ${1:-status} in
        status)
            check_disk_usage
            ;;
        cleanup)
            check_disk_usage
            cleanup_storage
            echo -e "\n${GREEN}After cleanup:${NC}"
            check_disk_usage
            ;;
        remote-write)
            configure_remote_write
            ;;
        setup-cron)
            setup_cron_cleanup
            ;;
        all)
            check_disk_usage
            cleanup_storage
            configure_remote_write
            setup_cron_cleanup
            echo -e "\n${GREEN}Final status:${NC}"
            check_disk_usage
            ;;
        *)
            echo "Usage: $0 [status|cleanup|remote-write|setup-cron|all]"
            exit 1
            ;;
    esac
}

main "$@"