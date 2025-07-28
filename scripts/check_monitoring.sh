#!/bin/bash
# AUREN Monitoring Stack Health Check Script
# Created: January 28, 2025
# Purpose: Automated monitoring of the monitoring infrastructure

# Configuration
LOG_FILE="/var/log/auren_monitoring.log"
PROMETHEUS_URL="http://localhost:9090"
GRAFANA_URL="http://localhost:3000"
METRICS_URL="http://localhost:8888/metrics"

# Services to monitor
SERVICES="auren-prometheus auren-grafana biometric-production"

# Create log file if it doesn't exist
touch $LOG_FILE

echo "$(date) - Starting monitoring health check" >> $LOG_FILE

# Function to check if container is running
check_container() {
    local service=$1
    if ! docker ps | grep -q $service; then
        echo "$(date) - ERROR: $service is down, attempting restart" >> $LOG_FILE
        docker start $service
        
        # Wait for startup
        sleep 5
        
        # Check if restart was successful
        if docker ps | grep -q $service; then
            echo "$(date) - SUCCESS: $service restarted successfully" >> $LOG_FILE
        else
            echo "$(date) - CRITICAL: $service failed to restart" >> $LOG_FILE
            # TODO: Send alert webhook here
        fi
        return 1
    fi
    return 0
}

# Check all critical services
ALL_HEALTHY=true
for service in $SERVICES; do
    if ! check_container $service; then
        ALL_HEALTHY=false
    fi
done

# Check if metrics endpoint is accessible
if ! curl -s $METRICS_URL > /dev/null; then
    echo "$(date) - ERROR: Metrics endpoint not responding" >> $LOG_FILE
    echo "$(date) - Attempting to restart biometric-production" >> $LOG_FILE
    docker restart biometric-production
    ALL_HEALTHY=false
else
    # Check if metrics contain expected content
    METRICS_COUNT=$(curl -s $METRICS_URL | wc -l)
    if [ $METRICS_COUNT -lt 10 ]; then
        echo "$(date) - WARNING: Metrics endpoint returning insufficient data (lines: $METRICS_COUNT)" >> $LOG_FILE
        ALL_HEALTHY=false
    fi
fi

# Check Prometheus targets
if docker ps | grep -q auren-prometheus; then
    DOWN_TARGETS=$(curl -s $PROMETHEUS_URL/api/v1/targets 2>/dev/null | jq '.data.activeTargets[] | select(.health=="down") | .labels.job' | wc -l)
    if [ $DOWN_TARGETS -gt 0 ]; then
        echo "$(date) - WARNING: $DOWN_TARGETS Prometheus targets are down" >> $LOG_FILE
        # Log which targets are down
        curl -s $PROMETHEUS_URL/api/v1/targets 2>/dev/null | jq '.data.activeTargets[] | select(.health=="down") | .labels.job' >> $LOG_FILE
        ALL_HEALTHY=false
    fi
fi

# Check Grafana health
if docker ps | grep -q auren-grafana; then
    if ! curl -s $GRAFANA_URL/api/health > /dev/null; then
        echo "$(date) - WARNING: Grafana API not responding" >> $LOG_FILE
        ALL_HEALTHY=false
    fi
fi

# Log overall status
if $ALL_HEALTHY; then
    echo "$(date) - All monitoring services healthy" >> $LOG_FILE
else
    echo "$(date) - Monitoring stack has issues, check log for details" >> $LOG_FILE
fi

# Rotate log if it gets too large (>10MB)
LOG_SIZE=$(stat -f%z "$LOG_FILE" 2>/dev/null || stat -c%s "$LOG_FILE" 2>/dev/null)
if [ $LOG_SIZE -gt 10485760 ]; then
    mv $LOG_FILE "$LOG_FILE.old"
    touch $LOG_FILE
    echo "$(date) - Log rotated (size was $LOG_SIZE bytes)" >> $LOG_FILE
fi

exit 0 