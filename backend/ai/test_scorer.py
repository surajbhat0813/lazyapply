"""
Smoke test for the AI scoring layer.
Uses mock Job objects so no LinkedIn session is required.

Run from anywhere:  python backend/ai/test_scorer.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.scrapers.linkedin import Job
from backend.ai.scorer import JobScorer, UserProfile

PROFILE = UserProfile(
    target_roles=["Software Engineer", "Backend Engineer", "Python Developer"],
    skills=["Python", "FastAPI", "PostgreSQL", "Docker", "REST APIs", "React"],
    experience_years=3,
    location="Bangalore",
    remote_preference="hybrid",
    summary="Backend engineer focused on Python and API development.",
)

MOCK_JOBS = [
    Job(
        title="Senior Backend Engineer",
        company="Acme Corp",
        location="Bangalore, Karnataka, India",
        url="https://www.linkedin.com/jobs/view/1",
        employment_type="Full-time",
        seniority_level="Senior",
        description=(
            "We are looking for a Senior Backend Engineer with strong Python and FastAPI skills. "
            "You will design and build REST APIs, work with PostgreSQL databases, and deploy "
            "services using Docker and Kubernetes. Hybrid work model in Bangalore."
        ),
    ),
    Job(
        title="iOS Mobile Developer",
        company="App Studio",
        location="Mumbai, Maharashtra, India",
        url="https://www.linkedin.com/jobs/view/2",
        employment_type="Full-time",
        seniority_level="Mid-Senior",
        description=(
            "Seeking an experienced iOS developer with Swift and Objective-C expertise. "
            "You'll build native mobile apps and work with Xcode and Apple frameworks. "
            "Onsite only in Mumbai."
        ),
    ),
    Job(
        title="Python Developer",
        company="Startup XYZ",
        location="Remote",
        url="https://www.linkedin.com/jobs/view/3",
        employment_type="Full-time",
        seniority_level="Associate",
        description=(
            "Looking for a Python developer to build automation scripts and data pipelines. "
            "Familiarity with Django or FastAPI is a plus. Fully remote position."
        ),
    ),
]


def main():
    print("=== AI Job Scorer Smoke Test ===\n")
    print(f"Profile: {', '.join(PROFILE.target_roles)}")
    print(f"Skills: {', '.join(PROFILE.skills)}\n")

    scorer = JobScorer(PROFILE)
    results = scorer.score_all(MOCK_JOBS)

    print("\n--- Ranked Results ---")
    for r in results:
        print(f"\n[{r.score}/100] {r.job.title} @ {r.job.company}  →  {r.recommendation.upper()}")
        print(f"  {r.reasoning}")
        if r.matching_skills:
            print(f"  Matching: {', '.join(r.matching_skills)}")
        if r.missing_skills:
            print(f"  Missing:  {', '.join(r.missing_skills)}")


if __name__ == "__main__":
    main()
