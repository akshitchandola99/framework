# 09 — QA Testing Strategy

*Phase 3 · Document 1 of 4. Written for a QA engineer joining Airtap, assuming everything covered
in Phase 1 (system architecture) and Phase 2 (AI theory ↔ implementation). This phase is
practitioner-facing: it does not explain how the code works — it tells you what to test, why, and
how. Companion documents: [10_failure_modes.md](10_failure_modes.md) (what breaks),
[11_observability.md](11_observability.md) (where to look), [12_debugging_checklist.md](12_debugging_checklist.md)
(what to do about it).*

---

## How to test a product like this

Three properties of Airtap change how testing has to work here, compared to a typical web/mobile
product:

1. **The core logic is non-deterministic.** The same task, run twice, can take a different — and
   equally correct — path. Exact-match assertions ("the agent must tap coordinate 412,88") mostly
   don't work. You're testing for a *distribution* of acceptable behavior, verified by outcome and
   state, not a single expected trace.
2. **A meaningful share of the product is physical hardware.** A BLE dongle, a real phone, a USB
   connection — these fail in ways that have no software analogue and cannot be reasoned about from
   the code. They have to be tested on real devices, not simulated.
3. **Some actions are irreversible.** A sent message, a completed purchase, a deleted item — there
   is no "regenerate response" undo button. Test depth should scale directly with blast radius: the
   same instinct as testing a payment flow harder than a settings screen, applied to a system where
   almost any tool call could, in principle, be the risky one.

Everything in this document set is organized around the same 15 subsystems, in the same order,
so you can cross-reference between "what to test" (this document), "what breaks" (document 10),
"where to look" (document 11), and "what to do" (document 12) without re-orienting each time.

---

## Test environments and accounts

Before testing anything: know which environment you're in and what account state you need.

- **Environments are fully isolated**: `local`, `dev1–4`, `qa1`, `qa2`, `prod`. A task, device
  pairing, or account in one environment is invisible in another — "it doesn't exist" is often
  really "you're looking in the wrong environment," not a bug.
- **New accounts start gated.** An account is `WAITLISTED` by default and can't create tasks until
  admitted — either by an email-domain allowlist or a manual admission action. If a fresh test
  account "does nothing," check its admission status before assuming the product is broken.
- **Automation/CI accounts** should use a Personal Access Token rather than a normal session login —
  this is the supported credential for scripted test runs.
- **Client apps must be pointed at the right backend.** Pilot Web and Pilot iOS both have
  environment-specific configurations (env files for web, build schemes for iOS); confirm you're
  testing against the environment you think you are, especially after a context switch.
- **Daily credit/usage limits reset on UTC date rollover**, not a rolling window — a test run
  spanning UTC midnight can appear to fail mid-run for a reason unrelated to what you're actually
  testing.

---

## Risk-based prioritization

Not all 15 subsystems deserve equal test depth. Applying the same risk-tiering instinct the roadmap
recommends for individual actions, at the subsystem level:

| Tier | Subsystems | Why |
|---|---|---|
| 🔴 **Deepest coverage** | Agent Decision Loop, Tool Selection & Device Command Routing, Android/iOS Device Automation, HID Dongle Hardware | Where a wrong or ungrounded decision becomes a real, sometimes irreversible, physical action. |
| 🟡 **High coverage** | LLM Provider Layer, Memory & Context, Task Lifecycle, Cloud Phone, Evaluation Framework | Correctness and continuity issues here are usually recoverable but directly affect whether the product does what it claims. |
| 🟢 **Standard coverage** | Client Applications, Authentication, Routines & Scheduling, Alternate Intake Channels, Background Jobs & Queue | Real, testable failure surfaces, but generally fail loudly and recoverably rather than silently or irreversibly. |

This isn't a ranking of *importance* — it's a ranking of where a subtle bug does the most damage
before anyone notices it, which is where test investment pays off fastest.

---

## Subsystem 1 — Client Applications (Pilot Web + Pilot iOS)

**Purpose**: the surface a user actually touches — compose a task, watch it run, pair a device, set
up a routine, manage their account.

**Expected Behaviour**:
- A composed task (text/image/voice) reaches the backend and appears in the thread within a normal
  network round trip.
- The task thread updates live as the agent works — new steps, screenshots, and status labels
  appear without a manual refresh.
- Device pairing (QR + code) succeeds for a freshly installed receiver app and fails clearly
  (not silently) for an expired or mistyped code.
- Auth state (signed in / waitlisted / banned / signed out) is reflected accurately and immediately
  in what the UI allows.
- Routines can be created via preset schedules and via free-text schedule descriptions, both
  producing a schedule that matches what the user described.

**Edge Cases to Test**:
- Sending a follow-up message while a task is actively executing vs. while it's waiting on the user
  vs. while it's already finished.
- Losing network connectivity mid-task, then regaining it — does the thread catch up or stay stale?
- Multiple browser tabs / two devices signed into the same account simultaneously.
- Voice input with background noise, multiple languages, or silence.
- A routine's free-text schedule description that's deliberately vague, contradictory, or
  impossible ("every day at 25:00").
- Switching a task's target device mid-composition, after already selecting one.

**Regression Risks**: any change to the realtime update mechanism, the composer's attachment
handling, or the auth state machine is high-risk for silent breakage — these are the parts of the
client most likely to fail in a way that *looks* fine until you watch closely (a thread that stops
updating still shows the last successful state, not an error).

**Test Approach**: manual exploratory testing remains the primary method today; automated coverage
is currently a thin UI-shell smoke suite (page loads, key elements present) rather than full task
execution — treat any automated pass here as confirming the app *loads*, not that a task actually
completes correctly. Cross-platform parity checks (does a behavior on web match iOS?) are worth
running deliberately rather than assuming they'll match.

---

## Subsystem 2 — Authentication & Account Access

**Purpose**: gate who can use the product and what they can do — separate from, and layered on top
of, whether a device is paired.

**Expected Behaviour**:
- A valid session token grants access; an expired one prompts a clean re-authentication, not a
  silent failure.
- Admission state (`WAITLISTED`/`ADMITTED`/`BANNED`) is enforced independently of token validity —
  a perfectly valid token on a waitlisted account is still blocked from task creation.
- Device pairing issues a credential scoped only to that device's own data — one device can never
  read another device's or another user's data.
- Permission-gated internal surfaces (dashboards, evals, admin console) are inaccessible to accounts
  without the relevant permission.

**Edge Cases to Test**:
- Token expiry occurring mid-task (does the in-flight task survive; does the next action prompt
  re-auth cleanly?).
- Sign-out on one tab/device while another tab/device for the same account stays open.
- A pairing code used twice, or after its expiry window.
- An account transitioning from `WAITLISTED` to `ADMITTED` while a session is already open — does
  the client pick this up without a full logout/login?
- A Personal Access Token used from an unexpected context (wrong environment, revoked token).

**Regression Risks**: changes to the admission-gate logic or to device-pairing token issuance are
high-risk — a mistake here either locks out legitimate users or, worse, under-scopes a credential.
Any change to cross-tab/cross-device session handling should be retested for races, not just the
single-session happy path.

**Test Approach**: primarily manual/exploratory given the state-transition and race-condition
nature of the risk here; a scripted check confirming a waitlisted PAT/account is correctly denied
task creation is a cheap, high-value regression guard worth keeping in any automated suite.

---

## Subsystem 3 — Task Lifecycle & State Management

**Purpose**: the record of a task's life — its state, its message thread, and the rules for what can
happen next from any given state.

**Expected Behaviour**:
- A task moves through a well-defined set of states (queued, executing, waiting-on-user variants,
  and terminal states) and never appears to skip or reverse through them illogically.
- Only one blocking task runs per user at a time; a second task queues and auto-starts when the
  first finishes.
- A follow-up message sent mid-execution is queued and picked up at the next step, not dropped or
  used to interrupt the current step.
- Resuming a finished/waiting task correctly re-validates preconditions (e.g., available credit)
  rather than blindly continuing.

**Edge Cases to Test**:
- Cancelling a task at each distinct state (queued, mid-step, waiting-on-user) and confirming a
  clean, consistent terminal state each time.
- Two rapid task-creation requests from the same user in immediate succession.
- A task that runs long enough to be a genuine candidate for the stale-task safety sweep — confirm
  it's still hours, not minutes, before anything auto-intervenes.
- Deleting/sharing a task in each of its possible states.
- A task resumed after the account's credit balance dropped to zero while it was waiting.

**Regression Risks**: the state-transition map itself is the highest-risk surface — any change to
which tool call or event maps to which state needs full state-matrix retesting, not just the
specific path that changed. Changes near the per-user queueing rule are a close second, since a
bug there is easy to miss in single-task testing and only appears under concurrent load.

**Test Approach**: this is one of the more automatable subsystems — state transitions are discrete
and assertable. Prioritize a state-matrix regression suite (every documented state × every valid
transition into and out of it) over ad hoc manual spot checks.

---

## Subsystem 4 — Agent Decision Loop

**Purpose**: the actual "brain" — reads the current screen and context, decides one action at a
time, until the task is done. This is the highest-value, hardest-to-test subsystem in the product.

**Expected Behaviour**:
- Every decision is preceded by visible reasoning (an observe/review/plan-style explanation) that
  is genuinely specific to the current screen and task — not generic filler.
- The agent recognizes when it has completed the task and stops, rather than continuing to act.
- The agent recognizes when it's missing required information and asks the user, rather than
  guessing.
- The agent recognizes when it needs the user to take over (e.g., a login wall) and hands off
  cleanly.
- Repetitive or dead-end UI states cause the agent to change strategy, not repeat the same action.

**Edge Cases to Test**:
- Tasks with genuinely ambiguous target apps or accounts ("send it to John" when there are two
  Johns).
- Screens that change mid-perception (an animation, a toast notification, a loading spinner caught
  mid-transition).
- Apps with sparse or entirely missing structured UI metadata (games, canvas-rendered views,
  WebViews) — this is where the agent is most exposed.
- A task that plausibly nears an irreversible action (a purchase, a delete, a message send) —
  observe what actually happens today, since this isn't guaranteed to be gated.
- Deliberately adversarial on-screen content (text on a page instructing the agent to do something
  other than the user's actual request) — a genuine indirect-prompt-injection test.
- A long-running task that crosses into context compaction — confirm coherence survives it.

**Regression Risks**: any change to the system prompt, the playbook rules, the tool schemas, or
which model powers a given receiver type is a full-regression trigger for this subsystem — small
wording changes here have historically outsized, hard-to-predict effects on behavior across many
tasks at once, which is exactly why this is the single most important subsystem to gate behind a
quality check before shipping a change (see the Evaluation Framework, Subsystem 14).

**Test Approach**: run the same task multiple times and evaluate a *success rate*, not a single
pass/fail — non-determinism is the default here, not the exception. Separate "did it reason
correctly" from "did the action land correctly" (the latter is Subsystem 7/8's territory) when
triaging a failure — conflating the two wastes investigation time. Red-team the guardrails
(internal-detail leakage, injection resistance) as a standing, recurring test category, not a
one-time check.

---

## Subsystem 5 — LLM Provider Layer (Multi-Model Inference)

**Purpose**: the layer that actually calls whichever AI model powers a given decision, across
several different vendors.

**Expected Behaviour**:
- Behavior is functionally consistent across the different models/vendors that can power the same
  receiver type or purpose — differences should be in degree (accuracy, latency), not in kind
  (one vendor silently skipping a required behavior).
- Token/cost accounting for every call is accurate and reflected in the account's usage.
- A transient provider failure (rate limit, timeout) recovers automatically within a bounded
  window; a persistent one fails the task with a clear reason, not an infinite retry.

**Edge Cases to Test**:
- The same task executed by each configured model/vendor combination — deliberately compare
  outcomes, not just confirm each one "works."
- Extremely short and extremely long tasks, to exercise both the token-tracking floor and the
  context-compaction ceiling.
- A deliberately triggered rate limit or timeout (where testable) to confirm retry/backoff behavior
  matches what's documented.
- A model swap (via configuration) mid-investigation — confirm coordinate/tap accuracy is
  re-verified, not assumed to carry over from the previous model.

**Regression Risks**: any vendor SDK upgrade or new vendor onboarding is a full-matrix regression
trigger (structured output, multimodal input, tool calling, and reasoning all need reverification
per vendor) — a bug that's vendor-specific is easy to miss if testing only exercises the default
model.

**Test Approach**: build and maintain a small, repeatable "cross-vendor parity" task set,
independent of the main eval dataset, specifically to catch behavior that diverges by vendor rather
than by task difficulty.

---

## Subsystem 6 — Memory & Context

**Purpose**: what the agent carries forward — both within one task (conversation history) and
across a user's entire history with the product (long-term memory).

**Expected Behaviour**:
- A fact stated in one task is available and correctly used in a later, unrelated task by the same
  user.
- Memory never crosses users — this is a security property, not just a correctness one.
- A corrected/updated fact supersedes the old one going forward (behavior not independently
  confirmed as of this writing — treat as an open test question, not an assumption).
- Long context within a single task compacts without losing coherence about what's already been
  done.

**Edge Cases to Test**:
- Stating a fact, then explicitly contradicting it in a later task.
- A user asking the agent to "forget" something, and confirming it's actually gone, not just
  acknowledged in the reply text.
- Two users with very similar or identical stated facts, tested concurrently, to catch any
  cross-contamination.
- A task long enough to force at least one context-compaction event, followed by several more
  steps, checking the agent doesn't "forget" what it already tried.
- A brand-new account with no memory history at all — confirm graceful behavior, not an error.

**Regression Risks**: this is a security-adjacent subsystem — any change to how memory is scoped,
read, or written deserves isolation retesting, not just functional retesting. A memory-write
change is also a cost-risk (an unbounded or overly verbose memory write inflates future prompts).

**Test Approach**: cross-user isolation testing should be a standing, recurring suite, not a
one-time check — treat it with the same rigor as a permissions/authorization test suite elsewhere
in the product, because that's functionally what it is.

---

## Subsystem 7 — Tool Selection & Device Command Routing

**Purpose**: the bridge between "the agent decided X" and "X actually happened somewhere" —
choosing the right tool, filling correct arguments, and routing the resulting command to the right
execution channel (cloud vs. a specific paired device).

**Expected Behaviour**:
- Only tools that are genuinely usable on the current receiver type are ever offered or chosen.
- Tool arguments are well-formed and match what the current screen/task actually calls for.
- A tool's result (success, or a specific failure) is correctly reflected in what the agent does
  next — a failed action should not be treated as if it succeeded.
- The correct transport (cloud vs. device) is used for the current task's receiver, with no
  cross-wiring.

**Edge Cases to Test**:
- A task that starts on one receiver type and — if ever possible — the receiver becomes unavailable
  mid-task.
- Tool arguments at their boundaries: empty strings, very long text, unusual characters/emoji,
  right-to-left scripts.
- A tool call that plausibly maps to more than one valid interpretation (which of several similar
  buttons/fields is meant).
- Deliberately interrupting an in-progress action (e.g., locking the screen) exactly as a command is
  dispatched, to test the race, not just the before/after states.

**Regression Risks**: any change to the receiver-type-based tool filtering list is high-risk for a
"tool offered but not executable on this receiver" class of bug — verify the *exclusion* list, not
only that new tools work where intended.

**Test Approach**: this subsystem benefits from targeted, scripted fault injection (deliberately
returning a specific failure from a tool and confirming the agent's next decision handles it
correctly) more than from broad exploratory testing.

---

## Subsystem 8 — Android Device Automation

**Purpose**: the on-device software that actually executes a decision on a physical or emulated
Android phone — via accessibility-based input or the HID dongle.

**Expected Behaviour**:
- Commands from the backend are picked up promptly when the device is awake and connected.
- A backgrounded/sleeping device wakes and resumes within a reasonable window when a task targets
  it.
- Device-side failure states (locked screen, missing permission, paused app, outdated app version)
  are reported back as specific, distinguishable reasons — not a generic failure.
- Screenshots are current, legible, and correctly reflect the device's actual state at capture time.

**Edge Cases to Test**:
- Screen lock triggered at various points mid-task (immediately after pairing, mid-action, between
  steps).
- Revoking the accessibility permission or screen-capture permission mid-session.
- OEM-specific battery optimization killing the app in the background (test on more than one
  device manufacturer — this varies significantly by OEM).
- A receiver app intentionally left on an old version against a backend with a raised minimum
  version requirement.
- Low storage, low battery, and airplane-mode-toggle scenarios during an active task.
- Switching between the accessibility-driven and dongle-driven execution paths on devices that
  support both.

**Regression Risks**: OS-version and OEM-skin changes are an ongoing regression risk independent of
any code change on Airtap's side — a new Android OS release or OEM update can silently change
accessibility or battery-management behavior. This subsystem needs periodic revalidation on a
device/OS matrix, not just after Airtap's own releases.

**Test Approach**: real devices are mandatory for permission, battery, and OEM-specific behavior;
an emulator is acceptable for pure UI-navigation correctness but cannot substitute for the
hardware/OS-integration edge cases above.

---

## Subsystem 9 — iOS Device Automation

**Purpose**: the on-device software that executes a decision on a physical iPhone, always via the
HID dongle (no software-injection alternative exists on iOS).

**Expected Behaviour**:
- The dongle is correctly detected as unusable if AssistiveTouch is off, with a clear prompt to
  enable it — not a silent failure to act.
- Screen capture (via the OS broadcast/recording mechanism) accurately reflects "is a broadcast
  currently running," including correctly detecting a stale "still running" state left over from
  before a phone reboot.
- The background command-execution process survives normal backgrounding for a reasonable session
  length.
- Firmware version mismatches between the dongle and what the app expects trigger a clear update
  flow rather than silent malfunction.

**Edge Cases to Test**:
- Toggling AssistiveTouch off mid-session, not just at setup.
- Rebooting the phone with a broadcast/session previously active, then reopening the app — confirm
  it reports the correct (stopped) state.
- An incoming phone call or other audio interruption during an active session.
- Force-quitting the app mid-firmware-update and confirming recovery on next launch rather than a
  stuck dongle.
- Background time limits — how long can the app stay backgrounded before the session degrades or
  drops?

**Regression Risks**: iOS OS updates (especially around background execution, broadcast APIs, and
Bluetooth permission prompts) are a standing, code-independent regression risk — treat every iOS
major/minor OS release as a mandatory revalidation trigger for this subsystem specifically.

**Test Approach**: real hardware only — none of this subsystem's real risk (BLE, ReplayKit,
background survival, firmware) is meaningfully testable on a simulator.

---

## Subsystem 10 — HID Dongle Hardware

**Purpose**: the physical BLE-to-USB bridge that turns a software decision into a genuine hardware
input signal on the target device — the mechanism that makes automation indistinguishable from a
real person, and the only input path on iOS at all.

**Expected Behaviour**:
- The dongle reliably reconnects after a brief disconnect, with a bounded, predictable retry
  pattern — not an immediate permanent failure, and not a silent infinite hang.
- Text, taps, and swipes render correctly on the host device as genuine hardware input.
- A firmware mismatch is detected and can be resolved via an update flow without manual
  intervention beyond initiating it.
- Battery/power state is reflected accurately when it affects the dongle's ability to function.

**Edge Cases to Test**:
- Moving the dongle out of Bluetooth range mid-task, then back in range.
- Unplugging the dongle from the host device (USB side) while still BLE-connected to the receiver.
- A low or dead dongle battery.
- Interrupting a firmware update at every distinct stage you can identify (just started, mid-flash,
  just before completion) and confirming recovery, not a bricked-looking state.
- Very long text input, which is sent in chunks — interrupt mid-chunk-sequence and check for
  partial text left in a field, distinct from "typing failed entirely."
- Two dongles near each other / multiple receivers in the same physical space, to check for
  cross-pairing confusion.

**Regression Risks**: firmware changes are the highest-risk category here — a firmware update needs
validation on real hardware across both platforms (Android and iOS use independently-implemented
but protocol-compatible controllers) before wide rollout, since a firmware bug affects every user of
that hardware revision simultaneously.

**Test Approach**: exclusively real hardware; this is the subsystem where "test on the actual
device" is not a preference but a hard requirement — none of these failure modes can be
meaningfully simulated.

---

## Subsystem 11 — Cloud Phone (Virtual Device)

**Purpose**: the no-hardware-required option — an ephemeral, cloud-hosted virtual Android device,
controlled and viewed live over the network.

**Expected Behaviour**:
- A requested cloud phone becomes usable within a reasonable, bounded startup time.
- The live view (video) stays synchronized with the actual device state, with no persistent lag or
  freeze.
- Input sent through the live view reaches the virtual device correctly and promptly.
- The session cleanly times out after the documented idle period, and reconnecting after a timeout
  is a smooth experience, not a stuck or confusing one.

**Edge Cases to Test**:
- Starting a task the instant a cloud phone is requested, before it's had time to fully warm up.
- Network conditions that degrade mid-session (throttled bandwidth, brief disconnect) — does the
  live view recover, or does it need a manual reconnect?
- Multiple rapid session start/stop cycles in succession.
- Idle timeout boundary testing — right before and right after the documented threshold.
- Browser tab backgrounded/foregrounded repeatedly during an active session.

**Regression Risks**: this subsystem depends on an external service outside this product's own
release cycle — a regression can appear with no corresponding code change on Airtap's side. Track
and correlate incidents against that external dependency's own status/release notes when
triaging.

**Test Approach**: functional/task-execution testing can reasonably use this path in place of
physical hardware for pure software-behavior testing (it exercises the same Agent Decision Loop);
reserve physical-device testing specifically for anything hardware/dongle-specific, which a cloud
phone cannot exercise at all.

---

## Subsystem 12 — Routines & Scheduling

**Purpose**: tasks that run on a recurring schedule instead of being triggered by a user click,
including natural-language-to-schedule translation.

**Expected Behaviour**:
- A routine fires within a reasonable window of its scheduled time (some slack is expected and
  intentional — see Regression Risks) — not off by hours or on the wrong day.
- A free-text schedule description is translated into the schedule the user actually meant, or is
  rejected clearly if it's genuinely ambiguous/invalid.
- A routine's own memory/context correctly persists across its runs without leaking into unrelated
  tasks or other routines.
- Repeated failures auto-disable a routine rather than letting it fail silently forever.

**Edge Cases to Test**:
- Vague relative time phrases ("every morning," "a few times a week").
- Contradictory or combined schedules in one description.
- Out-of-range dates (a nonexistent calendar date) and inverted time ranges.
- Very short recurrence intervals.
- Timezone edge cases — a routine created in one timezone, a user later traveling to another.
- A routine scheduled to run while its target device is unavailable/unpaired.
- Many routines scheduled for the exact same instant, to check for a "thundering herd" effect.

**Regression Risks**: scheduling has intentional slack (a polling interval plus deliberate jitter)
— don't misreport "fired a few minutes late" as a bug; do treat "fired hours late, on the wrong
day, or not at all" as one. Any change to natural-language schedule parsing is a full regression
trigger for the whole valid/invalid prompt matrix, not just the specific phrasing that changed.

**Test Approach**: maintain (or reuse, if one already exists) a large matrix of valid and
deliberately invalid natural-language schedule descriptions as a standing regression suite — this
is a well-bounded, highly automatable test surface.

---

## Subsystem 13 — Alternate Intake Channels (Telegram / iMessage-SMS-RCS)

**Purpose**: text-message-based ways to create and continue tasks without opening an app.

**Expected Behaviour**:
- Linking an account via the documented flow succeeds and is reflected consistently across all
  channels.
- A task created via text behaves identically, once running, to one created via the app — same
  engine, same rules.
- Replies are delivered back to the correct channel at the correct lifecycle points (completion,
  clarification, etc.).
- A channel-specific delivery problem degrades gracefully rather than silently losing a user's
  message.

**Edge Cases to Test**:
- Sending a message to start a task while a different task is already active for that user.
- Cancel/stop commands issued via text mid-task.
- Rapid-fire multiple messages in quick succession.
- An unlinked or expired-link account attempting to use the channel.
- A degraded-deliverability contact (if testable) — confirm silence isn't mistaken for the channel
  simply working.

**Regression Risks**: because these channels reuse the same underlying task engine, most
regression risk here is channel-specific plumbing (linking, message parsing, reply delivery) rather
than task-execution logic — scope regression testing accordingly after a change: a change to the
webhook/intake code needs channel-specific retesting; a change to the agent loop needs the same
retesting it would get from any other entry point.

**Test Approach**: manual, periodic verification of the intake→reply round trip per channel; deep
task-execution testing is redundant here if already covered via the primary app (same engine).

---

## Subsystem 14 — Evaluation Framework (AI Quality Regression)

**Purpose**: the mechanism for catching an agent-quality regression (a model or prompt change that
makes the agent measurably worse) before it reaches real users.

**Expected Behaviour**:
- A run against the curated task dataset produces a stable, reproducible-in-aggregate pass rate for
  an unchanged model/prompt configuration.
- A deliberately degraded prompt or model choice is reliably caught by a run (i.e., the eval
  dataset is sensitive enough to actually detect a real regression, not just pass everything).
- Judge-based checks agree reasonably well with a human's own read of the same output.
- Cost/latency figures in a run's report match what's independently observable elsewhere.

**Edge Cases to Test**:
- Running the same configuration twice and comparing pass rates — how much natural variance exists
  run-to-run, and is that variance itself being tracked?
- A case specifically designed so a verbose-but-wrong answer might score better than a
  correct-but-terse one — direct verbosity-bias testing.
- A case run with the judge-question order flipped (if pairwise comparison is ever used) — position-
  bias testing.
- A prompt/model change known to be a genuine improvement or regression (from other testing) —
  confirm the eval framework actually reflects that direction.

**Regression Risks**: the framework itself can silently drift — an upgrade to whichever model does
the judging can shift historical scores without any product change at all, breaking baseline
comparability. Treat a judge-model upgrade as an event requiring its own validation pass, the same
as any other model change elsewhere in the product.

**Test Approach**: since this framework currently has no automatic trigger, the highest-leverage
QA action available is **process**, not code: establish (and hold the team to) running an eval pass
before any prompt/model change ships, and treat "was an eval run attached to this change" as a
release-checklist item until it's automated. Separately, periodically audit a sample of the eval
framework's own judged results by hand to catch judge drift early.

---

## Subsystem 15 — Background Jobs & Queue

**Purpose**: everything that happens outside the direct request/response cycle — agent steps,
routine polling, scheduled reports, memory writes.

**Expected Behaviour**:
- Every enqueued unit of work eventually executes or reports a clear failure — nothing silently
  vanishes.
- A worker crash or restart doesn't lose in-flight work; the next available worker picks it up.
- Background work volume doesn't starve live, user-facing request handling (they currently share
  infrastructure).

**Edge Cases to Test**:
- A deliberately long queue backlog (many tasks/routines firing close together) — does latency
  degrade gracefully or does something start timing out?
- A forced restart of a backend instance mid-job — confirm the job resumes rather than vanishing.
- Simultaneous high load on both live API traffic and background jobs at once, since they currently
  share the same process/instance pool.

**Regression Risks**: because live traffic and background work aren't isolated from each other, any
change that adds significant background load (a new scheduled job, a heavier per-task background
write) is a regression risk for live request latency, not just for the background work itself —
test both together, not in isolation.

**Test Approach**: load/stress testing here should specifically include a mixed live-traffic-plus-
background-load scenario, since testing either in isolation would miss the shared-resource risk
that's specific to this architecture.

---

## Putting it together: coverage map

| Subsystem | Automated today | Manual today | Real hardware required |
|---|---|---|---|
| 1. Client Applications | Thin (UI-shell smoke only) | Primary method | No |
| 2. Authentication | Minimal | Primary method | No |
| 3. Task Lifecycle | Feasible, underused | Common | No |
| 4. Agent Decision Loop | Via Evaluation Framework only | Essential, ongoing | No (cloud phone suffices) |
| 5. LLM Provider Layer | Adapter-level unit tests exist | Cross-vendor parity checks | No |
| 6. Memory & Context | Minimal | Essential (isolation testing) | No |
| 7. Tool Selection & Routing | Feasible, underused | Common | No |
| 8. Android Device Automation | Protocol-level unit tests only | Essential | **Yes** |
| 9. iOS Device Automation | Protocol-level unit tests only | Essential | **Yes** |
| 10. HID Dongle Hardware | Protocol-level unit tests only | Essential | **Yes** |
| 11. Cloud Phone | Minimal | Common | No |
| 12. Routines & Scheduling | Feasible, underused | Common | No |
| 13. Alternate Channels | Minimal | Periodic | No |
| 14. Evaluation Framework | The framework itself is the automation | Judge auditing | No |
| 15. Background Jobs & Queue | Minimal | Load-test scenarios | No |

The honest takeaway: automated coverage today is real but narrow (binary/hardware protocol
correctness, some backend logic, a thin UI smoke layer). The large majority of functional,
AI-quality, and hardware coverage is — and for the physical-hardware rows, must remain — manual.
Where you personally add the most value early on is exactly where this table says "essential" and
"real hardware required" line up: Subsystems 4, 8, 9, and 10.

---
**Next:** [10_failure_modes.md](10_failure_modes.md) — the same 15 subsystems, this time cataloged by what actually breaks and how that failure shows up downstream.
