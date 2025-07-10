#!/bin/bash

echo "🚀 AUREN Production Readiness Check"

# 1. Type checking
echo "Running type checks..."
if command -v mypy &> /dev/null; then
    mypy src/ --ignore-missing-imports
else
    echo "⚠️  mypy not installed, skipping type checks"
fi

# 2. Unit tests
echo "Running tests..."
if [ -d "tests" ]; then
    pytest tests/ -v
else
    echo "⚠️  No tests directory found"
fi

# 3. Security scan
echo "Security scanning..."
if command -v bandit &> /dev/null; then
    bandit -r src/
else
    echo "⚠️  bandit not installed, skipping security scan"
fi

# 4. Environment validation
echo "Validating environment..."
if [ -f "start_auren.py" ]; then
    python start_auren.py --validate-only
else
    echo "⚠️  start_auren.py not found"
fi

# 5. Docker build test
echo "Testing Docker build..."
if [ -f "../Dockerfile" ]; then
    docker build -t auren:test ..
else
    echo "⚠️  Dockerfile not found"
fi

# 6. Import validation
echo "Validating imports..."
python -c "
import sys
sys.path.append('src')

try:
    from protocols.mirage.mirage_protocol import MIRAGEProtocol
    from biometric.analyzers.facial_analyzer import BiometricAnalyzer
    from integrations.biometric_whatsapp import BiometricWhatsAppConnector
    from agents.crew_compatibility import AurenAgent
    print('✅ All core modules import successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

echo "✅ Production check complete" 