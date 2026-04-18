"""Web scraper for Budapest ML/AI jobs from company career pages."""

from __future__ import annotations

import re
import json
import logging
from typing import Optional
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from job_finder.models import JobRecord
from job_finder.collectors.manual_import import _generate_job_hash

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# User agent to avoid blocking
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}


async def scrape_greenhouse_board(greenhouse_id: str, company_name: str) -> list[dict]:
    """
    Scrape jobs from a Greenhouse job board using public API.
    
    Args:
        greenhouse_id: Greenhouse board ID (e.g., "aimotive" for aimotive.greenhouse.io)
        company_name: Company name for metadata
    
    Returns:
        List of job dicts with title, location, url, description_html
    """
    jobs = []
    
    try:
        jobs_url = f"https://{greenhouse_id}.greenhouse.io/api/v1/jobs?content=true"
        
        async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:
            response = await client.get(jobs_url)
            
            if response.status_code != 200:
                logger.warning(f"Greenhouse {greenhouse_id} returned {response.status_code}")
                return jobs
            
            data = response.json()
            for job in data.get("jobs", [])[:30]:  # Limit to 30 jobs
                try:
                    # Check if job is in Budapest (or no location = flexible)
                    location = job.get("location", {})
                    location_name = location.get("name", "").lower()
                    
                    # Include jobs that are Budapest or have flexible location
                    if location_name and "budapest" not in location_name and location_name.strip():
                        continue
                    
                    title = job.get("title", "").strip()
                    if not title:
                        continue
                    
                    # Extract main content (remove HTML tags)
                    content = job.get("content", "")
                    if content:
                        content_clean = re.sub(r"<[^>]+>", " ", content)
                        content_clean = re.sub(r"\s+", " ", content_clean).strip()
                    else:
                        content_clean = ""
                    
                    jobs.append({
                        "company": company_name,
                        "title": title,
                        "location": location_name or "Budapest",
                        "url": job.get("absolute_url", ""),
                        "description_html": content_clean,
                        "employment_type": "full-time",
                    })
                except Exception as e:
                    logger.debug(f"Error parsing Greenhouse job: {e}")
                    continue
    
    except Exception as e:
        logger.warning(f"Error scraping Greenhouse {greenhouse_id}: {e}")
    
    return jobs


async def scrape_general_career_page(url: str, company_name: str, keywords: list[str] | None = None) -> list[dict]:
    """
    Scrape jobs from a general career page using BeautifulSoup.
    
    Args:
        url: Career page URL
        company_name: Company name
        keywords: Keywords to filter jobs (ml, ai, engineer, etc.)
    
    Returns:
        List of job dicts
    """
    if keywords is None:
        keywords = ["machine learning", "ai", "engineer", "robotics", "autonomous", "ml", "learning", "research"]
    
    jobs = []
    
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers=HEADERS) as client:
            response = await client.get(url)
            if response.status_code != 200:
                logger.warning(f"Career page {url} returned {response.status_code}")
                return jobs
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style tags
            for tag in soup(["script", "style"]):
                tag.decompose()
            
            # Look for common job listing patterns
            job_elements = []
            
            # Pattern 1: Jobs in divs with job/position/opening/vacancy class
            job_elements.extend(soup.find_all(["div", "article"], class_=re.compile(r"job|position|opening|vacancy|posting", re.I)))
            
            # Pattern 2: Jobs in list items
            if not job_elements:
                job_list = soup.find("ul", class_=re.compile(r"job|position|opening", re.I))
                if job_list:
                    job_elements = job_list.find_all("li", limit=20)
            
            # Pattern 3: Look for tables with job data
            if not job_elements:
                tables = soup.find_all("table", class_=re.compile(r"job|position", re.I))
                for table in tables:
                    job_elements.extend(table.find_all("tr")[1:20])  # Skip header
            
            for element in job_elements[:25]:  # Limit to first 25
                try:
                    # Extract job text
                    element_text = element.get_text(" ", strip=True).lower()
                    
                    # Quick filter: check if element contains job keywords
                    if not any(kw in element_text for kw in keywords):
                        continue
                    
                    # Extract title (try multiple selectors)
                    title = ""
                    for selector in ["h1", "h2", "h3", "h4", ".title", ".job-title", ".position-title"]:
                        title_elem = element.select_one(selector)
                        if title_elem:
                            title = title_elem.get_text(strip=True)
                            break
                    
                    # If no title found, try to extract from text
                    if not title:
                        text_content = element.get_text("\n", strip=True)
                        lines = [l.strip() for l in text_content.split("\n") if l.strip()]
                        if lines:
                            # First non-empty line is likely the title
                            title = lines[0][:120]
                    
                    if not title or len(title) < 10:
                        continue
                    
                    # Extract job link
                    link_elem = element.find("a", href=True)
                    job_url = urljoin(url, link_elem["href"]) if link_elem else url
                    
                    # Extract location if present
                    location_text = ""
                    for selector in [".location", ".city", "[class*='location']", "[class*='city']"]:
                        loc_elem = element.select_one(selector)
                        if loc_elem:
                            location_text = loc_elem.get_text(strip=True)
                            break
                    
                    location = location_text if location_text else "Budapest"
                    
                    # Extract description (full visible text up to 800 chars)
                    description = element.get_text(" ", strip=True)[:800]
                    
                    # Final validation: title should contain relevant keyword
                    if not any(kw in title.lower() for kw in keywords):
                        continue
                    
                    jobs.append({
                        "company": company_name,
                        "title": title,
                        "location": location,
                        "url": job_url,
                        "description_html": description,
                        "employment_type": "full-time",
                    })
                except Exception as e:
                    logger.debug(f"Error parsing job element: {e}")
                    continue
    
    except Exception as e:
        logger.warning(f"Error scraping {company_name} ({url}): {e}")
    
    return jobs


async def scrape_aimotive_greenhouse() -> list[dict]:
    """Scrape AiMotive jobs from Greenhouse."""
    return await scrape_greenhouse_board("aimotive", "AiMotive")


async def scrape_all_budapest_companies() -> list[dict]:
    """
    Scrape all target Budapest companies.
    Focuses on companies with known career page structures.
    """
    all_jobs = []
    
    company_urls = {
        "AiMotive": "https://www.aimotive.com/careers",
        "Zenitech": "https://zenitech.com/careers",
        "Turbine": "https://turbine.io/careers",
        "Siemens": "https://careers.siemens.com",
        "KUKA": "https://www.kuka.com/careers",
        "SAP": "https://careers.sap.com",
        "HCLTech": "https://www.hcltech.com/careers",
        "micro1": "https://micro1.ai/careers",
    }
    
    print("Scraping Budapest company career pages...")
    print("(This may take 30-60 seconds depending on page load times)\n")
    
    for company, url in company_urls.items():
        print(f"  {company:15s} ... ", end="", flush=True)
        try:
            jobs = await scrape_general_career_page(url, company)
            if jobs:
                print(f"✓ Found {len(jobs)} job(s)")
                all_jobs.extend(jobs)
            else:
                print(f"(no ML/AI jobs found)")
        except Exception as e:
            print(f"(error: {type(e).__name__})")
    
    # Try Greenhouse for AiMotive (higher success rate)
    print(f"\n  {'AiMotive (GH)':15s} ... ", end="", flush=True)
    try:
        gh_jobs = await scrape_aimotive_greenhouse()
        if gh_jobs:
            print(f"✓ Found {len(gh_jobs)} job(s)")
            all_jobs.extend(gh_jobs)
        else:
            print(f"(no jobs found)")
    except Exception as e:
        print(f"(error: {type(e).__name__})")
    
    return all_jobs


def save_jobs_to_csv(jobs: list[dict], output_path: Path) -> None:
    """
    Save scraped jobs to CSV file for import.
    
    Args:
        jobs: List of job dicts from scraper
        output_path: Path to save CSV file
    """
    import csv
    
    if not jobs:
        print("❌ No jobs to save")
        return
    
    # Extract plain text from HTML descriptions if needed
    cleaned_jobs = []
    for job in jobs:
        cleaned_job = job.copy()
        desc = cleaned_job.get("description_html", "")
        
        # Remove HTML tags
        if isinstance(desc, str):
            desc_clean = re.sub(r"<[^>]+>", " ", desc)
            desc_clean = re.sub(r"\s+", " ", desc_clean).strip()[:800]
            cleaned_job["description_html"] = desc_clean
        
        cleaned_jobs.append(cleaned_job)
    
    # Write CSV
    fieldnames = ["company", "title", "location", "url", "description_html", "seniority", "employment_type"]
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for job in cleaned_jobs:
            row = {
                "company": job.get("company", ""),
                "title": job.get("title", ""),
                "location": job.get("location", "Budapest"),
                "url": job.get("url", ""),
                "description_html": job.get("description_html", ""),
                "seniority": "mid",
                "employment_type": job.get("employment_type", "full-time"),
            }
            writer.writerow(row)
    
    print(f"✓ Saved {len(jobs)} jobs to {output_path}")


async def main():
    """Main entry point for scraping Budapest jobs."""
    jobs = await scrape_all_budapest_companies()
    
    if jobs:
        output_path = Path("budapest_jobs_scraped.csv")
        save_jobs_to_csv(jobs, output_path)
        print(f"\nScraped {len(jobs)} total jobs")
        print(f"Run: uv run job-finder import-jobs --csv {output_path}")
    else:
        print("No jobs scraped. Try visiting career pages manually.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
