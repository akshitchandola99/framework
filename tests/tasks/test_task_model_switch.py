import logging
from pages.task_page import TaskPage
import pytest

log = logging.getLogger(__name__)

@pytest.mark.order(4)
def test_model_switch(page):
    log.info("Switching the task model")
    tp = TaskPage(page)
    default_model, new_model = tp.switch_model()

    log.info("Comparing models: %s vs %s", default_model, new_model)
    assert default_model != new_model, f"Model did not switch: still {default_model}"
    log.info("Model switching successful")
