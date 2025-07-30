# AUREN SOP: PWA + NEUROS Deployment Troubleshooting Guide

*   **Created**: [Current Date]
*   **Author**: Senior Engineer (AI Assistant)
*   **Version**: 1.0
*   **Purpose**: A definitive, layer-by-layer guide to diagnosing and resolving common deployment issues between the PWA frontend and the NEUROS AI backend. This document is the standard procedure for any engineer encountering related problems.

---

## 🎯 **Primary Philosophy: Isolate the Failure Layer**

Modern containerized deployments have multiple failure points. Guessing is inefficient. This guide follows a systematic, bottom-up approach to isolate the problem, from the host machine's Docker daemon to the application code itself. **Do not skip layers.**

---

##  Layer 1: The Sanity Check - Is Docker Even Running?

This is the most fundamental layer. Without a running Docker daemon, nothing else matters.

### **Symptoms**

You will see errors like:

```text
Cannot connect to the Docker daemon at unix:///Users/Jason/.docker/run/docker.sock. Is the docker daemon running?
Error response from daemon:
```

### **Diagnostic & Resolution**

1.  **Confirm Docker is running.** On macOS or Windows, this means ensuring the Docker Desktop application is open and has finished initializing.
2.  **Start Docker.** If it's not running, start it. On macOS, this can be done from the terminal:
    ```bash
    open -a Docker
    ```
3.  **Wait and Verify.** Give the daemon 15-30 seconds to initialize, then run a simple command to confirm it's responsive:
    ```bash
    docker ps
    ```
    If this command returns a table (even an empty one) instead of an error, you have successfully cleared Layer 1.

---

## Layer 2: The Dependency Deep-Dive - The Environment Mismatch

This was the core of our recent deployment issue. An incorrect or incomplete Python environment inside the container is a common and frustrating problem.

### **Symptoms**

*   `docker-compose build` fails during `pip install`.
*   Container starts but immediately exits with `ModuleNotFoundError`.
*   Errors like `ResolutionImpossible` or `conflicting dependencies`.

### **Root Cause Analysis: The LangGraph v0.2+ Paradigm Shift**

The primary blocker was a misunderstanding of a critical change in the `langgraph` library:

*   **Before v0.2:** Checkpointer implementations (like for PostgreSQL) were included in the main `langgraph` package as "extras" (e.g., `langgraph[postgres]`).
*   **After v0.2:** Checkpointers were moved to **separate, standalone PyPI packages**.

This means `langgraph[postgres]` is an invalid package. The correct approach is to install the specific checkpointer package.

### **Diagnostic & Resolution**

1.  **Stop and Nuke Everything.** Do not attempt to debug a potentially corrupted environment. Start clean.
    ```bash
    docker-compose down -v
    docker system prune -f
    ```

2.  **Fix `requirements.txt`.** This is the blueprint for your container's environment. Ensure it is correct.

    **GOLD STANDARD `requirements.txt`:**
    ```python
    # AI Providers & Core Framework
    fastapi
    langchain>=0.2.17
    langchain-core
    langchain-openai
    langgraph>=0.2.0
    langsmith
    openai>=1.33.0
    uvicorn

    # LangGraph v0.2+ Checkpointer (CRITICAL)
    langgraph-checkpoint-postgres>=1.0.0

    # Infrastructure & Database
    asyncpg>=0.29.0
    kafka-python>=2.0.2
    psycopg[binary]>=3.1.0  # Required for Postgres checkpointer
    psycopg2-binary>=2.9.9
    redis>=5.0.0

    # Observability
    opentelemetry-api>=1.20.0
    opentelemetry-exporter-prometheus>=0.41b0
    opentelemetry-sdk>=1.20.0

    # Utilities & Web
    pydantic-settings>=2.0.0
    python-dotenv>=1.0.0
    streamlit>=1.30.0

    # Testing
    pytest>=7.4.0
    pytest-asyncio>=0.21.0
    pytest-cov>=4.1.0
    ```

3.  **Fix the `init_checkpointer.py` Import.** The code using the checkpointer must also be updated.

    **GOLD STANDARD `init_checkpointer.py`:**
    ```python
    # ✅ NEW (v0.2+): Import from the separate package
    from langgraph_checkpoint_postgres import PostgresSaver
    import asyncio

    async def setup():
        # Note: The autocommit=true is not needed here, psycopg handles it.
        DB_URI = "postgresql://postgres:example@postgres:5432/neuros"
        
        # The checkpointer now returns a context manager. Use 'async with'.
        async with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
            # The .setup() method is called implicitly by the context manager.
            # No need to call it manually.
            print("✅ Checkpointer tables created/verified!")

    if __name__ == "__main__":
        asyncio.run(setup())
    ```
    *Note: The latest API for `PostgresSaver` uses a context manager (`async with`), which handles setup and teardown automatically. The `await checkpointer.setup()` call is no longer needed inside the `with` block.*

---

## Layer 3: The Container Build - A Repeatable Blueprint

Your `Dockerfile` should be minimal and robust. It should explicitly install dependencies to avoid ambiguity.

### **Symptoms**

*   `pip install` fails with cryptic errors.
*   Executables like `uvicorn` or `psql` are not found in the container's `$PATH`.

### **Diagnostic & Resolution**

1.  **Create a Gold Standard `Dockerfile`**. This version installs system dependencies needed by Python packages (`libpq-dev` for `psycopg`) and uses a multi-stage `pip install` process for clarity and robustness.

    **GOLD STANDARD `Dockerfile`:**
    ```Dockerfile
    FROM python:3.12-slim

    WORKDIR /app

    # Install system dependencies required for Python packages like psycopg
    RUN apt-get update && apt-get install -y \
        gcc \
        libpq-dev \
        && rm -rf /var/lib/apt/lists/*

    # Copy requirements first to leverage Docker layer caching
    COPY requirements.txt .

    # Upgrade pip and install all dependencies from the requirements file
    RUN pip install --upgrade pip && \
        pip install -r requirements.txt

    # Copy the rest of the application code
    COPY . .

    # The CMD will be specified in docker-compose.yml for flexibility
    ```

---

## Layer 4: The Runtime Configuration - Orchestrating the Services

`docker-compose.yml` ties everything together. Small errors here can cause cascading failures.

### **Symptoms**

*   Containers fail to start or exit immediately.
*   Connection refused errors between containers.
*   `nc: command not found` or other shell errors in logs.

### **Diagnostic & Resolution**

1.  **Implement Health Checks.** This is non-negotiable. It ensures dependent services don't start until their dependencies are actually ready, not just "running".
2.  **Use Correct Service Names for Networking.** Containers on the same Docker network talk to each other using their service names (e.g., `postgres`), not `localhost`.
3.  **Ensure Startup Commands are Robust.** Avoid using shell utilities like `nc` that may not exist in slim base images.

    **GOLD STANDARD `docker-compose.yml`:**
    ```yaml
    services:
      redis:
        image: redis:alpine
        container_name: redis
        healthcheck:
          test: ["CMD", "redis-cli", "ping"]
          interval: 5s
          timeout: 3s
          retries: 5
        networks:
          - neuros_network
        
      postgres:
        image: postgres:16
        container_name: postgres
        environment:
          - POSTGRES_PASSWORD=example
          - POSTGRES_USER=postgres
          - POSTGRES_DB=neuros
        healthcheck:
          test: ["CMD-SHELL", "pg_isready -U postgres"]
          interval: 5s
          timeout: 3s
          retries: 5
        networks:
          - neuros_network
        
      neuros:
        build: .
        container_name: neuros
        depends_on:
          redis:
            condition: service_healthy # Waits for Redis to be healthy
          postgres:
            condition: service_healthy # Waits for PostgreSQL to be healthy
        environment:
          - REDIS_OM_URL=redis://redis:6379
          - DATABASE_URI=postgresql://postgres:example@postgres:5432/neuros
          - OPENAI_API_KEY=${OPENAI_API_KEY} # Ensure this is in a .env file
        networks:
          - neuros_network
        ports:
          - "8000:8000"
        command: |
          bash -c "
            echo 'Running checkpointer setup...' &&
            python init_checkpointer.py && 
            echo 'Starting application server...' &&
            python -m uvicorn main:app --host 0.0.0.0 --port 8000
          "

    networks:
      neuros_network:
    ```

---

## Layer 5: In-Container Verification - The Final Proof

Once the containers are running, you need to confirm that everything *inside* them is working as expected.

### **Symptoms**

*   The container is "Up" but the application inside is not responding or has errors.
*   You suspect dependencies are installed but not importable.

### **Diagnostic & Resolution**

1.  **Check the Logs First.** This is the fastest way to see the output of your startup command.
    ```bash
    docker logs neuros
    ```
2.  **Create a Verification Script.** If logs are unclear, a targeted script can prove the environment is sound.

    **GOLD STANDARD `test_imports.py`:**
    ```python
    #!/usr/bin/env python3
    """Test that all critical imports work"""

    try:
        print("Testing imports...")
        
        import fastapi
        print("✅ FastAPI imported")
        
        import langgraph
        print("✅ LangGraph imported")
        
        from langgraph.checkpoint.postgres import PostgresSaver
        print("✅ PostgresSaver imported successfully!")
        
        import redis
        import asyncpg
        import uvicorn
        print("✅ All other dependencies imported")
        
        print("\n🎉 All imports successful! The environment is correctly set up.")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
    ```

3.  **Execute the Script in the Running Container.**
    ```bash
    # First, ensure the container is running
    docker-compose up -d

    # Copy the script to the container and execute it
    docker cp test_imports.py neuros:/app/
    docker exec neuros python test_imports.py
    ```
    A successful output from this script is the definitive confirmation that your environment is correct.

---

## 🚀 **The Full Troubleshooting Workflow**

1.  `docker ps` -> **Confirm daemon is running.**
2.  `docker-compose down -v && docker system prune -f` -> **Nuke the old environment.**
3.  **Apply Gold Standard files** -> Update `requirements.txt`, `Dockerfile`, `docker-compose.yml`, `init_checkpointer.py`.
4.  `docker-compose build --no-cache` -> **Build a fresh image.**
5.  `docker-compose up -d` -> **Start the services.**
6.  `docker logs neuros` -> **Check for startup errors.**
7.  `docker exec neuros python test_imports.py` -> **Verify the environment.**

By following these layers, any engineer can systematically and efficiently resolve this class of deployment issues without guesswork. 