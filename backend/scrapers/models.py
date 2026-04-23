from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    platform: str = ""
    description: str = ""
    posted_date: str = ""
    employment_type: str = ""
    seniority_level: str = ""
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())
