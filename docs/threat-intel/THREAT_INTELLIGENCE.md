# Threat Intelligence

NeuroSOC stores canonical IOC records and preserves original submitted values. Supported types are IPv4, IPv6, domain, URL, MD5, SHA1, and SHA256.

Indicators have confidence, severity, lifecycle timestamps, provenance, tags, and provider observations. Revoked or expired indicators are retained for evidence but excluded from event matching.

## APIs

- `GET /threat-intelligence/indicators`
- `POST /threat-intelligence/indicators`
- `POST /threat-intelligence/indicators/{id}/revoke`
- `POST /threat-intelligence/indicators/import`
- `GET /threat-intelligence/indicators/{id}`
- `GET /threat-intelligence/matches/event/{event_id}`
- `GET /threat-intelligence/providers`
- `POST /threat-intelligence/providers/{provider}/lookup`

Write operations require `detections:manage`. Viewing requires `detections:read`. Provider lookups are permission checked and should be rate limited by deployment policy.
