import logging

from playwright.sync_api import expect

log = logging.getLogger(__name__)


def test_task_user_details(go_to_home_page):
    log.info("Checking user name and email in the user menu")

    user_name, user_email = go_to_home_page.get_user_details()

    log.info("Asserting user name is non-empty")
    assert user_name, "Expected user name to be non-empty"

    log.info("Asserting user email contains @ and .com")
    assert "@" in user_email and ".com" in user_email, (
        f"Expected email to contain @ and .com, got {user_email!r}"
    )

    log.info("Verifying user name is visible in the menu")
    expect(go_to_home_page.user_name).to_be_visible()
    expect(go_to_home_page.user_name).to_have_text(user_name)

    log.info("Verifying user email is visible in the menu")
    expect(go_to_home_page.user_email).to_be_visible()
    expect(go_to_home_page.user_email).to_have_text(user_email)

    log.info("Cross-checking user name against the home greeting")
    expect(go_to_home_page.greeting_text_user_msg).to_be_visible()
    greeting = go_to_home_page.greeting_text_user_msg.inner_text()
    log.info("Greeting heading: %r", greeting)
    assert user_name in greeting, (
        f"User name {user_name!r} not found in greeting {greeting!r}"
    )

    log.info("User details verified: name=%r, email=%r", user_name, user_email)
