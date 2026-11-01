# WebSocket Streaming

Connect to `/realtime/ws`. After the socket opens, send:

```json
{"type":"auth","token":"<access-token>"}
```

The token is not placed in the URL. The server validates it, loads the active database user, and requires `events:read`. Supported client frames are limited to `ping`. No client-supplied identity is accepted.

Notifications are also available through authenticated `GET /realtime/notifications?after=<UTC timestamp>`. The React client reconciles missed notifications on connect and at a bounded interval. Redis pub/sub broadcasts across API instances are not currently implemented; SQL reconciliation remains the supported multi-instance correctness mechanism.
