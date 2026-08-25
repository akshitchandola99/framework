import logging
from playwright.sync_api import Page
import re

log = logging.getLogger(__name__)

class BasePage():
    def __init__(self, page: Page):
        self.page = page

        #locators
        self.create_new_task_button = page.get_by_role("button", name="Create new Task")
        self.task_composer = page.get_by_role("textbox", name="Chat with Airtap")
        self.send_button = page.get_by_role("button", name="Send message")
        self.attachment_input = page.locator('input[type = "file"]')
        self.attachment_invalid_msg = page.get_by_text("Only image and PDF files can be attached.")
        self.stop_task_button = page.locator("Section").get_by_label("Stop task")
        self.stop_task_confirm_button = page.get_by_role("button",name="Stop task", exact = True)
        self.greeting_text_user_msg = page.get_by_role("heading", name = re.compile(r"^Hello\s.+"))
        self.greeting_text_msg = page.get_by_text("What can I do for you today?")

    #actions
    def create_new_task(self):
        log.info("Tapping 'Create new Task' button")
        self.create_new_task_button.click()

    def enter_task(self, task):
        log.info("Entering task prompt: %r", task)
        self.task_composer.fill(task)

    def attach_files(self,file_paths):
        log.info("Attaching files %s",file_paths)
        self.attachment_input.set_input_files(file_paths)

    def submit_task(self):
        log.info("Submitting task")
        self.send_button.click()
    def stop_task(self):
        log.info("Clicking stop task")
        self.stop_task_button.click()

    def select_model(self):
        log.info("Opening model picker")
        self.choose_model_button.click()

    def stop_task_if_already_running(self):
        log.info("Stopping already-running task")
        self.stop_task_button.click()
        log.info("Confirming stop task")
        self.stop_task_confirm_button.click()











