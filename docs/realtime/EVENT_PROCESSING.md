# Event Processing

Accepted payloads are normalized to UTC timestamps, validated by Pydantic, and preserved in `raw` evidence plus metadata. Clients may supply `external_id` or `idempotency_key`; an identical ingestion key returns the previously accepted event without creating another record.

Requests that omit an idempotency key are allowed and represent separate submissions. Producers should supply stable keys for safe retries.

Batch requests are handled independently and return one result per input index. Processing is triggered only after each successful database commit.
