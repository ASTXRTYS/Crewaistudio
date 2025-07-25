#!/bin/bash
# AUREN Master Script - Never worry about errors again!

echo "🧠 AUREN Health Intelligence System"
echo "===================================="

# Always set correct environment
export PYTHONPATH="$(pwd):$PYTHONPATH"

# Handle command
case "$1" in
    start)
        echo "🚀 Starting AUREN..."
        python auren_launcher.py
        ;;
    
    stop)
        echo "🛑 Stopping AUREN..."
        pkill -f dashboard_api.py
        pkill -f enhanced_websocket_streamer.py  
        pkill -f demo_neuroscientist.py
        docker-compose -f docker-compose.dev.yml down
        echo "✅ All services stopped"
        ;;
    
    status)
        echo "📊 AUREN Status:"
        echo -n "  Dashboard API: "
        lsof -i :8000 > /dev/null 2>&1 && echo "✅ Running" || echo "❌ Stopped"
        echo -n "  WebSocket Server: "
        lsof -i :8765 > /dev/null 2>&1 && echo "✅ Running" || echo "❌ Stopped"
        echo -n "  Redis: "
        docker ps | grep redis > /dev/null && echo "✅ Running" || echo "❌ Stopped"
        ;;
    
    demo)
        echo "🎭 Generating demo events..."
        python quick_dashboard_demo.py
        ;;
    
    health)
        echo "🏥 Running health check..."
        ./run_health_check.sh
        ;;
    
    *)
        echo "Usage: ./auren.sh {start|stop|status|demo|health}"
        echo ""
        echo "Commands:"
        echo "  start  - Start all AUREN services"
        echo "  stop   - Stop all AUREN services"
        echo "  status - Check service status"
        echo "  demo   - Generate demo events"
        echo "  health - Run system health check"
        ;;
esac 