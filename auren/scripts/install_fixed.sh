#!/bin/bash
# Install dependencies in correct order to avoid conflicts

echo "Installing AUREN dependencies in correct order..."

# 1. Core dependencies first
pip install -r requirements/base.txt

# 2. Install protobuf compromise version
pip install protobuf==4.25.3 --force-reinstall

# 3. AI dependencies (with specific versions)
pip install crewai==0.30.11
pip install "openai>=1.13.3,<2.0.0"
pip install crewai-tools==0.2.6
pip install "chromadb>=0.4.22,<0.5.0"
pip install "sqlalchemy>=2.0.27,<3.0.0"
pip install sentence-transformers>=2.3.0
pip install faiss-cpu>=1.7.4

# 4. CV dependencies (may show warnings but will work)
pip install opencv-python-headless==4.9.0.80
pip install mediapipe==0.10.9 || echo "MediaPipe installed with warnings"

# 5. Development dependencies
pip install -r requirements/dev.txt

# 6. Additional production dependencies
pip install prometheus-client==0.19.0
pip install structlog==24.1.0

echo "✅ All dependencies installed" 