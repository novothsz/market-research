from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Optional

from job_finder.models import JobRecord


def _generate_job_hash(company: str, title: str, location: str) -> str:
    """Generate a consistent hash for a job posting."""
    key = f"{company.lower()}:{title.lower()}:{location.lower()}"
    return hashlib.sha256(key.encode()).hexdigest()[:16]


def import_jobs_from_csv(csv_path: Path) -> list[JobRecord]:
    """
    Import jobs from a CSV file.
    
    Expected CSV columns:
    - company (required)
    - title (required)
    - location (required)
    - url (optional)
    - description (optional)
    - seniority (optional)
    - employment_type (optional)
    
    Example:
        company,title,location,url,description,seniority
        AiMotive,AI Research Engineer,Budapest,https://...,Research and develop AI algorithms...,senior
    """
    jobs = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            company = row.get('company', '').strip()
            title = row.get('title', '').strip()
            location = row.get('location', '').strip()
            
            if not company or not title or not location:
                continue
            
            url = row.get('url', '').strip() or f"manual::{company}::{title}"
            description = row.get('description', '').strip()
            seniority = row.get('seniority', '').strip()
            employment_type = row.get('employment_type', '').strip()
            
            job_hash = _generate_job_hash(company, title, location)
            
            job = JobRecord(
                source="manual_import",
                company=company,
                title=title,
                url=url,
                location_raw=location,
                description_text=description,
                employment_type=employment_type or None,
                job_hash=job_hash,
            )
            jobs.append(job)
    
    return jobs


def import_jobs_from_json(json_path: Path) -> list[JobRecord]:
    """
    Import jobs from a JSON file.
    
    Expected JSON format:
    [
        {
            "company": "AiMotive",
            "title": "AI Research Engineer",
            "location": "Budapest",
            "url": "https://...",
            "description": "...",
            "seniority": "senior"
        }
    ]
    """
    jobs = []
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not isinstance(data, list):
        data = [data]
    
    for record in data:
        company = record.get('company', '').strip()
        title = record.get('title', '').strip()
        location = record.get('location', '').strip()
        
        if not company or not title or not location:
            continue
        
        url = record.get('url', f"manual::{company}::{title}")
        description = record.get('description', '').strip()
        seniority = record.get('seniority', '').strip()
        employment_type = record.get('employment_type', '').strip()
        
        job_hash = _generate_job_hash(company, title, location)
        
        job = JobRecord(
            source="manual_import",
            company=company,
            title=title,
            url=url,
            location_raw=location,
            description_text=description,
            employment_type=employment_type or None,
            job_hash=job_hash,
        )
        jobs.append(job)
    
    return jobs


def create_sample_import_csv(output_path: Path) -> None:
    """Create a sample CSV template for importing jobs."""
    sample_data = """company,title,location,url,description,seniority,employment_type
AiMotive,AI Research Engineer,Budapest,https://www.aimotive.com/careers,Research and develop artificial intelligence and machine learning algorithms for autonomous vehicle perception systems. Focus on computer vision, object detection, and deep learning for road structure detection and traffic sign recognition. Work with reinforcement learning for decision making in autonomous driving scenarios.,senior,full-time
Zenitech,GenAI Engineer,Budapest,https://zenitech.com/careers,Develop end-to-end generative AI features including backend API services, model integration, model monitoring and deployments. Integrate and optimize large language models (LLMs) for specific use cases in business planning. Work with prompt engineering, RAG (Retrieval-Augmented Generation) implementation, and machine learning model fine-tuning.,mid,full-time
Turbine,Senior ML Engineer,Budapest,https://turbine.io/careers,Tackle hard, unsolved machine learning and deep learning problems heavily infused with biology. Design and implement novel AI algorithms and systems. Work with scientific computing, neural networks, and advanced machine learning techniques.,senior,full-time
Siemens,AI Engineer,Budapest,https://careers.siemens.com,Develop AI and NLP methods and their practical applications. Select and apply appropriate solutions from prompt engineering and RAG approaches to fine-tuning of foundation models. Work with machine learning pipelines and AI systems.,mid,full-time
KUKA,AI Engineer,Budapest,https://www.kuka.com/careers,Develop artificial intelligence solutions for robotics applications. Focus on RAG (Retrieval-Augmented Generation) and LLM integration for robotic control systems. Work with machine learning, computer vision, and robotic process automation.,mid,full-time
SAP,Agentic AI Engineer,Budapest,https://careers.sap.com,Design and implement agentic AI systems and multi-agent architectures. Work on AI orchestration, agent-based machine learning systems, and distributed intelligence. Develop autonomous agents that use reinforcement learning and decision making.,senior,full-time
HCLTech,Senior ML Engineer,Budapest,https://www.hcltech.com/careers,Lead the design and architecture of complex large-scale machine learning systems. Focus on ML platform engineering, MLOps infrastructure, and machine learning operations. Design the infrastructure that trains, deploys, scales, and governs machine learning models.,senior,full-time
"""
    output_path.write_text(sample_data, encoding='utf-8')
