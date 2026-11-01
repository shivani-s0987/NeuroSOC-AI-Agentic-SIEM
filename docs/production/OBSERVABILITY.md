# Observability

## Endpoints

- `/health/live`: process liveness; should remain healthy if external providers are unavailable.
- `/health/ready`: database readiness for API traffic.
- `/api/v1/realtime/health`: authorized realtime worker state.

Docker and orchestration probes use liveness. Traffic is only routed after readiness.

## Logging

HTTP logs are emitted as JSON and include timestamp, level, logger, method, path, status, duration, and request ID. Do not log credentials, tokens, API keys, database URLs, full confidential payloads, or user passwords. Correlate downstream operations with a propagated request ID or trace ID.

## Metrics

Prometheus exposition is not currently included. A production deployment must scrape application metrics from an authenticated private endpoint for API latency/error counts, database pool health, worker outcomes/retries, ingestion throughput, detection latency, alert generation, and realtime connections.

## Troubleshooting

1. Check `/health/live`; restart if it fails consistently.
2. Check `/health/ready`; inspect PostgreSQL connectivity and pool errors.
3. Inspect worker logs and event `processing_status`.
4. Check Redis/Celery connectivity separately when Celery is enabled.
5. Examine provider errors without exposing provider credentials.
