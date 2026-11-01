# Event Flow

1. `POST /events/ingest` validates and normalizes an event.
2. The event and processing job are committed atomically.
3. A versioned `event.created` notification is committed in the same transaction.
4. A Celery task is enqueued when Redis/Celery is configured.
5. The worker updates processing state and runs detection rules.
6. Detection and alert fingerprints prevent duplicate correlated results.
7. `event.processed` and alert notifications are persisted.
8. Authorized WebSocket clients receive connection status; clients reconcile durable notifications using the cursor API.
