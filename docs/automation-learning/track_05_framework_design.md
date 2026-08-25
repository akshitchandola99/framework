# Track 5 — Framework Design & Test Architecture

*Deep-dive for Track 5 of [00_master_study_plan.md](00_master_study_plan.md). Assumes
[Track 1](track_01_python_for_automation.md)–[Track 4](track_04_playwright.md). This is where the
pieces become one maintainable thing.*

## What this track is about

Tracks 2–4 taught you to write tests. This track is about **the container they live in**.

| | A folder of scripts | A framework |
|---|---|---|
| Change environment | Edit 50 files | Change one env var |
| Add a test | Copy-paste setup | Ask for a fixture |
| A locator changes | Fix it everywhere | Fix it once |
| New person joins | "Ask Akshit" | Read the README, run it |

**The honest test:** could someone else clone your repo and add a test tomorrow without asking you
anything? That's the difference.

## How this document is organised

1. **Topics 1–10** — the concepts, each with what Airtap's existing suite does well or badly
2. **Part A** — building the API framework from zero, step by step
3. **Part B** — building the Playwright framework from zero, step by step
4. **Part C** — merging both into one repo
5. **The Airtap scorecard** — a consolidated review

Throughout, the perspective is **"you are building this from scratch."** Airtap's `web-automation/`
already exists and does several things genuinely well — but you'll learn more by understanding
*why* each decision was made than by inheriting it.

## Topic table

| # | Topic | Priority | Notes |
|---|---|---|---|
| 1 | Test strategy — what to automate | 🟠 P1 | Decide before you build. |
| 2 | Project structure | 🔴 P0 | Folders that scale. |
| 3 | Environment/config management | 🔴 P0 | Never hardcode a URL. |
| 4 | Maintainable test code | 🟠 P1 | Applies from line one. |
| 5 | Test data strategy | 🟠 P1 | Create it, clean it up. |
| 6 | **Combining API + UI** | 🔴 P0 | The senior-level pattern. |
| 7 | Logging | 🟠 P1 | |
| 8 | Reporting | 🟠 P1 | `pytest-html`, Allure. |
| 9 | Parallel execution | 🟠 P1 | And what makes it safe. |
| 10 | **Flaky test root-causing** | 🔴 P0 | Senior/junior dividing line. |

---

# 1. Test strategy — decide before you build 🟠

## The question

**Not** "how do I automate this?" but **"should I?"**

Automating everything is a classic mistake. Every test costs time to write *and* time to maintain
forever.

## The test pyramid

```
        /\        E2E (slow, brittle, few)
       /  \
      /----\      Integration / API  (fast, stable, many)
     /      \
    /--------\    Unit (instant, most)
```

**Wide at the bottom, narrow at the top.** Most teams get this upside-down — lots of slow UI tests,
almost no API tests. That's the "ice cream cone" anti-pattern.

## What to automate

| Automate | Leave manual |
|---|---|
| Runs every release | Runs once |
| Clear pass/fail | Needs human judgment ("does this look right?") |
| High risk if broken | Cosmetic |
| Boring and repetitive | Exploratory |
| Stable feature | Changing weekly |

## The ROI test

> Will this test save more time than it costs to write and maintain?

A test you rerun 200 times: worth it. A test for a feature being redesigned next month: not yet.

## Applied to Airtap

| Area | Where it belongs | Why |
|---|---|---|
| Task creation, cancel, list | **API** | Fast, stable, no browser needed |
| RRULE schedule parsing (129 cases) | **API** | Pure input→output. Perfect for `parametrize` |
| Auth: no token, bad token, waitlisted | **API** | Instant, and includes security checks |
| Login flow | **UI** | Genuinely a browser flow |
| Composer renders, task thread updates | **UI** | Visual, user-facing |
| Grounding accuracy (did the tap land right?) | **Manual + eval** | Needs judgment; non-deterministic |
| Dongle/BLE/hardware | **Manual** | Physical. No software substitute |

**The judgement call worth stating in an interview:** *"I'd put roughly 70% of Airtap's automation
at the API layer, because task lifecycle logic is where the risk is and the API tests it in
milliseconds. UI tests cover only what the user actually sees."*

## ⚠️ Airtap today

The existing suite is **100% UI, 0% API**, and all three tests are "does the page render". That's
inverted from where the value is. The single highest-impact change is adding an API layer.

---

# 2. Project structure 🔴

## The goal

Someone opens the repo and knows where things go without asking.

## Recommended layout

```
airtap-automation/
├── README.md                  ← how to run it. Non-negotiable.
├── requirements.txt           ← pinned dependencies
├── pytest.ini                 ← config + markers
├── .gitignore
├── .env.example               ← which variables are needed (no secrets)
│
├── config/
│   └── settings.py            ← URLs, tokens, timeouts — from env vars
│
├── api_clients/               ← package (Track 3 #6)
│   ├── __init__.py
│   ├── base_client.py
│   ├── task_client.py
│   └── routine_client.py
│
├── pages/                     ← package (Track 4 #9)
│   ├── __init__.py
│   ├── pilot_app_page.py
│   └── pilot_website_page.py
│
├── helpers/
│   ├── __init__.py
│   ├── assertions.py          ← assert_success()
│   └── polling.py             ← wait_for_task()
│
├── schemas/
│   └── task_schemas.py        ← JSON Schemas
│
├── data/
│   └── rrule_cases.json       ← the 129 test cases
│
└── tests/
    ├── conftest.py            ← shared fixtures
    ├── api/
    │   ├── conftest.py        ← api_client fixture
    │   └── test_tasks.py
    └── ui/
        ├── conftest.py        ← browser fixtures
        └── test_task_creation.py
```

## The rules

| Rule | Why |
|---|---|
| One folder per concern | You know where to look |
| `tests/` contains **only** tests | No helpers hiding among tests |
| Split `api/` and `ui/` | Run them separately; different fixtures |
| Every package gets `__init__.py` | It's a package, not a folder |
| Config in one place | One edit to switch environments |

## Airtap review

**✅ Does well**

```
web-automation/
├── pages/                ← proper package with __init__.py
│   ├── __init__.py       ← re-exports for clean imports
│   ├── pilot_app_page.py
│   └── pilot_website_page.py
├── tests/
│   ├── conftest.py
│   └── test_smoke.py
├── browser_config.py     ← launch config separated out
└── pytest.ini
```

Page Objects properly separated. `pytest.ini` sets `pythonpath = .` so imports work. `.gitignore`
correctly excludes `chrome-profile/`, `logs/`, `.venv/`, `report.html`.

**❌ Missing**

| Gap | Impact |
|---|---|
| **No `requirements.txt`** | Nobody can reproduce your environment. Biggest gap. |
| **No README** | New person can't run it without asking |
| No `config/` | URLs hardcoded in `conftest.py` (see #3) |
| No `api_clients/` | No API layer at all |
| No `helpers/` or `schemas/` | Nowhere for shared logic to live yet |
| No `api/` vs `ui/` split | Fine at 3 tests; breaks at 30 |

**Fix first:** `pip freeze > requirements.txt` and a 10-line README. Ten minutes' work, removes the
two biggest onboarding blockers.

---

# 3. Environment and config 🔴

## The rule

**Never hardcode a URL, token, or timeout in a test.**

## Why

```python
page.goto("https://airtap.ai/")     # ❌ in 40 files
```

Now test against qa2 → edit 40 files. Also: you're testing **production**.

## The pattern

```python
# config/settings.py
import os

ENVIRONMENTS = {
    "qa1":  "https://qa1.airtap.ai",
    "qa2":  "https://qa2.airtap.ai",
    "prod": "https://airtap.ai",
}

ENV = os.getenv("AIRTAP_ENV", "qa1")          # default to qa1, NOT prod
BASE_URL = ENVIRONMENTS[ENV]
PAT = os.environ["AIRTAP_PAT"]                 # no default — fail loudly if missing

DEFAULT_TIMEOUT_MS = 15_000
TASK_POLL_TIMEOUT_S = 180
```

Switching environment:

```bash
AIRTAP_ENV=qa2 pytest
```

## Two deliberate choices above

**Default to qa1, not prod.** If someone forgets the variable, they hit QA — not production.

**`os.environ[...]` for the token, `os.getenv(...)` for the environment.** A missing token should
crash immediately with a clear error, not fail 30 tests later with a confusing 401.

## Documenting the variables

```bash
# .env.example  — committed. Real .env is gitignored.
AIRTAP_ENV=qa1
AIRTAP_PAT=at-pat-your-token-here
```

## ⚠️ Airtap review

**This is the clearest problem in the existing suite.** From `tests/conftest.py`:

```python
PILOT_WEBSITE_URL = "https://airtap.ai/"
PILOT_APP_URL = "https://airtap.ai/app"
```

And from `browser_config.py`:

```python
"headless": False,      # ← hardcoded; will not run in CI
```

**Three consequences:**

| Problem | Consequence |
|---|---|
| Hardcoded to `airtap.ai` | The suite tests **production** |
| No environment switch | Can't point at qa1/qa2 |
| `headless: False` | Can't run in CI — there's no screen |

**The fix** — small, high value:

```python
# config/settings.py
BASE_URL = ENVIRONMENTS[os.getenv("AIRTAP_ENV", "qa1")]
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
```

```python
# conftest.py
page.goto(f"{BASE_URL}/", wait_until="domcontentloaded")
```

---

# 4. Writing maintainable test code 🟠

## Naming

```python
def test_1():                          # ❌ meaningless
def test_task():                       # ❌ what about it?
def test_task_creation_returns_id():   # ✅ says what it proves
```

**A good test name reads as a sentence about behaviour.** When it fails in CI, the name alone
should tell you what broke.

Airtap does this well:

```python
def test_pilot_website_launched(page)
def test_home_to_app_navigation(page)
def test_app_page_launched(page)
```

## Arrange–Act–Assert

```python
def test_task_creation_returns_id(task_client):
    payload = make_task_payload("hello")            # Arrange

    resp = task_client.create(**payload)             # Act

    assert resp.status_code == 200                   # Assert
    assert resp.json()["taskId"]
```

Three visual blocks. Easy to scan.

## One reason to fail

```python
def test_everything(task_client):        # ❌ if it fails, which part?
    create_task()
    check_list()
    cancel_task()
    check_deleted()
```

Split into four tests. Each failure names itself.

**Nuance:** a *workflow* test that genuinely tests a sequence is fine — but then the name should say
so (`test_task_lifecycle_create_to_cancel`), and it should be one flow, not four unrelated checks.

## DRY — but don't over-abstract

Repetition is bad. **Over-abstraction is worse.**

```python
# ❌ over-abstracted — nobody can read this
def test_generic(runner, cfg, exp):
    assert runner.execute(cfg).matches(exp)
```

You can't tell what it tests without opening three other files.

> **Rule of thumb:** a test should be readable top-to-bottom without jumping to other files.
> Helpers should remove *noise* (auth, URLs, waiting), never *meaning*.

## Assertion messages

```python
assert resp.status_code == 200
# AssertionError: assert 401 == 200          ← 401 where? why?

assert resp.status_code == 200, f"taskCreate failed: {resp.text[:200]}"
# AssertionError: taskCreate failed: {"status":"FailureTokenExpired"...}
```

Airtap does this consistently, including on Playwright assertions:

```python
expect(cta, "Try it CTA is not visible").to_be_visible(timeout=15_000)
```

## Airtap review

**✅ Genuinely good practice on show**

- Type hints everywhere: `def hello_user_heading(self) -> Locator:`
- `from __future__ import annotations` at the top of every file
- Docstrings: `"""Marketing website loads and the Try it CTA is interactable."""`
- Comments explaining *why*, e.g. `# Ex: "Hello Alex" - user name varies.`
- Descriptive assertion messages throughout

**⚠️ One thing to reconsider — the logging style**

```python
assert page.url == "https://airtap.ai/", "Pilot website URL is not correct"
logger.info("Passed: pilot website URL is https://airtap.ai/")

cta = pilot_website.try_airtap_link()
expect(cta, "Try it CTA is not visible").to_be_visible(timeout=15_000)
logger.info("Passed: Try it CTA is visible")
```

Every assertion is followed by a manual "Passed" log. It works — but:

- It's **duplicate information**. pytest already reports pass/fail, and `-v` names each test.
- It **doubles the length** of every test, burying the actual logic.
- It's **manual** — easy to forget, or to leave stale after an edit.

**Better:** let pytest report results, and use the trace viewer (Track 4 #6) for detail. Keep
logging for things pytest *doesn't* know — the environment, a generated task ID, a retry.

```python
logger.info("Running against %s as %s", BASE_URL, ENV)
logger.info("Created task %s", task_id)
```

That's the useful half, without the noise.

---

# 5. Test data strategy 🟠

## Three questions

1. Where does the data come from?
2. Does it collide with other tests?
3. Who cleans it up?

## Where it comes from

| Approach | Good | Bad |
|---|---|---|
| Hardcoded in the test | Simple | Collides, unclear intent |
| Builder function | Fresh each time, readable | — |
| Fixture factory | Adds cleanup | Slightly more setup |
| Loaded from file | Great for big sets (129 RRULE cases) | — |

## Make it unique

Two tests creating "Test Routine" will collide.

```python
from faker import Faker
fake = Faker()

def make_routine_name():
    return f"qa-{fake.uuid4()[:8]}"     # qa-3f8a91b2
```

The `qa-` prefix also makes leftover data easy to spot and bulk-delete.

## Clean up — always

```python
@pytest.fixture
def created_task(task_client):
    created = []

    def _create(text="test"):
        task_id = assert_success(task_client.create({"text": text}))["taskId"]
        created.append(task_id)
        return task_id

    yield _create

    for task_id in created:
        task_client.cancel(task_id)      # runs even if the test failed
```

**The `yield` placement matters** (Track 2 #3): cleanup after `yield` runs on failure too.

## ⚠️ Airtap-specific: cleanup is not optional

Every task you create:
- Runs a **real AI agent** — real LLM cost, real minutes
- Sits in a **shared QA environment** other people use
- Counts against a **daily credit limit** that resets at UTC midnight

Two habits that follow:

```python
task_client.create({"text": "..."}, cancelAfterSteps=3)     # cap the cost
```

and always cancel what you create.

## Never depend on existing data

```python
def test_task_list(task_client):
    tasks = task_client.get_list().json()["tasks"]
    assert tasks[0]["title"] == "My old task"     # ❌ someone deleted it
```

Create what you need, or assert on structure (`isinstance(tasks, list)`), not specific contents.

---

# 6. Combining API + UI 🔴

**The most valuable pattern in this track**, and a strong interview answer.

## The problem

A UI test that sets up state through the UI is slow and fragile:

```python
def test_task_appears_in_list(page):
    login(page)                          # 8 s
    page.goto("/app")                    # 2 s
    create_task_via_ui(page, "hello")    # 5 s
    wait_for_completion_in_ui(page)      # 90 s  ← watching the DOM
    expect(page.get_by_text("hello")).to_be_visible()   # the actual test
```

**105 seconds**, and five places to break — only the last line is what you're testing.

## The fix

**Set up state via API. Test only the thing you care about via UI.**

```python
def test_task_appears_in_list(page, task_client):
    task_id = assert_success(task_client.create({"text": "hello"}))["taskId"]   # 0.3 s
    wait_for_task(task_client, task_id)                                        # polls API

    page.goto(f"{BASE_URL}/app")                                               # 2 s
    expect(page.get_by_text("hello")).to_be_visible()                          # the actual test
```

Faster, and it only fails for the reason you care about.

## Three ways to combine them

**1. API sets up, UI verifies** (most common)

```python
task_id = task_client.create(...)["taskId"]     # arrange via API
page.goto("/app")
expect(page.get_by_text("...")).to_be_visible() # assert via UI
```

**2. UI acts, API verifies** — proves the UI really did something

```python
app.task_creation_input().fill("hello")
app.task_creation_submit_button().click()

tasks = task_client.get_list().json()["tasks"]
assert any(t["title"] == "hello" for t in tasks)     # the backend really got it
```

**3. UI acts, API waits, UI verifies** — best for Airtap's async tasks

```python
with page.expect_response(lambda r: "taskCreate" in r.url) as info:
    app.task_creation_submit_button().click()

task_id = info.value.json()["taskId"]
wait_for_task(task_client, task_id)                  # API polling — reliable

expect(page.get_by_text("Completed")).to_be_visible(timeout=30_000)
```

**Why pattern 3 matters here:** waiting by watching the DOM for 90 seconds is flaky. The API tells
you definitively when the task is done. Then you check the UI reflects it.

## The interview line

> *"I use API calls for setup and waiting, and the UI only for what the user actually sees. It cut
> our task-creation test from ~100 seconds to about 5, and removed four failure points that had
> nothing to do with what the test was checking."*

## ⚠️ Airtap today

There's no API client, so this is impossible right now. **This is the strongest argument for
building Part A before extending Part B.**

---

# 7. Logging 🟠

## What to log

| Log | Don't log |
|---|---|
| Environment and user at start | Every assertion that passed |
| Generated IDs (task, routine) | What pytest already reports |
| Retries and waits | Tokens, passwords, PII |
| Timing of slow operations | |

## Simple setup

```python
# conftest.py
import logging

def pytest_configure(config):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    logging.info("Environment: %s (%s)", ENV, BASE_URL)
```

## ⚠️ Never log secrets

```python
logger.info("Using token %s", PAT)                    # ❌ token in a log file
logger.info("Using token %s...", PAT[:12])            # ✅ prefix only
```

The `at-pat-` prefix plus two characters is enough to identify which token, without exposing it.

## Airtap review

**✅ Genuinely well done.** Real code from `conftest.py`:

```python
def pytest_configure(config):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ...
    logger.addHandler(logging.FileHandler(LOG_DIR / f"test_run_{timestamp}.log"))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item):
    logger.info("START %s", item.nodeid)
    yield
```

- Timestamped file per run — history preserved
- Both console and file
- START/END markers around every test via hooks
- UTC timestamps
- `logs/` in `.gitignore`

**⚠️ The one issue** — the per-assertion `logger.info("Passed: ...")` noise covered in #4.

**⚠️ Missing:** the environment is never logged, because there's no concept of one. Once you add
#3, log it at startup — the first question about any failed CI run is "which environment?"

---

# 8. Reporting 🟠

## Why

CI has no screen. A report is how a human sees what happened.

## `pytest-html` — the simple one

```bash
pip install pytest-html
pytest --html=report.html --self-contained-html
```

`--self-contained-html` inlines the CSS so the file works when emailed or downloaded from CI.

Airtap already produces `report.html`. ✅

## Allure — the richer one

Frequently named in job descriptions, so worth real setup practice.

```bash
pip install allure-pytest
pytest --alluredir=allure-results
allure serve allure-results
```

What it adds:

```python
import allure

@allure.feature("Task Management")
@allure.story("Task creation")
@allure.severity(allure.severity_level.CRITICAL)
def test_task_creation(task_client):
    with allure.step("Create task"):
        task_id = task_client.create({"text": "hello"}).json()["taskId"]

    with allure.step("Wait for completion"):
        details = wait_for_task(task_client, task_id)

    allure.attach(json.dumps(details, indent=2), "Task details",
                  allure.attachment_type.JSON)
```

Gives you: step-by-step breakdown, attachments (screenshots, JSON, logs), trend history across
runs, and grouping by feature.

## Attach on failure

```python
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        page = item.funcargs.get("page")
        if page:
            allure.attach(page.screenshot(), "screenshot",
                          allure.attachment_type.PNG)
```

Every UI failure now carries a screenshot. **Do this early** — it saves enormous time on CI
failures.

## Airtap review

**✅** `pytest-html` in use; `report.html` gitignored.
**❌** No screenshot-on-failure, no trace capture, no Allure. For a suite that runs headed on a
local machine that's survivable — the moment it runs in CI, it isn't.

---

# 9. Parallel execution 🟠

## The tool

```bash
pip install pytest-xdist
pytest -n 4          # 4 workers
pytest -n auto       # one per CPU core
```

## What must be true

Tests must be **independent**. In parallel there is no order.

| Requirement | Meaning |
|---|---|
| No shared mutable state | No module-level variables between tests |
| No order dependency | Every test runs alone |
| Unique test data | Two workers can't both create "Test Routine" |
| Isolated sessions | Fresh browser context per test |

## The three killers

**1. Shared state**

```python
task_id = None                    # ❌ module level

def test_create():
    global task_id
    task_id = create()["taskId"]

def test_read():                  # different worker — task_id is None
    get_details(task_id)
```

**2. Order dependency**

```python
def test_app_page(page):
    page.wait_for_url("/app")     # ❌ assumes an earlier test navigated
```

**3. Data collision** — fixed by unique names (#5).

## ⚠️ Airtap: parallel is impossible today

Three separate blockers:

| Blocker | Why |
|---|---|
| **Persistent Chrome profile** | `SingletonLock` — one process at a time. The code even skips tests when it's locked. |
| **Shared session-scoped context** | All tests share one browser session |
| **Order dependency** | `test_app_page_launched` needs `test_home_to_app_navigation` to have run |

The proof is in the code:

```python
def test_app_page_launched(page):
    page.wait_for_url("https://airtap.ai/app")     # only true because test 2 navigated
```

Run that test alone and it fails.

**The fix chain:** `storageState` (Track 4 #8) → fresh context per test → each test does its own
`page.goto()`. Parallel then works.

---

# 10. Flaky test root-causing 🔴

**The senior/junior dividing line.**

## What flaky means

Passes sometimes, fails sometimes, **no code change**.

## Why it's worse than a failing test

A failing test gets fixed. A flaky test gets **ignored** — and once people ignore red builds, the
suite stops protecting anything.

## The junior response

```bash
pytest --reruns 3
```

The test now "passes". The problem is still there — you've just made it invisible.

## The senior response

**Find out why first.** Categories:

| Cause | Signal | Fix |
|---|---|---|
| Fixed `sleep()` | Fails on slow runs | `expect()` with timeout |
| Race condition | Fails under load/parallel | Wait for a condition |
| Order dependency | Fails alone, passes in suite | Self-sufficient setup |
| Shared data | Fails in a certain order | Fresh data per test |
| Real backend slowness | Random timeouts | Longer timeout, or mock |
| Genuine product bug | **Intermittent in production too** | **File the bug** |

That last row matters. **Sometimes a flaky test is finding a real intermittent bug.** Retrying it
hides a production defect.

## How to investigate

```bash
pytest --count=20 tests/test_x.py     # pytest-repeat: how often?
pytest -n 4                            # does parallel expose it?
pytest tests/test_x.py                 # does it fail alone?
```

Then read the trace (Track 4 #6) from a failing run.

## When retry is acceptable

- A genuinely unreliable third-party dependency
- A **temporary** measure with a ticket to fix it
- Never as the default answer

```ini
# pytest.ini — if you must, be explicit
addopts = --reruns 1 --reruns-delay 2
```

## The interview answer

> *"I find out why before I retry. Retrying without root-causing trades a visible problem for an
> invisible one — and sometimes the flakiness is a real intermittent bug that retrying hides."*

## ⚠️ Airtap's known flakiness sources

| Source | Status |
|---|---|
| `time.sleep(5)` | Present — fix with `expect()` |
| Order dependency | Present — `test_app_page_launched` |
| Shared browser context | Present — session-scoped |
| Non-deterministic AI | Inherent — assert state, not text |
| Production environment | Present — real traffic, real variability |

Four of the five are fixable. The fifth (AI non-determinism) is handled by asserting on **state**,
not wording.

---

# Part A — Building the API framework from zero

No API suite exists. Here's the build, in order.

## Step 0 — Prerequisites

- [ ] Test account on **qa1 or qa2**, confirmed `ADMITTED` (not waitlisted)
- [ ] A **Personal Access Token** for it (`at-pat-...`)
- [ ] Read [airtap_api_contract.md](airtap_api_contract.md)

## Step 1 — Skeleton

```bash
mkdir -p api-automation/{config,api_clients,helpers,schemas,data,tests/api}
cd api-automation
python -m venv .venv && source .venv/bin/activate
pip install pytest requests jsonschema
pip freeze > requirements.txt
```

```ini
# pytest.ini
[pytest]
testpaths = tests
pythonpath = .
addopts = -ra -v
markers =
    smoke: fast critical checks
    slow: takes over 30 seconds
    negative: error-path tests
```

```gitignore
.venv/
__pycache__/
.pytest_cache/
report.html
.env
```

## Step 2 — Config (#3)

```python
# config/settings.py
import os

ENVIRONMENTS = {"qa1": "https://qa1.airtap.ai", "qa2": "https://qa2.airtap.ai"}
ENV = os.getenv("AIRTAP_ENV", "qa1")
BASE_URL = ENVIRONMENTS[ENV]
PAT = os.environ["AIRTAP_PAT"]
TASK_POLL_TIMEOUT_S = int(os.getenv("TASK_POLL_TIMEOUT_S", "180"))
```

## Step 3 — First unauthenticated test

Prove the plumbing before adding auth.

```python
# tests/api/test_health.py
import requests, pytest
from config.settings import BASE_URL

@pytest.mark.smoke
def test_health_check():
    resp = requests.get(f"{BASE_URL}/cortex/api/check/v1/checkHealth", timeout=30)
    assert resp.status_code == 200
```

## Step 4 — Base client (Track 3 #6)

```python
# api_clients/base_client.py
import requests
from config.settings import BASE_URL, PAT

class BaseClient:
    def __init__(self, base_url=BASE_URL, token=PAT, timeout=30):
        self.base_url, self.timeout = base_url, timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })

    def post(self, endpoint, payload=None):
        return self.session.post(f"{self.base_url}{endpoint}",
                                 json=payload or {}, timeout=self.timeout)

    def get(self, endpoint):
        return self.session.get(f"{self.base_url}{endpoint}", timeout=self.timeout)

    def close(self):
        self.session.close()
```

## Step 5 — Assertion helper

```python
# helpers/assertions.py
def assert_success(resp):
    """Check BOTH the HTTP code and Airtap's own status field."""
    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    assert body["status"] == "Success", \
        f"status={body['status']} message={body.get('message')}"
    return body
```

**Use this everywhere.** It's the guard against the "HTTP 200 but `status: Failure`" trap.

## Step 6 — Task client

```python
# api_clients/task_client.py
from api_clients.base_client import BaseClient

class TaskClient(BaseClient):
    def create(self, user_message, receiver_id="cloud", **extra):
        return self.post("/cortex/api/task/v1/taskCreate", {
            "userMessage": user_message, "receiverId": receiver_id, **extra})

    def get_details(self, task_id, debug=False):
        return self.post("/cortex/api/task/v1/taskGetDetails",
                         {"taskId": task_id, "debug": debug})

    def get_list(self):
        return self.post("/cortex/api/task/v1/taskGetList", {})

    def cancel(self, task_id):
        return self.post("/cortex/api/task/v1/taskCancel", {"taskId": task_id})
```

## Step 7 — Fixtures

```python
# tests/api/conftest.py
import pytest
from api_clients.task_client import TaskClient

@pytest.fixture(scope="session")
def task_client():
    client = TaskClient()
    yield client
    client.close()
```

## Step 8 — Auth tests (positive + negative)

```python
@pytest.mark.smoke
def test_authenticated_list_works(task_client):
    assert_success(task_client.get_list())

@pytest.mark.negative
def test_no_token_rejected():
    resp = requests.post(f"{BASE_URL}/cortex/api/task/v1/taskGetList",
                         json={}, timeout=30)
    assert resp.status_code == 401
```

## Step 9 — The polling helper (the key piece)

```python
# helpers/polling.py
import time
from helpers.assertions import assert_success

TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED", "STOPPED"}

class TaskTimeoutError(Exception):
    pass

def wait_for_task(client, task_id, timeout=180, interval=3):
    deadline = time.time() + timeout
    state = "UNKNOWN"
    while time.time() < deadline:
        details = assert_success(client.get_details(task_id))
        state = details["taskState"]
        if state in TERMINAL_STATES:
            return details
        time.sleep(interval)
    raise TaskTimeoutError(f"Task {task_id} still '{state}' after {timeout}s")
```

**Build this once — Part B reuses it.**

## Step 10 — First real task test

```python
def test_task_reaches_terminal_state(task_client):
    task_id = assert_success(task_client.create(
        {"text": "what is 2 plus 2?"}, cancelAfterSteps=5))["taskId"]

    details = wait_for_task(task_client, task_id)
    assert details["taskState"] in ("COMPLETED", "STOPPED")
```

Note `cancelAfterSteps=5` — cost control (#5).

## Step 11 — Schema validation, negative cases, RRULE suite

```python
# schemas/task_schemas.py
TASK_DETAILS_SCHEMA = {
    "type": "object",
    "required": ["status", "taskState"],
    "properties": {
        "taskState": {"type": "string", "enum": [
            "QUEUED", "WAITING_FOR_EXECUTION",
            "WAITING_FOR_USER_INPUT", "WAITING_FOR_USER_INTERVENTION",
            "COMPLETED", "FAILED", "CANCELLED", "STOPPED"]},
    },
}
```

Then convert `pilot/manual-custom-routine-rrule-ai-test-cases.md` (129 rows) into
`data/rrule_cases.json` and one parametrized test.

## Step 12 — README

```markdown
# Airtap API Automation

## Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

## Run
export AIRTAP_ENV=qa1
export AIRTAP_PAT=at-pat-xxx
pytest                    # everything
pytest -m smoke           # fast checks
```

**Ten minutes. Do not skip it.**

---

# Part B — Building the Playwright framework from zero

## Step 0 — Decide the auth approach first

This decision shapes everything else.

| Approach | CI? | Parallel? | Tests login? |
|---|---|---|---|
| Persistent Chrome profile *(Airtap today)* | ❌ | ❌ | ❌ |
| **`storageState`** | ✅ | ✅ | ✅ (separately) |

**Choose `storageState`.** It's the difference between a local-only suite and a real one.

## Step 1 — Skeleton

```bash
mkdir -p ui-automation/{config,pages,helpers,tests/ui}
pip install pytest pytest-playwright
playwright install chromium
pip freeze > requirements.txt
```

```gitignore
.venv/
auth.json          ← ⚠️ contains a live session
test-results/
```

## Step 2 — Config, including headless

```python
# config/settings.py
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
DEFAULT_TIMEOUT_MS = int(os.getenv("DEFAULT_TIMEOUT_MS", "15000"))
```

Local runs stay visible; CI sets `HEADLESS=true`.

## Step 3 — Generate the auth state (once)

```python
# scripts/save_auth.py
from playwright.sync_api import sync_playwright
from config.settings import BASE_URL

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(f"{BASE_URL}/app")
    input("Log in, then press Enter...")
    page.context.storage_state(path="auth.json")
    browser.close()
```

## Step 4 — Fixtures with fresh context per test

```python
# tests/ui/conftest.py
@pytest.fixture(scope="session")
def browser(playwright_session):
    browser = playwright_session.chromium.launch(headless=HEADLESS)
    yield browser
    browser.close()

@pytest.fixture
def page(browser):
    context = browser.new_context(storage_state="auth.json")     # logged in
    page = context.new_page()
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)
    yield page
    context.close()                                               # isolated
```

**Session-scoped browser** (expensive) + **function-scoped context** (isolation). Both benefits.

## Step 5 — Page Objects

Copy Airtap's existing `pages/` — they're good (Track 4 #3). Follow the same conventions:
role-based locators, regex for varying text, comments on any CSS fallback.

## Step 6 — Self-sufficient tests

```python
@pytest.mark.smoke
def test_app_page_renders(page):
    page.goto(f"{BASE_URL}/app")           # ← own setup, no dependency
    app = PilotAppPage(page)
    expect(app.task_creation_input()).to_be_visible()
```

**Every test navigates itself.** Never rely on where a previous test left the browser.

## Step 7 — Debug artefacts from day one

```ini
# pytest.ini
addopts = -ra -v --tracing retain-on-failure --screenshot only-on-failure
```

## Step 8 — The combined test (the payoff)

```python
def test_task_creation_end_to_end(page, task_client):
    page.goto(f"{BASE_URL}/app")
    app = PilotAppPage(page)

    with page.expect_response(lambda r: "taskCreate" in r.url) as info:
        app.task_creation_input().fill("what is 2 plus 2?")
        app.task_creation_submit_button().click()

    task_id = info.value.json()["taskId"]      # UI acted
    wait_for_task(task_client, task_id)        # API waited — reliable
    expect(page.get_by_text("Completed")).to_be_visible(timeout=30_000)   # UI verified
```

**This is the goal.** Everything in Parts A and B leads here.

## Step 9 — README

---

# Part C — One repo, both suites

Keep them in one repo so they share config, helpers, and CI.

```
airtap-automation/
├── config/settings.py         ← shared
├── helpers/                   ← assert_success, wait_for_task — shared
├── api_clients/
├── pages/
└── tests/
    ├── conftest.py            ← shared fixtures
    ├── api/conftest.py
    └── ui/conftest.py
```

The **shared `helpers/`** is the point: `wait_for_task()` is written once and used by both.

```bash
pytest tests/api          # fast — every commit
pytest tests/ui           # slower — nightly or pre-release
pytest -m smoke           # both, fast subset
```

---

# The Airtap suite scorecard

| Area | Verdict | Notes |
|---|---|---|
| **Page Object Model** | ✅ Good | Proper package, clean separation |
| **Locator quality** | ✅ Very good | Role-based, regex for variants, CSS fallback documented |
| **Fixture design** | ✅ Good | Correct scoping, `yield` teardown, chained |
| **Logging infrastructure** | ✅ Good | Timestamped files, hooks, START/END |
| **Type hints & docstrings** | ✅ Good | Consistent throughout |
| **`.gitignore`** | ✅ Good | Profile, logs, venv all excluded |
| **Assertion messages** | ✅ Good | Descriptive on both `assert` and `expect` |
| **`pytest.ini`** | ⚠️ Basic | Works; no markers |
| **Reporting** | ⚠️ Basic | HTML only; no screenshots/traces |
| **Test coverage** | ⚠️ Thin | 3 tests, render-only, no task creation |
| **`requirements.txt`** | ❌ Missing | **Nobody can reproduce the environment** |
| **README** | ❌ Missing | New person can't run it |
| **Environment config** | ❌ Missing | Hardcoded to **production** |
| **API layer** | ❌ Missing | No API tests at all |
| **Test isolation** | ❌ Broken | Order-dependent |
| **CI readiness** | ❌ No | `headless: False`, profile lock |
| **Parallel-safe** | ❌ No | Three separate blockers |
| **Fixed sleeps** | ❌ Present | `time.sleep(5)` |

## Fix order

**Quick wins (under an hour, high value)**
1. `pip freeze > requirements.txt`
2. Write a README
3. Replace `time.sleep(5)` with `expect(...)`
4. Add markers to `pytest.ini`

**Structural (a day each)**
5. Environment config — stop testing production
6. `storageState` instead of the persistent profile
7. Make each test self-sufficient
8. Enable tracing and screenshot-on-failure

**The big one (Part A)**
9. Build the API framework — unlocks combining, speed, and real coverage

---

# Quick-fire differentiation table

| Question | Answer |
|---|---|
| Scripts vs framework | Could someone else add a test without asking you? |
| Test pyramid vs ice cream cone | Many fast/few slow, vs many slow/few fast |
| DRY vs over-abstraction | Remove noise, never meaning |
| Where should setup happen? | API when possible; UI only for what's being tested |
| Fixture vs helper function | Fixture for setup/teardown; helper for pure logic |
| `pytest-html` vs Allure | Simple single file vs steps, attachments, history |
| Retry vs root-cause | Retry hides; root-cause fixes |
| What makes a test parallel-safe? | No shared state, no order dependency, unique data |
| Session vs function fixture scope | Expensive connections vs anything mutable |
| Why not hardcode URLs? | One env switch, and you stop testing production |

---

# Practice checklist

**Assess**
- [ ] List everything `web-automation/` does well — you'll reuse it
- [ ] Run `test_app_page_launched` alone; explain the failure
- [ ] Confirm which environment the suite actually targets

**Quick wins**
- [ ] Add `requirements.txt`
- [ ] Write a README with setup + run commands
- [ ] Replace `time.sleep(5)` with a condition wait
- [ ] Add `smoke` / `slow` markers and run `pytest -m smoke`

**Structural**
- [ ] Add `config/settings.py` with an env switch, defaulting to qa1
- [ ] Make `headless` configurable
- [ ] Create `auth.json` via `storageState` and a fresh-context fixture
- [ ] Make every test do its own `page.goto()`
- [ ] Enable `--tracing retain-on-failure`

**Build (Part A)**
- [ ] Follow Steps 1–12 and get the health check passing
- [ ] Build `BaseClient` and `TaskClient`
- [ ] Write `assert_success()` and `wait_for_task()`
- [ ] Create a task with `cancelAfterSteps=3` and poll it

**The payoff**
- [ ] Write one test that uses API for setup and UI for verification
- [ ] Compare its runtime to the pure-UI equivalent
- [ ] Run `pytest -n 2` and fix whatever breaks
