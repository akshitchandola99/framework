from playwright.sync_api import sync_playwright
import pytest

from pathlib import Path

import logging

PROFILE_DIR = Path(__file__).resolve().parent / "chrome-profile"

log = logging.getLogger(__name__)


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
        log.info("Creating & handing over the page context")

        yield page

        log.info("Clearing page context")
        context.close()

@pytest.fixture(scope="session", autouse=True)
def ensure_logged_in(page):
        log.info("Navigating to https://airtap.ai/app")
        page.goto("https://airtap.ai/app")
        page.wait_for_load_state("domcontentloaded")
        log.info("Landed on %s", page.url)

        if "/login" not in page.url:
            log.info("User is logged in")
            return

        log.info("User is not logged in. Manual login required")
        pytest.exit("User is not logged in. Manual login required")









    







