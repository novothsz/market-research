from __future__ import annotations

from pathlib import Path
from job_finder.models import JobRecord


def extract_primary_location(location_raw: str | None) -> str:
    """Extract the primary location from a location string."""
    if not location_raw:
        return "unknown"
    
    location_lower = location_raw.lower()
    
    # Check for priority cities first
    priority_cities = {
        "budapest": "budapest",
        "vienna": "vienna",
        "graz": "graz",
        "zurich": "zurich",
    }
    
    for keyword, city in priority_cities.items():
        if keyword in location_lower:
            return city
    
    # Check for remote
    if "remote" in location_lower:
        return "remote"
    
    return "other"


def export_jobs_by_location(
    jobs: list[JobRecord],
    output_dir: Path,
    prompt_text: str,
) -> dict[str, int]:
    """Export jobs into separate files by location."""
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Group jobs by location
    jobs_by_location: dict[str, list[JobRecord]] = {
        "budapest": [],
        "vienna": [],
        "graz": [],
        "zurich": [],
        "remote": [],
        "other": [],
    }
    
    for job in jobs:
        primary_loc = extract_primary_location(job.location_raw)
        if primary_loc in jobs_by_location:
            jobs_by_location[primary_loc].append(job)
    
    export_counts = {}
    
    for location, location_jobs in jobs_by_location.items():
        if not location_jobs:
            continue
        
        output_file = output_dir / f"shortlist_{location}.md"
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"# Job Shortlist - {location.title()}\n\n")
            f.write(f"Search objective: {prompt_text}\n\n")
            
            for idx, job in enumerate(location_jobs, 1):
                f.write(f"## {idx}. {job.title}\n")
                f.write(f"- Company: {job.company or 'Unknown'}\n")
                f.write(f"- Source: {job.source}\n")
                f.write(f"- URL: {job.url}\n")
                f.write(f"- Location: {job.location_raw or 'Unknown'}\n")
                f.write(f"- Score: {job.relevance_score or 0}\n")
                f.write(f"- Label: {job.relevance_label or 'unclassified'}\n")
                
                if job.rule_reason:
                    f.write(f"- Reason: {job.rule_reason}\n")
                
                if job.matched_signals:
                    signals = ", ".join(job.matched_signals[:10])
                    f.write(f"- Matched signals: {signals}\n")
                
                if job.red_flags:
                    flags = ", ".join(job.red_flags[:5])
                    f.write(f"- Red flags: {flags}\n")
                
                f.write("\n")
        
        export_counts[location] = len(location_jobs)
    
    return export_counts
