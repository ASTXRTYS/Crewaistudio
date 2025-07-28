#!/bin/bash

# AUREN ONE-COMMAND DEPLOYMENT
# Execute this to deploy everything

echo "╔══════════════════════════════════════════════════════════╗"
echo "║            AUREN PRODUCTION DEPLOYMENT                    ║"
echo "║         Deploying to aupex.ai @ 144.126.215.218         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "This will:"
echo "  ✓ Deploy all services to DigitalOcean"
echo "  ✓ Set up continuous operation (24/7)"
echo "  ✓ Configure auto-recovery and monitoring"
echo "  ✓ Make your dashboard live at https://aupex.ai"
echo ""
echo "You'll need to enter your server password when prompted."
echo ""
read -p "Ready to deploy? (y/n): " -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Executing deployment..."
    ./scripts/master_deploy.sh
else
    echo "Deployment cancelled."
fi 