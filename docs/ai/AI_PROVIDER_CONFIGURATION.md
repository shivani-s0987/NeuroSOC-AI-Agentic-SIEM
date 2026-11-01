# AI Provider Configuration

## Supported providers
- `AI_PROVIDER=fallback`: deterministic database summary; no external request.
- `AI_PROVIDER=openai`: OpenAI-compatible `/chat/completions` API.
- `AI_PROVIDER=external`: configurable compatible endpoint using the same HTTP contract.

The value `mock` remains accepted for compatibility and uses the deterministic fallback.

## Environment variables
- `AI_ENABLED=true|false`
- `AI_API_KEY`: provider secret, never sent to the frontend.
- `AI_BASE_URL`: compatible API origin, for example `https://api.openai.com/v1`.
- `AI_MODEL`: configured model name.
- `AI_TIMEOUT_SECONDS`
- `AI_RETRIES`
- `AI_MAX_TOKENS`
- `AI_TEMPERATURE`
- `AI_CONTEXT_MAX_EVENTS`
- `AI_MAX_FIELD_CHARS`

For a real provider, set a provider and credential, for example:

```env
AI_PROVIDER=openai
AI_API_KEY=your-provider-key
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
```

Do not commit real keys. Provider outages produce safe categorized failures and do not fabricate provider output.
