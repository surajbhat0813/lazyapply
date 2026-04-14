import os
import json
from playwright.sync_api import sync_playwright
from encryption import encrypt_data, decrypt_data

# Where we save session files
SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "../../data/sessions")

# Make sure the sessions folder exists
os.makedirs(SESSIONS_DIR, exist_ok=True)

#dictionary of platforms and their login URLs for easy access - object-oriented approach to avoid hardcoding URLs in multiple places
PLATFORMS = {
    "linkedin": "https://www.linkedin.com/login",
    "naukri": "https://www.naukri.com/nlogin/login",
    "indeed": "https://secure.indeed.com/auth"
}


def save_session(platform: str):
    """
    Opens a real browser window, lets the user log in manually,
    then saves their session cookies encrypted to disk.
    """
    print(f"\n🌐 Opening {platform.capitalize()} login page...")
    print("👉 Please log in manually in the browser window that opens.")
    print("✅ Once you are fully logged in, come back here and press ENTER.\n")

    with sync_playwright() as p:
        # headless=False means the browser window is visible
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        # Go to the platform's login page
        page.goto(PLATFORMS[platform])

        # Wait for the user to log in manually
        input(f"Press ENTER after you have logged into {platform.capitalize()}...")

        # Grab all cookies from the session
        cookies = context.cookies()

        # Encrypt and save to disk
        session_data = json.dumps(cookies)
        encrypted = encrypt_data(session_data)

        session_file = os.path.join(SESSIONS_DIR, f"{platform}.enc")
        with open(session_file, "wb") as f:
            f.write(encrypted)

        print(f"✅ Session saved for {platform.capitalize()}!")
        browser.close()


def load_session(platform: str):
    """
    Loads a saved encrypted session and returns an active browser context.
    Returns None if no session exists.
    """
    session_file = os.path.join(SESSIONS_DIR, f"{platform}.enc")

    if not os.path.exists(session_file):
        print(f"⚠️  No saved session found for {platform.capitalize()}.")
        print(f"    Run save_session('{platform}') first.")
        return None, None

    # Read and decrypt the session file
    with open(session_file, "rb") as f:
        encrypted = f.read()

    session_data = decrypt_data(encrypted)
    cookies = json.loads(session_data)

    # Launch browser and inject the saved cookies
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    context.add_cookies(cookies)

    print(f"✅ Session loaded for {platform.capitalize()}!")
    return p, browser, context


def is_session_saved(platform: str) -> bool:
    """
    Simple check — does a saved session file exist for this platform?
    """
    session_file = os.path.join(SESSIONS_DIR, f"{platform}.enc")
    return os.path.exists(session_file)


def delete_session(platform: str):
    """
    Deletes the saved session for a platform.
    User will need to log in again next time.
    """
    session_file = os.path.join(SESSIONS_DIR, f"{platform}.enc")

    if os.path.exists(session_file):
        os.remove(session_file)
        print(f"🗑️  Session deleted for {platform.capitalize()}.")
    else:
        print(f"⚠️  No session found for {platform.capitalize()}.")
