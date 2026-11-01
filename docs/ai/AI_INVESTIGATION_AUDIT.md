# AI Investigation Audit

## Repository surfaces reviewed
- Backend assistant placeholder: `backend/app/services/ai_service.py`
- Assistant API: `backend/app/routers/assistant.py`
- Data access: `backend/app/models.py`, alerts, events, cases, detections, and threat-intelligence routers/services
- RBAC: `backend/app/core/permissions.py` and `backend/app/security.py`
- Database/migrations: `backend/app/database.py`, `alembic/`
- Configuration: `backend/app/config.py`, `.env.example`
- Frontend: `frontend/src/App.tsx`, `frontend/src/api.ts`
- Tests and CI: `backend/tests/`, `frontend/src/App.test.tsx`, `.github/workflows/ci.yml`

## Findings before PR 4
- The assistant service returned a hardcoded `[Model generated]` string and had no provider integration.
- The legacy `/assistant/explain` endpoint accepted unscoped frontend context and did not retrieve database evidence.
- Alert, event, detection, case, and threat-intelligence data were not connected to assistant output.
- There was no provider response schema, evidence-reference validation, or persisted investigation lifecycle.
- Existing role permissions permitted authorized SOC analysts and viewers to read alerts; investigation creation now requires an alert read permission and is initiated under an authenticated user.
- No credentials were stored in source code, although provider configuration was not implemented.
- Prompts were not separated from telemetry, and logs were not bounded.

## PR 4 additions
- OpenAI-compatible HTTP provider abstraction plus a clearly identified deterministic fallback.
- Alert-scoped context builder using bounded database queries.
- Evidence allowlist validation before and after structured provider output.
- Investigation, immutable result, and separate feedback persistence.
- Start, retrieve, retry, rerun, alert shortcut, feedback, and history APIs.
- Analyst-facing investigation screen backed only by API responses.

## Residual risks
- Prompt injection cannot be eliminated for external models; event content is always serialized as untrusted data.
- Provider availability and strict JSON support depend on the selected compatible endpoint.
- Existing installations require Alembic upgrade to create investigation tables.
