# 10 — Failure Modes

*Phase 3 · Document 2 of 4. Same 15 subsystems as [09_qa_testing_strategy.md](09_qa_testing_strategy.md),
same order. This document catalogs what actually breaks, how the failure shows up as it travels
downstream, and how to tell which subsystem is really at fault when a symptom reaches you.*

---

## Three shapes of failure, worth telling apart before anything else

Every failure in this document falls into one of three shapes, and the shape determines how you
investigate it:

- **[Coded]** — a failure the system anticipated and gives a specific, named reason for (a status
  code, a typed error, a distinct UI state). These fail loudly and are the easiest category to
  triage: the reason given is usually trustworthy.
- **[Infra]** — a transient, environmental failure (a network blip, a rate limit, a momentarily
  unavailable dependency). These are expected to self-resolve within a bounded retry window; a
  failure here is only a bug if it doesn't resolve within that window, or resolves in a way that
  corrupts state.
- **[AI-quality]** — the system worked exactly as coded, and the *decision* was simply wrong. There
  is no error, no exception, no failed status — just an agent that took a plausible-looking wrong
  action, or gave a wrong answer with full confidence. This is the shape with no classical-QA
  analogue and the one most likely to go unnoticed by any automated check that only watches for
  errors.

Every subsystem below tags its failures with one of these three so you know, at a glance, whether
you're looking for a log line or a behavioral pattern.

---

## Subsystem 1 — Client Applications

**Possible Failures**:
- [Coded] Realtime connection degrades to a cached/stale state; UI shows a staleness indicator.
- [Coded] Backend version mismatch after a deploy — a stale open tab's calls are rejected.
- [Infra] Attachment upload fails on a flaky connection.
- [AI-quality] N/A — this subsystem has no AI decision-making of its own.

**How It Propagates**: a realtime disconnect doesn't fail the task — it fails the *user's view* of
the task. The task keeps running normally server-side; the client is simply not being told about
new steps until reconnection. Symptom: "the task looks frozen" while the underlying task is
actually progressing or has already finished.

**How to Isolate**: check whether the task's actual state (via a fresh page load / re-fetch, or an
admin/internal view) has moved on even though the open tab hasn't. If the underlying state *has*
progressed, this is a client-display issue, not a task-engine issue — stop investigating the agent
loop and look at the client's realtime layer instead.

---

## Subsystem 2 — Authentication & Account Access

**Possible Failures**:
- [Coded] Expired/invalid token → rejected request.
- [Coded] Waitlisted/banned account → blocked regardless of token validity.
- [Coded] Missing permission on an internal route → not-found-style rejection (deliberately not a
  403, so it doesn't confirm the resource exists).
- [Infra] The external auth service is slow or briefly unavailable.

**How It Propagates**: an auth failure blocks the request *before* it ever reaches task/agent
logic — it never gets the chance to become an agent-loop or device problem. Symptom: every action
for that account fails identically and immediately, regardless of what the user is trying to do —
a strong signal this is an auth-layer issue, not a feature-specific one.

**How to Isolate**: if literally everything fails identically for one account, but works for
another account in the same environment, this is almost always Subsystem 2, not whatever feature
the user happened to be using when they noticed. Check admission state first — it's the single most
common cause of "nothing works for this new test account."

---

## Subsystem 3 — Task Lifecycle & State Management

**Possible Failures**:
- [Coded] A task ends in an unexpected terminal state given what actually happened.
- [Coded] A second task doesn't queue correctly behind an active one (or queues when it shouldn't).
- [Infra] A worker process restarts mid-step, orphaning that step's job.
- [AI-quality] N/A directly, though this subsystem records the AI-quality failures that originate
  elsewhere.

**How It Propagates**: this subsystem is the *record* other subsystems report into — a failure that
originates in the agent loop, a tool, or a device shows up here as a specific terminal state and
reason code. A genuinely orphaned job (Infra) is the one failure that originates *in* this
subsystem: nothing reports an error, the task simply stops advancing, and — because the loop is a
chain of jobs, not an in-memory process — nothing notices for hours, not minutes.

**How to Isolate**: read the task's own recorded state history first, always — it tells you what
the system itself believes happened, in what order, which is usually enough to point you at exactly
one other subsystem to investigate next rather than guessing. A task showing no state change at all
for an extended period, with no error recorded anywhere, is the signature of an orphaned job — this
is the one case where the "record" itself has gone silent rather than reporting something else's
failure.

---

## Subsystem 4 — Agent Decision Loop

**Possible Failures**:
- [Coded] A malformed tool call exhausts its one corrective retry and fails the task.
- [Infra] The device-context fetch (screenshot/UI dump) fails or times out.
- [AI-quality] The agent reasons correctly but chooses the wrong action (a downstream, Subsystem
  7/8 grounding issue — see there).
- [AI-quality] The agent reasons *incorrectly* — misreads the screen, misunderstands the task,
  or repeats an unproductive action pattern despite loop-avoidance instructions.
- [AI-quality] The agent completes the task but the final answer is wrong, incomplete, or not
  actually grounded in what it observed.
- [AI-quality] The agent fails to recognize it needs to ask for clarification or hand off to the
  user, and proceeds on a wrong assumption instead.

**How It Propagates**: this is the subsystem where a failure most often does **not** look like a
failure at all. A wrong decision here doesn't throw an error — it produces a real tool call that
executes normally at every layer below it. The task can complete in a `COMPLETED` state, with no
error anywhere in the system, while having done the wrong thing entirely. This is the core reason
"the task finished without error" is not sufficient evidence that the task succeeded.

**How to Isolate**: this is the one subsystem where isolating the failure means reading the
reasoning trail, not searching for an error. First separate *reasoning* failures from *grounding*
failures: did the stated reasoning correctly describe the screen and correctly conclude what should
happen next (in which case the failure is downstream — the action execution, Subsystem 7/8), or was
the reasoning itself already wrong (in which case it's genuinely this subsystem)? These have
different owners and different fixes; conflating them is the most common triage mistake for this
class of issue.

---

## Subsystem 5 — LLM Provider Layer

**Possible Failures**:
- [Coded] A malformed/invalid structured output from the model, caught by schema validation.
- [Infra] Rate limiting, timeout, or momentary model unavailability from the vendor.
- [Infra] A vendor-specific feature gap (e.g., a capability that works on one vendor but not
  another) surfacing as an unexpected failure only on that vendor.
- [AI-quality] N/A directly — this layer's own failures are transport/format failures, not decision
  quality (decision quality is Subsystem 4).

**How It Propagates**: an Infra-shaped failure here retries automatically within a bounded window
and, if it resolves, is invisible to the user beyond added latency. If the window is exhausted, it
surfaces as a task failure with an infrastructure-related reason — distinguishable from an
AI-quality failure because there IS an explicit reason recorded, not just a wrong-but-successful
outcome.

**How to Isolate**: check whether the specific failing case reproduces only on one particular
vendor/model configuration. If yes, this is very likely Subsystem 5 (a vendor-specific gap), not a
generic prompt or agent-logic problem — and the fix path is different (an adapter-level gap, not a
prompt change). A known, worth-remembering edge: a cloud-phone session that isn't warmed up yet has
been observed to fail immediately rather than benefit from the same automatic retry other
infrastructure errors get — don't assume every infra-shaped failure retries the same way.

---

## Subsystem 6 — Memory & Context

**Possible Failures**:
- [Coded] N/A — memory read/write itself doesn't have a rich set of named failure codes; it either
  works or the omission is silent.
- [AI-quality] A relevant fact isn't recalled when it should be.
- [AI-quality] A stale or contradicted fact is used instead of the current, correct one.
- [Coded/Security] Cross-user memory leakage — a different class of severity entirely (a data
  breach shape, not a quality shape).
- [Infra] Context compaction fails to preserve something the task still needed.

**How It Propagates**: a memory failure doesn't produce an error anywhere — it produces a task that
proceeds *normally*, just with wrong or missing context baked into its very first decision. Every
downstream step then looks locally reasonable, because each step is reasoning correctly from what
it was given — the actual defect is upstream, in what was injected before reasoning even started.

**How to Isolate**: if a task's behavior only makes sense assuming it didn't know something it
should have known (or knew something it shouldn't), check what was actually injected into that
task's starting context before assuming the reasoning itself is at fault — this is a "wrong input,
correct processing" failure shape, and no amount of scrutinizing the decision logic downstream will
explain it.

---

## Subsystem 7 — Tool Selection & Device Command Routing

**Possible Failures**:
- [Coded] An unregistered/unknown tool call is rejected explicitly.
- [Coded] A tool offered to the model that its current receiver type can't actually execute (a
  filtering-list bug).
- [AI-quality] The right tool is chosen but filled with subtly wrong arguments.
- [AI-quality] A tool executes and returns a failure, but the agent proceeds as if it succeeded.
- [Infra] The command reaches the wrong transport (cloud vs. device) due to a receiver-type
  resolution issue.

**How It Propagates**: a wrong-argument failure (grounding, most visibly — a tap that lands on the
wrong coordinate) propagates as an unexpected screen state on the *next* perceive step. Whether it
gets caught depends entirely on Subsystem 4's self-verification working — if it does, the task
takes an extra recovery step or two (visible as inefficiency); if it doesn't, the wrong path
compounds silently.

**How to Isolate**: the deciding question is "was the tool call itself wrong (name or arguments),
or did a *correctly chosen* tool call fail to produce the intended effect on the device?" The first
is this subsystem or Subsystem 4; the second points at Subsystem 8/9/10 (the device/hardware layer
actually executing it). Compare the tool call as recorded against the resulting device state to
answer this directly rather than guessing from the final symptom alone.

---

## Subsystem 8 — Android Device Automation

**Possible Failures**:
- [Coded] Screen locked, accessibility permission missing, receiver paused, receiver unlinked,
  receiver version too old — all specific, distinguishable, device-reported reasons.
- [Infra] The device is asleep/backgrounded and slow to wake.
- [Infra] OS-level background kill (OEM battery optimization) stops the receiver process entirely.
- [Coded] Screenshot capture fails due to missing/revoked capture permission.

**How It Propagates**: most of this subsystem's failures are the "good" kind — they fail loudly
with a specific, named reason that travels cleanly up to the task's failure reason. The genuinely
hard-to-trace case is an OS-level background kill: nothing "fails" in the normal sense; the device
simply stops responding to commands entirely, which looks identical, from the backend's point of
view, to the device being asleep or out of network range — the distinction (dead process vs. just
quiet) isn't observable from the cloud side at all.

**How to Isolate**: a *specific* reported reason (locked, permission, paused, version) needs no
further isolation — it's already telling you exactly what happened; go fix or reproduce that
specific state. A *generic* timeout/no-response, by contrast, requires checking the device directly
(is the app still running? Was it recently killed by the OS?) since the backend genuinely cannot
distinguish "asleep" from "dead" from "out of range" on its own.

---

## Subsystem 9 — iOS Device Automation

**Possible Failures**:
- [Coded] Screen broadcast not running (screen-capture equivalent of Android's permission failure).
- [Coded] AssistiveTouch off, detected via a failed self-test tap at pairing time.
- [Infra] The background command-execution process (tied to the screen broadcast) is memory-killed
  by the OS.
- [Coded] A stale "broadcast still running" state surviving a phone reboot, later self-corrected via
  a boot-time check.
- [Infra] The silent-audio background-survival mechanism is interrupted (a phone call, another
  app taking audio focus).

**How It Propagates**: because the always-running command loop lives inside the same process as
screen capture, a failure of one is very often a failure of both simultaneously — losing screen
capture on iOS tends to mean losing command execution too, unlike Android where accessibility input
and screen capture are more independent. Symptom: an iOS device that "goes quiet" tends to go
completely quiet (no new screenshots AND no command execution), rather than degrading one at a
time.

**How to Isolate**: check the broadcast/session running-state first — on iOS, it's usually the
single most informative signal, since so much else depends on it. If the broadcast reports as
stopped when the user believes it should be running, check specifically whether the phone was
recently rebooted (the known stale-state scenario) before assuming a new, different bug.

---

## Subsystem 10 — HID Dongle Hardware

**Possible Failures**:
- [Infra] BLE out of range, causing disconnect.
- [Infra] Dead or critically low dongle battery.
- [Coded] Firmware version mismatch, detected and (usually) auto-remediated via an update flow.
- [Infra] An interrupted firmware update leaving the dongle in a bootloader-only, pre-recovery
  state.
- [Infra] A loose or unplugged USB connection to the host device.

**How It Propagates**: every failure at this layer propagates upward as a device-command failure at
Subsystem 8/9 — the backend and the on-device app both see "the command didn't reach the device" or
"no response," without necessarily being able to tell BLE-range from dead-battery from
unplugged-USB apart from the symptom alone. This is the layer where the failure and the visible
symptom are most separated: the user just sees "the task failed" or "nothing is happening," with no
indication at all that the actual cause is a piece of hardware on a desk.

**How to Isolate**: this is the one subsystem where isolation is physical, not logical — check the
dongle itself (connection lights/status if available, physical BLE range, USB seating, battery)
directly rather than trying to infer the cause from logs alone. If a device-command failure
reproduces consistently for one specific physical dongle/device pair but not others in the same
environment, treat it as a hardware issue first, a software issue second.

---

## Subsystem 11 — Cloud Phone

**Possible Failures**:
- [Infra] Session not yet warmed up when a command/task starts.
- [Infra] WebRTC negotiation failure (no video, or video that never connects).
- [Coded] Idle timeout disconnect after the documented inactivity window.
- [Infra] The external VM-management dependency itself degrades or is unavailable.

**How It Propagates**: a WebRTC/session failure is purely a **live-view** problem when it's on the
signaling side — the underlying cloud device and the task driving it can continue working correctly
even if the user's browser never successfully shows video. Conversely, a session that genuinely
never finished booting fails at the command layer directly, which is a different, task-blocking
failure, not just a viewing inconvenience.

**How to Isolate**: separate "can I see it" from "is it working" as two independent questions —
they can fail independently. If the task itself is progressing (new steps, screenshots appearing in
the thread) but the live video view is broken, this is a signaling/view-layer issue, not a
task-execution one, and should be triaged and reported as such rather than as "the cloud phone is
broken."

---

## Subsystem 12 — Routines & Scheduling

**Possible Failures**:
- [Coded] Invalid or ambiguous natural-language schedule input rejected explicitly.
- [Infra] Scheduling jitter causing a routine to fire later than its exact nominal time (expected,
  bounded, not a bug within the documented window).
- [Coded] A routine auto-disabled after repeated consecutive failures.
- [AI-quality] A schedule description is parsed into a technically-valid but user-unintended
  recurrence rule.

**How It Propagates**: a routine failure propagates exactly like a normal task failure once it
starts executing (see Subsystem 3/4) — the scheduling layer's *own* unique failure mode is entirely
about *whether and when* the task starts at all, not what happens once it does. A silently
misparsed schedule is the most dangerous shape here: the routine runs successfully, on a schedule
the user never actually asked for, with nothing anywhere reporting an error.

**How to Isolate**: first confirm whether the problem is scheduling (wrong time/day/frequency,
right or wrong task content) or execution (right time, wrong task outcome) — a misreported "routine
doesn't work" complaint conflates these constantly. Check the routine's own configured schedule
against what the user actually described in plain language before assuming an execution bug.

---

## Subsystem 13 — Alternate Intake Channels

**Possible Failures**:
- [Coded] Unlinked/expired-link account rejected at message intake.
- [Infra] Webhook delivery failure from the messaging provider's side.
- [Coded/silent] A channel-specific processing failure that's designed to still return success to
  the vendor (to avoid retry storms) — meaning a real internal failure here can be genuinely
  invisible to both the user and the vendor simultaneously.

**How It Propagates**: because at least one of these channels is deliberately built to acknowledge
receipt even when internal processing fails, a bug here can be the quietest failure shape in this
entire document — no user-visible error, no vendor-visible error, only an internal log line (if
that). Symptom: a user reports "I texted and nothing happened," with literally nothing else to go
on.

**How to Isolate**: for this specific "nothing happened, no error anywhere" symptom, start from
delivery confirmation on the channel provider's own side (did the message even arrive), then check
internal logs for a processing attempt — don't assume the task engine itself is at fault before
confirming the message was received and parsed at all.

---

## Subsystem 14 — Evaluation Framework

**Possible Failures**:
- [Coded] N/A in the traditional sense — a check failing correctly is the framework working, not a
  bug.
- [AI-quality] The judge itself is a biased grader (favoring longer answers, favoring
  answer-order in a comparison) — a failure of the *test*, not the thing under test.
- [Infra] A judge-model upgrade silently shifts historical scores, breaking baseline comparability.
- [Process] No automatic trigger exists — a real regression can ship with no eval run ever having
  been attempted against it.

**How It Propagates**: this subsystem's most dangerous failure mode doesn't produce a bad eval
result at all — it produces *no eval result*, because nothing ran. A shipped regression from an
un-evaluated change propagates exactly like any other Subsystem 4 (Agent Decision Loop) failure in
production, discovered by users instead of by this framework, which is precisely the scenario this
subsystem exists to prevent.

**How to Isolate**: if a production quality regression is traced back to a specific prompt/model
change, the first question for this subsystem specifically is "was an eval run ever attached to
that change, and if so, did it actually flag anything?" — a "yes, and it missed it" points at the
judge/dataset quality; a "no" points at the process gap itself, which is the more common answer
today.

---

## Subsystem 15 — Background Jobs & Queue

**Possible Failures**:
- [Infra] A job's worker crashes mid-execution.
- [Infra] Queue backlog under high load, causing delayed (not failed) execution.
- [Infra] Shared-resource contention with live API traffic, since both currently run on the same
  instances.

**How It Propagates**: this subsystem's failures are almost purely *latency* failures propagating
into every other subsystem that depends on background work — a routine that "didn't fire," a memory
write that "didn't happen," a step that "took forever" can all trace back to queue congestion rather
than a defect in the feature itself. A true job loss (not just delay) is rarer and shows up as the
Subsystem 3 "orphaned job" signature — no error, no progress, ever.

**How to Isolate**: if multiple, otherwise-unrelated background-dependent symptoms appear around
the same time (routines late, memory writes missing, steps slow), suspect this subsystem — a
shared-infrastructure bottleneck — before investigating each symptom's own feature logic
independently.

---

## Symptom → Likely Subsystem, at a glance

A fast first-pass lookup; [12_debugging_checklist.md](12_debugging_checklist.md) has the full
step-by-step for each of these.

| Symptom | Check first | Then check |
|---|---|---|
| Task appears frozen, no updates | Client realtime layer (S1) | Task state directly (S3), Job Queue (S15) |
| Task failed immediately, specific reason given | That reason's own subsystem directly (usually S8/S9/S10) | — |
| Task failed after a delay, generic/no reason | LLM Provider (S5) | Device layer (S8/S9/S10) |
| Task completed but did the wrong thing, no error anywhere | Agent Decision Loop (S4) reasoning trail | Tool Selection/grounding (S7) |
| Agent seems to have "forgotten" something | Memory & Context (S6) | Task Lifecycle history (S3) |
| Everything fails for one account only | Authentication (S2) | — |
| Device won't respond at all | Device automation (S8/S9) | Dongle hardware (S10) |
| "I texted/DMed and nothing happened" | Alternate channel delivery (S13) | — |
| Routine ran at the wrong time / not at all | Scheduling config vs. described intent (S12) | Job Queue (S15) |
| A prompt/model change "feels" worse in production | Evaluation Framework — was it actually run? (S14) | Agent Decision Loop (S4) |

---
**Next:** [11_observability.md](11_observability.md) — exactly where to look, per subsystem, to confirm or rule out each of the failures above.
