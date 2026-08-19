from playwright.sync_api import expect


def test_reload(page):
    page.reload()
    expect(page,f"unexpected url after reload").to_have_url("https://airtap.ai/appp")
