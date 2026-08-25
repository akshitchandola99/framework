import logging

log = logging.getLogger(__name__)

class TaskPage():
    def __init__(self,page):
        self.page=page

        #locators
        self.follow_up_composer = page.get_by_role("textbox", name="Continue with Airtap")
        self.send_button = page.get_by_role("button", name="Send message")
        self.attachment_input = page.locator('input[type="file"]')
        self.task_completed_txt = page.get_by_text("Task completed!")
        self.stop_task_button = page.locator("Section").get_by_label("Stop task")
        self.stop_task_confirm_button = page.get_by_role("button",name="Stop task", exact = True)  
        self.task_stopped_txt = page.get_by_text("Task stopped by user")
        self.choose_model_button = page.get_by_role("button",name="Choose task model")
        self.task_model_container = page.locator(".flex.flex-col.gap-1.p-3")
        self.task_models = self.task_model_container.get_by_role("button")
        self.selected_task_model = self.task_model_container.get_by_role("button", pressed=True)
        self.unselected_task_models = self.task_model_container.get_by_role("button", pressed=False)

    #actions

    def enter_follow_up_task(self,task):
        log.info("Entering follow-up prompt: %r", task)
        self.follow_up_composer.fill(task)

    def submit_follow_up_task(self):
        log.info("Submitting follow-up")
        self.send_button.click()

    def attach_files(self,file_paths):
        log.info("Attaching files %s",file_paths)
        self.attachment_input.set_input_files(file_paths)

    def stop_task(self):
        log.info("Clicking stop task")
        self.stop_task_button.click()
        log.info("Confirming stop task")
        self.stop_task_confirm_button.click()

    def select_model(self):
        log.info("Opening model picker")
        self.choose_model_button.click()

    def switch_model(self):
        self.select_model()
        log.info("Total models found: %s %s", self.task_models.count(), self.task_models.all_text_contents())

        default_model_name = self.selected_task_model.locator("p").inner_text()
        log.info("Default selected model is: %s", default_model_name)

        new_model = self.unselected_task_models.first
        new_model_name = new_model.locator("p").inner_text()
        log.info("Switching to model: %s", new_model_name)
        new_model.click()

        return default_model_name, new_model_name
        

    #information

