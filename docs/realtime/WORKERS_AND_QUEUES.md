# Workers and Queues

Run the Redis worker with:

```bash
celery -A app.worker --app-dir backend worker --loglevel=INFO
```

Without Redis/Celery configuration, run the database poller:

```bash
PYTHONPATH=backend python -m app.worker
```

Every event has a durable processing job. Pending jobs can be recovered after API, broker, or worker interruption. Worker tasks are retried with a bounded attempt count. Terminal failures remain in SQL with an operator-readable error. Detection fingerprints suppress duplicate alerts across repeated deliveries.
