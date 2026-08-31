import logging
import re

from playwright.sync_api import expect

from config.settings import DEFAULT_TIMEOUT, LONG_TIMEOUT, TASK_URL_PATTERN
from test_data.prompts import GREETING

log = logging.getLogger(__name__)


# Verifies submitting a new task opens the task page and completes successfully.
def test_task_execution(page, go_to_home_page, task_page):
    log.info("Starting a new task from the composer")
    go_to_home_page.enter_task(task=GREETING)
    go_to_home_page.submit_task()

    log.info("Checking task URL after submit")
    expect(page).to_have_url(re.compile(TASK_URL_PATTERN), timeout=DEFAULT_TIMEOUT)
    task_page.wait_for_task_completed(timeout=LONG_TIMEOUT)
