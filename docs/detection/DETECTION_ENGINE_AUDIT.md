# Detection Engine Audit

## Existing architecture

The baseline used `detection_service.py` with one hardcoded failed-auth keyword and one fixed detection created after the first match. Rules were inserted on each execution, timestamps came from event handling, and alerts had no stable correlation fingerprint. There was no rule parser, operator evaluator, replayable threshold window, or rule history.

## Confirmed limitations

- Keyword matching could not express grouping, thresholds, distinct users, or safe operators.
- Failed rule loading could stop all subsequent detection behavior implicitly.
- Detection events were deduplicated by the description substring only in the old implementation.
- Rule loading always inserted duplicate `Rule` rows or depended on unique constraints.
- Alert generation was not tied to the rule match group.
- Detection API exposed rules without full permission enforcement.
- Historical timestamps were processed without a bounded query and fixed-time evaluation.
- Existing event normalization preserved only selected model columns.

## PR 3 solution

The implementation adds a custom YAML rule model, safe operator evaluator, normalized event view, bounded time-window correlation, stable fingerprinting, alert/detection provenance, rule registry loading, management API, and an initial 11-rule library.

This format is custom Sigma-inspired and is not claimed Sigma-compatible.
