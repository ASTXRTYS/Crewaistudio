#!/bin/bash
echo "🔧 AUREN Dependency Fix Script"

# Update requirements.txt with exact versions
cat > /auren/requirements.txt << EOF
# Core dependencies
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.5.3
python-multipart==0.0.6

# AI/ML dependencies
crewai==0.30.11
sentence-transformers==2.3.1
chromadb==0.4.22
faiss-cpu==1.7.4
numpy==1.26.3
scipy==1.11.4

# WhatsApp integration
requests==2.31.0
aiohttp==3.9.1

# Biometric analysis
opencv-python-headless==4.9.0.80
dlib==19.24.2
mediapipe==0.10.9

# Monitoring
prometheus-client==0.19.0
structlog==24.1.0
EOF

# Install and verify
pip install -r requirements.txt
python -c "import sentence_transformers, chromadb, faiss; print('✅ All dependencies installed')" 