#!/bin/bash
# Simple AUREN startup script that prevents common errors

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Export PYTHONPATH to include project root
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

echo "🧠 Starting AUREN with proper environment..."
echo "PYTHONPATH=$PYTHONPATH"

# Run the bulletproof launcher
python "${SCRIPT_DIR}/auren_launcher.py" 