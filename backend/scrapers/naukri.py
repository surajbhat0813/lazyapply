import os
import time
from urllib.parse import urlencode

from playwright.sync_api import Page, sync_playwright

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.scrapers.models import Job

PROFILE_DIR = os.path.join(os.path.dirname(__file__), "../../data/sessions/profiles/naukri")
NAUKRI_JOBS_URL = "https://www.naukri.com/jobs-in-india"

REMOTE_FILTER = {"remote": "5", "hybrid": "2", "onsite": "1"}
DATE_FILTER = {"day": "1", "week": "7", "month": "30"}

# Confirmed against live Naukri HTML (April 2025)
CARD_SELECTORS = ", ".join([
    "div.srp-jobtuple-wrapper",   # current primary
    ".cust-job-tuple",             # current inner
    "article.jobTuple",            # legacy
    "div[class*='srp-jobtuple']",  # fallback
    "div[class*='jobTuple']",      # fallback
])

TITLE_SELECTORS = [
    "a.title",                     # confirmed: class="title "
    ".row1 h2 a",
    ".row1 a",
    "h2 a",
    "a[href*='job-listings']",
]

COMPANY_SELECTORS = [
    "a.comp-name",                 # confirmed: class=" comp-name mw-25"
    ".comp-name",
    ".subTitle",
    "a.subTitle",
    ".row2 a",
]

LOCATION_SELECTORS = [
    ".locWdth",                    # confirmed in some pages
    ".loc-wrap span[title]",       # confirmed: <span title="Mohali">
    ".loc span",
    ".row3 span[title]",
    "[class*='location'] span",
]

DESC_SELECTORS = [
    ".job-desc",
    ".JDC",
    "[class*='job-description']",
    ".dang-inner-html",
    "[class*='jobDesc']",
    "#job_description",
    ".description__text",
]


class NaukriScraper:
    def __init__(self, headless: bool = False):
        self.headless = headless

    def _profile_exists(self) -> bool:
        return os.path.exists(PROFILE_DIR) and any(os.scandir(PROFILE_DIR))

    def _build_search_url(
        self,
        query: str,
        location: str,
        remote: str | None,
        date_posted: str | None,
        experience: int | None,
    ) -> str:
        params: dict[str, str] = {"k": query, "l": location}
        if remote and remote in REMOTE_FILTER:
            params["workType"] = REMOTE_FILTER[remote]
        if date_posted and date_posted in DATE_FILTER:
            params["jobAge"] = DATE_FILTER[date_posted]
        if experience is not None:
            params["experience"] = str(experience)
        return f"{NAUKRI_JOBS_URL}?{urlencode(params)}"

    def _dismiss_modal(self, page: Page) -> None:
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
        except Exception:
            pass
        for selector in ["[class*='close']", "[aria-label='close']", "[class*='modal'] button"]:
            try:
                btn = page.query_selector(selector)
                if btn and btn.is_visible():
                    btn.click()
                    page.wait_for_timeout(300)
                    break
            except Exception:
                continue

    def _find_cards(self, page: Page) -> list:
        return page.query_selector_all(CARD_SELECTORS)

    def _scroll_to_load(self, page: Page, target: int) -> None:
        prev_count = 0
        for _ in range(15):
            cards = self._find_cards(page)
            count = len(cards)
            if count >= target:
                break
            if count == prev_count:
                break
            if cards:
                cards[-1].scroll_into_view_if_needed()
                page.wait_for_timeout(1500)
            prev_count = count

    def _get_text(self, card, selectors: list[str]) -> str:
        for sel in selectors:
            try:
                el = card.query_selector(sel)
                if el:
                    return el.inner_text().strip()
            except Exception:
                continue
        return ""

    def _get_attr(self, card, selectors: list[str], attr: str) -> str:
        for sel in selectors:
            try:
                el = card.query_selector(sel)
                if el:
                    val = el.get_attribute(attr) or ""
                    if val:
                        return val.strip()
            except Exception:
                continue
        return ""

    def _collect_cards(self, page: Page, max_results: int) -> list[dict]:
        self._scroll_to_load(page, max_results)

        cards = self._find_cards(page)
        jobs = []
        seen = set()

        for card in cards:
            if len(jobs) >= max_results:
                break
            try:
                url = self._get_attr(card, TITLE_SELECTORS, "href")
                if not url:
                    continue
                url = url.split("?")[0].strip()
                if not url or url in seen:
                    continue
                seen.add(url)

                title = self._get_text(card, TITLE_SELECTORS)
                if not title:
                    continue

                company = self._get_text(card, COMPANY_SELECTORS)
                location = self._get_text(card, LOCATION_SELECTORS)
                posted_date = self._get_text(card, [".job-post-day", "[class*='date']", "[class*='freshness']"])

                jobs.append({
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": url,
                    "posted_date": posted_date,
                })
            except Exception:
                continue

        return jobs

    def _extract_detail(self, page: Page, url: str) -> dict:
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_timeout(2000)
        self._dismiss_modal(page)

        description = ""
        for sel in DESC_SELECTORS:
            el = page.query_selector(sel)
            if el:
                description = el.inner_text().strip()
                if description:
                    break

        employment_type = ""
        emp_el = page.query_selector("[class*='employment'], [class*='job-type'], [class*='jobType']")
        if emp_el:
            employment_type = emp_el.inner_text().strip()

        return {
            "description": description,
            "employment_type": employment_type,
            "seniority_level": "",
        }

    def search(
        self,
        query: str,
        location: str,
        remote: str | None = None,
        date_posted: str | None = None,
        experience: int | None = None,
        max_results: int = 25,
        fetch_descriptions: bool = True,
    ) -> list[Job]:
        use_profile = self._profile_exists()

        p = sync_playwright().start()

        if use_profile:
            context = p.chromium.launch_persistent_context(
                user_data_dir=PROFILE_DIR,
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
        else:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )

        try:
            page = context.new_page()
            search_url = self._build_search_url(query, location, remote, date_posted, experience)

            print(f"Searching Naukri: {query} in {location}")
            page.goto(search_url, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)
            self._dismiss_modal(page)

            # Wait for any known card selector to appear
            try:
                page.wait_for_selector(CARD_SELECTORS, timeout=25000)
            except Exception:
                # If no known selector found, dump what's visible to help debug
                print("  Warning: no job cards found with known selectors — page may have changed")
                return []

            cards = self._collect_cards(page, max_results)
            print(f"Found {len(cards)} listings")

            jobs: list[Job] = []
            for i, card in enumerate(cards):
                print(f"  [{i + 1}/{len(cards)}] {card['title']} @ {card['company']}")
                detail: dict = {}
                if fetch_descriptions:
                    try:
                        detail = self._extract_detail(page, card["url"])
                        time.sleep(1)
                    except Exception as e:
                        print(f"    Could not fetch description: {e}")

                jobs.append(Job(
                    title=card["title"],
                    company=card["company"],
                    location=card["location"],
                    url=card["url"],
                    platform="naukri",
                    posted_date=card["posted_date"],
                    description=detail.get("description", ""),
                    employment_type=detail.get("employment_type", ""),
                    seniority_level=detail.get("seniority_level", ""),
                ))

            return jobs

        finally:
            context.close()
            p.stop()
