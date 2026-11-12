from __future__ import annotations

import hashlib
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

VOLATILE_QUERY_KEYS = {"utm_source", "utm_medium", "utm_campaign", "fbclid", "gclid", "_"}


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url)
    query = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in VOLATILE_QUERY_KEYS
    ]
    query.sort()
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((parsed.scheme, parsed.netloc.lower(), path, "", urlencode(query), ""))


def state_fingerprint(url: str, auth_state: str, viewport: str, landmarks: list[str]) -> str:
    canonical = canonicalize_url(url)
    material = "|".join([canonical, auth_state, viewport, ",".join(sorted(landmarks)[:20])])
    return hashlib.sha256(material.encode("utf-8")).hexdigest()
