# NEUROS Cognitive Service - Production Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 neuros && \
    chown -R neuros:neuros /app

# Copy requirements first for better caching
COPY --chown=neuros:neuros requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=neuros:neuros section_8_neuros_graph.py .
COPY --chown=neuros:neuros neuros_agent_profile.yaml /config/
COPY --chown=neuros:neuros main.py .

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data && \
    chown -R neuros:neuros /app/logs /app/data

# Switch to non-root user
USER neuros

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO
ENV SERVICE_NAME=neuros-cognitive

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the service
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"] 