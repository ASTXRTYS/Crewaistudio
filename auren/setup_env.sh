#!/bin/bash
# AUREN Environment Setup Script
# Sets up PYTHONPATH and validates environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Export PYTHONPATH to include the auren directory
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

echo "🚀 AUREN Environment Setup"
echo "========================="
echo "PYTHONPATH set to: ${PYTHONPATH}"

# Check if .env file exists
if [ ! -f "${SCRIPT_DIR}/.env" ]; then
    echo ""
    echo "⚠️  Warning: .env file not found!"
    echo "Creating .env from .env.example..."
    
    if [ -f "${SCRIPT_DIR}/.env.example" ]; then
        cp "${SCRIPT_DIR}/.env.example" "${SCRIPT_DIR}/.env"
        echo "✅ Created .env file. Please update it with your actual values."
    else
        echo "❌ .env.example not found. Please create a .env file manually."
    fi
fi

# Validate Python installation
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1)
    echo "✅ Python installed: ${PYTHON_VERSION}"
else
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo ""
    echo "⚠️  No virtual environment detected."
    echo "   It's recommended to use a virtual environment."
    echo "   Create one with: python3 -m venv venv"
    echo "   Activate with: source venv/bin/activate"
fi

# Validate required Python packages
echo ""
echo "Checking required packages..."
python3 -c "
import sys
required_packages = [
    'crewai',
    'asyncpg',
    'redis',
    'pydantic',
    'dotenv'
]

missing = []
for package in required_packages:
    try:
        if package == 'dotenv':
            import dotenv
        else:
            __import__(package)
    except ImportError:
        missing.append(package)

if missing:
    print('❌ Missing packages:', ', '.join(missing))
    print('   Install with: pip install -r requirements.txt')
    sys.exit(1)
else:
    print('✅ All required packages installed')
"

# Source this file to export PYTHONPATH
echo ""
echo "✅ Environment setup complete!"
echo ""
echo "To use this environment in your current shell:"
echo "   source ${SCRIPT_DIR}/setup_env.sh"
echo ""
echo "To run AUREN:"
echo "   python ${SCRIPT_DIR}/start_auren.py" 