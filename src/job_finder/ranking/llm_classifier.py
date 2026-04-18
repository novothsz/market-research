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


def apply_llm_final_gate(
    job: JobRecord,
    profile_text: str,
    prompt_text: str,
    rule_result: ClassificationResult,
    model: str = "gemma3:4b",
    host: str = "http://127.0.0.1:11434",
    timeout_seconds: float = 45.0,
) -> ClassificationResult:
    """Use LLM to make final go/no-go decision on including job in shortlist."""
    if not rule_result.is_relevant:
        return rule_result

    instruction = (
        "You are a job relevance classifier. Decide if this job should be in a candidate's shortlist. "
        "Return JSON only.\n"
        f"Candidate profile:\n{profile_text[:2000]}\n\n"
        f"Search goal:\n{prompt_text}\n\n"
        f"Job title: {job.title}\n"
        f"Company: {job.company or 'unknown'}\n"
        f"Location: {job.location_raw or 'unknown'}\n"
        f"Description:\n{job.description_text[:4000]}\n\n"
        "Questions to answer:\n"
        "1. Is this job a strong match for the candidate's skills and experience?\n"
        "2. Does the location work (priority: Budapest, Vienna, Graz, Zurich, or remote-friendly)?\n"
        "3. Is this aligned with the candidate's search goals?\n"
        "Return: {\"should_include\": true/false, \"confidence\": 0.0-1.0, \"reason\": \"brief justification\"}"
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
    except (httpx.HTTPError, json.JSONDecodeError, Exception):
        return rule_result

    raw_text = str(response_json.get("response") or "")
    parsed = _extract_json_object(raw_text)
    if not parsed:
        return rule_result

    should_include = bool(parsed.get("should_include", rule_result.is_relevant))
    confidence = float(parsed.get("confidence", rule_result.confidence))
    confidence = max(0.0, min(confidence, 1.0))
    reason = str(parsed.get("reason", ""))

    # Update relevance based on LLM decision
    return ClassificationResult(
        is_relevant=should_include,
        category=rule_result.category,
        confidence=confidence,
        score=rule_result.score if should_include else 0.0,
        why_relevant=reason if should_include else "",
        why_not_relevant=reason if not should_include else rule_result.why_not_relevant,
        matched_signals=rule_result.matched_signals if should_include else [],
        red_flags=rule_result.red_flags + (["llm_rejected"] if not should_include else []),
    )


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
