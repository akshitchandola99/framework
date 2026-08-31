import logging
import re

from playwright.sync_api import expect

from config.settings import DEFAULT_TIMEOUT, LONG_TIMEOUT, TASK_URL_PATTERN
from test_data.prompts import GREETING

log = logging.getLogger(__name__)


# Verifies switching the model and running a task completes on the task page.
def test_task_model_switch(page, go_to_home_page, task_page):
    log.info("Switching the task model on the home composer")
    default_model, new_model = task_page.switch_model()
    log.info("Default model: %r, new model: %r", default_model, new_model)

    log.info("Asserting both model names are present")
    assert default_model.strip(), "Expected default model name to be non-empty"
    assert new_model.strip(), "Expected new model name to be non-empty"

    log.info("Comparing models: %s vs %s", default_model, new_model)
    assert default_model != new_model, f"Model did not switch: still {default_model}"

    log.info("Submitting a task with the switched model")
    go_to_home_page.enter_task(task=GREETING)
    go_to_home_page.submit_task()

    log.info("Checking task URL after submit")
    expect(page).to_have_url(re.compile(TASK_URL_PATTERN), timeout=DEFAULT_TIMEOUT)

    log.info("Waiting for task completion")
    task_page.wait_for_task_completed(timeout=LONG_TIMEOUT)

    log.info("Confirming task remained on the task URL after completion")
    expect(page).to_have_url(re.compile(TASK_URL_PATTERN))

    log.info(
        "Model switch and task execution successful: %s -> %s",
        default_model,
        new_model,
    )
