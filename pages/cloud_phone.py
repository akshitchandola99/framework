from pages.base_page import BasePage



class CloudPhone(BasePage):
    def __init__(self,page):
        super().__init__(page)

    #locators
    self.open_device_button = page.get_by_role("button", name="Open device")
    self.close_device_button = page.get_by_role("button", name="Close device")
    self.unmute_device_button = page.get_by_role("button", name="Unmute cloud phone")
    self.mute_device_button = page.get_by_role("button", name="mute cloud phone")


