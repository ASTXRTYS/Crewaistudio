# otel_init.py
import os
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Conditional imports based on environment
try:
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    HAS_OTLP = True
except ImportError:
    HAS_OTLP = False
    print("OTLP exporter not available, traces will not be exported")

try:
    from opentelemetry.instrumentation.kafka import KafkaInstrumentor
    HAS_KAFKA_INSTRUMENTATION = True
except ImportError:
    HAS_KAFKA_INSTRUMENTATION = False
    print("Kafka instrumentation not available")

def configure_otel(app):
    # -------- Resources & Providers --------
    res = Resource.create({"service.name": "auren-neuros"})
    tracer_provider = TracerProvider(resource=res)
    trace.set_tracer_provider(tracer_provider)

    # OTLP → Collector (uses env OTEL_EXPORTER_OTLP_ENDPOINT if set)
    if HAS_OTLP and os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter())
        )

    # Prometheus metrics exporter (scraped at /metrics on :8000)
    prom_reader = PrometheusMetricReader()
    metrics.set_meter_provider(
        MeterProvider(resource=res, metric_readers=[prom_reader])
    )

    # -------- Instrumentations --------
    FastAPIInstrumentor().instrument_app(app)
    if HAS_KAFKA_INSTRUMENTATION:
        KafkaInstrumentor().instrument()

    return prom_reader  # exposes /metrics