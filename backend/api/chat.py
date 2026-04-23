import json
import os
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field
from groq import Groq

from backend.scrapers.linkedin import LinkedInScraper
from backend.scrapers.naukri import NaukriScraper
from backend.scrapers.indeed import IndeedScraper
from backend.ai.scorer import JobScorer, UserProfile
from backend.database import get_connection, init_db

router = APIRouter(prefix="/chat", tags=["chat"])

init_db()

MODEL = "llama-3.3-70b-versatile"


def _get_groq() -> Groq:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY environment variable is not set")
    return Groq(api_key=key)


# ---------- Request / Response models ----------

class JobContext(BaseModel):
    title: str
    company: str
    location: str = ""
    url: str = ""
    platform: str = ""
    score: int | None = None
    recommendation: str = ""
    description: str = ""


class ProfileRequest(BaseModel):
    target_roles: list[str]
    skills: list[str]
    experience_years: int
    location: str
    remote_preference: str = "any"
    summary: str = ""
    salary_min: int = 0
    salary_max: int = 0


class ChatRequest(BaseModel):
    message: str
    platform: str = "naukri"
    date_posted: str | None = None
    max_results: int = Field(default=10, ge=1, le=30)
    profile: ProfileRequest
    last_jobs: list[JobContext] = []


class ChatResponse(BaseModel):
    type: str   # "search" | "message" | "saved" | "tracker_summary"
    content: str
    jobs: list[dict] = []
    saved_count: int = 0
    applications: list[dict] = []


# ---------- Intent detection ----------

INTENT_SYSTEM = """You are an intent classifier for a job hunting assistant chatbot.
Classify the user message into EXACTLY one intent and return JSON only — no extra text.

Intents:
- "search"  — user wants to find/search for jobs
- "save"    — user wants to save/bookmark one or more jobs from the last search results
- "tracker" — user wants to see their saved applications or tracker
- "apply"   — user wants to automatically apply to jobs
- "chat"    — greetings, questions about the tool, or anything else

JSON schema to return:
{
  "intent": "<search|save|tracker|apply|chat>",
  "query": "<extracted search query if intent=search, else null>",
  "save_all": <true if they want to save all last results, else false>,
  "job_indices": <[0-based indices] if they mention specific jobs like "first", "second", "the React one" — match to position in last results. null if unclear or save_all>,
  "reply": "<only fill this for intent=chat — a short, friendly response>"
}

Examples:
User: "find me react developer jobs in bangalore"
→ {"intent":"search","query":"react developer jobs in bangalore","save_all":false,"job_indices":null,"reply":null}

User: "save the first one"
→ {"intent":"save","query":null,"save_all":false,"job_indices":[0],"reply":null}

User: "save all of them"
→ {"intent":"save","query":null,"save_all":true,"job_indices":null,"reply":null}

User: "save the second and fourth"
→ {"intent":"save","query":null,"save_all":false,"job_indices":[1,3],"reply":null}

User: "show me my tracker" / "what jobs did i save?"
→ {"intent":"tracker","query":null,"save_all":false,"job_indices":null,"reply":null}

User: "can you apply for me?"
→ {"intent":"apply","query":null,"save_all":false,"job_indices":null,"reply":null}

User: "hi" / "how does this work?"
→ {"intent":"chat","query":null,"save_all":false,"job_indices":null,"reply":"..."}
"""


def detect_intent(message: str, last_jobs: list[JobContext]) -> dict:
    jobs_context = ""
    if last_jobs:
        lines = [f"{i+1}. {j.title} at {j.company}" for i, j in enumerate(last_jobs)]
        jobs_context = "\nLast shown jobs:\n" + "\n".join(lines)

    resp = _get_groq().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": INTENT_SYSTEM},
            {"role": "user", "content": message + jobs_context},
        ],
        temperature=0,
        max_tokens=256,
    )
    raw = resp.choices[0].message.content.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ---------- Handlers ----------

def _build_scraper(platform: str):
    if platform == "linkedin":
        return LinkedInScraper(headless=False)
    elif platform == "naukri":
        return NaukriScraper(headless=False)
    return IndeedScraper(headless=False)


def handle_search(req: ChatRequest, query: str) -> ChatResponse:
    scraper = _build_scraper(req.platform)
    try:
        jobs = scraper.search(
            query=query,
            location=req.profile.location,
            date_posted=req.date_posted,
            max_results=req.max_results,
            fetch_descriptions=True,
        )
    except Exception as e:
        return ChatResponse(
            type="message",
            content=f"Sorry, the scraper ran into an issue: {e}. Try again in a moment.",
        )

    if not jobs:
        return ChatResponse(
            type="message",
            content=f"No jobs found for that search on {req.platform}. Try different keywords or another platform.",
        )

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
    scored = JobScorer(profile).score_all(jobs)

    results = [
        {
            "title": s.job.title, "company": s.job.company, "location": s.job.location,
            "url": s.job.url, "platform": s.job.platform, "description": s.job.description,
            "posted_date": s.job.posted_date, "employment_type": s.job.employment_type,
            "seniority_level": s.job.seniority_level, "scraped_at": s.job.scraped_at,
            "score": s.score, "reasoning": s.reasoning,
            "matching_skills": s.matching_skills, "missing_skills": s.missing_skills,
            "recommendation": s.recommendation,
        }
        for s in scored
    ]

    content = f"Found **{len(results)} jobs** on {req.platform} matching your search. Here are the top results ranked by fit:"
    return ChatResponse(type="search", content=content, jobs=results)


def handle_save(last_jobs: list[JobContext], save_all: bool, indices: list[int] | None) -> ChatResponse:
    if not last_jobs:
        return ChatResponse(
            type="message",
            content="I don't have any recent search results to save. Run a job search first, then ask me to save.",
        )

    if save_all:
        targets = last_jobs
    elif indices:
        valid = [i for i in indices if 0 <= i < len(last_jobs)]
        if not valid:
            return ChatResponse(
                type="message",
                content=f"I couldn't match those positions. The last search returned {len(last_jobs)} jobs — try 'save the first one' or 'save all'.",
            )
        targets = [last_jobs[i] for i in valid]
    else:
        targets = last_jobs[:1]

    saved = 0
    already = 0
    with get_connection() as conn:
        for job in targets:
            existing = conn.execute(
                "SELECT id FROM applications WHERE url = ?", (job.url,)
            ).fetchone() if job.url else None

            if existing:
                already += 1
                continue

            conn.execute(
                """INSERT INTO applications
                   (title, company, location, url, platform, score, recommendation, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (job.title, job.company, job.location, job.url,
                 job.platform, job.score, job.recommendation, job.description),
            )
            saved += 1
        conn.commit()

    parts = []
    if saved:
        parts.append(f"Saved **{saved} job{'s' if saved > 1 else ''}** to your tracker.")
    if already:
        parts.append(f"{already} {'were' if already > 1 else 'was'} already saved.")
    parts.append("Go to the **Tracker** tab to manage them.")

    return ChatResponse(type="saved", content=" ".join(parts), saved_count=saved)


def handle_tracker() -> ChatResponse:
    with get_connection() as conn:
        apps = conn.execute(
            "SELECT * FROM applications ORDER BY saved_at DESC LIMIT 5"
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
        by_status = conn.execute(
            "SELECT status, COUNT(*) as c FROM applications GROUP BY status"
        ).fetchall()

    if total == 0:
        return ChatResponse(
            type="message",
            content="Your tracker is empty. Search for jobs and hit the bookmark icon (or ask me to save them) to start tracking.",
        )

    status_summary = ", ".join(f"{r['c']} {r['status']}" for r in by_status)
    content = f"You have **{total} application{'s' if total > 1 else ''}** saved — {status_summary}. Opening your tracker now."
    return ChatResponse(
        type="tracker_summary",
        content=content,
        applications=[dict(a) for a in apps],
    )


def handle_apply() -> ChatResponse:
    return ChatResponse(
        type="message",
        content=(
            "I can't auto-submit applications for you — most job platforms have protections against that, "
            "and applying manually means you can tailor each one. "
            "What I *can* do is save the best matches to your tracker so you have a list ready to apply to. "
            "Want me to save the jobs from the last search?"
        ),
    )


def handle_chat(reply: str) -> ChatResponse:
    if not reply:
        reply = "I'm your job hunting assistant. Ask me to search for jobs, save results, or check your tracker."
    return ChatResponse(type="message", content=reply)


# ---------- Main endpoint ----------

@router.post("", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    try:
        intent_data = detect_intent(req.message, req.last_jobs)
    except Exception:
        # Fallback: treat as search if intent detection fails
        return handle_search(req, req.message)

    intent = intent_data.get("intent", "chat")

    if intent == "search":
        query = intent_data.get("query") or req.message
        return handle_search(req, query)

    elif intent == "save":
        return handle_save(
            req.last_jobs,
            save_all=intent_data.get("save_all", False),
            indices=intent_data.get("job_indices"),
        )

    elif intent == "tracker":
        return handle_tracker()

    elif intent == "apply":
        return handle_apply()

    else:
        return handle_chat(intent_data.get("reply", ""))
