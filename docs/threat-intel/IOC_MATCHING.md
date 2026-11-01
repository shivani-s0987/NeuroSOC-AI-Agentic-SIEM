# IOC Matching

The realtime worker extracts addresses from structured IP fields and URLs, domains and hashes from event text. Arbitrary substring matching is not used; candidates are normalized and looked up against active, non-expired, non-revoked indicators.

Matches record the event, indicator, matched field/value, match type, confidence, severity and source provenance. The uniqueness constraint suppresses retries. An IOC match does not modify detection severity.
