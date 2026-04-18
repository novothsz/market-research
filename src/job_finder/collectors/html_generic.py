from __future__ import annotations

from collections.abc import Sequence
from urllib.parse import urlparse

from bs4 import BeautifulSoup
import httpx

from job_finder.models import JobRecord
from job_finder.normalize.dedupe import canonicalize_url, compute_job_hash
from job_finder.normalize.html_to_text import html_to_text


def collect_from_html_pages(
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
        for page_url in urls:
            page_url = page_url.strip()
            if not page_url:
                continue

            try:
                response = client.get(page_url)
                response.raise_for_status()
            except httpx.HTTPError:
                continue

            soup = BeautifulSoup(response.text, "html.parser")
            title_node = soup.find("h1") or soup.find("title")
            title = title_node.get_text(strip=True) if title_node else "Untitled role"

            main = soup.find("main") or soup.find("article") or soup.body
            description_html = str(main) if main is not None else response.text
            description_text = html_to_text(description_html)

            host = urlparse(page_url).netloc or "html"
            canonical_url = canonicalize_url(page_url)

            jobs.append(
                JobRecord(
                    source=f"html:{host}",
                    company=host,
                    title=title,
                    url=canonical_url,
                    description_html=description_html,
                    description_text=description_text,
                    job_hash=compute_job_hash(
                        company=host,
                        title=title,
                        location_raw="",
                        url=canonical_url,
                    ),
                )
            )

    return jobs
