# AI Investigation Design

## Components
- Provider abstraction: `backend/app/services/ai_service.py`
- Evidence context and validation: `backend/app/services/investigation_service.py`
- Workflow API: `backend/app/routers/assistant.py`
- Persistent models: `investigations`, `investigation_results`, and `investigation_feedback`
- Frontend: `frontend/src/App.tsx`

## Evidence design
Evidence references use stable identifiers such as `event:123`, `alert:45`, `rule:ssh_bruteforce`, `case:9`, `intel:3`, and `mitre:T1110`.

Context retrieval is bounded by `AI_CONTEXT_MAX_EVENTS` and field length limits. Raw fields are transported as data, metadata secrets are excluded, and the provider receives an explicit allowlist. Every finding and timeline reference is checked against that allowlist.

Absence is represented as unavailable or missing evidence; it is never converted to negative evidence.

## Provider behavior
Configured OpenAI-compatible endpoints receive JSON and are expected to return an object matching the Pydantic investigation schema. Failures are categorized as missing credentials, timeout, rate limit, provider error, unavailable, invalid response, or invalid evidence. Retries are capped.

When no real provider is configured, provider metadata is `fallback` and the user-facing result explicitly states that deterministic database synthesis, not an LLM, produced the response.

## Lifecycle
`PENDING`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, and `REQUIRES_REVIEW`. A failed investigation remains in history and retry creates a new version with a `rerun_of` link rather than overwriting the prior record.
