#!/bin/bash

echo "🚀 CrewAI Studio Quick Start"
echo "=========================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "the" ]; then
    echo "📦 Setting up virtual environment..."
    ./install_venv.sh
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source the/bin/activate

# Install dependencies if needed
echo "📚 Checking dependencies..."
pip install -r requirements.txt --quiet

# Run CrewAI Studio
echo "🎯 Starting CrewAI Studio..."
echo "🌐 Open your browser to: http://localhost:8501"
echo "⏹️  Press Ctrl+C to stop"
echo ""

streamlit run app/app.py 