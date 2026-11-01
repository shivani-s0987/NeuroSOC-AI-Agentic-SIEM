# Feature Traceability Matrix

| Feature | Original PR | Backend | Frontend | Tests | Runtime verification | Status |
|---|---|---|---|---|---|---|
| Health and API startup | PR 1 | `app/main.py`, `app/database.py` | Dashboard shell | `test_api.py` | Uvicorn and `/health` verified | Verified |
| Event ingestion | PR 1 | `routers/events.py`, `services/ingest_service.py` | Events explorer | `test_api.py` | API create-event test passed | Partial |
| CLI | PR 1 | `app/cli.py` | n/a | `test_cli.py` | Version test passed | Verified |
| Registration/login | PR 2 | `routers/auth.py`, `security.py` | Login/dashboard flow | `test_api.py` | Registration and login test passed | Partial |
| Detection rules | PR 3 | `services/detection_service.py`, `rules/sample.yml` | Detection rules page | No dedicated test | Source inspection only | Unverified |
| AI investigations | PR 4 | `routers/assistant.py`, `services/ai_service.py` | Investigation page | No dedicated test | Not executed | Unverified |
| Dashboard navigation | PR 5 | Analytics APIs | React pages | `App.test.tsx` | Test/build passed | Partial |
| Real-time processing | PR 6 | Not fully represented in the test suite | Frontend integration | No dedicated test | Not executed | Unverified |
| Threat intelligence | PR 7 | `services/threat_intel_service.py` | Threat intelligence and MITRE pages | No dedicated test | Not executed | Unverified |
| Cases/reports | PR 7-8 | `routers/cases.py`, `routers/reports.py`, `services/report_service.py` | Case/report pages | No dedicated test | Not executed | Unverified |
| Docker/CI | PR 8 | Dockerfile and workflow | Frontend workflow | CI commands | Docker build not executed | Partial |
