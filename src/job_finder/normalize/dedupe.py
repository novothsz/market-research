from __future__ import annotations

import hashlib
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


TRACKING_QUERY_PREFIXES = ("utm_", "fbclid", "gclid", "mc_cid", "mc_eid")


def canonicalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    filtered_query = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=True)
        if not any(key.startswith(prefix) for prefix in TRACKING_QUERY_PREFIXES)
    ]

    normalized_path = parsed.path.rstrip("/") or "/"
    query = urlencode(filtered_query, doseq=True)

    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            normalized_path,
            "",
            query,
            "",
        )
    )


def compute_job_hash(company: str | None, title: str, location_raw: str | None, url: str) -> str:
    parts = [
        (company or "").strip().lower(),
        title.strip().lower(),
        (location_raw or "").strip().lower(),
        canonicalize_url(url),
    ]
    payload = "|".join(parts)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return digest[:20]
