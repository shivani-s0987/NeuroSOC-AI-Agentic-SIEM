# Threat Intelligence Implementation Audit

## Repository state reviewed

- PR 6 realtime processing is present and uses durable SQL jobs, Celery/Redis, notifications, and authenticated WebSockets.
- Existing `threat_intel` and `mitre_techniques` tables are placeholders.
- Existing investigation enrichment queries threat-intel indicators directly.
- Detection rules contain MITRE technique references, but those references were not backed by an ATT&CK dataset.
- The threat-intelligence frontend route was explicitly a placeholder.
- Existing authentication and RBAC permissions support read/manage separation.

## Reused functionality

- Existing SQLAlchemy models and Alembic baseline.
- Existing JWT/RBAC permissions.
- Existing detection event and alert tables.
- Existing realtime worker hook.
- Existing React dashboard shell and API client.

## Existing limitations

- No provider synchronization framework existed.
- Existing threat-intel records did not preserve normalized values, provenance, lifecycle, or observations.
- MITRE knowledge was limited to technique IDs and names.
- No event-to-indicator relationship existed.
- Live provider coverage is intentionally limited to adapters whose HTTP contract is implemented and mocked in tests.
