import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import urlencode

from playwright.sync_api import Page, sync_playwright

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.sessions.encryption import decrypt_data


SESSION_FILE = os.path.join(os.path.dirname(__file__), "../../data/sessions/linkedin.enc")

LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs/search/"

REMOTE_FILTER = {"remote": "2", "onsite": "1", "hybrid": "3"}
DATE_FILTER = {"day": "r86400", "week": "r604800", "month": "r2592000"}


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    description: str = ""
    posted_date: str = ""
    employment_type: str = ""
    seniority_level: str = ""
    scraped_at: str = field(default_factory=lambda: datetime.now().isoformat())


class LinkedInScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless

    def _load_cookies(self) -> list[dict]:
        if not os.path.exists(SESSION_FILE):
            raise RuntimeError(
                "No LinkedIn session found. Run save_session('linkedin') first."
            )
        with open(SESSION_FILE, "rb") as f:
            encrypted = f.read()
        return json.loads(decrypt_data(encrypted))

    def _build_search_url(
        self,
        query: str,
        location: str,
        remote: str | None,
        date_posted: str | None,
    ) -> str:
        params: dict[str, str] = {"keywords": query, "location": location}
        if remote and remote in REMOTE_FILTER:
            params["f_WT"] = REMOTE_FILTER[remote]
        if date_posted and date_posted in DATE_FILTER:
            params["f_TPR"] = DATE_FILTER[date_posted]
        return f"{LINKEDIN_JOBS_URL}?{urlencode(params)}"

    def _scroll_to_load(self, page: Page, target: int) -> None:
        """Scroll the job list panel until we have at least `target` cards loaded."""
        prev_count = 0
        for _ in range(15):
            cards = page.query_selector_all("li.jobs-search-results__list-item")
            count = len(cards)
            if count >= target:
                break
            if count == prev_count:
                # Try "Load more" button if no new cards appeared
                btn = page.query_selector("button.infinite-scroller__show-more-button")
                if btn:
                    btn.click()
                    page.wait_for_timeout(2000)
                else:
                    break
            if cards:
                cards[-1].scroll_into_view_if_needed()
                page.wait_for_timeout(1500)
            prev_count = count

    def _collect_cards(self, page: Page, max_results: int) -> list[dict]:
        """Extract basic metadata from each job card in the search results."""
        self._scroll_to_load(page, max_results)

        cards = page.query_selector_all("li.jobs-search-results__list-item")
        jobs = []
        seen = set()

        for card in cards:
            if len(jobs) >= max_results:
                break
            try:
                link = card.query_selector("a.job-card-list__title--link") or \
                       card.query_selector("a.job-card-list__title")
                if not link:
                    continue

                raw_url = link.get_attribute("href") or ""
                url = raw_url.split("?")[0].strip()
                if not url or url in seen:
                    continue
                seen.add(url)

                title = link.inner_text().strip()

                company_el = card.query_selector(".job-card-container__company-name")
                company = company_el.inner_text().strip() if company_el else ""

                location_el = card.query_selector(".job-card-container__metadata-item")
                location = location_el.inner_text().strip() if location_el else ""

                date_el = card.query_selector("time")
                posted_date = date_el.get_attribute("datetime") if date_el else ""

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": url,
                    "posted_date": posted_date or "",
                })
            except Exception:
                continue

        return jobs

    def _extract_detail(self, page: Page, url: str) -> dict:
        """Visit a job page and extract full description and criteria."""
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(1000)

        # Expand truncated description if "Show more" button exists
        try:
            btn = page.query_selector(".jobs-description__footer-button")
            if btn:
                btn.click()
                page.wait_for_timeout(500)
        except Exception:
            pass

        description = ""
        desc_el = page.query_selector(".jobs-description__content") or \
                  page.query_selector(".jobs-description-content__text")
        if desc_el:
            description = desc_el.inner_text().strip()

        employment_type = ""
        seniority_level = ""
        for item in page.query_selector_all(".job-criteria__item"):
            label_el = item.query_selector(".job-criteria__subheader")
            value_el = item.query_selector(".job-criteria__text")
            if not label_el or not value_el:
                continue
            label = label_el.inner_text().strip().lower()
            value = value_el.inner_text().strip()
            if "employment" in label:
                employment_type = value
            elif "seniority" in label:
                seniority_level = value

        return {
            "description": description,
            "employment_type": employment_type,
            "seniority_level": seniority_level,
        }

    def search(
        self,
        query: str,
        location: str,
        remote: str | None = None,
        date_posted: str | None = None,
        max_results: int = 25,
        fetch_descriptions: bool = True,
    ) -> list[Job]:
        """
        Search LinkedIn Jobs and return structured job listings.

        Args:
            query:               Job title or keywords, e.g. "Frontend Engineer"
            location:            Location string, e.g. "Bangalore" or "Remote"
            remote:              Work type filter — "remote", "onsite", or "hybrid"
            date_posted:         Recency filter — "day", "week", or "month"
            max_results:         Cap on number of jobs returned (default 25)
            fetch_descriptions:  Visit each job page to get full description (default True)

        Returns:
            List of Job objects
        """
        cookies = self._load_cookies()

        p = sync_playwright().start()
        browser = p.chromium.launch(headless=self.headless)
        context = browser.new_context()
        context.add_cookies(cookies)

        try:
            page = context.new_page()
            search_url = self._build_search_url(query, location, remote, date_posted)

            print(f"Searching LinkedIn Jobs: {query} in {location}")
            page.goto(search_url, wait_until="domcontentloaded")

            # Bail early if session expired and LinkedIn redirected to login
            if "login" in page.url or "authwall" in page.url:
                raise RuntimeError(
                    "LinkedIn session expired. Re-run save_session('linkedin') to refresh."
                )

            page.wait_for_selector(
                "li.jobs-search-results__list-item", timeout=15000
            )

            cards = self._collect_cards(page, max_results)
            print(f"Found {len(cards)} listings")

            jobs: list[Job] = []
            for i, card in enumerate(cards):
                print(f"  [{i + 1}/{len(cards)}] {card['title']} @ {card['company']}")
                detail: dict = {}
                if fetch_descriptions:
                    try:
                        detail = self._extract_detail(page, card["url"])
                        time.sleep(1)  # polite delay between job page requests
                    except Exception as e:
                        print(f"    Could not fetch description: {e}")

                jobs.append(Job(
                    title=card["title"],
                    company=card["company"],
                    location=card["location"],
                    url=card["url"],
                    posted_date=card["posted_date"],
                    description=detail.get("description", ""),
                    employment_type=detail.get("employment_type", ""),
                    seniority_level=detail.get("seniority_level", ""),
                ))

            return jobs

        finally:
            browser.close()
            p.stop()
