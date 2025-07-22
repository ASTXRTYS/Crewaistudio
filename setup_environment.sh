#!/bin/bash
# AUREN Environment Setup Script

echo "Setting up AUREN development environment..."

# Check Python version
python_version=$(python3 --version | cut -d' ' -f2)
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.10+ is required. Found: $python_version"
    exit 1
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Copy environment template if .env doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cat > .env << 'EOF'
# OpenAI Configuration
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL_NAME=gpt-4

# Database Settings
DB_HOST=localhost
DB_PORT=5432
DB_USER=auren_user
DB_PASSWORD=auren_secure_password
DB_NAME=auren_db

# Redis Settings
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://localhost:6379

# Kafka Settings
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_SECURITY_PROTOCOL=PLAINTEXT

# Application Settings
LOG_LEVEL=INFO
ENVIRONMENT=development
TOKEN_TRACKING_ENABLED=true
DAILY_BUDGET_LIMIT=10.0
EOF
    echo "Please update .env with your actual API keys and credentials"
fi

echo "Environment setup complete. Activate with: source venv/bin/activate" 