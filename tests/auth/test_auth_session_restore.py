import logging

from playwright.sync_api import expect

from config.settings import APP_URL, DEFAULT_TIMEOUT

log = logging.getLogger(__name__)


# Verifies the session restore screen appears on reload and the home page loads afterward.
def test_auth_session_restore(page, go_to_home_page):
    log.info("Reloading page to trigger session restore")
    page.reload(wait_until="commit")

    log.info("Checking session restoring message is shown")
    expect(go_to_home_page.session_restoring_msg).to_be_visible(timeout=DEFAULT_TIMEOUT)
    expect(go_to_home_page.airtap_logo).to_be_visible(timeout=DEFAULT_TIMEOUT)

    log.info("Waiting for session restore to complete")
    expect(page).to_have_url(APP_URL, timeout=DEFAULT_TIMEOUT)
    expect(go_to_home_page.session_restoring_msg).not_to_be_visible(timeout=DEFAULT_TIMEOUT)
    expect(go_to_home_page.greeting_text_msg).to_be_visible(timeout=DEFAULT_TIMEOUT)
    expect(go_to_home_page.create_new_task_button).to_be_visible(timeout=DEFAULT_TIMEOUT)
    log.info("Session restored successfully at %s", page.url)
