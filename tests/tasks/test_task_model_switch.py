import logging

from playwright.sync_api import expect

from config.settings import DEFAULT_TIMEOUT

log = logging.getLogger(__name__)


def test_model_switch(go_to_task_page):
    log.info("Switching the task model")
    default_model, new_model = go_to_task_page.switch_model()

    log.info("Comparing models: %s vs %s", default_model, new_model)
    assert default_model != new_model, f"Model did not switch: still {default_model}"

    go_to_task_page.select_model()
    selected_after_switch = go_to_task_page.selected_task_model.locator("p").inner_text()
    log.info("Selected model after switch: %s", selected_after_switch)
    assert selected_after_switch == new_model, (
        f"Expected selected model {new_model!r}, got {selected_after_switch!r}"
    )
    expect(go_to_task_page.selected_task_model).to_have_attribute(
        "aria-pressed", "true", timeout=DEFAULT_TIMEOUT
    )
    log.info("Model switching successful")
