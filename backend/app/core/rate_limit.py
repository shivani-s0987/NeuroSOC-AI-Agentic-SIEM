import time
from collections import defaultdict, deque

from fastapi import HTTPException

_buckets: dict[str, deque[float]] = defaultdict(deque)


def check_rate_limit(key: str, limit: int) -> None:
    now = time.monotonic()
    bucket = _buckets[key]
    cutoff = now - 60
    while bucket and bucket[0] <= cutoff:
        bucket.popleft()
    if len(bucket) >= limit:
        raise HTTPException(status_code=429, detail="Too many attempts; retry later")
    bucket.append(now)
