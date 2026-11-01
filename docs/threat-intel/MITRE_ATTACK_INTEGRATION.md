# MITRE ATT&CK Integration

MITRE ATT&CK techniques are stored with technique ID, name, description, platforms, data sources, tactics, parent relationships, detection guidance, STIX ID, external URL and revoked/deprecated state.

The implementation exposes technique search through:

`GET /mitre/techniques`

Detection rules already carry ATT&CK technique identifiers. This release validates identifiers against imported knowledge and exposes imported coverage; it does not claim full Enterprise ATT&CK coverage. Official dataset import should be performed from a versioned MITRE ATT&CK STIX release and recorded in deployment operations.
