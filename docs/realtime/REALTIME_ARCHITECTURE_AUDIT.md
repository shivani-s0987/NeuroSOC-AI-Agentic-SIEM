# Real-Time Architecture Audit

## Existing implementation

- FastAPI lifespan and middleware are defined in `backend/app/main.py`.
- Events are validated by Pydantic and persisted through SQLAlchemy.
- Detections are YAML-driven and correlated in `backend/app/services/detection_service.py`.
- Alerts are created by the detection service and exposed through versioned APIs.
- Authentication uses signed JWT bearer tokens and RBAC permissions.
- React uses one Axios client and currently has manual API refresh behavior.
- Docker Compose provides PostgreSQL and the API; it did not provide Redis or a worker.
- SQLite remains supported through SQLAlchemy configuration.

## Findings addressed

1. File/event creation was synchronous and did not create an explicit processing job.
2. There was no durable idempotency key or processing state on events.
3. Worker-style execution was not separated from request handling.
4. Detection could create duplicate detections only through application fingerprints; alert transaction boundaries needed stronger worker idempotency.
5. The dashboard had no controlled live transport.
6. Redis pub/sub was not previously used as a queue.

## Security requirements

WebSockets authenticate with an access token sent as the first JSON frame, avoiding credential-bearing URLs. The server derives the user from the JWT and database account, then applies `events:read`. Browser origin policy remains enforced by FastAPI CORS.
