#!/bin/bash

# Fix knowledge graph loading issue

echo "🔧 Fixing knowledge graph loading..."

cd auren/dashboard_v2/src/components

# Update KnowledgeGraph.jsx to handle missing agent_id gracefully
sed -i.bak 's/const \[agentId, setAgentId\] = createSignal("");/const [agentId, setAgentId] = createSignal("neuroscientist");/g' KnowledgeGraph.jsx

# Clean up backup
rm -f KnowledgeGraph.jsx.bak

# Rebuild
cd ../..
echo "🔨 Rebuilding dashboard with fix..."
npm run build

echo "✅ Knowledge graph loading fixed!" 