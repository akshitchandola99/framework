from playwright.sync_api import sync_playwright
import pytest

from pathlib import Path
import json

PROFILE_DIR = Path(__file__).resolve().parent / "chrome-profile"


@pytest.fixture(scope="session")
def page():
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
                user_data_dir = PROFILE_DIR ,
                headless = False,
                slow_mo=3000,
                channel="chrome",
                no_viewport=True,
                args=["--start-maximized"],
                ignore_default_args=["--enable-automation","--no-sandbox"])

        page = context.pages[0] if context.pages else context.new_page()

        yield page

        context.close()

@pytest.fixture(scope="session", autouse=True)
def ensure_logged_in(page):
        page.goto("https://airtap.ai/app")
        page.wait_for_load_state("domcontentloaded")

        if "/login" not in page.url:
            print("User is logged in")
            return

        print("User is not logged in.")
        pytest.exit("Login Failed. Stopping pytest execution")










    






