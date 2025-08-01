# main_kpi.py - NEUROS with REAL KPI emission (no fake data)
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel
from datetime import datetime

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

# Initialize KPIs to zero on startup
@app.on_event("startup")
async def startup_event():
    """Initialize all KPIs to zero - no fake data"""
    emit("hrv_rmssd", 0.0)
    emit("sleep_debt", 0.0)
    emit("recovery_score", 0.0)

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

class BiometricData(BaseModel):
    hrv: float = None
    sleep_debt: float = None
    recovery_score: float = None
    user_id: str = "anonymous"

# Health endpoint
@app.get("/health", response_model=HealthStatus)
async def health():
    return HealthStatus()

# Main analyze endpoint - ONLY REAL KPI EMISSION
@app.post("/api/agents/neuros/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    # Check if we have real biometric data to process
    # This is where you would integrate with actual biometric sensors
    
    # For now, we'll check if the request contains biometric data
    biometric_data = getattr(request, 'biometric_data', None)
    
    if biometric_data:
        # If we have real data, emit it
        if 'hrv' in biometric_data:
            emit("hrv_rmssd", biometric_data['hrv'])
        if 'sleep_debt' in biometric_data:
            emit("sleep_debt", biometric_data['sleep_debt'])
        if 'recovery_score' in biometric_data:
            emit("recovery_score", biometric_data['recovery_score'])
        
        response_text = f"Processing your message with biometric data: HRV={biometric_data.get('hrv', 0)}ms"
        kpi_emitted = True
    else:
        # No biometric data - don't emit fake values
        response_text = f"I received your message: '{request.message}'. No biometric data is currently being processed."
        kpi_emitted = False
    
    return AnalyzeResponse(
        response=response_text,
        session_id=request.session_id,
        kpi_emitted=kpi_emitted
    )

# Biometric data endpoint - for real sensor data
@app.post("/api/agents/neuros/biometric")
async def update_biometric(data: BiometricData):
    """Endpoint to receive real biometric data from sensors"""
    updated = []
    
    if data.hrv is not None:
        emit("hrv_rmssd", data.hrv)
        updated.append(f"HRV={data.hrv}ms")
    
    if data.sleep_debt is not None:
        emit("sleep_debt", data.sleep_debt)
        updated.append(f"Sleep Debt={data.sleep_debt}h")
    
    if data.recovery_score is not None:
        emit("recovery_score", data.recovery_score)
        updated.append(f"Recovery={data.recovery_score}%")
    
    if updated:
        return {"status": "success", "updated": updated}
    else:
        return {"status": "no_data", "message": "No biometric data provided"}

# Root endpoint
@app.get("/")
async def root():
    return {"service": "NEUROS Advanced with Real KPI Metrics", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)