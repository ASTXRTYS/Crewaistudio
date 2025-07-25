#!/bin/bash
# Run AUREN health check with proper PYTHONPATH

echo "🏥 Running AUREN System Health Check..."
echo "Setting PYTHONPATH to include current directory..."
export PYTHONPATH=$PYTHONPATH:$(pwd)
python auren/utils/check_system_health.py 