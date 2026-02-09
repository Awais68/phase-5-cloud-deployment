"""
Production-Ready FastAPI Application Instrumentation
Includes: Prometheus metrics, OpenTelemetry tracing, structured logging

This module demonstrates how to instrument a FastAPI application with:
1. Prometheus metrics (via prometheus_client)
2. OpenTelemetry distributed tracing (Jaeger backend)
3. Structured JSON logging (Loki-friendly)
4. Correlation IDs across logs, metrics, and traces
"""

import json
import logging
import time
import uuid
from contextvars import ContextVar
from datetime import datetime
from typing import Optional, Callable

from fastapi import FastAPI, Request, Response, Depends
from fastapi.responses import JSONResponse
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    generate_latest,
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
)
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

# ==========================================
# Configuration
# ==========================================

SERVICE_NAME = "backend"  # Change per service: backend, notification, recurring-task, audit-log
SERVICE_VERSION = "1.0.0"
ENVIRONMENT = "development"  # Change to production for OKE
JAEGER_ENDPOINT = "http://jaeger-collector.monitoring.svc.cluster.local:4317"

# ==========================================
# Context Variables for Correlation
# ==========================================

correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


# ==========================================
# Structured Logging Setup
# ==========================================

class StructuredLogger:
    """
    Structured JSON logger for Loki ingestion via Promtail.

    Logs are output to stdout in JSON format with consistent fields:
    - timestamp: ISO 8601 format
    - level: INFO, WARNING, ERROR, DEBUG
    - service: Service name
    - message: Log message
    - correlation_id: Request correlation ID
    - trace_id: OpenTelemetry trace ID
    - span_id: OpenTelemetry span ID
    - **kwargs: Additional structured fields
    """

    def __init__(self, service_name: str, version: str):
        self.service_name = service_name
        self.version = version
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.INFO)

        # Remove default handlers
        self.logger.handlers = []

        # Add stdout handler with no formatting (we format as JSON)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.logger.addHandler(handler)

    def _get_trace_context(self) -> dict:
        """Extract current trace and span IDs from OpenTelemetry context."""
        span = trace.get_current_span()
        span_context = span.get_span_context()

        if span_context.is_valid:
            return {
                "trace_id": format(span_context.trace_id, "032x"),
                "span_id": format(span_context.span_id, "016x"),
            }
        return {"trace_id": None, "span_id": None}

    def _format_log(self, level: str, message: str, **kwargs) -> str:
        """Format log entry as JSON."""
        trace_context = self._get_trace_context()

        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "service": self.service_name,
            "version": self.version,
            "environment": ENVIRONMENT,
            "message": message,
            "correlation_id": correlation_id_var.get(),
            "user_id": user_id_var.get(),
            "trace_id": trace_context["trace_id"],
            "span_id": trace_context["span_id"],
            **kwargs,
        }

        # Remove None values to reduce log size
        return json.dumps({k: v for k, v in log_entry.items() if v is not None})

    def info(self, message: str, **kwargs):
        """Log INFO level message."""
        self.logger.info(self._format_log("INFO", message, **kwargs))

    def warning(self, message: str, **kwargs):
        """Log WARNING level message."""
        self.logger.warning(self._format_log("WARNING", message, **kwargs))

    def error(self, message: str, **kwargs):
        """Log ERROR level message."""
        self.logger.error(self._format_log("ERROR", message, **kwargs))

    def debug(self, message: str, **kwargs):
        """Log DEBUG level message."""
        self.logger.debug(self._format_log("DEBUG", message, **kwargs))


# Initialize logger
logger = StructuredLogger(SERVICE_NAME, SERVICE_VERSION)


# ==========================================
# Prometheus Metrics Setup
# ==========================================

# Create custom registry (optional, for better isolation)
registry = CollectorRegistry()

# Application info metric
app_info = Info(
    "app",
    "Application information",
    registry=registry
)
app_info.info({
    "service": SERVICE_NAME,
    "version": SERVICE_VERSION,
    "environment": ENVIRONMENT,
})

# HTTP request metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=registry,
)

http_active_requests = Gauge(
    "http_active_requests",
    "Number of active HTTP requests",
    ["method", "endpoint"],
    registry=registry,
)

http_request_size_bytes = Histogram(
    "http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000],
    registry=registry,
)

http_response_size_bytes = Histogram(
    "http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
    buckets=[100, 1000, 10000, 100000, 1000000],
    registry=registry,
)

# Database operation metrics
db_operations_total = Counter(
    "db_operations_total",
    "Total database operations",
    ["operation", "table", "status"],
    registry=registry,
)

db_operation_duration_seconds = Histogram(
    "db_operation_duration_seconds",
    "Database operation duration in seconds",
    ["operation", "table"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=registry,
)

db_connection_pool_active = Gauge(
    "db_connection_pool_active",
    "Number of active database connections",
    registry=registry,
)

db_connection_pool_max = Gauge(
    "db_connection_pool_max",
    "Maximum database connection pool size",
    registry=registry,
)

# Kafka/Event metrics
kafka_events_published_total = Counter(
    "kafka_events_published_total",
    "Total Kafka events published",
    ["topic", "event_type", "status"],
    registry=registry,
)

kafka_events_consumed_total = Counter(
    "kafka_events_consumed_total",
    "Total Kafka events consumed",
    ["topic", "event_type", "status"],
    registry=registry,
)

kafka_event_publish_duration_seconds = Histogram(
    "kafka_event_publish_duration_seconds",
    "Kafka event publish duration in seconds",
    ["topic", "event_type"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=registry,
)

kafka_event_processing_duration_seconds = Histogram(
    "kafka_event_processing_duration_seconds",
    "Kafka event processing duration in seconds",
    ["topic", "event_type"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=registry,
)

# Business metrics (examples - customize per service)
task_operations_total = Counter(
    "task_operations_total",
    "Total task operations",
    ["operation", "status"],  # operation: create, update, delete, complete
    registry=registry,
)

notifications_sent_total = Counter(
    "notifications_sent_total",
    "Total notifications sent",
    ["channel", "status"],  # channel: email, push, websocket
    registry=registry,
)

recurring_task_generation_lag_seconds = Gauge(
    "recurring_task_generation_lag_seconds",
    "Lag in recurring task generation (seconds behind schedule)",
    registry=registry,
)

audit_log_writes_total = Counter(
    "audit_log_writes_total",
    "Total audit log writes",
    ["status"],
    registry=registry,
)


# ==========================================
# OpenTelemetry Tracing Setup
# ==========================================

def configure_opentelemetry():
    """
    Configure OpenTelemetry with Jaeger exporter.

    This sets up:
    - Resource attributes (service name, version, environment)
    - OTLP exporter to Jaeger collector
    - Batch span processor for performance
    - Trace context propagation
    """

    # Create resource with service information
    resource = Resource.create({
        "service.name": SERVICE_NAME,
        "service.version": SERVICE_VERSION,
        "deployment.environment": ENVIRONMENT,
    })

    # Create tracer provider
    tracer_provider = TracerProvider(resource=resource)

    # Create OTLP exporter (Jaeger-compatible)
    otlp_exporter = OTLPSpanExporter(
        endpoint=JAEGER_ENDPOINT,
        insecure=True,  # Set to False in production with TLS
    )

    # Add batch span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Set global tracer provider
    trace.set_tracer_provider(tracer_provider)

    logger.info("OpenTelemetry configured", jaeger_endpoint=JAEGER_ENDPOINT)


# ==========================================
# FastAPI Application
# ==========================================

app = FastAPI(
    title=f"{SERVICE_NAME.title()} Service",
    description=f"{SERVICE_NAME.title()} microservice with full observability",
    version=SERVICE_VERSION,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# Middleware for Metrics and Correlation
# ==========================================

class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Generates/propagates correlation IDs
    2. Extracts user IDs from headers
    3. Measures request duration
    4. Records metrics
    5. Logs requests
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        correlation_id_var.set(correlation_id)

        # Extract user ID if present
        user_id = request.headers.get("X-User-ID")
        if user_id:
            user_id_var.set(user_id)

        # Extract trace context for propagation
        propagator = TraceContextTextMapPropagator()
        context = propagator.extract(carrier=dict(request.headers))

        # Get current span and set attributes
        span = trace.get_current_span()
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        span.set_attribute("http.correlation_id", correlation_id)
        if user_id:
            span.set_attribute("user.id", user_id)

        # Normalize endpoint for metrics (remove path parameters)
        endpoint = self._normalize_endpoint(request.url.path)

        # Increment active requests
        http_active_requests.labels(method=request.method, endpoint=endpoint).inc()

        # Measure request size
        content_length = request.headers.get("content-length", 0)
        if content_length:
            http_request_size_bytes.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(int(content_length))

        # Start timer
        start_time = time.time()

        try:
            # Process request
            response = await call_next(request)
            status = response.status_code

            # Measure response size
            if hasattr(response, "headers") and "content-length" in response.headers:
                http_response_size_bytes.labels(
                    method=request.method,
                    endpoint=endpoint,
                ).observe(int(response.headers["content-length"]))

        except Exception as exc:
            # Record exception in span
            span.record_exception(exc)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc)))

            # Log error
            logger.error(
                "Request failed with exception",
                method=request.method,
                endpoint=endpoint,
                exception=str(exc),
                exception_type=type(exc).__name__,
            )

            # Set status for metrics
            status = 500

            # Re-raise exception
            raise

        finally:
            # Calculate duration
            duration = time.time() - start_time

            # Record metrics
            http_requests_total.labels(
                method=request.method,
                endpoint=endpoint,
                status=status,
            ).inc()

            http_request_duration_seconds.labels(
                method=request.method,
                endpoint=endpoint,
            ).observe(duration)

            http_active_requests.labels(
                method=request.method,
                endpoint=endpoint,
            ).dec()

            # Log request
            log_level = "error" if status >= 500 else "warning" if status >= 400 else "info"
            getattr(logger, log_level)(
                "HTTP request completed",
                method=request.method,
                endpoint=endpoint,
                status=status,
                duration_ms=round(duration * 1000, 2),
            )

            # Set span attributes
            span.set_attribute("http.status_code", status)
            span.set_attribute("http.duration_ms", duration * 1000)

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id

        return response

    def _normalize_endpoint(self, path: str) -> str:
        """
        Normalize endpoint path for metrics cardinality control.

        Examples:
        - /tasks/123 -> /tasks/{id}
        - /users/abc/tasks/456 -> /users/{id}/tasks/{id}
        """
        parts = path.split("/")
        normalized = []

        for part in parts:
            # Replace UUIDs and numeric IDs with {id}
            if part and (part.isdigit() or len(part) == 36):
                normalized.append("{id}")
            else:
                normalized.append(part)

        return "/".join(normalized)


# Add middleware
app.add_middleware(ObservabilityMiddleware)


# ==========================================
# Startup and Shutdown Events
# ==========================================

@app.on_event("startup")
async def startup_event():
    """Initialize observability on startup."""
    configure_opentelemetry()

    # Instrument FastAPI automatically
    FastAPIInstrumentor.instrument_app(app)

    # Instrument SQLAlchemy (if using)
    # SQLAlchemyInstrumentor().instrument(engine=engine)

    # Instrument requests library (for external HTTP calls)
    RequestsInstrumentor().instrument()

    logger.info("Application started", service=SERVICE_NAME, version=SERVICE_VERSION)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Application shutting down", service=SERVICE_NAME)


# ==========================================
# Health and Metrics Endpoints
# ==========================================

@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes liveness probe."""
    return {"status": "healthy", "service": SERVICE_NAME, "version": SERVICE_VERSION}


@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint for Kubernetes readiness probe.

    Add checks for:
    - Database connectivity
    - External service dependencies
    - Critical resources
    """
    # TODO: Add actual readiness checks
    return {"status": "ready", "service": SERVICE_NAME}


@app.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint.

    Scraped by ServiceMonitor every 30s.
    """
    return Response(
        content=generate_latest(registry),
        media_type=CONTENT_TYPE_LATEST,
    )


# ==========================================
# Example Instrumented Endpoints
# ==========================================

@app.post("/tasks")
async def create_task(request: Request):
    """
    Example endpoint: Create a task.

    Demonstrates:
    - Custom span creation
    - Span attributes
    - Business metric recording
    - Structured logging
    - Database operation tracking
    """
    tracer = trace.get_tracer(__name__)

    with tracer.start_as_current_span("create_task") as span:
        try:
            # Parse request body
            body = await request.json()

            # Set span attributes
            span.set_attribute("task.title", body.get("title", ""))
            span.set_attribute("task.user_id", body.get("user_id", ""))

            # Log task creation
            logger.info(
                "Creating task",
                task_title=body.get("title"),
                user_id=body.get("user_id"),
            )

            # Simulate database operation
            with tracer.start_as_current_span("db.insert_task") as db_span:
                db_span.set_attribute("db.operation", "insert")
                db_span.set_attribute("db.table", "tasks")

                db_start = time.time()

                # TODO: Actual database operation
                # task = await db.tasks.create(body)
                time.sleep(0.01)  # Simulate DB latency

                db_duration = time.time() - db_start

                # Record database metrics
                db_operations_total.labels(
                    operation="insert",
                    table="tasks",
                    status="success",
                ).inc()

                db_operation_duration_seconds.labels(
                    operation="insert",
                    table="tasks",
                ).observe(db_duration)

            # Simulate Kafka event publishing
            with tracer.start_as_current_span("kafka.publish_task_created") as kafka_span:
                kafka_span.set_attribute("messaging.system", "kafka")
                kafka_span.set_attribute("messaging.destination", "task.created")
                kafka_span.set_attribute("messaging.destination_kind", "topic")

                kafka_start = time.time()

                # TODO: Actual Kafka publishing
                # await kafka.publish("task.created", {"task_id": task.id})
                time.sleep(0.05)  # Simulate Kafka latency

                kafka_duration = time.time() - kafka_start

                # Record Kafka metrics
                kafka_events_published_total.labels(
                    topic="task.created",
                    event_type="task_created",
                    status="success",
                ).inc()

                kafka_event_publish_duration_seconds.labels(
                    topic="task.created",
                    event_type="task_created",
                ).observe(kafka_duration)

            # Record business metric
            task_operations_total.labels(
                operation="create",
                status="success",
            ).inc()

            logger.info(
                "Task created successfully",
                task_id="task-123",  # Replace with actual task ID
                user_id=body.get("user_id"),
            )

            return {"status": "created", "task_id": "task-123"}

        except Exception as e:
            # Record failure metrics
            task_operations_total.labels(
                operation="create",
                status="error",
            ).inc()

            # Log error
            logger.error(
                "Failed to create task",
                error=str(e),
                error_type=type(e).__name__,
            )

            # Set span status
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            span.record_exception(e)

            raise


# ==========================================
# Helper Functions for Instrumentation
# ==========================================

def track_database_operation(operation: str, table: str):
    """
    Decorator for tracking database operations.

    Usage:
        @track_database_operation("select", "tasks")
        async def get_tasks():
            return await db.tasks.all()
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)

            with tracer.start_as_current_span(f"db.{operation}_{table}") as span:
                span.set_attribute("db.operation", operation)
                span.set_attribute("db.table", table)

                start_time = time.time()
                status = "success"

                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    status = "error"
                    span.record_exception(e)
                    raise
                finally:
                    duration = time.time() - start_time

                    db_operations_total.labels(
                        operation=operation,
                        table=table,
                        status=status,
                    ).inc()

                    db_operation_duration_seconds.labels(
                        operation=operation,
                        table=table,
                    ).observe(duration)

        return wrapper

    return decorator


def track_kafka_event(topic: str, event_type: str, operation: str = "publish"):
    """
    Decorator for tracking Kafka event operations.

    Usage:
        @track_kafka_event("task.created", "task_created", "publish")
        async def publish_task_created(task_id: str):
            await kafka.publish("task.created", {"task_id": task_id})
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)

            with tracer.start_as_current_span(f"kafka.{operation}") as span:
                span.set_attribute("messaging.system", "kafka")
                span.set_attribute("messaging.destination", topic)
                span.set_attribute("messaging.destination_kind", "topic")

                start_time = time.time()
                status = "success"

                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    status = "failed"
                    span.record_exception(e)
                    raise
                finally:
                    duration = time.time() - start_time

                    if operation == "publish":
                        kafka_events_published_total.labels(
                            topic=topic,
                            event_type=event_type,
                            status=status,
                        ).inc()

                        kafka_event_publish_duration_seconds.labels(
                            topic=topic,
                            event_type=event_type,
                        ).observe(duration)
                    else:  # consume
                        kafka_events_consumed_total.labels(
                            topic=topic,
                            event_type=event_type,
                            status=status,
                        ).inc()

                        kafka_event_processing_duration_seconds.labels(
                            topic=topic,
                            event_type=event_type,
                        ).observe(duration)

        return wrapper

    return decorator


# ==========================================
# Main Entry Point
# ==========================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_config=None,  # Disable default logging (we use structured logging)
    )
