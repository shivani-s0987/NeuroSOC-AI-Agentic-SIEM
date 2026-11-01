from __future__ import annotations

import ipaddress
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit

from idna import encode as idna_encode

HASH_LENGTHS = {"md5": 32, "sha1": 40, "sha256": 64}


def normalize_ioc(value: str, ioc_type: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Indicator value is required")
    value = value.strip()
    kind = ioc_type.lower()
    if kind == "ipv4":
        address = ipaddress.ip_address(value)
        if address.version != 4:
            raise ValueError("Indicator is not a valid IPv4 address")
        return str(address)
    if kind == "ipv6":
        address = ipaddress.ip_address(value)
        if address.version != 6:
            raise ValueError("Indicator is not a valid IPv6 address")
        return str(address)
    if kind == "domain":
        candidate = value.rstrip(".").lower()
        if "://" in candidate or "/" in candidate:
            raise ValueError("Domain must not contain a scheme or path")
        return idna_encode(candidate).decode("ascii")
    if kind == "url":
        parsed = urlsplit(value)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
            raise ValueError("URL must use http or https and include a host")
        if parsed.hostname is None or parsed.username is not None or parsed.password is not None:
            raise ValueError("URL is malformed or contains embedded credentials")
        hostname = parsed.hostname.lower()
        try:
            hostname = str(ipaddress.ip_address(hostname))
        except ValueError:
            hostname = idna_encode(hostname).decode("ascii")
        port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
        explicit_port = f":{parsed.port}" if parsed.port is not None else ""
        path = parsed.path or "/"
        return f"{parsed.scheme.lower()}://{hostname}{explicit_port}{path}" + (f"?{parsed.query}" if parsed.query else "") + (f"#{parsed.fragment}" if parsed.fragment else "")
    if kind in HASH_LENGTHS:
        normalized = value.lower()
        if not re.fullmatch(r"[0-9a-f]+", normalized) or len(normalized) != HASH_LENGTHS[kind]:
            raise ValueError(f"{kind.upper()} must contain exactly {HASH_LENGTHS[kind]} hexadecimal characters")
        return normalized
    raise ValueError(f"Unsupported IOC type: {ioc_type}")


def infer_ioc_type(value: str) -> str | None:
    try:
        address = ipaddress.ip_address(value.strip())
        return "ipv4" if address.version == 4 else "ipv6"
    except ValueError:
        pass
    if re.fullmatch(r"[0-9a-fA-F]{32}", value.strip()):
        return "md5"
    if re.fullmatch(r"[0-9a-fA-F]{40}", value.strip()):
        return "sha1"
    if re.fullmatch(r"[0-9a-fA-F]{64}", value.strip()):
        return "sha256"
    if "://" in value:
        return "url"
    if "." in value and "/" not in value and " " not in value:
        return "domain"
    return None


def extract_event_candidates(event) -> list[tuple[str, str, str]]:
    candidates: list[tuple[str, str, str]] = []
    fields = {
        "src_ip": getattr(event, "src_ip", None),
        "dst_ip": getattr(event, "dst_ip", None),
        "message": getattr(event, "message", None),
        "raw": getattr(event, "raw", None),
    }
    for field, value in fields.items():
        if not value:
            continue
        text = str(value)
        if field in {"src_ip", "dst_ip"}:
            candidates.append((field, field.endswith("ip") and infer_ioc_type(text) or "domain", text))
            continue
        for address in re.findall(r"(?<![\w:.])(?:\d{1,3}\.){3}\d{1,3}(?![\w:.])", text):
            candidates.append((field, "ipv4", address))
        for url in re.findall(r"https?://[^\s\"<>]+", text):
            candidates.append((field, "url", url.rstrip(".,)")))
        for domain in re.findall(r"(?<![@\w.-])(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)+[A-Za-z]{2,63}(?![\w.-])", text):
            if not domain.lower().endswith((".png", ".jpg", ".js", ".css")):
                candidates.append((field, "domain", domain))
        for hash_value in re.findall(r"(?<![0-9a-fA-F])[0-9a-fA-F]{32}(?![0-9a-fA-F])|(?<![0-9a-fA-F])[0-9a-fA-F]{40}(?![0-9a-fA-F])|(?<![0-9a-fA-F])[0-9a-fA-F]{64}(?![0-9a-fA-F])", text):
            candidates.append((field, infer_ioc_type(hash_value), hash_value))
    return candidates
