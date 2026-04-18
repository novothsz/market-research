from __future__ import annotations

from pathlib import Path

import typer

from job_finder.collectors import (
    collect_from_html_pages,
    collect_from_jsonld_pages,
    collect_greenhouse_jobs,
)
from job_finder.config import AppConfig, load_config, render_default_config
from job_finder.export import export_jobs_to_csv, export_jobs_to_markdown
from job_finder.models import ClassificationResult, JobRecord
from job_finder.profile_ingest import load_profile
from job_finder.ranking import classify_job_with_ollama, classify_job_with_rules
from job_finder.storage import (
    connect_db,
    count_jobs,
    fetch_jobs,
    fetch_ranked_jobs,
    init_db,
    update_classification,
    upsert_jobs,
)


app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="Collect, classify, rank, and export job postings.",
)


def _dedupe_jobs(jobs: list[JobRecord]) -> list[JobRecord]:
    unique: dict[str, JobRecord] = {}
    for job in jobs:
        unique[job.job_hash] = job
    return list(unique.values())


def _load_prompt(prompt: str | None, prompt_file: Path | None) -> str:
    if prompt and prompt.strip():
        return prompt.strip()

    if prompt_file is not None:
        if not prompt_file.exists():
            raise typer.BadParameter(f"Prompt file not found: {prompt_file}")
        content = prompt_file.read_text(encoding="utf-8").strip()
        if content:
            return content

    raise typer.BadParameter("Provide either --prompt or --prompt-file.")


def _collect_jobs(cfg: AppConfig, html_fallback: bool) -> tuple[int, int, int]:
    gathered: list[JobRecord] = []
    verify = cfg.http_verify
    gathered.extend(
        collect_greenhouse_jobs(
            cfg.collectors.greenhouse_boards,
            timeout_seconds=cfg.request_timeout_seconds,
            user_agent=cfg.user_agent,
            verify=verify,
        )
    )
    gathered.extend(
        collect_from_jsonld_pages(
            cfg.collectors.seed_urls,
            timeout_seconds=cfg.request_timeout_seconds,
            user_agent=cfg.user_agent,
            verify=verify,
        )
    )

    if html_fallback:
        fallback_urls = cfg.collectors.html_fallback_urls or cfg.collectors.seed_urls
        gathered.extend(
            collect_from_html_pages(
                fallback_urls,
                timeout_seconds=cfg.request_timeout_seconds,
                user_agent=cfg.user_agent,
                verify=verify,
            )
        )

    unique_jobs = _dedupe_jobs(gathered)

    conn = connect_db(cfg.database_path)
    try:
        init_db(conn)
        upsert_jobs(conn, unique_jobs)
        total = count_jobs(conn)
    finally:
        conn.close()

    return len(gathered), len(unique_jobs), total


def _merge_results(rule_result: ClassificationResult, llm_result: ClassificationResult) -> ClassificationResult:
    if llm_result.confidence >= rule_result.confidence:
        return llm_result

    merged_signals = sorted(set(rule_result.matched_signals + llm_result.matched_signals))
    merged_red_flags = sorted(set(rule_result.red_flags + llm_result.red_flags))
    merged_score = (rule_result.score * 0.75) + (llm_result.score * 0.25)
    merged_conf = (rule_result.confidence * 0.75) + (llm_result.confidence * 0.25)

    return ClassificationResult(
        is_relevant=rule_result.is_relevant,
        category=rule_result.category,
        confidence=max(0.0, min(1.0, merged_conf)),
        score=max(0.0, min(100.0, merged_score)),
        why_relevant=rule_result.why_relevant,
        why_not_relevant=rule_result.why_not_relevant,
        matched_signals=merged_signals,
        red_flags=merged_red_flags,
    )


def _classify_jobs(
    cfg: AppConfig,
    prompt_text: str,
    profile_text: str,
    only_unclassified: bool,
    use_llm: bool,
    llm_model: str,
    limit: int,
) -> tuple[int, int]:
    conn = connect_db(cfg.database_path)
    try:
        init_db(conn)
        jobs = fetch_jobs(
            conn,
            only_unclassified=only_unclassified,
            limit=limit if limit > 0 else None,
        )

        updated = 0
        llm_used = 0

        for job in jobs:
            rule_result = classify_job_with_rules(job, profile_text=profile_text, prompt_text=prompt_text)
            final_result = rule_result
            llm_reason = ""
            rule_reason = rule_result.why_relevant or rule_result.why_not_relevant

            # Use LLM only for uncertain rule-based decisions.
            if use_llm and 35.0 <= rule_result.score <= 75.0:
                llm_result = classify_job_with_ollama(
                    job,
                    prompt_text=prompt_text,
                    model=llm_model,
                    timeout_seconds=max(cfg.request_timeout_seconds, 45.0),
                )
                if llm_result is not None:
                    final_result = _merge_results(rule_result, llm_result)
                    llm_reason = llm_result.why_relevant or llm_result.why_not_relevant
                    llm_used += 1

            update_classification(
                conn,
                job_hash=job.job_hash,
                result=final_result,
                llm_reason=llm_reason,
                rule_reason=rule_reason,
            )
            updated += 1
    finally:
        conn.close()

    return updated, llm_used


def _resolve_output_path(fmt: str, output: Path | None) -> Path:
    if output is not None:
        return output
    if fmt == "csv":
        return Path("data/shortlist.csv")
    return Path("data/shortlist.md")


def _export_ranked_jobs(
    cfg: AppConfig,
    fmt: str,
    output: Path | None,
    limit: int,
    relevant_only: bool,
    prompt_text: str,
) -> tuple[Path, int]:
    conn = connect_db(cfg.database_path)
    try:
        init_db(conn)
        jobs = fetch_ranked_jobs(conn, limit=limit, relevant_only=relevant_only)
    finally:
        conn.close()

    out = _resolve_output_path(fmt, output)
    if fmt == "csv":
        count = export_jobs_to_csv(out, jobs)
    else:
        count = export_jobs_to_markdown(out, jobs, prompt_text=prompt_text)
    return out, count


@app.command("init-config")
def init_config(
    path: Path = typer.Option(Path("config.toml"), "--path", "-p"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing config file."),
) -> None:
    if path.exists() and not force:
        raise typer.BadParameter(f"Config already exists: {path}. Use --force to overwrite.")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_default_config(), encoding="utf-8")
    typer.echo(f"Wrote config file: {path}")


@app.command()
def collect(
    config: Path = typer.Option(Path("config.toml"), "--config", "-c"),
    html_fallback: bool = typer.Option(
        False,
        "--html-fallback/--no-html-fallback",
        help="Use generic HTML parsing fallback URLs.",
    ),
) -> None:
    cfg = load_config(config)
    raw_count, unique_count, total = _collect_jobs(cfg, html_fallback=html_fallback)
    typer.echo(
        f"Collected raw={raw_count}, unique={unique_count}, database_total={total}"
    )


@app.command()
def classify(
    config: Path = typer.Option(Path("config.toml"), "--config", "-c"),
    prompt: str | None = typer.Option(None, "--prompt", help="Search goal prompt text."),
    prompt_file: Path | None = typer.Option(None, "--prompt-file", help="Path to prompt text file."),
    profile_file: Path | None = typer.Option(None, "--profile-file", help="Path to user profile text."),
    profile_text: str | None = typer.Option(None, "--profile-text", help="Inline profile text."),
    only_unclassified: bool = typer.Option(True, "--only-unclassified/--all"),
    use_llm: bool = typer.Option(False, "--use-llm/--no-llm"),
    llm_model: str = typer.Option("gemma3:4b", "--llm-model"),
    limit: int = typer.Option(0, "--limit", min=0),
) -> None:
    cfg = load_config(config)
    prompt_text = _load_prompt(prompt, prompt_file)
    profile = load_profile(profile_file=profile_file, profile_text=profile_text)
    updated, llm_used = _classify_jobs(
        cfg,
        prompt_text=prompt_text,
        profile_text=profile,
        only_unclassified=only_unclassified,
        use_llm=use_llm,
        llm_model=llm_model,
        limit=limit,
    )
    typer.echo(f"Classified jobs={updated}, llm_calls={llm_used}")


@app.command()
def rank(
    config: Path = typer.Option(Path("config.toml"), "--config", "-c"),
    limit: int = typer.Option(25, "--limit", min=1),
    relevant_only: bool = typer.Option(True, "--relevant-only/--all"),
) -> None:
    cfg = load_config(config)
    conn = connect_db(cfg.database_path)
    try:
        init_db(conn)
        jobs = fetch_ranked_jobs(conn, limit=limit, relevant_only=relevant_only)
    finally:
        conn.close()

    if not jobs:
        typer.echo("No jobs found.")
        return

    for idx, job in enumerate(jobs, start=1):
        score = f"{job.relevance_score:.1f}" if job.relevance_score is not None else "n/a"
        reason = job.llm_reason or job.rule_reason or ""
        typer.echo(
            f"{idx:>2}. [{score}] {job.relevance_label or 'unclassified'} | "
            f"{job.title} | {job.company or 'unknown'}"
        )
        typer.echo(f"    {job.url}")
        if reason:
            typer.echo(f"    {reason[:180]}")


@app.command()
def export(
    config: Path = typer.Option(Path("config.toml"), "--config", "-c"),
    format: str = typer.Option("markdown", "--format", "-f", help="csv or markdown"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    prompt: str | None = typer.Option(None, "--prompt"),
    prompt_file: Path | None = typer.Option(None, "--prompt-file"),
    limit: int = typer.Option(50, "--limit", min=1),
    relevant_only: bool = typer.Option(True, "--relevant-only/--all"),
) -> None:
    cfg = load_config(config)
    fmt = format.lower().strip()
    if fmt in {"md", "markdown"}:
        fmt = "markdown"
    elif fmt == "csv":
        fmt = "csv"
    else:
        raise typer.BadParameter("--format must be csv or markdown")

    prompt_text = ""
    if prompt or prompt_file:
        prompt_text = _load_prompt(prompt, prompt_file)

    out, count = _export_ranked_jobs(
        cfg,
        fmt=fmt,
        output=output,
        limit=limit,
        relevant_only=relevant_only,
        prompt_text=prompt_text,
    )
    typer.echo(f"Exported {count} jobs to {out}")


@app.command()
def run(
    config: Path = typer.Option(Path("config.toml"), "--config", "-c"),
    prompt: str | None = typer.Option(None, "--prompt"),
    prompt_file: Path | None = typer.Option(None, "--prompt-file"),
    profile_file: Path | None = typer.Option(None, "--profile-file"),
    profile_text: str | None = typer.Option(None, "--profile-text"),
    html_fallback: bool = typer.Option(False, "--html-fallback/--no-html-fallback"),
    use_llm: bool = typer.Option(False, "--use-llm/--no-llm"),
    llm_model: str = typer.Option("gemma3:4b", "--llm-model"),
    format: str = typer.Option("markdown", "--format", "-f"),
    output: Path | None = typer.Option(None, "--output", "-o"),
    limit: int = typer.Option(50, "--limit", min=1),
) -> None:
    cfg = load_config(config)
    prompt_text = _load_prompt(prompt, prompt_file)
    profile = load_profile(profile_file=profile_file, profile_text=profile_text)

    raw_count, unique_count, total = _collect_jobs(cfg, html_fallback=html_fallback)
    typer.echo(
        f"Collect phase complete: raw={raw_count}, unique={unique_count}, database_total={total}"
    )

    updated, llm_used = _classify_jobs(
        cfg,
        prompt_text=prompt_text,
        profile_text=profile,
        only_unclassified=True,
        use_llm=use_llm,
        llm_model=llm_model,
        limit=0,
    )
    typer.echo(f"Classify phase complete: classified={updated}, llm_calls={llm_used}")

    fmt = format.lower().strip()
    if fmt in {"md", "markdown"}:
        fmt = "markdown"
    elif fmt != "csv":
        raise typer.BadParameter("--format must be csv or markdown")

    out, count = _export_ranked_jobs(
        cfg,
        fmt=fmt,
        output=output,
        limit=limit,
        relevant_only=True,
        prompt_text=prompt_text,
    )
    typer.echo(f"Export phase complete: exported={count}, output={out}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
