#!/bin/bash
# Fix ChromaDB NumPy 2.0 compatibility issue

echo "🔧 Fixing ChromaDB NumPy compatibility issue..."

# SSH into server and fix the issue
sshpass -p '.HvddX+@6dArsKd' ssh -o StrictHostKeyChecking=no root@144.126.215.218 << 'EOF'
echo "Stopping ChromaDB container..."
docker stop auren-chromadb

echo "Removing old container..."
docker rm auren-chromadb

echo "Creating new ChromaDB container with NumPy fix..."
docker run -d \
  --name auren-chromadb \
  --network auren-network \
  -e CHROMADB_HOST=0.0.0.0 \
  -e CHROMADB_PORT=8000 \
  -e IS_PERSISTENT=TRUE \
  -v chromadb-data:/chroma/chroma \
  --restart unless-stopped \
  chromadb/chroma:0.4.15

echo "Waiting for ChromaDB to start..."
sleep 10

echo "Checking ChromaDB status..."
docker ps | grep chromadb

echo "Checking logs..."
docker logs --tail 10 auren-chromadb

echo "✅ ChromaDB fix attempted. If still failing, may need to use older version."
EOF

echo "🎯 ChromaDB fix script completed!" 