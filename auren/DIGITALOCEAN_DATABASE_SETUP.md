# AUREN DigitalOcean PostgreSQL Setup Guide

## Overview

This guide shows how to configure AUREN to use PostgreSQL hosted on DigitalOcean instead of running locally.

## Prerequisites

1. DigitalOcean account
2. AUREN project cloned locally
3. Basic knowledge of environment variables

## Step 1: Create DigitalOcean Database Cluster

### 1.1 Access DigitalOcean Dashboard
- Go to [DigitalOcean Dashboard](https://cloud.digitalocean.com/)
- Navigate to **Databases** in the left sidebar

### 1.2 Create PostgreSQL Cluster
- Click **Create Database Cluster**
- Choose **PostgreSQL** as the database engine
- Select your preferred region (choose closest to your users)
- Choose a plan based on your needs:
  - **Basic**: Good for development/testing
  - **Professional**: Recommended for production
  - **Enterprise**: For high-traffic applications

### 1.3 Configure Database
- **Database Name**: `auren_db` (or your preferred name)
- **Database User**: `auren_user` (or your preferred username)
- **Password**: Generate a strong password
- **Trusted Sources**: Add your IP address or `0.0.0.0/0` for development

### 1.4 Note Connection Details
After creation, note down:
- **Host**: `your-cluster-name.db.ondigitalocean.com`
- **Port**: Usually `25060` (SSL) or `25061` (non-SSL)
- **Database**: `auren_db`
- **Username**: `auren_user`
- **Password**: Your chosen password

## Step 2: Configure AUREN Environment

### 2.1 Create Environment File
Create a `.env` file in your AUREN project root:

```bash
# Copy the example file
cp auren/.env.example .env
```

### 2.2 Update Database Configuration

#### Option A: Single DATABASE_URL (Recommended)
```bash
# In your .env file
DATABASE_URL=postgresql://auren_user:your_password@your-cluster-name.db.ondigitalocean.com:25060/auren_db?sslmode=require
```

#### Option B: Individual Components
```bash
# In your .env file
DB_HOST=your-cluster-name.db.ondigitalocean.com
DB_PORT=25060
DB_NAME=auren_db
DB_USER=auren_user
DB_PASSWORD=your_password
DB_SSL_MODE=require
```

### 2.3 Complete Environment Configuration
```bash
# Required for DigitalOcean PostgreSQL
DATABASE_URL=postgresql://auren_user:your_password@your-cluster-name.db.ondigitalocean.com:25060/auren_db?sslmode=require

# Other AUREN settings
REDIS_URL=redis://localhost:6379/0
CHROMADB_HOST=localhost
CHROMADB_PORT=8000
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Performance settings for remote database
POSTGRES_MAX_CONNECTIONS=50
```

## Step 3: Test Database Connection

### 3.1 Run Database Setup Script
```bash
cd auren
python setup_cognitive_twin.py
```

### 3.2 Test Connection Manually
```python
import asyncio
import asyncpg

async def test_connection():
    try:
        conn = await asyncpg.connect(
            "postgresql://auren_user:your_password@your-cluster-name.db.ondigitalocean.com:25060/auren_db?sslmode=require"
        )
        print("✅ Database connection successful!")
        await conn.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")

asyncio.run(test_connection())
```

## Step 4: Update Docker Configuration (Optional)

If you're using Docker, update the docker-compose file to use the remote database:

```yaml
# In auren/docker/docker-compose.yml
services:
  # Remove or comment out the local postgres service
  # postgres:
  #   image: timescale/timescaledb:latest-pg16
  #   ...

  auren-api:
    environment:
      - DATABASE_URL=postgresql://auren_user:your_password@your-cluster-name.db.ondigitalocean.com:25060/auren_db?sslmode=require
```

## Step 5: Security Considerations

### 5.1 Network Security
- Use SSL connections (`sslmode=require`)
- Restrict database access to specific IP addresses
- Use strong passwords
- Consider using connection pooling for production

### 5.2 Environment Security
- Never commit `.env` files to version control
- Use secrets management in production
- Rotate database passwords regularly

## Step 6: Performance Optimization

### 6.1 Connection Pooling
```python
# In your application code
import asyncpg

pool = await asyncpg.create_pool(
    DATABASE_URL,
    min_size=5,
    max_size=20,
    command_timeout=30
)
```

### 6.2 Monitoring
- Monitor database performance in DigitalOcean dashboard
- Set up alerts for high CPU/memory usage
- Track connection count and query performance

## Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Check firewall settings
   - Verify IP address is in trusted sources
   - Ensure SSL mode is correct

2. **Authentication Failed**
   - Verify username/password
   - Check database name
   - Ensure user has proper permissions

3. **SSL Issues**
   - Use `sslmode=require` for DigitalOcean
   - Check certificate validity
   - Verify port number (25060 for SSL)

### Debug Commands
```bash
# Test network connectivity
telnet your-cluster-name.db.ondigitalocean.com 25060

# Test with psql (if installed)
psql "postgresql://auren_user:password@host:25060/auren_db?sslmode=require"

# Check environment variables
echo $DATABASE_URL
```

## Benefits of DigitalOcean PostgreSQL

1. **Managed Service**: No server maintenance required
2. **Automatic Backups**: Built-in backup and recovery
3. **High Availability**: Automatic failover
4. **Scalability**: Easy to upgrade resources
5. **Security**: Built-in encryption and access controls
6. **Monitoring**: Built-in performance monitoring

## Cost Considerations

- **Basic Plan**: ~$15/month (1GB RAM, 1 vCPU)
- **Professional Plan**: ~$25/month (2GB RAM, 1 vCPU)
- **Enterprise Plan**: ~$50/month (4GB RAM, 2 vCPU)

Choose based on your expected data volume and performance requirements.

## Next Steps

1. Set up automated backups
2. Configure monitoring alerts
3. Implement connection pooling
4. Set up read replicas if needed
5. Plan for disaster recovery

## Support

- [DigitalOcean Database Documentation](https://docs.digitalocean.com/products/databases/)
- [AUREN Database Configuration](auren/src/core/config.py)
- [PostgreSQL SSL Configuration](https://www.postgresql.org/docs/current/ssl-tcp.html) 