import logging
import re

from playwright.sync_api import expect

from config.settings import DEFAULT_TIMEOUT, TASK_URL_PATTERN

log = logging.getLogger(__name__)


# Verifies opening the first recent task shows the matching task title.
def test_task_recent(page, go_to_home_page, task_page):
    log.info("Reading recent task titles")
    go_to_home_page.wait_for_recent_tasks()

    recent_count = go_to_home_page.recent_task_titles_text.count()
    log.info("Total recent tasks: %s", recent_count)
    assert recent_count > 0, "Expected at least one task in Recent"

    first_10_titles = go_to_home_page.get_recent_titles(limit=10)
    log.info("First %s recent titles: %s", len(first_10_titles), first_10_titles)

    first_recent_title = task_page.open_recent_task_title()
    expect(page).to_have_url(re.compile(TASK_URL_PATTERN), timeout=DEFAULT_TIMEOUT)

    open_task_title = task_page.task_title_text.inner_text()
    log.info("Open task title: %r", open_task_title)
    log.info("First recent title: %r", first_recent_title)

    assert open_task_title == first_recent_title, (
        f"Open task title {open_task_title!r} does not match "
        f"first recent title {first_recent_title!r}"
    )
    log.info("Open task matches the first Recent entry")
