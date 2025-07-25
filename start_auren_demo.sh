#!/bin/bash
# AUREN Demo Startup Script
# This script helps you start all AUREN services

echo "🧠 AUREN Demo Startup Script"
echo "============================"
echo ""

# Set PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
echo "✅ PYTHONPATH configured"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi
echo "✅ Docker is running"

# Function to open new terminal
open_terminal() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        osascript -e "tell app \"Terminal\" to do script \"cd $(pwd) && export PYTHONPATH=$PYTHONPATH:$(pwd) && $1\""
    else
        # Linux (try common terminal emulators)
        if command -v gnome-terminal &> /dev/null; then
            gnome-terminal -- bash -c "cd $(pwd) && export PYTHONPATH=$PYTHONPATH:$(pwd) && $1; exec bash"
        elif command -v xterm &> /dev/null; then
            xterm -e "cd $(pwd) && export PYTHONPATH=$PYTHONPATH:$(pwd) && $1; bash" &
        else
            echo "Please run in a new terminal: $1"
        fi
    fi
}

echo ""
echo "📋 Starting AUREN Services..."
echo ""

# Step 1: Start Docker services
echo "1️⃣ Starting Docker services..."
docker-compose -f docker-compose.dev.yml up -d
if [ $? -eq 0 ]; then
    echo "✅ Docker services started successfully"
else
    echo "❌ Failed to start Docker services"
    exit 1
fi

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 5

# Step 2: Start Dashboard API
echo ""
echo "2️⃣ Starting Dashboard API in new terminal..."
open_terminal "source .venv/bin/activate && python auren/api/dashboard_api.py"
echo "✅ Dashboard API starting..."

# Step 3: Start WebSocket Server
echo ""
echo "3️⃣ Starting WebSocket server in new terminal..."
open_terminal "source .venv/bin/activate && python auren/realtime/enhanced_websocket_streamer.py"
echo "✅ WebSocket server starting..."

# Wait for services to start
echo ""
echo "⏳ Waiting for services to start (10 seconds)..."
sleep 10

# Step 4: Instructions for demo
echo ""
echo "✨ AUREN is starting up!"
echo ""
echo "📊 Next steps:"
echo "1. Wait for the services to fully start (check the terminals)"
echo "2. Run the demo: python auren/demo/demo_neuroscientist.py --duration 2"
echo "3. Open dashboard: http://localhost:8000/dashboard"
echo ""
echo "🔍 To check system health:"
echo "   ./run_health_check.sh"
echo ""
echo "🛑 To stop all services:"
echo "   docker-compose -f docker-compose.dev.yml down"
echo "   (Then close the terminal windows)"
echo ""
echo "Enjoy exploring AUREN! 🧠✨" 