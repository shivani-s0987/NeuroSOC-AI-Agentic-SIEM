# CodeQL Remediation Report

## Status

GitHub verification is pending: local validation passed, but this report does not claim resolution of hosted CodeQL alerts until GitHub runs the workflow on the updated commit.

## Findings

### Uncontrolled path expression

- Severity: High
- Original location: `backend/app/detection_engine.py:141`
- Provenance: pre-existing code surfaced by the larger pull request diff.
- Root cause: `load_yaml()` opened a caller-provided path directly.
- Remediation: paths are decoded for traversal inspection, must be relative, must not contain backslash or `..`, are resolved beneath the detection-rule directory, and must remain beneath that directory after canonicalization. Missing files, absolute paths, and symlink escapes are rejected.
- Caller impact: the rules API and detection service now load rule filenames rather than arbitrary API paths.

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
- Detection rule files must be regular `.yml` files under the application-controlled directory.

## Validation pending

Run complete local checks documented in the final response. Hosted CodeQL must be rerun for `Upgradable-Features` on the resulting commit.
