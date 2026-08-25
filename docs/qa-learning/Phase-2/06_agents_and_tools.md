# 06 — Agents and Tools

*Phase 2 · Document 3 of 7. This is the core of the product — the roadmap itself calls this
territory "the part of the roadmap closest to what you test every day." Covers Phases 7–10 and 13
of the AI Roadmap. See [04_ai_components_mapping.md](04_ai_components_mapping.md) for the full
checklist.*

---

## 1. Is Airtap Actually an "Agent"?

### 1. AI Theory

Four words get used loosely: chatbot (text in, text out), assistant (adds a tool call you
basically asked for), workflow (an LLM inside a flowchart a human drew), and agent (given a goal,
it decides its own sequence of steps, acts, checks the result, and adjusts). The dividing line is
**autonomy over the sequence of steps**, not whether tools are involved.

### 2. Airtap Implementation

Airtap is a genuine agent by this test. A user gives it a goal in natural language ("check my last
Amazon order," "book me a ride"); nothing in the codebase hard-codes the sequence of taps and
screens needed to satisfy that goal. `cortex/src/yoda/yoda.ts` decides, one step at a time, what to
do next based on what it currently sees — this is architecturally distinct from, say, the
`android-direct-actions` skill's fixed intent lookups (§9 below), which *are* closer to a workflow
for the narrow slice of tasks they cover.

### 3. Runtime Workflow

```text
User: "What was my last Amazon order?"
   ↓
No pre-written script exists for "check Amazon order" — the agent has to figure out:
   open Amazon app or browser? → search order history? → which screen? → scroll? → read it?
   ↓
Each of those decisions is made live, step by step, by the Agent Orchestrator
```



### 4. Why Airtap Uses It

The whole product premise is operating arbitrary, unscripted requests across arbitrary apps — a
fixed workflow would need a hand-written flowchart per task type per app, which doesn't scale to
"any request, any app." Genuine autonomy over the step sequence is required by the product itself,
not a design flourish.

### 5. QA Perspective

- The roadmap's own honest caveat applies in reverse here: **most production "AI agents" are
actually workflows** because workflows are cheaper and more testable — Airtap deliberately isn't
one, which is exactly why it needs the much heavier testing investment (this whole document) that
a scripted workflow wouldn't.
- Test the trajectory, not just the destination: an agent can reach a correct final state through a
completely wrong or fragile path (see §11's action-level vs. task-level distinction).



### 6. Interview Mapping

- **"What's the difference between a workflow and an agent?"** → A workflow follows a human-drawn
flowchart; an agent draws its own at runtime.
- **"Is Airtap an agent?"** → Yes — task decomposition and step sequencing happen live, per
request, not from a pre-written script (with one deliberate, narrow exception — §9).
- **"Why not a workflow?"** → The product needs to handle arbitrary requests across arbitrary
apps; a flowchart-per-task-type doesn't scale to that.
- **"What would you test?"** → Whether the agent reaches the goal via a *reasonable* path, not
just whether it eventually gets there.

---



## 2. The Core Agent Loop & ReAct



### 1. AI Theory

Every agent reduces to one loop: perceive the current state → think/plan → act → observe the
result → repeat until done. **ReAct** (Reason + Act) is the specific, near-universal implementation
of this loop where the model is forced to write down its reasoning *before* every action — the
written reasoning becomes part of its own context, making the next action more likely to follow
logically from it.

### 2. Airtap Implementation

`yoda.ts`'s per-step cycle (fully detailed in Phase 1's
[03_request_lifecycle.md](../Phase-1/03_request_lifecycle.md)) **is** this loop: conditionally
refresh device context (perceive) → build the prompt and call the LLM (think) → dispatch the chosen
tool (act) → the next step's context fetch re-observes the result (observe) → the job re-enqueues
itself if the task isn't done (repeat). Confirmed from Phase 1's research: **every tool schema
extends a common** `observe/review/plan` **chain-of-thought envelope** — this is Airtap's literal
ReAct implementation, structurally enforced by the tool schema itself (Zod), not just requested by
prompt wording.

### 3. Runtime Workflow

```text
Job Queue hands off "run next step" to the Agent Orchestrator (yoda)
   ↓
PERCEIVE: conditionally fetch fresh screenshot + UI dump
   ↓
THINK: build prompt → LLM call → model fills observe/review/plan fields, then picks ONE tool
   ↓
ACT: Tool Executor dispatches the chosen tool
   ↓
(next job) OBSERVE: next step's context fetch sees the result of that action
   ↓
Loop continues until a terminal/waiting tool call, or a safety limit is hit
```



### 4. Why Airtap Uses It

Without a forced "reason before acting" structure, a model can jump straight to a plausible-looking
but wrong action. Making the model write `observe`/`review`/`plan` fields before its tool choice —
schema-enforced, not just prompt-requested — means that reasoning is always present and always
structured the same way, which is also what makes it usable for debugging (see §5 below).

### 5. QA Perspective

- **The** `observe/review/plan` **fields are a free, structured debugging artifact.** When an agent
taps the wrong thing, read these fields (via `taskOmniDebug`/Langfuse — Phase 1) before assuming
anything about *why*: they're a direct, human-readable statement of what the model thought it was
looking at and why it chose that action.
- **Separate two different bug classes** when a step goes wrong: did it reason correctly and then
act on the wrong location (a **grounding** failure, §7), or did it reason incorrectly from the
start (a **planning/perception** failure)? These have completely different fixes, and conflating
them wastes debugging time.
- **The loop is a chain of jobs, not an in-memory loop** (Phase 1 finding) — a genuinely stuck task
(the re-enqueue never happens) isn't rescued for 24 hours by the maintenance sweep. A "stuck 10
minutes in" report is not yet at the point where anything self-heals.



### 6. Interview Mapping

- **"What is ReAct?"** → Forcing a model to write its reasoning down before every action, so the
reasoning conditions the next decision and doubles as a debugging log.
- **"What does Airtap use for it?"** → A schema-enforced `observe/review/plan` envelope on every
tool call, inside `yoda`'s per-step loop.
- **"Why was this design chosen?"** → It makes the reasoning structurally mandatory (not just
requested), and turns every step into a self-documenting artifact for debugging.
- **"What would you test?"** → Read the reasoning trace on a wrong action and classify it as a
reasoning failure or a grounding failure — they need different fixes.

---



## 3. Planning



### 1. AI Theory

Planning is decomposing a fuzzy goal into concrete steps before (or while) executing them.
Interleaved, step-by-step planning (decide the next step, act, look, decide the next) is slower per
step than committing to a full upfront plan, but far more robust — if step 3 fails, an upfront plan
is stuck with an invalid rest-of-plan, while interleaved planning simply reconsiders.

### 2. Airtap Implementation

The `ReportPlan11111` tool, enforced by the playbook (`yodaSystemPlaybook.md` §4 "Planning"): for
actionable requests, `ReportPlan` is required as an early tool call (generally the first, unless a
target app with a clear package name warrants launching it first for visible progress). The
playbook explicitly instructs keeping the plan **high-level** when a matching skill exists, rather
than locking into brittle UI steps a skill might replace. `ReportPlan` is skipped only for
greetings, small talk, or capability-only questions.

### 3. Runtime Workflow

```text
User request classified as actionable
   ↓
Playbook rule: ReportPlan required (after LaunchApp, if a target app is already clear)
   ↓
Model emits a ReportPlan tool call — visible in the task thread as the stated plan
   ↓
Skill Loading (§6) checked next, before substantive execution
   ↓
Execution proceeds step by step — NOT locked to the original plan's literal steps
```



### 4. Why Airtap Uses It

A visible, required planning step gives the user (and QA) a checkable artifact before any
irreversible action happens — and Airtap's own cheapest evaluation checks (§13) specifically grade
`ReportPlan` in isolation, exactly matching the roadmap's own recommendation ("test plan quality
before execution — you can grade a plan without ever running it").

### 5. QA Perspective

- **Plan quality is gradeable in isolation.** Airtap's eval framework already does this — a
`report_plan` check verifies the model emitted a plan, cancelling the task shortly after (a cheap,
fast correctness signal that doesn't require full task completion).
- **Watch for over-committed plans.** The playbook explicitly warns against locking into brittle UI
steps when a skill might replace them — a good regression case is a task where a skill exists but
the model's `ReportPlan` ignores it and hard-codes manual UI navigation anyway.



### 6. Interview Mapping

- **"What's the difference between upfront and interleaved planning?"** → Upfront plans the whole
sequence first (brittle if a step fails); interleaved decides one step at a time based on the
latest observation (more robust, more LLM calls).
- **"What does Airtap use?"** → A required `ReportPlan` tool call before substantive execution,
kept intentionally high-level, followed by step-by-step interleaved execution.
- **"Why was this design chosen?"** → A visible plan is auditable and cheaply gradeable, and
keeping it high-level avoids locking into steps a loaded skill might override.
- **"What would you test?"** → Whether the plan is sensible *before* running anything (Airtap's own
`report_plan` eval check is the working example), and whether the model actually follows a
matching skill instead of ignoring it.

---



## 4. Single-Agent Architecture



### 1. AI Theory

Multi-agent systems split work across several specialized LLM "agents" (planner, executor,
reviewer) that hand off to each other. They add real value when a task has genuinely separable
sub-jobs — but they're slower, costlier (more LLM calls), and every handoff is a new place for
information to get lost. The mature default is a single, well-prompted agent unless there's a
concrete reason to split.

### 2. Airtap Implementation

Confirmed single-agent: one loop (`yoda`), one model call per step, no separate planner/executor/
reviewer processes. `cortex/package.json` contains no multi-agent framework dependency (no
LangGraph, CrewAI, AutoGen/AG2, OpenAI Agents SDK, or AWS Strands) — the agent loop is fully
custom-built. `ReportPlan` (§3) and the eval framework's `llm_judge` (§13) provide *some* of the
functional flavor of planning and reviewing, but neither is a separate live agent process
participating in the task loop — planning is one tool call within the single loop, and judging only
happens in offline eval runs, not on live production tasks.

### 3. Runtime Workflow

```text
Every task, every step: ONE model call, in ONE loop (yoda), regardless of task complexity
   ↓
No handoff to a separate "planner agent" or "reviewer agent" process
```



### 4. Why Airtap Uses It

This matches the roadmap's own stated default and its own reasoning: a mobile GUI-automation task
generally doesn't split cleanly into independent specialist roles the way, say, "research this,
then write about it, then fact-check it" does — every step needs the *same* context (what's on
screen right now) and the *same* capability (decide one action). Multi-agent handoff overhead
(latency, cost, dropped context between agents) would work against a product where per-step latency
already matters.

### 5. QA Perspective

- **No handoff bugs to test for** (the multi-agent failure class simply doesn't apply here) — but
the single-agent trade-off is real: there's no independent "reviewer" catching a bad decision
before it executes, live in production. The closest thing — `llm_judge` — only runs in offline
eval, not on real user tasks. Worth being explicit about this gap when discussing production
safety nets.
- If a future change *does* introduce a second agent process (e.g., a live pre-action reviewer),
treat it as a genuinely new architecture requiring the full multi-agent testing playbook
(handoff-data-loss testing, "test the reviewer itself" by feeding it known-bad work) — none of
that exists today because there's nothing to test yet.



### 6. Interview Mapping

- **"When should you use multi-agent over single-agent?"** → Only when a task has genuinely
separable sub-jobs needing different tools/instructions, or a real independent-review win —
otherwise it's overhead without benefit.
- **"What does Airtap use?"** → Single-agent, confirmed by both the loop's own structure and the
absence of any multi-agent framework dependency.
- **"Why was this design chosen?"** → A GUI-automation step doesn't split into independent
specialist roles the way a research-and-write task does; every step needs the same context and
capability.
- **"What would you test?"** → Nothing multi-agent-specific today — but flag that there's no live,
in-production reviewer catching bad decisions before they execute, which is a deliberate
trade-off worth naming, not a hidden gap.

---



## 5. Tool Manager — Declaring What the Agent Can Do



### 1. AI Theory

"Function/tool calling" means describing a set of callable functions (name, description, argument
schema) to the model; instead of prose, the model can respond with a structured request to invoke
one of them. The model only *decides* — it never executes anything itself.

### 2. Airtap Implementation

`cortex/src/yoda/yodaTools.ts` — Zod schemas for every tool the agent can call, including a
mega-tool (`AndroidOperation`, a discriminated union covering tap/swipe/type/long-press/navigate/
launch/wait/browser-open/search-in-play-store/get-state/clipboard/uninstall...), a second
cloud-only mega-tool (`ChromeOperation`, for browser-DevTools-Protocol automation), and flat tools:
`WebSearch`, `GoogleAiMode`, `AmazonProductSearch`, `Instagram*`, `GenerateImage`/`EditImage`,
`ViewFile`, `ApkInstallTool`, `SendEmail`, `ManageRoutines`, `LoadSkill`, `ReportPlan`,
`RespondToUser`, `RequestClarification`, `RequestTakeover`. **Every tool is filtered per receiver
type** before being offered to the model — an `iosDongle` task never even sees `ChromeOperation`,
`LaunchIntent`, `GetFiles`, or `SearchAppInPlayStore` in its available tool list; a
`physical`/`androidDongle` task never sees `ApkInstallTool`, `GetClipboardData`, or `UninstallApp`.

### 3. Runtime Workflow

```text
Agent Orchestrator resolves receiver type for this task
   ↓
Tool Manager (yodaTools.ts) filters the full tool catalog down to what this receiver type supports
   ↓
Filtered schemas included in the LLM request (via omni)
   ↓
Model picks exactly one tool + fills its arguments (structured, schema-validated)
```



### 4. Why Airtap Uses It

Without tool declarations, the model could only produce prose — it has no way to touch a device,
search the web, or send an email on its own. Filtering the catalog per receiver type also directly
prevents an entire class of bug: an iOS dongle task literally cannot be offered a Chrome-CDP tool
that its receiver has no way to execute, because the tool never appears in its prompt in the first
place.

### 5. QA Perspective

- **Verify the filtering, not just the tools.** The highest-value regression test here isn't "does
`Tap` work" — it's "does an `iosDongle` task's tool list actually exclude `ChromeOperation`" —
test the *exclusion* per receiver type, since a leaked tool would be offered to a model that has
no way to actually execute it.
- **New tool checklist**: confirm a newly added tool is both declared here *and* reachable from the
Tool Executor (§6) — a tool declared but never wired to a handler would be silently unusable.
- **Argument schema validation**: per `omni`'s contract, tool arguments are validated against the
declared schema and fail fast on mismatch — test malformed/boundary arguments (empty strings,
wrong types) and confirm this fails loudly rather than passing through.



### 6. Interview Mapping

- **"What is a tool schema?"** → A declared name, description, and argument shape that tells the
model what it can ask for and how.
- **"What does Airtap use?"** → Zod-defined tool schemas in `yodaTools.ts`, filtered per receiver
type before every call.
- **"Why was this design chosen?"** → Per-receiver-type filtering prevents the model from ever
choosing a tool its current device physically can't execute.
- **"What would you test?"** → That tool availability is correctly excluded/included per receiver
type, and that every declared tool actually has a working execution path.

---



## 6. Tool Executor — Actually Running the Chosen Tool



### 1. AI Theory

The model only *requests* a tool call; trusted application code is what actually runs it and
returns a result. This split — model proposes, code disposes — is the entire safety and testing
story for tool calling.

### 2. Airtap Implementation

`cortex/src/android/androidActions.ts`'s `AndroidActionRegistry` — a flat, in-memory
`Map<toolName, handler>` populated at boot via `.register(name, description, handler, {requiresReceiver})`. This single registry dispatches **every** tool the model can call, not just
device-touching ones — `yoda.ts` calls `androidActionRegistry.execute(ctx, toolUse, ...)`
generically regardless of whether the tool is `AndroidOperation`, `WebSearch`, or `GenerateImage`.
The `requiresReceiver` flag on each registration determines whether a live device/session must be
resolved before the handler runs — device-touching tools branch onward to the Automation Layer
(§8); non-device tools (web search, image generation, email) call their target API directly.

### 3. Runtime Workflow

```text
LLM response includes exactly one tool call (name + validated arguments)
   ↓
Tool Executor (AndroidActionRegistry) looks up the handler by tool name
   ↓
If requiresReceiver: resolve the live Android instance/session first
   ↓
Handler runs — either dispatching to the device (Automation Layer, §8) or calling an external API directly
   ↓
Result returned, persisted with the step, and folded into the next prompt as a tool_result
```



### 4. Why Airtap Uses It

This is the concrete implementation of "the model proposes, the code disposes" — the model can
never directly touch a device or an external system; every single effect happens through code
Airtap owns and controls. It's also what makes device-touching and non-device tools uniform from
the orchestrator's point of view — `yoda` doesn't need special-case logic per tool, just one
generic `execute()` call.

### 5. QA Perspective

- **Three independent failure classes to test, per the roadmap's own framing**: wrong tool
selected, malformed/hallucinated arguments, and the tool executing but the model ignoring or
mishandling its result. Test each separately — they have different root causes.
- **Unknown-tool handling**: confirm a call to an unregistered tool name fails explicitly (per
`omni`'s "unknown tool use fails explicitly" contract requirement) rather than being silently
swallowed.
- **The scariest bug class**: a *plausible-looking* tool call with a subtly wrong or
attacker-influenced argument (see prompt injection in
[08_prompt_pipeline.md](08_prompt_pipeline.md)) — test argument correctness as hard as tool
selection, not just "did it pick the right tool."



### 6. Interview Mapping

- **"Does the LLM execute the tool itself?"** → No — it only requests; trusted code executes and
returns the result. This split is the entire safety story.
- **"What does Airtap use to execute tools?"** → One generic dispatch registry
(`AndroidActionRegistry`) handling every tool type uniformly.
- **"Why was this design chosen?"** → Uniform dispatch means the orchestrator doesn't need
special-case logic per tool, and keeps the "model proposes, code disposes" boundary in exactly
one place.
- **"What would you test?"** → Tool selection correctness, argument correctness, and result
handling — as three separate test surfaces, not one.

---



## 7. Screen Understanding & Grounding



### 1. AI Theory

**Screen understanding** is how the agent perceives a screen: raw vision (a screenshot, read like a
human would) versus the OS's accessibility tree (structured element data — text, bounds,
clickability). **Grounding** is the separate, harder problem of connecting a *decision* ("tap
login") to an actual pixel the OS can act on. A model can be completely right about *what* to do and
still wrong about *where* — a failure category with no equivalent in classical test automation,
since a selector either resolves or it doesn't; it can't be "approximately right."

### 2. Airtap Implementation

Confirmed **hybrid** screen understanding: the playbook (`yodaSystemPlaybook.md` §6.3) explicitly
instructs using "the current screenshot image **together with** the UI dump" to verify state and
choose coordinates — vision and structured state feed the same decision, matching the roadmap's own
recommended real-world pattern. Grounding is confirmed **coordinate-based**: the `Tap`/related
action schemas take `coordinates: [x, y]` directly (verified in `yodaTools.ts`), and `mreg`'s
`androidCoordinateMode` field configures which coordinate space a given model expects
(`devicePixels`, `normalized1000`, or `preprocessedVisionPixels`) — the system, not the model,
handles the final unit conversion, but the model itself is still estimating a pixel/normalized
position from what it sees, not selecting a labeled element node. No evidence of **Set-of-Marks**
(numbered-box overlay) prompting was found anywhere in the codebase — grepped specifically for it
and found nothing.

### 3. Runtime Workflow

```text
Device context fetch: screenshot + UI dump captured together
   ↓
Both included in the LLM prompt (image content part + structured text)
   ↓
Model decides an action AND estimates where: coordinates: [x, y]
   ↓
mreg's androidCoordinateMode tells the system how to interpret those numbers for this model
   ↓
Tool Executor dispatches the tap at the resolved coordinate — no OS-level "find element by ID" step
```



### 4. Why Airtap Uses It

Pure vision-only coordinate guessing is exactly the failure mode the roadmap warns about — models
are "genuinely bad at precise spatial estimation" from an image alone. Giving the model the UI dump
*alongside* the screenshot gives it structured, textual grounding cues (positions, labels, bounds)
to sharpen its coordinate estimate, without requiring every app to expose a perfect accessibility
tree (which many don't — canvas apps, games, custom-rendered views). It's a deliberate middle
ground: cheaper and more universal than a full element-selection system that only works when the
tree is complete, more accurate than vision alone.

### 5. QA Perspective

- **This is the single highest-value test category from the whole roadmap for this product.**
Grounding accuracy should be measured as its **own** metric — "given a correct decision, did the
tap land on the correct element?" — not buried inside overall task success, because a task can
succeed despite a grounding miss (the agent retries and eventually lands right) and that's a
fragility signal, not a pass.
- **Never verify by screenshot-diffing.** Verify by checking actual resulting app/device state —
this is explicitly why AndroidWorld (the published benchmark Airtap does *not* use, but whose
design principle is worth adopting) is considered reproducible: it inspects real state, not
pixels. A theme change, a notification banner, or a battery-percentage change breaks a pixel-diff
"assertion" that was never really testing the right thing.
- **Test apps with sparse/empty accessibility trees deliberately** (games, canvas, WebViews,
poorly-built apps) — this is precisely where the vision half of the hybrid has to carry the whole
decision, and where grounding failures concentrate.
- **Different screen sizes/resolutions/keyboard-popup layout shifts** are classic coordinate-based
grounding failure triggers — test across device form factors, not just one reference device.
- **Different models can have different coordinate accuracy** (§2 of
[05_llm_usage.md](05_llm_usage.md)) — re-verify grounding specifically after any model-routing
change.



### 6. Interview Mapping

- **"What's grounding, and why is it hard?"** → Connecting a model's decision to an actual screen
location; hard because the model can be exactly right about *what* to do and only approximately
right about *where* — and approximately right is simply wrong for a tap coordinate.
- **"What does Airtap use for grounding?"** → Coordinate-based tap targets, informed by both a
screenshot and a structured UI dump together — not element-ID selection, not Set-of-Marks.
- **"Why was this design chosen?"** → Coordinate output works on anything the model can see,
including apps with poor or missing accessibility trees; the UI dump sharpens accuracy without
requiring every app to expose one.
- **"What would you test?"** → Grounding accuracy as an isolated metric (not buried in task
success), verified against real device/app state, specifically on apps with sparse accessibility
metadata and across different screen sizes.

---



## 8. Action Space & Automation Layer



### 1. AI Theory

The action space is the complete list of moves an agent may make — smaller is more reliable, since
every extra action is another thing the model can pick wrongly, and there must be an explicit "I'm
done" action or the agent has no way to know when to stop. Underneath the model's decision, some
real automation layer actually executes it on the device — common names: ADB, UI Automator, Appium,
XCUITest.

### 2. Airtap Implementation

The action space is deliberately bounded (per Phase 1's tool inventory): tap, swipe, type,
long-press, navigate back/home, launch app, open browser, wait, plus device-state queries
(clipboard, files, current app). The explicit "done" action is `RespondToUser` (task complete),
with `RequestClarification`/`RequestTakeover` as the two "I need a human" exits. **The automation
layer underneath is confirmed NOT ADB.** Every ADB-related string found in the Android receiver's
source is a comment describing something the app *deliberately doesn't rely on* — e.g., a note that
a certain developer-settings action would need "ADB access" (framed as a limitation, not a
mechanism used), and a Firebase Analytics debug-mode setup instruction meant for engineers testing
the app during development, unrelated to the runtime automation path. The real automation layer is
Android's **Accessibility Service** API (`physical` receiver type) and/or the **HID dongle**
(`androidDongle`/`iosDongle` receiver types) — see Phase 1's Device Layer documentation
(`receiver`/`receiver-ios`) for the full mechanics.

### 3. Runtime Workflow

```text
Tool Executor resolves a device action needs to happen
   ↓
Device Command Router picks the channel (cloud HTTP, or device RPC — Phase 1, doc 02)
   ↓
On-device Android/iOS Controller receives the command
   ↓
EITHER: Accessibility Service API call (physical Android)
    OR: encoded HID packet sent over BLE to the dongle → real USB keyboard/mouse/touch signal (dongle receivers)
   ↓
Device state changes; next perceive step observes the result
```



### 4. Why Airtap Uses It

ADB requires the target device to have USB debugging / developer mode enabled — a real end-user's
personal phone will not have this on, and requiring it would be a non-starter for the product's
actual audience. Accessibility Service is a legitimate, no-developer-mode-required Android API
(the same one screen readers use). The HID dongle goes a step further: it makes the automation
**genuinely indistinguishable from a human using real hardware**, which matters for apps that try
to detect and block software-level automation — and it's the *only* option on iOS, which has no
Android-Accessibility-Service equivalent for programmatic input injection.

### 5. QA Perspective

- **This is a strong, concrete connection point to classical mobile QA background**: Appium/ADB
experience explains the *shape* of the problem (an automation layer under a decision-maker) even
though Airtap's actual mechanism is deliberately not ADB-based — worth being precise about that
distinction rather than assuming ADB is involved.
- **Constrain-the-action-space testing**: every extra action type is more failure surface — if a
new action is proposed, ask whether an existing one already covers the need before adding it.
- **The explicit "done" action matters**: verify `RespondToUser` is reliably reachable and that a
task can't get stuck perpetually deciding it isn't done yet (ties to §10's loop-avoidance).
- **Physical hardware failure modes have no software equivalent** — BLE range, dongle battery, USB
contact, Accessibility Service permission revocation — see Phase 1's Device Layer documentation
for the full, code-verified list; these need to be tested on real hardware, not reasoned about.



### 6. Interview Mapping

- **"What's underneath a mobile agent's tap decision?"** → Some automation layer that translates a
decision into a real OS/hardware action — commonly ADB, Accessibility APIs, or dedicated hardware.
- **"What does Airtap use?"** → Android Accessibility Service and/or a physical BLE-to-USB HID
dongle — explicitly not ADB.
- **"Why was this design chosen?"** → ADB needs developer mode enabled, which a real user's phone
won't have; Accessibility Service needs no such setup, and the HID dongle additionally makes
input genuinely indistinguishable from a human (and is the only option at all on iOS).
- **"What would you test?"** → Whether the action space stays minimal and the `done` action is
always reachable; separately, physical-hardware failure modes (BLE range, dongle battery,
permission revocation) on real devices.

---



## 9. The Rule-Based Shortcut: `android-direct-actions`



### 1. AI Theory

Not every action needs AI-driven visual grounding. When a deterministic mechanism already exists
for a well-defined action (an exact-match database lookup instead of a vector search; a native OS
API instead of visually finding and tapping a button), using the deterministic path is faster,
cheaper, and immune to grounding failure entirely — the same principle behind "you don't need a
vector DB for exact-match ID lookups" (Phase 4–6 of the roadmap), applied to actions instead of
data retrieval.

### 2. Airtap Implementation

The `android-direct-actions` skill (`cortex/src/skills/definitions/android-direct-actions.md`)
exposes a `LaunchIntent` tool that fires native Android Intents directly — `SET_ALARM`,
`DIAL`/`CALL`, `SENDTO` (SMS/email), `VIEW` (web/map search), direct settings-screen intents,
camera/media capture, contact/calendar creation — instead of visually navigating to and tapping
through each of those flows. The skill's own decision rules explicitly favor the deterministic path
("if Android already provides a direct intent for the user goal, prefer that path before attempting
step-by-step navigation") and explicitly favor the *safer* variant of an intent when one exists
(`DIAL` over `CALL`, so the number is prefilled but not auto-dialed, unless the user explicitly
wants the call placed immediately). **This skill is deliberately hidden for dongle receivers** —
`LaunchIntent` requires actual Android API-level access to call `startActivity()`, which only the
Accessibility-Service-based `physical` receiver type has; a dongle only emits simulated hardware
signals and has no way to invoke an OS intent programmatically.

### 3. Runtime Workflow

```text
User: "Set an alarm for 7:30 tomorrow"
   ↓
Playbook's Skill Loading step recognizes a matching skill
   ↓
LoadSkill("android-direct-actions") — full playbook injected
   ↓
Model emits LaunchIntent(action: SET_ALARM, extras: [HOUR, MINUTES, MESSAGE])
   ↓
Deterministic Android intent fires directly — no screenshot, no tap coordinates, no grounding step at all
```



### 4. Why Airtap Uses It

For a well-defined action like setting an alarm, visually finding the clock app, tapping the "+"
button, setting the hour and minute wheels, and confirming is slow and has multiple grounding
opportunities to fail. A direct intent is a single deterministic call with no vision, no
coordinates, and no way to "almost" work — it either fires correctly or fails explicitly on a
malformed parameter. This is a genuine instance of choosing the cheaper, more reliable tool when
one is available, rather than defaulting to AI-vision grounding for everything.

### 5. QA Perspective

- **A different, much simpler test surface than the vision path**: since there's no grounding step,
correctness testing here is closer to classical API testing — right action string, right extras,
right data URI shape — not screenshot/coordinate verification at all.
- **Confirm the hidden-for-dongle behavior holds**: a dongle-receiver task asking to "set an alarm"
should fall back to the normal vision-and-tap path, not silently fail by trying to call a tool it
was never offered.
- **Irreversibility awareness is written into the skill itself**: `CALL` (places the call
immediately) vs. `DIAL` (prefills only) is a real, deliberate safety choice worth explicitly
testing — confirm the model defaults to `DIAL` unless the user was unambiguous about wanting the
call placed.
- **Best-effort settings screens**: the skill's own notes acknowledge some settings intents don't
exist on every device/OEM — worth confirming failure here is graceful, not a hard crash.



### 6. Interview Mapping

- **"When would you skip the AI-vision path entirely?"** → When a deterministic API already exists
for the exact action — same principle as skipping a vector DB for an exact-match lookup.
Grounding failures literally can't happen if there's no grounding step.
= **"What does Airtap use for this?"** → A skill (`android-direct-actions`) that fires native
Android Intents directly for well-defined actions (alarms, calls, SMS, settings, calendar),
bypassing visual tap-based navigation entirely.
- **"Why was this design chosen?"** → Faster, cheaper, and immune to grounding failure for actions
that have a clean deterministic equivalent; also deliberately prefers the safer intent variant
for anything irreversible.
- **"What would you test?"** → API-style correctness (right intent, right extras) rather than
visual verification, plus confirming this path is unavailable — and gracefully so — on dongle
receivers that can't invoke it.

---



## 10. Decision Making, Retry Logic & Loop Avoidance



### 1. AI Theory

An agent needs to handle failure gracefully — retry sensibly, not infinitely — or it becomes what
the roadmap calls "a bug with a budget": something that can tap the same broken button hundreds of
times, burning cost overnight, with no natural stopping point.

### 2. Airtap Implementation

Two distinct layers, confirmed in Phase 1's research: **prompt-level** guidance (the playbook's
§6.2 "Progress and loop avoidance" — explicitly instructs comparing the current UI dump/screenshot
against the prior step, treating repeated screens/popups/unchanged items as no progress, and
changing strategy rather than repeating an action pattern) and **code-level** hard limits (a bounded
retry window for specific infrastructure error types, an overall per-task step cap, and a 24-hour
maintenance sweep that force-fails tasks stuck in an executing/waiting state). The loop-avoidance
logic itself is prompt-level only — there is no code-level circuit breaker that detects "the same
action fired 3 times in a row" and intervenes automatically.

### 3. Runtime Workflow

```text
After every device action:
   ↓
Playbook rule: compare current UI dump/screenshot against the prior step
   ↓
Repeated/unchanged state? → model is instructed to change strategy, not repeat the action
   ↓
(separately, code-level) step count checked against the overall per-task cap
   ↓
(separately, code-level) infrastructure errors checked against a bounded retry window
   ↓
(separately, code-level) a task stuck 24h in an active state gets force-failed by the maintenance sweep
```



### 4. Why Airtap Uses It

Without any of this, a confused agent on a genuinely stuck UI (a broken button, a modal that won't
dismiss) would either loop until it hits an unrelated cost ceiling, or never resolve at all. Layering
prompt-level self-awareness with code-level hard limits covers both "the model recognizes it's stuck
and changes tack" (the common case) and "the model doesn't recognize it" (the safety net).

### 5. QA Perspective

- **The prompt-level loop-avoidance instruction is NOT code-enforced** — this is a genuine,
legitimate place to find real AI-quality bugs (not backend bugs) by constructing deliberately
repetitive or dead-end UI flows and confirming the model actually changes strategy rather than
repeating itself.
- **The self-healing window is hours, not minutes.** A task that looks hung ten minutes in is not
yet within reach of the 24-hour stale-task sweep — don't assume something will auto-recover
quickly just because a safety net exists somewhere.
- **Cost-ceiling testing**: assert an upper bound on steps/tokens per task as a first-class test,
not a performance nit — per the roadmap, a step-count explosion is a P1-class defect for an agent
product, not a minor inefficiency.



### 6. Interview Mapping

- **"How do you stop an agent from looping forever?"** → Layer prompt-level self-awareness (compare
state, change strategy on no progress) with code-level hard limits (max steps, bounded retries, a
stale-task sweep as a last resort).
- **"What does Airtap use?"** → Exactly that combination — playbook-level loop-avoidance
instructions plus code-level step caps, retry windows, and a 24-hour stale-task sweep.
- **"Why was this design chosen?"** → The prompt-level layer handles the common case efficiently
(the model self-corrects); the code-level layer is the guaranteed backstop for when it doesn't.
- **"What would you test?"** → Deliberately repetitive/dead-end UI flows (does the model actually
change strategy?), and the boundary behavior of the hard limits themselves (does the cap actually
fire, and does "stuck" get force-failed within the documented window, not sooner or never?).

---



## 11. Success at Two Levels, and Risk-Tiering Actions



### 1. AI Theory

Success has to be measured at two levels that can come apart in both directions: **action-level**
(did this individual tap do the right thing?) and **task-level** (did the whole goal get
accomplished?). An agent can execute every action flawlessly while working the wrong overall plan,
or fumble several actions and still stumble into the right final state — the second case is
especially dangerous, because it looks like success while actually being fragile. Because mistakes
here are often *irreversible* (a sent message, a purchase, a deletion — no "regenerate response"
button), the mature response is to risk-tier the action space: safe to fully automate, gated behind
a confirmation, or not yet safe to automate at all.

### 2. Airtap Implementation

Both `ReportPlan` (task-level plan, graded independently — §3) and per-step tool execution
(action-level, individually validated) exist as distinct artifacts, so action-level and task-level
correctness genuinely *can* be inspected separately using what the system already records. **Formal
risk-tiering was not confirmed as a system-enforced mechanism.** What was found: the playbook's
general guardrails (never hallucinate credentials; treat visible app state as untrusted until
verified) and the `android-direct-actions` skill's explicit preference for the safer variant of an
intent when one exists (`DIAL` over `CALL`) — both real, but neither is a formal, code-enforced
classification that, say, automatically forces `RequestClarification` for any tool call resembling
a purchase or deletion, regardless of which app it's in. `RequestClarification` and
`RequestTakeover` exist as available exits, but invoking them for a risky action is a model
judgment call in the moment, not a hard system gate.

### 3. Runtime Workflow

```text
Model chooses an action
   ↓
No system-level classification tags this action as safe / needs-confirmation / forbidden
   ↓
The model's own judgment (shaped by playbook guardrails) decides whether to act,
   or to call RequestClarification / RequestTakeover instead
```



### 4. Why Airtap Uses It (and the honest gap)

Measuring both levels is straightforward with what's already recorded (steps + plan), so that part
is a real, deliberate design choice worth using. The absence of a formal, code-enforced risk tier is
worth stating plainly rather than glossing over — the roadmap frames this specific pattern (🟢 safe
to automate / 🟡 confirm first / 🔴 not yet autonomous) as **the single strongest answer** a
QA-background candidate can give in this space, precisely because most systems (Airtap included, on
current evidence) lean on model judgment rather than a hard gate for this. Naming the gap
accurately is more valuable than claiming a protection that wasn't found.

### 5. QA Perspective

- **This is the single highest-blast-radius test category for the whole product.** Test coverage
should be deepest exactly here — the same instinct as testing a payment flow harder than a
settings screen, applied to a system where the "payment flow" could be any tool call the model
chooses to make.
- **Concrete test to run**: construct tasks that plausibly lead toward an irreversible action (a
purchase, a delete, a message send, a permission grant) and confirm what actually happens today —
does the model pause and ask, or proceed? Since no hard gate was confirmed, this behavior is
currently a property of model judgment and prompting, which means it can vary by model (see
[05_llm_usage.md](05_llm_usage.md) on model routing) and is worth re-verifying after any
model-routing change, not just once.
- **Task-level vs. action-level, concretely**: a good regression test deliberately breaks one step
mid-task (simulate a wrong tap) and checks whether the agent recovers cleanly or "succeeds" by
accident through a route that won't hold up next time.



### 6. Interview Mapping

- **"Why measure action-level and task-level success separately?"** → An agent can look successful
by luck (task succeeded despite wrong actions) or look broken while actually being on-plan
(actions right, wrong overall app/target) — conflating the two hides real fragility.
- **"Does Airtap risk-tier its actions?"** → Partially, informally — guardrails and
safer-intent-variant preferences exist in the prompt layer, but no formal, code-enforced
three-tier gate (safe/confirm/forbidden) was found in this investigation.
- **"Why does this matter?"** → GUI-agent mistakes are often irreversible — there's no "regenerate
response" for a sent message or a completed purchase.
- **"What would you test?"** → Deliberately construct tasks approaching an irreversible action and
verify what actually happens today; treat this as the deepest, highest-priority test surface in
the entire product, and re-verify it whenever the underlying model changes.

---



## 12. Reflection & Self-Correction



### 1. AI Theory

Reflection is the agent checking its own last action or output and fixing it if wrong. It works
well against an **external, objective signal** (code didn't compile → fix it; a tap produced no
screen change → retry differently) and works badly when a model grades its own subjective judgment
with no outside signal — a model that was wrong for a reason tends to be wrong again for the same
reason when asked to simply "check itself."

### 2. Airtap Implementation

No dedicated, separate "reflection pass" (a second LLM call whose only job is critiquing the first)
was found in the main task loop. What exists instead: prompt-level self-verification instructions
baked into the same single decision call (playbook §6.4, "treat any visible app state as untrusted
until the key task-defining fields are verified against the current user request") and heuristic,
code-level detection of at least one specific known failure state (recognizing a Google Play
sign-in wall directly from the screenshot and routing to `WAITING_FOR_USER_INTERVENTION` even
without an explicit model tool call requesting it — a Phase 1 finding). Both are real, but neither
is the roadmap's canonical "reflection" pattern of a distinct critique step reviewing a separate
prior action.

### 3. Runtime Workflow

```text
Same decision call that chooses the next action ALSO carries self-verification instructions
   ↓
("is this the correct app/surface? do the key fields match the request?")
   ↓
Separately, and in parallel: specific known bad states (e.g. a login wall) are detected
   heuristically at the code level, independent of what the model itself concluded
```



### 4. Why Airtap Uses It

A fully separate reflection pass would add a full extra LLM call (and its cost/latency) to *every*
step, for a benefit the roadmap itself is skeptical of when there's no external signal to check
against. Folding self-verification into the same call is cheaper; the heuristic backstop for at
least one well-known failure state (the login wall) adds a real external-signal check for that
specific, high-frequency case without paying for a general-purpose reflection call everywhere.

### 5. QA Perspective

- **This is a real, evidence-based gap worth testing directly**, not assuming exists: construct a
scenario where the agent's self-verification *should* catch a mismatch (wrong account selected,
stale pre-filled field) and confirm whether it actually does, since this depends entirely on the
main decision call getting it right in a single pass — there's no second, independent check
behind it for the general case.
- **The login-wall heuristic is a good template for testing other known failure states**: if a new
common blocker is identified (e.g., a specific paywall or CAPTCHA pattern), check whether it gets
the same code-level heuristic backstop, or whether it currently relies purely on the model
noticing on its own.



### 6. Interview Mapping

- **"What's the risk with self-correction?"** → Without an external signal, a model checking its
own work tends to just agree with itself — the same weakness that makes it a biased judge (§13).
- **"What does Airtap use?"** → Self-verification folded into the same decision call (not a
separate reflection pass), plus a code-level heuristic backstop for at least one specific known
failure state.
- **"Why was this design chosen?"** → A full separate reflection call would double the cost/latency
of every step for a benefit that's weak without an external signal; a targeted heuristic for a
known bad state is cheaper and more reliable for that specific case.
- **"What would you test?"** → Whether single-pass self-verification actually catches a deliberately
planted state mismatch — this is the part of the system with the least independent backup if the
main decision call gets it wrong.

---



## 13. The Evaluation Layer



### 1. AI Theory

An eval is a test where the assertion is a judgment call rather than an exact match, because the
same correct behavior can look different across runs. **LLM-as-judge** — using a strong model to
grade another model's output against a rubric — is the modern default technique when there's no
single ground-truth string to compare against. For agents specifically, Task Success Rate (TSR) is
the headline number, but step accuracy and trajectory match matter too, because TSR alone hides an
agent that stumbles into the right answer through a fragile, lucky path.

### 2. Airtap Implementation

`cortex/src/eval/` — a real, working evaluation framework, detailed in Phase 1's
[04_system_components.md](../Phase-1/04_system_components.md). A curated dataset
(`evalTaskDataset.v2.json`, ~50+ cases) defines ordered assertions per case, each `must_have`
(blocking) or `good_to_have` (scored, non-blocking): `report_plan` (did the model emit a plan —
most current cases are this cheap, plan-only type), `final_output_contains`/`_not_contains`
(substring/regex on the final visible response), and `llm_judge` (a separate model, default
`gemini-3-flash-preview`, answers yes/no questions against the full sanitized task trace — every
question must be `true` for the check to pass; this is the **reference-free** judge pattern, not
pairwise comparison or reference-based scoring). Runs execute through the **real** task engine
(`taskCreateCore`, etc. — not a simulated harness), triggered on-demand from an internal Pilot
screen (`/evals`), gated by an `eval:access` permission. Reports include per-case and aggregate
cost/latency/token stats, so an eval run doubles as a lightweight performance check alongside
correctness.

### 3. Runtime Workflow

```text
Engineer triggers a run from Pilot's /evals screen (POST evalRun)
   ↓
evalTaskRunner creates a REAL task per case via taskCreateCore, using the real Agent Orchestrator
   ↓
Task runs exactly as a live user's would (same yoda loop, same tools)
   ↓
Checks evaluated against the resulting trace: report_plan / final_output_contains / llm_judge
   ↓
Judge model (via omni) scores llm_judge questions independently
   ↓
Report generated: pass/fail per check, judge evidence, aggregate cost/latency/tokens
```



### 4. Why Airtap Uses It

Non-deterministic agent behavior can't be regression-tested with exact-match assertions — running
real tasks against a curated dataset and grading them with a mix of cheap deterministic checks and
LLM-judge questions is the practical, working answer to "how do you know a prompt or model change
didn't quietly make the agent worse." Running the *real* task engine (rather than a mocked
simulation) means the eval is testing the actual production code path, not an approximation of it.

### 5. QA Perspective

- **The single biggest gap, already identified in Phase 1**: there is no CI hook or schedule that
triggers eval runs automatically — it's purely on-demand. This means a model or prompt change can
ship without anyone running an eval pass first; this is the most direct, concrete instance of the
roadmap's "Eval Ops" concept (evaluation as a continuous pipeline, not a pre-launch script) **not
yet being fully realized** in this product. Flagging this — and, if relevant, proposing/verifying
a CI or scheduled trigger — is a genuinely high-leverage QA contribution here.
- **Most current cases are** `report_plan`**-only** — a cheap, pre-execution signal, not full
task-completion verification. Don't assume a passing eval run means every case was verified
end-to-end; check which check types a given case actually uses.
- **No confirmed mitigation for known judge biases** (verbosity, position, self-preference, judge
drift) — worth testing directly: does a longer, padded answer score better on an `llm_judge`
check than a correct, concise one? Does upgrading the judge model shift historical scores,
breaking baseline comparability?
- **No formally named step-accuracy or trajectory-match metric** was found distinct from the
existing checks — if trajectory fragility (right answer, wrong/lucky path) is a concern, that's
currently not something the eval framework measures directly; it would need to be added or
checked manually via the reasoning trace (§2).
- **This is Airtap's own build, not a third-party tool** — no Promptfoo/DeepEval/RAGAS/LangSmith/
Braintrust dependency exists; don't assume any of those tools' specific behaviors or CLIs apply
here.



### 6. Interview Mapping

- **"What's LLM-as-judge, and what are its failure modes?"** → Using a strong model to grade output
against a rubric when there's no exact answer; known biases include favoring longer answers
(verbosity bias), favoring whichever option is seen first in a comparison (position bias), and
scores drifting silently when the judge model itself is upgraded.
- **"What does Airtap use for evaluation?"** → A custom-built framework (`cortex/src/eval`) running
real tasks through the real task engine against a curated dataset, graded by a mix of
deterministic checks and a reference-free LLM judge.
- **"Why was this design chosen?"** → Running the real task engine tests the actual production path,
not an approximation; a curated dataset with typed checks fits the roadmap's own "distribution of
acceptable behavior, not exact match" testing philosophy for non-deterministic systems.
- **"What would you test?"** → Whether the eval framework itself has blind spots — no automatic
trigger (a real gap), no confirmed judge-bias mitigation, and mostly plan-level (not full
completion) checks in the current dataset. Testing the eval system's own limitations is exactly
the kind of judgment a QA background brings that a typical AI-engineer candidate wouldn't
naturally reach for.

---

**Next:** [07_memory_and_context.md](07_memory_and_context.md) — how Airtap remembers things across turns, tasks, and sessions.