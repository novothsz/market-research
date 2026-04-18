# Budapest Job Discovery - Improvements Summary

## What Was Changed

### 1. **Relaxed Relevance Threshold** ✅
- **Before**: Jobs needed score ≥ 55.0 to be considered relevant
- **After**: Jobs need score ≥ 50.0 for Budapest location
- **Result**: AiMotive (81.5) and KUKA (60.0) now pass the threshold

### 2. **Expanded Search Terms** ✅
Added new keywords matching your interests:

#### Direct RL Terms (worth 18 pts each)
- `autonomous vehicle` 
- `autonomous driving`
- `self-driving`
- `motion planning`

#### Adjacent ML Terms (worth 6.5 pts each)
- `control systems`
- `trajectory optimization`
- `motion control`
- `autonomous systems`
- `perception systems`
- `computer vision`
- `path planning`

#### Robotics/Control Terms
- `vehicle autonomy`
- `robot`
- `av`

### 3. **Web Scraper Infrastructure** ✅
Added automated job scraping with:
- **Greenhouse API integration** for AiMotive
- **General career page scraper** with robust HTML parsing
- **Proper user-agent headers** to avoid blocking
- **Async/concurrent collection** for speed
- **Better error handling** with detailed logging

### 4. **New CLI Command** ✅
```bash
uv run job-finder scrape-budapest
```
Automatically scrapes these companies:
- AiMotive (autonomous vehicles)
- Zenitech (GenAI)
- Turbine (biology + ML)
- Siemens (NLP/AI)
- SAP (agentic AI)
- KUKA (robotics AI)
- HCLTech (MLOps)
- micro1 (community detection)

## Results

### Before Changes
```
53.5 | NO  | KUKA            | AI Engineer
50.5 | NO  | AiMotive        | AI Research Engineer
47.5 | NO  | Siemens         | AI Engineer
47.5 | NO  | HCLTech         | Senior ML Engineer
38.0 | NO  | SAP             | Agentic AI Engineer
26.0 | NO  | Zenitech        | GenAI Engineer
26.0 | NO  | Turbine         | Senior ML Engineer
```

### After Changes
```
81.5 | YES | AiMotive        | AI Research Engineer  ← +31 points!
60.0 | YES | KUKA            | AI Engineer           ← +6.5 points
47.5 | NO  | Siemens         | AI Engineer
47.5 | NO  | HCLTech         | Senior ML Engineer
38.0 | NO  | SAP             | Agentic AI Engineer
26.0 | NO  | Zenitech        | GenAI Engineer
26.0 | NO  | Turbine         | Senior ML Engineer
```

### Budapest Shortlist
2 jobs now appear in shortlist:
```
# Job Shortlist - Budapest

## 1. AI Research Engineer
- Company: AiMotive
- Score: 81.5
- Matched signals: autonomous vehicle, budapest, computer vision, engineer, 
  learning, machine learning, perception systems, research

## 2. AI Engineer
- Company: KUKA
- Score: 60.0
- Matched signals: budapest, control systems, engineer, learning, 
  machine learning, robot, robotics
```

## How to Use

### Option 1: Automatic Web Scraping
```bash
# Scrape all 8 companies automatically
uv run job-finder scrape-budapest

# Review results
less budapest_jobs_scraped.csv

# Import into database
uv run job-finder import-jobs --csv budapest_jobs_scraped.csv

# Classify and export
uv run job-finder classify -c config.toml --prompt-file prompt.txt \
  --profile-file "examples/CV 2026.pdf" --all

uv run job-finder export-by-location -c config.toml -o data
```

### Option 2: Manual Collection (More Reliable)
```bash
# Generate search guide with company URLs
uv run job-finder search-guide

# Review budapest_search_guide.md
less budapest_search_guide.md

# Manually collect jobs into CSV (using guide)
# Then import:
uv run job-finder import-jobs --csv budapest_jobs.csv

# Continue from there
uv run job-finder classify -c config.toml --prompt-file prompt.txt \
  --profile-file "examples/CV 2026.pdf" --all

uv run job-finder export-by-location -c config.toml -o data
```

## Key Improvements Explained

### Why AiMotive jumped from 50.5 → 81.5?
- New `autonomous vehicle` term added to direct RL terms = +18 pts
- Descriptions mentions "autonomous vehicles" + "computer vision" = matched key signals
- Total: 50.5 + 18 + additional keyword matching = 81.5

### Why KUKA improved from 53.5 → 60.0?
- New `control systems` term added = +6.5 pts  
- New category matching for robotics/control terms
- Now recognized as "robotics_or_control" category
- Total: 53.5 + 6.5 = 60.0 (above 50 threshold)

## What's Next?

1. **Use the scraper** to collect more Budapest jobs automatically, OR
2. **Manual collection** using the search guide for guaranteed coverage
3. Enrich job descriptions with more content from career pages
4. Import into database and reclassify
5. Generate updated shortlists

The threshold relaxation is permanent for Budapest, so as you import more jobs, they'll be evaluated at the 50-point threshold instead of 55.

## Technical Details

- **Files modified**: 
  - `src/job_finder/ranking/rules.py` - Lower threshold & expand terms
  - `src/job_finder/cli.py` - Add asyncio import & scrape command
  - Added `src/job_finder/collectors/scraper.py` - Web scraping infrastructure

- **Dependencies already available**:
  - `httpx` for async HTTP requests
  - `beautifulsoup4` for HTML parsing
  - `asyncio` for concurrent operations

- **Command added**: `scrape-budapest` (with `--output` option)

All changes committed to git. ✅
