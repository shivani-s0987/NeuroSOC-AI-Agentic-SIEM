# AI Security and Privacy Controls

- Provider credentials are read only by the backend and never serialized through API responses.
- External provider calls are disabled by setting `AI_PROVIDER=fallback` or `AI_ENABLED=false`.
- Authentication and alert-read RBAC are required before context retrieval.
- Event content, command lines, and messages have field-size limits and are serialized as untrusted data.
- Passwords, tokens, secrets, authorization values, cookies, and API keys are removed recursively from event metadata sent to providers.
- Provider requests have timeout and retry caps.
- Raw provider exceptions are not exposed publicly.
- Investigation feedback is stored separately and must not be treated as verified training data.
- Recommended containment actions require analyst approval; generated commands are never executed.
- Retention requires deployment-specific policy configuration. This application does not claim regulatory compliance certification.

When configured with an external provider, alert summaries, bounded event data, usernames, hosts, IP addresses, rule descriptions, case summaries, and available threat-intelligence records may be sent to the provider. Do not enable external providers for data classifications that prohibit that transfer.
