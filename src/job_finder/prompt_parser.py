from __future__ import annotations

from pydantic import BaseModel, Field
import re


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "for",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
    "that",
    "this",
    "from",
    "find",
    "search",
    "looking",
    "look",
    "role",
    "roles",
    "job",
    "jobs",
    "position",
    "positions",
    "work",
    "based",
    "available",
    "done",
    "related",
}


class SearchIntent(BaseModel):
    include_terms: list[str] = Field(default_factory=list)
    exclude_terms: list[str] = Field(default_factory=list)
    location_terms: list[str] = Field(default_factory=list)
    remote_requested: bool = False


def _unique_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def parse_search_prompt(prompt: str) -> SearchIntent:
    lower = prompt.lower()
    tokens = re.findall(r"[a-z0-9+#-]{2,}", lower)

    include: list[str] = []
    exclude: list[str] = []
    for idx, tok in enumerate(tokens):
        if tok in STOPWORDS:
            continue
        prev = tokens[idx - 1] if idx > 0 else ""
        if prev in {"no", "not", "without", "exclude"}:
            exclude.append(tok)
        else:
            include.append(tok)

    location_terms = []
    for marker in ("hungary", "hungarian", "budapest", "europe", "eu"):
        if marker in lower:
            location_terms.append(marker)

    remote_requested = any(
        marker in lower
        for marker in (
            "remote",
            "work from home",
            "telecommute",
            "distributed",
            "hybrid",
        )
    )

    return SearchIntent(
        include_terms=_unique_keep_order(include),
        exclude_terms=_unique_keep_order(exclude),
        location_terms=_unique_keep_order(location_terms),
        remote_requested=remote_requested,
    )
