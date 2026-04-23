import os
import shutil
from playwright.sync_api import sync_playwright

PROFILES_DIR = os.path.join(os.path.dirname(__file__), "../../data/sessions/profiles")
os.makedirs(PROFILES_DIR, exist_ok=True)

PLATFORMS = {
    "linkedin": "https://www.linkedin.com/login",
    "naukri": "https://www.naukri.com/nlogin/login",
    "indeed": "https://secure.indeed.com/auth"
}

PENDING_LOGINS = {}


def _get_profile_dir(platform: str) -> str:
    return os.path.join(PROFILES_DIR, platform)


def start_session_login(platform: str) -> bool:
    if platform in PENDING_LOGINS:
        return False

    profile_dir = _get_profile_dir(platform)
    os.makedirs(profile_dir, exist_ok=True)

    p = sync_playwright().start()
    context = p.chromium.launch_persistent_context(
        user_data_dir=profile_dir,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = context.new_page()
    page.goto(PLATFORMS[platform])

    PENDING_LOGINS[platform] = {
        "playwright": p,
        "context": context,
    }
    return True


def complete_session_login(platform: str) -> int | None:
    pending = PENDING_LOGINS.get(platform)
    if pending is None:
        return None

    cookie_count = len(pending["context"].cookies())
    pending["context"].close()
    pending["playwright"].stop()
    del PENDING_LOGINS[platform]
    return cookie_count


def cancel_session_login(platform: str) -> bool:
    pending = PENDING_LOGINS.get(platform)
    if pending is None:
        return False

    pending["context"].close()
    pending["playwright"].stop()
    del PENDING_LOGINS[platform]
    return True


def is_login_pending(platform: str) -> bool:
    return platform in PENDING_LOGINS


def verify_session(platform: str) -> dict[str, object] | None:
    profile_dir = _get_profile_dir(platform)
    if not os.path.exists(profile_dir) or not any(os.scandir(profile_dir)):
        return None

    return {
        "platform": platform,
        "saved": True,
        "valid": True,
        "profile_dir": profile_dir,
    }


def is_session_saved(platform: str) -> bool:
    profile_dir = _get_profile_dir(platform)
    return os.path.exists(profile_dir) and any(os.scandir(profile_dir))


def delete_session(platform: str):
    profile_dir = _get_profile_dir(platform)
    if os.path.exists(profile_dir):
        shutil.rmtree(profile_dir)
        print(f"Session deleted for {platform.capitalize()}.")
    else:
        print(f"No session found for {platform.capitalize()}.")


def save_session(platform: str):
    """CLI helper: open browser, let user log in, save profile."""
    print(f"\nOpening {platform.capitalize()} login page...")
    print("Log in manually in the browser window that opens.")
    print("Once fully logged in, come back here and press ENTER.\n")

    started = start_session_login(platform)
    if not started:
        print(f"Login already in progress for {platform.capitalize()}.")
        return

    input(f"Press ENTER after you have logged into {platform.capitalize()}...")
    cookie_count = complete_session_login(platform)
    print(f"Session saved for {platform.capitalize()}! ({cookie_count} cookies stored)")
