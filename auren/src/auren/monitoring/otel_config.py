"""
OpenTelemetry Configuration for AUREN Production Monitoring.

This module sets up comprehensive observability for the AUREN system,
with special focus on the Neuroscientist MVP. It provides:
- Distributed tracing across all components
- Custom metrics for agent performance
- Context propagation for multi-agent support
- Integration with Prometheus and Jaeger/Tempo
"""

import os
import logging
from typing import Optional, Dict, Any
from opentelemetry import trace, metrics, baggage
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.asyncio import AsyncioInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.kafka import KafkaInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.sdk.metrics import MeterProvider, Counter, Histogram, UpDownCounter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.sdk.trace import TracerProvider, SpanProcessor
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode
from functools import wraps
import time
import asyncio

logger = logging.getLogger(__name__)


class AURENTelemetry:
    """
    Central telemetry configuration for AUREN.
    
    Provides unified setup for tracing, metrics, and logging
    with AUREN-specific customizations.
    """
    
    def __init__(
        self,
        service_name: str = "auren-neuroscientist",
        service_version: str = "1.0.0",
        otlp_endpoint: Optional[str] = None,
        prometheus_port: int = 8000,
        enable_console_export: bool = False
    ):
        """
        Initialize AUREN telemetry.
        
        Args:
            service_name: Name of the service (e.g., "auren-neuroscientist")
            service_version: Version of the service
            otlp_endpoint: OTLP collector endpoint (e.g., "localhost:4317")
            prometheus_port: Port for Prometheus metrics endpoint
            enable_console_export: Whether to export spans to console
        """
        self.service_name = service_name
        self.service_version = service_version
        self.otlp_endpoint = otlp_endpoint or os.getenv("OTLP_ENDPOINT", "localhost:4317")
        self.prometheus_port = prometheus_port
        self.enable_console_export = enable_console_export
        
        # Initialize providers
        self._tracer_provider: Optional[TracerProvider] = None
        self._meter_provider: Optional[MeterProvider] = None
        
        # Metrics
        self._metrics: Dict[str, Any] = {}
    
    def initialize(self):
        """Initialize all telemetry components."""
        logger.info(f"Initializing AUREN telemetry for {self.service_name}")
        
        # Create resource
        resource = Resource.create({
            SERVICE_NAME: self.service_name,
            SERVICE_VERSION: self.service_version,
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
            "service.namespace": "auren",
            "service.instance.id": os.getenv("HOSTNAME", "local")
        })
        
        # Initialize tracing
        self._init_tracing(resource)
        
        # Initialize metrics
        self._init_metrics(resource)
        
        # Initialize instrumentations
        self._init_instrumentations()
        
        # Set propagator for distributed tracing
        set_global_textmap(B3MultiFormat())
        
        logger.info("AUREN telemetry initialized successfully")
    
    def _init_tracing(self, resource: Resource):
        """Initialize distributed tracing."""
        # Create tracer provider
        self._tracer_provider = TracerProvider(resource=resource)
        
        # Add OTLP exporter
        if self.otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.otlp_endpoint,
                insecure=True  # Use TLS in production
            )
            self._tracer_provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
        
        # Add console exporter for debugging
        if self.enable_console_export:
            console_exporter = ConsoleSpanExporter()
            self._tracer_provider.add_span_processor(
                BatchSpanProcessor(console_exporter)
            )
        
        # Set as global tracer provider
        trace.set_tracer_provider(self._tracer_provider)
    
    def _init_metrics(self, resource: Resource):
        """Initialize metrics collection."""
        # Create meter provider with Prometheus reader
        prometheus_reader = PrometheusMetricReader(
            port=self.prometheus_port
        )
        
        self._meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[prometheus_reader]
        )
        
        # Set as global meter provider
        metrics.set_meter_provider(self._meter_provider)
        
        # Create AUREN-specific metrics
        meter = metrics.get_meter("auren.metrics")
        
        # Agent task metrics
        self._metrics["agent_tasks_total"] = meter.create_counter(
            name="auren_agent_tasks_processed_total",
            description="Total number of tasks processed by agents",
            unit="tasks"
        )
        
        self._metrics["task_duration"] = meter.create_histogram(
            name="auren_task_execution_duration_seconds",
            description="Task execution duration in seconds",
            unit="seconds"
        )
        
        # Token usage metrics
        self._metrics["tokens_used"] = meter.create_counter(
            name="auren_tokens_used_total",
            description="Total tokens consumed",
            unit="tokens"
        )
        
        self._metrics["token_cost"] = meter.create_counter(
            name="auren_llm_token_cost_usd_total",
            description="Total cost of tokens in USD",
            unit="USD"
        )
        
        # Neuroscientist-specific metrics
        self._metrics["hrv_analyses"] = meter.create_counter(
            name="auren_neuroscientist_hrv_analyses_total",
            description="Total HRV analyses performed",
            unit="analyses"
        )
        
        self._metrics["recovery_recommendations"] = meter.create_counter(
            name="auren_neuroscientist_recovery_recommendations_total",
            description="Total recovery recommendations made",
            unit="recommendations"
        )
        
        # System health metrics
        self._metrics["active_users"] = meter.create_up_down_counter(
            name="auren_active_users",
            description="Current number of active users",
            unit="users"
        )
        
        self._metrics["gateway_latency"] = meter.create_histogram(
            name="auren_gateway_latency_seconds",
            description="AI Gateway response latency",
            unit="seconds"
        )
    
    def _init_instrumentations(self):
        """Initialize automatic instrumentations."""
        # Asyncio instrumentation
        AsyncioInstrumentor().instrument()
        
        # Redis instrumentation
        RedisInstrumentor().instrument()
        
        # PostgreSQL instrumentation
        Psycopg2Instrumentor().instrument()
        
        # Kafka instrumentation (if available)
        try:
            KafkaInstrumentor().instrument()
        except Exception as e:
            logger.warning(f"Kafka instrumentation not available: {e}")
        
        # Logging instrumentation
        LoggingInstrumentor().instrument(
            set_logging_format=True,
            log_level=logging.INFO
        )
    
    def get_tracer(self, name: str) -> trace.Tracer:
        """Get a tracer instance."""
        return trace.get_tracer(name, self.service_version)
    
    def get_meter(self, name: str) -> metrics.Meter:
        """Get a meter instance."""
        return metrics.get_meter(name, self.service_version)
    
    def record_agent_task(
        self,
        agent_name: str,
        task_type: str,
        duration: float,
        status: str = "success"
    ):
        """Record agent task execution metrics."""
        attributes = {
            "agent.name": agent_name,
            "task.type": task_type,
            "status": status
        }
        
        self._metrics["agent_tasks_total"].add(1, attributes)
        self._metrics["task_duration"].record(duration, attributes)
    
    def record_token_usage(
        self,
        agent_name: str,
        model: str,
        tokens: int,
        cost: float
    ):
        """Record token usage metrics."""
        attributes = {
            "agent.name": agent_name,
            "model": model
        }
        
        self._metrics["tokens_used"].add(tokens, attributes)
        self._metrics["token_cost"].add(cost, attributes)
    
    def record_neuroscientist_activity(
        self,
        activity_type: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record Neuroscientist-specific activities."""
        attributes = {
            "activity.type": activity_type,
            "user.id": user_id
        }
        
        if metadata:
            # Add relevant metadata as attributes
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    attributes[f"metadata.{key}"] = value
        
        if activity_type == "hrv_analysis":
            self._metrics["hrv_analyses"].add(1, attributes)
        elif activity_type == "recovery_recommendation":
            self._metrics["recovery_recommendations"].add(1, attributes)


# Decorator for tracing AUREN operations
def otel_trace(
    operation_name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    record_exception: bool = True
):
    """
    Decorator for adding OpenTelemetry tracing to functions.
    
    Args:
        operation_name: Name of the operation (defaults to function name)
        attributes: Additional attributes to add to the span
        record_exception: Whether to record exceptions
    
    Usage:
        @otel_trace(operation_name="neuroscientist.analyze_hrv")
        async def analyze_hrv(data: Dict) -> Dict:
            # Your code here
            pass
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            span_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name) as span:
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Add function context
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    # Execute function
                    start_time = time.time()
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Record success
                    span.set_attribute("duration.seconds", duration)
                    span.set_status(Status(StatusCode.OK))
                    
                    return result
                    
                except Exception as e:
                    # Record exception
                    if record_exception:
                        span.record_exception(e)
                    span.set_status(
                        Status(StatusCode.ERROR, str(e))
                    )
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            span_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name) as span:
                # Add custom attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Add function context
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    # Execute function
                    start_time = time.time()
                    result = func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Record success
                    span.set_attribute("duration.seconds", duration)
                    span.set_status(Status(StatusCode.OK))
                    
                    return result
                    
                except Exception as e:
                    # Record exception
                    if record_exception:
                        span.record_exception(e)
                    span.set_status(
                        Status(StatusCode.ERROR, str(e))
                    )
                    raise
        
        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global telemetry instance
_telemetry: Optional[AURENTelemetry] = None


def init_telemetry(
    service_name: str = "auren-neuroscientist",
    **kwargs
) -> AURENTelemetry:
    """
    Initialize global telemetry instance.
    
    Args:
        service_name: Name of the service
        **kwargs: Additional configuration options
        
    Returns:
        Initialized telemetry instance
    """
    global _telemetry
    
    if _telemetry is None:
        _telemetry = AURENTelemetry(service_name, **kwargs)
        _telemetry.initialize()
    
    return _telemetry


def get_telemetry() -> AURENTelemetry:
    """Get the global telemetry instance."""
    if _telemetry is None:
        raise RuntimeError(
            "Telemetry not initialized. Call init_telemetry() first."
        )
    return _telemetry 