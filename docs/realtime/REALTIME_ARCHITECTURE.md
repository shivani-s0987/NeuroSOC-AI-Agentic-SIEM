# Real-Time Architecture

FastAPI remains the API and streaming gateway. SQLAlchemy owns durable application state. Celery executes `neurosoc.process_event` tasks through Redis. PostgreSQL is the production source of truth; SQLite is supported for development and tests.

An ingestion transaction commits the normalized event, processing job, and notification together. Workers process persisted jobs, run detections and correlation, and commit outcomes idempotently.

Redis never replaces the database as the durable queue or notification replay store. The WebSocket gateway is authenticated and permission checked, while the notification REST endpoint provides reconciliation for missed updates.
