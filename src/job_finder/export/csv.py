from __future__ import annotations

from collections.abc import Iterable
import csv
from pathlib import Path

from job_finder.models import JobRecord


CSV_FIELDS = [
    "source",
    "company",
    "title",
    "url",
    "location_raw",
    "country",
    "remote_type",
    "employment_type",
    "salary_raw",
    "posted_at",
    "relevance_score",
    "relevance_label",
    "classification_confidence",
    "is_relevant",
    "rule_reason",
    "llm_reason",
    "matched_signals",
    "red_flags",
    "job_hash",
]


def export_jobs_to_csv(path: Path, jobs: Iterable[JobRecord]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for job in jobs:
            writer.writerow(
                {
                    **job.model_dump(),
                    "matched_signals": ", ".join(job.matched_signals),
                    "red_flags": ", ".join(job.red_flags),
                }
            )
            count += 1
    return count
