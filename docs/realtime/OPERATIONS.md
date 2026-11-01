# Real-Time Operations

## Local startup

```bash
docker compose up --build
```

The Compose deployment starts PostgreSQL, Redis, API, worker, and frontend. Production credentials must be supplied through environment variables.

## Health

- `/health`: API liveness.
- `/realtime/health`: queue depth, failed jobs, and active WebSocket count. It requires settings-management permission.
- `/events/processing-status/{event_id}`: durable per-event status.

## Troubleshooting

Pending jobs with a healthy broker may indicate a stopped worker or enqueue configuration. Pending jobs in SQL should be processed by recovery/manual replay. Failed jobs should be inspected through processing-status and terminal worker errors before correcting the input or rule.
