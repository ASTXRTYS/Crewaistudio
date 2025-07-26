#!/bin/bash

# Fix all API URLs in the dashboard to use relative paths

echo "🔧 Fixing Dashboard API URLs..."

cd auren/dashboard_v2/src

# Fix WebSocket URL to use dynamic host
sed -i.bak "s|ws://aupex.ai/ws|ws://\${window.location.host}/ws|g" App.jsx

# Fix all localhost API calls to use relative URLs
find . -name "*.jsx" -type f -exec sed -i.bak 's|http://localhost:8080/api/|/api/|g' {} +

# Fix any remaining localhost references
find . -name "*.jsx" -type f -exec sed -i.bak 's|http://localhost:8080|/api|g' {} +

# Clean up backup files
find . -name "*.bak" -type f -delete

echo "✅ API URLs fixed!"

# Rebuild the dashboard
cd ..
echo "🔨 Rebuilding dashboard..."
npm run build

echo "✅ Dashboard rebuilt with correct API URLs!" 