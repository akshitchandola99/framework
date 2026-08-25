import logging
import re
from playwright.sync_api import expect
import pytest

log = logging.getLogger(__name__)

@pytest.mark.order(6)
def test_task_url(page):
    log.info("Checking task URL: %s", page.url)
    expect(page).to_have_url(re.compile(r"https://airtap.ai/app/t\?taskId=task-.*"))
    log.info("Task URL is valid")
