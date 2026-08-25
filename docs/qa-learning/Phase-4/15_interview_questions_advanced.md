# 15 — Interview Questions: Advanced

*Phase 4 · Document 3 of 3. Assumes [13](13_interview_questions_beginner.md) and
[14](14_interview_questions_intermediate.md). This document covers system design, hard QA judgment
calls, and the questions where a QA background is genuinely the strongest answer in the room — not
generic AI knowledge, but the ability to say precisely how you'd test and de-risk a system like
this. Same three-part format throughout.*

---

## Q1. How do you test a system whose core logic is non-deterministic?

### Part A — Generic AI Interview Answer
This is the core mindset shift from classical QA, worth stating cleanly: the same prompt can
produce genuinely different outputs that are *all* correct, so exact-match assertions
(`assertEqual(actual, expected)`) mostly stop working as the primary testing tool. You're no longer
testing for one expected output — you're testing for a *distribution* of acceptable behavior. In
practice this means: run the same case multiple times and track a success *rate*, not a single
pass/fail; grade output against a rubric or with an LLM-as-a-judge instead of an exact string match
where no single right answer exists; reserve exact-match assertions for the narrow places they still
genuinely apply (does it parse as valid JSON, does it match a required schema — Phase 3's roadmap
notes call this out as "a rare place where classical exact checks still apply to an LLM"); and treat
a *drop* in a tracked success rate, not a single failed run, as your actual regression signal.

### Part B — How Airtap Implements This
Airtap's own architecture reflects exactly this philosophy rather than fighting it. Its evaluation
framework runs each curated test case through the real production task engine and grades it with a
mix of narrow deterministic checks (did a specific required piece of content appear or not — one of
the few places an exact-ish check is appropriate) and an LLM-judge, which answers a set of yes/no
questions against the full task trace rather than comparing to one fixed expected transcript. Sampling
parameters (temperature, top-P) are exposed as configurable, per-call-purpose knobs specifically
because different call types want different points on the determinism spectrum — a title-generation
call can tolerate more variety than the main decision loop, which generally wants consistency. Where
Airtap is honestly incomplete against this ideal, worth naming directly: the evaluation framework
that embodies this philosophy has no automatic trigger — it's run on demand, not gated into every
prompt or model change automatically, which is the single most concrete, actionable gap identifiable
in the whole product from a testing-maturity standpoint.

### Part C — QA Perspective
- **What to validate**: build every regression check for AI-driven behavior around a success *rate*
  across N repeated runs, not a single run's pass/fail — and explicitly decide, per test, whether a
  rate drop of some threshold (not any single failure) is what should actually block a release.
- **Possible bugs**: a test suite that silently over-relies on exact-match assertions against
  non-deterministic output is itself a bug — it will produce constant false failures on perfectly
  valid variation and erode trust in the whole suite over time.
- **Logs to inspect**: evaluation run reports (aggregate pass rate, cost, latency per run) for
  trend-level signal; individual reasoning traces for single-case root-causing.
- **Edge cases to test**: cases specifically near a decision boundary (ambiguous requests, screens
  with multiple plausible correct interpretations) — these are where run-to-run variance is highest
  and where a rate-based approach earns its value over a single-run check.
- **Likely follow-up questions**: "How many repeated runs are 'enough' to trust a success-rate
  number, and how would you decide?" "What's the difference between accepting non-determinism and
  lowering your quality bar?"

---

## Q2. What's the difference between action-level and task-level success — and why can an agent "succeed" while still being broken?

### Part A — Generic AI Interview Answer
Success has to be measured at two levels that genuinely come apart in both directions, and
conflating them is a classic mistake. **Action-level**: did this one specific step do the right
thing? **Task-level**: did the overall goal actually get accomplished? They diverge two ways, both
dangerous: every individual action can be flawless while the agent works the *wrong overall plan*
(perfect execution of a wrong goal); or several individual actions can be wrong — a mistaken tap, a
recovery, a retry — while the task still eventually, accidentally, succeeds. That second case is the
one that should worry you most: a lucky stumble into the right final state isn't a working agent,
it's an incident waiting for a slightly different screen next time, and a metric that only looks at
final task success will happily hide it, reporting a clean pass.

### Part B — How Airtap Implements This
Airtap's own reasoning trail architecture makes both levels genuinely inspectable, even where they
aren't yet both formally scored as separate named metrics (see the Task Success Rate vs. trajectory
discussion in the intermediate document). Every single step carries its own reasoning and its own
tool call, independently readable — action-level detail is always available. Task-level success is
what the evaluation framework's checks primarily grade today (did the final response contain the
right content, was a sound plan stated). A concrete, real illustration of the divergence exists in
the product's own design: the operating rules include an explicit instruction to verify the correct
app/account/state is actually in focus before continuing a flow, precisely because it's possible to
be several steps into a task that's silently operating in the wrong context — every subsequent
action can be locally "correct" relative to that wrong context while the task as a whole is
completely off track.

### Part C — QA Perspective
- **What to validate**: don't grade a task purely by its final state — sample and read the
  step-by-step trajectory on at least a subset of passing cases, specifically looking for
  unnecessary recoveries, retries, or corrections that suggest a fragile, lucky path rather than a
  clean one.
- **Possible bugs**: a task graded "passed" by an automated check that only inspects the final
  output, while the actual execution path included several avoidable missteps — this is a real,
  silent quality gap current tooling here doesn't fully surface.
- **Logs to inspect**: full per-step reasoning and tool-call history for a "passed" case, read end
  to end rather than just checking the final response.
- **Edge cases to test**: deliberately re-run a task that passed once and check whether it takes a
  similarly clean path on repeated runs, or whether the first pass was a lucky outlier.
- **Likely follow-up questions**: "How would you formally add a trajectory-quality metric to an
  evaluation framework that currently only has task-level and plan-quality checks?" "Give an example
  from this product specifically where action-level and task-level success could diverge."

---

## Q3. How do you assess and mitigate prompt injection risk in an agent that consumes untrusted visual content?

### Part A — Generic AI Interview Answer
Prompt injection is an attacker smuggling instructions into a model's input so it ignores the
developer's original instructions and follows the attacker's instead — the LLM-era cousin of SQL
injection, except there's no clean escaping/parameterization fix, because natural language *is* the
instruction format. **Direct** injection is the user typing the attack themselves. **Indirect**
injection is the scarier, more relevant case for an agent: the attack is hidden in content the model
merely *reads* as part of its normal job — a web page, a document, an image with embedded text — and
fires when the model processes it as ordinary input. For a chatbot, a successful injection might leak
a system prompt. For an agent that can actually *act* on the world, the same injection can trigger a
real, sometimes irreversible action — which is exactly why this is described as the highest-blast-
radius failure category for any action-taking agent. Mitigation is defense in depth, not a single
fix: clearly separate untrusted content from instructions in how it's framed to the model,
least-privilege tool access, mandatory confirmation before anything irreversible, never storing
secrets in a prompt that could be exfiltrated, and a standing adversarial/red-team test suite rather
than a one-time check.

### Part B — How Airtap Implements This
This is a confirmed, real risk surface for Airtap specifically, not a theoretical one worth just
name-dropping: every single agent step reads a screenshot of **arbitrary, untrusted content** — any
app, any website the agent is asked to navigate — as a first-class input to its next decision. A
manipulated web page or app screen containing adversarial visible text is exactly the indirect-
injection vector described generically above, just delivered as pixels instead of retrieved
document text. Confirmed mitigations that exist today: explicit guardrails against ever revealing
internal details (system prompt content, tool schemas, skill contents), a hard rule against ever
inventing a credential, and an instruction to treat any visible app state as untrusted until key
task-defining details are actually verified against the current request. What was **not** confirmed
to exist: any dedicated detection step that specifically scans on-screen content for
injection-shaped instructions before the model reasons about it, or a formal, code-enforced gate
that blocks an irreversible action specifically when it follows suspicious on-screen content. The
defense that exists today is about limiting *consequences*, not detecting the attempt itself — a
distinction worth being precise about rather than overstating the protection in place.

### Part C — QA Perspective
- **What to validate**: no injected content — direct or indirect — should be able to trigger an
  irreversible action without whatever confirmation/clarification mechanism exists; internal
  details (system prompt, tool schemas) should never leak under adversarial pressure, on-screen or
  in conversation.
- **Possible bugs**: because there's no confirmed dedicated injection-detection layer, and separately
  no confirmed formal risk-tier gate specifically for irreversible actions, the combination of
  "injected instruction + no hard gate" is the single highest-priority scenario to test in this
  entire product — this is a real, not hypothetical, exposure to actively probe.
- **Logs to inspect**: the step's own reasoning trail after suspected adversarial content — this will
  show whether the model noticed and reasoned about the odd content, or acted on it without any
  apparent awareness at all.
- **Edge cases to test**: construct real test pages/app states with visible adversarial instruction
  text and have the agent navigate to and screenshot them as part of an otherwise-normal-looking
  task; test both direct (in the user's own request) and indirect (on-screen) channels separately.
- **Likely follow-up questions**: "How would you build this into a standing, automated red-team
  suite rather than a one-time manual check?" "If you found a real injection vulnerability here,
  what would you recommend as the fix, given there's no clean 'escaping' solution for natural
  language?"

---

## Q4. What automation layer would you choose for mobile GUI automation — ADB, Accessibility APIs, or dedicated hardware — and why?

### Part A — Generic AI Interview Answer
Underneath any mobile agent's decision sits some real automation layer that turns a decision into an
actual device action. The common names: **ADB** (Android Debug Bridge — a command-line pipe into a
device, the literal mechanism behind `adb shell input tap x y`), **UI Automator** (Android's native
UI-driving and -inspecting framework, also the source of the accessibility tree), **Appium**
(cross-platform automation wrapping these lower-level mechanisms), and **XCUITest** (Apple's native
iOS UI testing framework). The trade-offs: ADB is powerful and precise but requires developer mode /
USB debugging enabled on the target device — completely unavailable on a real end user's personal
phone in its default state. Accessibility-API-based approaches need no special developer access and
are the same mechanism screen readers legitimately use, making them viable on a normal consumer
device. Dedicated hardware input (a physical device emulating real keyboard/mouse/touch signals) is
the most expensive and complex option, but produces input that's genuinely indistinguishable from a
real human, which matters directly for any app that tries to detect and block software-level
automation — and it's the only viable option on platforms with no accessibility-based input-injection
API at all.

### Part B — How Airtap Implements This
Airtap deliberately does **not** use ADB — confirmed directly: every ADB-related reference found
anywhere in the Android receiver's own code is a comment describing something the app explicitly
does *not* rely on (a noted limitation requiring "ADB access" it doesn't have, and a developer-only
debug-analytics setup instruction unrelated to runtime automation). Instead, Airtap uses two real
mechanisms depending on how a device is set up: Android's Accessibility Service API for
software-driven input on devices set up that way, and a physical BLE-to-USB HID dongle for devices
set up to use genuine hardware input — the same dongle mechanism is the *only* option on iOS, since
iOS has no equivalent accessibility-based input-injection API at all. This is a deliberate,
well-reasoned product decision, not an oversight: the entire audience for this product is real
end-user phones that will never have developer mode turned on, so an ADB-dependent design would be a
non-starter from day one; and the hardware option exists specifically because some use cases need
input that's genuinely indistinguishable from a human, which no software-injection approach — ADB
included — can fully guarantee against a sufficiently determined detection mechanism.

### Part C — QA Perspective
- **What to validate**: confirm the correct automation path is actually used for each device
  configuration (software-driven vs. hardware-driven), and that capability claims in the agent's own
  instructions correctly differ between them (a hardware-only device should never be told, or
  attempt, something only the software path can do, like installing an app).
- **Possible bugs**: OS or OEM updates silently changing Accessibility Service behavior (a
  code-independent regression risk that needs periodic revalidation, not just after Airtap's own
  releases); firmware/hardware failures on the dongle path that have literally no software
  equivalent to reason about from logs alone.
- **Logs to inspect**: device-reported failure reasons (permission missing, paused, etc.) for the
  software path; the receiver app's own displayed connection state for the hardware path, since
  cloud-side logs alone often can't distinguish "asleep" from "genuinely broken" for physical
  hardware.
- **Edge cases to test**: OEM-specific accessibility/battery-management behavior (this varies
  significantly across manufacturers and needs its own device matrix); every physical-hardware
  failure mode (BLE range, dead battery, loose USB) that has no software analogue at all and must be
  tested on real devices.
- **Likely follow-up questions**: "Why is a physical hardware dongle the *only* viable option on
  iOS specifically?" "What's the actual product risk of relying on Accessibility Service instead of
  ADB, if any?"

---

## Q5. How would you design a risk-tiered safety system for an agent that can take real, irreversible actions?

### Part A — Generic AI Interview Answer
Because a GUI agent's mistakes are often irreversible — a sent message, a completed purchase, a
deleted file, with no "regenerate response" undo — the mature response is to risk-tier the entire
action space rather than treating every action the same way. A practical three-tier framework: 🟢
**safe to fully automate** (read-heavy, non-destructive actions — checking a status, searching,
scrolling); 🟡 **gated behind confirmation** (anything that posts, sends, or submits, and is hard to
undo); 🔴 **not yet safe to automate autonomously** (financial transactions, deletions, permission
grants — anything genuinely needing human judgment). This is exactly the same risk-based instinct
classical QA already applies to testing a payment flow harder than a settings page, translated
directly onto a new failure category. The strongest possible interview answer here explicitly says
this out loud: the instinct isn't new, only the failure category is.

### Part B — How Airtap Implements This
Airtap has real, genuine pieces of this philosophy in place, but — stated precisely rather than
overclaimed — **not a formal, code-enforced three-tier system**. What exists: general guardrails in
the agent's operating instructions (never fabricate a credential; verify state before acting), and,
specifically within one narrow skill built around firing direct system-level actions, an explicit
instruction to prefer the safer variant of an available action when multiple exist (a dial action
that only prefills a number, rather than one that places a call immediately, unless the user was
unambiguous about wanting the call placed). The agent also has two general-purpose escape hatches —
one for asking the user a clarifying question, one for explicitly handing off control entirely — but
invoking either of these for a genuinely risky action is a **model judgment call in the moment**, not
a hard, system-level gate that automatically fires for any action resembling a purchase or deletion,
regardless of which app it happens to be in. This is a real, honestly-identifiable gap: the design
philosophy described generically above is only partially, informally realized today.

### Part C — QA Perspective
- **What to validate**: this is the single highest-blast-radius test category identifiable across
  this entire product — coverage here should be deepest, not incidental.
- **Possible bugs**: an irreversible-feeling action proceeding without any confirmation step at all,
  in a scenario where a reasonable person would expect one — this is a plausible, real, currently
  under-guarded finding given the informal nature of what's in place today, not a hypothetical.
- **Logs to inspect**: the step's reasoning trail immediately preceding an action that plausibly
  approaches irreversibility, to see whether risk was actually considered at all.
- **Edge cases to test**: deliberately construct tasks that plausibly lead toward a purchase, a
  deletion, a message send, or a permission grant, across several different apps, and directly
  observe what happens today — don't assume protection exists; confirm it, case by case.
- **Likely follow-up questions**: "How would you actually implement a formal, code-enforced risk
  tier here, given the agent's tool calls are fairly generic (a `tap`, not a labeled `buy` action)?"
  "What would you propose as the very first, highest-leverage risk-gating change to ship?"

---

## Q6. What is "Eval Ops," and how would you operationalize continuous evaluation for an agent product?

### Part A — Generic AI Interview Answer
The modern framing: evaluation isn't a pre-launch script you run once and declare victory — it's a
continuous operational system, the same conceptual move as going from manual QA to a CI pipeline. In
practice this means running evals continuously against a sample of live production traffic (not just
a fixed offline dataset), treating a drop in eval scores like a failing build that blocks or flags a
release, and running two complementary kinds of tooling rather than one: something for CI gating
(block a bad prompt/model change before it ships) and something separate for continuous production
sampling (score a slice of real live traffic on an ongoing basis, feeding back into monitoring). Most
real teams end up running both, because pre-launch testing and post-launch monitoring are genuinely
different jobs with different data.

### Part B — How Airtap Implements This
Airtap has the *infrastructure* for the first half of this — a real evaluation framework with a
curated dataset, deterministic checks, and an LLM judge, running against the actual production task
engine rather than a simulated approximation of it — but it is **not currently operated as a
continuous pipeline**: it's triggered manually, on demand, from an internal screen, with no
confirmed automatic hook tying it to code merges, deployments, or a schedule. This is the single most
concrete, actionable finding in this entire document set: the hard infrastructure work already
exists; what's missing is wiring it into the release process so it runs *automatically* rather than
depending on someone remembering to trigger it. Separately, there's no confirmed continuous sampling
of live production traffic feeding back into an ongoing quality score — the tracing/debug capture
infrastructure that *could* support this (every LLM call, on every real task, is already captured)
exists, but isn't confirmed to be wired into any automated scoring loop today.

### Part C — QA Perspective
- **What to validate**: whether an eval run was actually attached to a given prompt/model change
  before it shipped — this should become a release-checklist item you personally hold the line on
  until it's automated.
- **Possible bugs**: a shipped prompt/model regression with literally no eval run in its history —
  the most direct, traceable instance of this exact gap, and worth specifically checking for after
  any noticed production quality dip.
- **Logs to inspect**: the evaluation framework's own run history for a given time window, correlated
  against the change history of prompts/models in that same window.
- **Edge cases to test**: a deliberately degraded prompt or model choice, run through the existing
  framework, to confirm it's actually *sensitive* enough to catch a real regression and not just
  passing everything by default.
- **Likely follow-up questions**: "What's the very first automation you'd build to close this gap —
  a merge-blocking CI check, or a scheduled nightly run — and why that one first?" "How would you
  design continuous production sampling on top of infrastructure that already captures every LLM
  call?"

---

## Q7. How do you debug a wrong agent decision when no error was thrown anywhere?

### Part A — Generic AI Interview Answer
This is the failure shape with no classical-QA analogue: the system did exactly what it was coded to
do, at every layer, and the *decision* was simply wrong — no exception, no failed status, nothing for
a traditional error-monitoring tool to catch. The right approach isn't searching logs for an error
that doesn't exist — it's reconstructing the reasoning chain: what did the system actually perceive,
what did it conclude from that, what did it decide to do, and where in that chain does the story stop
making sense? The single most useful habit for this category of bug: separate a *reasoning* failure
(the model misunderstood the situation from the start) from a *grounding/execution* failure (the
reasoning was correct, but the resulting action didn't land where or how intended) — these are
different bugs with different fixes, and conflating them wastes investigation time.

### Part B — How Airtap Implements This
Airtap is unusually well-instrumented for exactly this failure shape, which is worth knowing and
using directly rather than falling back on generic error-log searching. Every single step carries a
structured, mandatory reasoning trail (an observation of the current state, a review of what that
means, and a plan) *before* its actual chosen action — reading this is almost always the fastest way
to answer "why did it do that." Beyond that, a layered set of artifacts exists specifically for this:
a recorded history of every state the task moved through and why; lightweight checkpoint breadcrumbs
showing exactly where inside a given step the process was at any point; and a complete, always-on
capture of every single LLM call's exact input and output, for every step of every task — not
sampled, not opt-in for this one. The recommended order, from coarse to fine: state history first
(what happened, broadly), step breadcrumbs second (where inside a slow/stuck step things were), full
call capture third (exactly what the model saw and said), and a separate tracing view or aggregate
dashboards last (is this an isolated case or part of a trend).

### Part C — QA Perspective
- **What to validate**: that this layered debugging approach genuinely gets you to a root cause
  faster than ad hoc log searching — practice using it on real cases until it's your default
  instinct, not a fallback.
- **Possible bugs**: don't assume every "no error" case is a pure AI-quality issue — confirm first
  that there really is no recorded state-transition reason or device-reported failure code hiding the
  actual explanation; check the cheap, structured signals before assuming you need the deepest layer.
- **Logs to inspect**: in order — task state history, step-level trace breadcrumbs, full per-call
  model debug capture, then a separate tracing view/dashboards for pattern-level confirmation.
- **Edge cases to test**: deliberately construct a case where the correct diagnosis requires reading
  reasoning across *multiple* steps, not just the final one — the point where things went wrong is
  very often several steps before the visibly wrong outcome.
- **Likely follow-up questions**: "Walk me through exactly how you'd triage a specific 'the agent did
  the wrong thing' ticket, start to finish." "What's the difference between a reasoning failure and a
  grounding failure, and why does the distinction matter for who fixes it?"

---

## Q8. What are LoRA, QLoRA, and Distillation — and when would you reach for them instead of prompting or RAG?

### Part A — Generic AI Interview Answer
**LoRA (Low-Rank Adaptation)**: instead of fully retraining a model's billions of parameters (slow,
expensive, produces a full new copy of the model), you freeze the original model and train a small
set of additional "adapter" weights bolted on the side — changing under 1% of total parameters while
capturing most of the customization benefit. **QLoRA** adds quantization on top: the frozen base
model is loaded in a compressed form so the whole fine-tune can run on much smaller, cheaper hardware.
This is *the* answer to "how would you customize a model's behavior without retraining the whole
thing." **Distillation** is a different technique for a different goal: training a small "student"
model to mimic a large "teacher" model's behavior (or, for reasoning models specifically, its
reasoning traces) — trading a little accuracy for a lot of speed and cost, which is exactly the
justification for wanting a smaller, faster, cheaper model for something like on-device or
high-volume inference instead of calling a frontier model for every tiny decision. The decision
framework worth stating cleanly: prompting changes how you *ask*; RAG changes what the model *knows*;
fine-tuning (including LoRA/QLoRA) changes the model's *weights/behavior* directly; distillation
changes the model's *size/cost profile* while trying to preserve behavior. Reach for the cheapest
lever that actually addresses the real cause — wrong tone/format is a prompting problem, missing
facts is a RAG problem, and a deep, consistent, high-volume behavior change is where fine-tuning
finally earns its cost.

### Part B — How Airtap Implements This
None of LoRA, QLoRA, or true model distillation are used anywhere in Airtap — confirmed directly: no
training or fine-tuning infrastructure exists in the product at all; every model it calls is a stock,
off-the-shelf, already-trained model consumed via API. This is a legitimate, defensible design
choice worth explaining rather than a gap: Airtap steers behavior almost entirely through prompt
engineering (a detailed system prompt and rulebook) plus deliberate model *selection* for different
purposes — which is conceptually adjacent to what distillation tries to achieve, without actually
training anything. Specifically, lighter, cheaper, faster off-the-shelf models are assigned to
narrower jobs (hardware-constrained device types, generating a task title, deciding what's worth
remembering) while a stronger model is reserved for the main decision loop — achieving distillation's
practical goal (a cheap, fast model for a narrow job) through model selection rather than through
training a genuinely distilled model. This is a real, precise distinction worth being able to draw
directly: "adjacent in spirit, not the same technique."

### Part C — QA Perspective
- **What to validate**: N/A for fine-tuning/distillation-specific correctness, since neither is
  used — don't spend test effort here.
- **Possible bugs**: N/A directly, though the model-selection strategy that stands in for
  distillation's goal has its own, different test surface — see the Model Routing question in the
  intermediate document.
- **Logs to inspect**: N/A for this concept specifically.
- **Edge cases to test**: N/A as currently implemented.
- **Likely follow-up questions**: "If Airtap's product needs ever justified fine-tuning, what
  specific, narrow behavior would be the strongest candidate, and why?" "What would change about your
  test strategy the day a fine-tuned or distilled model was introduced into this product — what new
  regression risk would that add that doesn't exist today with stock models?"

---

## Q9. How would you design observability for a multi-vendor, multi-model AI agent system?

### Part A — Generic AI Interview Answer
A layered strategy, from coarse to fine, is the right shape: high-level state/outcome tracking (what
happened, at a glance, across many runs); step- or call-level tracing (where, within one run, did
things go right or wrong); complete, unsampled capture of raw model inputs/outputs for genuinely deep
debugging (you often need to see the *exact* prompt and *exact* response, not a summary); and
aggregate dashboards for trend detection across models, users, and time. For a genuinely multi-vendor
system specifically, normalize as much as possible into one consistent shape (token counts, latency,
cost, error types) so cross-vendor comparison is actually possible, while still preserving raw,
vendor-specific request/response data for the cases where normalization itself might be hiding a
vendor-specific bug. The mature framing worth stating directly: sampled telemetry is fine for spotting
trends, but at least one layer of your observability needs to be complete and unsampled, because a
sampled record can, by definition, simply be missing the one call you actually need to see.

### Part B — How Airtap Implements This
Airtap's observability stack is a close, real match for this generic shape. Task state history gives
the coarse view. Lightweight, named checkpoints logged throughout a single step give a step-level
trace. A dedicated tracing view (opt-in per call site — a known, real gap, since at least one call
type isn't wired into it) gives a visual, ordered per-task timeline of model calls. And critically,
the deepest, most complete layer is genuinely unsampled: every single LLM call across the entire
product — the main decision loop, memory generation, title generation, schedule parsing, evaluation
judging, all of it — has its exact vendor request and exact vendor response captured, always, not
sampled, and stored for later inspection. Aggregate dashboards then normalize across vendors for
per-model latency, failure rate, cost, and cache efficiency. The one confirmed weak point worth
naming honestly: general backend error tracking (as opposed to this LLM-call-specific capture) is
explicitly *sampled*, not complete — meaning the "always capture everything" property that makes this
observability stack strong specifically applies to LLM calls, not to every category of backend error
equally, and that distinction matters when deciding which tool to trust as your complete record for a
given kind of investigation.

### Part C — QA Perspective
- **What to validate**: that the "always-on, unsampled" claim for LLM call capture actually holds —
  spot-check that a call you know happened is actually retrievable, especially after any
  infrastructure change near this capture mechanism.
- **Possible bugs**: a newly-added LLM call site that forgets to wire itself into the tracing view
  (an easy, real, opt-in-by-design gap) — silently invisible in that one tool while still fully
  captured in the deeper, always-on layer, so knowing *which* tool has the gap matters.
- **Logs to inspect**: use the deepest layer (complete per-call capture) as the trustworthy baseline
  whenever a lighter-weight tool's absence of data is ambiguous — "not in the trace" is not the same
  as "didn't happen."
- **Edge cases to test**: a task that spans multiple different model vendors across its own steps (if
  reachable via a routing change mid-investigation) — confirm observability stays consistent and
  complete across that vendor switch, not just within one vendor's calls.
- **Likely follow-up questions**: "Why keep an opt-in tracing tool at all, if the deeper capture
  layer is already complete and unsampled?" "How would you design an alert that fires specifically
  when a new LLM call site ships without being wired into observability?"

---

## Q10. How would you test memory/context systems for both correctness and security?

### Part A — Generic AI Interview Answer
Memory testing is genuinely nasty because its bugs are stateful, delayed, and cross-session — a
classic hard category even in traditional QA, now applied to a system with no built-in error
signaling when it gets something wrong. Two priorities should come before everything else. First,
**cross-user isolation is a security test, not a quality test** — one user's memory surfacing for a
different user is a data breach, and should be tested with that severity and rigor, not treated as a
softer "quality" bug. Second, **stale-memory bugs are silent and delayed** — a write can look
completely fine at the time, and the failure only shows up sessions later when an outdated fact
resurfaces; that separation in time between cause and symptom is exactly the kind of bug traditional
test suites are worst at catching, which is precisely why it needs deliberate, structured testing
rather than being left to incidental discovery.

### Part B — How Airtap Implements This
Airtap's memory is scoped strictly per user and persists across every task that user runs — never
shared or pooled across accounts by any confirmed mechanism. It's implemented as plain, directly
readable text files rather than an opaque index, which is genuinely useful for testing: you can
simply read the actual stored content for a test account rather than needing specialized tooling. The
automatic memory-writer call is deliberately restricted to only two of several files (long-term facts
and today's short-term notes) — it cannot touch the user's core profile facts or the agent's own
persona configuration, both of which are user-edited directly instead. This is a real, meaningful
security boundary worth testing specifically: an attempt, via ordinary conversation, to get the
agent to "convince itself" into rewriting its own persona or the user's profile should fail, because
the write path for those files simply isn't reachable from the automatic memory-writing mechanism at
all. What's genuinely unconfirmed and worth treating as an open test question rather than an
assumption: the exact mechanics of how a stale or contradicted fact gets resolved when a new,
conflicting fact is stated later.

### Part C — QA Perspective
- **What to validate**: cross-user isolation first, always, treated with the rigor of an
  authorization test suite; recall of a fact across genuinely separate, unrelated tasks by the same
  user second.
- **Possible bugs**: a stale fact continuing to be used after a later correction (unconfirmed
  behavior — genuinely worth testing rather than assuming either way); the write-boundary protection
  around persona/profile files failing under a sufficiently persistent adversarial conversation.
- **Logs to inspect**: the actual stored memory content directly (it's plain text); the memory-writer
  call's own captured input/output (via the same complete LLM-call capture used everywhere else) to
  see exactly what it decided to keep and why.
- **Edge cases to test**: state a fact, then explicitly contradict it in a later task, and check
  which one wins; attempt to get the agent to alter its own persona/identity configuration through
  in-conversation pressure and confirm it doesn't persist; run two accounts with intentionally
  similar stated facts concurrently to probe for cross-contamination under load.
- **Likely follow-up questions**: "How would you build an automated, standing isolation-test suite
  for this rather than a one-time manual check?" "What's your recommended fix if you actually found a
  stale-memory bug — and how would you regression-test the fix?"

---

## Q11. Errors compound in multi-step agents — how does this change your testing strategy?

### Part A — Generic AI Interview Answer
A simple but genuinely important piece of arithmetic: if each step in a multi-step task is 95%
reliable, a 10-step task's overall reliability is roughly `0.95^10` ≈ 60%; a 20-step task drops to
around 36%. This one line explains most agent failures seen in production, and it means per-step
reliability that sounds impressively high in isolation can still produce a genuinely unreliable
end-to-end product once enough steps are chained together. The direct implication for testing: you
can't validate an agent by only testing short, simple tasks and assuming reliability holds at
length — task length itself is an independent risk axis that needs its own explicit test coverage,
separate from testing task *variety*. It also reframes what "improving reliability" even means: a
small, unglamorous improvement to per-step accuracy compounds into a much larger improvement in
long-task success rate, which is a genuinely strong, non-obvious argument for investing in
step-level quality (grounding accuracy, reasoning quality) over chasing flashier, task-level fixes.

### Part B — How Airtap Implements This
This math applies directly and literally to Airtap's own architecture: a task is a chain of
independently-executed steps, and a long, multi-app, many-step task is genuinely more exposed to
compounding failure than a short one, exactly as the generic math predicts. Airtap has real,
partial mitigations for this baked into its design, worth naming specifically: context compaction
keeps a long task's growing history from degrading model performance as length increases; the
agent's own operating instructions include explicit loop-avoidance and no-progress-detection rules
aimed at catching and correcting a failing pattern *before* it consumes many additional steps; and a
hard step-count ceiling exists as a final backstop against a task that never resolves. None of these
change the underlying compounding-probability math — they're mitigations at the margins (catching
drift early, capping the worst case), not a fix for the fact that more steps genuinely means more
opportunities to fail.

### Part C — QA Perspective
- **What to validate**: reliability specifically as a function of task *length* — deliberately test
  short, medium, and long/multi-app tasks as three distinct categories, not one undifferentiated
  "does the agent work" bucket, since success rate should be expected to differ meaningfully across
  them.
- **Possible bugs**: a per-step accuracy regression that looks negligible in isolated,
  single-step testing but produces a disproportionately large drop in long-task success once
  compounded — this is exactly the kind of regression that a test suite focused only on short tasks
  would miss entirely.
- **Logs to inspect**: step count and per-step outcome across a sample of both short and long tasks,
  to actually measure whether reliability degrades with length the way the math predicts, and by how
  much.
- **Edge cases to test**: deliberately construct a long, multi-app, many-step task specifically to
  exercise compaction, loop-avoidance, and step-ceiling mechanisms together, not just to test
  "does a long task eventually finish."
- **Likely follow-up questions**: "If you improved per-step accuracy from 95% to 98%, roughly how
  much would that change 20-step task reliability, and why does that matter for prioritization?"
  "Which mitigation available in this product — compaction, loop-avoidance, or the step ceiling — do
  you think has the biggest effect on long-task reliability, and how would you measure that?"

---

## Q12. Airtap deliberately avoids RAG, multi-agent systems, and MCP — walk through why each choice makes sense, and when you'd revisit it.

### Part A — Generic AI Interview Answer
A strong system-design answer isn't just knowing a technique exists — it's knowing when *not* to
reach for it, and being able to name the specific condition under which that judgment would flip.
Three general principles apply across all three of these: RAG and vector search earn their
complexity at a real scale threshold (roughly, the roadmap's own commonly cited "under ten thousand
chunks, you probably don't need one"), not automatically for any AI product; multi-agent
architectures earn their cost only when a task has genuinely *separable* sub-jobs benefiting from
specialization or independent review, and are otherwise pure overhead — more latency, more cost, more
places for information to get lost between handoffs; and a shared, standardized tool protocol like
MCP earns its value specifically through *interoperability* across many different agents and tools,
which matters far less for a product with one agent and a small, fixed, well-known tool set of its
own.

### Part B — How Airtap Implements This
All three "not used" findings are real, directly confirmed, and each has a specific, defensible
reason rooted in this product's actual shape, not just an oversight:
- **No RAG/vector database**: per-user memory here is a small, bounded set of plain-text files —
  nowhere near the scale where retrieval infrastructure would out-perform simply reading everything
  directly into the prompt. Revisit this the moment memory size genuinely starts crowding out task
  context in the prompt — that's the concrete, measurable signal, not a fixed calendar date.
- **No multi-agent architecture**: every step of this product's core task needs the *same* context
  (the current screen) and the *same* capability (decide one action) — there's no natural
  specialist-role split the way a research-then-write-then-fact-check pipeline has. Revisit this if a
  genuinely separable, independently-valuable role emerges — a live, pre-execution reviewer
  specifically catching risky actions before they execute (tying directly to the open risk-tiering
  gap discussed earlier) is the most plausible concrete candidate.
- **No MCP for the agent's own tools**: the product has one agent and a small, well-known, internally
  owned set of tools — MCP's interoperability benefit doesn't have much to attach to here. Revisit
  this if Airtap ever needs to expose its own tools to *other* agents/products, or needs to rapidly
  integrate many external, independently-maintained tool providers — that's the scenario where a
  shared standard starts paying for itself.

### Part C — QA Perspective
- **What to validate**: that each "not used" status stays true over time — these are genuinely
  scale/shape-dependent judgment calls, not permanent facts, so periodically re-confirming them
  (rather than assuming forever) is itself a reasonable, lightweight ongoing check.
- **Possible bugs**: N/A directly for any of the three technologies themselves, since none are in
  use — but see each technique's own Part B above for the *actual* applicable risk in its place
  (context-window pressure from memory growth; the missing live-reviewer gap; nothing currently
  applicable for MCP).
- **Logs to inspect**: memory file size trends over time per account (the leading indicator for the
  RAG threshold specifically).
- **Edge cases to test**: N/A for the absent technologies themselves; the relevant edge case is a
  very long-tenured test account's memory size, as an early-warning proxy for the RAG-threshold
  question.
- **Likely follow-up questions**: "Which of these three 'not yet' decisions do you think is closest
  to flipping, and why?" "If you had to introduce exactly one of these three tomorrow, which would
  you pick, and what's the smallest version of it you'd ship first?"

---

## Q13. System design: design (or critique) a mobile GUI agent product's architecture end-to-end.

### Part A — Generic AI Interview Answer
A clean, complete shape to draw for this class of product, going from a natural-language request to
a finished action:

```text
User Prompt
   ↓
LLM Planner (parse intent, break into steps)
   ↓
Screen State Capture (screenshot + accessibility tree)
   ↓
Vision-Language Model (screen understanding + grounding)
   ↓
Action Decision (coordinate target or element target)
   ↓
Action Executor (automation layer — ADB / Accessibility API / dedicated hardware)
   ↓
Device / App State Change
   ↓
Verification (did the action produce the expected state?)
   ↓
Loop back to Planner (multi-step task), or return Final Response
```
The two middle-to-late stages — **capture** and **verify** — are where real systems in this category
actually break most often, not the glamorous "decide" step everyone focuses on first. A stale
screenshot (captured mid-animation, mid-load, or with a keyboard covering the target) produces
brilliant reasoning about a screen that no longer exists; a failed action nobody verifies means every
subsequent step reasons about a state that was never actually reached. If asked to say one thing in
this kind of interview, that's the one worth saying.

### Part B — How Airtap Implements This
Airtap is a genuine, close, real-world implementation of this exact shape, with a few specific,
defensible departures worth naming precisely rather than glossing over. There's no separate "Planner"
*module* — planning is one possible tool call inside the same single decision loop that also decides
individual actions, not a distinct upstream phase handing off to a different component. Screen
capture is conditional, not automatic on every step — only refetched after an action that could
plausibly have changed the screen, an efficiency trade-off. The automation layer is confirmed
Accessibility Service and/or a physical HID dongle, deliberately not ADB, for reasons covered
earlier in this document. And "Verification" isn't one clean stage — it's genuinely three different
things layered together: deterministic schema validation of the model's own output, a deterministic,
specific status reported back by the device itself, and — critically, the layer with the least
independent backup — the model's own single-pass self-verification at the *start* of the next loop
iteration, when it looks at the new screenshot and is instructed to treat it as unverified until key
details match. There is no separate, independent reflection/critique call double-checking that
third layer.

### Part C — QA Perspective
- **What to validate**: the "capture and verify" claim directly, on this exact product — deliberately
  construct scenarios where the screen changes mid-capture (an animation, a popup) and where an
  action plausibly fails silently, and confirm what actually happens at each layer.
- **Possible bugs**: the third verification layer (single-pass, model-driven self-verification) has
  no independent backup if it misses something — this is the most theoretically exposed point in the
  entire architecture and deserves proportionally the deepest test investment.
- **Logs to inspect**: for a suspected capture/verify failure specifically — the exact screenshot
  used for a step's decision (was it actually current?), and the device's own deterministic
  execution-status report (did it claim success even if the outcome was wrong?).
- **Edge cases to test**: an action fired at the exact moment a screen is mid-transition; a device
  status report of "success" paired with a screenshot showing an unexpected resulting state, to
  confirm the *next* step's reasoning actually catches the mismatch rather than proceeding blindly.
- **Likely follow-up questions**: "If you had to add one new component to this architecture to make
  it meaningfully more reliable, what would it be and why — and what would it cost?" (A strong,
  defensible answer: an independent, code-level state-verification check after every action —
  distinct from the model's own single-pass self-verification — closing exactly the gap identified
  above, at the cost of one extra step/latency per action.) "How would you prioritize fixing capture
  reliability versus verification reliability if you could only invest in one first?"

---

This closes Phase 4 and the full interview-preparation arc: [13](13_interview_questions_beginner.md)
gave you the vocabulary, [14](14_interview_questions_intermediate.md) gave you the architecture,
and this document gave you the judgment calls — the part most candidates in this space can't
actually back up with a real system.
