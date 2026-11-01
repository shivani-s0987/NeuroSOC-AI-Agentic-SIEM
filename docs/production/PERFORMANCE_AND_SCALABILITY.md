# Performance and Scalability

No production benchmark numbers are fabricated for this repository. Capacity must be established against a representative deployment.

## Required measurement plan

Record:

- Application/image version and commit.
- Deployment topology and instance sizes.
- Dataset sizes for events, alerts, IOCs, and users.
- Event ingestion workload, concurrency, duration, and payload distribution.
- Detection, IOC matching, alert, pagination, worker, and database connection metrics.
- Throughput and p50/p95/p99 latency.
- HTTP and worker error counts.
- PostgreSQL locks, query time, CPU, memory, pool usage, and disk.

## Execution

Use an isolated staging PostgreSQL database. Ramp load gradually and halt before producing customer/security data. A browser or load test tool may be chosen based on deployment support. Document the exact command and raw result artifacts.

## Known capacity controls

- API pool defaults are configurable in application settings.
- Worker concurrency is configurable for Celery.
- Polling fallback has bounded attempts and configurable delay.
- Database pagination and indexes must be verified with representative datasets.
