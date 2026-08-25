# 04 — System Components

*Phase 1 · Document 4 of 4. Assumes you've read [01](01_project_overview.md),
[02](02_high_level_architecture.md), and [03](03_request_lifecycle.md).*

Documents 2 and 3 explained the system as a *story* — how the pieces connect, and what happens
when you follow one task through them. This document is the opposite shape on purpose: a flat,
scannable **reference catalog** of every major component that actually participates in a live user
request, one consistent profile each, so you can jump straight to "the Tool Executor" or "the
Android Controller" without re-reading a narrative.

Every component below was confirmed directly in the repository — nothing here is a guess at what
"should" exist based on typical AI-agent architectures. Where a commonly expected piece (a
dedicated Planner, a standalone Safety Layer, a standalone Retry module, a Request Router separate
from the API layer) does **not** exist as its own component, that's called out explicitly in the
closing section rather than left for you to discover by searching for a file that isn't there.

## How this catalog is organized

Components are grouped in roughly the order a request passes through them, split into seven
sections. Sections A–C and E–G are general request-handling and platform plumbing; **Section D is
where AI-specific concepts begin** — deliberately kept separate so you have a solid, non-AI system
map before layering agent concepts on top of it.

| # | Component | Lives in |
|---|---|---|
| **A. Entry Points** | | |
| 1 | Pilot Web | `pilot/` |
| 2 | Pilot iOS | `pilot-ios/` |
| 3 | Telegram Bot Integration | `cortex/src/tg/` |
| 4 | Messaging Integration (iMessage / SMS / RCS) | `cortex/src/linq/` |
| **B. API & Access Layer** | | |
| 5 | API Layer | `cortex/src/srv/`, `cortex/src/at/` |
| 6 | Auth Layer | `cortex/src/auth/`, `cortex/src/user/userPersonalAccessToken.ts` |
| **C. Task Engine** | | |
| 7 | Task Manager | `cortex/src/task/` |
| 8 | Job Queue & Background Workers | `cortex/src/jq/` + job definitions across modules |
| **D. Agent Orchestration & AI Core** | | |
| 9 | Agent Orchestrator | `cortex/src/yoda/yoda.ts`, `yodaJobs.ts` |
| 10 | Prompt Builder | `cortex/src/yoda/` (prompt assembly) + `cortex/src/templates/` |
| 11 | Context Manager | `cortex/src/yoda/yodaConversationHistory.ts`, `yodaCompaction.ts` |
| 12 | Model Registry | `cortex/src/mreg/` |
| 13 | LLM Provider Layer | `cortex/src/omni/` |
| 14 | Memory | `cortex/src/umem/` |
| 15 | Skill Registry | `cortex/src/skills/` |
| 16 | Tool Manager | `cortex/src/yoda/yodaTools.ts` |
| 17 | Tool Executor | `cortex/src/android/androidActions.ts` |
| **E. Device Communication & Control** | | |
| 18 | Device Command Router | `cortex/src/android/androidExecuteCommand.ts`, `androidInteractions.ts`, `androidGetInstance.ts` |
| 19 | Receiver Management & RPC | `cortex/src/rcvr/` |
| 20 | Cloud Phone Orchestrator Client | `cortex/src/orch/` |
| 21 | Android Controller | `receiver/` |
| 22 | iOS Controller | `receiver-ios/` |
| 23 | HID Dongle | `receiver/usbhidlib/`, `receiver-ios/Receiver/HidInput.swift` (+ physical hardware) |
| **F. Data & Storage** | | |
| 24 | Database | `cortex/src/ddb/` (Firestore) |
| 25 | Cache | `cortex/src/mdb/` (Redis) |
| 26 | Blob Storage | `cortex/src/img/` (S3) |
| **G. Cross-Cutting: Observability, Safety, Evaluation** | | |
| 27 | Logging | `cortex/src/log/` |
| 28 | Error Monitoring | Sentry, wired in `cortexInit.ts` + `pilot/`, `website/` |
| 29 | Telemetry & Tracing | `cortex/src/omni/omniLangfuseSetup.ts`, `omniTracing.ts` |
| 30 | Task Debug & Trace Capture | `cortex/src/task/taskOmniDebug.ts`, `taskYodaTrace.ts`, `taskStateTimeline.ts` |
| 31 | Retry Handling | `cortex/src/yoda/yodaJobs.ts` (embedded, not a standalone module) |
| 32 | Safety & Guardrails | Distributed (see profile) |
| 33 | Evaluation Layer | `cortex/src/eval/` |
| 34 | Analytics Event Publishing | `cortex/src/stats/` |

**Deliberately out of scope** (real, but don't participate in a live task request): the marketing
`website/`, the waitlist-signup `subscriber/` module, `task-analysis-producer/` (analyzes tasks
after the fact, offline), `web-automation/` (a test project, not a runtime component),
`agent-skills/airtap` (a Claude Code skill for driving Airtap externally), and `dash/` (internal
reporting queried on demand by staff, not triggered by or participating in any individual user's
task).

---

## A. Entry Points — Where a User Request Originates

### 1. Pilot Web

**What it is:** The primary web application end users and internal staff use to create tasks,
watch them run, pair devices, and manage routines.
**Why it exists:** The main product surface — without it, the only ways to reach Airtap are
Telegram, texting, or the iOS app.
**Where it lives:** `pilot/` (Next.js app; task UI in `pilot/components/task-details/`,
`pilot/components/message-composer/`; API client in `pilot/lib/tasks/`, `pilot/lib/app-api.ts`).
**Technology:** Next.js 16, React 19, TypeScript, Firebase Web SDK (Firestore listeners, FCM),
Sentry.
**Input:** User keystrokes/attachments/voice in the composer; Firestore "ping" documents;
REST responses from Cortex.
**Output:** HTTPS calls to Cortex's API Layer (`taskCreate`, `taskAddUserMessage`,
`taskQueueUserMessage`, `rtnCreate`, `rcvrGetPairingCode`, ...); rendered UI.
**Calls next:** API Layer (`srv`) for every action; Database (Firestore) directly, read-only, for
realtime "ping" listeners.
**How QA should validate it:**
- Confirm the realtime staleness banner appears when the Firestore connection is degraded (e.g.
  throttle/disconnect the network mid-task) and clears correctly on reconnect.
- Confirm an un-refreshed tab correctly surfaces a version-conflict error after a backend deploy,
  rather than failing silently.
- Exercise the composer's three input modes (text, attachment, voice) and confirm each reaches the
  backend correctly.

### 2. Pilot iOS

**What it is:** The native iOS client ("PocketPilot.ai"), covering the same end-user surface as
Pilot Web plus an opt-in mode that turns the phone itself into a receiver.
**Why it exists:** A mobile-native equivalent of Pilot Web, and (via its receiver mode) a way for a
user's own iPhone to become a controllable device without a separate dedicated receiver phone.
**Where it lives:** `pilot-ios/` (task UI in `Tasks/`; realtime in `Tasks/TaskListRealtimeService.swift`;
API transport in `Core/PilotAPIClient.swift`, `Repositories/`; receiver mode in `Shared/BleManager.swift`,
`HidDongleController.swift`, `BroadcastExtension/`).
**Technology:** Swift, Firebase iOS SDK, Google WebRTC SDK (native cloud-phone view), CoreBluetooth
(for its own receiver mode), ReplayKit (for its own receiver mode), Google Sign-In, Sign in with
Apple.
**Input:** User input in the app UI; Firestore ping documents; REST responses from Cortex.
**Output:** HTTPS calls to the API Layer; when acting as a receiver, HID commands out to a dongle.
**Calls next:** API Layer (`srv`); Database (Firestore) directly for realtime listeners; when its
receiver mode is active, the same Receiver Management & RPC contract that `receiver-ios` uses.
**How QA should validate it:**
- Verify the same realtime-ping-then-refetch pattern as Pilot Web behaves correctly on iOS
  specifically (backgrounding the app, losing connectivity).
- If testing the opt-in receiver mode, confirm the account isn't simultaneously confused about
  being "a client" and "the device being controlled" (a real, code-acknowledged edge case).
- Confirm all three sign-in methods (Google, phone OTP, Sign in with Apple) succeed independently.

### 3. Telegram Bot Integration

**What it is:** A Telegram bot that lets a linked user create and continue tasks by DM.
**Why it exists:** A text-first, no-app-install channel for people who'd rather message a bot than
open a web/mobile app.
**Where it lives:** `cortex/src/tg/`.
**Technology:** Telegram Bot API, inbound webhook (secret-token validated) — not polling, despite
what the module's original description implies.
**Input:** Telegram webhook payloads (`/new <task>`, plain follow-up messages, `/stop`).
**Output:** Calls into the Task Manager (`taskCreateCore`/equivalent continuation functions); a
reply message sent back to the Telegram chat when the task reaches a terminal or waiting state.
**Calls next:** Task Manager (`task`), by calling the same core functions Pilot uses.
**How QA should validate it:**
- Confirm account linking, `/new`, plain-message continuation, and `/stop` each behave like their
  Pilot equivalents (same task engine underneath).
- Confirm a webhook failure doesn't silently drop a user's message — check whether the webhook
  returns an error status on internal failure (it does, unlike the Linq integration below).
- Confirm the "typing" indicator runs while a task is executing and stops appropriately.

### 4. Messaging Integration (iMessage / SMS / RCS)

**What it is:** A texting-based task-intake and reply channel, functionally parallel to Telegram,
built on a third-party messaging integration called Linq.
**Why it exists:** Reaches users who'd rather text a number than use an app — notably covers
iMessage, which has no bot/webhook concept of its own.
**Where it lives:** `cortex/src/linq/`.
**Technology:** `@linqapp/sdk`, inbound webhook.
**Input:** Inbound webhook payloads from the Linq platform (linked-number messages).
**Output:** Calls into the Task Manager; outbound reply messages via Linq; per-chat deliverability
health tracking (`healthStatus`: healthy/at-risk/critical/opted-out).
**Calls next:** Task Manager (`task`).
**How QA should validate it:**
- Confirm first-contact auto-provisioning works (a documented change removed an earlier manual
  `/signup` step).
- **Specifically test the silent-failure path**: this webhook returns HTTP 200 even when internal
  processing throws, by design, to avoid vendor retry storms — meaning a bug here won't be visible
  to Linq or necessarily to a user; verify a failure still surfaces somewhere (a log at minimum) so
  it isn't invisible end-to-end.
- Test behavior once a chat's `healthStatus` degrades — confirm this doesn't silently swallow
  replies without any signal reaching the user or an internal alert.

---

## B. API & Access Layer

### 5. API Layer

**What it is:** The single HTTP entry point into Cortex — every client (Pilot, Telegram, Linq)
talks to the backend exclusively through this layer.
**Why it exists:** Provides one consistent place for routing, request validation, auth
pre-handling, and error shaping, instead of every module reinventing HTTP handling.
**Where it lives:** `cortex/src/srv/` (`srv.ts`, `srvAddRoute.ts`); the shared response envelope
types live alongside it in `cortex/src/at/` (`AtStatus`, `AtSuccessResponse`/`AtErrorResponse`).
**Technology:** Fastify, `@fastify/cors`, `class-validator` for request DTOs.
**Input:** Raw HTTPS requests, almost all `POST`, at `/cortex/api/<module>/v1/<action>`.
**Output:** A consistent `{status: AtStatus, ...}` JSON envelope; on error, a mapped HTTP status
(400 validation, 401 unauthorized, 409 conflict/version-mismatch, 413 body-too-large, 500 server).
**Calls next:** Auth Layer (as a pre-handler) first, then the specific module handler for the
requested route (Task Manager, Receiver Management, Model Registry, etc.).
**How QA should validate it:**
- Confirm requests from an origin not on the CORS allow-list fail closed.
- Confirm undeclared extra fields in a request body are silently dropped (not rejected) while
  missing/malformed *declared* fields return a structured 400 — this is intentional, not a bug.
- Confirm a stale client version against a version-checked route returns the specific
  `FailurePilotVersionConflict` status, not a generic error.
- Send a body over the size cap and confirm a clean 413, not a hang or crash.

### 6. Auth Layer

**What it is:** Verifies who is making a request and whether they're allowed to.
**Why it exists:** Every action needs to know which user is asking and whether their account is in
good standing before any business logic runs.
**Where it lives:** `cortex/src/auth/` (`auth.ts`, `authPreHandler.ts`); the alternate
Personal-Access-Token credential path lives in `cortex/src/user/userPersonalAccessToken.ts`.
**Technology:** Delegates session validation to an external auth service over HTTP
(`X-API-Key`-signed); PATs are `sha256`-hashed at rest and detected by an `at-pat-` prefix.
**Input:** A bearer session token or a PAT on the request; the requesting route's declared
permission requirements.
**Output:** A populated `authUser` on the request (for downstream handlers), or a rejection —
401/403 for a bad/expired token, 403 for a waitlisted/banned account, 404 (not 403) for missing
permissions.
**Calls next:** Whichever module handler the route targets, now with a trusted `authUser` attached
— most immediately the Task Manager, Receiver Management, or User modules.
**How QA should validate it:**
- Confirm an expired session token is rejected and that the client's refresh-then-retry path
  actually recovers.
- Confirm a `WAITLISTED` or `BANNED` account is blocked even with an otherwise perfectly valid
  token — this is a separate gate from token validity.
- Confirm a missing-permission request returns 404, not 403 (deliberate, to avoid confirming a
  resource exists) — a test asserting on status code alone should expect this specifically.
- Confirm a PAT works as a full alternate credential for automation use cases.

---

## C. Task Engine

### 7. Task Manager

**What it is:** Owns the Task entity itself — its data, its state machine, and the routes for
creating, reading, messaging, cancelling, and sharing tasks.
**Why it exists:** Centralizes "what is a task and what state is it in" as one authority every
other component (the agent loop, the clients, routines, eval) reads and writes through, instead of
each having its own notion of task state.
**Where it lives:** `cortex/src/task/` (~40 files; key ones: `task.ts`, `taskCreateCore.ts`,
`taskStep.ts`, `taskQueue.ts`, `taskStateTimeline.ts`, `taskRoutes.ts`).
**Technology:** TypeScript, Firestore (via the Database component).
**Input:** Task-creation requests (message content, receiver ID, model override, timezone) from
any entry point; step results and state-resolution calls from the Agent Orchestrator; cancel/query
calls from clients.
**Output:** A persisted Task record with state, message thread, and step history; a background job
enqueued for the next step; realtime "ping" updates for clients.
**Calls next:** Job Queue & Background Workers, to schedule the first/next agent step.
**How QA should validate it:**
- Confirm the one-active-task-per-user rule: a second task while one is running should land in
  `QUEUED` and auto-start only once the first reaches a terminal state.
- Walk every documented terminal/waiting state (`COMPLETED`, `FAILED`, `CANCELLED`, `STOPPED`,
  `WAITING_FOR_USER_INPUT`, `WAITING_FOR_USER_INTERVENTION`) and confirm each is reachable and
  correctly rendered.
- Confirm a task stuck mid-execution is *not* rescued quickly — the self-heal sweep only fires
  after 24 hours, so don't expect fast automatic recovery from an orphaned task.
- Confirm resuming a task that previously stopped for low credit balance re-checks that balance
  rather than resuming unconditionally.

### 8. Job Queue & Background Workers

**What it is:** The mechanism that runs work outside the request/response cycle — most
importantly, every step of an agent task, but also routine polling and scheduled reports.
**Why it exists:** An agent task can take many seconds-to-minutes across many steps; running that
synchronously inside one HTTP request isn't viable, and a durable queue lets any backend instance
pick up the next unit of work and survive a process restart mid-task.
**Where it lives:** `cortex/src/jq/` (the queue infrastructure itself); job *definitions* live in
the modules that own them — `cortex/src/yoda/yodaJobs.ts` (`runTask`, `doKeepAlive`,
`startOrchSession`), `cortex/src/rtn/rtnJobs.ts` (routine polling), `cortex/src/dash/dashReportJobs.ts`
(daily report email).
**Technology:** BullMQ on Redis.
**Input:** Enqueued jobs with a type and payload (e.g., `{taskId, stepNumber}` for `runTask`).
**Output:** Job execution results; for `runTask`, either another enqueued job (continue the task)
or nothing further (task reached a stopping state).
**Calls next:** Whichever module owns that job type — most centrally, the Agent Orchestrator for
`runTask` jobs.
**How QA should validate it:**
- Remember the HTTP server and the job worker run in the **same process** — an unhealthy backend
  instance affects live API traffic and background work together, not independently. Factor that
  into how you interpret "everything is slow" incidents.
- Confirm routine execution timing matches the documented ~60-second poll plus per-routine jitter
  — a routine due at a specific minute may legitimately fire several minutes late, which is
  expected, not a bug.
- If reproducing a stuck task, check whether its job chain simply stopped re-enqueuing (this is
  the layer where that would happen).

---

## D. Agent Orchestration & AI Core

*This is the AI-specific heart of the system — everything above and below this section is
general-purpose platform plumbing.*

### 9. Agent Orchestrator

**What it is:** The component that runs one step of an agent task: read context, decide an action,
persist the result, decide what happens next.
**Why it exists:** This is the actual "brain loop" of the product — the thing that turns a
natural-language request into a sequence of concrete device actions.
**Where it lives:** `cortex/src/yoda/yoda.ts` (the step logic) and `yoda/yodaJobs.ts` (the job
wrapper that turns a step into a background job and re-enqueues the next one).
**Technology:** TypeScript; no ML/inference code of its own — it calls out to the LLM Provider
Layer for every decision.
**Input:** A task ID and step number (from the Job Queue); the current conversation history and
device context.
**Output:** A persisted step record (reasoning, chosen tool call, cost/token stats); a resolved
next task state; if needed, a dispatched device action; if the task should continue, a re-enqueued
job for the next step.
**Calls next:** Prompt Builder and Context Manager (to assemble the request), LLM Provider Layer
(to get a decision), Tool Executor (to carry it out), Task Manager (to persist state).
**How QA should validate it:**
- Confirm the conditional device-context refresh: a step whose previous action didn't touch the
  device may reason from a screenshot that's one step stale — verify this is expected behavior,
  not treated as "the agent didn't notice the screen changed."
- Deliberately trigger a malformed tool call scenario if possible and confirm exactly one retry
  happens before the task fails — a second silent retry, or zero retries, would both be
  regressions.
- Confirm loop-avoidance behavior on a genuinely repetitive UI — this is prompt-level guidance
  only, not code-enforced, so it's a legitimate place to find real AI-quality bugs, not backend
  bugs.

### 10. Prompt Builder

**What it is:** The logic (inside the Agent Orchestrator) plus the template files it draws from,
responsible for assembling exactly what gets sent to the model on a given step.
**Why it exists:** The model's instructions change based on receiver type, whether a routine
triggered the task, and what's happened so far — this needs to be assembled fresh, correctly, on
every call.
**Where it lives:** Assembly logic in `cortex/src/yoda/yoda.ts`; the actual prompt/playbook content
in `cortex/src/templates/` (`yodaSystemPrompt.mustache`, `yodaVolatileSystemPrompt.mustache`,
`yodaSystemPlaybook.md` + `yodaSystemPlaybookAndroidDongle.md` + `yodaSystemPlaybookIosDongle.md`,
`yodaDisplayMetadataSystemPrompt.mustache`).
**Technology:** Mustache templating, Markdown playbook files.
**Input:** Receiver type, routine context (if any), the user's memory (from the Memory component),
current date/location, and the (possibly compacted) conversation history.
**Output:** A stable, cacheable system-prompt half plus a volatile per-turn half, combined into the
final request sent to the LLM Provider Layer.
**Calls next:** LLM Provider Layer (`omni`), carrying the assembled prompt plus the tool schemas
from the Tool Manager.
**How QA should validate it:**
- Confirm the correct playbook variant is actually selected per receiver type — an `iosDongle`
  task should never see capability claims (like installing apps) that playbook explicitly
  disclaims.
- Confirm the model never leaks the raw system prompt, tool schemas, or internal field markers to
  the user, even under adversarial prompting — this is an explicit, named guardrail in the
  playbook and a reasonable thing to red-team directly.

### 11. Context Manager

**What it is:** Manages how conversation history is assembled for a step, and compresses it once a
task has run long enough that the full history becomes impractical.
**Why it exists:** Long-running tasks accumulate history that eventually threatens cost, latency,
and model accuracy; without compaction, a sufficiently long task would eventually fail outright on
context size.
**Where it lives:** `cortex/src/yoda/yodaConversationHistory.ts` (assembly),
`cortex/src/yoda/yodaCompaction.ts` (compaction).
**Technology:** TypeScript; compaction itself is implemented as an extra call through the LLM
Provider Layer using a summarization prompt.
**Input:** The full step-by-step history of a task so far; the previous step's token usage (to
decide whether compaction is needed).
**Output:** Either the full history (short tasks) or a compacted summary plus everything since
(long tasks), ready for the Prompt Builder to include.
**Calls next:** LLM Provider Layer, for the summarization call itself, when compaction triggers.
**How QA should validate it:**
- Run (or find) a long task and confirm a visible "context automatically compacted" entry appears
  in the thread at the expected point.
- Confirm a compacted task still behaves coherently afterward — i.e., the agent doesn't lose track
  of what it was doing.
- Treat a compaction event as a legitimate explanation for "a step that did nothing visible on the
  device" — it's a real extra step, not a stall.

### 12. Model Registry

**What it is:** The lookup that decides which LLM model backs a given purpose (main agent loop,
dongle-constrained receivers, routines, title generation, memory generation, etc.).
**Why it exists:** Different call types have different cost/capability tradeoffs — a full task step
warrants a stronger model than a cheap title-generation call — and this needs to be centrally
configurable rather than hardcoded per call site.
**Where it lives:** `cortex/src/mreg/` (`mreg.ts`, `mregGetModelHandler.ts`).
**Technology:** TypeScript, backed by the live Firestore config (`ConfSubEnv`) rather than
hardcoded values — meaning model routing can change without a redeploy.
**Input:** A model purpose/ID lookup key (e.g., default model, default model for iOS dongle,
default model for routines).
**Output:** A resolved model identity plus metadata: vendor routing info, pricing, and the
coordinate system that model expects (device pixels, normalized 0–1000, or preprocessed vision
pixels).
**Calls next:** LLM Provider Layer, with the resolved model FQN.
**How QA should validate it:**
- After a live model-routing change, confirm it takes effect without a deploy (per Document 2's
  live-config behavior) — and confirm it applies consistently across every call type that should
  be affected.
- Since coordinate handling is genuinely model-specific, re-verify tap/swipe accuracy specifically
  whenever the underlying model for a receiver type changes — this is called out as something that
  doesn't automatically generalize across models.

### 13. LLM Provider Layer

**What it is:** The vendor-agnostic layer every LLM call in the system goes through — it hides
Anthropic, Google, OpenAI, xAI, Groq, OpenRouter, and AWS Bedrock behind one contract.
**Why it exists:** So the rest of the backend (the Agent Orchestrator, evaluation, memory
generation, title generation, RRULE generation, etc.) never needs vendor-specific logic; it also
centralizes cost calculation, error normalization, and tracing for every model call in one place.
**Where it lives:** `cortex/src/omni/` (`omni.ts` plus per-vendor adapters: `omniAnthropic.ts`,
`omniGemini.ts`, `omniResponses.ts` shared by OpenAI/OpenRouter/xAI/Groq, `omniChatCompletions.ts`).
**Technology:** `@anthropic-ai/sdk` + `@anthropic-ai/bedrock-sdk`, `@google/genai`, and a shared
OpenAI-compatible HTTP client for the Responses-API-compatible vendors (OpenAI, OpenRouter, xAI,
Groq); `@langfuse/otel`/`@langfuse/tracing` and `@opentelemetry/*` for tracing hooks.
**Input:** A canonical request — system prompt, message history, tool schemas or a JSON schema,
inference knobs, a `vendor/model` identity.
**Output:** A canonical response — reasoning/text/at-most-one-tool-call, normalized token/cost
stats, a normalized error on failure, and (always) the raw vendor request/response for debugging.
**Calls next:** Whichever component made the call resumes with the result — most centrally the
Agent Orchestrator, but also Memory, Evaluation, and routine RRULE generation.
**How QA should validate it:**
- If a task's behavior seems to differ specifically by which model executed it, treat that as an
  expected axis of variation to investigate (feature support genuinely differs by vendor), not
  automatically a bug.
- Confirm the single-tool-call-per-turn contract holds regardless of vendor, even for providers
  that natively support parallel tool calls — this is intentionally disabled everywhere.
- Any *new* call site added to the codebase should pass a tracer explicitly to appear in the
  Telemetry & Tracing component — a "call I can't find in Langfuse" may mean exactly that it was
  never wired up, a known class of gap (see Component 29).

### 14. Memory

**What it is:** Per-user, persistent context that survives across tasks — not per-task
conversation history, but longer-term facts and notes the agent carries forward.
**Why it exists:** So the agent can reference something from a prior, unrelated task ("the user
mentioned they're vegetarian last week") without that context living inside any single task's
history.
**Where it lives:** `cortex/src/umem/` (`umemCore.ts`, `umemTaskMemory.ts`, `umemWorkspace.ts`).
**Technology:** TypeScript, Firestore; a dedicated cheap model call (via the LLM Provider Layer)
generates memory updates.
**Input:** A just-completed task's content, on every terminal state.
**Output:** Updates to two of four memory files per user — long-term `memory.md` and today's
short-term notes file (the persona/identity/user-facts files are user-editable only, not
agent-writable this way).
**Calls next:** Nothing further at write time; at *read* time, the Prompt Builder pulls current
memory content into the volatile system prompt for future tasks.
**How QA should validate it:**
- Complete a task that states a durable fact, then start an unrelated task and confirm the agent
  demonstrates awareness of it — this is the core behavior to validate.
- Confirm a user can view/edit/reset their memory files directly, and that an agent-driven memory
  update never overwrites the user-owned persona/identity files.
- Confirm memory generation firing is tied to *terminal* states only, not to every step.

### 15. Skill Registry

**What it is:** A library of domain-specific instruction playbooks (e.g., how to research on
Instagram, how to book a ride, how to install an app) the agent can pull into context.
**Why it exists:** Keeps the main system prompt lean by keeping specialized, less-frequently-needed
instructions out of it by default, loaded only when relevant.
**Where it lives:** `cortex/src/skills/` (`skillRegistry.ts`, `skillLoader.ts`,
`skills/definitions/*.md` — e.g. `instagram.md`, `shopping.md`, `giftFinder.md`,
`chrome-browser-automation.md`, `app-installation.md`, `android-direct-actions.md`,
`airtap-ride-hailing.md`, `airtap-faq.md`, `telegram.md`).
**Technology:** Markdown files with frontmatter, loaded into an in-memory registry at boot;
user-owned custom/override skills persist in Firestore.
**Input:** Either an explicit `LoadSkill` tool call from the model (on-demand skills), or the
current foreground app's package name (auto-loaded skills, matched automatically without a tool
call).
**Output:** The full skill playbook content, injected into the next prompt.
**Calls next:** Feeds back into the Prompt Builder for the next step.
**How QA should validate it:**
- Confirm on-demand skills only appear in full once explicitly loaded (before that, only their
  name/description should be visible in-prompt) — and confirm auto-loaded skills trigger correctly
  when their associated app is in the foreground, with no tool call needed.
- Confirm the two skills hidden for dongle receivers (`android-direct-actions`,
  `app-installation`) are in fact unavailable/unusable on those receiver types.
- If a user has a custom/override skill saved, confirm it takes precedence over the built-in
  version with the same identity.

### 16. Tool Manager

**What it is:** The declared catalog of every action the agent is allowed to take on a given step
— the schemas, not the execution logic.
**Why it exists:** The model can only choose from tools it's explicitly told exist; this is the
single source of truth for what those tools are and what parameters they require, and it's what
gets filtered per receiver type before every call.
**Where it lives:** `cortex/src/yoda/yodaTools.ts`.
**Technology:** Zod schemas.
**Input:** The current receiver type (to know which tools to include/exclude).
**Output:** A filtered list of tool schemas for the LLM Provider Layer to pass to the model —
device-operation and browser-automation mega-tools with discriminated action unions, plus flat
tools like web search, image generation, email, routine management, skill loading, and the
plan/respond/clarify/takeover control tools.
**Calls next:** LLM Provider Layer (as part of the request the Prompt Builder assembles); once the
model responds, the chosen tool name is handed to the Tool Executor.
**How QA should validate it:**
- Confirm tool availability differences per receiver type hold in practice — e.g., an iOS dongle
  task should never be offered browser-automation or Play-Store-search tools; a physical/dongle
  Android receiver should never be offered the cloud-only browser tool.
- If a new tool is added, confirm it's reachable end-to-end (declared here, handled by the Tool
  Executor) rather than just declared and silently unused.

### 17. Tool Executor

**What it is:** The dispatcher that takes the one tool call the model chose and actually runs it.
**Why it exists:** Separates "what the model decided" from "how that gets carried out" — a single,
uniform dispatch mechanism handles every tool, whether it needs the device, a web search API, or
nothing external at all.
**Where it lives:** `cortex/src/android/androidActions.ts` (the `AndroidActionRegistry`, despite
living in the `android` module — it dispatches *every* tool, not just device ones).
**Technology:** TypeScript, an in-memory `Map<toolName, handler>` populated at boot.
**Input:** The chosen tool name and its (validated) parameters from the Agent Orchestrator.
**Output:** The result of executing that specific handler — a search result, a generated image, an
email sent, or (for device-touching tools) a request handed off to the Device Command Router.
**Calls next:** For tools flagged as needing a live receiver, the Device Command Router; for
everything else (web search, image generation, email...), the relevant external API/module
directly, bypassing the device layer entirely.
**How QA should validate it:**
- Confirm a call to an unregistered/unknown tool name fails explicitly rather than being silently
  ignored.
- Confirm tools that don't require a receiver (e.g., web search) still work correctly for a task
  that has no receiver context resolved yet, if that's a reachable state.
- When testing a *specific* tool, identify whether it's device-routed or direct — that determines
  which downstream layer's failure modes are actually relevant to that test.

---

## E. Device Communication & Control

### 18. Device Command Router

**What it is:** The decision point for *how* a device-touching action actually reaches a device —
picks between a cloud VM's direct HTTP path and a paired device's RPC path.
**Why it exists:** A cloud phone and a paired physical phone are reachable in fundamentally
different ways (Document 2); something has to decide which applies for a given receiver before
dispatch can proceed.
**Where it lives:** `cortex/src/android/androidExecuteCommand.ts` (the branch point),
`androidInteractions.ts` (the cloud HTTP implementation), `androidGetInstance.ts` (resolves which
concrete device/session a task's receiver ID actually refers to).
**Technology:** TypeScript; plain HTTP for the cloud path.
**Input:** A resolved device action plus the task's `receiverType` (`cloud`, `physical`,
`androidDongle`, `iosDongle`).
**Output:** For `cloud`, a direct HTTP call/response to the VM's in-instance agent. For the other
three, a handoff to Receiver Management & RPC.
**Calls next:** Cloud Phone Orchestrator Client's managed instance directly (cloud), or Receiver
Management & RPC (paired devices).
**How QA should validate it:**
- Confirm behavior differs correctly and predictably by receiver type — this is the literal fork
  point, so a bug here would misroute a command to the wrong transport entirely.
- Test a command issued the instant a cloud phone is requested, before its session is fully
  warmed up — this is called out as *not* covered by the same automatic-retry handling as other
  infrastructure errors, and is a good deliberate reproduction target.

### 19. Receiver Management & RPC

**What it is:** Owns everything about a paired device on the backend side: its identity, pairing,
the request/response protocol used to command it, and the WebRTC signaling handshake for cloud
phones.
**Why it exists:** Physical phones can't be reached with a normal direct network call (they sleep,
background, sit behind arbitrary networks) — this component defines the store-and-forward protocol
that works around that using Firestore.
**Where it lives:** `cortex/src/rcvr/` (`rcvr.ts`, `rcvrRpc.ts`, `rcvrAddReceiverHandler.ts`,
`rcvrGetPairingCodeHandler.ts`, `rcvrStartWebrtcHandler.ts`, `rcvrSetAnswerSdpHandler.ts`,
`rcvrCreateTicketHandler.ts`, `rcvrOrch.ts`).
**Technology:** Firestore `onSnapshot` listeners, Firebase Admin SDK (custom token minting for
device auth), FCM (wake pushes).
**Input:** A device action to send (from the Device Command Router); pairing requests from a
device; WebRTC offer/answer from a browser (relayed onward via the Cloud Phone Orchestrator
Client).
**Output:** A single-slot RPC exchange per receiver (`rpc/request` written, `rpc/response`
awaited, 30s default timeout); a screenshot or status result read back inline as JSON; a Firebase
custom token issued on successful pairing.
**Calls next:** The physical Android or iOS Controller app (via Firestore, not a direct call), plus
the Cloud Phone Orchestrator Client for WebRTC signaling specifically.
**How QA should validate it:**
- Issue two commands to the same receiver faster than one round trip completes and observe the
  behavior — this is a single-slot mailbox, not a queue, so this is a real, reproducible stress
  scenario, not a hypothetical.
- Put a paired phone to sleep/background it, then send a task, and confirm the FCM wake path
  actually recovers it within the timeout window rather than just timing out.
- Send a busy/high-resolution screen through this path and check behavior near Firestore's
  practical document-size ceiling — there's no chunking on this path today.
- Confirm each device-reported failure (screen locked, accessibility permission revoked, receiver
  paused, receiver unlinked, unsupported version, iOS broadcast not running) surfaces as its own
  distinct, correctly labeled failure — not a generic error.

### 20. Cloud Phone Orchestrator Client

**What it is:** Cortex's client for a separate service (outside this repository) that provisions
and manages ephemeral cloud-hosted Android VMs, and the signaling relay for the live WebRTC view of
one.
**Why it exists:** Lets a user run a task with no physical hardware at all — the "cloud phone"
option — by talking to a purpose-built VM-management service rather than reimplementing that here.
**Where it lives:** `cortex/src/orch/` (`orchApi.ts`, `orchErrors.ts`, `orchUtils.ts`).
**Technology:** HTTP client to the external orch service.
**Input:** Session lifecycle calls (start/keep-alive) and WebRTC signaling payloads (SDP
offer/answer, ICE candidates) forwarded from Receiver Management & RPC.
**Output:** A running (or failed-to-start) cloud VM session; relayed SDP/ICE answers back to the
requesting browser. Cortex never touches the actual audio/video stream — only signaling.
**Calls next:** The external orch service and, transitively, the ephemeral VM it manages; the
actual per-step device commands to that VM go via the Device Command Router's direct HTTP path,
not back through this client.
**How QA should validate it:**
- Treat a "grey screen"/no-video report as ambiguous by default — distinguish a genuine outage
  from a client that isn't retrying by checking the actual status this layer returns, since many
  `orch` statuses are deliberately mapped down to one retryable status.
- Confirm the cloud phone's idle-timeout disconnect behaves correctly and that reconnecting after
  it is a clean experience, not a stuck state.
- Since this service lives outside the repository, treat it as a real external dependency in test
  planning — its availability/latency isn't something a code change here can fix.

### 21. Android Controller

**What it is:** The on-device Android application that receives commands and physically carries
them out on the phone being controlled.
**Why it exists:** Something has to actually run on the target Android phone to execute taps,
swipes, screenshots, and app launches — this is that app, and it's the literal point where a
software decision becomes a physical action.
**Where it lives:** `receiver/` (Java, package `ai.airtap.receiver`); key classes:
`accessibility/FirebaseCommandListener.java` (command intake), `accessibility/CommandExecutor.java`
(dispatch table, ~25 commands), `accessibility/UiAccessibilityService.java` (software input path),
`usbhid/UsbHidService.java` + `UsbHidManager.java` (hardware input path), `screencap/ScreenCaptureService.java`
(screenshots).
**Technology:** Java, Android SDK (`AccessibilityService`, `MediaProjectionManager`, Bluetooth LE
APIs, `ForegroundService`), Firebase (Firestore, Auth, Cloud Messaging), Gradle. Ships as two
distinct builds/version tracks from one codebase: `physical` (accessibility-driven) and
`androidDongle` (HID-driven).
**Input:** Firestore `rpc/request` documents (via a long-lived listener, not polling); FCM wake
pushes.
**Output:** Physical device actions (accessibility API calls or HID packets via the dongle);
`rpc/response` documents, including inline base64 screenshots; Zendesk support tickets with
uploaded log files.
**Calls next:** For `androidDongle` builds, the HID Dongle component over Bluetooth; for `physical`
builds, the phone's own Accessibility Service APIs directly (no dongle involved).
**How QA should validate it:**
- Deliberately trigger each explicitly coded failure state and confirm the exact right response:
  lock the screen (`FailureReceiverScreenLocked`), revoke screen-capture permission, and pair
  against a backend with a version floor above the installed app's version
  (`FailureUnsupportedVersion`).
- Confirm pairing surfaces a clear, specific error when the Firebase project encoded in the
  pairing token doesn't match the build's own project (a real, coded "wrong app variant paired to
  wrong environment" detection).
- Treat `receiver/README.md` and `receiver/TECHNICAL_IMPLEMENTATION.md` as directionally correct
  but not literally accurate — they reference an old package name; verify against the real
  `ai.airtap.receiver` code, not just the docs.
- Test OS-level background-kill resilience (aggressive OEM battery managers) specifically — this
  is a known ecosystem risk the app mitigates with foreground services and wake locks but can't
  fully eliminate.

### 22. iOS Controller

**What it is:** The on-device iOS application dedicated to being controlled — the iOS counterpart
to the Android Controller.
**Why it exists:** iOS has no accessibility-injection equivalent to Android's, so a dedicated app
using the HID dongle plus screen broadcasting is the only way to control an iPhone.
**Where it lives:** `receiver-ios/` (Swift); key files: `Receiver.swift` (main coordinator,
Firebase pairing, Firestore listener, dispatch), `BleManager.swift` (BLE central role),
`HidDongleController.swift` (dongle state machine + firmware handling), `HidInput.swift` (HID
packet/report encoding), `AudioKeepalive.swift` (background-survival trick),
`BroadcastExtension/SampleHandler.swift` (screen capture).
**Technology:** Swift, CoreBluetooth, ReplayKit (broadcast upload extension), AVFoundation (for the
audio-session keepalive trick), Firebase (Firestore, Auth).
**Input:** Firestore `rpc/request` documents; a continuous stream of captured screen frames from
its own broadcast extension process.
**Output:** HID commands sent over Bluetooth to the dongle; `rpc/response` documents, including the
most recently captured screenshot frame (not a fresh on-demand grab).
**Calls next:** The HID Dongle component, exclusively — there is no software-injection fallback on
iOS.
**How QA should validate it:**
- Confirm the AssistiveTouch self-test at pairing time: with AssistiveTouch off, the app should
  detect its own test tap failing and prompt the user, rather than silently proceeding into a
  broken state.
- Reboot a phone that had an active broadcast session running beforehand, and confirm the app
  correctly reports the broadcast as stopped — this exercises a specific boot-time staleness check
  built to prevent a false "still running" reading.
- Background the app (or otherwise interrupt the silent-audio keepalive, e.g. an incoming phone
  call) and confirm the app detects the interruption and auto-resumes rather than silently going
  dark.
- Force-quit the app mid-firmware-update and confirm the dongle recovery path is actually
  triggered on next launch, rather than leaving the dongle stuck.

### 23. HID Dongle

**What it is:** A small BLE-to-USB hardware accessory that turns a wireless command into a genuine
keyboard/mouse/touch signal on whatever it's plugged into.
**Why it exists:** This is the mechanism that lets Airtap control a device with real hardware
input indistinguishable from a person, rather than software-level automation that some apps can
detect and block — and it's the *only* input mechanism available on iOS at all.
**Where it lives:** The hardware itself, plus its host-side libraries: `receiver/usbhidlib/`
(Android — BLE scanning, GATT management, `KeyboardController`/`MouseController`/`TouchController`)
and `receiver-ios/Receiver/HidInput.swift` (iOS equivalent encoders).
**Technology:** Bluetooth LE (GATT) between the receiver app and the dongle; USB HID (keyboard,
mouse, and digitizer/touch report types) between the dongle and the host phone; a custom packet
protocol on top (raw keyboard, absolute mouse, digitizer touch, firmware-timed text, and an
iOS-only Unicode keyboard command) plus a firmware update sub-protocol.
**Input:** BLE-encoded commands from the Android or iOS Controller (tap coordinates, key presses,
text batches).
**Output:** Real USB HID reports on the host phone; BLE status/connection-state callbacks back to
the controller app.
**Calls next:** Nothing further in software — this is the terminal hop; the host phone's own OS
receives the HID signal as if from real hardware.
**How QA should validate it:**
- This is the component where genuinely hardware-only test cases live: BLE out-of-range behavior,
  a dead/low battery, a loose or unplugged USB connection, and reconnect timing (documented
  backoff steps up to 60 seconds) — none of these have a pure-software equivalent, so they need to
  be physically reproduced, not just reasoned about.
- Deliberately test a firmware-version mismatch and confirm the update flow triggers correctly;
  then deliberately interrupt an in-progress update (kill the app, walk the dongle out of range)
  and confirm recovery rather than a bricked-looking state.
- On Android specifically, confirm `androidDongle` and `physical` builds are tested as genuinely
  separate paths — they are different APKs with independent version numbers, not one build with a
  toggle.

---

## F. Data & Storage

### 24. Database

**What it is:** The system of record for essentially everything — users, tasks, receivers,
routines, live configuration — and, via `onSnapshot` listeners, the realtime transport for both
device RPC and browser UI updates.
**Why it exists:** A single, realtime-capable store that both serves normal reads/writes and
doubles as a push mechanism removes the need for a separate messaging/notification system for
either the device-command path or the live-UI-update path.
**Where it lives:** `cortex/src/ddb/` (the wrapper every other module reads/writes through);
security boundaries defined in `cortex/agent.firestore.rules`; the query shape implied by
`cortex/agent.firestore.indexes.json`.
**Technology:** Google Cloud Firestore.
**Input:** Reads/writes from essentially every backend module.
**Output:** Persisted documents; realtime change notifications to anything listening.
**Calls next:** Nothing further — it's a storage leaf — but it fans *out* passively to any active
listener (a device's RPC listener, a client's ping listener).
**How QA should validate it:**
- This isn't something to test in isolation so much as through its security rules: confirm a
  paired device genuinely cannot read another receiver's data, cannot read its own `rpc/response`
  (only write it), and that the browser client can only read the specific `PilotUpdates` documents
  it's meant to.
- Be aware environments are fully isolated at this layer — a "missing" task/user/receiver is often
  simply in a different environment's project, not actually missing.

### 25. Cache

**What it is:** A Redis-backed cache layer, also used as the storage backend for the Job Queue.
**Why it exists:** Reduces repeated load for frequently-read data and provides the fast, ephemeral
storage BullMQ needs for job state.
**Where it lives:** `cortex/src/mdb/` (`mdb.ts`, `mdbObjMgr.ts`).
**Technology:** Redis (`ioredis`).
**Input:** Cache reads/writes from backend modules; job state reads/writes from the Job Queue.
**Output:** Cached values (or a cache miss, falling through to the real data source); job state.
**Calls next:** Nothing further — a storage leaf, same as the Database.
**How QA should validate it:**
- Not typically something to test directly; relevant mainly when diagnosing "the queue seems
  down" — a Redis outage would affect both caching *and* the Job Queue simultaneously, which is a
  useful diagnostic signal.
- A dedicated internal alerting path pages the team specifically on database/cache failures — if
  investigating an incident, that alert (rather than guesswork) is the fastest confirmation this
  layer is implicated.

### 26. Blob Storage

**What it is:** Object storage for large binary content: task screenshots (from the cloud-phone
and scrollable-capture paths), gzip-compressed per-call LLM debug payloads, and evaluation/task
analysis data.
**Why it exists:** This kind of content doesn't belong inline in a Firestore document — it's large,
binary, and doesn't need realtime-listener semantics.
**Where it lives:** `cortex/src/img/` (`imgSaveImage.ts`, `imgGetImage.ts`, `imgClient.ts`).
**Technology:** AWS S3, namespaced per environment.
**Input:** Image/binary data from wherever it's captured (cloud-phone screenshots, debug capture).
**Output:** A stored object plus a retrievable URL/reference.
**Calls next:** Nothing further — a storage leaf.
**How QA should validate it:**
- Remember this is **not** the storage path for paired-device screenshots — those travel inline as
  base64 through the Database/RPC path instead (Component 19), a meaningfully different failure
  surface (no size chunking there, versus proper blob storage here).
- If investigating a missing debug artifact, confirm which path (S3 vs. inline Firestore) that
  particular kind of screenshot is supposed to use before concluding something is actually broken.

---

## G. Cross-Cutting: Observability, Safety, Evaluation

### 27. Logging

**What it is:** The single centralized logger every backend module writes through.
**Why it exists:** One consistent place to control log levels, formatting, and where logs end up,
rather than ad hoc `console.log` scattered through the codebase.
**Where it lives:** `cortex/src/log/log.ts`.
**Technology:** A custom TypeScript logger; AWS CloudWatch Logs SDK for shipped logs; triggers
Sentry (Component 28) internally for `warn`/`error` calls.
**Input:** `debug`/`info`/`warn`/`error` calls with a message and metadata (a `taskId` is the de
facto correlation key at most call sites) from anywhere in the backend.
**Output:** Colored console lines (when enabled); batched CloudWatch log events (up to 10,000
events or 1MB per flush, every 5 seconds); a Sentry capture for `warn`/`error`.
**Calls next:** Error Monitoring (Sentry), for `warn`/`error` calls only.
**How QA should validate it:**
- Don't expect to filter logs by module name via a "module tag" — the module-scoped logger pattern
  exists syntactically throughout the codebase but doesn't currently tag output with the module
  name; searching by `taskId` (or request ID for HTTP-scoped issues) is the reliable approach.
- Be aware a crash between CloudWatch flush cycles can lose the most recent (up to 5 seconds' worth
  of, or up to 1MB/10,000-event) log activity — an incomplete-looking crash log near the very end
  isn't necessarily a logging bug.

### 28. Error Monitoring

**What it is:** Automated capture and aggregation of application errors, used independently on the
backend and on each frontend.
**Why it exists:** Gives the team visibility into unhandled/logged errors in production without
relying on users to report them.
**Where it lives:** Backend: wired in `cortex/src/cortexInit.ts`. Frontend: `pilot/sentry-client.ts`
+ `pilot/sentry-runtime.ts`, and an equivalent pair in `website/`.
**Technology:** Sentry (`@sentry/node` on the backend; Sentry's browser/Next.js SDK on the
frontends).
**Input:** Backend: every `log.warn`/`log.error` call. Frontend: unhandled exceptions, error
boundaries, and (in Pilot specifically) a systematic wrapper that captures failed backend API calls
as typed contract errors (e.g. a distinct error type per domain — dashboard, eval, model, receiver,
routine).
**Output:** Aggregated error events, with breadcrumbs/context, visible in Sentry's dashboard.
**Calls next:** Nothing further — a terminal observability sink.
**How QA should validate it:**
- **Know the backend sampling rate is 20%** — most backend errors never reach Sentry by design;
  treat Sentry as a *sample*, not the complete backend error record (CloudWatch/console logs are
  complete; Sentry is not).
- On the frontend, confirm a broken Pilot→Cortex API contract for a specific domain (e.g., evals)
  shows up as that domain's specific typed contract error, not a generic network failure — useful
  for triaging which layer actually broke.

### 29. Telemetry & Tracing

**What it is:** Per-call, per-task tracing of LLM calls specifically — a timeline view of every
model call a task made, with full input/output.
**Why it exists:** This is the primary tool for answering "why did the AI decide to do that,"
distinct from general error monitoring — it's about model *behavior*, not application errors.
**Where it lives:** `cortex/src/omni/omniLangfuseSetup.ts`, `omniTracing.ts`; initialized in
`cortexInit.ts`.
**Technology:** Langfuse, via a dedicated OpenTelemetry pipeline kept deliberately separate from
Sentry's own OTel usage.
**Input:** Full request (system prompt, messages, model, inference knobs) and full response
(reasoning/text/tool-use, raw vendor response, token/cost stats) for any LLM call whose caller
passed a tracer.
**Output:** A queryable trace per task (Langfuse `sessionId` = `taskId`), viewable end-to-end.
**Calls next:** Nothing further — a terminal observability sink, external to the backend's own
storage.
**How QA should validate it:**
- **This is opt-in per call site, not automatic** — confirmed gap: the UI status-label generation
  call is not traced here. If a specific call type seems to be missing from a Langfuse trace,
  check whether it's a known, existing gap before treating it as a new bug.
- Use this as your first stop (alongside Component 30) when a task made a strange decision — you
  can see exactly what the model was shown, not just what code inferred from its answer.

### 30. Task Debug & Trace Capture

**What it is:** Purpose-built, task-specific debugging data captured by the product itself (not a
third-party tool) — the most complete and most granular record of what happened during a task.
**Why it exists:** For diagnosing one specific task's behavior in full detail — what state it was
in and when, where inside a given step it got stuck, and exactly what every model call involved —
without depending on an external tool's retention or sampling.
**Where it lives:** `cortex/src/task/taskStateTimeline.ts` (state transition history),
`taskYodaTrace.ts` (step-level checkpoint breadcrumbs), `taskOmniDebug.ts` (full per-call vendor
request/response capture).
**Technology:** TypeScript; state timeline and breadcrumbs go to the Database/Logging; full call
payloads are gzip-compressed and persisted to Blob Storage (S3).
**Input:** Every state transition, ~20 named checkpoints per step, and every single LLM call made
on the task's behalf (main decision, display-label, compaction, memory generation, title
generation, follow-on suggestions — all of them).
**Output:** A layered, queryable record: coarse state history → step-level breadcrumbs → complete
per-call vendor payloads.
**Calls next:** Nothing further — a terminal, purpose-built debugging sink, exposed via API to the
task's owner or an admin.
**How QA should validate it:**
- Use this as the **default first stop** when triaging any single misbehaving task, in this order:
  state timeline (what happened, when) → step trace (where inside a step it stalled) → full call
  capture (exactly what the model was shown and said).
- Unlike Telemetry & Tracing (Component 29), this capture is **always-on for every call**, not
  opt-in — if something is missing here, that's a genuine bug worth escalating, whereas a gap in
  Langfuse might just be a known opt-in gap.
- Confirm access control: only the task's owner or an admin should be able to retrieve this data
  for a given task.

### 31. Retry Handling

**What it is:** Not a standalone module — the automatic-retry behavior for a failing agent step,
embedded directly in the Agent Orchestrator's job-error handling.
**Why it exists:** Distinguishes genuinely transient infrastructure hiccups (worth a bounded retry)
from real failures (worth failing fast) without needing a generic, one-size-fits-all retry
framework.
**Where it lives:** `cortex/src/yoda/yodaJobs.ts` (the error-handling logic run when a step job
fails), plus a narrower one-shot retry specifically for malformed tool calls inside `yoda.ts`.
**Technology:** TypeScript, plain conditional logic (no separate retry library/queue-level retry
policy).
**Input:** The specific error type a step failed with.
**Output:** Either another attempt at the step (within a bounded window — e.g. a device-context
fetch failure gets roughly 4 minutes of retrying, most Omni-layer infrastructure errors get one
retry), or a `FAILED` task with a specific reason if the window is exhausted.
**Calls next:** Back to the Agent Orchestrator for another attempt, or the Task Manager to record
`FAILED`.
**How QA should validate it:**
- Explicitly confirm which error types *are* on the retry list (rate limiting, model unavailable,
  timeout, output validation failure, device-context fetch failure) versus which are documented as
  **not** on it (a cloud session that isn't ready yet is the confirmed example) — the latter should
  fail fast on the very first occurrence, and that's worth verifying rather than assuming
  everything retries the same way.
- Confirm a malformed tool call gets exactly one corrective retry, not zero and not several.

### 32. Safety & Guardrails

**What it is:** Not a single module — a set of independent, purpose-specific enforcement points
that together constrain what the agent (and the platform around it) is allowed to do. Documented
here as one entry specifically because there is no single "Safety Layer" to point to.
**Why it exists:** Different kinds of risk are mitigated at different layers because they're
different kinds of problems — what the model is instructed never to reveal, what an unauthenticated
caller can reach, how much a user can spend, and how long a task loop is allowed to run all need
different mechanisms.
**Where it actually lives:**
- **Prompt-level guardrails** — the playbook (Component 10) explicitly instructs the model never to
  reveal its system prompt, tool schemas, or internally-tagged field content, and never to act when
  required input is missing.
- **Trust-boundary enforcement** — Firestore security rules (Component 24) restrict a paired
  device to only its own RPC subcollection; the Auth Layer (Component 6) enforces account
  admission state independently of token validity.
- **Spend limits** — per-user daily credit/usage caps (`cortex/src/user/userUsage.ts`,
  `userUsagePlan.ts`), enforced before a step is allowed to proceed and reset on UTC-date rollover.
- **Loop limits** — an overall per-task step cap, and (for evaluation runs specifically) a
  configurable cancel-after-N-steps cap.
- **Network-level gating** — an explicit CORS allow-list (Component 5) and a version-floor check
  that can lock out outdated receiver apps (Component 19).
**Technology:** Varies by enforcement point — see above.
**Input/Output/Calls next:** Not applicable as a single component — each enforcement point's
input/output is described under its owning component above.
**How QA should validate it:**
- Treat each bullet above as its own independent test surface — don't assume testing one covers
  the others; a bug in credit-limit enforcement says nothing about whether prompt guardrails hold.
- Specifically red-team the prompt-level guardrails (attempt to get the agent to reveal its system
  prompt or tool schemas) — this is the one enforcement point that's probabilistic (model
  behavior) rather than deterministic (code), and therefore the one most likely to have real gaps.
- Confirm the daily quota boundary behaves correctly for a test that spans UTC midnight — the reset
  is a hard date boundary, not a rolling window.

### 33. Evaluation Layer

**What it is:** An on-demand, dataset-driven regression test of agent *quality* — does the agent
still correctly complete a curated set of representative tasks.
**Why it exists:** Model and prompt changes can silently change agent behavior in ways normal unit
tests can't catch; this runs real tasks through the real task engine against known test prompts and
checks the outcome.
**Where it lives:** `cortex/src/eval/` (`evalTaskDataset.ts` / `cortex/src/eval/data/`,
`evalTaskRunner.ts`, `evalJudge.ts`, `evalRunGetReportHandler.ts`); triggered from Pilot's
`/evals` screen (`pilot/app/evals/`, `pilot/components/evals/`).
**Technology:** TypeScript; runs through the real Task Manager and Agent Orchestrator (not a
separate simulated harness); uses an LLM (via the LLM Provider Layer) as a judge for
`llm_judge`-type checks.
**Input:** A curated dataset of test prompts, each with one or more ordered assertions
(`report_plan`, `final_output_contains`/`not_contains`, `llm_judge` questions) marked required
(`must_have`) or scored-but-non-blocking (`good_to_have`); an optional model override; an optional
case-ID subset.
**Output:** A per-case and per-run report: pass/fail per check, judge verdicts with cited evidence,
and aggregated cost/latency/token stats for the run.
**Calls next:** Task Manager (to create and drive each synthetic task), LLM Provider Layer (for the
judge model).
**How QA should validate it:**
- **Know this has no automatic trigger** — no CI hook, no schedule; it only protects against a
  quality regression if a human runs it before a change ships. If you're validating a model/prompt
  change, running this yourself (or confirming someone did) is a real, load-bearing QA step here,
  not optional polish.
- Understand most current cases check `report_plan` only — that the agent decided to act sensibly
  — rather than full task completion; don't assume a passing eval run means every case was
  verified end-to-end.
- Use the run report's cost/latency aggregates as a lightweight performance-regression signal too,
  not just a correctness check.

### 34. Analytics Event Publishing

**What it is:** Lightweight, fire-and-forget publishing of product events during request handling
(task created/completed/failed, receiver paired, feedback given, etc.).
**Why it exists:** Feeds the internal dashboards and analytics warehouse without coupling any
request's success to whether analytics succeeds.
**Where it lives:** `cortex/src/stats/` (`stats.ts`, `statsInit.ts`).
**Technology:** Google Cloud Pub/Sub (`@google-cloud/pubsub`), landing in BigQuery downstream for
the (out-of-scope-here) internal `dash` dashboards.
**Input:** Named event calls from various modules during normal request handling (e.g.
`CortexTaskCreated`, `CortexTaskCompleted`, `PilotAgentResponseLiked`).
**Output:** Published Pub/Sub messages; no return value consumed by the caller.
**Calls next:** Nothing the request path waits on — genuinely fire-and-forget.
**How QA should validate it:**
- Don't expect this to affect user-facing behavior at all if it fails — verify a request still
  succeeds normally even if event publishing is degraded (it's explicitly not on the critical
  path).
- If specifically validating analytics correctness (e.g. before a metrics-dependent release
  decision), that's a `dash`/data-quality concern downstream of this component, not something
  observable from the request itself.

---

## What you might expect that doesn't exist as its own component

A few items from common AI-agent architecture checklists were deliberately checked for and **not**
found as separate, standalone components. Naming this explicitly so you don't go looking for a
file that isn't there:

- **A dedicated Planner.** There is no separate planning phase or module that runs before
  execution. Planning is a *convention*, not a component: the model can call a `ReportPlan` tool as
  part of the same single-tool-call-per-step loop everything else uses (Component 9), and the
  cheapest evaluation checks (Component 33) specifically look for whether that call happened.
- **A standalone Request Router.** There's no module separate from the API Layer (Component 5)
  that does routing — Fastify's own route table, populated through a consistent
  `srvAddRoute`/module-prefix convention, fills that role directly.
- **A standalone Safety Layer.** No single module owns "safety." See Component 32 for where
  safety-relevant enforcement actually lives, spread across several independent components.
- **A standalone Retry System/module.** No generic retry framework or queue-level retry policy
  exists. See Component 31 — retry behavior is specific, conditional logic embedded in the Agent
  Orchestrator's own error handling.

---
**This completes the Phase 1 system map.** Documents [01](01_project_overview.md)–[03](03_request_lifecycle.md)
explain how these components behave together as a flow; this document is the index to come back to
when you need to know one component's job in isolation.
