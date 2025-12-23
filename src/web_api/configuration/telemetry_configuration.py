import logging
import os
from azure.monitor.opentelemetry.exporter import (
    AzureMonitorLogExporter,
    AzureMonitorMetricExporter,
    AzureMonitorTraceExporter,
)
from opentelemetry._logs import set_logger_provider
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import set_tracer_provider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.metrics.view import View
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.metrics import set_meter_provider
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor


def _setup_otel_trace(endpoint, resource):
    exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
    # Initialize a trace provider for the application. This is a factory for creating tracers.
    tracer_provider = TracerProvider(resource=resource)
    # Span processors are initialized with an exporter which is responsible
    # for sending the telemetry data to a particular backend.
    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    # Sets the global default tracer provider
    set_tracer_provider(tracer_provider)


def _setup_otel_metrics(endpoint, resource):
    exporter = OTLPMetricExporter(endpoint=endpoint)

    # Initialize a metric provider for the application. This is a factory for creating meters.
    meter_provider = MeterProvider(
        metric_readers=[PeriodicExportingMetricReader(exporter, export_interval_millis=5000)],
        resource=resource,
        views=[
            View(instrument_name="semantic_kernel*"),
        ],
    )
    # Sets the global default meter provider
    set_meter_provider(meter_provider)


def _setup_azure_monitor_tracing(connection_string, resource):
    exporter = AzureMonitorTraceExporter(connection_string=connection_string)

    # Initialize a trace provider for the application. This is a factory for creating tracers.
    tracer_provider = TracerProvider(resource=resource)
    # Span processors are initialized with an exporter which is responsible
    # for sending the telemetry data to a particular backend.
    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    # Sets the global default tracer provider
    set_tracer_provider(tracer_provider)


def _setup_azure_monitor_metrics(connection_string, resource):
    exporter = AzureMonitorMetricExporter(connection_string=connection_string)

    # Initialize a metric provider for the application. This is a factory for creating meters.
    export_interval_millis = int(os.getenv("METRIC_EXPORT_INTERVAL_MILLIS", 5000))
    meter_provider = MeterProvider(
        metric_readers=[
            PeriodicExportingMetricReader(exporter, export_interval_millis=export_interval_millis)],
        resource=resource,
        views=[
            View(instrument_name="semantic_kernel*"),
        ],
    )
    # Sets the global default meter provider
    set_meter_provider(meter_provider)


def _setup_logging(exporter, resource):
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    numeric_level = getattr(logging, log_level, logging.INFO)

    logger_provider = LoggerProvider(resource=resource)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(exporter))
    set_logger_provider(logger_provider)

    logger = logging.getLogger()
    logger.setLevel(numeric_level)

    handler = LoggingHandler(level=numeric_level)
    logger.addHandler(handler)  # OTEL Handler
    logger.addHandler(logging.StreamHandler())  # Log Stream Handler

    RequestsInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()
    logger.info("OpenTelemetry logging initialized")


def configure_telemetry():
    """
    Configures telemetry for the application using either Azure Monitor or OpenTelemetry exporters.

    This function sets up tracing, metrics, and logging exporters based on the presence of an
    Application Insights connection string. If the connection string is available, it configures
    Azure Monitor exporters for logging, tracing, and metrics. Otherwise, it assumes a local
    development environment and configures OpenTelemetry Protocol (OTLP) exporters.

    Environment Variables:
        APPLICATIONINSIGHTS_SERVICE_NAME: Optional; the name of the service for telemetry.
        APPLICATIONINSIGHTS_CONNECTION_STRING: Optional; the connection string for Azure Monitor.
        HOSTNAME: Optional; the instance identifier for the service.
        OTEL_EXPORTER_OTLP_ENDPOINT: Optional; the OTLP endpoint for local telemetry export.

    Raises:
        Any exceptions raised by the underlying exporter setup functions.
    """
    service_name = os.getenv("APPLICATIONINSIGHTS_SERVICE_NAME", "streaming-ask-licensing")
    OTEL_RESOURCE_ATTRIBUTES = {
        "service.name": service_name,
        "service.namespace": "chat_service",
        "service.instance.id": os.getenv("HOSTNAME", "local"),
    }
    resource = Resource.create(OTEL_RESOURCE_ATTRIBUTES)
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if connection_string:
        logging_exporter = AzureMonitorLogExporter(connection_string=connection_string)
        _setup_azure_monitor_tracing(connection_string=connection_string, resource=resource)
        _setup_azure_monitor_metrics(connection_string=connection_string, resource=resource)
        _setup_logging(exporter=logging_exporter, resource=resource)
    elif os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        # Assume we're running locally
        # Define resource attributes for OpenTelemetry
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4317")
        logging_exporter = OTLPLogExporter(endpoint=endpoint, insecure=True)
        _setup_otel_trace(endpoint, resource)
        _setup_otel_metrics(endpoint, resource)
        _setup_logging(exporter=logging_exporter, resource=resource)
    else:
        print(
            "No telemetry configuration found. Please set either "
            "APPLICATIONINSIGHTS_CONNECTION_STRING or OTEL_EXPORTER_OTLP_ENDPOINT."
        )
