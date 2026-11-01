from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

OPERATORS = {
    "equals",
    "not_equals",
    "contains",
    "not_contains",
    "starts_with",
    "ends_with",
    "in",
    "not_in",
    "greater_than",
    "greater_than_or_equal",
    "less_than",
    "less_than_or_equal",
    "exists",
    "not_exists",
    "regex",
}
SEVERITIES = {"info", "low", "medium", "high", "critical"}
GROUP_FIELDS = {
    "source_ip",
    "src_ip",
    "username",
    "user",
    "host",
    "hostname",
    "event_type",
    "source",
}


def parse_duration(value: str) -> timedelta:
    match = re.fullmatch(r"(\d+)([smhd])", value.strip().lower())
    if not match:
        raise ValueError("timeframe must match a number followed by s, m, h, or d")
    amount, unit = int(match.group(1)), match.group(2)
    if amount < 1:
        raise ValueError("timeframe must be positive")
    return timedelta(
        seconds=amount
        if unit == "s"
        else amount * 60
        if unit == "m"
        else amount * 3600
        if unit == "h"
        else amount * 86400
    )


class Mitre(BaseModel):
    tactics: list[str] = Field(default_factory=list)
    techniques: list[str] = Field(default_factory=list)


class Response(BaseModel):
    create_alert: bool = True
    recommended_action: str = Field(min_length=1, max_length=2000)


class Rule(BaseModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]{2,79}$")
    name: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=4000)
    enabled: bool = True
    severity: str
    category: str = Field(min_length=2, max_length=80)
    tags: list[str] = Field(default_factory=list)
    logsource: dict[str, str] = Field(default_factory=dict)
    detection: dict[str, Any]
    mitre: Mitre = Field(default_factory=Mitre)
    response: Response
    version: int = Field(default=1, ge=1)

    @field_validator("severity")
    @classmethod
    def valid_severity(cls, value: str) -> str:
        if value.lower() not in SEVERITIES:
            raise ValueError("invalid severity")
        return value.lower()

    @model_validator(mode="after")
    def validate_detection(self) -> "Rule":
        detection = self.detection
        selection = detection.get("selection")
        if not isinstance(selection, dict) or not selection:
            raise ValueError("detection.selection must be a non-empty object")
        if detection.get("condition") != "selection" and not isinstance(
            detection.get("condition"), dict
        ):
            raise ValueError("unsupported detection condition")
        count = detection.get("count")
        timeframe = detection.get("timeframe")
        if count is not None and (
            not isinstance(count, int) or isinstance(count, bool) or count < 1 or count > 1000000
        ):
            raise ValueError("count must be an integer between 1 and 1000000")
        if timeframe is not None:
            parse_duration(timeframe)
        for field in detection.get("group_by", []):
            if field not in GROUP_FIELDS:
                raise ValueError(f"unsupported group_by field: {field}")
        validate_selection(selection)
        return self


def validate_selection(selection: dict[str, Any], depth: int = 0) -> None:
    if depth > 3:
        raise ValueError("selection nesting exceeds three levels")
    for key, condition in selection.items():
        if key in {"and", "or"}:
            if not isinstance(condition, list):
                raise ValueError(f"{key} condition must be a list")
            for child in condition:
                if isinstance(child, dict):
                    validate_selection(child, depth + 1)
        elif isinstance(condition, dict):
            operator = condition.get("operator")
            if operator not in OPERATORS:
                raise ValueError(f"unsupported operator for {key}: {operator}")
            if operator == "regex":
                pattern = condition.get("value")
                if not isinstance(pattern, str) or len(pattern) > 512:
                    raise ValueError("regex pattern must be a string of at most 512 characters")
                try:
                    re.compile(pattern)
                except re.error as exc:
                    raise ValueError(f"invalid regex: {exc}") from exc


def load_yaml(path: Path | str) -> Rule:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("rule must be a YAML mapping")
    return Rule.model_validate(data)


def normalize_event(event: Any) -> dict[str, Any]:
    if isinstance(event, dict):
        source = event
    else:
        source = {
            column: getattr(event, column, None)
            for column in (
                "id",
                "source",
                "event_type",
                "severity",
                "host",
                "user",
                "src_ip",
                "dst_ip",
                "process_name",
                "message",
                "raw",
                "timestamp",
                "payload_metadata",
            )
        }
    metadata = source.get("payload_metadata") or source.get("metadata") or {}
    if isinstance(metadata, dict):
        source.update(metadata)
    normalized = dict(source)
    normalized["source_ip"] = source.get("source_ip") or source.get("src_ip")
    normalized["username"] = source.get("username") or source.get("user")
    normalized["hostname"] = source.get("hostname") or source.get("host")
    normalized["command_line"] = source.get("command_line") or source.get("process_name")
    timestamp = source.get("timestamp")
    if isinstance(timestamp, datetime):
        normalized["timestamp"] = (
            timestamp.replace(tzinfo=timezone.utc)
            if timestamp.tzinfo is None
            else timestamp.astimezone(timezone.utc)
        )
    return normalized


def field_value(event: dict[str, Any], field: str) -> Any:
    return event.get(field)


def operator_matches(actual: Any, condition: dict[str, Any] | Any) -> bool:
    if not isinstance(condition, dict) or "operator" not in condition:
        return actual == condition
    operator = condition["operator"]
    expected = condition.get("value")
    if operator == "exists":
        return actual is not None
    if operator == "not_exists":
        return actual is None
    if actual is None:
        return False
    if operator == "equals":
        return actual == expected
    if operator == "not_equals":
        return actual != expected
    text = str(actual)
    wanted = str(expected)
    if operator == "contains":
        return wanted.lower() in text.lower()
    if operator == "not_contains":
        return wanted.lower() not in text.lower()
    if operator == "starts_with":
        return text.lower().startswith(wanted.lower())
    if operator == "ends_with":
        return text.lower().endswith(wanted.lower())
    if operator == "in":
        return (
            actual in expected
            if isinstance(expected, (list, tuple, set))
            else text.lower() in str(expected).lower()
        )
    if operator == "not_in":
        return (
            actual not in expected
            if isinstance(expected, (list, tuple, set))
            else text.lower() not in str(expected).lower()
        )
    try:
        if operator == "greater_than":
            return float(actual) > float(expected)
        if operator == "greater_than_or_equal":
            return float(actual) >= float(expected)
        if operator == "less_than":
            return float(actual) < float(expected)
        if operator == "less_than_or_equal":
            return float(actual) <= float(expected)
    except (TypeError, ValueError):
        return False
    if operator == "regex":
        return re.search(wanted, text) is not None
    return False


def selection_matches(event: dict[str, Any], selection: dict[str, Any]) -> bool:
    if "and" in selection:
        if not all(
            selection_matches(event, child) if isinstance(child, dict) else False
            for child in selection["and"]
        ):
            return False
        return (
            all(selection_matches(event, child) for child in selection.get("or", []))
            if selection.get("or")
            else True
        )
    if "or" in selection:
        return any(selection_matches(event, child) for child in selection["or"])
    return all(
        operator_matches(field_value(event, field), condition)
        for field, condition in selection.items()
    )


@dataclass(frozen=True)
class MatchGroup:
    fingerprint: str
    rule_id: str
    context: dict[str, str]
    event_ids: tuple[int, ...]
    first_observed: datetime
    last_observed: datetime


def correlate(rule: Rule, events: list[Any], as_of: datetime | None = None) -> list[MatchGroup]:
    normalized = [normalize_event(event) for event in events]
    selection = rule.detection["selection"]
    matching = [event for event in normalized if selection_matches(event, selection)]
    if as_of is None:
        timestamps = [
            event["timestamp"] for event in matching if isinstance(event.get("timestamp"), datetime)
        ]
        as_of = max(timestamps) if timestamps else datetime.now(timezone.utc)
    timeframe = parse_duration(rule.detection["timeframe"])
    lower = as_of - timeframe
    window = [
        event
        for event in matching
        if isinstance(event.get("timestamp"), datetime)
        and lower
        <= (
            event["timestamp"].replace(tzinfo=timezone.utc)
            if event["timestamp"].tzinfo is None
            else event["timestamp"].astimezone(timezone.utc)
        )
        <= as_of
    ]
    groups: dict[tuple[tuple[str, str], ...], list[dict[str, Any]]] = {}
    for event in window:
        context = {
            field: str(event.get(field) or "unknown")
            for field in rule.detection.get("group_by", [])
        }
        key = tuple(sorted(context.items()))
        groups.setdefault(key, []).append(event)
    threshold = int(rule.detection.get("count", 1))
    results: list[MatchGroup] = []
    distinct_field = rule.detection.get("distinct_by")
    for context_items, grouped in groups.items():
        context = dict(context_items)
        sample_count = (
            len({event.get(distinct_field) for event in grouped})
            if distinct_field
            else len(grouped)
        )
        if sample_count < threshold:
            continue
        ids = tuple(sorted({int(event["id"]) for event in grouped if event.get("id") is not None}))
        timestamps = [event["timestamp"] for event in grouped]
        fingerprint = f"{rule.id}:{':'.join(f'{key}={value}' for key, value in context_items)}"
        results.append(
            MatchGroup(fingerprint, rule.id, context, ids, min(timestamps), max(timestamps))
        )
    return sorted(results, key=lambda match: match.fingerprint)
