#!/bin/bash
echo "🔧 Installing AUREN dependencies"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install core dependencies
echo "Installing core dependencies..."
pip install -r requirements.txt

# Install dev dependencies
echo "Installing development dependencies..."
pip install -r requirements-dev.txt

# Special handling for dlib (if needed)
echo "Checking dlib installation..."
python -c "import dlib" 2>/dev/null || {
    echo "Installing dlib (this may take a while)..."
    pip install cmake
    pip install dlib
}

# Verify installation
echo -e "\n✅ Verifying installation..."
python -c "
import crewai
import mediapipe
import cv2
print('✅ All core imports successful')
print(f'CrewAI version: {crewai.__version__}')
"

echo -e "\n✅ Dependencies installed successfully" 