# Track 2 — Pytest

*Deep-dive for Track 2 of [00_master_study_plan.md](00_master_study_plan.md). Topics are in
learning order. Assumes [Track 1](track_01_python_for_automation.md) — especially decorators (#8)
and context managers (#9), since fixtures use both ideas.*

## What is pytest?

**pytest is Python's most-used testing framework.** You write plain functions; pytest finds them,
runs them, and tells you clearly what passed and what failed.

It is **not** a browser tool or an API tool. It's the **runner and organiser** underneath them.
Playwright clicks the buttons, `requests` calls the API — pytest decides what runs, in what order,
with what setup, and reports the result.

What it handles for you:

| Job | How it does it |
|---|---|
| **Find** your tests | Naming rules — no registration or config needed |
| **Run** them and **report** | One `pytest` command; failure output shows expected vs. actual |
| **Setup and cleanup** | Fixtures — shared, reusable, automatically cleaned up |
| **Same test, many inputs** | `parametrize` — 129 cases from one function |
| **Group and filter** | Markers — run only smoke, or skip slow tests |
| **Extend** | Plugins — parallel runs, HTML reports, retries, coverage |

**Why this track matters:** pytest is the foundation under both API testing (Track 3) and
Playwright (Track 4). Every fixture, every marker, every `parametrize` you'll write later is pytest.
Your original roadmap listed it as a "tool" — it's really the floor everything else stands on.

**Good news:** Airtap already has a working pytest suite at `web-automation/`. Almost every example
below is real code from it, so you can open the file and see it in context.

## Topic table

| # | Topic | Priority | Notes |
|---|---|---|---|
| 1 | Test discovery, naming, `assert` | 🔴 P0 | How pytest finds and runs your tests. |
| 2 | `pytest.ini` config + CLI flags | 🟠 P1 | Configure once, then daily-driver ergonomics. |
| 3 | **Fixtures** — definition, `yield` teardown, scope | 🔴 P0 | The single most important pytest concept. |
| 4 | `conftest.py` | 🔴 P0 | Where shared fixtures live. |
| 5 | `@pytest.mark.parametrize` | 🔴 P0 | One test, many inputs. Turns a 129-row checklist into 10 lines. |
| 6 | Markers + `-m` filtering | 🟠 P1 | Run subsets: smoke, regression, slow. |
| 7 | Fixture factories, `autouse` | 🟡 P2 | Patterns you'll want once the suite grows. |
| 8 | Plugins | 🟠 P1 | `xdist`, `html`, `asyncio`, `rerunfailures`, `cov`. |
| 9 | Hooks *(bonus)* | 🟡 P2 | Airtap's suite uses these — worth recognising. |

---

# 1. Test discovery, naming, and `assert` 🔴

## What "discovery" means

You don't tell pytest which tests to run. You just type:

```bash
pytest
```

...and it **goes looking** for tests by itself. It follows simple naming rules.

## The naming rules

| Thing | Must be named | Example |
|---|---|---|
| File | `test_*.py` or `*_test.py` | `test_smoke.py` ✅ |
| Function | `test_*` | `def test_login():` ✅ |
| Class (optional) | `Test*` | `class TestLogin:` ✅ |

If you name a file `smoke_tests.py`, **pytest will silently ignore it**. No error, no warning — it
just runs zero tests. This confuses almost everyone once.

## A real Airtap test

From `web-automation/tests/test_smoke.py`:

```python
def test_pilot_website_launched(page: Page) -> None:
    """Marketing website loads and the Try it CTA is interactable."""
    pilot_website = PilotWebsite(page)

    assert page.url == "https://airtap.ai/", "Pilot website URL is not correct"
```

Three things to notice:
1. File is `test_smoke.py` ✅
2. Function starts with `test_` ✅
3. `page` appears as an argument — that's a **fixture** (topic #3). pytest fills it in for you.

## `assert` — plain Python, no special methods

Other test frameworks make you learn methods like `assertEqual`. Pytest just uses Python's built-in
`assert`:

```python
assert page.url == "https://airtap.ai/"
assert response.status_code == 200
assert "COMPLETED" in task["state"]
assert len(steps) > 0
```

**Add a message after a comma.** It shows up when the test fails:

```python
assert page.url == "https://airtap.ai/", "Pilot website URL is not correct"
```

## Why pytest's assert is special

Normally `assert x == y` just tells you "assertion failed." Pytest **rewrites** it behind the
scenes to show you the actual values:

```
E       AssertionError: Pilot website URL is not correct
E       assert 'https://airtap.ai/app' == 'https://airtap.ai/'
E         - https://airtap.ai/
E         + https://airtap.ai/app
```

You immediately see what it got vs. what it expected. That's free — you don't do anything.

## Running tests

```bash
pytest                          # everything
pytest tests/test_smoke.py      # one file
pytest tests/test_smoke.py::test_app_page_launched     # one test
```

## Reading the output

```
tests/test_smoke.py ..F                                        [100%]
```

- `.` = passed
- `F` = failed
- `s` = skipped
- `E` = error during setup (the test never even ran)

**`F` vs `E` matters.** `F` means your test ran and the assertion was wrong. `E` means setup broke
— usually a fixture failed, so the test body never executed.

---

# 2. `pytest.ini` and CLI flags 🟠

## What `pytest.ini` is

A small config file at your project root. It saves you from typing the same options every time.

Airtap's real one — `web-automation/pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = .
addopts = -ra
```

Line by line:

| Line | What it does |
|---|---|
| `[pytest]` | Section header — required |
| `testpaths = tests` | Only look in the `tests/` folder. Faster, and won't pick up stray files |
| `pythonpath = .` | Add the project root to Python's import path — this is what makes `from pages import PilotAppPage` work |
| `addopts = -ra` | Always add these flags. `-ra` shows a summary of everything that didn't pass |

**`pythonpath = .` is the one that saves you pain.** Without it, importing your own `pages/` folder
from inside `tests/` fails with `ModuleNotFoundError`.

## The flags you'll actually use daily

| Flag | What it does | When |
|---|---|---|
| `-v` | Verbose — show each test name and result | Almost always |
| `-x` | Stop at the first failure | Debugging — don't wait for 50 more failures |
| `-k "login"` | Only run tests whose *name* contains "login" | Focus on one area |
| `--lf` | Last failed — rerun only what failed last time | The fastest debug loop there is |
| `-s` | Show `print()` output | When you're printf-debugging |
| `--tb=short` | Shorter tracebacks | When output is overwhelming |
| `--collect-only` | List tests without running them | "Is pytest even finding my test?" |

## The debug loop worth memorising

```bash
pytest              # 3 failures
pytest --lf -x -v   # rerun only those 3, stop at the first, show names
```

Fix, repeat. You never re-run the passing 200 tests while debugging.

## `-k` is smarter than it looks

```bash
pytest -k "login"                 # name contains "login"
pytest -k "login and not slow"    # contains login, doesn't contain slow
pytest -k "smoke or api"          # either
```

---

# 3. Fixtures 🔴

**The most important topic in this track.** A fixture is setup code that pytest runs *for* you and
hands to your test.

## The problem fixtures solve

Without fixtures, every test repeats the same setup:

```python
def test_one():
    browser = launch_browser()        # repeated
    page = browser.new_page()         # repeated
    ...
    browser.close()                   # repeated

def test_two():
    browser = launch_browser()        # repeated again
    page = browser.new_page()         # repeated again
    ...
    browser.close()                   # repeated again
```

## The fixture version

```python
import pytest

@pytest.fixture
def page():
    browser = launch_browser()
    yield browser.new_page()      # hand it to the test
    browser.close()               # cleanup, after the test finishes


def test_one(page):               # just ask for it by name
    page.goto("https://airtap.ai/")

def test_two(page):               # pytest builds a fresh one
    page.goto("https://airtap.ai/app")
```

**How pytest connects them:** it looks at your test's argument names. `def test_one(page)` means
"find a fixture called `page` and give me its value." Nothing else — just the name matching.

## `yield` is the setup/teardown split

This shape should look familiar from [Track 1 #9](track_01_python_for_automation.md) (context
managers) — it's the same idea:

```python
@pytest.fixture
def api_session():
    session = requests.Session()          # ← SETUP: before the test
    session.headers["Authorization"] = f"Bearer {TOKEN}"
    yield session                          # ← the test runs here
    session.close()                        # ← TEARDOWN: after the test
```

Everything before `yield` runs before the test. Everything after runs when the test finishes —
**even if the test failed.**

## Scope — how often the setup runs

This is the part people get wrong. Scope controls how *often* pytest rebuilds the fixture.

| Scope | Rebuilt | Use for |
|---|---|---|
| `function` *(default)* | Before **every test** | Anything that must be clean per test |
| `class` | Once per test class | Shared setup within a group |
| `module` | Once per test **file** | Expensive setup shared by one file |
| `session` | **Once** for the whole run | Very expensive things — browsers, DB connections |

```python
@pytest.fixture(scope="session")
def expensive_thing():
    ...
```

## The real Airtap example

From `web-automation/tests/conftest.py` — three fixtures, chained together:

```python
@pytest.fixture(scope="session")
def playwright_session():
    with sync_playwright() as playwright:
        yield playwright                    # started ONCE for the whole run


@pytest.fixture(scope="session")
def browser_context(playwright_session):    # ← asks for the fixture above
    context = launch_chrome_persistent_context(playwright_session)
    page = context.pages[0] if context.pages else context.new_page()
    page.goto(PILOT_WEBSITE_URL, wait_until="domcontentloaded", timeout=60_000)
    yield context
    context.close()                          # closed ONCE at the end


@pytest.fixture                              # no scope = function scope
def page(browser_context):                   # ← asks for the fixture above
    yield browser_context.pages[0] if browser_context.pages else browser_context.new_page()
```

**Read the chain bottom-up:**

```
test_app_page_launched(page)
        ↓ needs
      page                (function scope — fresh reference per test)
        ↓ needs
   browser_context        (session scope — one browser for the whole run)
        ↓ needs
 playwright_session       (session scope — started once)
```

**Why these scopes?** Launching Chrome takes seconds. Doing it before all three smoke tests instead
of before each one saves real time. But `page` is cheap, so it stays function-scoped.

**Fixtures can depend on fixtures.** You just name them as arguments, same as a test does. pytest
works out the order and builds them for you.

## Fixtures can skip tests

Also from Airtap's conftest:

```python
@pytest.fixture(scope="session")
def browser_context(playwright_session):
    if (CHROME_PROFILE_DIR / "SingletonLock").exists():
        pytest.skip("chrome-profile is locked (Chrome already using that user-data dir).")
    ...
```

If Chrome is already open using that profile, the tests **skip** with a clear reason instead of
failing confusingly. That's a genuinely good pattern — a skip with a message is much better than a
crash someone has to decode.

## The scope trap

A `session`-scoped fixture holding **changeable** data is shared by every test:

```python
@pytest.fixture(scope="session")
def test_payload():
    return {"prompt": "test", "options": {"timeout": 30}}    # ⚠️ shared!
```

If test one modifies it, test two gets the modified version. This is exactly the mutable-shared-data
bug from [Track 1 #12](track_01_python_for_automation.md).

**Rule:** session scope is for *expensive connections* (browsers, sessions). Use function scope for
*data*.

---

# 4. `conftest.py` 🔴

## What it is

A special file where you put fixtures you want to **share across multiple test files**. You never
import it — pytest finds it automatically.

## How discovery works

pytest looks for `conftest.py` in the test's folder, then every folder above it:

```
web-automation/
├── conftest.py            ← available to EVERYTHING below
└── tests/
    ├── conftest.py        ← available to everything in tests/
    ├── test_smoke.py
    └── api/
        ├── conftest.py    ← available only inside api/
        └── test_tasks.py
```

A test in `api/test_tasks.py` can use fixtures from **all three** conftest files. Closest wins if
names clash.

## Why you don't import it

```python
from conftest import page      # ❌ never do this
```

```python
def test_something(page):      # ✅ just ask for it by name
    ...
```

pytest injects it. Importing it manually breaks things in confusing ways.

## What goes where

| Put it in... | When |
|---|---|
| The test file itself | Only that file uses it |
| `tests/conftest.py` | Several test files use it |
| Root `conftest.py` | Everything uses it, or you need project-wide config |

## Airtap's structure

`web-automation/tests/conftest.py` holds the browser fixtures — so all three test files in
`test_smoke.py` get `page` without any imports.

**When you add an API suite** (Track 3), the natural layout is:

```
tests/
├── conftest.py          ← shared: environment config, auth token
├── ui/
│   └── conftest.py      ← browser fixtures move here
└── api/
    └── conftest.py      ← api_client fixture lives here
```

---

# 5. `@pytest.mark.parametrize` 🔴

## What it does

Run the **same test** with **different inputs**, without copy-pasting.

## The problem

```python
def test_rrule_weekday():
    assert to_rrule("Every weekday at 8:30 AM") == "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;..."

def test_rrule_monday():
    assert to_rrule("Every Monday at 9 AM") == "RRULE:FREQ=WEEKLY;BYDAY=MO;..."

def test_rrule_daily():
    assert to_rrule("Every day at 9 AM") == "RRULE:FREQ=DAILY;BYHOUR=9;BYMINUTE=0"
# ...126 more of these
```

## The fix

```python
import pytest

@pytest.mark.parametrize("prompt, expected", [
    ("Every weekday at 8:30 AM", "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=8;BYMINUTE=30"),
    ("Every Monday at 9 AM",     "RRULE:FREQ=WEEKLY;BYDAY=MO;BYHOUR=9;BYMINUTE=0"),
    ("Every day at 9 AM",        "RRULE:FREQ=DAILY;BYHOUR=9;BYMINUTE=0"),
])
def test_rrule_generation(prompt, expected):
    assert to_rrule(prompt) == expected
```

**This is a real Airtap opportunity.** `pilot/manual-custom-routine-rrule-ai-test-cases.md`
contains **129 rows** of schedule prompts and their expected RRULE output — written by hand, run
manually today. That entire file can become one parametrized test.

## How it reads

```python
@pytest.mark.parametrize("prompt, expected", [ ... ])
                          ^^^^^^^^^^^^^^^^   ^^^^^
                          argument names     list of value-pairs
```

Each tuple in the list becomes one test run. Three tuples = three tests.

## Output

```
test_rrule_generation[Every weekday at 8:30 AM-RRULE:FREQ=WEEKLY...] PASSED
test_rrule_generation[Every Monday at 9 AM-RRULE:FREQ=WEEKLY...]     PASSED
test_rrule_generation[Every day at 9 AM-RRULE:FREQ=DAILY...]         FAILED
```

**Each case is its own test.** One failing case doesn't stop the others, and you can rerun just
that one:

```bash
pytest -k "Every day at 9 AM"
```

## Readable IDs

Long parameters make ugly names. Use `ids` to label them:

```python
@pytest.mark.parametrize("prompt, expected", [
    ("Every weekday at 8:30 AM", "RRULE:FREQ=WEEKLY;..."),
    ("Every day at 9 AM",        "RRULE:FREQ=DAILY;..."),
], ids=["weekday-morning", "daily-9am"])
```

```
test_rrule_generation[weekday-morning] PASSED
test_rrule_generation[daily-9am]       PASSED
```

## Loading cases from a file

For 129 cases you don't paste them into the test. Load them:

```python
import json
from pathlib import Path

CASES = json.loads(Path("data/rrule_cases.json").read_text())

@pytest.mark.parametrize("case", CASES, ids=lambda c: c["prompt"][:40])
def test_rrule_generation(case):
    assert to_rrule(case["prompt"]) == case["expected"]
```

Now adding a test case means adding one line to a data file — no code change.

## Negative cases too

The same file has an **Invalid Prompts** section. Those become their own parametrized test:

```python
@pytest.mark.parametrize("bad_prompt", [
    "Every day at 25:00",
    "Sometime soon",
    "Every 32nd of the month",
])
def test_invalid_schedule_is_rejected(bad_prompt):
    with pytest.raises(ValueError):
        to_rrule(bad_prompt)
```

## `pytest.raises` — testing that something fails

```python
with pytest.raises(ValueError):
    to_rrule("Every day at 25:00")
```

Reads as: *"I expect this block to raise a ValueError. If it doesn't, fail the test."*

Check the message too:

```python
with pytest.raises(ValueError, match="invalid hour"):
    to_rrule("Every day at 25:00")
```

## Stacking parametrize

Two decorators = every combination:

```python
@pytest.mark.parametrize("receiver", ["cloud", "physical"])
@pytest.mark.parametrize("model", ["airtap-1.0", "airtap-1.1"])
def test_task_creation(receiver, model):
    ...
```

That's 2 × 2 = **4 tests**. Useful, but be careful — combinations multiply fast.

---

# 6. Markers 🟠

## What they are

Labels you stick on tests so you can run groups of them.

```python
@pytest.mark.smoke
def test_pilot_website_launched(page):
    ...

@pytest.mark.slow
def test_full_task_execution(page):
    ...
```

## Running by marker

```bash
pytest -m smoke              # only smoke tests
pytest -m "not slow"         # everything except slow ones
pytest -m "smoke or api"     # either
```

## Register them (or you get warnings)

Add to `pytest.ini`:

```ini
[pytest]
testpaths = tests
pythonpath = .
addopts = -ra
markers =
    smoke: quick checks that must always pass
    regression: full suite, slower
    slow: takes over 30 seconds
    ui: needs a browser
    api: API only, no browser
```

Without this, pytest warns `PytestUnknownMarkWarning` on every run.

## Built-in markers worth knowing

**Skip — never run this:**

```python
@pytest.mark.skip(reason="feature not built yet")
def test_device_pairing():
    ...
```

**Skipif — skip under a condition:**

```python
@pytest.mark.skipif(os.getenv("ENV") == "prod", reason="don't create tasks in production")
def test_task_creation():
    ...
```

That one is genuinely useful for Airtap — some tests should never run against production.

**xfail — expected to fail:**

```python
@pytest.mark.xfail(reason="known bug AT-1234")
def test_known_broken():
    ...
```

It runs, but a failure doesn't break the build. Better than `skip` for a known bug, because if
someone fixes it you get `XPASS` and know to remove the marker.

## Why markers matter for CI

A realistic setup:

```bash
# on every commit — fast
pytest -m "smoke and not slow"

# nightly — everything
pytest
```

---

# 7. Fixture factories and `autouse` 🟡

## Fixture factories — when the test needs to pass arguments

A normal fixture gives you one fixed thing. Sometimes you need it customised per test.

**The trick: return a function.** (This is the "function returning a function" idea from
[Track 1 #8](track_01_python_for_automation.md).)

```python
@pytest.fixture
def make_task_payload():
    def _make(prompt, receiver="cloud", timeout=120):
        return {"prompt": prompt, "receiverType": receiver, "timeoutSec": timeout}
    return _make                    # return the function itself


def test_cloud_task(make_task_payload):
    payload = make_task_payload("check the weather")
    ...

def test_physical_task(make_task_payload):
    payload = make_task_payload("open settings", receiver="physical")
    ...
```

Each test builds exactly the data it needs — and each gets a **fresh dict**, avoiding the shared-data
bug from Track 1 #12.

## Factories with cleanup

The really useful version tracks what it created and cleans up afterwards:

```python
@pytest.fixture
def created_task(api_client):
    created = []

    def _create(prompt):
        task = api_client.create_task(prompt)
        created.append(task["id"])
        return task

    yield _create                             # tests use it here

    for task_id in created:                   # cleanup runs no matter what
        api_client.delete_task(task_id)
```

Every task any test creates gets deleted — even if the test failed. This keeps your QA environment
clean.

## `autouse` — a fixture that runs without being asked

```python
@pytest.fixture(autouse=True)
def log_test_boundaries(request):
    logger.info("START %s", request.node.nodeid)
    yield
    logger.info("END %s", request.node.nodeid)
```

Every test in scope now logs its start and end — no test has to ask for it.

**Use sparingly.** Autouse fixtures are invisible: someone reading a test can't see what's running.
Good for logging and environment checks. Bad for anything that changes test data.

---

# 8. Plugins 🟠

Install with pip, and they mostly just work.

| Plugin | What it does | Command |
|---|---|---|
| `pytest-html` | HTML report file | `pytest --html=report.html` |
| `pytest-xdist` | Run tests in parallel | `pytest -n 4` |
| `pytest-rerunfailures` | Auto-retry failures | `pytest --reruns 2` |
| `pytest-cov` | Coverage report | `pytest --cov=pages` |
| `pytest-asyncio` | Lets you write `async def` tests | `@pytest.mark.asyncio` |
| `pytest-playwright` | Playwright fixtures (`page`, `browser`) | Used in Track 4 |

**Airtap already produces `web-automation/report.html`** — that's `pytest-html`.

## `pytest-xdist` — parallel runs

```bash
pytest -n 4         # 4 workers
pytest -n auto      # one per CPU core
```

**The catch:** tests must be independent. If test A creates data that test B expects, parallel runs
break them — because the order is no longer guaranteed. This is why "no shared mutable state"
matters.

Also relevant here: this is what the GIL discussion in [Track 1 #15](track_01_python_for_automation.md)
is about. You never hand-roll threads for tests. `xdist` does it.

## `pytest-rerunfailures` — use with care

```bash
pytest --reruns 2
```

This hides flakiness rather than fixing it. It's a reasonable stopgap for a known-flaky external
dependency. It is **not** a fix for a real bug — and being able to explain that difference is a
senior/junior dividing line (covered in Track 5).

---

# 9. Hooks *(bonus — Airtap uses these)* 🟡

You don't need to write these early, but Airtap's `conftest.py` has three, so it helps to recognise
them.

**A hook is a function with a special name that pytest calls automatically** at a specific moment.

## The real ones from Airtap's conftest

```python
def pytest_configure(config):
    """Runs ONCE, before any tests. Airtap uses it to set up logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ...
    logger.addHandler(logging.FileHandler(LOG_DIR / f"test_run_{timestamp}.log"))
```

This is why you see `web-automation/logs/test_run_20260615_080510.log` — a fresh timestamped log
file per run.

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item):
    logger.info("START %s", item.nodeid)
    yield


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item):
    yield
    logger.info("END %s", item.nodeid)
    logger.info("----------")
```

These run around **every** test, writing `START`/`END` markers into the log.

## Common hooks

| Hook | When it runs |
|---|---|
| `pytest_configure` | Once, at startup |
| `pytest_runtest_setup` | Before each test |
| `pytest_runtest_teardown` | After each test |
| `pytest_addoption` | Add your own CLI flags (e.g. `--env=qa1`) |

`pytest_addoption` is the one you'll want soon — it's how you add `--env qa1` to switch which Airtap
environment the suite runs against.

## Hook vs fixture

- **Fixture** = gives your test a *thing* (a page, a client, data)
- **Hook** = runs *behaviour* at a lifecycle moment (logging, setup, reporting)

---

# One real anti-pattern from Airtap's own suite

At the end of `test_app_page_launched`:

```python
time.sleep(5)  # Wait for the cloudphone video UI to load
```

**Why this is bad:**
- If the UI loads in 1 second, you waste 4 seconds — every run, forever
- If it takes 6 seconds, the test fails anyway
- It hides *what* you're actually waiting for

**The fix — wait for a condition, not a duration:**

```python
expect(pilot_app_page.cloudphone_video_ui()).to_be_visible(timeout=15_000)
```

This returns as soon as the thing appears, and fails clearly if it doesn't within 15 seconds.

**The rule: never sleep, always wait for a condition.** This is one of the most common causes of
both slow suites and flaky suites — and spotting it in Airtap's own code is a genuinely good thing
to be able to say in an interview.

---

# Quick-fire differentiation table

| Question | Answer |
|---|---|
| Fixture vs hook | Fixture gives the test a *thing*; hook runs *behaviour* at a lifecycle moment |
| `yield` vs `return` in a fixture | `yield` lets you run teardown after; `return` gives no teardown |
| function vs session scope | Function = rebuilt per test (safe); session = built once (fast, but shared) |
| `conftest.py` vs a normal module | conftest is auto-discovered — never import it |
| `skip` vs `xfail` | Skip never runs; xfail runs and tolerates failure |
| Marker vs `-k` | Marker is a label you add; `-k` matches the test *name* |
| `F` vs `E` in output | `F` = assertion failed; `E` = setup/fixture broke before the test ran |
| `parametrize` vs a loop in the test | Parametrize makes each case its own test; a loop stops at the first failure |
| `--reruns` vs fixing flakiness | Reruns hide the symptom; only root-causing fixes it |
| Why `pythonpath = .`? | So `tests/` can import your own `pages/` folder |

---

# Practice checklist

Do these **without AI**, ideally inside `web-automation/`.

**Basics**
- [ ] Run the existing Airtap suite: `pytest -v`
- [ ] Run just one test by node ID
- [ ] Deliberately break an assertion and read the diff pytest prints
- [ ] Rename a test file to `smoke.py` and watch pytest find nothing — then rename it back

**Flags**
- [ ] Use `--collect-only` to list tests without running them
- [ ] Break two tests, then use `pytest --lf -x` to rerun only those

**Fixtures**
- [ ] Draw the fixture chain in Airtap's `conftest.py` on paper (`page` → ? → ?)
- [ ] Write a fixture that prints "setup" and "teardown" around a test
- [ ] Make the test fail on purpose — confirm teardown still runs
- [ ] Change a fixture from `function` to `session` scope and observe how many times setup prints

**Parametrize**
- [ ] Write a parametrized test with 5 cases
- [ ] Add `ids` so the output is readable
- [ ] Convert 10 rows from `manual-custom-routine-rrule-ai-test-cases.md` into a parametrized test
- [ ] Write a `pytest.raises` test for an invalid schedule prompt

**Markers**
- [ ] Add a `smoke` marker to one Airtap test and register it in `pytest.ini`
- [ ] Run `pytest -m smoke` and confirm only that one runs

**Going further**
- [ ] Write a fixture factory that builds a task payload with defaults
- [ ] Replace the `time.sleep(5)` in `test_app_page_launched` with a proper condition wait
- [ ] Install `pytest-xdist` and run the suite with `-n 2`
