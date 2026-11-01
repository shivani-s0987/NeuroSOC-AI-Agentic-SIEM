from __future__ import annotations

import logging
from typing import Any

import httpx


class URLhausProvider:
    """Read-only adapter for the documented Abuse.ch URLhaus lookup API."""

    name = "urlhaus"
    base_url = "https://urlhaus-api.abuse.ch/v1"

    def __init__(self, client: httpx.Client | None = None, base_url: str | None = None) -> None:
        self.client = client
        self.base_url = base_url or self.base_url

    def lookup(self, value: str, ioc_type: str) -> dict[str, Any]:
        endpoint = "host" if ioc_type in {"ipv4", "ipv6", "domain"} else "url"
        field = "host" if endpoint == "host" else "url"
        client = self.client or httpx.Client(timeout=10.0)
        try:
            response = client.post(f"{self.base_url}/{endpoint}/", data={field: value})
            response.raise_for_status()
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("URLhaus returned a non-object response")
            return {
                "provider": self.name,
                "status": payload.get("query_status", "unknown"),
                "url_count": payload.get("urlhaus_link_count", 0),
                "reference": payload.get("urlhaus_reference"),
                "raw_available": bool(payload),
            }
        except httpx.HTTPError as exc:
            logging.getLogger("neurosoc.threat-intel").warning("URLhaus lookup failed: %s", exc)
            raise RuntimeError("URLhaus lookup unavailable") from exc
        finally:
            if self.client is None:
                client.close()
