from __future__ import annotations

from job_finder.models import ClassificationResult, JobRecord
from job_finder.prompt_parser import parse_search_prompt


DIRECT_RL_TERMS = {
    "reinforcement learning",
    "offline rl",
    "policy gradient",
    "actor critic",
    "q-learning",
    "deep q",
    "sequential decision",
    "multi-armed bandit",
}

ADJACENT_TERMS = {
    "imitation learning",
    "robot learning",
    "control theory",
    "planning",
    "operations research",
    "decision intelligence",
    "machine learning",
    "deep learning",
}

ROBOTICS_CONTROL_TERMS = {
    "robotics",
    "autonomy",
    "control",
    "trajectory",
    "navigation",
}

NEGATIVE_TERMS = {
    "sales",
    "hr",
    "recruiter",
    "frontend",
    "graphic designer",
    "account manager",
}

REMOTE_TERMS = {
    "remote",
    "hybrid",
    "work from home",
    "telecommute",
    "distributed",
}

HUNGARY_TERMS = {
    "hungary",
    "hungarian",
    "budapest",
}


def _count_present(text: str, terms: set[str]) -> list[str]:
    return [term for term in terms if term in text]


def _profile_tokens(profile_text: str) -> set[str]:
    raw = profile_text.lower().replace(",", " ").replace("/", " ").split()
    return {token.strip() for token in raw if len(token.strip()) >= 3}


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(value, hi))


def _detect_category(text: str, direct_hits: list[str], adjacent_hits: list[str]) -> str:
    if direct_hits:
        return "direct_rl"

    if _count_present(text, ROBOTICS_CONTROL_TERMS):
        return "robotics_or_control"

    if adjacent_hits:
        return "adjacent_ml"

    if "machine learning" in text or "deep learning" in text:
        return "generic_ml_not_rl"

    return "not_relevant"


def classify_job_with_rules(job: JobRecord, profile_text: str, prompt_text: str) -> ClassificationResult:
    intent = parse_search_prompt(prompt_text)

    job_corpus = " ".join(
        [
            job.title or "",
            job.company or "",
            job.location_raw or "",
            job.description_text or "",
        ]
    ).lower()

    direct_hits = _count_present(job_corpus, DIRECT_RL_TERMS)
    adjacent_hits = _count_present(job_corpus, ADJACENT_TERMS)
    negative_hits = _count_present(job_corpus, NEGATIVE_TERMS)
    remote_hits = _count_present(job_corpus, REMOTE_TERMS)
    hungary_hits = _count_present(job_corpus, HUNGARY_TERMS)

    profile = _profile_tokens(profile_text)
    prompt_terms = [term for term in intent.include_terms if len(term) >= 3]
    prompt_hits = [term for term in prompt_terms if term in job_corpus]
    profile_hits = [tok for tok in profile if tok in job_corpus][:10]

    score = 10.0
    score += min(54.0, len(direct_hits) * 18.0)
    score += min(20.0, len(adjacent_hits) * 6.5)
    score += min(18.0, len(prompt_hits) * 3.0)
    score += min(16.0, len(profile_hits) * 2.0)

    if intent.remote_requested:
        score += 8.0 if remote_hits else -6.0

    if intent.location_terms:
        score += 6.0 if hungary_hits else -2.0

    if negative_hits and not direct_hits:
        score -= min(24.0, len(negative_hits) * 8.0)

    score = _clamp(score, 0.0, 100.0)
    category = _detect_category(job_corpus, direct_hits, adjacent_hits)

    is_relevant = score >= 55.0 and category in {
        "direct_rl",
        "adjacent_ml",
        "robotics_or_control",
    }

    matched_signals = sorted(set(direct_hits + adjacent_hits + prompt_hits[:8]))
    red_flags = sorted(set(negative_hits))

    why_relevant = ""
    if matched_signals:
        why_relevant = "Matched signals: " + ", ".join(matched_signals[:8])

    why_not_relevant = ""
    if red_flags:
        why_not_relevant = "Potential mismatch signals: " + ", ".join(red_flags[:6])
    elif not matched_signals:
        why_not_relevant = "No strong domain-specific evidence was found in the job text."

    confidence = _clamp(0.45 + (score / 180.0), 0.0, 0.95)

    return ClassificationResult(
        is_relevant=is_relevant,
        category=category,
        confidence=confidence,
        score=score,
        why_relevant=why_relevant,
        why_not_relevant=why_not_relevant,
        matched_signals=matched_signals,
        red_flags=red_flags,
    )
