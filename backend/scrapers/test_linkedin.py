"""
Quick smoke test for the LinkedIn scraper.
Run from anywhere:  python backend/scrapers/test_linkedin.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.scrapers.linkedin import LinkedInScraper

scraper = LinkedInScraper(headless=False)  # headless=False so you can see the browser

jobs = scraper.search(
    query="Software Engineer",
    location="Bangalore",
    remote="hybrid",
    date_posted="week",
    max_results=5,
    fetch_descriptions=True,
)

print(f"\n--- Results ({len(jobs)} jobs) ---")
for job in jobs:
    print(f"\n{job.title} @ {job.company}")
    print(f"  Location:    {job.location}")
    print(f"  Type:        {job.employment_type or 'N/A'}")
    print(f"  Seniority:   {job.seniority_level or 'N/A'}")
    print(f"  Posted:      {job.posted_date or 'N/A'}")
    print(f"  URL:         {job.url}")
    print(f"  Description: {job.description[:200]}..." if job.description else "  Description: N/A")
