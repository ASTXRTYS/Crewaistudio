# main_kpi.py - NEUROS with KPI emission
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from datetime import datetime
import random

# Import KPI emitter
from shared_modules.kpi_emitter import emit

# Create FastAPI app
app = FastAPI(title="NEUROS Advanced with KPI")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus instrumentation - adds /metrics endpoint
Instrumentator().instrument(app).expose(app)

# Data models
class HealthStatus(BaseModel):
    status: str = "healthy"
    service: str = "neuros-advanced"
    timestamp: str = datetime.now().isoformat()
    opentelemetry_configured: bool = True
    kpi_enabled: bool = True

class AnalyzeRequest(BaseModel):
    message: str
    user_id: str = "anonymous"
    session_id: str = "default"

class AnalyzeResponse(BaseModel):
    response: str
    session_id: str
    kpi_emitted: bool = True

# Health endpoint
@app.get("/health", response_model=HealthStatus)
async def health():
    return HealthStatus()

# Main analyze endpoint with KPI emission
@app.post("/api/agents/neuros/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    # Emit pre-processing KPIs (simulated values for now)
    hrv_value = random.uniform(30, 70)  # Simulated HRV
    emit("hrv_rmssd", hrv_value)
    
    # Simple response for testing
    response_text = f"I received your message: '{request.message}'. Your simulated HRV is {hrv_value:.1f}ms."
    
    # Emit post-processing KPIs
    emit("sleep_debt", random.uniform(0, 8))
    emit("recovery_score", random.uniform(60, 100))
    
    return AnalyzeResponse(
        response=response_text,
        session_id=request.session_id,
        kpi_emitted=True
    )

# Root endpoint
@app.get("/")
async def root():
    return {"service": "NEUROS Advanced with KPI Metrics", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)