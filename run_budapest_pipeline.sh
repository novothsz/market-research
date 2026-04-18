#!/bin/bash

# Budapest Job Discovery Pipeline
# Combines web scraping + manual collection + classification + export + PDF conversion

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════════"
echo "🚀 Budapest ML/AI Job Discovery Pipeline"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Step 1: Generate search guide for manual collection
echo "📋 Step 1: Generating search guide for manual collection..."
uv run job-finder search-guide || true
echo "✓ Search guide created: budapest_search_guide.md"
echo ""

# Step 2: Attempt web scraping
echo "🌐 Step 2: Attempting web scraping from career pages..."
echo "   (This may take 30-60 seconds...)"
uv run job-finder scrape-budapest --output budapest_jobs_scraped.csv || true
echo ""

# Step 3: Check what jobs we have
echo "📊 Step 3: Checking collected jobs..."

SCRAPED_COUNT=0
MANUAL_COUNT=0

if [ -f "budapest_jobs_scraped.csv" ]; then
    SCRAPED_COUNT=$(tail -n +2 budapest_jobs_scraped.csv | wc -l)
    if [ "$SCRAPED_COUNT" -gt 0 ]; then
        echo "   ✓ Found $SCRAPED_COUNT jobs from web scraping"
    fi
fi

if [ -f "budapest_jobs.csv" ]; then
    MANUAL_COUNT=$(tail -n +2 budapest_jobs.csv | wc -l)
    if [ "$MANUAL_COUNT" -gt 0 ]; then
        echo "   ✓ Found $MANUAL_COUNT jobs from manual collection (budapest_jobs.csv)"
    fi
fi

if [ "$SCRAPED_COUNT" -eq 0 ] && [ "$MANUAL_COUNT" -eq 0 ]; then
    echo "   ⚠️  No jobs found yet."
    echo "   Please manually add jobs to budapest_jobs.csv using the search guide,"
    echo "   or website scraping may have encountered connection issues."
    echo ""
    echo "   To manually collect:"
    echo "   1. Review: less budapest_search_guide.md"
    echo "   2. Visit company career pages and copy job details"
    echo "   3. Save to: budapest_jobs.csv"
    echo "   4. Re-run this script"
    exit 1
fi

echo ""

# Step 4: Import jobs
echo "📥 Step 4: Importing collected jobs into database..."

if [ -f "budapest_jobs_scraped.csv" ] && [ "$SCRAPED_COUNT" -gt 0 ]; then
    echo "   Importing from web scraping..."
    uv run job-finder import-jobs --csv budapest_jobs_scraped.csv
fi

if [ -f "budapest_jobs.csv" ] && [ "$MANUAL_COUNT" -gt 0 ]; then
    echo "   Importing from manual collection..."
    uv run job-finder import-jobs --csv budapest_jobs.csv
fi

echo ""

# Step 5: Classify jobs
echo "🤖 Step 5: Classifying jobs against your profile..."
echo "   (Using your CV and search criteria...)"
if [ -f "config.toml" ]; then
    uv run job-finder classify -c config.toml --prompt-file prompt.txt --profile-file "examples/CV 2026.pdf" --all
else
    uv run job-finder classify --prompt-file prompt.txt --profile-file "examples/CV 2026.pdf" --all
fi
echo ""

# Step 6: Export by location
echo "📍 Step 6: Exporting jobs by location..."
if [ -f "config.toml" ]; then
    uv run job-finder export-by-location -c config.toml -o data
else
    uv run job-finder export-by-location -o data
fi
echo ""

# Step 7: Convert to PDF
echo "📄 Step 7: Converting shortlists to PDF..."
uv run job-finder export-pdf -d data
echo ""

# Step 8: Summary
echo "════════════════════════════════════════════════════════════════"
echo "✅ Pipeline Complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📁 Results are available in:"
echo "   📊 Shortlists (Markdown): data/markdown/"
echo "   📄 Shortlists (PDF):      data/pdf/"
echo ""
echo "View your results:"
echo "   less data/markdown/shortlist_budapest.md"
echo "   open data/pdf/shortlist_budapest.pdf"
echo ""
