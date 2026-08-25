# 09 — Runtime Request Walkthrough

*Phase 2 · Document 6 of 7. This document takes everything from [05](05_llm_usage.md)–
[08](08_prompt_pipeline.md) and lays it out as one annotated pipeline, tracing a single request
from the user to the response. Phase 1's [03_request_lifecycle.md](../Phase-1/03_request_lifecycle.md)
covers the full platform-level mechanics (state machine, retries, concurrency) — this document
overlays the AI-specific concept annotations on top of that same journey, matching the shape the
roadmap itself uses for "AI Product Architecture."*

---

## Starting point: the roadmap's own textbook diagram

The `AI ROADMAP`'s architecture phase gives this generic shape for a mobile/GUI agent product:

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
Action Executor (ADB / OS automation layer)
   ↓
Device / App State Change
   ↓
Verification (did the action produce the expected state?)
   ↓
Loop back to Planner (multi-step task), or return Final Response
```

Airtap's real pipeline is a genuine, close implementation of this shape — with a few real,
worth-naming differences: there's no separate "Planner" module (planning is one tool call inside
the same loop that also decides actions — see [06 §3–4](06_agents_and_tools.md)); there's no ADB
(see [06 §8](06_agents_and_tools.md)); and "Verification" isn't a separate stage so much as a
distributed set of checks layered across a few different places (schema validation, receiver-
reported status, and the next loop iteration's re-observation). The rest of this document is that
mapping, made precise and annotated.

---

## The annotated pipeline

```text
User
 ↓         [Pilot Web / Pilot iOS / Telegram / Linq]
API
 ↓         [Cortex API Layer — srv]
Task Manager + Job Queue
 ↓         [task + jq — creates the Task, schedules the first step]
Agent Orchestrator  ("Planner")
 ↓         [yoda.ts — decides what happens this step]
Memory
 ↓         [umem — read and injected, not a separate call]
Prompt Builder
 ↓         [yoda's prompt assembly + cortex/src/templates/]
LLM  (via the LLM Provider Layer)
 ↓         [omni → Anthropic / Google / OpenAI / xAI / Groq / OpenRouter / Bedrock]
Tool Selection
 ↓         [yodaTools.ts declares → androidActions.ts executes]
Android / iOS Automation
 ↓         [Device Command Router → Receiver RPC or Cloud HTTP → physical device or cloud VM]
Validation
 ↓         [distributed: schema validation + receiver status + next-loop re-observation]
Response  (or loop back to Agent Orchestrator for the next step)
```

Every stage below expands one row of that diagram with the four annotations you asked for:
**component name, repository location, technologies used, QA focus.**

---

### Stage 1 — User

| | |
|---|---|
| **Component name** | Pilot Web / Pilot iOS / Telegram bot / Linq (iMessage-SMS-RCS) |
| **Repository location** | `pilot/`, `pilot-ios/`, `cortex/src/tg/`, `cortex/src/linq/` |
| **Technologies used** | Next.js/React (web), Swift (iOS), Telegram Bot API webhook, `@linqapp/sdk` |
| **QA focus** | Confirm behavior is consistent regardless of entry point — a bug in *how a task behaves* should reproduce from any channel; a bug in *how it starts/replies* is more likely channel-specific. See Phase 1 [02](../Phase-1/02_high_level_architecture.md) for the full entry-point comparison. |

Not an AI concept itself, but the origin of the natural-language request that everything downstream
exists to interpret.

---

### Stage 2 — API

| | |
|---|---|
| **Component name** | API Layer |
| **Repository location** | `cortex/src/srv/` |
| **Technologies used** | Fastify, `class-validator` DTOs |
| **QA focus** | Not AI-specific — see Phase 1's [04_system_components.md §5](../Phase-1/04_system_components.md) for full coverage (auth, CORS, versioning). Relevant here only as the entry point that validates and hands the request to the Task Manager. |

---

### Stage 3 — Task Manager + Job Queue

| | |
|---|---|
| **Component name** | Task Manager, Job Queue & Background Workers |
| **Repository location** | `cortex/src/task/`, `cortex/src/jq/` |
| **Technologies used** | Firestore (task state), BullMQ on Redis (job queue) |
| **QA focus** | Not AI-specific — full coverage in Phase 1. Relevant here only as the mechanism that turns "a task was created" into "an Agent Orchestrator step gets scheduled." Remember: each step is a separate job, not an in-memory loop (Phase 1, [03 §the shape of this document](../Phase-1/03_request_lifecycle.md)). |

---

### Stage 4 — Agent Orchestrator ("Planner")

| | |
|---|---|
| **Component name** | Agent Orchestrator (internally `yoda`) |
| **Repository location** | `cortex/src/yoda/yoda.ts`, `yodaJobs.ts` |
| **Technologies used** | TypeScript; no ML of its own — orchestrates calls into every other AI component on this list |
| **QA focus** | See [06_agents_and_tools.md §1–2](06_agents_and_tools.md) in full. Focus areas: is this a genuine agent decision (autonomous step sequencing) versus the one deliberate workflow-like shortcut (`android-direct-actions`, [06 §9](06_agents_and_tools.md))? Is the `observe/review/plan` reasoning present and substantive on every step? |

**Roadmap-diagram mapping note**: the generic diagram's "LLM Planner" box maps onto this stage —
but there's no separate planner *module*. Planning (the `ReportPlan` tool call, [06 §3](06_agents_and_tools.md))
is one possible outcome of this same orchestrator's per-step decision, not a distinct upstream
phase that hands off to a different component.

---

### Stage 5 — Memory

| | |
|---|---|
| **Component name** | Memory (`umem`) |
| **Repository location** | `cortex/src/umem/` |
| **Technologies used** | Firestore-backed plain-text files, read directly (no embeddings/vector search — see [07 §5](07_memory_and_context.md)) |
| **QA focus** | See [07_memory_and_context.md §2](07_memory_and_context.md) in full. Cross-user isolation is the highest-priority check here. |

**Where this activates precisely**: memory is **read** at prompt-build time (Stage 6, folded into
the volatile system prompt) and **written** only at task-terminal states, via a separate background
job — not on every step. It's shown here as its own stage because it's a distinct, real component
the roadmap's generic diagram doesn't even have a box for (the textbook diagram jumps straight from
Planner to Screen Capture) — Airtap's real pipeline reads persistent cross-task memory on every
single step, which is a genuine addition beyond the generic shape.

---

### Stage 6 — Prompt Builder

| | |
|---|---|
| **Component name** | Prompt Builder (assembly logic inside `yoda.ts`, content in `cortex/src/templates/`) |
| **Repository location** | `cortex/src/yoda/yoda.ts`, `cortex/src/templates/*.mustache`, `*.md` |
| **Technologies used** | Mustache templating, Markdown playbooks |
| **QA focus** | See [08_prompt_pipeline.md](08_prompt_pipeline.md) in full — this stage is that entire document. Focus areas: correct playbook variant per receiver type, stable/volatile split staying clean (cache regression risk), and this being the stage where the screenshot (Stage 5's sibling, technically fetched just before this) gets folded in as multimodal input. |

**Screen State Capture, mapped**: the roadmap's diagram has a distinct "Screen State Capture"
box between Planner and VLM. In Airtap, this is a device round-trip (screenshot + UI dump) that
happens *before* the Prompt Builder runs, feeding directly into it — conditionally, not on every
step (Phase 1's [03 §2b](../Phase-1/03_request_lifecycle.md)). It's folded into this stage's
annotation rather than given its own row because, mechanically, it's an input the Prompt Builder
consumes, not a separate AI-reasoning stage of its own.

---

### Stage 7 — LLM (via the LLM Provider Layer)

| | |
|---|---|
| **Component name** | LLM Provider Layer (`omni`) + Model Registry (`mreg`) |
| **Repository location** | `cortex/src/omni/`, `cortex/src/mreg/` |
| **Technologies used** | `@anthropic-ai/sdk`, `@anthropic-ai/bedrock-sdk`, `@google/genai`, shared OpenAI-Responses-compatible HTTP client (OpenAI/OpenRouter/xAI/Groq) |
| **QA focus** | See [05_llm_usage.md](05_llm_usage.md) in full — this stage is most of that document (model selection, tokens, sampling, reasoning, vision input, caching, rate limits). |

**This is the "Vision-Language Model" box from the generic diagram**, made concrete: the actual
call that receives the screenshot + UI dump + prompt and returns reasoning + a tool call.

---

### Stage 8 — Tool Selection

| | |
|---|---|
| **Component name** | Tool Manager (declares) + Tool Executor (dispatches) |
| **Repository location** | `cortex/src/yoda/yodaTools.ts` (Tool Manager), `cortex/src/android/androidActions.ts` (Tool Executor — `AndroidActionRegistry`) |
| **Technologies used** | Zod schemas, an in-memory `Map<toolName, handler>` |
| **QA focus** | See [06_agents_and_tools.md §5–6](06_agents_and_tools.md) in full. Focus areas: tool availability correctly filtered per receiver type, and the three independent failure classes (wrong tool, malformed arguments, ignored/mishandled result). |

**This is also where "Action Decision" from the generic diagram lives** — the model's tool call
*is* the coordinate-target decision (see [06 §7](06_agents_and_tools.md) for grounding mechanics);
there's no separate downstream "decide where to tap" step distinct from the tool call itself.

---

### Stage 9 — Android / iOS Automation

| | |
|---|---|
| **Component name** | Device Command Router → Receiver Management & RPC (paired devices) or Cloud Phone Orchestrator Client (cloud phone) → on-device Android/iOS Controller |
| **Repository location** | `cortex/src/android/androidExecuteCommand.ts`, `cortex/src/rcvr/`, `cortex/src/orch/`, `receiver/`, `receiver-ios/` |
| **Technologies used** | Firestore RPC (paired devices), plain HTTP (cloud phone), Android Accessibility Service API, BLE-to-USB HID dongle |
| **QA focus** | See [06_agents_and_tools.md §8](06_agents_and_tools.md) and Phase 1's Device Layer documentation for the full, code-verified failure-mode list (physical hardware included). Confirm this is genuinely **not** ADB — see [06 §8](06_agents_and_tools.md) for why. |

**This is the generic diagram's "Action Executor" + "Device/App State Change" boxes, combined** —
in Airtap these are inseparable: dispatching the command *is* what changes the device state, over
whichever transport applies to this receiver type (Phase 1's [02](../Phase-1/02_high_level_architecture.md)
covers the cloud-vs-physical transport split in full).

---

### Stage 10 — Validation

| | |
|---|---|
| **Component name** | *Distributed — no single "Validation" component exists* |
| **Repository location** | `omni` (schema validation), `rcvr`/receiver apps (execution status), `yoda.ts` (next-step re-observation), the playbook (`yodaSystemPlaybook.md` §6.4, self-verification instructions) |
| **Technologies used** | Zod schema validation (deterministic), device-reported status codes (deterministic), LLM self-verification (probabilistic, prompt-driven) |
| **QA focus** | This is the stage most worth testing precisely *because* it's not one clean component — see below. |

**Worth stating precisely, not glossing over**: the generic diagram shows "Verification" as one
clean stage between Execute and Loop-back. Airtap's real verification is genuinely **three
different things layered together**, each catching a different failure class:

1. **Structural validation** (deterministic, code-level): did the model's tool call match its
   declared schema? `omni` fails this explicitly rather than tolerating a malformed call
   ([05 §1](05_llm_usage.md)).
2. **Execution-status validation** (deterministic, code-level): did the receiver report success, or
   a specific typed failure (screen locked, permission revoked, etc.)? Phase 1's Device Layer and
   Receiver Management documentation cover this fully.
3. **State verification** (probabilistic, prompt-level): did the action produce the *expected*
   screen state? This is not a separate code stage at all — it's the playbook's own instruction
   (§6.4: "treat any visible app state as untrusted until verified") applied by the model itself,
   at the start of the *next* loop iteration, when it looks at the new screenshot. Per
   [06_agents_and_tools.md §12](06_agents_and_tools.md), there is no dedicated, separate reflection/
   critique call independently double-checking this — it's folded into the same single decision
   call that then decides the next action.

**QA implication**: layers 1 and 2 are reliable, deterministic, and easy to assert on directly.
Layer 3 — the one that actually answers "did the tap land where the agent thinks it did" — is
exactly the layer with no independent backup if the model's single-pass self-verification misses
something. This is the single most concrete, testable version of the roadmap's own core claim for
this whole product category: *"the perception-action loop breaks at capture and verify, not at
decide."* Constructing scenarios where layer 3 specifically should catch a problem (a stale or
unexpected screen state) and confirming whether it actually does is one of the highest-value test
investments describable in this entire document set.

---

### Stage 11 — Response (or loop back)

| | |
|---|---|
| **Component name** | Task Manager (state resolution) + client realtime reflection |
| **Repository location** | `cortex/src/task/` (`taskResolveNextState`), `pilot/lib/firebase/client.ts` / equivalent in `pilot-ios` |
| **Technologies used** | Firestore `onSnapshot` listeners (a lightweight "ping," not the payload itself) + REST refetch |
| **QA focus** | Not AI-specific — fully covered in Phase 1's [03_request_lifecycle.md](../Phase-1/03_request_lifecycle.md) (Stage 2f–4). Relevant here only as the branch point: `RespondToUser`/`RequestClarification`/`RequestTakeover` end the loop; anything else requiring more work re-enqueues back to Stage 4. |

---

## A concrete worked trace

To make the pipeline tangible, here's one illustrative request traced through every stage (screen
content and exact field values are illustrative, not captured from a real run):

```text
User: "What was my last Amazon order?"
   │
   ▼ [Stage 1-3: entry point → API → Task created, first step job enqueued]
   │
   ▼ [Stage 4: Agent Orchestrator, step 1]
   │   No prior context. Decides: this is actionable → needs a plan.
   │
   ▼ [Stage 5: Memory read]
   │   umem.user.md: "prefers concise answers." Injected into volatile prompt.
   │
   ▼ [Stage 6: Prompt Builder]
   │   Stable half (cached): persona, playbook, tool schemas for this receiver type.
   │   Volatile half: memory snippet above, today's date, no routine context (user-initiated task).
   │
   ▼ [Stage 7: LLM call via omni]
   │   Model (per mreg's config for this receiver type) returns:
   │   observe: "No app open yet." review: "Need Amazon app or browser."
   │   plan: "Launch Amazon, go to orders." tool_call: ReportPlan(...)
   │
   ▼ [Stage 8: Tool Selection]
   │   ReportPlan dispatched — no device action, just recorded as the visible plan.
   │
   ▼ [Stage 10: Validation]
   │   Schema valid. No device action to verify yet.
   │
   ▼ [Stage 11: loop back — task not done]
   │
   ▼ [Stage 4: Agent Orchestrator, step 2]
   │   Playbook's launch-first rule + skill check → LaunchApp(Amazon), possibly LoadSkill(shopping)
   │
   ▼ [Stage 8→9: Tool Selection → Automation]
   │   LaunchApp dispatched → Device Command Router → (say) Receiver RPC →
   │   physical receiver executes → Amazon app opens
   │
   ▼ [Stage 10: Validation]
   │   Receiver reports success (deterministic). Next step's screenshot will confirm state (probabilistic).
   │
   ▼ [Stage 11: loop back]
   │
   ▼ [Stage 4-9, step 3+]
   │   Perceive: screenshot + UI dump show Amazon home screen (state verification of step 2's LaunchApp)
   │   Think: navigate to Orders → Tap(coordinates: [x, y]) on the Orders menu item
   │   Act: dispatched, executed
   │   ... (repeats: navigate → orders list → read latest order → possibly a screenshot for evidence)
   │
   ▼ [Stage 4, final step]
   │   observe/review/plan conclude the answer is found
   │   tool_call: RespondToUser("Your last order was ... on ...")
   │
   ▼ [Stage 11: Response]
       Task → COMPLETED. Firestore ping fires. Client refetches. Thread renders the final answer
       (plus any screenshot evidence). Background: umem memory-write job may fire (task ended).
```

Every step above involved a fresh Stage 4→10 pass; the loop only terminates at the
`RespondToUser` call in the final step.

---

## Where each AI-Roadmap phase actually activates

A single cross-reference, tying this pipeline back to the roadmap's own phase numbering:

| Pipeline stage | Roadmap phases that activate here |
|---|---|
| Agent Orchestrator | Phase 7 (Agents), Phase 8 (Agentic AI / ReAct) |
| Memory | Phase 11 (Memory) |
| Prompt Builder | Phase 3 (Prompt Engineering) |
| LLM call | Phase 2 (Transformers/LLMs), Phase 15 (Infrastructure: tokens, caching, routing) |
| Tool Selection | Phase 10 (Tool Calling), Phase 3's Function Calling section |
| Android/iOS Automation | Phase 9 (Multimodal/GUI/Computer-Use Agents) |
| Validation | Phase 9's perception-action-loop material specifically |
| (cross-cutting, every stage) | Phase 13 (Evals) and Phase 17 (Testing) — not a pipeline stage, but the lens every "QA focus" row above is written through |

---
**Next:** [10_component_reference.md](10_component_reference.md) — a fast, component-first lookup companion to this pipeline and to document 04's concept-first checklist.
