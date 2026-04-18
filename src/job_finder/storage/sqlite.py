from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path
import sqlite3

from job_finder.models import ClassificationResult, JobRecord


DDL = """
CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  company TEXT,
  title TEXT NOT NULL,
  url TEXT NOT NULL,
  location_raw TEXT,
  country TEXT,
  remote_type TEXT,
  description_html TEXT,
  description_text TEXT,
  employment_type TEXT,
  salary_raw TEXT,
  posted_at TEXT,
  relevance_score REAL,
  relevance_label TEXT,
  llm_reason TEXT,
  rule_reason TEXT,
  classification_confidence REAL,
  is_relevant INTEGER,
  matched_signals TEXT,
  red_flags TEXT,
  job_hash TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


def connect_db(path: str) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(DDL)
    conn.commit()


def upsert_jobs(conn: sqlite3.Connection, jobs: Iterable[JobRecord]) -> int:
    sql = """
    INSERT INTO jobs (
      source, company, title, url, location_raw, country, remote_type,
      description_html, description_text, employment_type, salary_raw, posted_at,
      relevance_score, relevance_label, llm_reason, rule_reason,
      classification_confidence, is_relevant, matched_signals, red_flags, job_hash
    ) VALUES (
      :source, :company, :title, :url, :location_raw, :country, :remote_type,
      :description_html, :description_text, :employment_type, :salary_raw, :posted_at,
      :relevance_score, :relevance_label, :llm_reason, :rule_reason,
      :classification_confidence, :is_relevant, :matched_signals, :red_flags, :job_hash
    )
    ON CONFLICT(job_hash) DO UPDATE SET
      source = excluded.source,
      company = excluded.company,
      title = excluded.title,
      url = excluded.url,
      location_raw = excluded.location_raw,
      country = excluded.country,
      remote_type = excluded.remote_type,
      description_html = excluded.description_html,
      description_text = excluded.description_text,
      employment_type = excluded.employment_type,
      salary_raw = excluded.salary_raw,
      posted_at = excluded.posted_at,
      updated_at = CURRENT_TIMESTAMP
    """

    count = 0
    for job in jobs:
        payload = {
            **job.model_dump(),
            "is_relevant": None if job.is_relevant is None else int(job.is_relevant),
            "matched_signals": json.dumps(job.matched_signals, ensure_ascii=True),
            "red_flags": json.dumps(job.red_flags, ensure_ascii=True),
        }
        conn.execute(sql, payload)
        count += 1

    conn.commit()
    return count


def _row_to_job(row: sqlite3.Row) -> JobRecord:
    return JobRecord(
        source=row["source"],
        company=row["company"],
        title=row["title"],
        url=row["url"],
        location_raw=row["location_raw"],
        country=row["country"],
        remote_type=row["remote_type"],
        description_html=row["description_html"],
        description_text=row["description_text"] or "",
        employment_type=row["employment_type"],
        salary_raw=row["salary_raw"],
        posted_at=row["posted_at"],
        relevance_score=row["relevance_score"],
        relevance_label=row["relevance_label"],
        llm_reason=row["llm_reason"],
        rule_reason=row["rule_reason"],
        classification_confidence=row["classification_confidence"],
        is_relevant=None if row["is_relevant"] is None else bool(row["is_relevant"]),
        matched_signals=json.loads(row["matched_signals"] or "[]"),
        red_flags=json.loads(row["red_flags"] or "[]"),
        job_hash=row["job_hash"],
    )


def fetch_jobs(
    conn: sqlite3.Connection,
    only_unclassified: bool = False,
    limit: int | None = None,
) -> list[JobRecord]:
    sql = "SELECT * FROM jobs"
    params: dict[str, object] = {}
    if only_unclassified:
        sql += " WHERE relevance_score IS NULL"
    sql += " ORDER BY COALESCE(posted_at, created_at) DESC"
    if limit and limit > 0:
        sql += " LIMIT :limit"
        params["limit"] = limit
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_job(row) for row in rows]


def update_classification(
    conn: sqlite3.Connection,
    job_hash: str,
    result: ClassificationResult,
    llm_reason: str = "",
    rule_reason: str = "",
) -> None:
    conn.execute(
        """
        UPDATE jobs
        SET
          relevance_score = ?,
          relevance_label = ?,
          llm_reason = ?,
          rule_reason = ?,
          classification_confidence = ?,
          is_relevant = ?,
          matched_signals = ?,
          red_flags = ?,
          updated_at = CURRENT_TIMESTAMP
        WHERE job_hash = ?
        """,
        (
            result.score,
            result.category,
            llm_reason,
            rule_reason,
            result.confidence,
            int(result.is_relevant),
            json.dumps(result.matched_signals, ensure_ascii=True),
            json.dumps(result.red_flags, ensure_ascii=True),
            job_hash,
        ),
    )
    conn.commit()


def fetch_ranked_jobs(
    conn: sqlite3.Connection,
    limit: int = 50,
    relevant_only: bool = True,
) -> list[JobRecord]:
    sql = "SELECT * FROM jobs"
    params: dict[str, object] = {"limit": limit}
    if relevant_only:
        sql += " WHERE is_relevant = 1"
    sql += " ORDER BY COALESCE(relevance_score, 0) DESC, COALESCE(posted_at, created_at) DESC LIMIT :limit"
    rows = conn.execute(sql, params).fetchall()
    return [_row_to_job(row) for row in rows]


def count_jobs(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS n FROM jobs").fetchone()
    return int(row["n"])
