from __future__ import annotations

import httpx
from pathlib import Path
import json
import re
from typing import Optional

from job_finder.models import JobRecord
from job_finder.collectors.manual_import import _generate_job_hash


# Company career page URLs and scraping hints
BUDAPEST_COMPANIES = {
    "AiMotive": {
        "career_url": "https://www.aimotive.com/careers",
        "job_board": "greenhouse",  # AiMotive uses Greenhouse
        "greenhouse_id": "aimotive",
    },
    "Zenitech": {
        "career_url": "https://zenitech.com/careers",
        "job_board": "unknown",
    },
    "Turbine": {
        "career_url": "https://turbine.io/careers",
        "job_board": "unknown",
    },
    "Siemens": {
        "career_url": "https://careers.siemens.com",
        "job_board": "siemens",
        "location_filter": "Budapest",
    },
    "KUKA": {
        "career_url": "https://www.kuka.com/careers",
        "job_board": "unknown",
    },
    "SAP": {
        "career_url": "https://careers.sap.com",
        "job_board": "sap",
        "location_filter": "Budapest",
    },
    "HCLTech": {
        "career_url": "https://www.hcltech.com/careers",
        "job_board": "hcl",
        "location_filter": "Budapest",
    },
    "micro1": {
        "career_url": "https://micro1.ai/careers",
        "job_board": "unknown",
    },
}


def search_linkedin_jobs(company_name: str, location: str = "Budapest", keywords: list[str] | None = None) -> list[dict]:
    """
    Generate LinkedIn job search URLs for a company.
    Returns search URLs that can be manually visited or used with LinkedIn API.
    """
    if keywords is None:
        keywords = ["machine learning", "AI", "AI engineer", "ML engineer", "data scientist"]
    
    urls = []
    for keyword in keywords:
        # LinkedIn job search URL pattern
        url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={keyword.replace(' ', '%20')}"
            f"&location={location.replace(' ', '%20')}"
            f"&company={company_name.replace(' ', '%20')}"
        )
        urls.append(url)
    
    return urls


def search_indeed_jobs(company_name: str, location: str = "Budapest") -> str:
    """
    Generate Indeed job search URL for a company.
    """
    return (
        f"https://www.indeed.com/jobs?"
        f"q=machine+learning&l={location}&c={company_name.replace(' ', '+')}"
    )


def search_company_site(company_name: str, location: str = "Budapest") -> list[str]:
    """
    Generate Google search URLs to find jobs on company websites.
    Returns search queries that can be manually run or used with a search API.
    """
    queries = [
        f"site:{_get_domain(company_name)} {location} machine learning",
        f"site:{_get_domain(company_name)} {location} AI engineer",
        f"{company_name} careers machine learning {location}",
        f"{company_name} jobs AI {location}",
    ]
    return queries


def _get_domain(company_name: str) -> str:
    """Get company domain from name (heuristic)."""
    domain_map = {
        "AiMotive": "aimotive.com",
        "Zenitech": "zenitech.com",
        "Turbine": "turbine.io",
        "Siemens": "siemens.com",
        "KUKA": "kuka.com",
        "SAP": "sap.com",
        "HCLTech": "hcltech.com",
        "micro1": "micro1.ai",
    }
    return domain_map.get(company_name, company_name.lower().replace(" ", "") + ".com")


def generate_job_search_guide(output_path: Path) -> None:
    """Generate a markdown guide for manually searching and collecting Budapest jobs."""
    guide = r"""# Budapest ML/AI Job Search Guide

## How to Find and Import Budapest ML/AI Jobs

This guide helps you systematically search for and collect ML/AI jobs from Budapest-based companies.

## Companies to Search

### Primary Targets (Confirmed ML/AI Hiring)

1. **AiMotive** (Autonomous Vehicle AI)
   - Careers: https://www.aimotive.com/careers
   - LinkedIn: Search "AiMotive Budapest AI engineer"
   - Indeed: https://www.indeed.com/jobs?q=machine+learning&c=AiMotive&l=Budapest
   - Keywords: autonomous vehicles, computer vision, AI, ML

2. **Zenitech** (GenAI Focus)
   - Careers: https://zenitech.com/careers
   - Keywords: GenAI, LLM, prompt engineering, RAG

3. **Turbine** (Biology + ML)
   - Careers: https://turbine.io/careers
   - Keywords: machine learning, biology, algorithms

4. **Siemens** (NLP/AI)
   - Careers: https://careers.siemens.com
   - Keywords: AI, NLP, machine learning, Budapest

5. **SAP** (Agentic AI)
   - Careers: https://careers.sap.com
   - Keywords: agentic AI, agents, AI

6. **KUKA** (Robotics AI)
   - Careers: https://www.kuka.com/careers
   - Keywords: AI, RAG, robotics

7. **HCLTech** (MLOps/Platform)
   - Careers: https://www.hcltech.com/careers
   - Keywords: ML engineering, MLOps, distributed systems

8. **micro1** (Community Detection)
   - Careers: https://micro1.ai/careers
   - Keywords: machine learning, AI

## Search Methods

### Method 1: Direct Company Career Pages
1. Visit company careers URL
2. Search for "machine learning", "AI", "engineer"
3. Filter by Budapest or Hungary location
4. Copy relevant job details

### Method 2: LinkedIn Job Search
For each company, use these search patterns:
\`\`\`
site:linkedin.com "machine learning" "{company_name}" Budapest
site:linkedin.com "AI engineer" "{company_name}" Budapest
site:linkedin.com "ML engineer" "{company_name}" Budapest
\`\`\`

### Method 3: Indeed Job Search
\`\`\`
site:indeed.com machine learning "{company_name}" Budapest
site:indeed.com AI engineer "{company_name}" Budapest
\`\`\`

### Method 4: Google Job Search
\`\`\`
"machine learning" jobs Budapest "{company_name}"
"AI engineer" jobs Budapest "{company_name}"
"{company_name} careers" machine learning Budapest
\`\`\`

## Data Collection Template

Create a CSV file (budapest_jobs.csv) with discovered jobs:

\`\`\`csv
company,title,location,url,description,seniority,employment_type
AiMotive,AI Research Engineer,Budapest,https://...,Research AI algorithms for autonomous vehicles,senior,full-time
Zenitech,GenAI Engineer,Budapest,https://...,Develop GenAI features with LLM integration,mid,full-time
\`\`\`

## Importing Collected Jobs

Once you have a CSV file with collected jobs:

\`\`\`bash
uv run job-finder import-jobs -i budapest_jobs.csv
\`\`\`

Your imported jobs will then be:
1. Classified using the same ML/rules engine
2. Scored against your profile
3. Exported to location-based shortlists
4. Converted to PDF

## Tips for Effective Searching

- Combine multiple search methods for coverage
- Check multiple job boards (company sites, LinkedIn, Indeed, Glassdoor)
- Save job URLs for reference
- Include full job descriptions (helps with classification accuracy)
- Focus on seniority that matches your background
- Note salary/benefits if available

## Next Steps

1. Collect jobs into budapest_jobs.csv
2. Run: `uv run job-finder import-jobs -i budapest_jobs.csv`
3. Generate shortlists: `uv run job-finder export-by-location -c config.toml -o data`
4. Export to PDF: `uv run job-finder export-pdf -d data`
"""
    output_path.write_text(guide, encoding='utf-8')
