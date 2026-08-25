from pages.task_page import TaskPage
import pytest
from playwright.sync_api import expect 

import logging


log = logging.getLogger(__name__)

@pytest.mark.order(5)
def test_task_followup(page):
    log.info("Sending follow-up on the current task")
    tp = TaskPage(page)
    tp.enter_follow_up_task(task = "open device settings")
    tp.submit_follow_up_task()
    log.info("Waiting for task completion")
    expect(tp.task_completed_txt).to_be_visible(timeout=60_000)
    log.info("Follow-up task completed")
    
