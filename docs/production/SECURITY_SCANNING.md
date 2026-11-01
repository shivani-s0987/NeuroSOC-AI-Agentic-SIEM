# Security Scanning

## Automated checks

The security workflow runs:

- GitHub CodeQL for Python and JavaScript/TypeScript.
- `pip-audit` for Python dependencies.
- Bandit for Python static analysis.
- `npm audit --audit-level=high` for JavaScript dependencies.

## Severity policy

- Critical or high dependency findings block release review.
- High-severity CodeQL findings require triage before merge when introduced by the change.
- Medium and low findings require an owner, due date, and tracking issue when not fixed immediately.
- Suppressions must contain an owner, rationale, expiry/review date, and affected rule or package.

Container scanning, Trivy/Hadolint, and deployment-secret scanning are recommended release controls for the platform that hosts this repository. No single scan proves the application secure; findings must be assessed in context.
