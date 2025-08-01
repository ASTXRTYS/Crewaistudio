"""
Metrics Bridge API - Enables selective front-end access to backend observability data
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
import yaml
import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AUREN Metrics Bridge", version="1.0.0")

# Enable CORS for front-end access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
PROMETHEUS_URL = "http://auren-prometheus:9090"
KPI_REGISTRY_PATH = "/app/shared_modules/kpi_registry.yaml"

# Cache for KPI catalog
kpi_catalog_cache = None
kpi_catalog_last_update = 0
KPI_CATALOG_TTL = 300  # 5 minutes

class ConnectionManager:
    """Manages WebSocket connections for real-time metrics"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Dict] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = {"metrics": [], "user_id": None}

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]

    async def send_metric_update(self, websocket: WebSocket, data: dict):
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error sending metric update: {e}")

    def update_subscription(self, websocket: WebSocket, metrics: List[str], user_id: Optional[str]):
        if websocket in self.subscriptions:
            self.subscriptions[websocket]["metrics"] = metrics
            self.subscriptions[websocket]["user_id"] = user_id

manager = ConnectionManager()

async def get_kpi_catalog():
    """Get KPI catalog with caching"""
    global kpi_catalog_cache, kpi_catalog_last_update
    
    current_time = time.time()
    if kpi_catalog_cache and (current_time - kpi_catalog_last_update) < KPI_CATALOG_TTL:
        return kpi_catalog_cache
    
    try:
        # Try to read from container path first
        registry_path = Path(KPI_REGISTRY_PATH)
        if not registry_path.exists():
            # Fallback to local path
            registry_path = Path("agents/shared_modules/kpi_registry.yaml")
        
        with open(registry_path) as f:
            registry = yaml.safe_load(f)
        
        kpi_catalog_cache = registry.get("kpis", [])
        kpi_catalog_last_update = current_time
        return kpi_catalog_cache
    except Exception as e:
        logger.error(f"Error loading KPI registry: {e}")
        return []

async def query_prometheus(query: str, time_range: str = "1h", step: str = "15s") -> Dict:
    """Query Prometheus for metric data"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{PROMETHEUS_URL}/api/v1/query_range",
                params={
                    "query": query,
                    "start": f"now-{time_range}",
                    "end": "now",
                    "step": step
                },
                timeout=10.0
            )
            return response.json()
        except Exception as e:
            logger.error(f"Prometheus query error: {e}")
            return {"status": "error", "error": str(e)}

async def get_current_metric_value(metric: str, user_id: Optional[str] = None) -> Optional[float]:
    """Get current value of a metric"""
    query = metric
    if user_id:
        query = f'{metric}{{user_id="{user_id}"}}'
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={"query": query},
                timeout=5.0
            )
            data = response.json()
            
            if data["status"] == "success" and data["data"]["result"]:
                result = data["data"]["result"][0]
                return float(result["value"][1])
            return None
        except Exception as e:
            logger.error(f"Error getting current metric value: {e}")
            return None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "metrics-bridge"}

@app.get("/api/metrics/catalog")
async def get_available_metrics():
    """List all available metrics from KPI registry"""
    kpis = await get_kpi_catalog()
    
    return {
        "metrics": [
            {
                "id": kpi["name"],
                "name": kpi["description"],
                "metric": kpi["prometheus_metric"],
                "unit": kpi["unit"],
                "category": kpi.get("category", "general"),
                "thresholds": kpi.get("risk_thresholds", {})
            }
            for kpi in kpis
        ]
    }

@app.get("/api/metrics/query/{metric_name}")
async def query_metric(
    metric_name: str,
    user_id: Optional[str] = None,
    time_range: str = "1h",
    step: str = "15s"
):
    """Query specific metric from Prometheus"""
    # Validate metric name against catalog
    kpis = await get_kpi_catalog()
    valid_metrics = [kpi["prometheus_metric"] for kpi in kpis]
    
    if metric_name not in valid_metrics:
        raise HTTPException(status_code=404, detail=f"Metric {metric_name} not found in catalog")
    
    query = metric_name
    if user_id:
        query = f'{metric_name}{{user_id="{user_id}"}}'
    
    data = await query_prometheus(query, time_range, step)
    
    # Transform Prometheus format to frontend-friendly format
    if data.get("status") == "success" and data["data"]["result"]:
        result = data["data"]["result"][0]
        return {
            "metric": metric_name,
            "user_id": user_id,
            "data": [
                {
                    "timestamp": int(ts),
                    "value": float(val)
                }
                for ts, val in result["values"]
            ]
        }
    
    return {"metric": metric_name, "user_id": user_id, "data": []}

@app.get("/api/metrics/current/{metric_name}")
async def get_metric_current_value(
    metric_name: str,
    user_id: Optional[str] = None
):
    """Get current value of a metric"""
    value = await get_current_metric_value(metric_name, user_id)
    
    return {
        "metric": metric_name,
        "user_id": user_id,
        "value": value,
        "timestamp": int(time.time())
    }

@app.websocket("/api/metrics/stream")
async def metrics_stream(websocket: WebSocket):
    """Real-time metric streaming via WebSocket"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive subscription request
            try:
                request = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
                
                # Update subscription
                metrics = request.get("metrics", [])
                user_id = request.get("user_id")
                manager.update_subscription(websocket, metrics, user_id)
                
                # Send acknowledgment
                await websocket.send_json({
                    "type": "subscription_updated",
                    "metrics": metrics,
                    "user_id": user_id
                })
            except asyncio.TimeoutError:
                pass
            
            # Send metric updates for all subscriptions
            subscription = manager.subscriptions.get(websocket, {})
            for metric in subscription.get("metrics", []):
                value = await get_current_metric_value(
                    metric, 
                    subscription.get("user_id")
                )
                
                if value is not None:
                    await manager.send_metric_update(websocket, {
                        "type": "metric_update",
                        "metric": metric,
                        "value": value,
                        "timestamp": int(time.time()),
                        "user_id": subscription.get("user_id")
                    })
            
            # Wait before next update
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/api/metrics/aggregates")
async def get_metric_aggregates(
    metric_name: str,
    user_id: Optional[str] = None,
    time_range: str = "1h"
):
    """Get aggregated metrics (min, max, avg, current)"""
    base_query = metric_name
    if user_id:
        base_query = f'{metric_name}{{user_id="{user_id}"}}'
    
    # Run multiple queries in parallel
    queries = {
        "current": base_query,
        "avg": f"avg_over_time({base_query}[{time_range}])",
        "max": f"max_over_time({base_query}[{time_range}])",
        "min": f"min_over_time({base_query}[{time_range}])"
    }
    
    results = {}
    async with httpx.AsyncClient() as client:
        for agg_type, query in queries.items():
            try:
                response = await client.get(
                    f"{PROMETHEUS_URL}/api/v1/query",
                    params={"query": query},
                    timeout=5.0
                )
                data = response.json()
                
                if data["status"] == "success" and data["data"]["result"]:
                    result = data["data"]["result"][0]
                    results[agg_type] = float(result["value"][1])
                else:
                    results[agg_type] = None
            except Exception as e:
                logger.error(f"Error getting {agg_type} aggregate: {e}")
                results[agg_type] = None
    
    return {
        "metric": metric_name,
        "user_id": user_id,
        "time_range": time_range,
        "aggregates": results,
        "timestamp": int(time.time())
    }

@app.post("/api/metrics/batch")
async def query_metrics_batch(request: Dict[str, Any]):
    """Query multiple metrics in a single request"""
    metrics = request.get("metrics", [])
    user_id = request.get("user_id")
    time_range = request.get("time_range", "1h")
    
    results = []
    for metric in metrics:
        try:
            data = await query_metric(metric, user_id, time_range)
            results.append(data)
        except Exception as e:
            results.append({
                "metric": metric,
                "error": str(e),
                "data": []
            })
    
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)