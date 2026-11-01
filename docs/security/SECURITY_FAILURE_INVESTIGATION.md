# Security Workflow Failure Investigation

## Scope and baseline

- Target branch: `Upgradable-Features`
- Security workflow: `.github/workflows/security.yml`
- Workflow run inspected: `124827577987`
- Working tree before remediation: branch clean except for a generated local `bandit-report.json`
- Local installed Bandit scan: version 1.9.4

## Scanner results

### Bandit

The machine-readable scan identified five findings, all **Low severity / High confidence**. The reported GitHub workflow wording described five high-severity findings, but the available current repository scan does not reproduce a High severity result. This discrepancy is recorded rather than inferred away.

| Rule | File | Line | Count | Cause |
|---|---|---:|---:|---|
| B404 | `backend/app/cli.py` | 8 | 1 | Import of the subprocess module |
| B607 | `backend/app/cli.py` | 97 | 1 | Partial executable name for `pg_dump` |
| B603 | `backend/app/cli.py` | 97 | 1 | Subprocess execution |
| B607 | `backend/app/cli.py` | 154 | 1 | Partial executable name for `pg_restore` |
| B603 | `backend/app/cli.py` | 154 | 1 | Subprocess execution |

The backup and restore commands used fixed argument lists and shell execution was disabled. The executable was nevertheless resolved through `PATH`, and Bandit could not prove that the call was safe. The actual trust boundary is a local administrator CLI; untrusted HTTP input does not reach either subprocess call.

### Python dependencies

`pip-audit -r backend/requirements.txt` completed successfully with exit code 0 and no known vulnerabilities.

### Frontend dependencies

`npm audit --audit-level=high` completed successfully with exit code 0 and found zero vulnerabilities.

## Remediation

1. Resolve `pg_dump` and `pg_restore` with `shutil.which()` and pass the resulting absolute executable path.
2. Retain fixed argument lists, no shell execution, and captured output.
3. Add a narrow Bandit suppression for `B404` because PostgreSQL CLI backup and restore require the subprocess module.
4. Add narrow `B603` suppressions at the two allowlisted, fixed-argument subprocess calls.
5. Add an executable-resolution regression test for PostgreSQL backup.
6. Preserve full JSON and human-readable Bandit output in CI and upload the JSON report as an artifact.
