#!/bin/bash

# Stop all AUREN services to free up computer resources

echo "🛑 Stopping AUREN Local Services"
echo "================================"

# Show what's currently running
echo "Currently running services:"
docker ps --format "table {{.Names}}\t{{.Status}}" | head -15

echo -e "\n⚠️  This will stop all AUREN services running locally"
read -p "Continue? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\nStopping services..."
    
    # Stop all services
    docker-compose down
    
    # Also stop any orphaned containers
    docker stop auren-api 2>/dev/null || true
    
    echo -e "\n✅ All services stopped!"
    echo "Your computer resources are now freed up."
    
    # Show confirmation
    echo -e "\nRemaining Docker containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}"
else
    echo "Cancelled - services still running"
fi 