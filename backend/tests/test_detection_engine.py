from datetime import datetime, timedelta, timezone

from app.detection_engine import (
    correlate,
    DETECTION_RULE_DIRECTORY,
    load_builtin_rules,
    normalize_event,
    operator_matches,
    parse_duration,
    selection_matches,
    parse_rule_yaml,
)

BASE = datetime(2026, 10, 31, 12, 0, tzinfo=timezone.utc)


def test_rule_content_parsing(tmp_path):
    valid = (
        "id: valid\nname: Valid\ndescription: Valid\nseverity: medium\n"
        "enabled: true\nversion: 1\ncategory: test\ndetection:\n  selection:\n"
        "    event_type: test\n  timeframe: 5m\n  condition: selection\n"
        "response:\n  recommended_action: Review\nmitre:\n  tactics: []\n  techniques: []\n"
        "correlation:\n  group_by: []\n  deduplication_window: 5m\n"
    )
    assert parse_rule_yaml(valid).id == "valid"
    try:
        parse_rule_yaml("[]")
        raise AssertionError("non-mapping YAML was accepted")
    except ValueError:
        pass


def test_condition_operators():
    assert operator_matches("failed login", {"operator": "contains", "value": "failed"})
    assert operator_matches("PowerShell.EXE", {"operator": "ends_with", "value": "powershell.exe"})
    assert operator_matches(443, {"operator": "greater_than", "value": 80})
    assert operator_matches("unknown_user", {"operator": "not_in", "value": ["valid"]})
    assert operator_matches("fallback", {"operator": "exists", "value": True})
    assert not operator_matches(None, {"operator": "exists", "value": True})


def test_selection_missing_null_and_regex():
    assert selection_matches(
        normalize_event({"event_type": "authentication_failure", "username": None}),
        {"event_type": "authentication_failure"},
    )
    assert not selection_matches({}, {"username": {"operator": "exists", "value": True}})
    assert operator_matches("abc-123", {"operator": "regex", "value": r"^abc-\d+$"})


def test_ssh_rule_reaches_threshold_on_event_boundary():
    rule = load_builtin_rules()["ssh_bruteforce"]
    events = []
    for index in range(10):
        timestamp = BASE - timedelta(minutes=5) + timedelta(seconds=index)
        events.append(
            {
                "id": index + 1,
                "timestamp": timestamp,
                "event_type": "authentication_failure",
                "source": "ssh",
                "source_ip": "198.51.100.10",
            }
        )
    matches = correlate(rule, events, as_of=BASE)
    assert len(matches) == 1
    assert matches[0].context["source_ip"] == "198.51.100.10"
    assert len(matches[0].event_ids) == 10


def test_threshold_grouping_and_out_of_window_events():
    rule = load_builtin_rules()["ssh_bruteforce"]
    events = [
        {
            "id": 1,
            "timestamp": BASE - timedelta(minutes=6),
            "event_type": "authentication_failure",
            "source": "ssh",
            "source_ip": "198.51.100.10",
        },
        {
            "id": 2,
            "timestamp": BASE,
            "event_type": "authentication_failure",
            "source": "ssh",
            "source_ip": "198.51.100.11",
        },
    ]
    assert correlate(rule, events, as_of=BASE) == []


def test_password_spraying_counts_distinct_users():
    rule = load_builtin_rules()["password_spraying"]
    events = [
        {
            "id": index + 1,
            "timestamp": BASE,
            "event_type": "authentication_failure",
            "source_ip": "203.0.113.4",
            "username": f"user-{index}",
        }
        for index in range(5)
    ]
    matches = correlate(rule, events, as_of=BASE)
    assert len(matches) == 1


def test_port_scan_counts_distinct_ports():
    rule = load_builtin_rules()["port_scan"]
    events = [
        {
            "id": index + 1,
            "timestamp": BASE,
            "event_type": "connection_attempt",
            "source_ip": "203.0.113.8",
            "destination_port": port,
        }
        for index, port in enumerate([22, 80, 443, 8080, 8443])
    ]
    assert len(correlate(rule, events, as_of=BASE)) == 1


def test_suspicious_powershell_requires_combined_indicators():
    rule = load_builtin_rules()["suspicious_powershell"]
    safe = {
        "id": 1,
        "timestamp": BASE,
        "process_name": "powershell.exe",
        "command_line": "Get-Process",
        "host": "host-1",
        "username": "analyst",
    }
    suspicious = {**safe, "command_line": "powershell.exe -enc SQBFAFgA"}
    assert correlate(rule, [safe], as_of=BASE) == []
    assert len(correlate(rule, [suspicious], as_of=BASE)) == 1


def test_rule_library_has_ten_unique_valid_rules():
    paths = sorted(DETECTION_RULE_DIRECTORY.glob("*.yml"))
    registry = load_builtin_rules()
    ids = list(registry)
    assert len(paths) >= 10
    assert len(ids) == len(set(ids))


def test_duration_parser():
    assert parse_duration("5m") == timedelta(minutes=5)
    try:
        parse_duration("1x")
        assert False
    except ValueError:
        pass
