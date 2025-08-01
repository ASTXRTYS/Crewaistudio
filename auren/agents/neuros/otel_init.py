# otel_init.py
from opentelemetry import trace, metrics
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.prometheus import PrometheusExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.kafka import KafkaInstrumentor

def configure_otel(app):
    # -------- Resources & Providers --------
    res = Resource.create({"service.name": "auren-neuros"})
    tracer_provider = TracerProvider(resource=res)
    trace.set_tracer_provider(tracer_provider)

    # OTLP → Collector (uses env OTEL_EXPORTER_OTLP_ENDPOINT if set)
    tracer_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter())
    )

    # Prometheus metrics exporter (scraped at /metrics on :8000)
    prom_exporter = PrometheusExporter()
    metrics.set_meter_provider(
        MeterProvider(resource=res, metric_readers=[prom_exporter])
    )

    # -------- Instrumentations --------
    FastAPIInstrumentor().instrument_app(app)
    KafkaInstrumentor().instrument()

    return prom_exporter  # exposes /metrics 