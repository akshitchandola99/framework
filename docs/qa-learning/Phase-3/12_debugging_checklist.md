# 12 — Debugging Checklist

*Phase 3 · Document 4 of 4. Where the other three documents give you the map
([09](09_qa_testing_strategy.md)), the catalog ([10_failure_modes.md](10_failure_modes.md)), and
the instrumentation ([11_observability.md](11_observability.md)), this document gives you the
actual step-by-step. Part A starts from a symptom you're looking at right now. Part B gives you
recipes for forcing a specific failure to happen on purpose, for testing. Part C is a fast
per-subsystem index back into the other three documents.*

---

## Before you start: the general method

1. Read the task's state history first. Always. It tells you what the system itself believes
   happened, which narrows everything that follows.
2. Separate the three failure shapes early ([10_failure_modes.md](10_failure_modes.md)): is there a
   specific named reason recorded (**Coded** — go read it, it's usually trustworthy), is there a
   retry/timeout pattern in progress (**Infra** — check if it's still within its expected window),
   or is there no error at all despite a wrong outcome (**AI-quality** — go read the reasoning
   trail, not the error log, because there isn't one)?
3. Don't diagnose from the final symptom alone. Reconstruct the sequence: what did the system
   observe, what did it decide, what did it do, what actually happened as a result. Most
   misdiagnoses in this product come from skipping straight to "it's broken" without walking that
   chain.
4. If real hardware is involved anywhere in the chain, don't rule it out from logs alone — a
   surprising number of "software" symptoms in this product are, at the root, a dongle out of
   range or a screen that locked at the wrong moment.

---

## Part A — Symptom-First Runbooks

### 1. Task appears stuck / not progressing

1. Check the client's realtime-connection indicator first — if it's showing degraded/stale, this
   may be a display problem, not a real one. Force a fresh reload of the task and compare.
2. If the task genuinely hasn't moved: read its state history. What's the last recorded
   transition, and how long ago?
3. Still in an active/executing state with no recent transition → check step-level trace
   breadcrumbs for where inside the step things stopped.
4. Check whether the last LLM call for that step is still pending, failed into a retry window, or
   completed normally but nothing happened after.
5. Check the target device/receiver's connection state directly — is it awake, connected, and
   responsive?
6. If none of the above explains it and the task has been inactive for an extended period, this may
   be an orphaned background job. Remember: the automatic safety sweep for this is measured in
   hours, not minutes — don't expect it to self-resolve quickly, and escalate rather than wait.

### 2. Agent tapped the wrong element / took the wrong action (grounding failure)

1. Confirm this is actually a grounding failure, not a reasoning failure: read that step's
   reasoning fields. Did it correctly identify the *right* target and simply miss the coordinate, or
   did it misidentify the target in the first place?
2. If grounding: inspect the exact screenshot from that step for visual ambiguity — similar-looking
   controls close together, a keyboard covering the target, small or low-contrast text.
3. Note the device's screen resolution and which model powered that step — both are known,
   legitimate sources of coordinate-accuracy variance.
4. Check the next step: did the agent's own self-verification notice the miss and recover, or did
   it proceed as if the tap landed correctly?
5. If reasoning was itself wrong (not a grounding issue): treat this as an Agent Decision Loop
   finding, not a device/hardware one — the fix path is completely different.

### 3. Task failed immediately with no clear reason

1. Read the recorded failure reason on the task itself first — "no clear reason" from the user's
   side often still has a specific internal code.
2. A specific device-reported reason (locked screen, missing permission, paused, outdated version)
   → go straight to that device's own state; no further backend investigation needed.
3. No device-level reason, but a structured-output/schema validation failure → pull the full
   per-call model debug capture for that step and inspect the raw model output directly.
4. If this is a cloud-phone task: check whether it was started immediately after requesting the
   phone — a session that isn't warmed up yet is a known scenario that can fail on the very first
   attempt rather than retrying.

### 4. Task completed but the answer is wrong or nonsensical (no error anywhere)

1. Confirm there's genuinely no error recorded anywhere in the task — this determines you're in
   AI-quality territory, not a coded/infra one.
2. Read the full reasoning trail across *every* step, not just the last one — the point where it
   went wrong is often several steps before the final, visibly wrong answer.
3. Check what was injected into the task's context at the very start (memory, routine context) —
   confirm the model was reasoning from *correct* inputs before concluding the reasoning logic
   itself is at fault.
4. Check whether the final response is actually consistent with what the agent observed during the
   task, or contradicts it — a disconnect here is a distinct, nameable defect (an ungrounded final
   answer).
5. Re-run the same task 3–5 times before concluding this is a consistent, reproducible defect —
   distinguish "wrong every time" from "wrong this one time," since the fix and the severity differ.

### 5. Device won't pair / receiver not responding to a pairing attempt

1. Confirm the pairing code hasn't expired (short window) or already been used.
2. Confirm the receiver app's version isn't older than the currently required minimum for this
   environment.
3. Confirm the device has network connectivity.
4. If pairing fails with an environment/account-mismatch-flavored error, check whether the receiver
   build and the backend environment being tested against actually correspond to each other — a
   receiver built for one environment cannot pair against a different one, and this is a real,
   specifically-detected failure case, not a generic error.

### 6. Dongle won't connect, or disconnects mid-task

1. Physical checks first, before any software investigation: dongle powered, USB properly seated
   in the host device, BLE within range.
2. Check the receiver app's own displayed connection state directly on the device — this is more
   informative than any cloud-side log for this layer.
3. Check dongle battery level if visible.
4. If a firmware update was recently attempted or interrupted, check for a bootloader-stuck /
   recovery-needed state specifically.
5. To confirm this is genuinely hardware and not a one-off: reproduce with a *different* dongle on
   the *same* device, and the *same* dongle on a *different* device — this isolates whether the
   fault travels with the dongle or the device.

### 7. Screenshot / screen state looks stale or wrong

1. First confirm whether a fresh screenshot was actually expected at this step — recall that
   refresh is conditional (only after a device-touching action); a screenshot that's one step behind
   may be expected behavior, not a bug.
2. Check screen-capture permission status on the device.
3. On iOS specifically: check the broadcast/session running-state, and specifically whether the
   device was recently rebooted (a known scenario where stale state needs a specific check to be
   correctly cleared).
4. If small text is illegible: check image compression settings against the device's display
   density — this is a known, real trade-off, not necessarily a defect.

### 8. Cloud phone won't load / stuck on a black screen

1. Separate two independent questions immediately: is the *task* actually progressing (new steps,
   screenshots appearing) regardless of what the video shows, and is the *video view* connected?
   Check both, don't assume they're the same problem.
2. If the task is progressing but video isn't: this is a signaling/view-layer issue — check WebRTC
   connection status specifically, not task execution.
3. If the task itself isn't progressing either: check the session's boot-stage progression — was
   this task started before the session finished warming up?
4. Check client-side network conditions (throttled bandwidth, an unstable connection) as a
   contributing factor to a video-specific failure.

### 9. Routine didn't fire, or fired at the wrong time

1. Pull up the routine's actual configured schedule and compare it directly, side by side, against
   what the user originally described in plain language.
2. Before concluding "wrong time," confirm the discrepancy is outside the expected scheduling
   jitter window — a few minutes of slack is by design, not a bug.
3. Check whether the routine was auto-disabled due to repeated prior failures.
4. Check timezone configuration specifically if the discrepancy looks like a fixed-hour offset —
   this is the single most common root cause for "fired on the wrong day/time" reports.

### 10. Agent appears to "loop" or repeat the same action

1. Pull the task's step count and elapsed time/cost — confirm this is genuinely elevated relative to
   a normal task of similar complexity.
2. Read several consecutive steps' reasoning fields in sequence — did the agent recognize "no
   progress" and still repeat the action anyway, or did it perceive each attempt as meaningfully
   different (a perception problem, not a decision-logic problem)?
3. Check whether a step-count or duration limit eventually intervened, and whether it fired at the
   expected threshold.
4. To reproduce deliberately for regression testing: construct a task that lands on a genuinely
   dead-end or repetitive UI state (a broken button, a modal that won't dismiss) and observe whether
   the agent changes strategy.

### 11. Unexpected cost or latency spike on a task

1. Check step count first — this is the most common, simplest explanation.
2. Check whether a reasoning-capable model configuration was used for this task/receiver type —
   reasoning tokens add cost and latency that aren't visible in the user-facing response.
3. Check for context-compaction events during the task — each one is a genuine extra full LLM call.
4. Check cache efficiency for this task's specific model/receiver-type combination against the
   normal baseline for that combination — a silent cache-efficiency regression is a pure cost issue
   with no correctness symptom to tip you off otherwise.
5. Compare against the aggregate per-model dashboard to see if this is an isolated task or part of
   a broader trend.

### 12. Task asked for user input/intervention unexpectedly, or failed to ask when it should have

1. If it asked unnecessarily: read the reasoning trail for *why* it believed clarification or
   takeover was needed — determine whether there was genuine, defensible ambiguity in the request or
   screen, or whether it misread something that was actually clear.
2. If it did **not** ask when it arguably should have (e.g., proceeded through something a human
   should have been consulted on): check whether this matches a known, code-level-detected scenario
   (certain login walls are specifically detected) or falls outside anything currently covered.
3. Treat "it should have asked but didn't, and there's no code-level gate that would have forced
   it to" as an expected, reproducible category of finding in this product today — this is a
   documented, open gap in how irreversible/risky actions are gated, not a one-off bug. Report it as
   a product-risk finding, not just a single-task defect.

---

## Part B — Reproduction Techniques

Concrete ways to force a specific failure to happen on purpose, for building regression tests or
confirming a fix.

| Failure to reproduce | How |
|---|---|
| Stuck / orphaned task | Target a device you can deliberately disconnect (airplane mode, kill the receiver app) mid-task, then observe whether/how the system reports it. |
| Grounding failure | Target an app with a custom-rendered UI (a game, a canvas view, a WebView) or a screen with several visually similar controls close together; test with the on-screen keyboard open, which shifts layout. |
| Dongle disconnect | Physically move the dongle out of BLE range, or power it off, mid-task; separately, unplug the USB side while BLE stays connected. |
| Screen-locked mid-task | Manually lock the target device's screen at a precise moment during an active task — try immediately after pairing, mid-action, and between steps as three distinct timings. |
| Rate limit / timeout | Only reproducible where a sandboxed key/quota is available to exhaust deliberately; otherwise, treat this as opportunistic (observe behavior during real load spikes) rather than forcibly reproducible in isolation. |
| Context compaction | Run an artificially long, multi-part task (chained follow-up requests, a complex multi-app workflow) until the token threshold is crossed; watch for the visible "context compacted" marker in the thread. |
| Auth/permission failure | Create a fresh, deliberately non-admitted account and attempt any gated action; separately, use a deliberately expired or revoked token. |
| Receiver version mismatch | In a non-production environment only: pair a deliberately outdated receiver build against an environment whose minimum version has been raised. |
| Indirect prompt injection | Construct a test web page or app screen containing visible adversarial instruction text, and have the agent navigate to and read it as part of a legitimate-looking task. |
| Cross-user memory leak | State distinctive, easily-identifiable facts on two separate test accounts, then check for cross-contamination in later, unrelated tasks on each account. |
| Invalid/ambiguous routine schedule | Submit deliberately vague ("sometime soon"), contradictory ("every day, but only on weekends, except Tuesdays"), or out-of-range ("the 32nd of this month") natural-language schedule descriptions. |
| OEM background-kill (Android) | Leave a task's target device backgrounded for an extended period on a device from an OEM known for aggressive battery management; compare against a more permissive OEM as a control. |
| iOS background/audio interruption | Trigger an incoming call or another app's audio session during an active session; separately, background the app past a range of durations to find where the session degrades. |
| Firmware update interruption | Deliberately force-quit the app or move the dongle out of range mid-firmware-update, at more than one point in the process, and confirm recovery on next launch. |
| Non-determinism / "distribution" testing | Run the identical task 5–10 times unmodified and record the success rate and the variety of paths taken, rather than treating any single run as definitive. |

---

## Part C — Per-Subsystem Quick Reference

| Subsystem | First thing to check | Typical root causes | Full detail |
|---|---|---|---|
| 1. Client Applications | Realtime connection indicator | Stale connection, backend-version mismatch after deploy | [10 §1](10_failure_modes.md), [11 §1](11_observability.md) |
| 2. Authentication & Account Access | The specific rejection reason code | Expired token, waitlisted account, missing permission | [10 §2](10_failure_modes.md), [11 §2](11_observability.md) |
| 3. Task Lifecycle & State Management | Task state history | Wrong state transition, orphaned job, queueing bug | [10 §3](10_failure_modes.md), [11 §3](11_observability.md) |
| 4. Agent Decision Loop | Step reasoning fields | Reasoning error, missed self-verification, ungrounded final answer | [10 §4](10_failure_modes.md), [11 §4](11_observability.md) |
| 5. LLM Provider Layer | Raw vendor request/response | Vendor-specific gap, rate limit/timeout, schema mismatch | [10 §5](10_failure_modes.md), [11 §5](11_observability.md) |
| 6. Memory & Context | The actual stored memory content | Wrong/missing recall, stale fact, cross-user leak | [10 §6](10_failure_modes.md), [11 §6](11_observability.md) |
| 7. Tool Selection & Device Command Routing | Tool call vs. resulting device state, side by side | Wrong arguments, ignored tool failure, receiver-type filtering bug | [10 §7](10_failure_modes.md), [11 §7](11_observability.md) |
| 8. Android Device Automation | Device-reported failure reason | Locked screen, permission revoked, OEM background kill | [10 §8](10_failure_modes.md), [11 §8](11_observability.md) |
| 9. iOS Device Automation | Broadcast/session running-state | AssistiveTouch off, stale post-reboot state, background kill | [10 §9](10_failure_modes.md), [11 §9](11_observability.md) |
| 10. HID Dongle Hardware | The dongle/device physically | BLE range, battery, USB seating, firmware mismatch | [10 §10](10_failure_modes.md), [11 §10](11_observability.md) |
| 11. Cloud Phone | Signaling status vs. task execution status, separately | Session not warmed up, WebRTC negotiation failure | [10 §11](10_failure_modes.md), [11 §11](11_observability.md) |
| 12. Routines & Scheduling | Configured schedule vs. described intent | Misparsed natural language, timezone mismatch, auto-disable | [10 §12](10_failure_modes.md), [11 §12](11_observability.md) |
| 13. Alternate Intake Channels | Channel provider's own delivery confirmation | Unlinked account, silent internal processing failure | [10 §13](10_failure_modes.md), [11 §13](11_observability.md) |
| 14. Evaluation Framework | Whether a run was attempted at all | No automatic trigger, judge bias, judge-model drift | [10 §14](10_failure_modes.md), [11 §14](11_observability.md) |
| 15. Background Jobs & Queue | Clustering of unrelated background-feature symptoms | Worker crash, queue backlog, shared-resource contention | [10 §15](10_failure_modes.md), [11 §15](11_observability.md) |

---

## Closing note

Two habits carry more weight than any individual checklist item in this document:

- **Read the reasoning before you read anything else**, whenever the symptom smells like an
  AI-quality issue rather than a coded error. It's the one thing this product gives you that most
  systems don't, and it's usually faster than any other investigation path.
- **Don't rule out physical hardware from software alone.** A dongle out of range, a screen that
  locked at the wrong moment, or an OS that killed a backgrounded app all look, from the cloud side,
  like generic timeouts. If the chain of evidence runs out in the logs, the next step is checking
  the device, not re-reading the logs again.

This closes Phase 3.
