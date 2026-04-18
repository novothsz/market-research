from __future__ import annotations

import json

import httpx

from job_finder.models import ClassificationResult, JobRecord


def _extract_json_object(text: str) -> dict[str, object] | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    snippet = text[start : end + 1]
    try:
        payload = json.loads(snippet)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    return payload


def classify_job_with_ollama(
    job: JobRecord,
    prompt_text: str,
    model: str = "gemma3:4b",
    host: str = "http://127.0.0.1:11434",
    timeout_seconds: float = 45.0,
) -> ClassificationResult | None:
    schema = {
        "is_relevant": True,
        "category": "direct_rl",
        "confidence": 0.0,
        "why_relevant": "",
        "why_not_relevant": "",
        "matched_signals": [],
        "red_flags": [],
    }

    instruction = (
        "Classify relevance for this job and return JSON only. "
        "Use categories: direct_rl, adjacent_ml, robotics_or_control, "
        "generic_ml_not_rl, not_relevant.\n"
        f"Target search goal: {prompt_text}\n"
        f"Job title: {job.title}\n"
        f"Company: {job.company or 'unknown'}\n"
        f"Location: {job.location_raw or 'unknown'}\n"
        f"Description:\n{job.description_text[:7000]}\n"
        f"JSON schema example: {json.dumps(schema)}"
    )

    payload = {
        "model": model,
        "prompt": instruction,
        "stream": False,
    }

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.post(f"{host}/api/generate", json=payload)
            response.raise_for_status()
            response_json = response.json()
    except (httpx.HTTPError, json.JSONDecodeError):
        return None

    raw_text = str(response_json.get("response") or "")
    parsed = _extract_json_object(raw_text)
    if not parsed:
        return None

    confidence = float(parsed.get("confidence") or 0.0)
    confidence = max(0.0, min(confidence, 1.0))

    try:
        return ClassificationResult(
            is_relevant=bool(parsed.get("is_relevant")),
            category=str(parsed.get("category") or "not_relevant"),
            confidence=confidence,
            score=round(confidence * 100.0, 2),
            why_relevant=str(parsed.get("why_relevant") or ""),
            why_not_relevant=str(parsed.get("why_not_relevant") or ""),
            matched_signals=[str(x) for x in parsed.get("matched_signals", [])],
            red_flags=[str(x) for x in parsed.get("red_flags", [])],
        )
    except (TypeError, ValueError):
        return None
