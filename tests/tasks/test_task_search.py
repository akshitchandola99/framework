import logging

from playwright.sync_api import expect

log = logging.getLogger(__name__)


# Verifies searching recent tasks returns only titles matching the search text.
def test_task_search(go_to_home_page):
    log.info("Searching recent tasks")
    search_input = "Greeting"

    go_to_home_page.search_task(search_input)
    go_to_home_page.wait_for_recent_tasks()

    recent_count = go_to_home_page.recent_task_titles_text.count()
    log.info("Search input: %r", search_input)
    log.info("Total matching recent tasks: %s", recent_count)
    assert recent_count > 0, f"Expected at least one recent task matching {search_input!r}"

    first_5_titles = go_to_home_page.get_recent_titles(limit=5)
    log.info("First %s matching titles: %s", len(first_5_titles), first_5_titles)
    expect(go_to_home_page.recent_task_titles_text.first).to_contain_text(
        search_input, ignore_case=True
    )

    for title in first_5_titles:
        log.info("Checking title contains search text: %r", title)
        assert search_input.lower() in title.lower(), (
            f"Title {title!r} does not contain {search_input!r}"
        )

    log.info("All checked recent titles contain %r", search_input)
