import logging
import re

from playwright.sync_api import expect

from config.settings import TASK_URL_PATTERN

log = logging.getLogger(__name__)


# Verifies the current page URL matches the expected task link format.
def test_task_link_validation(page,go_to_task_page):
    log.info("Checking task URL: %s", page.url)
    expect(page).to_have_url(re.compile(TASK_URL_PATTERN))
    log.info("Task URL is valid")
