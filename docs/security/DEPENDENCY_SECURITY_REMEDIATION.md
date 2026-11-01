# Dependency Security Remediation

## Scope

The original `pip-audit -r backend/requirements.txt` result reported 56 vulnerability entries in five packages. The entries include duplicate advisory records for the same package versions.

## Original versions

| Package | Original | Selected |
|---|---:|---:|
| Jinja2 | 3.1.4 | 3.1.6 |
| PyJWT | 2.9.0 | 2.15.1 |
| pytest | 8.3.4 | 9.0.3 |
| python-multipart | 0.0.21 | 0.0.31 |
| Starlette | 0.38.6 | 1.3.1 |
| FastAPI | 0.115.0 | 0.162.0 |

## Advisory handling

The versions were selected from the fixes reported by `pip-audit` and checked against package availability and compatibility:

- Jinja2 3.1.6 resolves the Jinja2 fixes through 3.1.6.
- PyJWT 2.15.1 covers all fixes reported through 2.15.0.
- pytest 9.0.3 matches the first fixed release reported by the advisory database.
- python-multipart 0.0.31 covers the fixes reported through 0.0.31.
- Starlette 1.3.1 covers the fixes reported through 1.3.1 and requires FastAPI 0.162.0 for the compatible supported relationship.

The pytest development dependency was moved out of runtime requirements. The pytest async plugin was updated for pytest 9 compatibility.

## Reproducibility

Python 3.12 is the supported CI/runtime line. Runtime dependencies are pinned in `backend/requirements.txt`; the resolved environment is committed in `backend/requirements.lock`, and `backend/requirements-dev.txt` installs the development test dependencies.

The Dockerfile and CI install the same declared versions. CI runs `pip check` and audits both runtime and development requirements.

## Commands executed

```bash
python3.12 -m venv /tmp/neurosoc-audit
/tmp/neurosoc-audit/bin/python -m pip install -r backend/requirements.txt \
  -r backend/requirements-dev.txt pip-audit
/tmp/neurosoc-audit/bin/python -m pip check
/tmp/neurosoc-audit/bin/pip-audit -r backend/requirements.txt
/tmp/neurosoc-audit/bin/pip-audit -r backend/requirements-dev.txt
/tmp/neurosoc-audit/bin/python -m pytest backend/tests -q
```

## Result

Both runtime and development audits returned **No known vulnerabilities found**. The clean-environment backend suite passed 4 tests. Dependency resolution reported no broken requirements.

## Compatibility

FastAPI and Starlette were upgraded together. Starlette 1.3.1 and FastAPI 0.162.0 resolved successfully, and the application tests passed.
