from __future__ import annotations

from collections.abc import Sequence

import httpx

from job_finder.models import JobRecord
from job_finder.normalize.dedupe import canonicalize_url, compute_job_hash
from job_finder.normalize.html_to_text import html_to_text


def collect_greenhouse_jobs(
    board_tokens: Sequence[str],
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
        for board in board_tokens:
            board = board.strip()
            if not board:
                continue

            url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
            try:
                response = client.get(url, params={"content": "true"})
                response.raise_for_status()
            except httpx.HTTPError:
                continue

            payload = response.json()
            for raw in payload.get("jobs", []):
                title = str(raw.get("title") or "").strip()
                url_raw = str(raw.get("absolute_url") or raw.get("url") or "").strip()
                if not title or not url_raw:
                    continue

                location_raw = ""
                location = raw.get("location")
                if isinstance(location, dict):
                    location_raw = str(location.get("name") or "").strip()

                description_html = str(raw.get("content") or "")
                description_text = html_to_text(description_html)
                canonical_url = canonicalize_url(url_raw)

                jobs.append(
                    JobRecord(
                        source=f"greenhouse:{board}",
                        company=board,
                        title=title,
                        url=canonical_url,
                        location_raw=location_raw or None,
                        description_html=description_html,
                        description_text=description_text,
                        posted_at=str(raw.get("updated_at") or raw.get("created_at") or "") or None,
                        job_hash=compute_job_hash(
                            company=board,
                            title=title,
                            location_raw=location_raw,
                            url=canonical_url,
                        ),
                    )
                )

    return jobs
