import logging
import re

from playwright.sync_api import expect

from config.settings import LONG_TIMEOUT, SAMPLE_JPG, SAMPLE_PDF, SAMPLE_PNG, SAMPLE_XLSX, TASK_URL_PATTERN

log = logging.getLogger(__name__)


def test_task_attachments(page, go_to_home_page, task_page):
    log.info("Starting a new task with attachments")
    go_to_home_page.create_new_task()

    go_to_home_page.attach_files([SAMPLE_JPG, SAMPLE_PDF, SAMPLE_PNG, SAMPLE_XLSX])
    go_to_home_page.enter_task(task="what type of files are these?")
    log.info("Waiting for invalid attachment message")
    expect(go_to_home_page.attachment_invalid_msg).to_be_visible()
    go_to_home_page.submit_task()

    expect(page).to_have_url(re.compile(TASK_URL_PATTERN), timeout=LONG_TIMEOUT)
    task_page.wait_for_task_completed(timeout=LONG_TIMEOUT)
