# Master Study Plan — SDET / Senior QA Automation

*The single, consolidated plan. Merges your original `Job_Switch_Study_Roadmap.md` with
[01_automation_testing_roadmap.md](01_automation_testing_roadmap.md) (how to learn each skill) and
[02_airtap_automation_implementation_plan.md](02_airtap_automation_implementation_plan.md) (what to
build against Airtap). Where those three disagreed, this document is the authority. Read this one
first; use the other two as drill-downs.*

**Target role:** Senior QA Automation Engineer → SDET-2 / SDET-3

---

## Your actual starting position (read this before the topic list)

This matters because it should change how you allocate time, and most generic roadmaps would
mislead you here.

**What you already have that most candidates don't:** 8 years of QA plus ~1 year on a mobile
agentic-AI product. You have *hands-on* experience with LLM-driven agents, grounding failures,
non-deterministic behavior, prompt injection risk, and agent evaluation — on a real production
system, not a tutorial. After the work we did in `docs/qa-learning/`, you can also explain the
architecture of one end-to-end. That combination is genuinely rare in the market right now.

**What's actually holding you back:** not AI knowledge — automation depth. Specifically: writing
framework-quality Python without AI holding your hand, and pytest fundamentals (your original
roadmap listed pytest only as a "tool" — it's actually the foundation everything else sits on).

**So the strategic read:** don't spend Month 3 "learning AI testing" as if it's new. Front-load the
automation fundamentals you're weakest on, and treat the AI section as *consolidation and framing*
of what you already know. Your differentiator is already built — you need the automation
credibility to make interviewers take it seriously.

---

## Priority legend

| | Meaning |
|---|---|
| 🔴 **P0** | Interview-blocking. You will be rejected without this. Do not skip, do not compress. |
| 🟠 **P1** | Expected of the target role. Absence is a visible weakness. |
| 🟡 **P2** | Differentiator. Gets you from "qualified" to "preferred candidate." |
| 🟢 **P3** | Awareness only. Know the name, one sentence, when you'd use it. Do not deep-study. |

`#` = learning order within a track. Priority = how much it matters. They're independent — work
through the `#` order, but invest your effort by priority.

---

## Master topic table

### Track 1 — Python for Automation

| # | Topic | Priority | Notes |
|---|---|---|---|
| 1 | Virtual environments, `pip`, `requirements.txt` | 🔴 P0 | Table stakes. **First** — you can't write a line of project code without it. |
| 2 | Reading a traceback bottom-up | 🔴 P0 | **Missing from your original roadmap.** Needed the moment your first code breaks. The single highest-ROI debugging skill. |
| 3 | Collections (`dict`, `set`, `defaultdict`, `Counter`, `namedtuple`) | 🟠 P1 | Basic data handling. Test data manipulation, response parsing. |
| 4 | Exception handling | 🔴 P0 | Custom exceptions, `try/except/finally`, when *not* to catch. |
| 5 | `*args` / `**kwargs`, lambda | 🟠 P1 | Constant in framework code + classic interview question. **Must come before decorators** — decorators are written using them. |
| 6 | OOP: classes, objects, inheritance, `self`, `__init__` | 🔴 P0 | Page Objects and API clients *are* classes. Non-negotiable. |
| 7 | OOP theory terms (polymorphism, encapsulation, abstraction) | 🟠 P1 | Needed to *define* in interviews; low practical depth needed. Don't over-study. |
| 8 | **Decorators** | 🔴 P0 | Every pytest fixture/marker/parametrize is a decorator. If these feel like magic, pytest will too. Write one from scratch. |
| 9 | Context managers (`with`) | 🔴 P0 | Browser sessions, API sessions, setup/teardown. `@contextmanager` uses decorators — hence after #8. |
| 10 | Type hints | 🟠 P1 | Modern framework code is type-hinted; improves readability and catches errors early. |
| 11 | Dataclasses | 🟠 P1 | Clean test-data models without boilerplate. Needs type hints (#10). Pairs well with Pydantic later. |
| 12 | Deep vs shallow copy, mutable vs immutable, list vs tuple | 🟠 P1 | Interview flashcards *and* a real source of test bugs (shared data mutated between tests). |
| 13 | Generators & iterators | 🟡 P2 | Interview favorite ("generator vs iterator"); moderate practical use in test data. |
| 14 | Async programming (`async`/`await`) | 🟡 P2 | Needed for `httpx` async clients + some Playwright patterns. |
| 15 | Threading vs multiprocessing, GIL | 🟢 P3 | **Interview trivia only.** Learn the one-paragraph answer. Do *not* build projects around this — parallel test execution is solved by `pytest-xdist`, not by you writing threads. |

> Full explanations with examples: [track_01_python_for_automation.md](track_01_python_for_automation.md)

### Track 2 — Pytest (the foundation both API and UI sit on)

> **This entire track was missing from your original roadmap** — pytest appeared only as a bullet
> under "Tools." It's arguably the most important track in this document, because everything in
> Tracks 3 and 4 is built on it.

| # | Topic | Priority | Notes |
|---|---|---|---|
| 1 | Test discovery, naming conventions, `assert` | 🔴 P0 | |
| 2 | `pytest.ini` / config, CLI flags (`-k`, `-x`, `-v`, `--lf`) | 🟠 P1 | Configure the project before the suite grows. Daily-driver ergonomics. |
| 3 | **Fixtures** — definition, scope, `yield` teardown | 🔴 P0 | The single most important pytest concept. `function`/`class`/`module`/`session` scope and *why* you'd choose each. `yield` *is* how teardown works — learn them together. |
| 4 | `conftest.py` — what it is, how discovery works | 🔴 P0 | Where shared fixtures live. |
| 5 | `@pytest.mark.parametrize` | 🔴 P0 | One test, many inputs. This is what turns a 130-case manual checklist into 10 lines of code. |
| 6 | Markers + `-m` filtering (smoke/regression/slow) | 🟠 P1 | How you run subsets in CI. |
| 7 | Fixture factories, `autouse` | 🟡 P2 | Intermediate patterns you'll want once suites grow. |
| 8 | Plugins: `pytest-xdist`, `pytest-html`, `pytest-asyncio`, `pytest-rerunfailures`, `pytest-cov` | 🟠 P1 | Know what each does; install as needed. |

### Track 3 — API Automation

> **Deliberately the heaviest-weighted track.** Current industry research confirms API testing is
> the most underinvested, highest-value QA skill — most engineers over-index on UI automation
> because it's visual, but API tests catch more bugs, run faster, break less, and are valued more
> by hiring managers.

| # | Topic | Priority | Notes |
|---|---|---|---|
| 1 | HTTP methods, status code families, headers, params vs. body | 🔴 P0 | Understand *why* each status family means what it does, not memorized numbers. |
| 2 | `requests` library + `Session` objects | 🔴 P0 | Session = connection reuse + shared auth/cookies. |
| 3 | Auth: API keys, Bearer tokens, JWT | 🔴 P0 | Moved early — you can't call an authenticated Airtap endpoint without it (needed for doc 02 Part A Milestone 2). |
| 4 | Response validation beyond status code | 🔴 P0 | "It returned 200" is not a test. |
| 5 | **JSON Schema validation** (`jsonschema` or `pydantic`) | 🔴 P0 | The difference between "it's JSON" and "it's the *right* JSON." |
| 6 | Framework structure: base client, config per environment, no hardcoded URLs/secrets | 🔴 P0 | Structure the suite *before* it grows — refactoring 20 unstructured tests is wasted work. The difference between "scripts" and "a framework," and what AI-generated code usually gets wrong. |
| 7 | Negative & edge-case testing | 🔴 P0 | Wrong auth, missing fields, malformed body, boundary values. **This is where API testing earns its value.** |
| 8 | Test data: `Faker`, builders/factories | 🟠 P1 | Stop hardcoding dicts across tests. |
| 9 | API chaining (output of one call feeds the next) | 🟠 P1 | Core to any real workflow test. |
| 10 | Retry logic & handling rate limits | 🟠 P1 | |
| 11 | **Async polling for job-driven APIs** | 🔴 P0 | **Missing from your original roadmap.** Critical for Airtap specifically — tasks complete asynchronously. Poll-until-terminal-state with timeout, never `sleep()`. |
| 12 | Mocking (`unittest.mock`, `responses`) | 🟡 P2 | Test *your* handling of an API without depending on the real one. |
| 13 | `httpx` + async API testing | 🟡 P2 | Reach for it when testing genuinely async backends. Needs Track 1 #14. |
| 14 | Auth: OAuth2 flows | 🟡 P2 | Know the flow conceptually; full automation of OAuth is rare and often intentionally avoided. |
| 15 | Contract testing (Pact-style) | 🟢 P3 | Know the concept and why it exists. Rarely required at SDET-2/3 unless the JD names it. |

### Track 4 — Playwright / Web UI Automation

| # | Topic | Priority | Notes |
|---|---|---|---|
| 1 | Browser / context / page — what each level is, and contexts for parallel isolation | 🔴 P0 | A context is an isolated session; many contexts per browser. That isolation is also what makes parallel runs safe. |
| 2 | `codegen` for bootstrapping tests | 🟢 P3 | Day-one accelerator: record a flow, then read and clean up what it generates. Never ship raw. |
| 3 | **Locators, modern priority order** | 🔴 P0 | `get_by_role` → `get_by_label`/`get_by_text` → `get_by_test_id` → CSS/XPath last. Role-based doubles as an accessibility check. |
| 4 | Assertions (`expect`) and auto-retrying assertions | 🔴 P0 | |
| 5 | Auto-waiting — and the cases where it isn't enough | 🔴 P0 | Understand *why* you rarely need `sleep()`, and the exceptions (waiting on a network response/specific state). |
| 6 | Trace viewer, screenshots/video on failure | 🔴 P0 | Moved early — you need debugging tooling before the topics that generate hard failures. Essential for CI failures you can't watch live. |
| 7 | Fixtures (`pytest-playwright`, the `page` fixture) | 🔴 P0 | |
| 8 | Auth + `storageState` (log in once, reuse) | 🔴 P0 | |
| 9 | Page Object Model | 🟠 P1 | Airtap's existing suite uses it, so you need it. |
| 10 | Fixtures-first / composable fixtures as the modern alternative | 🟡 P2 | 2026 guidance leans this way for small/medium suites. Know both and when each fits. |
| 11 | Handling real flakiness sources (timing, animation, dynamic content) | 🔴 P0 | This is where UI suites live or die. |
| 12 | Network interception / route mocking | 🟡 P2 | Powerful for isolating the frontend from backend flakiness. |

### Track 5 — Framework Design & Test Architecture

> Rows 2–3 deepen what Track 3 #6 introduced. That overlap is intentional: Track 3 gets you a
> working structure for one API suite; Track 5 is about architecture across a whole framework.

| # | Topic | Priority | Notes |
|---|---|---|---|
| 1 | **Test strategy: what to automate vs. leave manual** | 🟠 P1 | **Missing from both roadmaps.** A planning decision that comes *before* building. ROI thinking, test pyramid application, risk-based prioritization. Classic senior interview question. |
| 2 | Project structure (`tests/`, `pages/`, `api_clients/`, `config/`, `utils/`) | 🔴 P0 | |
| 3 | Environment/config management (never hardcoded) | 🔴 P0 | |
| 4 | **Writing maintainable test code** (naming, DRY, avoiding over-abstraction) | 🟠 P1 | Applies from the first line you write, not as a final polish pass. Interviewers read your code — over-engineered frameworks are as bad as scripts. |
| 5 | Test data strategy (creation + cleanup) | 🟠 P1 | Don't pollute shared environments. |
| 6 | **Combining API + UI in one suite** | 🔴 P0 | **Missing from your original roadmap.** Set up state via fast API calls, test only the thing you care about via UI. Massive runtime savings — and a strong senior-level answer. |
| 7 | Logging strategy in a test framework | 🟠 P1 | |
| 8 | Reporting: `pytest-html`, **Allure** | 🟠 P1 | Allure is frequently named in JDs; worth real setup practice. |
| 9 | Parallel execution (`pytest-xdist`) + what makes tests parallel-safe | 🟠 P1 | Independence, no shared mutable state. |
| 10 | **Flaky test root-causing (not just retrying)** | 🔴 P0 | Understand *why* it's flaky before reaching for `rerunfailures`. This is a senior/junior dividing line. |

### Track 6 — CI/CD, Cloud & Tooling

> **Git and Linux/CLI are scheduled in Week 1**, not with the rest of this track — you need both
> from day one to version your framework and read failure output. The rest of the track lands in
> Week 10.

| # | Topic | Priority | Notes |
|---|---|---|---|
| 1 | **Linux/CLI basics** (`grep`, `tail`, `find`, pipes, exit codes, env vars) | 🟠 P1 | **Missing from both roadmaps.** Underpins Git, CI log reading, and Docker. Learn it first. |
| 2 | **Git properly** — branching, PRs, merge vs. rebase, resolving conflicts | 🔴 P0 | Your original roadmap just said "Git." You need working fluency, not awareness. |
| 3 | GitHub Actions — workflow YAML, triggers, caching, artifacts | 🔴 P0 | The modern default. Prioritize this over Jenkins. |
| 4 | Secrets management in CI | 🔴 P0 | Never hardcoded, never logged. Needed as soon as your first workflow authenticates. |
| 5 | Running browser tests in CI (headless, installing browsers, trace on failure) | 🔴 P0 | |
| 6 | Docker basics — image vs. container, Dockerfile, running tests in a container | 🟠 P1 | Common in JDs; genuinely useful for environment consistency. |
| 7 | AWS: S3, CloudWatch, IAM (concepts) | 🟡 P2 | Directly relevant — Airtap uses S3 + CloudWatch. Focus on log inspection and storage concepts. |
| 8 | AWS: EC2 | 🟢 P3 | Conceptual awareness only. |
| 9 | Jenkins | 🟢 P3 | Legacy but still in many enterprise JDs. Learn *only* if a specific target job names it. Don't invest ahead of need. |

### Track 7 — SQL

> Kept as its own track because it's genuinely interview-blocking and completely independent of
> everything else. Perfect for spaced repetition — 15 min/day beats one long weekend session.

| # | Topic | Priority |
|---|---|---|
| 1 | `SELECT`, `WHERE`, `ORDER BY`, `LIMIT` | 🔴 P0 |
| 2 | `JOIN`s (inner/left/right/full) — and knowing *which* to use | 🔴 P0 |
| 3 | `GROUP BY` + aggregates, `HAVING` vs. `WHERE` | 🔴 P0 |
| 4 | Subqueries | 🟠 P1 |
| 5 | `UNION` vs. `UNION ALL` | 🟠 P1 |
| 6 | Using SQL for *test validation* (verifying UI/API actions actually hit the DB) | 🟠 P1 |
| 7 | CTEs (`WITH`) | 🟡 P2 |
| 8 | Window functions (`ROW_NUMBER`, `RANK`, `OVER`) | 🟡 P2 |

### Track 8 — AI Testing

> **Your differentiator track.** But note the split below — some of this is required for interviews
> even though Airtap doesn't use it, and knowing *which is which* is itself a strong signal.

**8a. Already covered in depth by `docs/qa-learning/` — this is consolidation, not new learning:**

| # | Topic | Priority |
|---|---|---|
| 1 | LLM basics: context window, tokens, temperature, hallucination | 🔴 P0 |
| 2 | Prompt engineering + system prompt design | 🔴 P0 |
| 3 | Prompt injection (direct + indirect) | 🔴 P0 |
| 4 | Tool / function calling | 🔴 P0 |
| 5 | Agent architecture: planning, memory, tool execution, the agent loop, ReAct | 🔴 P0 |
| 6 | Grounding & GUI-agent-specific failure modes | 🔴 P0 |
| 7 | Guardrails, fallback logic, human-in-the-loop | 🟠 P1 |
| 8 | AI evaluation: accuracy, relevance, groundedness, toxicity, latency, cost | 🔴 P0 |
| 9 | LLM-as-a-judge + its biases (verbosity, position, drift) | 🔴 P0 |
| 10 | Agent-specific metrics: task success rate, step accuracy, trajectory | 🟠 P1 |

**8b. Required for interviews, but NOT used by Airtap — know the theory *and* know why Airtap skips it:**

| # | Topic | Priority | Note |
|---|---|---|---|
| 1 | RAG (retrieval-augmented generation) | 🔴 P0 | Near-guaranteed interview question. Airtap doesn't use it — being able to explain *why not* (scale threshold, full-context injection instead) is a stronger answer than reciting the pipeline. |
| 2 | Embeddings & similarity search | 🟠 P1 | Same framing. |
| 3 | Vector databases | 🟠 P1 | Know when you *don't* need one — that's the senior answer. |
| 4 | Fine-tuning vs. RAG vs. prompting ("which lever") | 🟠 P1 | Classic decision-framework question. |

**8c. New — actually writing AI tests in code (the gap between knowing and doing):**

| # | Topic | Priority | Note |
|---|---|---|---|
| 1 | Deterministic checks where they still apply (schema, tool name, status) | 🔴 P0 | Start here — these are ordinary pytest assertions, and the easiest bridge from Track 3. |
| 2 | State verification over screenshot comparison | 🔴 P0 | |
| 3 | Writing pytest tests that assert on a **success rate across N runs**, not one result | 🔴 P0 | The concrete answer to non-determinism. |
| 4 | Building an LLM-as-judge fixture in pytest | 🟠 P1 | |
| 5 | Adversarial / prompt-injection test cases as automated tests | 🟠 P1 | |
| 6 | Observability tools: **Langfuse** (Airtap uses this), DeepEval, Promptfoo, LangSmith | 🟡 P2 | Know names + niche. Langfuse first, since you can speak to it from real experience. |

### Track 9 — Interview Preparation (beyond technical topics)

> **Almost entirely missing from your original roadmap**, and it's often what decides the outcome.

| # | Topic | Priority | Notes |
|---|---|---|---|
| 1 | **Your Airtap story, told well** | 🔴 P0 | Build this first — the other answers reference it. Practice a 2-minute version of "what does the product do and what did you test." |
| 2 | Explaining non-determinism testing in 60 seconds | 🔴 P0 | Your single strongest differentiator — rehearse it until it's crisp. |
| 3 | **Behavioral / STAR stories** | 🔴 P0 | Prepare 5–6: hardest bug found, a production escape, disagreeing with a dev, improving a process, a failure you owned. |
| 4 | **System design for SDET**: "design an automation framework for X" | 🔴 P0 | Practice out loud. Structure: scope → layers → tooling → data → CI → reporting → maintenance. |
| 5 | Live coding: Python basics under time pressure | 🟠 P1 | String/list manipulation, dict counting. Not LeetCode-hard — SDET rounds are usually gentler than SWE rounds. |
| 6 | Questions *you* ask the interviewer | 🟠 P1 | Signals seniority. Ask about flakiness rates, release gating, ownership of test infra. |
| 7 | Code review exercise (reading someone else's test code and critiquing it) | 🟡 P2 | Increasingly common in SDET loops. |

### Track 10 — Domain Bonus (given your background)

| # | Topic | Priority | Notes |
|---|---|---|---|
| 1 | Appium / mobile automation awareness | 🟡 P2 | You work on a *mobile* agent product. Even conceptual fluency here strengthens your story — and note Airtap deliberately uses Accessibility Service + HID dongle rather than ADB, which is an interesting thing to be able to explain. |
| 2 | ADB basics | 🟢 P3 | Awareness — useful vocabulary in mobile-adjacent interviews. |
| 3 | Performance testing concepts (Locust for Python) | 🟢 P3 | Only if a JD asks. |
| 4 | Security testing awareness (OWASP Top 10) | 🟢 P3 | One-line familiarity is enough unless targeting security-adjacent roles. |

---

## The 12-week plan

Changes from your original month split: (a) pytest gets a real home, (b) Git and Linux/CLI move to
Week 1 since you need them from day one, (c) no week carries two full tracks, (d) interview prep is
spread across months instead of crammed at the end, and (e) AI testing is treated as consolidation
rather than new learning.

### Month 1 — Foundations (the part you can't fake)

| Week | Focus | Build |
|---|---|---|
| **1** | **Setup + Python part 1** — venv/pip, **Git basics** (Track 6 #2), **Linux/CLI basics** (Track 6 #1), traceback reading, collections, exception handling, `*args`/`**kwargs` | Repo initialised, first commits |
| **2** | **Python part 2** — OOP, decorators, context managers, type hints, dataclasses, copy/mutable flashcards | Small practice scripts, no AI |
| **3** | **Pytest** — all of Track 2 | First real fixtures + parametrize |
| **4** | **API part 1** — HTTP, `requests`/Session, auth, response + schema validation | Airtap API skeleton (doc 02 Part A **M1–M2**) |

**Month 1 deliverable:** a structured API test framework hitting real Airtap QA endpoints with
auth, environment config, and schema validation — committed to Git.

### Month 2 — Build depth

| Week | Focus | Build |
|---|---|---|
| **5** | **API part 2** — framework structure, negative testing, `Faker`/test data | RRULE parametrize suite (doc 02 Part A **M3**) |
| **6** | **API part 3** — async polling helper, API chaining, retry logic. **Begin STAR story drafting** (~30 min/week from here) | Task creation + polling (doc 02 Part A **M4–M5**) |
| **7** | **Playwright part 1** — browser/context/page, codegen, locators, assertions, auto-waiting, trace viewer | Understand + env-config the existing suite (doc 02 Part B **M1–M2**) |
| **8** | **Playwright part 2** — fixtures, `storageState` + login flow, POM, flakiness handling | Real login flow (doc 02 Part B **M3**) |

**Month 2 deliverable:** an API suite with a working async polling helper, plus a Playwright suite
with real login — both environment-configurable.

### Month 3 — Integrate, differentiate, prepare

| Week | Focus | Build |
|---|---|---|
| **9** | **Framework design** (Track 5) — test strategy, maintainable code, test data, logging, Allure. Begin system-design reading | Combining API + UI, then routines via UI (doc 02 Part B **M4–M5**) |
| **10** | **CI/CD** (Track 6 #3–#8) — GitHub Actions, secrets, browser tests in CI, Docker basics | Both suites running in CI |
| **11** | **AI testing** — Track 8c (writing the tests) + Track 8b gap-fill (RAG/embeddings/vector DBs theory) + Track 8a review pass + **Track 10** (Appium/ADB awareness) | Non-determinism tests against Airtap |
| **12** | **Interview readiness** — system design out loud, mock interviews, STAR + Airtap narrative rehearsal, code review practice | Portfolio project 2 finalised |

**Month 3 deliverable:** two portfolio-ready frameworks running in CI, plus a rehearsed 2-minute
story about testing a production AI agent.

### Throughout (all 12 weeks)

- **SQL** — 15 min/day, every day. Spaced repetition beats one long weekend session.
- **Interview flashcards** — 10 min/day. Python trivia, AI concepts, definitions.
- **Portfolio project 2** — build it *incrementally from Week 5 onward* by mirroring each Airtap
  pattern onto a public demo site. Don't leave it to Week 12; you just polish it there.

---

## Daily allocation (revised)

Your original table split time across all 5 topics every single day. That's less effective than
focused blocks — context-switching between five domains daily slows all five down.

**Better pattern — one primary focus + two constants:**

| Slot | Time | What |
|---|---|---|
| **Primary block** | 60–75 min | Whatever the current week's focus is (deep, uninterrupted) |
| **SQL** | 15 min | Every day, all 90 days — spaced repetition, ideal for this |
| **Interview flashcards** | 10 min | Python trivia, AI concepts, definitions — retrieval practice |
| **Hands-on build** | 30–45 min | Actually writing framework code against Airtap |

Total ≈ 2h/day, similar to your original 135 min, but with far less fragmentation.

---

## Portfolio projects (consolidated)

Your original list had 3 practice domains (ecommerce/flight/banking/dashboard) plus 3 frameworks.
That's more than needed and spreads effort thin.

**Build two things properly instead of six things shallowly:**

1. 🔴 **Airtap API + UI framework** (the real one, per
   [02_airtap_automation_implementation_plan.md](02_airtap_automation_implementation_plan.md)) —
   this is your strongest asset. Real product, real complexity, real async/non-deterministic
   challenges. Interviewers remember this far more than a practice ecommerce suite.
   *Built Weeks 4–10.*
2. 🟠 **One public-facing portfolio framework** — a clean, well-structured API + UI suite against a
   public demo site, for when you can't share Airtap code. Keep it small and *excellent*, not large
   and sprawling. This is your "here's my GitHub" answer.
   *Built incrementally from Week 5, finalised Week 12 — mirror each Airtap pattern onto it as you
   learn that pattern, rather than building it from scratch at the end.*

Skip: separate flight-booking, banking, and dashboard practice suites. They teach the same skills
three more times with diminishing returns.

---

## What I removed or downgraded, and why

You asked me to cut what isn't important — here's the honest accounting:

| Item | Action | Reasoning |
|---|---|---|
| **AWS AMI** | ❌ Removed | Near-zero relevance to SDET work. Machine images are an infra concern, not a testing one. |
| **Multiprocessing (deep study)** | ⬇️ Downgraded to P3 | Kept as interview trivia only. Parallel test execution is solved by `pytest-xdist` — you will not hand-roll multiprocessing for tests. |
| **GIL** | ⬇️ Downgraded to P3 | One-paragraph interview answer. No practical application in your day-to-day. |
| **Jenkins** | ⬇️ Downgraded to P3 | Still appears in enterprise JDs, but GitHub Actions is the better investment in 2026. Learn Jenkins *reactively* if a specific target role requires it. |
| **Contract testing (Pact)** | ⬇️ Downgraded to P3 | Genuinely useful in microservice-heavy orgs, but rarely required at SDET-2/3 unless explicitly named. Know the concept. |
| **Practice projects: flight booking, banking, dashboard** | ❌ Removed | Redundant with each other. Two strong projects beat six weak ones. |
| **OOP theory terms as deep study** | ⬇️ Downgraded to P1 | You need to *define* polymorphism/encapsulation in an interview; you don't need to deeply architect around them for test code. |
| **OpenAI Evals / LangSmith (as study targets)** | ⬇️ Downgraded to P2 | Know the names. Prioritize Langfuse — you have actual production exposure to it via Airtap, which is worth more than surface knowledge of three others. |

## What I added that was missing from both documents

| Addition | Why it matters |
|---|---|
| **Entire pytest track** | The largest gap. Your roadmap listed it as a tool; it's the foundation of everything in Tracks 3 and 4. |
| **Async polling for job-driven APIs** | Specifically critical for Airtap (tasks complete asynchronously) and a genuinely transferable senior skill. |
| **Combining API + UI in one suite** | A senior-level pattern and a strong interview answer. |
| **Flaky test root-causing (vs. retrying)** | A direct senior/mid dividing line in interviews. |
| **Test strategy — what to automate vs. not** | Classic senior question your roadmap didn't cover at all. |
| **Reading tracebacks / debugging skill** | Assumed by everyone, taught by no one. |
| **Git depth** (not just "Git") | Working fluency with branching/PRs/rebasing is assumed at this level. |
| **Linux/CLI basics** | You cannot debug CI failures without it. |
| **Behavioral + STAR + your Airtap narrative** | Often decides the outcome, and you have unusually good material here. |
| **System design practice (spoken, not just read)** | It's a *performance*, not a knowledge test. |
| **Writing maintainable test code** | Interviewers read your code. Over-abstraction is penalized as much as no abstraction. |
| **The "know it for interviews, know why Airtap skips it" framing for RAG/vectors** | Turns a gap into a demonstration of judgment. |
| **Appium/ADB awareness** | Directly reinforces your mobile-agent domain story. |

---

## One-paragraph version, if you only remember one thing

Your AI testing knowledge is already interview-strong — the work in `docs/qa-learning/` covered it
more deeply than most candidates will ever go. What will actually get you the offer is proving you
can *build and maintain automation frameworks independently*, without AI writing it for you. So:
**pytest and API automation are your P0 focus for the next six weeks**, Playwright and CI/CD for
the six after, and AI testing becomes the thing you *talk about brilliantly* rather than the thing
you're still learning. Build against Airtap, not toy apps — a real production AI agent is a far
better interview story than another practice ecommerce suite.
