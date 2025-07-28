#!/bin/bash
# AUREN Docker Cleanup Script
# Purpose: Clean redundant Docker images and containers
# Date: July 28, 2025

set -e

echo "==================================="
echo "AUREN DOCKER CLEANUP SCRIPT"
echo "==================================="
echo "This script will clean up redundant Docker resources"
echo "Press Ctrl+C to cancel, or Enter to continue..."
read

# Function to check disk usage
check_disk() {
    echo -e "\n📊 Current disk usage:"
    df -h / | grep -E "Filesystem|/dev"
}

# Function to count resources
count_resources() {
    echo -e "\n📈 Current resource count:"
    echo "Docker images (biometric/auren): $(docker images | grep -E "(biometric|auren)" | wc -l)"
    echo "Stopped containers: $(docker ps -a --filter "status=exited" | grep -E "(biometric|auren)" | wc -l || echo 0)"
    echo "All containers: $(docker ps -a | grep -E "(biometric|auren)" | wc -l)"
}

# Initial status
echo -e "\n🔍 INITIAL STATUS"
check_disk
count_resources

# Phase 1: Stop non-essential containers
echo -e "\n\n🛑 PHASE 1: Stopping non-essential containers..."
CONTAINERS_TO_STOP=$(docker ps -a | grep -E "biometric|auren" | grep -v "postgres\|redis\|kafka\|grafana\|prometheus\|biometric-production" | awk '{print $1}' || echo "")
if [ ! -z "$CONTAINERS_TO_STOP" ]; then
    echo "Stopping: $CONTAINERS_TO_STOP"
    docker stop $CONTAINERS_TO_STOP 2>/dev/null || true
else
    echo "No containers to stop"
fi

# Phase 2: Remove stopped containers
echo -e "\n\n🗑️ PHASE 2: Removing stopped containers..."
CONTAINERS_TO_REMOVE=$(docker ps -a -f status=exited | grep -E "biometric|auren" | awk '{print $1}' || echo "")
if [ ! -z "$CONTAINERS_TO_REMOVE" ]; then
    echo "Removing: $CONTAINERS_TO_REMOVE"
    docker rm $CONTAINERS_TO_REMOVE 2>/dev/null || true
else
    echo "No containers to remove"
fi

# Phase 3: List images for review
echo -e "\n\n🖼️ PHASE 3: Docker images review..."
echo "Current images:"
docker images | grep -E "(biometric|auren)" | awk '{printf "%-50s %-15s %s\n", $1":"$2, $3, $7$8}'

# Phase 4: Remove old images (keeping latest)
echo -e "\n\n🧹 PHASE 4: Removing old images..."
echo "Keeping only 'latest' tags and currently used images..."

# Get images in use
IMAGES_IN_USE=$(docker ps -a --format "{{.Image}}" | sort -u)

# Remove old tagged versions
OLD_IMAGES=$(docker images | grep -E "(biometric-backup|section-12)" | grep -v "latest" | awk '{print $3}' | sort -u || echo "")
if [ ! -z "$OLD_IMAGES" ]; then
    for img in $OLD_IMAGES; do
        if ! echo "$IMAGES_IN_USE" | grep -q "$img"; then
            echo "Removing image: $img"
            docker rmi $img 2>/dev/null || echo "Could not remove $img (may be in use)"
        fi
    done
else
    echo "No old images to remove"
fi

# Phase 5: Docker system cleanup
echo -e "\n\n🔧 PHASE 5: System cleanup..."

echo "Cleaning build cache..."
docker builder prune -f

echo "Cleaning dangling images..."
docker image prune -f

echo "Cleaning unused volumes..."
docker volume prune -f

# Phase 6: Archive old backups
echo -e "\n\n📦 PHASE 6: Backup directory cleanup..."
if [ -d "/opt/auren_deploy_backup_*" ]; then
    echo "Found backup directories. Options:"
    echo "1) Archive to /opt/archive"
    echo "2) Delete permanently"
    echo "3) Skip"
    read -p "Choose (1/2/3): " choice
    
    case $choice in
        1)
            mkdir -p /opt/archive
            mv /opt/auren_deploy_backup_* /opt/archive/ 2>/dev/null || echo "No backups to move"
            echo "Backups archived to /opt/archive"
            ;;
        2)
            rm -rf /opt/auren_deploy_backup_* 2>/dev/null || echo "No backups to delete"
            echo "Backups deleted"
            ;;
        3)
            echo "Skipping backup cleanup"
            ;;
    esac
else
    echo "No backup directories found"
fi

# Final status
echo -e "\n\n✅ CLEANUP COMPLETE"
check_disk
count_resources

echo -e "\n\n📋 NEXT STEPS:"
echo "1. Review remaining images and containers"
echo "2. Run 'docker system df' to see detailed space usage"
echo "3. If disk still > 90%, consider 'docker system prune -a' (CAREFUL!)"
echo "4. Update docker-compose.prod.yml with final configuration"

echo -e "\n🚀 To start clean AUREN deployment:"
echo "docker run -d \\"
echo "  --name biometric-production \\"
echo "  --network auren-network \\"
echo "  -p 8888:8888 \\"
echo "  -e POSTGRES_HOST=auren-postgres \\"
echo "  -e POSTGRES_USER=auren_user \\"
echo "  -e POSTGRES_PASSWORD=auren_password_2024 \\"
echo "  -e POSTGRES_DB=auren_production \\"
echo "  -e REDIS_HOST=auren-redis \\"
echo "  -e KAFKA_BOOTSTRAP_SERVERS=auren-kafka:9092 \\"
echo "  -e OPENAI_API_KEY='<your-key>' \\"
echo "  auren_deploy_biometric-bridge:latest" 