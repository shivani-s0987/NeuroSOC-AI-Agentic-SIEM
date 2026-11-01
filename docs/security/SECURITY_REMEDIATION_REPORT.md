# Security Remediation Report

## Original workflow failure

- Workflow run: `124827577987`
- Job: `dependencies`
- Workflow file: `.github/workflows/security.yml`
- Commands: `pip-audit -r backend/requirements.txt`, `bandit -q -r backend/app`, and `npm audit --audit-level=high`

## Finding disposition

The current local scan contains five findings, all in the PostgreSQL CLI backup and restore implementation.

| Finding | Status | Remediation |
|---|---|---|
| B404 subprocess import, `backend/app/cli.py:8` | FIXED AND VERIFIED | Documented narrow suppression for the required process module |
| B607 `pg_dump` partial path, `backend/app/cli.py:97` | FIXED AND VERIFIED | Resolve through `shutil.which()` and execute absolute path |
| B603 `pg_dump` subprocess call, `backend/app/cli.py:97` | FIXED AND VERIFIED | Fixed argument vector, shell disabled, narrow call-site suppression |
| B607 `pg_restore` partial path, `backend/app/cli.py:154` | FIXED AND VERIFIED | Resolve through `shutil.which()` and execute absolute path |
| B603 `pg_restore` subprocess call, `backend/app/cli.py:154` | FIXED AND VERIFIED | Fixed argument vector, shell disabled, narrow call-site suppression |

The workflow report described five High-severity findings. Local Bandit 1.9.4 reproduces the five as Low severity, so the original severity mismatch is documented rather than claimed to be independently resolved from unavailable run logs.

## Dependency findings

- Python: no vulnerabilities found; no dependency changes were required.
- Frontend: no high-severity or other vulnerabilities found; no dependency changes were required.
- No ignore file, audit threshold change, scanner skip, or `continue-on-error` was added.

## Security workflow

The security workflow now:

- installs Python and Node.js explicitly;
- runs Python and frontend dependency installation;
- runs pip-audit and npm audit as separate blocking steps;
- emits human-readable and JSON Bandit results;
- uploads the JSON Bandit report on success and failure;
- remains non-permissive when a scanner exits unsuccessfully.

## Regression coverage

`backend/tests/test_cli.py` now verifies that PostgreSQL backup resolves and invokes the absolute `pg_dump` executable using the configured database URL and fixed arguments.

## Validation

Commands:

```text
bandit -q -r backend/app                         -> pass
bandit -r backend/app -f json -o bandit-report.json -> pass
pip-audit -r backend/requirements.txt            -> 0 vulnerabilities
npm audit --audit-level=high                     -> 0 vulnerabilities
```

Backend validation from the repository root:

```text
pytest -q backend/tests                          -> 45 passed
pytest -q backend/tests/test_cli.py              -> 2 passed
ruff check backend/app backend/tests             -> passed
ruff format --check backend/app backend/tests    -> 56 files formatted
python -m compileall -q backend/app              -> passed
fresh SQLite Alembic upgrade                      -> head c6d8a2f4e103
```

Frontend validation:

```text
npm test -- --run                                -> 2 passed
npm run build                                    -> passed
```

## Remaining risks

- PostgreSQL backup and restore remain privileged local CLI operations and must be run with a trusted administrator environment.
- Database URLs are passed as process arguments and can be visible to local process observers if they contain credentials. Operator environments should provide credentials through PostgreSQL-supported environment/PG service configuration where possible.
- Live GitHub run logs were not available locally, so the workflow-reported High count could not be compared byte-for-byte.
