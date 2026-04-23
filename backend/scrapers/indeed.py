import os
import time
from urllib.parse import urlencode

from playwright.sync_api import Page, sync_playwright

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.scrapers.models import Job

PROFILE_DIR = os.path.join(os.path.dirname(__file__), "../../data/sessions/profiles/indeed")
INDEED_JOBS_URL = "https://in.indeed.com/jobs"

DATE_FILTER = {"day": "1", "week": "7", "month": "30"}


class IndeedScraper:
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
    ) -> str:
        params: dict[str, str] = {"q": query, "l": location, "sort": "date"}
        if remote == "remote":
            params["remotejob"] = "1"
        if date_posted and date_posted in DATE_FILTER:
            params["fromage"] = DATE_FILTER[date_posted]
        return f"{INDEED_JOBS_URL}?{urlencode(params)}"

    def _dismiss_modal(self, page: Page) -> None:
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
        except Exception:
            pass
        try:
            btn = (
                page.query_selector("[aria-label='close']") or
                page.query_selector("button[id*='close']") or
                page.query_selector(".icl-CloseButton")
            )
            if btn:
                btn.click()
                page.wait_for_timeout(300)
        except Exception:
            pass

    def _scroll_to_load(self, page: Page, target: int) -> None:
        prev_count = 0
        for _ in range(10):
            cards = page.query_selector_all("li.css-5lfssm, div.job_seen_beacon, .resultContent")
            count = len(cards)
            if count >= target:
                break
            if count == prev_count:
                # Try next page button
                btn = page.query_selector("[aria-label='Next Page'], [data-testid='pagination-page-next']")
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
        self._scroll_to_load(page, max_results)

        cards = page.query_selector_all("li.css-5lfssm, div.job_seen_beacon, .resultContent")
        jobs = []
        seen = set()

        for card in cards:
            if len(jobs) >= max_results:
                break
            try:
                link = (
                    card.query_selector("h2.jobTitle a") or
                    card.query_selector("a[id^='job_']") or
                    card.query_selector("a[data-jk]")
                )
                if not link:
                    continue

                href = link.get_attribute("href") or ""
                if href.startswith("/"):
                    href = f"https://in.indeed.com{href}"
                url = href.split("?")[0].strip()
                if not url or url in seen:
                    continue
                seen.add(url)

                title_el = card.query_selector("h2.jobTitle span, h2.jobTitle")
                title = title_el.inner_text().strip() if title_el else link.inner_text().strip()

                company_el = (
                    card.query_selector("span.companyName") or
                    card.query_selector("[data-testid='company-name']")
                )
                company = company_el.inner_text().strip() if company_el else ""

                location_el = (
                    card.query_selector("div.companyLocation") or
                    card.query_selector("[data-testid='text-location']")
                )
                location = location_el.inner_text().strip() if location_el else ""

                date_el = card.query_selector("span.date, [data-testid='myJobsStateDate']")
                posted_date = date_el.inner_text().strip() if date_el else ""

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
        page.wait_for_timeout(1500)
        self._dismiss_modal(page)

        description = ""
        desc_el = (
            page.query_selector("#jobDescriptionText") or
            page.query_selector(".jobsearch-jobDescriptionText") or
            page.query_selector("[data-testid='jobsearch-JobComponent-description']")
        )
        if desc_el:
            description = desc_el.inner_text().strip()

        employment_type = ""
        emp_el = page.query_selector("[data-testid='job-type-label'], .jobsearch-JobMetadataHeader-item")
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
            search_url = self._build_search_url(query, location, remote, date_posted)

            print(f"Searching Indeed: {query} in {location}")
            page.goto(search_url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            self._dismiss_modal(page)

            page.wait_for_selector(
                "li.css-5lfssm, div.job_seen_beacon, .resultContent", timeout=20000
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
                        time.sleep(1)
                    except Exception as e:
                        print(f"    Could not fetch description: {e}")

                jobs.append(Job(
                    title=card["title"],
                    company=card["company"],
                    location=card["location"],
                    url=card["url"],
                    platform="indeed",
                    posted_date=card["posted_date"],
                    description=detail.get("description", ""),
                    employment_type=detail.get("employment_type", ""),
                    seniority_level=detail.get("seniority_level", ""),
                ))

            return jobs

        finally:
            context.close()
            p.stop()
