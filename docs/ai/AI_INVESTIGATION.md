# Evidence-Grounded AI Investigation

## Start an investigation
`POST /api/v1/assistant/alerts/{alert_id}/investigate`

Optional JSON:
```json
{"alert_id": 1, "case_id": null, "force_rerun": false}
```

Retrieve or create repeat investigations through:
- `GET /api/v1/assistant/investigations`
- `GET /api/v1/assistant/investigations/{id}`
- `POST /api/v1/assistant/investigations/{id}/retry`
- `GET /api/v1/assistant/alerts/{id}/investigation`
- `POST /api/v1/assistant/investigations/{id}/feedback`

Every endpoint requires authentication and alert read permission. Investigation history is scoped to the initiating user.

## Structured result
The result includes an executive summary, alert assessment, observed facts versus hypotheses, bounded timeline, risk assessment, investigation steps, approval-required actions, limitations, and provider metadata.

## Analyst meaning of confidence
Confidence is a model or fallback quality estimate, not proof of compromise. Findings marked as observed facts must still be supported by valid evidence references. Hypotheses must not be presented as confirmed attacks.
