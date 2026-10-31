# Alert Correlation

Each match receives a deterministic fingerprint composed of rule ID and sorted group context. Detection and alert queries use this fingerprint to avoid duplicate records. Existing open detections/alerts are enriched with previously unseen event IDs and the newest observation timestamp.

There is no automatic reopening of closed alerts in this PR. This prevents a stale alert lifecycle from silently changing ownership or status. A future lifecycle policy must explicitly reopen closed alerts with an audit record.

Transactions persist detections and their correlated alert together. Rule execution catches invalid rules independently so valid rules can continue processing.
