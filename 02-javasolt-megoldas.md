# Proposed Solution

## Overview
The proposed solution should not be a single script that directly automates the LinkedIn web interface. Instead, it should be a Python pipeline composed of multiple components.

The main reason is that LinkedIn prohibits bots, crawlers, scripts, and other forms of automation, so direct authenticated LinkedIn scraping is risky and unstable in the long term. [cite:2]

For this reason, the solution should primarily rely on public and machine-processable job sources, and only use lightweight web extraction where it is technically and legally reasonable.

## Recommended Architecture
The system should be a multi-step pipeline:

1. Profile ingestion.
2. Search-goal interpretation.
3. Job link and description collection.
4. Normalization and cleaning.
5. LLM-based relevance evaluation.
6. Ranking and export.

Profile ingestion should not require live LinkedIn login. It should use inputs such as:

- Pasted LinkedIn About and Experience text.
- Text extracted from PDF or DOCX CV files.
- Optional manual profile fields such as skills, seniority, preferred location, and remote preference.

The search goal should be a separate prompt, for example: "Find reinforcement learning, offline RL, robotics learning, or sequential decision-making roles in Hungary or remote positions that can be done from Hungary."

## Job Collection
Job links and descriptions should be collected from multiple sources.

In the first stage, company career pages and ATS systems should be primary sources, because they are more stable and better structured than LinkedIn HTML pages.

Greenhouse's public Job Board API supports programmatic listing retrieval, and with content=true, detailed descriptions can also be fetched. [cite:24]

The second major source is JobPosting structured data on public job pages. According to Google documentation, the markup may include title, description, company, location, employment type, remote flag, and salary. [cite:26]

Suggested collection order:

- ATS API when available.
- JSON-LD or JobPosting structured data when available.
- Generic HTML parser fallback when structured data is not available.

## Why Not LinkedIn Automation
LinkedIn prohibits automated software and automated activity, so a logged-in script that clicks through LinkedIn and reads postings at scale should not be the core of the solution. [cite:2][cite:18]

LinkedIn should only serve as a source of user-provided profile material (exported or pasted text), not as a live account to be controlled by the system.

## Relevance Evaluation
Raw keyword filtering is not enough, because many postings mention RL but are not actually RL-focused.

So a two-stage evaluation is recommended:

- First stage: fast rule and keyword based filtering.
- Second stage: LLM classification based on the full job description.

The model should return structured JSON output with fields such as:

- is_relevant
- category
- confidence
- why_relevant
- why_not_relevant
- matched_signals
- red_flags

Example categories:

- direct_rl
- adjacent_ml
- robotics_or_control
- generic_ml_not_rl
- not_relevant

## Local Model Usage
This task does not necessarily require a large cloud model.

Google presents Gemma 3 as an open model family that can run locally in 1B, 4B, 12B, and 27B sizes, with long context and tool use capabilities. [cite:13]

So for relevance classification, local execution should be considered, for example via Ollama or another simple local inference runtime, as long as it is easy to call from Python.

The goal is not open-ended chat generation, but a narrower structured decision task.

## Data Model
A unified record structure is recommended for every job:

- source
- company
- title
- url
- location_raw
- country
- remote_type
- description_html
- description_text
- employment_type
- salary_raw
- posted_at
- relevance_score
- relevance_label
- llm_reason
- hash

The hash should support deduplication, because the same role can appear across multiple boards or aggregators.

## Recommended Python-Only Implementation
There is an explicit request to keep the project as Python-only as possible.

The solution should therefore avoid requiring Node.js, frontend build tools, or services in multiple languages.

Suggested stack:

- Python 3.11+.
- uv package manager and virtual environment handling.
- httpx or requests for HTTP.
- selectolax, beautifulsoup4, or lxml for HTML parsing.
- pydantic for data models.
- sqlite or sqlite3 for initial storage.
- typer or argparse for the CLI.
- optionally playwright only as a last-resort fallback, and only when absolutely necessary.

If fallback browser automation is required for a public site, it should still be driven from Python.

## Recommended Project Structure
One possible repository layout:

```text
job-finder/
  pyproject.toml
  uv.lock
  README.md
  src/job_finder/
    cli.py
    config.py
    models.py
    profile_ingest.py
    prompt_parser.py
    collectors/
      greenhouse.py
      jsonld.py
      html_generic.py
    normalize/
      html_to_text.py
      dedupe.py
    ranking/
      rules.py
      llm_classifier.py
    storage/
      sqlite.py
    export/
      markdown.py
      csv.py
```

## What to Ask the Development Agent For
In the task description for Claude Code or GitHub Copilot, emphasize:

- Python-first implementation.
- Prefer using only Python and uv.
- Do not build a LinkedIn-login or LinkedIn-DOM automation-first solution.
- Build a modular collector system.
- Use structured JSON output classification for relevance evaluation.
- Provide a simple CLI interface such as collect, classify, rank, and export commands.
- Make the first MVP work with SQLite and file-based configuration.
- Keep it easy to extend with new sources and new search themes.

## MVP Recommendation
The smallest useful first version should include:

- Manually provided profile text or pasted CV/LinkedIn text.
- One search prompt.
- Greenhouse + generic JSON-LD + generic HTML collector.
- SQLite storage.
- Simple rule-based filtering.
- Optional local LLM relevance classification.
- CSV or Markdown export for shortlist output.

This version is already useful for quickly exploring relevant Hungary-based or remote RL roles while staying technically simple and Python-centered.
