import logging
import re

from playwright.sync_api import expect

from config.settings import DEFAULT_TIMEOUT, TASK_URL_PATTERN

log = logging.getLogger(__name__)


def test_task_stop(page, go_to_home_page, task_page):
    log.info("Stopping a running task")

    log.info("Creating a new task to stop")
    go_to_home_page.create_new_task()
    go_to_home_page.enter_task(task="Hey! how is the weather today")
    go_to_home_page.submit_task()

    expect(page).to_have_url(re.compile(TASK_URL_PATTERN), timeout=DEFAULT_TIMEOUT)
    task_page.wait_for_task_running(timeout=DEFAULT_TIMEOUT)

    log.info("Stopping the newly started task")
    task_page.stop_task()
    task_page.wait_for_task_stopped(timeout=DEFAULT_TIMEOUT)
    expect(task_page.stop_task_button).not_to_be_visible(timeout=DEFAULT_TIMEOUT)
    log.info("Stop control is gone after task was stopped")
