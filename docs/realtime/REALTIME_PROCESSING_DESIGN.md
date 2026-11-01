# Real-Time Processing Design

## Selected technologies

- PostgreSQL for durable production state and SQLite for local development.
- Celery with Redis for asynchronous, acknowledged queue delivery.
- A database polling worker fallback when Celery/Redis is disabled.
- A durable SQL notification history plus WebSocket delivery.

Celery is used because it provides retries, worker concurrency, graceful shutdown, acknowledgement controls, and an independently managed process. Redis is used as transport and coordination only; processing and notification replay state remain durable in SQL.

## Flow

`API -> validation -> commit Event + ProcessingJob + notifications -> Celery enqueue -> worker -> detection/correlation -> alert persistence -> notification -> WebSocket/API reconciliation -> React`

The database commit happens before enqueue acknowledgement. If enqueue fails, the persisted pending job remains recoverable. Redis alone is never considered the source of truth.
