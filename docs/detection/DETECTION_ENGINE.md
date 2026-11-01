# Detection Engine

Run detections from `POST /detections/run` with `DETECTIONS_MANAGE`. View rules with `GET /detections/rules`. Validate JSON rule definitions with `POST /detections/rules/validate`; create rules with `POST /detections/rules`; simulate with `POST /detections/rules/{rule_id}/test`.

## Commands and files

Rules are YAML files under `backend/app/detection_rules`. Invalid files are logged and isolated from valid rules. The engine must not execute Python expressions or arbitrary code.

## Operators

`equals`, `not_equals`, `contains`, `not_contains`, `starts_with`, `ends_with`, `in`, `not_in`, `greater_than`, `greater_than_or_equal`, `less_than`, `less_than_or_equal`, `exists`, `not_exists`, and bounded `regex`.

String operators are case-insensitive. Missing fields never match positive field predicates. Regex patterns are limited to 512 characters and compiled without a dynamic execution path.

## Testing

```bash
pytest backend/tests/test_detection_engine.py -v
pytest backend/tests -v
ruff check backend
alembic upgrade head
```
