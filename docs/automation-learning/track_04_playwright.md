# Track 4 — Playwright / Web UI Automation

*Deep-dive for Track 4 of [00_master_study_plan.md](00_master_study_plan.md). Topics are in
learning order. Assumes [Track 1](track_01_python_for_automation.md) (classes, context managers),
[Track 2](track_02_pytest.md) (fixtures), and [Track 3](track_03_api_automation.md) (API calls —
you'll use them here to set up state fast).*

## What is Playwright?

**Playwright drives a real browser with code.** It opens Chrome, clicks buttons, types into fields,
and reads what's on screen — exactly like a person, but scripted.

```python
page.goto("https://airtap.ai/")
page.get_by_role("link", name="Try it").click()
```

It was built by Microsoft to fix the things that made older tools (Selenium especially) painful:

| Problem with older tools | Playwright's answer |
|---|---|
| You had to add `sleep()` everywhere | **Auto-waiting** — it waits for elements by itself |
| Tests broke when the CSS changed | **Role-based locators** — find things the way a user does |
| "It failed in CI, no idea why" | **Trace viewer** — a full recording you can step through |
| Slow to set up a clean session | **Contexts** — instant isolated sessions |

**Airtap status:** `web-automation/` already exists — Playwright + pytest + Page Objects, with
**3 tests**. It's a real starting point, but it only checks that pages *load*. No test creates a
task. That gap is your main opportunity.

## Topic table

| # | Topic | Priority | Notes |
|---|---|---|---|
| 1 | Browser / context / page | 🔴 P0 | Three levels. Contexts are what make parallel runs safe. |
| 2 | `codegen` | 🟢 P3 | Day-one accelerator. Record, then clean up. Never ship raw. |
| 3 | **Locators** | 🔴 P0 | The priority ladder. Gets you stable tests. |
| 4 | Assertions (`expect`) | 🔴 P0 | Auto-retrying — very different from a plain `assert`. |
| 5 | Auto-waiting | 🔴 P0 | Why you rarely need `sleep()` — and the exceptions. |
| 6 | Trace viewer, screenshots, video | 🔴 P0 | Early, because you need it before things get hard. |
| 7 | Fixtures (`pytest-playwright`) | 🔴 P0 | |
| 8 | Auth + `storageState` | 🔴 P0 | Log in once, reuse everywhere. |
| 9 | Page Object Model | 🟠 P1 | Airtap uses it, so you need it. |
| 10 | Fixtures-first alternative | 🟡 P2 | Modern alternative. Know when each fits. |
| 11 | Flakiness | 🔴 P0 | Where UI suites live or die. |
| 12 | Network interception | 🟡 P2 | Mock the backend, isolate the frontend. |

## Setup

```bash
pip install pytest-playwright
playwright install chromium
```

The second line downloads the actual browser. People forget it and get a confusing error.

---

# 1. Browser, context, page 🔴

## Three levels

```
Browser          ← the whole Chrome program (heavy, slow to start)
  └── Context    ← an isolated session, like an incognito window (instant)
        └── Page ← one tab
```

## What each one means

| Level | Mental model | Cost |
|---|---|---|
| **Browser** | The Chrome application itself | Seconds to launch |
| **Context** | A fresh incognito window — own cookies, own storage, own login | Milliseconds |
| **Page** | A single tab inside that window | Milliseconds |

## Why contexts matter

**A context is a completely clean session.** Two contexts in the same browser can't see each
other's cookies or logins.

That gives you two things:

1. **Test isolation** — test A logging in doesn't affect test B
2. **Cheap parallelism** — one browser, many contexts, all independent

Without contexts, you'd have to launch a whole new browser per test to get a clean state. That's
slow. Contexts give you the same isolation almost instantly.

```python
browser = playwright.chromium.launch()

context_a = browser.new_context()      # user A's session
context_b = browser.new_context()      # user B's session — totally separate

page_a = context_a.new_page()
page_b = context_b.new_page()
```

This is genuinely useful for Airtap: testing that **user A can't see user B's tasks** needs two
independent sessions at once. Two contexts, one browser.

## Airtap does something different: a persistent context

Airtap's `browser_config.py` uses `launch_persistent_context` instead:

```python
def chrome_persistent_launch_options() -> dict[str, Any]:
    return {
        "user_data_dir": str(CHROME_PROFILE_DIR),      # ← saves to a real folder
        "channel": "chrome",                            # ← real Chrome, not bundled Chromium
        "headless": False,                              # ← visible browser
        "ignore_default_args": ["--enable-automation", "--no-sandbox"],
        "args": ["--start-maximized"],
        "no_viewport": True,
    }
```

**What `user_data_dir` does:** cookies and logins are saved to `chrome-profile/` on disk and reused
next run. So the suite is *already logged in* — no login code needed.

**The trade-offs — worth understanding, because you'll have to fix this:**

| | Good | Bad |
|---|---|---|
| Already logged in | No login code to write | **Can't test login itself** |
| Simple | Works immediately | **Won't work in CI** — no saved profile there |
| | | **Can't run parallel** — one profile, one lock |

That last one is real and already handled in the code:

```python
if (CHROME_PROFILE_DIR / "SingletonLock").exists():
    pytest.skip("chrome-profile is locked (Chrome already using that user-data dir).")
```

If you have Chrome open with that profile, the tests **skip** rather than fail confusingly.

**Where this goes:** topic #8 (`storageState`) is the fix — it gives you "already logged in" without
the lock, and it works in CI.

## headless vs headed

```python
playwright.chromium.launch(headless=True)     # no window — fast, for CI
playwright.chromium.launch(headless=False)    # visible window — for debugging
```

Airtap runs headed (`headless: False`) because it's a local, watch-it-happen suite. **CI must run
headless** — there's no screen to draw on.

---

# 2. `codegen` — record a test 🟢

## What it does

Playwright opens a browser, you click around, and it **writes the code for you**.

```bash
playwright codegen https://airtap.ai/
```

Click "Try it" and it generates:

```python
page.get_by_role("link", name="Try it").click()
```

## Why it's genuinely useful

- Instant answer to "what's the locator for this thing?"
- It picks **good** locators by default (role-based, topic #3)
- Fastest way to explore an unfamiliar page

## Why it's marked P3

**Never ship what it generates.** Codegen produces a flat script — no Page Objects, no assertions,
sometimes brittle locators for tricky elements.

**Use it as a lookup tool, not a test generator.** Record → copy the locator → put it in a Page
Object → write a real assertion yourself.

---

# 3. Locators 🔴

**Get this right and your tests stop breaking randomly.**

## What a locator is

A locator is a **description of how to find something** — not the element itself.

```python
button = page.get_by_role("button", name="Send message")     # nothing has happened yet
button.click()                                                # NOW it looks for it
```

This matters: the locator is re-evaluated every time you use it. So a locator created before the
page updated still works after — it just looks again.

## The priority ladder

Use the highest one that works:

| Priority | Method | Finds by | Why |
|---|---|---|---|
| 1 | `get_by_role` | Its role + visible name | How a **user** (or screen reader) sees it. Survives styling changes. |
| 2 | `get_by_label` | Its form label | Natural for inputs |
| 3 | `get_by_text` | Visible text | Good for static content |
| 4 | `get_by_placeholder` | Placeholder text | Good for search/chat boxes |
| 5 | `get_by_test_id` | `data-testid` | Stable, but needs devs to add it |
| 6 | CSS / XPath | Structure | **Last resort** — breaks when markup changes |

## Why role beats CSS

```python
page.locator("div.MuiButton-root-x7f2 > span.label")     # ❌ breaks on any restyle
page.get_by_role("button", name="Send message")           # ✅ survives restyling
```

The CSS one depends on class names a build tool generated. Change the theme, it breaks. The role
one describes what the thing *is* — a button that says "Send message" — which only changes if the
actual UI changes.

**Bonus:** if `get_by_role` can't find your button, that's often a real accessibility bug. Your test
doubles as an accessibility check.

## Airtap's real locators — the whole ladder in one file

From `pages/pilot_app_page.py`:

```python
def hello_user_heading(self) -> Locator:
    # Ex: "Hello Alex" - user name varies.
    return self.page.get_by_role("heading", name=re.compile(r"^Hello\b"))

def what_can_i_do_for_you_today_text(self) -> Locator:
    return self.page.get_by_text("What can I do for you today?", exact=True)

def create_new_task_button(self) -> Locator:
    # Expanded sidebar: "Create Task"; collapsed rail: aria-label "Create new task".
    return self.page.get_by_role("button", name=re.compile(r"create\s+(new\s+)?task", re.IGNORECASE))

def task_creation_input(self) -> Locator:
    return self.page.get_by_placeholder("Chat with Airtap")

def task_creation_submit_button(self) -> Locator:
    return self.page.get_by_role("button", name="Send message")

def cloudphone_video_ui(self) -> Locator:
    # Cloud receiver UI renders as an autoplay inline video surface.
    return self.page.locator("video[autoplay][playsinline]")
```

Three things worth noticing:

**1. Regex for varying text.** The heading says "Hello Alex" or "Hello Sam" — the name changes. So:

```python
re.compile(r"^Hello\b")      # matches "Hello <anything>"
```

`^` means "starts with", `\b` is a word boundary. Without regex you'd have to hardcode a username.

**2. Regex for UI variants.** The create-task button has different text depending on whether the
sidebar is expanded:

```python
re.compile(r"create\s+(new\s+)?task", re.IGNORECASE)
```

Matches "Create Task" **and** "Create new task", any capitalisation. One locator, both states.

**3. The one CSS fallback — with a comment explaining why:**

```python
self.page.locator("video[autoplay][playsinline]")
```

A `<video>` element has no role or text to grab. CSS is the correct choice here — and the comment
says why. **That's the standard to follow:** if you drop to CSS, leave a note explaining what you
tried first.

## `exact=True`

```python
page.get_by_text("Task")                     # matches "Task", "Create Task", "Tasks"
page.get_by_text("Task", exact=True)         # matches only exactly "Task"
```

Airtap uses `exact=True` on the "What can I do for you today?" text and on the "Try it" link — good
practice for text that could partially match something else.

## Chaining and filtering

```python
# find inside another element
page.get_by_role("listitem").get_by_role("button", name="Delete")

# filter a list down
page.get_by_role("listitem").filter(has_text="COMPLETED")

# pick by position
page.get_by_role("listitem").first
page.get_by_role("listitem").nth(2)
```

Useful for Airtap's task list — "find the row containing this task ID, then click its button."

## Strict mode

If a locator matches **more than one** element, Playwright errors instead of guessing:

```
Error: strict mode violation: locator resolved to 3 elements
```

**This is a feature.** It's telling you your locator is ambiguous. Fix it by narrowing (`exact=True`,
`.filter()`, `.first`) — don't ignore it.

---

# 4. Assertions with `expect` 🔴

## Two kinds of assertion

```python
assert page.url == "https://airtap.ai/app"            # plain Python — checks once, right now
expect(button).to_be_visible()                         # Playwright — RETRIES until true or timeout
```

**This difference is the whole point.**

## Why `expect` retries

Web pages are asynchronous. Something might appear half a second after the click. A plain `assert`
checks the instant it runs — and fails on a page that would have been fine 200ms later.

`expect` keeps re-checking until it passes or the timeout expires:

```python
expect(pilot_app_page.create_new_task_button()).to_be_visible(timeout=15_000)
```

That's real Airtap code. It waits up to 15 seconds, returning as soon as the button appears.

## Common `expect` assertions

```python
expect(locator).to_be_visible()
expect(locator).to_be_hidden()
expect(locator).to_be_enabled()
expect(locator).to_have_text("Task created")
expect(locator).to_contain_text("COMPLETED")
expect(locator).to_have_value("hello")           # input fields
expect(locator).to_have_count(3)
expect(page).to_have_url("https://airtap.ai/app")
expect(page).to_have_title("Airtap")
```

## Airtap's real usage

From `test_smoke.py`:

```python
cta = pilot_website.try_airtap_link()
expect(cta, "Try it CTA is not visible").to_be_visible(timeout=15_000)
expect(cta, "Try it CTA is not enabled").to_be_enabled(timeout=15_000)
```

Note the **message as the second argument** — same idea as an `assert` message. When it fails you
get "Try it CTA is not visible" instead of a bare timeout.

## Regex in assertions

```python
expect(
    pilot_app_page.task_device_selector_button(),
    "Default device should be Cloud Phone",
).to_contain_text(re.compile(r"cloud\s*phone", re.IGNORECASE), timeout=15_000)
```

This is real Airtap code, and it's a good pattern: the UI might render "Cloud Phone", "cloud phone",
or "CloudPhone". The regex accepts all three. Testing *meaning*, not exact characters.

## When to use which

| Use | For |
|---|---|
| `expect(locator)` | Anything on the page — it might not be there yet |
| `assert` | Plain Python values you already have — a variable, an API response |

```python
assert page.url == "https://airtap.ai/"          # ✅ fine, URL is already known
expect(page).to_have_url("https://airtap.ai/")   # ✅ better if navigation might still be in flight
```

---

# 5. Auto-waiting 🔴

## What Playwright does for you

Before clicking, Playwright automatically waits for the element to be:

1. Attached to the page
2. Visible
3. Stable (not still animating)
4. Able to receive events (not covered by something else)
5. Enabled

```python
page.get_by_role("button", name="Send message").click()
```

That one line already waits for all five. **This is why you rarely need `sleep()`.**

## The default timeout

30 seconds for actions. Override per call:

```python
button.click(timeout=5_000)
```

## When auto-waiting is NOT enough

Auto-waiting waits for the **element**. It doesn't know about things that aren't tied to one
element:

| Situation | What to use |
|---|---|
| Waiting for an API call to finish | `page.wait_for_response(...)` |
| Waiting for a URL change | `page.wait_for_url(...)` |
| Waiting for page load stage | `page.wait_for_load_state(...)` |
| Element exists but data is still loading | `expect(...).to_contain_text(...)` |

Airtap uses two of these already:

```python
page.wait_for_url("https://airtap.ai/app")
page.wait_for_load_state("domcontentloaded")
```

## Waiting for a network response

Very useful for Airtap — the UI updates after the backend replies:

```python
with page.expect_response(lambda r: "taskCreate" in r.url) as response_info:
    pilot_app_page.task_creation_submit_button().click()

response = response_info.value
assert response.status == 200
```

Reads as: "start listening, then click, then wait for the matching response." You get to assert on
the **API call the UI made** — a genuinely powerful combination.

## ⚠️ The anti-pattern in Airtap's own suite

The last line of `test_app_page_launched`:

```python
time.sleep(5)  # Wait for the cloudphone video UI to load
```

**Three things wrong with it:**
1. If the UI loads in 1s, you waste 4s — every run, forever
2. If it takes 6s, the test fails anyway
3. It hides *what* you're waiting for

**The fix:**

```python
expect(pilot_app_page.cloudphone_video_ui()).to_be_visible(timeout=15_000)
```

Returns as soon as it's there; fails clearly if it isn't.

**The rule: never sleep, always wait for a condition.** Fixed sleeps are the single biggest cause of
both slow suites and flaky suites. Fixing this one in Airtap is on your practice checklist — and
it's a good thing to be able to mention in an interview.

---

# 6. Debugging tools 🔴

**Learn these before you need them.** When a test fails in CI at 3am, this is all you have.

## Trace viewer — the best one

A trace is a **full recording**: every action, a screenshot before and after each one, the DOM,
network calls, and console logs.

```bash
pytest --tracing on              # always
pytest --tracing retain-on-failure   # only keep traces for failures ← best default
```

Open it:

```bash
playwright show-trace trace.zip
```

You get a timeline you can scrub through. Click any action and see exactly what the page looked
like at that moment.

**This is the answer to "it passed locally but failed in CI."** You get the CI run's actual
screenshots.

## Screenshots and video

```bash
pytest --screenshot only-on-failure
pytest --video retain-on-failure
```

## Debug mode — step through live

```bash
PWDEBUG=1 pytest tests/test_smoke.py
```

Opens the Playwright Inspector: the browser pauses, and you step through actions one at a time. It
also highlights what each locator matches — invaluable when a locator isn't finding what you expect.

## Slow motion

```python
browser = playwright.chromium.launch(headless=False, slow_mo=1000)   # 1s between actions
```

Useful when something happens too fast to see.

## Airtap's own logging

Airtap's `conftest.py` writes a timestamped log per run via pytest hooks (Track 2 #9):

```python
logger.info("START %s", item.nodeid)
...
logger.info("END %s", item.nodeid)
```

Producing `logs/test_run_20260615_080510.log`. And the tests log each passing step:

```python
logger.info("Passed: Try it CTA is visible")
```

That's a reasonable pattern — but note it only records what the test *thought* happened. A trace
records what the **browser** actually did. Add tracing; it's strictly more informative.

---

# 7. Fixtures with `pytest-playwright` 🔴

## What you get free

Install `pytest-playwright` and these fixtures exist automatically:

| Fixture | What it gives you |
|---|---|
| `page` | A fresh page (new context each test) |
| `context` | The browser context |
| `browser` | The browser (session-scoped) |
| `browser_name` | `"chromium"`, `"firefox"`, `"webkit"` |

```python
def test_homepage(page):              # just ask for it
    page.goto("https://airtap.ai/")
    expect(page).to_have_title("Airtap")
```

**Default behaviour: a brand-new context per test.** Automatic isolation — no leftover cookies.

## Useful CLI options

```bash
pytest --headed                    # watch it run
pytest --browser firefox           # different browser
pytest --slowmo 500                # slow down
pytest --base-url https://qa1.airtap.ai
```

## Airtap doesn't use the built-in `page` fixture

It defines its own, because it needs the persistent Chrome profile:

```python
@pytest.fixture(scope="session")
def playwright_session():
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser_context(playwright_session):
    if (CHROME_PROFILE_DIR / "SingletonLock").exists():
        pytest.skip("chrome-profile is locked ...")
    context = launch_chrome_persistent_context(playwright_session)
    page = context.pages[0] if context.pages else context.new_page()
    page.goto(PILOT_WEBSITE_URL, wait_until="domcontentloaded", timeout=60_000)
    yield context
    context.close()


@pytest.fixture
def page(browser_context):
    yield browser_context.pages[0] if browser_context.pages else browser_context.new_page()
```

**Note the trade-off:** Airtap's `page` reuses **one shared context** for all tests (session scope),
rather than a fresh one per test. That's faster and keeps the login — but it means **tests are not
isolated**. Test 1 leaves the browser on `/app`, and test 3 depends on that.

Look at the real test:

```python
def test_app_page_launched(page):
    page.wait_for_url("https://airtap.ai/app")     # only true because test 2 navigated there
```

**This is why `test_app_page_launched` can't run on its own.** Worth knowing before you add tests —
and something `storageState` (next topic) fixes properly.

---

# 8. Auth and `storageState` 🔴

## The problem

Logging in through the UI before every test is slow (5–10s each) and fragile.

## The solution

Log in **once**, save the browser's cookies and storage to a file, and load that file into every
test's context.

## Step 1: save the state (run once)

```python
# scripts/save_auth.py
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto("https://qa1.airtap.ai/app")
    input("Log in manually, then press Enter here...")     # do it by hand once

    page.context.storage_state(path="auth.json")           # saved
    browser.close()
```

## Step 2: reuse it

```python
@pytest.fixture(scope="session")
def browser(playwright_session):
    browser = playwright_session.chromium.launch()
    yield browser
    browser.close()


@pytest.fixture
def page(browser):
    context = browser.new_context(storage_state="auth.json")   # ← already logged in
    page = context.new_page()
    yield page
    context.close()                                             # fresh context per test
```

**Now every test gets:** already logged in **and** a clean isolated context. Both benefits, no lock
file, works in CI.

## What's in `auth.json`

Cookies and localStorage — the things that prove you're logged in.

```json
{
  "cookies": [{"name": "session", "value": "...", "domain": "qa1.airtap.ai"}],
  "origins": [{"origin": "https://qa1.airtap.ai", "localStorage": [...]}]
}
```

## ⚠️ Never commit it

```gitignore
auth.json
```

It contains a live session. Anyone with the file is logged in as you. Airtap's `.gitignore` already
excludes `chrome-profile/` for exactly this reason — do the same for `auth.json`.

## Better: generate it, don't hand-make it

Since you'll have an API client from Track 3, you can often skip UI login entirely — get a token via
API, inject it into localStorage, done. Faster and scriptable in CI.

## Why this matters for Airtap specifically

It fixes three things at once, all identified in topic #1:

| Problem today | `storageState` fix |
|---|---|
| Can't run in CI (no saved profile) | `auth.json` is a file you can generate in CI |
| Can't run parallel (profile lock) | Each context loads the same file independently |
| Tests aren't isolated | Fresh context per test |

---

# 9. Page Object Model 🟠

## The idea

**Keep locators out of tests.** Put them in a class per page. Tests describe *what* to do; the Page
Object knows *how*.

## Why

Without it, a locator that changes must be fixed in every test that uses it:

```python
def test_one(page):
    page.get_by_role("button", name="Send message").click()     # repeated
def test_two(page):
    page.get_by_role("button", name="Send message").click()     # repeated
```

With a Page Object, you fix it in **one** place.

## Airtap's real Page Object

```python
class PilotAppPage:
    def __init__(self, page: Page) -> None:
        self.page = page

    def task_creation_input(self) -> Locator:
        return self.page.get_by_placeholder("Chat with Airtap")

    def task_creation_submit_button(self) -> Locator:
        return self.page.get_by_role("button", name="Send message")
```

This is a plain class — exactly Track 1 #6. `__init__` stores the page; each method returns a
locator.

## Two styles

Airtap's Page Objects **return locators**:

```python
pilot_app_page.task_creation_submit_button().click()      # test does the clicking
```

The other common style is **methods that do actions**:

```python
class PilotAppPage:
    def create_task(self, text: str):
        self.task_creation_input().fill(text)
        self.task_creation_submit_button().click()
```

```python
pilot_app_page.create_task("check the weather")           # test says WHAT, not HOW
```

**Both are valid.** Returning locators is flexible; action methods read better and remove repetition.
A good middle ground — which fits Airtap's existing code — is to keep the locator methods and add
action methods on top for multi-step flows.

## Rules that keep Page Objects useful

| Do | Don't |
|---|---|
| One class per page or major component | One giant class for the whole app |
| Return locators or perform actions | Put `assert`/`expect` inside — assertions belong in tests |
| Name methods after what a user does | Name them after CSS |
| Keep waits inside if they're page-specific | Duplicate the same locator in two classes |

**The "no assertions in Page Objects" rule matters.** A Page Object describes the page. A test
decides what's correct. Mixing them makes Page Objects unreusable.

## Don't confuse: Page Object vs API client

Same pattern, different layer — you already built the API version in Track 3 #6:

| | Page Object | API client |
|---|---|---|
| Hides | Locators, clicks | URLs, headers, auth |
| Exposes | `create_task()` | `create()` |

---

# 10. Fixtures-first — the modern alternative 🟡

## The idea

Instead of a class per page, build **small fixtures around business actions**.

```python
@pytest.fixture
def logged_in_page(page):
    page.goto("https://qa1.airtap.ai/app")
    expect(page.get_by_placeholder("Chat with Airtap")).to_be_visible()
    return page


@pytest.fixture
def page_with_task(logged_in_page):
    logged_in_page.get_by_placeholder("Chat with Airtap").fill("test task")
    logged_in_page.get_by_role("button", name="Send message").click()
    return logged_in_page


def test_task_appears_in_thread(page_with_task):        # setup already done
    expect(page_with_task.get_by_role("listitem").first).to_be_visible()
```

Fixtures compose: `page` → `logged_in_page` → `page_with_task`. Each test asks for the state it
needs.

## Which to use

| | Page Object | Fixtures-first |
|---|---|---|
| Best for | Large suites, many pages | Small/medium suites |
| Strength | Locators organised by page | Less boilerplate; states compose naturally |
| 2026 guidance | Still standard for big suites | Preferred for small/medium |

**For Airtap:** keep the Page Objects — they exist and work. Add fixtures for *states*
(`logged_in_page`, `page_with_task`). That combination is genuinely good: Page Objects hold
locators, fixtures hold setup.

---

# 11. Flakiness 🔴

**A flaky test passes sometimes and fails sometimes with no code change.** They're worse than
failing tests, because people start ignoring failures.

## The causes, and the fixes

| Cause | Symptom | Fix |
|---|---|---|
| Fixed `sleep()` | Fails on slow runs | `expect()` with timeout |
| Acting before load | "element not found" | `wait_for_load_state`, or `expect` |
| Animations | Click lands wrong | Playwright waits for stability — but check CSS transitions |
| Shared state | Fails only in a certain order | Fresh context per test |
| Test order dependency | Fails alone, passes in suite | Each test sets up its own state |
| Real backend slowness | Random timeouts | Longer timeout, or mock (topic #12) |
| Non-deterministic AI | Different result each run | Assert on state, not exact text |

## Test-order dependency — Airtap has this today

```python
def test_app_page_launched(page):
    page.wait_for_url("https://airtap.ai/app")     # only passes because test 2 navigated
```

Run it alone and it fails. **The fix:**

```python
def test_app_page_launched(page):
    page.goto("https://airtap.ai/app")             # set up its own state
    ...
```

**A test that can't run alone is a flaky test waiting to happen** — and it blocks parallel runs
entirely.

## How to find flakiness

```bash
pytest --count=10 tests/test_smoke.py     # needs pytest-repeat
pytest -n 4                                # parallel exposes order dependencies fast
```

## Retry is not a fix

```bash
pytest --reruns 2
```

This **hides** flakiness. Reasonable as a temporary measure for a genuinely unstable external
dependency. Not a fix for a real problem.

**The interview answer:** *"I find out why it's flaky before I retry it. Retrying without root-causing
means you've traded a visible problem for an invisible one."* That's a senior/junior dividing line.

## The Airtap-specific one

Task execution is genuinely non-deterministic — the AI can take a different path each run and still
be correct.

```python
expect(thread).to_contain_text("The answer is 4")     # ❌ wording varies
expect(status).to_contain_text("Completed")            # ✅ state, not wording
```

Assert on **state**, not exact AI-generated text. (Track 8c covers this fully.)

---

# 12. Network interception 🟡

## What it does

Intercept requests the page makes, and change or fake the reply.

## Mock a backend response

```python
def test_empty_task_list(page):
    def handle(route):
        route.fulfill(json={"status": "Success", "tasks": []})

    page.route("**/taskGetList", handle)
    page.goto("https://qa1.airtap.ai/app")

    expect(page.get_by_text("No tasks yet")).to_be_visible()
```

Now you can test the empty state **without** deleting real data.

## Simulate errors

```python
page.route("**/taskCreate", lambda route: route.fulfill(status=500))
# then assert the UI shows a sensible error message
```

Testing "what does the UI do when the backend fails?" is otherwise very hard to trigger.

## Block heavy resources

```python
page.route("**/*.{png,jpg,mp4}", lambda route: route.abort())    # faster tests
```

## Watch without changing

```python
with page.expect_response("**/taskCreate") as info:
    submit_button.click()
assert info.value.status == 200
```

## The trade-off

Mocking makes tests fast and predictable — but **you're no longer testing the real system**. If the
backend changes its response shape, your mocked test still passes while production breaks.

**Good rule:** mock for edge cases that are hard to produce (errors, empty states). Use the real
backend for main flows.

---

# Putting it together

What a well-structured Airtap UI test could look like, using everything above:

```python
# tests/ui/test_task_creation.py
import pytest
from playwright.sync_api import expect
from pages import PilotAppPage


@pytest.mark.smoke
def test_composer_is_ready(logged_in_page):
    app = PilotAppPage(logged_in_page)

    expect(app.task_creation_input()).to_be_visible(timeout=15_000)
    expect(app.task_creation_submit_button()).to_be_enabled()


def test_creating_a_task_calls_the_api(logged_in_page, task_client):
    app = PilotAppPage(logged_in_page)

    # watch the network call the UI makes
    with logged_in_page.expect_response(lambda r: "taskCreate" in r.url) as info:
        app.task_creation_input().fill("what is 2 plus 2?")
        app.task_creation_submit_button().click()

    response = info.value
    assert response.status == 200
    task_id = response.json()["taskId"]

    # use the API to wait — faster and more reliable than watching the DOM
    details = wait_for_task(task_client, task_id, timeout=180)
    assert details["taskState"] in ("COMPLETED", "STOPPED")

    # then confirm the UI reflects it
    expect(logged_in_page.get_by_text("Completed")).to_be_visible(timeout=30_000)
```

**The key move:** the `wait_for_task` helper from [Track 3 #11](track_03_api_automation.md) does the
waiting via API, then the UI check confirms what the user sees. API for reliable waiting, UI for
what matters visually. That's the "combine API + UI" pattern from Track 5 — and it's a strong
senior-level answer.

---

# Quick-fire differentiation table

| Question | Answer |
|---|---|
| Browser vs context vs page | App / isolated session / tab |
| Why contexts? | Isolation without relaunching the browser — enables parallel |
| `assert` vs `expect` | `assert` checks once; `expect` retries until timeout |
| `get_by_role` vs CSS | Role survives restyling; CSS breaks on markup change |
| `exact=True` | Whole-string match instead of substring |
| Strict mode violation | Your locator matched several elements — narrow it |
| Auto-waiting vs explicit wait | Auto covers elements; explicit is for network/URL/load state |
| `sleep` vs `expect(timeout=)` | Sleep always waits the full time; expect returns as soon as ready |
| Persistent context vs `storageState` | Profile folder (local only, locks) vs state file (CI-friendly, parallel) |
| Page Object vs fixtures-first | Class per page vs composable state fixtures — both valid |
| Trace vs screenshot | Trace is a full steppable recording; screenshot is one frame |
| headless vs headed | No window (CI) vs visible window (debugging) |
| Mocking vs real backend | Fast and predictable vs actually testing the system |

---

# Practice checklist

Work inside `web-automation/`. Do these **without AI**.

**Understand what exists**
- [ ] Run the suite: `pytest -v`
- [ ] Draw the fixture chain: `page` → `browser_context` → `playwright_session`
- [ ] Run `test_app_page_launched` **alone** and see it fail — explain why
- [ ] Open Chrome with the `chrome-profile` folder, run the suite, and see the skip trigger

**Locators**
- [ ] Run `playwright codegen https://airtap.ai/` and compare its locators to `pages/`
- [ ] Add a locator for one element not yet covered, using `get_by_role`
- [ ] Deliberately write an ambiguous locator and read the strict-mode error

**Debugging**
- [ ] Run with `--tracing on` and open the trace with `playwright show-trace`
- [ ] Run with `PWDEBUG=1` and step through one test
- [ ] Break a locator on purpose and read the failure

**Fixes worth making**
- [ ] Replace `time.sleep(5)` with `expect(...).to_be_visible(timeout=...)`
- [ ] Make `test_app_page_launched` self-sufficient with its own `page.goto()`
- [ ] Add an environment switch so the suite can target qa1 instead of production

**Going further**
- [ ] Create `auth.json` with `storageState` and a fixture that uses it
- [ ] Add an action method (`create_task`) to `PilotAppPage`
- [ ] Write a test that watches the `taskCreate` network call with `expect_response`
- [ ] Mock `taskGetList` to return an empty list and check the empty state
