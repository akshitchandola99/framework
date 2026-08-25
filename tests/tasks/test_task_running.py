import logging
from playwright.sync_api import expect
from pages.base_page import BasePage
import pytest

log = logging.getLogger(__name__)

@pytest.mark.order(2)
def test_task_stop(page):
    log.info("Checking home screen greeting")
    bp = BasePage(page)

    log.info("Checking if a task is already running")
    if bp.stop_task_button.is_visible():
        log.info("A task is already running; stopping it first")
        bp.stop_task_if_already_running()

    log.info("Waiting for greeting heading")
    expect(bp.greeting_text_user_msg).to_be_visible(timeout=10_000)
    log.info("Waiting for greeting prompt")
    expect(bp.greeting_text_msg).to_be_visible(timeout=10_000)