# 11 — Observability

*Phase 3 · Document 3 of 4. Same 15 subsystems, same order as
[09](09_qa_testing_strategy.md)/[10](10_failure_modes.md). This document answers one question per
subsystem: where do you actually look?*

---

## The general toolkit, in one place

Before the per-subsystem breakdown, five tools/views recur constantly across almost every
subsystem below. Knowing this short list well is worth more than memorizing every row in this
document:

1. **Task state history** — the recorded sequence of states a task moved through, with reasons and
   timing. Your starting point for almost any single-task investigation: it tells you *what the
   system itself believes happened*, before you go looking anywhere else.
2. **Step-level trace breadcrumbs** — lightweight checkpoints logged throughout a single step's
   execution. Use this to find *where inside a slow or stuck step* things stopped progressing.
3. **Full per-call model debug capture** — the complete, always-on record of every single LLM call
   a task made: exact prompt sent, exact response received, cost, tokens. This is the deepest, most
   complete layer and usually the fastest way to answer "why did the agent decide that."
4. **A tracing/timeline view (Langfuse)** — a similar per-task, ordered view of model calls, useful
   for a more visual read of a task's LLM-call sequence. Opt-in per call site — a small number of
   call types (notably the UI status-label generation) are known not to appear here, so a "missing"
   call in this view isn't automatically a bug.
5. **Internal dashboards** — aggregate views: per-model latency/cost/failure rate, funnel/product
   metrics, task-analysis browsing. Use these to answer "is this a one-off or a trend," after
   you already understand one specific case via tools 1–4.

**A reliable default order**: state history first (what happened), step trace second (where it got
stuck), full call capture third (why the model decided what it decided), tracing/dashboards last
(is this isolated or systemic).

---

## Subsystem 1 — Client Applications

**Observability Available**: browser/app-level error tracking (separate from and more complete than
the backend's own error tracking); a client-side degraded-connection indicator that's directly
visible in the UI itself.

**Logs/Signals to Inspect**: the client's own error-monitoring tool, filtered to the relevant
account/session — failed API calls surface here as typed, per-feature errors (e.g., a
receiver-pairing failure looks different from a dashboard-load failure), which is more informative
than a generic network-failure log line.

**Metrics That Matter**: task-creation success rate from the client's point of view, realtime
reconnect frequency, and time-to-first-update after a task is created (a proxy for whether the
realtime layer is healthy).

---

## Subsystem 2 — Authentication & Account Access

**Observability Available**: request-level status codes and structured rejection reasons
(distinct codes for expired token, waitlisted, banned, missing permission).

**Logs/Signals to Inspect**: the specific rejection reason on a failed request is almost always
sufficient on its own — don't stop at "it returned an error," read *which* structured reason it
returned, since expired-token, waitlisted, and missing-permission are three different problems with
three different fixes.

**Metrics That Matter**: auth failure rate by reason code (a spike specifically in "missing
permission" after a release is a strong signal of an accidental permission regression, distinct
from a general auth outage).

---

## Subsystem 3 — Task Lifecycle & State Management

**Observability Available**: complete state-transition history per task, including the reason for
each transition and how many agent steps had occurred at that point.

**Logs/Signals to Inspect**: the task's state history first, always. A task with no transitions
recorded for an extended period, with the last known state being an active/executing one, is the
signature of an orphaned background job (see [10 §3](10_failure_modes.md)) — this is visible
directly in the state history without needing any other tool.

**Metrics That Matter**: distribution of tasks across terminal states (completed vs. failed vs.
cancelled vs. stopped) over time — a shift in this distribution after a release is often the
earliest aggregate signal of a regression anywhere upstream, before any single-task investigation
even starts.

---

## Subsystem 4 — Agent Decision Loop

**Observability Available**: this subsystem has the richest observability in the entire product —
the reasoning fields on every single step (a direct, human-readable statement of what the model
believed and why), plus everything in the general toolkit above.

**Logs/Signals to Inspect**: the per-step reasoning fields are the single most valuable artifact
for this subsystem — read them before forming a hypothesis, not after. The full per-call model
debug capture is the next layer down when the reasoning field alone doesn't explain the behavior
(e.g., you want to see exactly what the screenshot looked like at that moment, or the literal model
output before any post-processing).

**Metrics That Matter**: step count per task (a rising average is an efficiency/looping concern
even when tasks still ultimately succeed), and — via the Evaluation Framework specifically — pass
rate trends on the curated dataset over time as changes ship.

---

## Subsystem 5 — LLM Provider Layer

**Observability Available**: per-call token/cost/latency stats (normalized across every vendor), an
aggregate per-model dashboard (latency, p95, failure rate, stop-reason breakdown, cost, cache
efficiency, top spenders), and the raw vendor request/response pair for every call via the full
debug capture.

**Logs/Signals to Inspect**: the raw vendor request/response is the ground truth when a bug is
suspected to be vendor-specific — it shows exactly what was sent and returned, bypassing any
possible misinterpretation introduced by normalization.

**Metrics That Matter**: per-model failure rate and stop-reason breakdown (a rising rate of hitting
a length/token limit, for instance, is a distinct signal from a rising rate of outright errors);
cache efficiency (a silent drop here is a pure cost regression with no correctness symptom at all,
so it needs to be watched proactively, not discovered from a complaint).

---

## Subsystem 6 — Memory & Context

**Observability Available**: the memory-write LLM call is captured like any other call (full debug
capture, tracing); the memory content itself is directly readable (it's plain text, not an opaque
embedding or index).

**Logs/Signals to Inspect**: because memory is plain text, the most direct debugging technique
available anywhere in this document is simply reading the actual stored memory content for the
account in question — no special tooling required, just direct inspection.

**Metrics That Matter**: no dedicated dashboard metric is expected for memory quality specifically
— this is a subsystem where proactive, deliberate testing (recall tests, isolation tests) matters
more than passive metric-watching, precisely because a memory failure produces no error signal on
its own.

---

## Subsystem 7 — Tool Selection & Device Command Routing

**Observability Available**: the chosen tool name and its arguments are recorded per step (visible
in the reasoning/tool-call record); the tool's result (success or specific failure) is recorded
alongside it.

**Logs/Signals to Inspect**: compare the recorded tool call directly against the resulting device
state (the next step's screenshot) — this side-by-side comparison is the fastest way to confirm
whether a wrong outcome traces to argument-level error versus execution-level failure.

**Metrics That Matter**: tool-call failure rate by tool name (a spike isolated to one specific tool
is a strong, specific signal); grounding accuracy specifically, if tracked separately from overall
task success (see [09](09_qa_testing_strategy.md) for why this should be measured as its own
metric, not buried inside task success rate).

---

## Subsystem 8 — Android Device Automation

**Observability Available**: device-reported status on every command (specific failure reasons,
not generic); receiver app version and connection state are both queryable.

**Logs/Signals to Inspect**: the specific device-reported failure reason on a failed command is
almost always immediately actionable on its own. When the signal is a generic timeout instead of a
specific reason, that itself is informative — it means the device didn't respond at all, which
points toward the device being asleep, killed, or disconnected, rather than a normal
in-app failure.

**Metrics That Matter**: command round-trip latency (device responsiveness), receiver-wake success
rate for backgrounded devices, and failure-reason distribution over time (a rising share of
"version too old" failures, for instance, flags a live-config/rollout mismatch immediately).

---

## Subsystem 9 — iOS Device Automation

**Observability Available**: broadcast/session running-state is directly queryable, including the
boot-time staleness check; device-reported failure reasons parallel Android's.

**Logs/Signals to Inspect**: check the broadcast running-state first for almost any iOS device
issue — so much else on this platform depends on it that it's the highest-information single signal
available.

**Metrics That Matter**: broadcast session uptime/stability (how often does it drop unexpectedly
versus end via a normal user action), and command execution success rate specifically while a
broadcast is confirmed running (isolates device-automation issues from broadcast-availability
issues).

---

## Subsystem 10 — HID Dongle Hardware

**Observability Available**: connection state is tracked on-device (the receiver app's own internal
state machine — scanning/connecting/connected/disconnected/updating-firmware); this state is the
most direct signal available, though it requires checking the device/app directly rather than a
remote dashboard.

**Logs/Signals to Inspect**: the receiver app's own displayed connection status is the fastest,
most direct signal for this hardware layer — remote/cloud-side logs can only tell you "the device
didn't respond," not *why*, so for genuinely physical failures, check the device itself before
digging through cloud logs.

**Metrics That Matter**: reconnect frequency and reconnect success rate (a rising reconnect rate for
a specific dongle/device pair, isolated from others, points at that specific piece of hardware);
firmware version distribution across the fleet (a large population still on old firmware is a
forward-looking risk if a version-floor requirement is ever raised).

---

## Subsystem 11 — Cloud Phone

**Observability Available**: session lifecycle events (boot stage progression is reported), WebRTC
signaling status distinct from the underlying command-execution status.

**Logs/Signals to Inspect**: separate the signaling status from the task's own execution status —
these are reported and can be checked independently, and doing so is exactly how you tell a
"can't see it" problem from an "isn't working" problem (see [10 §11](10_failure_modes.md)).

**Metrics That Matter**: session boot-time distribution (informs how much "warm-up" delay is
realistically needed before starting a task), WebRTC connection success rate, and idle-timeout
disconnect frequency versus session count (should track expected usage patterns, not spike
unexpectedly).

---

## Subsystem 12 — Routines & Scheduling

**Observability Available**: each routine's configured schedule is directly inspectable and
comparable against what the user described; execution history per routine is recorded the same way
a normal task's history is (since a routine run *is* a task, once started).

**Logs/Signals to Inspect**: compare the routine's actual stored schedule configuration against the
user's original natural-language description directly — this single comparison resolves most
"routine ran at the wrong time" reports without needing to look at execution logs at all.

**Metrics That Matter**: routine auto-disable rate (a rising rate of routines being auto-disabled
for repeated failure is an early warning worth tracking in aggregate, not just case by case), and
schedule-adherence (actual fire time vs. nominal scheduled time, to distinguish expected jitter from
a real delay problem).

---

## Subsystem 13 — Alternate Intake Channels

**Observability Available**: message linking status is queryable per account; delivery
confirmation may be available on the channel provider's own side, separate from internal logs.

**Logs/Signals to Inspect**: for a "nothing happened" report specifically, check the channel
provider's own delivery confirmation before internal logs — this document set has already flagged
that at least one of these channels is deliberately built to report success even on an internal
processing failure, so internal logs may show nothing informative at all for that specific failure
shape.

**Metrics That Matter**: per-channel task-creation success rate and reply-delivery rate,
specifically tracked separately per channel (Telegram vs. the texting integration) since they have
independent failure surfaces despite sharing the same underlying task engine.

---

## Subsystem 14 — Evaluation Framework

**Observability Available**: every run produces a report with per-case results and aggregate
cost/latency/token stats; individual case results include the judge's cited evidence, not just a
pass/fail verdict.

**Logs/Signals to Inspect**: read the judge's cited evidence on a specific failing case, not just
its pass/fail verdict — this is what lets you distinguish "the agent was actually wrong" from "the
judge graded it unfairly," which is a critical distinction for trusting or discounting any given
result.

**Metrics That Matter**: pass rate trend over time (run to run, tied to specific prompt/model
changes if possible), and — since this framework has no automatic trigger — the simple presence or
absence of a recent run at all is itself a meaningful "metric" to track as a process signal.

---

## Subsystem 15 — Background Jobs & Queue

**Observability Available**: job-level success/failure is implicit in the task/routine state it
was responsible for updating, since there's no dedicated per-job dashboard called out separately
from the features that depend on it.

**Logs/Signals to Inspect**: when several unrelated background-dependent symptoms cluster together
in time (see [10 §15](10_failure_modes.md)), that clustering *is* the signal — treat simultaneous,
otherwise-unrelated background-feature complaints as evidence pointing at shared queue
infrastructure, not as several independent bugs to investigate one by one.

**Metrics That Matter**: queue depth/backlog size over time, and job latency (time from enqueue to
execution start) — both are the earliest indicators of the shared-resource contention risk called
out in [09](09_qa_testing_strategy.md), well before it becomes visible as a specific feature
complaint.

---

## Known blind spots — what NOT to over-trust

Worth internalizing early, so you don't build false confidence in a signal that has a known gap:

- **Error tracking on the backend is sampled, not complete.** A large share of backend errors never
  reach the error-tracking tool at all — treat it as a *sample*, useful for spotting trends, not as
  the authoritative record of every backend error. Structured application logs are the complete
  record.
- **Tracing (Langfuse) is opt-in per call site, not universal.** At least one known call type (the
  UI status-label generation) doesn't appear there. A "missing" call in a trace isn't automatically
  evidence that call didn't happen — check the full per-call debug capture (which *is* always-on)
  before concluding something is untraced entirely.
- **Log messages don't reliably self-identify which module produced them**, despite a
  module-scoped logging pattern existing throughout the codebase — don't expect to filter logs by
  module name; correlate by task ID (or request ID for HTTP-scoped issues) instead.
- **A crash can lose the most recent window of batched log output** before it's flushed to
  long-term storage — an incomplete-looking log right at the end of a crash timeline isn't
  necessarily missing evidence of what happened; it may simply be lost in the batching window.
- **The Evaluation Framework has no automatic trigger.** Its absence from a given change's history
  is not visible as an alert anywhere — you have to actively check whether it ran, not wait to be
  told it didn't.
- **No confirmed mitigation exists for known judge biases** (favoring longer answers, favoring
  answer order in a comparison). Treat eval pass/fail results as informative, not infallible,
  especially near a close call.

---
**Next:** [12_debugging_checklist.md](12_debugging_checklist.md) — turning all of the above into step-by-step runbooks for the symptoms you'll actually see.
