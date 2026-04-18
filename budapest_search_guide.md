# Budapest ML/AI Job Search Guide

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
