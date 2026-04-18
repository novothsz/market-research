# Job Finder

Python-first job collection and relevance-ranking pipeline.

The project is designed to collect jobs from public, machine-readable sources (instead of LinkedIn account automation), classify relevance against your target prompt and profile, and export a ranked shortlist.

## Platform Support

- macOS (Apple Silicon and Intel)
- Linux
- Python 3.11+
- uv for both virtual environment and dependency management

The repository includes a `.python-version` file with Python 3.12 for consistent setup across machines (including MacBook Air).

## Install uv

On macOS (recommended):

```bash
brew install uv
```

Alternative install method:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Setup (MacBook Air and Linux)

From the repository root:

```bash
uv python install 3.12
uv sync --python 3.12
uv run job-finder --help
```

This creates a uv-managed `.venv`, installs dependencies, and verifies the CLI entrypoint.

## Configure

Create your runtime config:

```bash
cp config.example.toml config.toml
```

Edit `config.toml` and adjust:

- `database_path`: where SQLite will be stored
- `collectors.greenhouse_boards`: board tokens for API collection
- `collectors.seed_urls`: URLs for JSON-LD collection
- `collectors.html_fallback_urls`: optional generic HTML fallback URLs

Network/TLS note:

- On your MacBook Air, default `tls_verify = true` should work.
- If you are behind a proxy or SSL interception network, set `tls_ca_bundle` to your CA PEM path or use `tls_verify = false` temporarily.

## Inputs

Use the sample files or provide your own:

- `examples/profile.txt`: your static professional background
- `examples/prompt.txt`: your current search objective

## Run The Pipeline

One command (recommended):

```bash
uv run job-finder run \
  -c config.toml \
  --prompt-file examples/prompt.txt \
  --profile-file examples/profile.txt \
  -f markdown \
  -o data/shortlist.md \
  --limit 30
```

Step by step:

```bash
uv run job-finder collect -c config.toml
uv run job-finder classify -c config.toml --prompt-file examples/prompt.txt --profile-file examples/profile.txt
uv run job-finder rank -c config.toml --limit 20
uv run job-finder export -c config.toml -f markdown -o data/shortlist.md --prompt-file examples/prompt.txt
```

## Optional Local LLM Classification

If Ollama is running locally:

```bash
uv run job-finder classify \
  -c config.toml \
  --prompt-file examples/prompt.txt \
  --profile-file examples/profile.txt \
  --use-llm \
  --llm-model gemma3:4b
```

Or in one-shot mode:

```bash
uv run job-finder run \
  -c config.toml \
  --prompt-file examples/prompt.txt \
  --profile-file examples/profile.txt \
  --use-llm \
  --llm-model gemma3:4b
```

## CLI Commands

- `init-config`: write a starter config file
- `collect`: fetch job data from configured sources and store in SQLite
- `classify`: compute relevance labels/scores
- `rank`: print ranked jobs in terminal
- `export`: write ranked jobs to CSV or Markdown
- `run`: execute collect + classify + export in sequence

Inspect command options:

```bash
uv run job-finder <command> --help
```

## Outputs

- SQLite database: default `data/jobs.sqlite3`
- Markdown shortlist: for example `data/shortlist.md`
- CSV shortlist: for example `data/shortlist.csv`

## Repository Layout

```text
.
├── pyproject.toml
├── uv.lock
├── config.example.toml
├── examples/
│   ├── profile.txt
│   └── prompt.txt
└── src/job_finder/
    ├── cli.py
    ├── config.py
    ├── models.py
    ├── profile_ingest.py
    ├── prompt_parser.py
    ├── collectors/
    ├── normalize/
    ├── ranking/
    ├── storage/
    └── export/
```

## Development Notes

- This is an MVP architecture built for extension.
- Add source-specific collectors for higher precision and fewer false positives.
- Tune ranking heuristics as your search domain changes.

