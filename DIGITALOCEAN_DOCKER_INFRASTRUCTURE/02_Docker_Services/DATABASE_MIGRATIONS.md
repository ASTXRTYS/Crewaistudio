# DATABASE MIGRATION GUIDE

**Version**: 1.0  
**Last Updated**: January 20, 2025  
**Author**: AUREN Database Team  
**Review Cycle**: Monthly  

---

## 📊 Executive Summary

This guide provides comprehensive procedures for database migrations in AUREN, including schema versioning, migration strategies, rollback procedures, and testing approaches.

**Migration Principles:**
- **Version Control** - Every schema change tracked
- **Reversibility** - All migrations can be rolled back
- **Zero Downtime** - Migrations compatible with running code
- **Testing** - Migrations tested before production

---

## 🗄️ Current Database Schema

### Tables Overview
```sql
-- Core Tables
events                  -- Event sourcing store
agent_memories         -- Agent memory storage
hypotheses            -- Agent hypotheses
learning_progress     -- Learning tracking

-- Biometric Tables
biometric_events      -- Time-series biometric data
neuros_checkpoints    -- LangGraph state persistence
cognitive_mode_transitions -- Mode switching history
biometric_patterns    -- Detected patterns
biometric_alerts      -- Alert history

-- Audit Tables
audit_logs           -- HIPAA compliance logging
phi_access_logs      -- PHI access tracking
```

### TimescaleDB Hypertables
```sql
-- Time-series optimized tables
SELECT * FROM timescaledb_information.hypertables;
```

---

## 🔄 Migration Tool Setup

### 1. Install migrate CLI

```bash
# Download migrate tool
curl -L https://github.com/golang-migrate/migrate/releases/download/v4.17.0/migrate.linux-amd64.tar.gz | tar xvz
sudo mv migrate /usr/local/bin/migrate

# Verify installation
migrate -version
```

### 2. Create Migration Directory

```bash
# Project structure
mkdir -p migrations/{up,down}

# Directory structure
migrations/
├── 001_initial_schema.up.sql
├── 001_initial_schema.down.sql
├── 002_add_biometric_tables.up.sql
├── 002_add_biometric_tables.down.sql
└── README.md
```

### 3. Migration Configuration

```bash
# Create .env.migrations
cat > .env.migrations << EOF
DATABASE_URL=postgresql://auren_user:auren_password_2024@localhost:5432/auren_db?sslmode=disable
MIGRATION_DIR=./migrations
EOF
```

---

## 📝 Creating Migrations

### Migration Naming Convention
```
[sequence]_[description].[direction].sql

Examples:
001_initial_schema.up.sql
001_initial_schema.down.sql
002_add_user_preferences.up.sql
002_add_user_preferences.down.sql
```

### Example Migration Files

#### Up Migration (002_add_user_preferences.up.sql)
```sql
-- Add user preferences table
BEGIN;

CREATE TABLE IF NOT EXISTS user_preferences (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    theme VARCHAR(50) DEFAULT 'dark',
    notifications_enabled BOOLEAN DEFAULT true,
    language VARCHAR(10) DEFAULT 'en',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add index for faster lookups
CREATE INDEX idx_user_preferences_user_id ON user_preferences(user_id);

-- Add trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_preferences_updated_at 
    BEFORE UPDATE ON user_preferences 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add to audit trail
INSERT INTO migration_history (version, description, applied_at)
VALUES (2, 'add_user_preferences', NOW());

COMMIT;
```

#### Down Migration (002_add_user_preferences.down.sql)
```sql
-- Rollback user preferences table
BEGIN;

-- Drop triggers first
DROP TRIGGER IF EXISTS update_user_preferences_updated_at ON user_preferences;
DROP FUNCTION IF EXISTS update_updated_at_column();

-- Drop indexes
DROP INDEX IF EXISTS idx_user_preferences_user_id;

-- Drop table
DROP TABLE IF EXISTS user_preferences;

-- Remove from audit trail
DELETE FROM migration_history WHERE version = 2;

COMMIT;
```

---

## 🧬 Biometric Schema Migrations

### Critical Biometric Migrations

#### 003_biometric_schema.up.sql (TimescaleDB)
```sql
-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Create biometric events hypertable
CREATE TABLE IF NOT EXISTS biometric_events (
    time TIMESTAMPTZ NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DOUBLE PRECISION,
    raw_data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Convert to hypertable
SELECT create_hypertable('biometric_events', 'time', 
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

-- Create indexes for performance
CREATE INDEX idx_biometric_events_user_time ON biometric_events (user_id, time DESC);
CREATE INDEX idx_biometric_events_type_time ON biometric_events (event_type, time DESC);

-- Enable compression after 7 days
ALTER TABLE biometric_events SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'user_id,device_id',
    timescaledb.compress_orderby = 'time DESC'
);

-- Add compression policy
SELECT add_compression_policy('biometric_events', INTERVAL '7 days');

-- Add retention policy (optional - keeps 1 year)
SELECT add_retention_policy('biometric_events', INTERVAL '1 year');
```

#### 004_phi_encryption.up.sql (HIPAA Compliance)
```sql
-- Create encryption functions for PHI data
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Encryption key management (in production, use external key management)
CREATE TABLE IF NOT EXISTS encryption_keys (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(255) UNIQUE NOT NULL,
    encrypted_key TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    rotated_at TIMESTAMPTZ
);

-- PHI encryption functions
CREATE OR REPLACE FUNCTION encrypt_phi(data TEXT, key_id VARCHAR)
RETURNS TEXT AS $$
DECLARE
    encryption_key TEXT;
BEGIN
    -- Get encryption key (simplified - use proper key management in production)
    SELECT encrypted_key INTO encryption_key 
    FROM encryption_keys 
    WHERE encryption_keys.key_id = encrypt_phi.key_id;
    
    -- Encrypt using AES-256
    RETURN encode(
        encrypt(
            data::bytea, 
            encryption_key::bytea, 
            'aes'
        ), 
        'base64'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE FUNCTION decrypt_phi(encrypted_data TEXT, key_id VARCHAR)
RETURNS TEXT AS $$
DECLARE
    encryption_key TEXT;
BEGIN
    -- Get encryption key
    SELECT encrypted_key INTO encryption_key 
    FROM encryption_keys 
    WHERE encryption_keys.key_id = decrypt_phi.key_id;
    
    -- Decrypt using AES-256
    RETURN convert_from(
        decrypt(
            decode(encrypted_data, 'base64')::bytea,
            encryption_key::bytea,
            'aes'
        ),
        'UTF8'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Encrypted biometric storage
CREATE TABLE IF NOT EXISTS encrypted_biometric_data (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    encrypted_data TEXT NOT NULL,
    key_id VARCHAR(255) NOT NULL,
    data_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (key_id) REFERENCES encryption_keys(key_id)
);

-- PHI access audit log
CREATE TABLE IF NOT EXISTS phi_access_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    accessor_id VARCHAR(255) NOT NULL,
    access_type VARCHAR(50) NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    record_id INTEGER,
    access_time TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT
);
```

#### 005_biometric_bridge_state.up.sql (LangGraph State)
```sql
-- NEUROS checkpoint storage
CREATE TABLE IF NOT EXISTS neuros_checkpoints (
    thread_id VARCHAR(255) NOT NULL,
    checkpoint_id VARCHAR(255) NOT NULL,
    parent_id VARCHAR(255),
    state JSONB NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (thread_id, checkpoint_id)
);

-- Cognitive mode transitions
CREATE TABLE IF NOT EXISTS cognitive_mode_transitions (
    id SERIAL PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL,
    from_mode VARCHAR(50),
    to_mode VARCHAR(50) NOT NULL,
    trigger_event JSONB,
    transition_time TIMESTAMPTZ DEFAULT NOW(),
    decision_factors JSONB
);

-- Biometric pattern detection results
CREATE TABLE IF NOT EXISTS biometric_patterns (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    pattern_type VARCHAR(100) NOT NULL,
    confidence FLOAT NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    detection_time TIMESTAMPTZ DEFAULT NOW(),
    pattern_data JSONB,
    action_taken JSONB
);

-- Create indexes for performance
CREATE INDEX idx_neuros_checkpoints_thread ON neuros_checkpoints(thread_id);
CREATE INDEX idx_cognitive_transitions_thread ON cognitive_mode_transitions(thread_id);
CREATE INDEX idx_biometric_patterns_user ON biometric_patterns(user_id, detection_time DESC);
```

### Migration Testing Checklist

#### Pre-Production Testing
```bash
# 1. Test on staging database
docker-compose -f docker-compose.staging.yml up -d postgres
migrate -database $STAGING_DB_URL -path ./migrations up

# 2. Verify TimescaleDB functions
psql $STAGING_DB_URL -c "SELECT * FROM timescaledb_information.hypertables;"

# 3. Test encryption functions
psql $STAGING_DB_URL -c "SELECT encrypt_phi('test_data', 'default_key');"

# 4. Performance testing
pgbench -c 10 -j 2 -t 1000 $STAGING_DB_URL
```

#### Rollback Procedures
```sql
-- Emergency rollback for biometric schema
BEGIN;

-- Disable compression policies first
SELECT remove_compression_policy('biometric_events');
SELECT remove_retention_policy('biometric_events');

-- Drop hypertable
DROP TABLE IF EXISTS biometric_events CASCADE;

-- Drop encryption functions
DROP FUNCTION IF EXISTS encrypt_phi CASCADE;
DROP FUNCTION IF EXISTS decrypt_phi CASCADE;

-- Drop tables
DROP TABLE IF EXISTS encrypted_biometric_data;
DROP TABLE IF EXISTS phi_access_log;
DROP TABLE IF EXISTS neuros_checkpoints;
DROP TABLE IF EXISTS cognitive_mode_transitions;
DROP TABLE IF EXISTS biometric_patterns;

ROLLBACK; -- Change to COMMIT when ready
```

---

## 🚀 Running Migrations

### Local Development

```bash
# Check current version
migrate -database $DATABASE_URL -path ./migrations version

# Apply all migrations
migrate -database $DATABASE_URL -path ./migrations up

# Apply specific number of migrations
migrate -database $DATABASE_URL -path ./migrations up 2

# Rollback last migration
migrate -database $DATABASE_URL -path ./migrations down 1

# Force specific version (use with caution)
migrate -database $DATABASE_URL -path ./migrations force 3
```

### Production Deployment

```bash
#!/bin/bash
# deploy_migrations.sh

set -e

echo "🗄️  Starting database migration..."

# Load environment
source .env.migrations

# Backup database first
echo "📦 Creating backup..."
docker exec auren-postgres pg_dump -U auren_user auren_db | gzip > backup-$(date +%Y%m%d-%H%M%S).sql.gz

# Check current version
CURRENT_VERSION=$(migrate -database $DATABASE_URL -path ./migrations version)
echo "Current version: $CURRENT_VERSION"

# Test migrations in transaction
echo "🧪 Testing migrations..."
docker exec -i auren-postgres psql -U auren_user -d auren_db << EOF
BEGIN;
\i migrations/next_migration.up.sql
ROLLBACK;
EOF

if [ $? -eq 0 ]; then
    echo "✅ Migration test passed"
    
    # Apply migrations
    echo "🚀 Applying migrations..."
    migrate -database $DATABASE_URL -path ./migrations up
    
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migration test failed. Aborting."
    exit 1
fi
```

---

## 🔄 Zero-Downtime Migrations

### Strategy 1: Expand and Contract

```sql
-- Phase 1: Expand (add new column)
ALTER TABLE users ADD COLUMN email_new VARCHAR(255);

-- Phase 2: Migrate data (in application)
UPDATE users SET email_new = email WHERE email_new IS NULL;

-- Phase 3: Contract (after deployment)
ALTER TABLE users DROP COLUMN email;
ALTER TABLE users RENAME COLUMN email_new TO email;
```

### Strategy 2: Blue-Green Schema

```sql
-- Create new table with changes
CREATE TABLE users_v2 (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    -- new schema
);

-- Copy data
INSERT INTO users_v2 SELECT * FROM users;

-- Switch in application
-- Then clean up old table
DROP TABLE users;
ALTER TABLE users_v2 RENAME TO users;
```

### Strategy 3: Feature Flags

```python
# In application code
if feature_flags.get('use_new_schema'):
    query = "SELECT * FROM users_v2"
else:
    query = "SELECT * FROM users"
```

---

## 🧪 Migration Testing

### Test Database Setup

```bash
# Create test database
docker exec auren-postgres createdb -U auren_user auren_test

# Run migrations on test db
DATABASE_URL="postgresql://auren_user:password@localhost:5432/auren_test" \
migrate -path ./migrations up
```

### Automated Testing

```python
# test_migrations.py
import psycopg2
import subprocess
import pytest

class TestMigrations:
    def setup_method(self):
        # Create test database
        self.conn = psycopg2.connect(
            dbname="postgres",
            user="auren_user",
            password="password"
        )
        self.conn.autocommit = True
        cursor = self.conn.cursor()
        cursor.execute("CREATE DATABASE migration_test")
        
    def teardown_method(self):
        # Drop test database
        cursor = self.conn.cursor()
        cursor.execute("DROP DATABASE IF EXISTS migration_test")
        self.conn.close()
    
    def test_migrations_up_down(self):
        # Test all migrations up
        result = subprocess.run([
            "migrate", "-database", 
            "postgresql://user:pass@localhost/migration_test",
            "-path", "./migrations", "up"
        ])
        assert result.returncode == 0
        
        # Test all migrations down
        result = subprocess.run([
            "migrate", "-database",
            "postgresql://user:pass@localhost/migration_test", 
            "-path", "./migrations", "down"
        ])
        assert result.returncode == 0
```

---

## 🔙 Rollback Procedures

### Immediate Rollback

```bash
#!/bin/bash
# rollback_migration.sh

echo "⚠️  Rolling back last migration..."

# Check current version
CURRENT=$(migrate -database $DATABASE_URL -path ./migrations version)
echo "Current version: $CURRENT"

# Rollback one version
migrate -database $DATABASE_URL -path ./migrations down 1

# Verify
NEW_VERSION=$(migrate -database $DATABASE_URL -path ./migrations version)
echo "Rolled back to version: $NEW_VERSION"

# Restart services
docker-compose -f docker-compose.prod.yml restart auren-api
```

### Emergency Rollback

```bash
# If migrations corrupted, restore from backup
echo "🚨 Emergency rollback from backup..."

# Stop services
docker-compose -f docker-compose.prod.yml stop auren-api

# Restore backup
gunzip -c backup-20250120-143000.sql.gz | docker exec -i auren-postgres psql -U auren_user auren_db

# Restart services
docker-compose -f docker-compose.prod.yml start auren-api
```

---

## 📊 Migration History Tracking

### Create History Table

```sql
-- migrations/000_migration_history.up.sql
CREATE TABLE IF NOT EXISTS migration_history (
    id SERIAL PRIMARY KEY,
    version INTEGER NOT NULL,
    description VARCHAR(255),
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    applied_by VARCHAR(100) DEFAULT CURRENT_USER,
    execution_time_ms INTEGER,
    success BOOLEAN DEFAULT true,
    error_message TEXT
);

CREATE INDEX idx_migration_history_version ON migration_history(version);
```

### Track Migrations

```sql
-- In each migration
BEGIN;

-- Record start
INSERT INTO migration_history (version, description)
VALUES (3, 'add_indexes_for_performance');

-- Do migration work
CREATE INDEX CONCURRENTLY idx_events_created_at ON events(created_at);

-- Update completion
UPDATE migration_history 
SET execution_time_ms = EXTRACT(EPOCH FROM (NOW() - applied_at)) * 1000
WHERE version = 3;

COMMIT;
```

---

## 🔒 Production Safety Rules

### Pre-Migration Checklist

- [ ] Backup created and verified
- [ ] Migration tested on staging
- [ ] Rollback script prepared
- [ ] Team notified
- [ ] Low traffic period selected
- [ ] Monitoring alerts configured

### Migration Rules

1. **Always use transactions** when possible
2. **Never drop columns** immediately (use expand/contract)
3. **Create indexes CONCURRENTLY** to avoid locks
4. **Test rollbacks** before applying
5. **Monitor performance** during migration

### Dangerous Operations

```sql
-- ❌ Avoid these in production
ALTER TABLE large_table ADD COLUMN with_default VARCHAR(50) DEFAULT 'value';
DROP TABLE IF EXISTS important_data;
ALTER TABLE busy_table ALTER COLUMN type TYPE new_type;

-- ✅ Safer alternatives
ALTER TABLE large_table ADD COLUMN new_col VARCHAR(50);
-- Then update in batches

CREATE TABLE important_data_archive AS SELECT * FROM important_data;
-- Then drop after verification

-- Use blue-green for type changes
```

---

## 📈 Performance Considerations

### Large Table Migrations

```sql
-- Batch updates for large tables
DO $$
DECLARE
    batch_size INTEGER := 1000;
    offset_val INTEGER := 0;
    total_updated INTEGER := 0;
BEGIN
    LOOP
        UPDATE users 
        SET new_column = calculated_value()
        WHERE id IN (
            SELECT id FROM users 
            WHERE new_column IS NULL 
            LIMIT batch_size
        );
        
        GET DIAGNOSTICS total_updated = ROW_COUNT;
        EXIT WHEN total_updated = 0;
        
        -- Prevent lock accumulation
        PERFORM pg_sleep(0.1);
    END LOOP;
END $$;
```

### Index Creation

```sql
-- Create indexes without blocking
CREATE INDEX CONCURRENTLY idx_events_user_id ON events(user_id);

-- Monitor progress
SELECT * FROM pg_stat_progress_create_index;
```

---

## 🛠️ Troubleshooting

### Common Issues

#### Migration Stuck
```bash
# Check for locks
docker exec auren-postgres psql -U auren_user -d auren_db -c "
SELECT pid, usename, query, state 
FROM pg_stat_activity 
WHERE state != 'idle' 
ORDER BY query_start;"

# Kill blocking query
docker exec auren-postgres psql -U auren_user -d auren_db -c "
SELECT pg_cancel_backend(PID);"
```

#### Dirty Database State
```bash
# Force to specific version
migrate -database $DATABASE_URL -path ./migrations force 5

# Clean and retry
migrate -database $DATABASE_URL -path ./migrations down
migrate -database $DATABASE_URL -path ./migrations up
```

#### Connection Issues
```bash
# Test connection
docker exec auren-postgres pg_isready

# Check from container
docker exec auren-api psql $DATABASE_URL -c "SELECT 1"
```

---

## 📋 Migration Templates

### Add Column Template
```sql
-- up
ALTER TABLE table_name 
ADD COLUMN IF NOT EXISTS column_name VARCHAR(255);

-- down  
ALTER TABLE table_name 
DROP COLUMN IF EXISTS column_name;
```

### Add Index Template
```sql
-- up
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_table_column 
ON table_name(column_name);

-- down
DROP INDEX CONCURRENTLY IF EXISTS idx_table_column;
```

### Add Constraint Template
```sql
-- up
ALTER TABLE table_name
ADD CONSTRAINT constraint_name 
CHECK (column_name IS NOT NULL);

-- down
ALTER TABLE table_name
DROP CONSTRAINT IF EXISTS constraint_name;
```

---

## 🚀 CI/CD Integration

### GitHub Actions
```yaml
name: Database Migrations

on:
  push:
    paths:
      - 'migrations/**'

jobs:
  test-migrations:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: timescale/timescaledb:latest-pg16
        env:
          POSTGRES_PASSWORD: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Install migrate
        run: |
          curl -L https://github.com/golang-migrate/migrate/releases/download/v4.17.0/migrate.linux-amd64.tar.gz | tar xvz
          sudo mv migrate /usr/local/bin/
      
      - name: Run migrations up
        run: migrate -database postgresql://postgres:test@localhost:5432/postgres?sslmode=disable -path ./migrations up
      
      - name: Run migrations down
        run: migrate -database postgresql://postgres:test@localhost:5432/postgres?sslmode=disable -path ./migrations down
```

---

*Database migrations are critical operations. Always backup, test thoroughly, and have a rollback plan.* 