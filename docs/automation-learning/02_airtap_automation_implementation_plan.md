# Airtap Automation Implementation Plan

*The hands-on companion to [01_automation_testing_roadmap.md](01_automation_testing_roadmap.md).
Where that document teaches the skill, this one tells you exactly what to build, in what order,
against the real Airtap codebase — grounded in what actually exists today (confirmed directly
against the repository, not assumed).*

## Starting inventory — what already exists

| | Status |
|---|---|
| **Web automation** | A real starting point: `web-automation/` — Playwright + pytest, Page Object Model (`pages/pilot_website_page.py`, `pages/pilot_app_page.py`), currently **3 tests** covering marketing-site load and Pilot app shell rendering only. Runs against **production only**, using a **persistent, already-logged-in Chrome profile** (no automated login flow exists yet). No end-to-end task execution is tested. |
| **API automation** | **Does not exist yet.** This is a greenfield build. |

Both of these gaps — API automation from scratch, and web automation's lack of real task-execution
coverage — are exactly where you can add the most value early, and they're both called out
explicitly in this repo's own QA documentation as the honest state of automated coverage today.

## Before writing any code: three prerequisites

1. **A dedicated QA-environment test account.** Don't automate against your own personal account or
   production. You'll need an account that's admitted (not `WAITLISTED`) in whichever QA
   environment you target (`qa1` or `qa2`), ideally on an allow-listed email domain so it doesn't
   need manual admission every time you recreate it.
2. **A Personal Access Token (PAT) for that account.** This is confirmed as the intended credential
   for exactly this use case — automation and CI — as opposed to a normal browser session login.
   Get one issued for your test account before writing your first API test.
3. **Decide which receiver type your automated tests will target, and default to "cloud phone."**
   This matters more than it sounds like: task creation triggers a *real* agent run — real LLM
   calls (real cost against your test account's credit) and, if targeted at a real paired device,
   real physical actions. For automated, repeatable, CI-safe tests, target a **cloud phone**
   receiver, not a physical device — it's disposable, always available, and doesn't risk a
   real-world side effect on hardware sitting on someone's desk. Reserve physical-device automation
   for later, deliberate, supervised runs.

---

## Part A — API Automation, in sequence

### Milestone 1: Project skeleton + unauthenticated smoke checks

- New project, e.g. `api-automation/`, parallel to `web-automation/`. `pytest.ini`, a `requirements.txt`
  (`requests`, `pytest`, `jsonschema` or `pydantic` to start), and an environment config module that
  reads a base URL and PAT from env vars — never hardcoded, and switchable between `qa1`/`qa2`.
- Build the base API client: a thin class wrapping `requests.Session`, injecting the `Authorization`
  header from your PAT, prefixing every call with the environment's base URL and the
  `/cortex/api/<module>/v1/<action>` route shape.
- First tests, deliberately trivial and low-risk: the health-check endpoint (confirms the
  environment is actually up before anything else runs — a good thing to run first in every suite),
  and the APK-URL endpoint (both are unauthenticated, so they also validate your client setup
  before you add auth into the mix).

### Milestone 2: Authenticated read-only endpoints

- Task list, receiver list, your own memory contents. Confirm your PAT auth actually works, and
  practice schema validation here — assert the response shape, not just the status code.
- This is also the right place to write your first **negative** auth tests: a request with no auth
  header, a request with an invalid/garbage token, a request with a token belonging to a
  `WAITLISTED` account (create a second, deliberately-unadmitted test account for this) — and assert
  the *specific* rejection reason each one returns, not just "it failed."

### Milestone 3: Convert an existing manual test suite into automation (high value, low novelty risk)

This repo already has a detailed manual test document —
`pilot/manual-custom-routine-rrule-ai-test-cases.md` — enumerating roughly 65 valid and 65
deliberately-invalid natural-language schedule descriptions for the routine-scheduling feature. This
is close to a perfect first "real" automation project:
- The endpoint (`rtnGenerateRRule`-style route) takes a free-text schedule description and returns
  either a valid recurrence rule or an explicit rejection.
- The test *data* already exists, written by a human who thought carefully about edge cases — you
  just need to load it and turn it into a `@pytest.mark.parametrize` suite instead of a manual
  checklist.
- This directly demonstrates a core professional skill: recognizing when existing QA knowledge can
  be converted into automation instead of building new test cases from nothing.

### Milestone 4: Task creation + async completion — the real core skill

This is the one that matters most, and the one that's genuinely different from typical API testing:

1. Call task-create with a simple, deterministic-ish request (something like "what's 2+2" or a
   request that maps to the eval dataset's cheap `report_plan`-only style cases — avoid anything
   requiring real app interaction for your first version).
2. **Do not sleep-and-hope.** Build a real polling helper: check the task's status on an interval,
   up to a timeout, until it reaches a terminal state (completed/failed/cancelled) — this is
   directly Phase 6 of the roadmap document, made concrete.
3. Assert on the *state*, not exact text: did it reach `COMPLETED`, not "does the response contain
   these exact words." Save exact-content assertions for the narrow cases where the roadmap's
   "deterministic checks" category genuinely applies (e.g., a specific tool was called, per the
   task's step data — not the AI's free-text final answer).
4. Once this works, layer in the harder version: a task that actually needs a receiver (target your
   cloud phone), and assert against real reported state (task step count, terminal state, whether a
   specific tool appears in the step history) — not a screenshot comparison.

### Milestone 5: Negative and edge cases for task creation specifically

- Malformed request bodies, missing required fields
- Creating a second task while one is already active for the same account (should queue, not
  reject — confirm this specific, documented behavior)
- Cancelling a task at different points in its lifecycle
- Resuming a task that's waiting on user input vs. one that's already finished

---

## Part B — Web Automation, in sequence

### Milestone 1: Understand and stabilize what exists

Before adding anything, get the existing 3 tests running locally and understand *why* they're built
the way they are — particularly the persistent Chrome profile in `browser_config.py`. That's a real
constraint worth understanding, not just accepting: it means the suite depends on a Chrome profile
that's already authenticated, which is fast and simple but doesn't work in a clean CI environment
and can't easily test *login itself*.

### Milestone 2: Make the environment configurable

Currently the suite only targets production. Before building much more on top of it, add an
environment switch (env var or CLI flag) so it can target `qa1`/`qa2` too — you want your growing
web suite testing against the same QA environment your API suite and your test account live in, not
production, once you're doing anything beyond a pure read-only smoke check.

### Milestone 3: A real login flow, at least for one auth method

Phone-OTP login is the more automatable of Pilot's auth methods (Google Sign-In is a third-party
OAuth flow that actively resists automation — most teams don't fully automate it and instead rely on
a pre-authenticated session for that path, which is exactly what the existing persistent-profile
approach already does for you). Once you have a working login flow, use Playwright's `storageState`
to save that authenticated session and reuse it across tests, instead of logging in fresh every
time — directly Phase 3 of the roadmap document.

### Milestone 4: Real task creation through the UI, end to end

This is the gap explicitly called out in this repo's own QA documentation as missing today — the
existing suite never submits a task. Build it:
1. Use the composer to submit a simple task.
2. Wait for the thread to show progress — but don't just wait for *any* DOM change; use your
   Milestone 4 API polling helper from Part A *underneath* the UI test to know definitively when the
   task has reached a terminal state, then assert the UI reflects that correctly. This is the
   "combine API and UI" pattern from Phase 4 of the roadmap, made concrete: API for fast, reliable
   waiting; UI for testing what a human actually sees.
3. Assert the final thread state shows a completed task with a response — again, checking for
   presence/state, not exact AI-generated wording.

### Milestone 5: Routines, created through the UI

A good mid-complexity target once task creation works — create a routine via the composer's flow,
confirm it appears in the routines list, confirm its schedule matches what was entered. Pair this
with the RRULE dataset from Part A's Milestone 3 for a couple of representative cases through the
actual UI (not the full ~130-case matrix — that belongs in the API suite, where it's fast; a handful
of UI cases confirms the two layers agree).

### Milestone 6 (later, harder — don't start here): device pairing

Requires either a real physical test device or an emulator, and touches hardware-adjacent flows.
Treat this as a stretch goal once Milestones 1–5 are solid, not an early target.

---

## Part C — Bringing it together

### Suggested overall order (interleaving API and Web, not doing all of one then all of the other)

1. API Milestone 1–2 (skeleton, smoke, auth) — foundation, low risk
2. Web Milestone 1–2 (understand existing suite, add environment config) — foundation, low risk
3. API Milestone 3 (RRULE dataset conversion) — fast, high-value, reuses existing QA knowledge
4. API Milestone 4 (task creation + polling helper) — the core skill; **build the polling helper
   here once, then reuse it in Web Milestone 4**
5. Web Milestone 3 (login flow + `storageState`)
6. Web Milestone 4 (real task creation through the UI, using the polling helper from step 4)
7. API Milestone 5 + Web Milestone 5 (negative cases, routines)
8. CI integration (Phase 5 of the roadmap doc) for whatever's solid at this point
9. Web Milestone 6 (device pairing) — only once everything above is stable

### Why this order specifically

The API polling helper (step 4) is deliberately built *before* the web task-creation test (step 6)
so you build it once and reuse it — this is a real, common pattern: your fastest, most reliable
signal for "is this async thing done yet" almost always comes from the API layer, even when the
test you're ultimately writing is a UI test. Building it API-side first also means you can validate
the *pattern itself* (polling, timeout, terminal-state detection) against a system you're not also
simultaneously debugging Playwright locators against — one variable at a time.

### The recurring theme, made concrete one more time

Every milestone above that involves a real task hits the same wall a normal CRUD API/UI test never
does: **the response isn't fixed.** Two runs of the identical test input can take a different, both
correct, path. This isn't a flaw in your test — it's a real property of the system, covered in
depth earlier in this conversation and in Phase 6 of the roadmap document. The concrete engineering
answer, every time it comes up here: assert on **state** (did it finish, what tool got called, what
step count), assert on a **success rate across repeated runs** where a single run genuinely can't
tell you enough, and reserve exact-string assertions for the few places — schema shape, a specific
tool name, a status code — where there really is only one correct answer.
