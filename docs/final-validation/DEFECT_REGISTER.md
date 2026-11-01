# Defect Register

## NS-001 — SQLite URL generated without a database scheme

- **Severity:** High
- **Affected module:** `backend/app/database.py`
- **Root cause:** Absolute paths from `DATABASE_PATH` were passed directly to SQLAlchemy.
- **Fix:** Default SQLite URLs are converted to valid `sqlite:///...` URLs; PostgreSQL URLs receive no SQLite-only connection arguments.
- **Regression test:** Backend API and CLI test collection.
- **Verification:** 4 backend tests passed in Python 3.12.

## NS-002 — Runtime dependency versions contained known vulnerabilities

- **Severity:** Critical
- **Affected module:** Python dependency manifests and CI
- **Root cause:** Five vulnerable packages were pinned to old versions, while pytest was incorrectly coupled with runtime dependencies.
- **Fix:** Upgraded FastAPI and Starlette together and moved test dependencies to `requirements-dev.txt`.
- **Regression test:** Clean environment install, `pip check`, backend suite and both `pip-audit` manifests.
- **Verification:** No known vulnerabilities and 4 backend tests passed.

## NS-003 — Frontend canvas rendering is unavailable in jsdom

- **Severity:** Low
- **Affected module:** Frontend test environment
- **Root cause:** Chart.js calls `HTMLCanvasElement.getContext`, unsupported by jsdom.
- **Fix:** Added a narrow canvas context stub in `setupTests.ts`.
- **Regression test:** Frontend Vitest suite.
- **Verification:** 1 frontend test passed.
