from __future__ import annotations

from collections.abc import Iterable, Sequence
import json
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import httpx

from job_finder.models import JobRecord
from job_finder.normalize.dedupe import canonicalize_url, compute_job_hash
from job_finder.normalize.html_to_text import html_to_text


def _iter_jsonld_objects(node: object) -> Iterable[dict[str, object]]:
    if isinstance(node, list):
        for item in node:
            yield from _iter_jsonld_objects(item)
        return

    if isinstance(node, dict):
        graph = node.get("@graph")
        if graph is not None:
            yield from _iter_jsonld_objects(graph)
        yield node


def _is_job_posting(obj: dict[str, object]) -> bool:
    raw_type = obj.get("@type")
    if isinstance(raw_type, list):
        types = [str(item).lower() for item in raw_type]
    else:
        types = [str(raw_type).lower()]
    return "jobposting" in types


def _read_jsonld_scripts(html: str) -> list[dict[str, object]]:
    soup = BeautifulSoup(html, "html.parser")
    out: list[dict[str, object]] = []

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text() or ""
        raw = raw.strip()
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for obj in _iter_jsonld_objects(payload):
            if _is_job_posting(obj):
                out.append(obj)

    return out


def _parse_location(raw_location: object) -> str:
    if isinstance(raw_location, list):
        parts = [_parse_location(item) for item in raw_location]
        return ", ".join(part for part in parts if part)

    if isinstance(raw_location, dict):
        address = raw_location.get("address")
        if isinstance(address, dict):
            values: list[str] = []
            for key in ("addressLocality", "addressRegion", "addressCountry"):
                value = address.get(key)
                if value:
                    values.append(str(value))
            if values:
                return ", ".join(values)
        name = raw_location.get("name")
        if name:
            return str(name)

    if raw_location:
        return str(raw_location)

    return ""


def collect_from_jsonld_pages(
    urls: Sequence[str],
    timeout_seconds: float,
    user_agent: str,
    verify: bool | str = True,
) -> list[JobRecord]:
    jobs: list[JobRecord] = []
    headers = {"User-Agent": user_agent}

    with httpx.Client(
        timeout=timeout_seconds,
        headers=headers,
        follow_redirects=True,
        verify=verify,
    ) as client:
        for seed_url in urls:
            seed_url = seed_url.strip()
            if not seed_url:
                continue

            try:
                response = client.get(seed_url)
                response.raise_for_status()
            except httpx.HTTPError:
                continue

            jsonld_jobs = _read_jsonld_scripts(response.text)
            if not jsonld_jobs:
                continue

            source_host = urlparse(seed_url).netloc or "jsonld"
            for obj in jsonld_jobs:
                title = str(obj.get("title") or "").strip()
                if not title:
                    continue

                url_raw = str(obj.get("url") or obj.get("sameAs") or seed_url).strip()
                canonical_url = canonicalize_url(url_raw)
                company = None
                hiring = obj.get("hiringOrganization")
                if isinstance(hiring, dict):
                    company = str(hiring.get("name") or "").strip() or None

                location_raw = _parse_location(obj.get("jobLocation"))
                remote_type = None
                remote_marker = str(obj.get("jobLocationType") or "").upper()
                if "TELECOMMUTE" in remote_marker:
                    remote_type = "remote"

                description_html = str(obj.get("description") or "")
                description_text = html_to_text(description_html)

                employment_type = obj.get("employmentType")
                if isinstance(employment_type, list):
                    employment_type_raw = ", ".join(str(x) for x in employment_type)
                else:
                    employment_type_raw = str(employment_type or "")

                salary_raw = obj.get("baseSalary")
                if salary_raw is None:
                    salary_text = None
                else:
                    salary_text = json.dumps(salary_raw, ensure_ascii=True)

                jobs.append(
                    JobRecord(
                        source=f"jsonld:{source_host}",
                        company=company,
                        title=title,
                        url=canonical_url,
                        location_raw=location_raw or None,
                        remote_type=remote_type,
                        description_html=description_html,
                        description_text=description_text,
                        employment_type=employment_type_raw or None,
                        salary_raw=salary_text,
                        posted_at=str(obj.get("datePosted") or "") or None,
                        job_hash=compute_job_hash(
                            company=company,
                            title=title,
                            location_raw=location_raw,
                            url=canonical_url,
                        ),
                    )
                )

    return jobs
