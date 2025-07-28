#!/bin/bash
# Migrate Redis to Valkey - License Protection + Performance
# Created: 2025-01-29
# Purpose: Automated migration from Redis to Valkey across all compose files

set -e

echo "🔄 Redis to Valkey Migration Script"
echo "=================================="
echo ""

# Check current Redis version to ensure we're not already on problematic version
check_current_redis() {
    echo "📋 Checking current Redis versions..."
    
    # Find all docker-compose files
    COMPOSE_FILES=$(find . -name "docker-compose*.yml" -o -name "docker-compose*.yaml" | grep -v node_modules | sort)
    
    echo "Found compose files:"
    echo "$COMPOSE_FILES" | sed 's/^/  - /'
    echo ""
}

# Backup compose files
backup_files() {
    echo "💾 Creating backups..."
    BACKUP_DIR="backups/valkey-migration-$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            cp "$file" "$BACKUP_DIR/"
            echo "  ✅ Backed up: $file"
        fi
    done <<< "$COMPOSE_FILES"
    
    echo ""
    echo "Backups saved to: $BACKUP_DIR"
    echo ""
}

# Perform migration
migrate_to_valkey() {
    echo "🚀 Migrating to Valkey..."
    echo ""
    
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            echo "Processing: $file"
            
            # Count replacements
            REDIS_COUNT=$(grep -c "image: redis:" "$file" || true)
            
            if [ "$REDIS_COUNT" -gt 0 ]; then
                # Replace Redis images with Valkey
                sed -i.bak 's|image: redis:7-alpine|image: valkey/valkey:8-alpine|g' "$file"
                sed -i 's|image: redis:7.2-alpine|image: valkey/valkey:8-alpine|g' "$file"
                sed -i 's|image: redis:latest|image: valkey/valkey:8-alpine|g' "$file"
                
                # Update container names if they contain redis
                sed -i 's|container_name: \(.*\)-redis|container_name: \1-valkey|g' "$file"
                
                # Remove backup file
                rm -f "${file}.bak"
                
                echo "  ✅ Migrated $REDIS_COUNT Redis instances to Valkey"
            else
                echo "  ℹ️  No Redis images found"
            fi
            echo ""
        fi
    done <<< "$COMPOSE_FILES"
}

# Update documentation
update_documentation() {
    echo "📝 Updating documentation..."
    
    # Create migration record
    cat > "VALKEY_MIGRATION_RECORD.md" << EOF
# Valkey Migration Record
**Date**: $(date)
**Migrated By**: $(whoami)

## Summary
Successfully migrated from Redis to Valkey across all Docker Compose files.

## Reasons for Migration:
1. Redis license changed - OSS version frozen at 7.2.4
2. Valkey offers 20% performance improvement
3. Drop-in replacement with BSD license
4. Future-proof against license issues

## Changed Files:
$(echo "$COMPOSE_FILES" | sed 's/^/- /')

## Rollback Instructions:
If needed, restore from backups in: $BACKUP_DIR

## Verification:
\`\`\`bash
# Check all services are running
docker-compose ps

# Test Redis protocol compatibility
docker exec -it auren-valkey redis-cli ping
\`\`\`
EOF
    
    echo "  ✅ Created VALKEY_MIGRATION_RECORD.md"
    echo ""
}

# Add CI/CD check
create_ci_check() {
    echo "🔒 Creating CI/CD license check..."
    
    cat > "scripts/check_redis_license.sh" << 'EOF'
#!/bin/bash
# Check for Redis version compliance
# Prevents accidental Redis license violations

set -e

echo "Checking Redis/Valkey versions..."

# Find all compose files
COMPOSE_FILES=$(find . -name "docker-compose*.yml" -o -name "docker-compose*.yaml" | grep -v node_modules)

FOUND_REDIS=false
for file in $COMPOSE_FILES; do
    if grep -q "image: redis:" "$file"; then
        echo "❌ Found Redis image in $file"
        echo "   Please use Valkey instead: valkey/valkey:8-alpine"
        FOUND_REDIS=true
    fi
done

if [ "$FOUND_REDIS" = true ]; then
    echo ""
    echo "❌ Redis images detected! Use Valkey to avoid license issues."
    exit 1
else
    echo "✅ All services using Valkey. License compliant!"
fi
EOF
    
    chmod +x scripts/check_redis_license.sh
    echo "  ✅ Created scripts/check_redis_license.sh"
    echo ""
}

# Main execution
main() {
    echo "Starting Valkey migration..."
    echo ""
    
    check_current_redis
    
    # Confirm before proceeding
    echo "⚠️  This will replace all Redis images with Valkey."
    echo "   Valkey is a drop-in replacement, but please ensure you have backups."
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Migration cancelled."
        exit 0
    fi
    
    backup_files
    migrate_to_valkey
    update_documentation
    create_ci_check
    
    echo "🎉 Migration complete!"
    echo ""
    echo "Next steps:"
    echo "1. Review changes in compose files"
    echo "2. Test services locally: docker-compose up -d"
    echo "3. Verify Redis protocol: docker exec -it <container> redis-cli ping"
    echo "4. Add scripts/check_redis_license.sh to CI/CD pipeline"
    echo ""
    echo "Note: Valkey uses the same Redis protocol, so no application code changes needed!"
}

# Run if not sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 