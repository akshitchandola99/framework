import logging
import re

from playwright.sync_api import Page, expect

from config.settings import DEFAULT_TIMEOUT

log = logging.getLogger(__name__)


class BasePage:
    def __init__(self, page: Page):
        self.page = page

        # locators
        self.create_new_task_button = page.get_by_role("button", name="Create new Task")
        self.task_composer = page.get_by_role("textbox", name="Chat with Airtap")
        self.send_button = page.get_by_role("button", name="Send message")
        self.recent_task_titles_text = page.locator(
            r"div.group\/task span.text-\[var\(--airtap-title\)\]"
        )
        self.search_task_field = page.get_by_placeholder("Search Task")
        self.attachment_input = page.locator('input[type="file"]')
        self.attachment_invalid_msg = page.get_by_text(
            "Only image and PDF files can be attached."
        )
        self.stop_task_button = page.locator("Section").get_by_label("Stop task")
        self.stop_task_confirm_button = page.get_by_role(
            "button", name="Stop task", exact=True
        )
        self.greeting_text_user_msg = page.get_by_role(
            "heading", name=re.compile(r"^Hello\s.+")
        )
        self.greeting_text_msg = page.get_by_text("What can I do for you today?")
        self.session_restoring_msg = page.get_by_text("Restoring your Airtap session…")
        self.airtap_logo = page.get_by_role("img", name="Airtap logo")
        self.user_details = page.get_by_role("button", name="Open user menu").locator("p")
        self.user_name = self.user_details.first
        self.user_email = self.user_details.nth(1)

    # actions
    def create_new_task(self):
        log.info("Tapping 'Create new Task' button")
        expect(self.create_new_task_button).to_be_visible(timeout=DEFAULT_TIMEOUT)
        expect(self.create_new_task_button).to_be_enabled(timeout=DEFAULT_TIMEOUT)
        self.create_new_task_button.click()
        expect(self.task_composer).to_be_visible(timeout=DEFAULT_TIMEOUT)

    def search_task(self, search_input):
        log.info("Searching for tasks with text: %r", search_input)
        expect(self.search_task_field).to_be_visible(timeout=DEFAULT_TIMEOUT)
        expect(self.search_task_field).to_be_enabled(timeout=DEFAULT_TIMEOUT)
        self.search_task_field.fill(search_input)

    def enter_task(self, task):
        log.info("Entering task prompt: %r", task)
        expect(self.task_composer).to_be_visible(timeout=DEFAULT_TIMEOUT)
        expect(self.task_composer).to_be_enabled(timeout=DEFAULT_TIMEOUT)
        self.task_composer.fill(task)
        expect(self.task_composer).to_have_value(task, timeout=DEFAULT_TIMEOUT)

    def attach_files(self, file_paths):
        log.info("Attaching files %s", file_paths)
        expect(self.attachment_input).to_be_attached(timeout=DEFAULT_TIMEOUT)
        self.attachment_input.set_input_files(file_paths)

    def submit_task(self):
        log.info("Submitting task")
        expect(self.send_button).to_be_enabled(timeout=DEFAULT_TIMEOUT)
        self.send_button.click()

    def stop_task(self):
        log.info("Clicking stop task")
        expect(self.stop_task_button).to_be_visible(timeout=DEFAULT_TIMEOUT)
        self.stop_task_button.click()
        log.info("Confirming stop task")
        expect(self.stop_task_confirm_button).to_be_visible(timeout=DEFAULT_TIMEOUT)
        self.stop_task_confirm_button.click()

    def ensure_no_running_task(self):
        log.info("Checking if a task is already running")
        if self.stop_task_button.is_visible():
            log.info("A task is already running; stopping it first")
            self.stop_task()
        else:
            log.info("No running task found")

    def wait_for_recent_tasks(self, timeout=DEFAULT_TIMEOUT):
        log.info("Waiting for recent tasks to load")
        expect(self.recent_task_titles_text.first).to_be_visible(timeout=timeout)

    def get_recent_titles(self, limit=None):
        titles = self.recent_task_titles_text.all_inner_texts()
        if limit is not None:
            return titles[:limit]
        return titles

    def get_user_details(self):
        log.info("Checking for user details")
        expect(self.user_name).to_be_visible(timeout=DEFAULT_TIMEOUT)
        expect(self.user_email).to_be_visible(timeout=DEFAULT_TIMEOUT)
        user_name_txt = self.user_name.inner_text().strip()
        user_email_txt = self.user_email.inner_text().strip()
        return user_name_txt, user_email_txt


