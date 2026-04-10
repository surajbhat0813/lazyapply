from session_manager import save_session, load_session, is_session_saved

# ---- STEP 1: Save sessions ----
# Run this first. It will open a browser for each platform.
# Log in manually, then press ENTER.

# Uncomment one at a time to test:
save_session("linkedin")
# save_session("naukri")
# save_session("indeed")


# ---- STEP 2: Test loading a saved session ----
# After saving, test that the session loads correctly.

# p, browser, context = load_session("linkedin")
# if context:
#     page = context.new_page()
#     page.goto("https://www.linkedin.com/feed")  # should open logged-in feed
#     input("Press ENTER to close browser...")
#     browser.close()
#     p.stop()
