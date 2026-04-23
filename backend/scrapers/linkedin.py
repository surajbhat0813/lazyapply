import os
import time
from urllib.parse import urlencode

from playwright.sync_api import Page, sync_playwright

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from backend.scrapers.models import Job

PROFILE_DIR = os.path.join(os.path.dirname(__file__), "../../data/sessions/profiles/linkedin")

LINKEDIN_JOBS_URL = "https://www.linkedin.com/jobs/search/"

REMOTE_FILTER = {"remote": "2", "onsite": "1", "hybrid": "3"}
DATE_FILTER = {"day": "r86400", "week": "r604800", "month": "r2592000"}

# Selectors that work for both authenticated and guest (public) views
AUTH_CARD = "li.jobs-search-results__list-item"
GUEST_CARD = "li.job-search-card"
ANY_CARD = f"{AUTH_CARD}, {GUEST_CARD}"



class LinkedInScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless

    def _check_profile(self) -> None:
        if not os.path.exists(PROFILE_DIR) or not any(os.scandir(PROFILE_DIR)):
            raise RuntimeError(
                "No LinkedIn session found. Use POST /sessions/linkedin/save/start to log in first."
            )

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

    def _dismiss_modal(self, page: Page) -> None:
        """Close any sign-in modal that appears over job results."""
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
        except Exception:
            pass
        try:
            btn = (
                page.query_selector("button.modal__dismiss") or
                page.query_selector("[aria-label='Dismiss']") or
                page.query_selector("button[data-tracking-control-name*='dismiss']") or
                page.query_selector("button[data-tracking-control-name*='modal']") or
                page.query_selector("icon[type='cancel']")
            )
            if btn:
                btn.click()
                page.wait_for_timeout(500)
        except Exception:
            pass

    def _scroll_to_load(self, page: Page, target: int) -> None:
        """Scroll the job list panel until we have at least `target` cards loaded."""
        prev_count = 0
        for _ in range(15):
            cards = page.query_selector_all(ANY_CARD)
            count = len(cards)
            if count >= target:
                break
            if count == prev_count:
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
        """Extract basic metadata from each job card — handles both auth and guest layouts."""
        self._scroll_to_load(page, max_results)

        cards = page.query_selector_all(ANY_CARD)
        jobs = []
        seen = set()

        for card in cards:
            if len(jobs) >= max_results:
                break
            try:
                # Authenticated card layout
                link = (
                    card.query_selector("a.job-card-list__title--link") or
                    card.query_selector("a.job-card-list__title")
                )
                if link:
                    raw_url = link.get_attribute("href") or ""
                    title = link.inner_text().strip()
                    company_el = card.query_selector(".job-card-container__company-name")
                    company = company_el.inner_text().strip() if company_el else ""
                    location_el = card.query_selector(".job-card-container__metadata-item")
                    location = location_el.inner_text().strip() if location_el else ""
                else:
                    # Guest card layout
                    link = card.query_selector("a.base-card__full-link")
                    if not link:
                        continue
                    raw_url = link.get_attribute("href") or ""
                    title_el = card.query_selector("h3.base-search-card__title")
                    title = title_el.inner_text().strip() if title_el else ""
                    company_el = card.query_selector(".base-search-card__subtitle")
                    company = company_el.inner_text().strip() if company_el else ""
                    location_el = card.query_selector(".job-search-card__location")
                    location = location_el.inner_text().strip() if location_el else ""

                url = raw_url.split("?")[0].strip()
                if not url or url in seen:
                    continue
                seen.add(url)

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

        self._dismiss_modal(page)

        try:
            btn = page.query_selector(".jobs-description__footer-button")
            if btn:
                btn.click()
                page.wait_for_timeout(500)
        except Exception:
            pass

        description = ""
        desc_el = (
            page.query_selector(".jobs-description__content") or
            page.query_selector(".jobs-description-content__text") or
            page.query_selector(".description__text")
        )
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
        self._check_profile()

        p = sync_playwright().start()
        context = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=self.headless,
            args=["--disable-blink-features=AutomationControlled"],
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        try:
            page = context.new_page()
            search_url = self._build_search_url(query, location, remote, date_posted)

            print(f"Searching LinkedIn Jobs: {query} in {location}")
            page.goto(search_url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)

            if "login" in page.url or "authwall" in page.url:
                raise RuntimeError(
                    "LinkedIn session expired. Re-run save_session('linkedin') to refresh."
                )

            self._dismiss_modal(page)

            page.wait_for_selector(ANY_CARD, timeout=20000)

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
                    platform="linkedin",
                    posted_date=card["posted_date"],
                    description=detail.get("description", ""),
                    employment_type=detail.get("employment_type", ""),
                    seniority_level=detail.get("seniority_level", ""),
                ))

            return jobs

        finally:
            context.close()
            p.stop()
