import logging
from playwright.sync_api import expect
from pages.base_page import BasePage
from pages.task_page import TaskPage
import pytest

log = logging.getLogger(__name__)

@pytest.mark.order(3)
def test_task_execution(page):
    log.info("Starting a new task from the composer")
    bp = BasePage(page)
    bp.enter_task(task="Hey, how are you doing today?")
    bp.submit_task()

    tp = TaskPage(page)
    log.info("Waiting for task completion")
    expect(tp.task_completed_txt).to_be_visible(timeout=10_000)
    log.info("Task completed")


