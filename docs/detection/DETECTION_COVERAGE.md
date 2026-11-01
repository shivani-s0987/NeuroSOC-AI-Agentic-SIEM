# Detection Coverage

| Rule | Coverage | Evidence limit |
|---|---|---|
| ssh_bruteforce | Structured repeated SSH failures | Requires 10 failures in 5 minutes from grouped source IP |
| password_spraying | Distinct users from one failure source | Requires configured distinct-user threshold |
| privilege_escalation | Structured privilege changes and sudo action | Does not infer intent from free text alone |
| anomalous_login | Explicit provider/context anomaly marker | Cannot infer impossible travel without reliable geo/timestamps |
| port_scan | Multiple distinct destination ports | Requires telemetry-provided port values |
| suspicious_powershell | PowerShell plus encoded/hidden/Invoke indicator | May require endpoint process telemetry tuning |
| account_enumeration | Unknown-user/failed-user patterns | Requires username/result granularity |
| repeated_access_denied | Authorization failures | Requires protected-resource result telemetry |
| auth_after_privilege_change | Privileged authentication marker | Correlation quality depends on telemetry timestamps/username |
| suspicious_file_indicator | Explicit suspicious indicator | Does not perform malware scanning |

MITRE technique identifiers in rules are based on broad ATT&CK mappings and must not be interpreted as incident proof. Version mapping source should be reviewed before operational use.
