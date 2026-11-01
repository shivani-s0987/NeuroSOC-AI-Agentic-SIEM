# Frontend API Integration Matrix

| Frontend area | Endpoint | Status |
|---|---|---|
| Authentication | `/auth/login`, `/auth/register`, `/auth/me` | Integrated |
| Overview | `/analytics/summary` | Integrated |
| Events | `/events` | Integrated |
| Alerts | `/alerts`, `/assistant/alerts/{id}/investigate` | Integrated |
| Detection instances | `/detections` | Integrated |
| Detection rules | `/detections/rules`, enable/disable, validate | Backend available; dedicated enterprise editor follow-up |
| Cases | `/cases` | Integrated create/list |
| AI investigations | `/assistant/investigations*` | Integrated |
| Search | `/search` | Integrated substring search |
| Reports | `/reports` | Integrated |
| Settings | `/settings` | Integrated |
| Users | `/admin/users` | Integrated |
| Audit | `/admin/audit-logs` | Integrated |
| Threat intelligence | None for IOC listing | Backend follow-up |
| MITRE dataset | Only aggregate count in `/analytics/summary` | Backend follow-up |
| Alert assignment/status mutation | Not implemented by backend | Backend follow-up |
| Case update/notes UI | Case notes endpoint exists; updates require dedicated UI | Partial |
