# Role-Based Access Control

## Roles

- `ADMIN`: users, audit logs, settings, events, alerts, cases, detections, and reports.
- `SOC_ANALYST`: events, alerts, cases, detections/read, reports, and threat investigations; no user or settings administration.
- `SECURITY_VIEWER`: read-only access to permitted events, alerts, cases, detections, and reports.

Role values received through public registration are ignored. Only administrators may change roles or account status through `/api/v1/admin` routes. An administrator cannot change their own role, deactivate their own account, or deactivate the final active administrator.

Cases currently have no persisted owner identifier, so the API establishes analyst/admin management and viewer read access. The first user assigned to a case is authorization metadata, not an ownership proof until an owner field is added.

Backend permission dependencies remain authoritative; frontend navigation is only convenience.
