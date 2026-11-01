# Reliability and Recovery

Delivery is at least once, with idempotent processing:

- Database commit precedes acknowledgement and queue publish.
- Processing jobs survive broker outages.
- Worker deliveries can be repeated.
- Event, detection, and alert fingerprints prevent duplicate outcomes.
- Notifications have stable unique identifiers.
- Notification history supports cursor-based replay through the API.

Redis pub/sub is not used as replay storage. Messages published while a client was disconnected are recoverable only from notification history.
