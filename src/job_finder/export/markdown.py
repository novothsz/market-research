from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from job_finder.models import JobRecord


def export_jobs_to_markdown(path: Path, jobs: Iterable[JobRecord], prompt_text: str = "") -> int:
    path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = ["# Job Shortlist", ""]
    if prompt_text.strip():
        lines.append(f"Search objective: {prompt_text.strip()}")
        lines.append("")

    count = 0
    for idx, job in enumerate(jobs, start=1):
        score = f"{job.relevance_score:.1f}" if job.relevance_score is not None else "n/a"
        lines.extend(
            [
                f"## {idx}. {job.title}",
                f"- Company: {job.company or 'unknown'}",
                f"- Source: {job.source}",
                f"- URL: {job.url}",
                f"- Location: {job.location_raw or 'unknown'}",
                f"- Score: {score}",
                f"- Label: {job.relevance_label or 'unclassified'}",
            ]
        )

        reason = job.llm_reason or job.rule_reason or ""
        if reason:
            lines.append(f"- Reason: {reason}")

        if job.matched_signals:
            lines.append(f"- Matched signals: {', '.join(job.matched_signals[:10])}")

        if job.red_flags:
            lines.append(f"- Red flags: {', '.join(job.red_flags[:10])}")

        lines.append("")
        count += 1

    path.write_text("\n".join(lines), encoding="utf-8")
    return count
