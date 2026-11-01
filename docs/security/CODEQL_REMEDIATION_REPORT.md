# CodeQL Remediation Report

## Status

GitHub verification is pending: local validation passed, but this report does not claim resolution of hosted CodeQL alerts until GitHub runs the workflow on the updated commit.

## Findings

### Uncontrolled path expression

- Severity: High
- Original location: `backend/app/detection_engine.py:141`
- Provenance: pre-existing code surfaced by the larger pull request diff.
- Root cause: `load_yaml()` accepted caller-controlled filenames and converted them into filesystem paths. Canonicalization patched the symptom but preserved untrusted data-flow into path expressions and CodeQL continued to model it.
- Remediation: the generic path-based loader was removed. YAML is parsed only with `parse_rule_yaml(content)`. Built-in files are enumerated exclusively from the fixed application directory, parsed, keyed by validated ID, and exposed through an immutable mapping. Custom rules and execution content are database-backed.
- Caller impact: rule creation writes no files, dry-run queries the database, and detection execution parses database content. Rule IDs are never joined into filesystem paths.

## Architecture

- `backend/app/detection_engine.py` contains the content-only YAML parser and trusted built-in registry.
- Built-in rule synchronization occurs through database records only when an ID is absent, so custom rules are not overwritten.
- Custom rule creation validates YAML, stores `Rule.content`, and adds a `RuleVersion` in the same transaction.
- The dry-run endpoint parameterizes its ORM lookup, rejects malformed or mismatched stored content, and never performs filesystem access.
- Detection execution enumerates database rules and isolates malformed individual rules so one invalid record cannot abort the complete job.
- Request-derived rule IDs have no role in filesystem operations.

### Weak password hashing in production

- Severity: High
- Original location: `backend/app/security.py:33`
- Provenance: pre-existing compatibility branch.
- Root cause: verification accepted 64-character SHA-256 password hashes.
- Remediation: the SHA-256 password verification branch was removed. New and reset passwords use Argon2id, and 64-character legacy values are recognized as requiring rehash but cannot authenticate. Existing users with legacy hashes must use the password-reset flow.

### Weak password hashing in tests

- Severity: High
- Original location: `backend/tests/test_regression.py:38`
- Provenance: pre-existing regression test.
- Root cause: the test constructed a real-looking SHA-256 password hash.
- Remediation: ordinary password tests now use the application Argon2id utility. Legacy behavior is represented only by a non-authenticating sentinel fixture and its forced-reset classification.

## Files changed

- `backend/app/detection_engine.py`: canonical path validation.
- `backend/app/services/detection_service.py`: namespaced rule loading.
- `backend/app/security.py`: removed SHA-256 password verification.
- `backend/tests/test_detection_engine.py`: filesystem boundary and path regression tests.
- `backend/tests/test_auth_rbac.py`: legacy hash and refresh-token tests.
- `backend/tests/test_regression.py`: Argon2id password tests.

## Security behavior

- Password storage and verification remain Argon2id through `argon2.PasswordHasher`.
- Login upgrade behavior for supported Argon2 parameters remains intact.
- Legacy SHA-256 password hashes cannot authenticate and cannot create new Argon2 hashes without the legitimate password reset flow.
- Detection rule files are trusted read-only built-in assets under the application-controlled directory. Custom YAML never creates a file.

## Validation pending

- Local checks covering the new architecture pass; hosted CodeQL must be rerun for `Upgradable-Features` on the resulting commit.
