from playwright.sync_api import expect
import logging

from config.settings import APP_URL

log = logging.getLogger(__name__)


def test_auth_reload(page, go_to_home_page):
    log.info("Reloading page")
    page.reload()
    expect(page, "unexpected url after reload").to_have_url(APP_URL)
    log.info("Reload successful")
