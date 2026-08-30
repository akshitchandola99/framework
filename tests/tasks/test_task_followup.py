import logging
import re

from playwright.sync_api import expect

from config.settings import FOLLOWUP_TIMEOUT, TASK_URL_PATTERN

log = logging.getLogger(__name__)


def test_task_followup(page, go_to_task_page):
    log.info("Sending follow-up on the current task")
    expect(page).to_have_url(re.compile(TASK_URL_PATTERN))
    go_to_task_page.wait_for_follow_up_ready()

    go_to_task_page.enter_follow_up_task(task="open device settings")
    go_to_task_page.submit_follow_up_task()
    go_to_task_page.wait_for_task_completed(timeout=FOLLOWUP_TIMEOUT)
    expect(page).to_have_url(re.compile(TASK_URL_PATTERN))
    log.info("Follow-up completed on the same task URL")
