FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the ENTIRE auren directory structure
COPY auren/ /app/auren/
COPY config/ /app/config/

# Set the correct working directory for NEUROS
WORKDIR /app/auren/agents/neuros

# Command to run the REAL NEUROS
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
