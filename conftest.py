import logging
import re

import pytest
from playwright.sync_api import expect, sync_playwright

from config.settings import APP_URL, DEFAULT_TIMEOUT, PROFILE_DIR, TASK_URL_PATTERN
from pages.base_page import BasePage
from pages.task_page import TaskPage

log = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def page():
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            channel="chrome",
            no_viewport=True,
            args=["--start-maximized"],
            ignore_default_args=["--enable-automation", "--no-sandbox"],
        )

        page = context.pages[0] if context.pages else context.new_page()
        log.info("Creating & handing over the page context")

        yield page

        log.info("Clearing page context")
        context.close()


@pytest.fixture(scope="session", autouse=True)
def ensure_logged_in(page):
    log.info("Navigating to %s", APP_URL)
    page.goto(APP_URL) #1
    page.wait_for_load_state("domcontentloaded")
    log.info("Landed on %s", page.url)

    if "/login" in page.url:
        log.info("User is not logged in. Manual login required")
        pytest.exit("User is not logged in. Manual login required")

    log.info("User is logged in")
    expect(page).to_have_url(APP_URL, timeout=DEFAULT_TIMEOUT)
    log.info("Session ready at home: %s", page.url)


@pytest.fixture
def base_page(page):
    return BasePage(page)


@pytest.fixture
def task_page(page):
    return TaskPage(page)


@pytest.fixture
def ensure_no_task_running(base_page):
    log.info("Ensuring no task is running before test")
    base_page.ensure_no_running_task()


@pytest.fixture
def go_to_home_page(page, base_page, ensure_no_task_running):
    if page.url.rstrip("/") == APP_URL.rstrip("/"):
        log.info("Already on home: %s", page.url)
    else:
        log.info("Navigating to home from %s -> %s", page.url, APP_URL)
        page.goto(APP_URL) #2
        page.wait_for_load_state("domcontentloaded")

    expect(page).to_have_url(APP_URL, timeout=DEFAULT_TIMEOUT)
    log.info("Currently at home screen: %s", page.url)
    return base_page


@pytest.fixture
def go_to_task_page(page, task_page, ensure_no_task_running):
    task_url = re.compile(TASK_URL_PATTERN)

    if task_url.search(page.url):
        open_task_title = task_page.task_title_text.inner_text()
        log.info("Already on task page: %s (title=%r)", page.url, open_task_title)
        return task_page

    log.info("Opening the first task from Recent")
    recent_count = task_page.recent_task_titles_text.count()
    log.info("Recent tasks available: %s", recent_count)
    assert recent_count > 0, "Expected at least one task in Recent to open"

    first_recent_title = task_page.open_recent_task_title()
    expect(page).to_have_url(task_url, timeout=DEFAULT_TIMEOUT)

    open_task_title = task_page.task_title_text.inner_text()
    log.info("Opened task title: %r", open_task_title)
    log.info("First recent title: %r", first_recent_title)
    assert open_task_title == first_recent_title, (
        f"Open task title {open_task_title!r} does not match "
        f"first recent title {first_recent_title!r}"
    )
    log.info("On task page: %s", page.url)
    return task_page
