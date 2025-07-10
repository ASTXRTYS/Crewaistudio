#!/bin/bash

# CrewAI Studio - Robust Startup Script
# This script prevents common startup issues

echo "🚀 Starting CrewAI Studio..."

# 1. Navigate to project root
cd "$(dirname "$0")"

# 2. Clear Python cache to prevent stale bytecode issues
echo "🧹 Clearing Python cache..."
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

# 3. Activate virtual environment if it exists
if [ -d "the" ]; then
    echo "🐍 Activating virtual environment..."
    source the/bin/activate
elif [ -d "venv" ]; then
    echo "🐍 Activating virtual environment..."
    source venv/bin/activate
elif [ -d "#" ]; then
    echo "🐍 Activating virtual environment..."
    source "#/bin/activate"
fi

# 4. Check if required files exist
if [ ! -f "app/app.py" ]; then
    echo "❌ Error: app/app.py not found!"
    exit 1
fi

if [ ! -f "img/crewai_logo.png" ]; then
    echo "⚠️  Warning: img/crewai_logo.png not found!"
fi

# 5. Install/update dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Checking dependencies..."
    pip install -q -r requirements.txt
fi

# 6. Start the application
echo "✅ Starting Streamlit application..."
cd app && streamlit run app.py --server.headless=false

echo "🎉 CrewAI Studio started successfully!" 