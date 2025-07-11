#!/bin/bash
# Dependency resolution script for AUREN 2.0

set -e

echo "🔧 Resolving AUREN 2.0 dependencies..."

# Backup current requirements
cp requirements.txt requirements.txt.backup

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install base dependencies first
echo "Installing base dependencies..."
pip install -r requirements/base.txt

# Install AI dependencies
echo "Installing AI dependencies..."
pip install -r requirements/ai.txt

# Install CV dependencies
echo "Installing CV dependencies..."
pip install -r requirements/cv.txt

# Install production dependencies
echo "Installing production dependencies..."
pip install -r requirements/prod.txt

# Generate requirements.lock
echo "Generating requirements.lock..."
pip freeze > requirements.lock

echo "✅ Dependencies resolved successfully!"
echo "📝 New requirements.lock generated"
