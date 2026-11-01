# Provider Integrations

## URLhaus

NeuroSOC implements a read-only adapter for the Abuse.ch URLhaus API documented at:

`https://urlhaus-api.abuse.ch/api/`

URLhaus host and URL lookups use trusted HTTPS API endpoints with a bounded HTTP timeout. API credentials are not required by the implemented lookup contract.

Live connectivity was not required for automated tests. Tests mock all HTTP responses. Provider responses are normalized without inventing scores.

Configured provider settings:

```text
URLHAUS_ENABLED=true
URLHAUS_API_URL=https://urlhaus-api.abuse.ch/v1/
```
