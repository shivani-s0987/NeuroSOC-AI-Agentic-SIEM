# Evidence and Hallucination Controls

1. Evidence is collected from database alert, event, rule, case, threat-intelligence, and MITRE records.
2. Telemetry is serialized separately and bounded.
3. Only allowlisted evidence references may appear in findings and timeline entries.
4. Provider output is validated with Pydantic before persistence.
5. Unknown or fabricated references reject the provider result.
6. Facts and hypotheses are represented separately.
7. IP reputation, geography, compromise status, and attacker attribution are not inferred by the application.
8. Deterministic fallback metadata is exposed explicitly.

Security logs and command lines are attacker-controlled input. They cannot be trusted as instructions. The prompt directs the model to ignore embedded commands and never execute model output. Residual prompt-injection, model-misuse, and provider-side handling risks remain, especially when external providers are used.
