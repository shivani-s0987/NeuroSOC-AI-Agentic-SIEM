# IOC Schema

Each indicator retains:

- `value` / original submitted value.
- canonical normalized value and IOC type.
- confidence from 0 to 100.
- separate threat severity from detection severity.
- source and provenance.
- first seen, last seen, valid-from and expiration timestamps.
- active, revoked and expired lifecycle state.
- tags, description and external reference.

Canonical uniqueness is enforced by `(normalized_value, type)` semantics at the application and database normalized-value constraint. Provider observations and event matches preserve historical provenance.
