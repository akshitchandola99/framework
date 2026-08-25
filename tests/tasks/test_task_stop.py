import logging
from playwright.sync_api import expect
from pages.base_page import BasePage
from pages.task_page import TaskPage
import pytest

log = logging.getLogger(__name__)

@pytest.mark.order(7)
def test_task_stop(page):
    log.info("Stopping a running task")
    bp = BasePage(page)

    log.info("Checking if a task is already running")
    if bp.stop_task_button.is_visible():
        log.info("A task is already running; stopping it first")
        bp.stop_task_if_already_running()

    log.info("Creating a new task to stop")
    bp.create_new_task()

    bp.enter_task(task="Hey! how is the weather today")
    bp.submit_task()

    tp = TaskPage(page)
    log.info("Stopping the newly started task")
    tp.stop_task()
    
    log.info("Waiting for task-stopped confirmation")
    expect(tp.task_stopped_txt).to_be_visible(timeout=10_000)
    log.info("Task stopped")

