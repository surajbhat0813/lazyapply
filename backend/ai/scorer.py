import json
import os
import sys
from dataclasses import dataclass, field

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.scrapers.models import Job

from groq import Groq

MODEL = "llama-3.3-70b-versatile"

SCORE_SCHEMA = {
    "score": "integer 0-100 — overall fit",
    "reasoning": "1-2 sentence explanation",
    "matching_skills": "list of skills from the job that match the profile",
    "missing_skills": "list of important job requirements the candidate lacks",
    "recommendation": "'apply' | 'maybe' | 'skip'",
}


@dataclass
class UserProfile:
    target_roles: list[str]
    skills: list[str]
    experience_years: int
    location: str
    remote_preference: str  # "remote" | "hybrid" | "onsite" | "any"
    summary: str = ""
    salary_min: int = 0
    salary_max: int = 0


@dataclass
class ScoredJob:
    job: Job
    score: int
    reasoning: str
    matching_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)
    recommendation: str = "maybe"  # "apply" | "maybe" | "skip"


def _build_system_prompt(profile: UserProfile) -> str:
    roles = ", ".join(profile.target_roles)
    skills = ", ".join(profile.skills)
    salary_line = ""
    if profile.salary_min or profile.salary_max:
        salary_line = f"\nSalary expectation: {profile.salary_min}–{profile.salary_max}"

    return f"""You are a job-fit evaluator. Given a candidate profile and a job listing, score how well the job matches the candidate.

## Candidate Profile
Target roles: {roles}
Skills: {skills}
Experience: {profile.experience_years} years
Location: {profile.location}
Remote preference: {profile.remote_preference}{salary_line}
{f"Summary: {profile.summary}" if profile.summary else ""}

## Scoring Rules
- Score 80-100: Strong match — role, skills, and location all align well → recommend "apply"
- Score 50-79: Partial match — some gaps but worth considering → recommend "maybe"
- Score 0-49: Poor match — significant role/skill/location mismatch → recommend "skip"

## Output Format
Respond ONLY with a valid JSON object matching this exact schema:
{json.dumps(SCORE_SCHEMA, indent=2)}

No markdown fences, no extra keys, no explanation outside the JSON."""


def _build_user_message(job: Job) -> str:
    lines = [
        f"Title: {job.title}",
        f"Company: {job.company}",
        f"Location: {job.location}",
        f"Employment type: {job.employment_type or 'N/A'}",
        f"Seniority: {job.seniority_level or 'N/A'}",
    ]
    if job.description:
        lines.append(f"\nDescription:\n{job.description[:3000]}")
    return "\n".join(lines)


class JobScorer:
    def __init__(self, profile: UserProfile):
        self.profile = profile
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise RuntimeError("GROQ_API_KEY environment variable is not set.")
        self._client = Groq(api_key=api_key)
        self._system_prompt = _build_system_prompt(profile)

    def score(self, job: Job) -> ScoredJob:
        response = self._client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": _build_user_message(job)},
            ],
            max_tokens=512,
            temperature=0.1,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if the model adds them
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            start = raw.find("{")
            end = raw.rfind("}") + 1
            data = json.loads(raw[start:end])

        return ScoredJob(
            job=job,
            score=int(data.get("score", 0)),
            reasoning=data.get("reasoning", ""),
            matching_skills=data.get("matching_skills", []),
            missing_skills=data.get("missing_skills", []),
            recommendation=data.get("recommendation", "maybe"),
        )

    def score_all(self, jobs: list[Job]) -> list[ScoredJob]:
        results = []
        for i, job in enumerate(jobs):
            print(f"  Scoring [{i + 1}/{len(jobs)}] {job.title} @ {job.company}")
            try:
                scored = self.score(job)
                results.append(scored)
                print(f"    → {scored.score}/100 ({scored.recommendation})")
            except Exception as e:
                print(f"    → Error scoring job: {e}")
        results.sort(key=lambda s: s.score, reverse=True)
        return results
