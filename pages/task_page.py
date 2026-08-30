import logging

from playwright.sync_api import expect

from config.settings import DEFAULT_TIMEOUT
from pages.base_page import BasePage

log = logging.getLogger(__name__)


class TaskPage(BasePage):
    def __init__(self, page):
        super().__init__(page)

        # locators
        self.follow_up_composer = page.get_by_role(
            "textbox", name="Continue with Airtap"
        )
        self.task_title_text = page.locator("header").get_by_role("heading", level=1)
        self.recent_task_title = self.recent_task_titles_text.first
        self.task_completed_txt = page.get_by_text("Task completed!")
        self.task_stopped_txt = page.get_by_text("Task stopped by user")
        self.choose_model_button = page.get_by_role(
            "button", name="Choose task model"
        )
        self.task_model_container = page.locator(".flex.flex-col.gap-1.p-3")
        self.task_models = self.task_model_container.get_by_role("button")
        self.selected_task_model = self.task_model_container.get_by_role(
            "button", pressed=True
        )
        self.unselected_task_models = self.task_model_container.get_by_role(
            "button", pressed=False
        )

    # actions
    def enter_follow_up_task(self, task):
        log.info("Entering follow-up prompt: %r", task)
        expect(self.follow_up_composer).to_be_visible(timeout=DEFAULT_TIMEOUT)
        expect(self.follow_up_composer).to_be_enabled(timeout=DEFAULT_TIMEOUT)
        self.follow_up_composer.fill(task)
        expect(self.follow_up_composer).to_have_value(task, timeout=DEFAULT_TIMEOUT)

    def submit_follow_up_task(self):
        log.info("Submitting follow-up")
        expect(self.send_button).to_be_enabled(timeout=DEFAULT_TIMEOUT)
        self.send_button.click()

    def wait_for_task_completed(self, timeout=DEFAULT_TIMEOUT):
        log.info("Waiting for task completion")
        expect(self.task_completed_txt).to_be_visible(timeout=timeout)
        log.info("Task completed")

    def wait_for_task_running(self, timeout=DEFAULT_TIMEOUT):
        log.info("Waiting for stop control (task running)")
        expect(self.stop_task_button).to_be_visible(timeout=timeout)

    def wait_for_task_stopped(self, timeout=DEFAULT_TIMEOUT):
        log.info("Waiting for task-stopped confirmation")
        expect(self.task_stopped_txt).to_be_visible(timeout=timeout)
        log.info("Task stopped")

    def wait_for_follow_up_ready(self, timeout=DEFAULT_TIMEOUT):
        log.info("Waiting for follow-up composer")
        expect(self.follow_up_composer).to_be_visible(timeout=timeout)

    def select_model(self):
        log.info("Opening model picker")
        expect(self.choose_model_button).to_be_visible(timeout=DEFAULT_TIMEOUT)
        expect(self.choose_model_button).to_be_enabled(timeout=DEFAULT_TIMEOUT)
        self.choose_model_button.click()
        expect(self.task_model_container).to_be_visible(timeout=DEFAULT_TIMEOUT)

    def switch_model(self):
        self.select_model()
        expect(self.task_models).not_to_have_count(0, timeout=DEFAULT_TIMEOUT)
        expect(self.unselected_task_models.first).to_be_visible(timeout=DEFAULT_TIMEOUT)

        log.info(
            "Total models found: %s %s",
            self.task_models.count(),
            self.task_models.all_text_contents(),
        )

        expect(self.selected_task_model).to_be_visible(timeout=DEFAULT_TIMEOUT)
        default_model_name = self.selected_task_model.locator("p").inner_text()
        log.info("Default selected model is: %s", default_model_name)

        new_model = self.unselected_task_models.first
        new_model_name = new_model.locator("p").inner_text()
        log.info("Switching to model: %s", new_model_name)
        new_model.click()
        expect(new_model).to_have_attribute(
            "aria-pressed", "true", timeout=DEFAULT_TIMEOUT
        )

        return default_model_name, new_model_name

    def open_recent_task_title(self):
        expect(self.recent_task_title).to_be_visible(timeout=DEFAULT_TIMEOUT)
        title = self.recent_task_title.inner_text()
        log.info("Opening first recent task: %r", title)
        self.recent_task_title.click()
        expect(self.task_title_text).to_be_visible(timeout=DEFAULT_TIMEOUT)
        return title

