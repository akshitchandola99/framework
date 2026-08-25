# Automation Testing Roadmap — Python, API & Web

*A sequenced study plan to go from "wrote some Playwright and API scripts with AI's help" to
"can independently design, build, and maintain a real automation framework." Companion document:
[02_airtap_automation_implementation_plan.md](02_airtap_automation_implementation_plan.md), which
applies every phase below directly to Airtap's real codebase.*

## Where you're starting from, and why this roadmap is shaped the way it is

You've already built small orchestration jobs, small API frameworks, and some Playwright — with
AI doing a lot of the heavy lifting. That's a real, useful starting point, not a blank slate — but
it also means there's a real risk of gaps: code that *works* without you being fully sure *why*.
This roadmap is built to close exactly that gap, in order:

1. **Solidify the Python mechanics that automation code leans on hardest** (classes, decorators,
   context managers) — these show up constantly in test frameworks and are easy to use via AI
   without understanding.
2. **Learn the shared foundation both API and web automation sit on** — pytest itself.
3. **Go deep on API testing first, web testing second** — this is deliberate, not arbitrary: API
   testing is the highest-value, most underinvested skill in QA (confirmed directly in current
   2026 industry research — most engineers over-focus on UI automation because it's visual, but
   API tests catch more bugs, run faster, and are far more stable). You already have a head start
   here too.
4. **Then test architecture and CI/CD** — how real frameworks are organized and run continuously,
   not just as one-off scripts.
5. **Then the part that's genuinely different from a normal QA job**: testing a system whose core
   logic is non-deterministic — which is exactly Airtap, and exactly what the rest of this
   conversation has already prepared you to understand conceptually. This roadmap is where that
   understanding turns into code.

**A note on using AI while learning this**: keep using it, but change *how*. Ask it to explain
*why* a piece of code works before you accept it, not just to produce working code. A good habit:
after AI writes something, close the file and try to explain each line out loud to yourself. If you
can't, that's the part to actually study — this roadmap tells you where to go for it.

---

## Phase 0 — Python Foundations for Automation

*Goal: close the specific gaps that make test framework code confusing, not a full "learn Python"
course. If you can already comfortably do all of these without AI, skim and move to Phase 1.*

| Topic | Why it matters for automation specifically |
|---|---|
| Functions, arguments, `*args`/`**kwargs` | Every test helper and page-object method uses these |
| Classes, `self`, inheritance, `__init__` | Page Objects and API client wrappers are just classes |
| **Decorators** (`@something`) | Pytest fixtures, markers, and parametrize all *are* decorators — if these feel like magic, most of pytest will too |
| Context managers (`with ... as ...`) | Browser sessions, API sessions, and test setup/teardown all use this pattern |
| List/dict comprehensions | Constantly used for extracting/transforming test data and API responses |
| Type hints (`def f(x: int) -> bool`) | Modern frameworks lean on these heavily for readability and catching mistakes early |
| `async`/`await` basics | Needed later for `httpx` async clients and some Playwright patterns |
| Virtual environments & `pip` | Every project needs isolated, reproducible dependencies |
| Reading a traceback calmly | The single most important debugging skill — most people panic-read tracebacks instead of reading them bottom-up |

**How to actually close these gaps**: don't read a textbook — write 10 tiny scripts, one per
topic, from scratch, no AI. If a decorator genuinely confuses you, write a *from-scratch* decorator
that prints "before" and "after" around a function call. That one exercise demystifies 80% of what
pytest does internally.

---

## Phase 1 — Testing Fundamentals & Pytest

*Goal: the shared foundation everything else (API and web) is built on top of.*

1. **Testing theory, briefly** (you likely already know most of this from manual QA):
   test pyramid (unit → integration → end-to-end), why fewer/faster tests at the bottom and fewer/
   slower tests at the top, flaky vs. reliable tests, what "good test isolation" means.
2. **Pytest core**:
   - Writing a test function, `assert` statements, running via `pytest`
   - **Fixtures** — setup/teardown, fixture scope (`function`/`class`/`module`/`session`),
     `conftest.py` and why it exists
   - `@pytest.mark.parametrize` — running one test against many inputs
   - Markers (`@pytest.mark.slow`, custom markers, `-m` filtering)
   - `pytest.ini` / `pyproject.toml` configuration
   - Assertion introspection (why pytest's plain `assert` gives good failure messages without extra
     libraries)
3. **The pytest plugin ecosystem** (know these exist and roughly what each does; you'll install
   them as needed later): `pytest-xdist` (parallel runs), `pytest-html` (HTML reports — you
   already have this producing `report.html`), `pytest-asyncio` (async tests), `pytest-rerunfailures`
   (automatic retries), `pytest-cov` (coverage).

**Milestone check**: you should be able to explain, without looking anything up, what a fixture's
`scope` does and why you'd choose `session` over `function` for something like a browser instance.

---

## Phase 2 — API Test Automation

*Goal: this is where you build your strongest, most employable skill. Go deeper here than feels
necessary — this is explicitly the most underinvested skill in the field right now.*

1. **HTTP fundamentals, properly this time**: methods (GET/POST/PUT/DELETE/PATCH) and when each is
   actually appropriate, status code families (2xx/3xx/4xx/5xx) and what each family *means* (not
   just memorized numbers), headers (especially `Content-Type`, `Authorization`), query params vs.
   path params vs. body.
2. **The `requests` library**: making calls, reading `.status_code`/`.json()`/`.headers`, sessions
   (`requests.Session()` for connection reuse and shared auth/cookies across calls).
3. **Writing your first real API tests**: pytest + `requests`, asserting on status code AND body
   shape, not just "did it return 200."
4. **Schema validation**: why "the response is JSON" isn't the same as "the response has the right
   shape" — using `jsonschema` (or `pydantic` models) to assert a response actually matches a
   contract, not just that it parses.
5. **Structuring an API test framework properly** (this is where AI-assisted code most often goes
   wrong — it produces working scripts, not a framework):
   - A base API client class wrapping `requests.Session` (auth handling, base URL, common headers
     in one place)
   - Environment configuration (base URLs, credentials) kept *out* of test code — env vars or a
     config file per environment
   - Test data builders/factories instead of hardcoded dictionaries scattered through tests
6. **Negative and edge-case testing**: wrong auth, missing required fields, malformed JSON, boundary
   values, rate-limit behavior — API testing's real value is here, not just the happy path.
7. **Mocking**: `unittest.mock` and the `responses` library, for testing your own code's handling of
   an API's response *without* depending on a real, slow, or flaky external service.
8. **Async APIs with `httpx`**: when and why you'd reach for `httpx.AsyncClient` + `pytest-asyncio`
   instead of plain `requests` — mainly when testing high-throughput or genuinely async backends.

**Milestone check**: build a small API test suite (against any public test API, like
`https://reqres.in` or similar) with a proper client class, environment config, positive and
negative cases, and schema validation — from scratch, explaining each part.

---

## Phase 3 — Web UI Automation (Playwright)

*Goal: deepen what you already have "a little bit" of into something you actually understand
end-to-end. Current (2026) best practice, confirmed via research: prefer role-based, accessibility-
style locators, and lean on composable fixtures over heavy Page Object Model for small/medium
suites — both are covered below since Airtap's existing suite already uses Page Object Model and
you'll be extending it.*

1. **Playwright fundamentals**: browser, context, and page — what each level actually represents
   (a context is an isolated "incognito" session; you can run many contexts off one browser
   instance).
2. **Locators, done the modern way**: prefer `get_by_role`, then `get_by_label`/`get_by_text`, then
   `get_by_test_id` — falling back to raw CSS/XPath only when nothing else works. `get_by_role`
   doubles as a lightweight accessibility check, which is a nice bonus.
3. **Auto-waiting**: understand *why* Playwright mostly doesn't need explicit `sleep()` calls
   (actions auto-wait for the element to be actionable) — and the handful of cases where you still
   need an explicit wait (waiting for a network response, waiting for a specific state that isn't
   tied to one element).
4. **Writing your first Playwright + pytest tests**: using the `pytest-playwright` plugin, the
   built-in `page` fixture, basic actions (`click`, `fill`, `expect`).
5. **Codegen**: use `playwright codegen` to record a flow and generate starter code — a legitimate,
   fast way to bootstrap a test, *as long as you then clean up and understand the generated code*
   rather than shipping it as-is.
6. **Page Object Model vs. fixtures — learn both, know when to reach for which**:
   - POM: one class per page/component, methods for actions on that page. Good for larger,
     long-lived suites (this is what Airtap's existing suite already uses).
   - Fixtures-first: build small, composable fixtures around *business actions*
     ("logged_in_page," "page_with_task_created") rather than raw Playwright calls. Less
     boilerplate for smaller suites.
7. **Authentication state**: use `storageState` to log in once and reuse that session across many
   tests, instead of repeating a full login flow in every single test.
8. **Debugging tools**: trace viewer (`--trace on`), screenshots and video on failure, the Playwright
   Inspector for step-through debugging.
9. **Handling real-world flakiness sources**: waiting for a specific network response
   (`page.wait_for_response`), waiting for network idle vs. a specific element, retrying flaky
   assertions with Playwright's built-in `expect` polling instead of manual retry loops.

**Milestone check**: extend a page object with a new method *without* AI, using only Playwright's
own docs, and explain why you chose the locator strategy you used.

---

## Phase 4 — Test Architecture & Design Patterns

*Goal: the difference between "a folder of scripts" and "a framework someone else could maintain."*

1. **Project structure**: separating `tests/`, `pages/` or `fixtures/`, `api_clients/`, `config/`,
   `utils/` — and why this separation matters as a suite grows.
2. **Environment/config management**: loading different base URLs/credentials per environment
   (local/dev/qa/prod-style setups) cleanly, via env vars or per-environment config files — never
   hardcoded in test files.
3. **Test data strategy**: creating data via API calls for speed (instead of clicking through the
   UI just to set up state), and cleaning up after tests so they don't pollute shared environments.
4. **Combining API and UI in one suite** — a very real, very common pattern: use fast API calls to
   set up preconditions, then use the UI only to test the actual thing you care about. This alone
   can cut a slow UI suite's runtime dramatically.
5. **Parallelization**: `pytest-xdist` for running tests concurrently, and what has to be true about
   your tests (independence, no shared mutable state) for parallel runs to actually be safe.
6. **Flaky test handling, done properly** — not just "add a retry and hope": understanding *why* a
   test is flaky (timing, shared state, real non-determinism) before reaching for
   `pytest-rerunfailures` as a band-aid.
7. **Reporting**: `pytest-html` (already in use), and Allure as a richer alternative worth knowing
   about (step-by-step reports, attachments, history trends).

---

## Phase 5 — CI/CD Integration

*Goal: tests that run automatically, not just on your own machine.*

1. **Why CI matters for test suites specifically**: catching regressions before they reach real
   users, not relying on someone remembering to run tests manually (this is a theme you'll recognize
   — it's the same "Eval Ops" gap we identified in Airtap's own AI-evaluation framework, just for
   traditional automated tests instead).
2. **GitHub Actions basics** (a natural fit given this is a git-based project): workflow YAML
   structure, running pytest on a schedule or on every pull request, caching dependencies for
   faster runs.
3. **Managing secrets/credentials in CI** safely — never hardcoded, never logged.
4. **Publishing test results**: uploading HTML/Allure reports as CI artifacts, failing the build on
   test failure, optionally posting a summary/notification (e.g., to Slack) on failure.
5. **Running browser tests in CI specifically**: headless mode, installing Playwright's browser
   binaries in the CI environment, video/trace capture on failure for later debugging (since you
   can't watch it live the way you can locally).

---

## Phase 6 — Testing Non-Deterministic AI Systems

*Goal: this is the part of your skill set that will genuinely differentiate you — and it's the
direct, hands-on version of everything already covered conceptually earlier in this whole
conversation. Confirmed via current research: the industry has converged on almost exactly the
same three-part framing Airtap's own eval system already uses.*

1. **Why `assert result == expected` breaks down for AI-driven behavior** — you already know this
   conceptually; this phase is about writing tests that account for it in actual code.
2. **The three eval categories, and how to automate each in pytest**:
   - **Deterministic checks** — exact match, regex, JSON-schema validation. These *do* work as
     normal pytest assertions — use them wherever the output genuinely has one correct shape (a tool
     call's argument schema, for instance).
   - **Rubric-based / LLM-as-judge** — write a pytest fixture that calls a second LLM to grade the
     first's output against explicit yes/no questions, and assert on the judge's verdict. Know its
     limits (the biases we've already covered — verbosity, position, drift) and don't treat the
     judge as infallible in your own test assertions either.
   - **Composite/multi-metric scoring** — combining several checks (some deterministic, some
     judged) into one pass/fail, rather than relying on a single signal.
3. **Testing for a distribution, not a single value**: writing a test that runs the same scenario N
   times and asserts on a *success rate* threshold, not a single pass/fail — and deciding what N and
   what threshold are actually meaningful for a given test.
4. **State verification over screenshot comparison**: asserting against real, structured system
   state (an API response, a database record, a task's actual status) instead of comparing images —
   directly the same principle behind why AndroidWorld-style benchmarks are considered reproducible,
   which came up earlier in this conversation.
5. **Handling asynchronous, job-driven completion** (this is very specifically an Airtap pattern):
   writing clean polling helpers — "keep checking this task's status every N seconds, up to a
   timeout, until it reaches a terminal state" — instead of a fixed `sleep()`, which is both slower
   than necessary and still not actually reliable.
6. **Guardrail and adversarial testing as real, automatable test cases**: prompt-injection-style
   test inputs, confirming a specific bad outcome never happens (an internal-detail leak, an
   irreversible action without confirmation) — these are genuinely automatable, not just manual
   exploratory work.

---

## Suggested pacing

> **Superseded.** [00_master_study_plan.md](00_master_study_plan.md) carries the authoritative
> 12-week schedule, which covers SQL, CI/CD, and interview prep that this 9-week table doesn't.
> The table below is kept only as a compressed view of the six learning phases above.

Same priority-tagged format as your AI Roadmap, so it should feel familiar:
🔴 core, don't skip · 🟡 standard, worth real time · 🟢 good to have, compress first if short on time

| Week | Focus |
|---|---|
| 1 | 🟡 Phase 0 — close Python gaps (decorators, classes, context managers, async basics) |
| 2 | 🔴 Phase 1 — pytest fundamentals: fixtures, parametrize, markers, conftest |
| 3–4 | 🔴 Phase 2 — API testing: `requests`, schema validation, framework structure, negative cases |
| 5–6 | 🔴 Phase 3 — Playwright: locators, fixtures/POM, auth state, debugging tools |
| 7 | 🟡 Phase 4 — test architecture: config management, combining API+UI, parallelization |
| 8 | 🟡 Phase 5 — CI/CD: GitHub Actions, reporting, secrets |
| 9 | 🔴 Phase 6 — non-deterministic AI testing patterns (do this directly against Airtap, not a toy example — see the companion document) |

If you're short on time: **don't compress Phase 2 or Phase 6.** Phase 2 (API testing) is your
fastest path to being genuinely useful and employable; Phase 6 is what actually makes this
Airtap-relevant rather than generic QA skill-building. Phases 4–5 can be learned more lightly at
first and deepened later, since they're about *scaling* a suite you don't have much of yet.

---

## A short list of things worth bookmarking, not memorizing

- Playwright Python docs (official — the most reliable source, more so than blog tutorials, which
  drift out of date fast)
- Pytest's own documentation on fixtures — it's genuinely well-written and worth reading directly
  rather than only through secondary tutorials
- `jsonschema` and `pydantic` docs, for whichever schema-validation approach you settle on
- The `requests` and `httpx` quickstarts

---
**Next:** [02_airtap_automation_implementation_plan.md](02_airtap_automation_implementation_plan.md) — applying every phase above directly to Airtap's real API and web app, starting from the existing `web-automation/` project.
