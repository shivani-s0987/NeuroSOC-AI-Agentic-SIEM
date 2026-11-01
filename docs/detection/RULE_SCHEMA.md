# Rule Schema

Required fields: `id`, `name`, `description`, `enabled`, `severity`, `category`, `logsource`, `detection`, `mitre`, `response`, and `version`.

The `detection.selection` value is a non-empty object. It supports direct field equality, operator objects, and nested `and`/`or` arrays. Detection must name `selection` as its condition in this implementation.

Threshold rules require `timeframe` and a positive integer `count`. `distinct_by` optionally counts distinct values. `group_by` supports documented event normalization fields only.

Durations use a positive integer and unit: `s`, `m`, `h`, or `d`. Window boundaries are inclusive.

MITRE techniques and tactics are mapping metadata. They are not evidence of a confirmed intrusion.
