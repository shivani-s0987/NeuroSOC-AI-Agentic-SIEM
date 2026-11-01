# Detection Engine Design

## Components

- YAML loader and Pydantic validator.
- Rule registry and per-rule isolated execution.
- Normalized event view that preserves ORM fields and metadata.
- Safe condition evaluator without dynamic Python execution.
- Threshold, timeframe, grouping, and distinct-value correlation.
- Detection and alert persistence keyed by a deterministic fingerprint.
- Detection rule and version management APIs.

## Window semantics

Window start is inclusive and window end is inclusive: `lower <= timestamp <= as_of`. Historical processing uses the requested fixed `as_of`; if omitted, execution uses `max(event_timestamp)` rather than wall clock.

## Deduplication and updates

A group fingerprint includes rule ID and sorted group context. Repeated evaluation updates stored event IDs and observation timestamps and does not insert duplicate detections or alerts. Closed alerts are not reopened automatically in this revision; reopening should be explicit or implemented with a separate lifecycle policy.

## Performance

Queries begin at `as_of - timeframe` and are ordered by timestamp. Rules and grouping data are retained in memory per execution only. Production-scale processing should use bounded event batches and database-side windows, added in a later processing phase.
