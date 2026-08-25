from playwright.sync_api import expect
import logging
import pytest

log = logging.getLogger(__name__)


@pytest.mark.order(1)
def test_reload(page):
    log.info("Reloading page")
    page.reload()
    expect(page,"unexpected url after reload").to_have_url("https://airtap.ai/app")
    log.info("Reload successful")









