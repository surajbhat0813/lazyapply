from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

from backend.scrapers.linkedin import LinkedInScraper
from backend.scrapers.naukri import NaukriScraper
from backend.scrapers.indeed import IndeedScraper
from backend.ai.scorer import JobScorer, UserProfile

router = APIRouter(prefix="/jobs", tags=["jobs"])


# ---------- Request / Response models ----------

class ProfileRequest(BaseModel):
    target_roles: list[str]
    skills: list[str]
    experience_years: int
    location: str
    remote_preference: str = "any"  # "remote" | "hybrid" | "onsite" | "any"
    summary: str = ""
    salary_min: int = 0
    salary_max: int = 0


class SearchRequest(BaseModel):
    platform: Literal["linkedin", "naukri", "indeed"] = "linkedin"
    query: str
    location: str
    remote: str | None = None        # "remote" | "hybrid" | "onsite"
    date_posted: str | None = None   # "day" | "week" | "month"
    max_results: int = Field(default=25, ge=1, le=50)
    fetch_descriptions: bool = True
    profile: ProfileRequest


class ScoredJobResponse(BaseModel):
    title: str
    company: str
    location: str
    url: str
    platform: str
    description: str
    posted_date: str
    employment_type: str
    seniority_level: str
    scraped_at: str
    score: int
    reasoning: str
    matching_skills: list[str]
    missing_skills: list[str]
    recommendation: str  # "apply" | "maybe" | "skip"


class SearchResponse(BaseModel):
    total: int
    results: list[ScoredJobResponse]


# ---------- Endpoints ----------

@router.post("/search", response_model=SearchResponse)
def search_and_score(req: SearchRequest) -> SearchResponse:
    """
    Scrape LinkedIn for jobs matching the query, then score each one
    against the provided user profile. Returns results ranked by score.
    """
    # 1. Scrape
    try:
        if req.platform == "linkedin":
            scraper = LinkedInScraper(headless=False)
        elif req.platform == "naukri":
            scraper = NaukriScraper(headless=False)
        else:
            scraper = IndeedScraper(headless=False)

        jobs = scraper.search(
            query=req.query,
            location=req.location,
            remote=req.remote,
            date_posted=req.date_posted,
            max_results=req.max_results,
            fetch_descriptions=req.fetch_descriptions,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {exc}") from exc

    if not jobs:
        return SearchResponse(total=0, results=[])

    # 2. Score
    profile = UserProfile(
        target_roles=req.profile.target_roles,
        skills=req.profile.skills,
        experience_years=req.profile.experience_years,
        location=req.profile.location,
        remote_preference=req.profile.remote_preference,
        summary=req.profile.summary,
        salary_min=req.profile.salary_min,
        salary_max=req.profile.salary_max,
    )
    try:
        scorer = JobScorer(profile)
        scored = scorer.score_all(jobs)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # 3. Shape response
    results = [
        ScoredJobResponse(
            title=s.job.title,
            company=s.job.company,
            location=s.job.location,
            url=s.job.url,
            platform=s.job.platform,
            description=s.job.description,
            posted_date=s.job.posted_date,
            employment_type=s.job.employment_type,
            seniority_level=s.job.seniority_level,
            scraped_at=s.job.scraped_at,
            score=s.score,
            reasoning=s.reasoning,
            matching_skills=s.matching_skills,
            missing_skills=s.missing_skills,
            recommendation=s.recommendation,
        )
        for s in scored
    ]

    return SearchResponse(total=len(results), results=results)
