import re
from dataclasses import dataclass

from backend.scrapers.models import Job

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
URL_RE = re.compile(r"https?://(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})")

# Addresses/domains that show up in descriptions but aren't a real HR contact
BLOCKED_EMAIL_SUBSTRINGS = ("noreply", "no-reply", "donotreply", "do-not-reply", "notifications@")
BLOCKED_DOMAINS = {
    "linkedin.com", "indeed.com", "naukri.com", "glassdoor.com", "example.com",
    "sentry.io", "wixpress.com", "google.com", "cloudflare.com", "w3.org",
    "schema.org", "gstatic.com", "googleapis.com",
}
BLOCKED_IMAGE_EXTS = {"png", "jpg", "jpeg", "gif", "svg", "webp"}
GENERIC_ALIAS = "careers"


@dataclass
class ContactInfo:
    email: str | None = None
    source: str = "none"        # "extracted" | "inferred" | "none"
    confidence: str = "none"    # "high" | "low" | "none"
    note: str = ""


class ContactExtractor:
    """Finds a recruiter contact email in a job description, or infers a
    plausible generic one from a company domain mentioned in the text.

    Deliberately regex-based rather than LLM-based: hallucinating a contact
    email is worse than reporting none, so extraction stays deterministic.
    """

    def extract(self, job: Job) -> ContactInfo:
        text = job.description or ""

        email = self._find_email(text)
        if email:
            return ContactInfo(
                email=email,
                source="extracted",
                confidence="high",
                note="Found directly in the job listing.",
            )

        domain = self._find_company_domain(text)
        if domain:
            guess = f"{GENERIC_ALIAS}@{domain}"
            return ContactInfo(
                email=guess,
                source="inferred",
                confidence="low",
                note=f"No contact email listed. This is an unverified guess based on the domain {domain} found in the listing.",
            )

        return ContactInfo()

    def _find_email(self, text: str) -> str | None:
        for match in EMAIL_RE.findall(text):
            lower = match.lower()
            if any(b in lower for b in BLOCKED_EMAIL_SUBSTRINGS):
                continue
            domain = lower.split("@")[-1]
            if domain in BLOCKED_DOMAINS:
                continue
            ext = domain.rsplit(".", 1)[-1]
            if ext in BLOCKED_IMAGE_EXTS:
                continue
            return match
        return None

    def _find_company_domain(self, text: str) -> str | None:
        for match in URL_RE.findall(text):
            domain = match.lower()
            if domain in BLOCKED_DOMAINS or any(domain.endswith(f".{b}") or domain == b for b in BLOCKED_DOMAINS):
                continue
            return domain
        return None
