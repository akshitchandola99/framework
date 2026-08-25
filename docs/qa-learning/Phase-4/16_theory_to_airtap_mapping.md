# 16 — Theory to Airtap Mapping (Master Index)

*Phase 4 · Document 4 of 4 — the capstone. This is the master cross-reference connecting the
`AI ROADMAP` study material to Airtap's real implementation, your QA responsibilities, and your
interview preparation, all in one place. It does not replace the deep-dive documents — it points
into them. Use this document to look something up fast; use
[05](05_llm_usage.md)–[08](08_prompt_pipeline.md) (Phase 2), [09](../Phase-3/09_qa_testing_strategy.md)–
[12](../Phase-3/12_debugging_checklist.md) (Phase 3), and [13](13_interview_questions_beginner.md)–
[15](15_interview_questions_advanced.md) (Phase 4) for full depth on any row.*

---

## How to read this document

Every concept below got pulled from the `AI ROADMAP` study notes and checked against the actual
Airtap codebase — nothing here is asserted without that verification having happened somewhere
upstream in this document set. Each one is tagged:

- **Status**: ✅ Used (confirmed, real implementation) · ⚠️ Partial (a real but incomplete version
  exists) · ❌ Not Used (confirmed absent, with the reasoning stated).
- **QA Priority**: 🔴 deepest coverage (high blast radius or core to correctness) · 🟡 high coverage
  · 🟢 standard coverage — the same risk-tiering logic from
  [09_qa_testing_strategy.md](../Phase-3/09_qa_testing_strategy.md), applied per concept instead of
  per subsystem.

Section A–D cover the 32 confirmed-used-or-partial concepts, grouped the same way Phase 2 grouped
them (LLM usage, agents/tools, memory, prompting) so this index lines up with material you already
know. Section E covers the concepts confirmed **not** used, in a lighter format, since most of the
seven dimensions don't apply to something that isn't implemented.

---

## Master Table

| # | Concept | Category | Theory (one line) | Airtap Subsystem(s) | Status | QA Priority |
|---|---|---|---|---|---|---|
| 1 | Multi-Vendor LLM Abstraction | LLM Infra | One contract normalizing many LLM providers | LLM Provider Layer (`omni`) | ✅ | 🟡 |
| 2 | Model Selection & Routing | LLM Infra | Assigning the right model to the right job by cost/capability | Model Registry (`mreg`) | ✅ | 🟡 |
| 3 | Tokens, Context Window & Cost | LLM Infra | Text as billed units; a hard per-call size limit | `omni` stats, credit/usage system | ✅ | 🟢 |
| 4 | Sampling Controls (Temperature/Top-P) | LLM Infra | Controls how deterministic vs. varied output is | `omni` canonical request | ✅ | 🟢 |
| 5 | Conversation Roles & Message Structure | LLM Infra | System/user/assistant/tool-result as distinct channels | `omni` canonical message model | ✅ | 🟢 |
| 6 | Reasoning Models / Extended Thinking | LLM Infra | Models that "think" before answering, at extra cost | `mreg` `reasoningLevel`, agent loop | ✅ | 🟡 |
| 7 | Multimodal Vision Input (VLMs) | LLM Infra | A model reasoning over images and text together | Screenshot capture + `omni` multimodal input | ✅ | 🟡 |
| 8 | Prompt / Context Caching | LLM Infra | Reusing a processed prompt prefix to cut cost | Stable/volatile system prompt split | ✅ | 🟢 |
| 9 | Rate Limits, Timeouts & Error Handling | LLM Infra | Detecting and recovering from transient provider failures | `omni` error taxonomy, retry handling | ✅ | 🟢 |
| 10 | AI Agent Definition | Agents | Autonomy over the sequence of steps, not just tool use | Agent Orchestrator (`yoda`) | ✅ | 🟡 |
| 11 | The Agent Loop & ReAct | Agents | Perceive → reason (written down) → act → observe, repeat | `yoda`'s per-step cycle | ✅ | 🔴 |
| 12 | Planning | Agents | Decomposing a fuzzy goal into concrete steps | `ReportPlan` tool | ✅ | 🟡 |
| 13 | Single-Agent Architecture | Agents | One loop, one model call per step, no agent handoffs | `yoda`, no multi-agent framework | ✅ | 🟢 |
| 14 | Tool Calling — Declaration | Agents | Describing available tools/schemas to the model | Tool Manager (`yodaTools.ts`) | ✅ | 🟡 |
| 15 | Tool Calling — Execution | Agents | The model proposes, trusted code disposes | Tool Executor (`AndroidActionRegistry`) | ✅ | 🔴 |
| 16 | Screen Understanding & Grounding | Agents | Connecting a decision to a real, exact screen location | Screenshot + UI dump, coordinate-based tap | ✅ | 🔴 |
| 17 | Action Space & Automation Layer | Agents | The bounded moves an agent can make, and what executes them | Accessibility Service / HID dongle (not ADB) | ✅ | 🔴 |
| 18 | Rule-Based Shortcuts vs. AI Decisions | Agents | Using a deterministic path when one exists, instead of AI guessing | `android-direct-actions` skill | ✅ | 🟢 |
| 19 | Retry Logic & Loop Avoidance | Agents | Stopping conditions so an agent doesn't loop forever | Playbook rules + step/duration caps | ✅ | 🟡 |
| 20 | Risk-Tiered Action Safety | Agents | Gating irreversible actions behind confirmation | Guardrails + `RequestClarification`/`RequestTakeover` | ⚠️ | 🔴 |
| 21 | Reflection & Self-Correction | Agents | The agent checking its own last action against reality | Single-pass self-verification (playbook §6.4) | ⚠️ | 🟡 |
| 22 | Evaluation & LLM-as-a-Judge | Agents | Grading non-deterministic output against a rubric, at scale | Evaluation Framework (`cortex/src/eval`) | ✅ | 🟡 |
| 23 | Memory Taxonomy | Memory | Short/long-term, semantic/profile/episodic/working memory | `umem` (4 files + daily notes) | ✅ | 🟡 |
| 24 | Context Compaction | Memory | Summarizing a growing conversation instead of truncating it | `yodaCompaction` | ✅ | 🟡 |
| 25 | Routine-Scoped Memory | Memory | A dedicated memory scope for one recurring job | Routine `executionMemory` | ✅ | 🟢 |
| 26 | Prompt Anatomy & System Prompt Design | Prompting | Role/instruction/context/constraints/format as prompt parts | `yodaSystemPrompt` + playbooks | ✅ | 🟡 |
| 27 | Chain-of-Thought (schema-enforced) | Prompting | Forcing reasoning before an answer, more reliably than asking nicely | `observe/review/plan` tool envelope | ✅ | 🟢 |
| 28 | Structured Output / JSON Mode | Prompting | Forcing schema-conformant output instead of free text | Tool-call schemas via `omni` | ✅ | 🟡 |
| 29 | Few-Shot vs. Zero-Shot Prompting | Prompting | How many worked examples to include in a prompt | Mostly zero-shot; few-shot in one skill | ✅ | 🟢 |
| 30 | Prompt Chaining | Prompting | Breaking one big task into a pipeline of smaller prompts | Compaction calls, enforced tool sequencing | ✅ | 🟢 |
| 31 | Prompt Injection (Security) | Prompting | Untrusted content hijacking the model's instructions | Screenshots of arbitrary apps/websites | ✅ (risk) | 🔴 |
| 32 | Prompt Versioning | Prompting | Treating prompts like reviewed, tested, gated code | Git-tracked template files | ⚠️ | 🟡 |
| — | RAG (Retrieval-Augmented Generation) | Not Used | Retrieve relevant text, then generate an answer from it | — | ❌ | 🟢 |
| — | Vector Databases / Embeddings | Not Used | Fast similarity search over meaning-encoded content | — | ❌ | 🟢 |
| — | Multi-Agent Frameworks | Not Used | Multiple specialized LLM agents handing off to each other | — | ❌ | 🟢 |
| — | Model Context Protocol (in-product) | Not Used | A shared standard for exposing tools to models | — | ❌ | 🟢 |
| — | Fine-Tuning / LoRA / QLoRA | Not Used | Adjusting a model's weights for a narrow behavior | — | ❌ | 🟢 |
| — | Distillation | Not Used | Training a small model to mimic a large one | — | ❌ | 🟢 |
| — | Token Streaming | Not Used | Sending output token-by-token as it's generated | — | ❌ | 🟢 |
| — | Local / On-Device Inference | Not Used | Running the model itself on the device, not the cloud | — | ❌ | 🟢 |
| — | A/B Testing Infrastructure | Not Used | Rolling a change to a slice of traffic and comparing | — | ❌ | 🟢 |

---

# Section A — LLM Usage & Infrastructure

## 1. Multi-Vendor LLM Abstraction

**Category:** LLM Infra | **Status:** ✅ Used | **QA Priority:** 🟡

**Theory**: Different LLM providers (Anthropic, OpenAI, Google, and others) each have their own
request format, response shape, and quirks. A product that calls more than one needs an
abstraction layer so the rest of the codebase can say "generate a response" without hand-writing
vendor-specific code at every call site — this is standard practice the moment a system needs
provider flexibility, redundancy, or per-task model choice.

**Where it appears in Airtap**: `omni`, the internal LLM abstraction layer — one canonical
request/response contract with per-vendor adapters for Anthropic (direct and Bedrock), Google,
and a shared adapter for the OpenAI-Responses-compatible vendors (OpenAI, OpenRouter, xAI, Groq).

**Why Airtap uses it**: different jobs are deliberately routed to different vendors/models for cost
and capability reasons (see #2), and every one of the roughly dozen call sites across the product
needs to work identically regardless of which vendor answers a given call.

**How to test it**: cross-vendor parity testing — run the same task through each configured
vendor and compare outcomes deliberately, don't just confirm each "works" in isolation.

**Common interview questions**: "How would you design a system that talks to multiple LLM
providers?" "What's the risk of a vendor-specific bug hiding behind a shared abstraction?" (full
answers: [05_llm_usage.md §1](05_llm_usage.md))

**Common production failures**: a vendor-specific feature gap surfacing as an unexpected failure
only on one model; a genuinely different underlying vendor error not normalizing to the correct
typed error, breaking downstream retry logic.

**Debugging techniques**: pull the raw vendor request/response for the failing call (captured
always, per call) — this is ground truth, bypassing any normalization that might be masking the
real issue; check whether the bug reproduces only on one specific vendor before assuming it's
universal.

---

## 2. Model Selection & Routing

**Category:** LLM Infra | **Status:** ✅ Used | **QA Priority:** 🟡

**Theory**: Not every request needs the most expensive, most capable model — routing easy requests
to a small/cheap model and reserving a flagship model for hard cases is one of the most consistently
cited cost-optimization patterns in production AI, with real deployments reporting large cost
reductions at similar quality.

**Where it appears in Airtap**: the Model Registry (`mreg`), a live, config-driven lookup — not a
dynamic difficulty classifier, but a fixed, purpose-based assignment (main loop, hardware-
constrained receivers, routines, title/memory/schedule-generation each get their own configured
model).

**Why Airtap uses it**: a UI status label doesn't need frontier reasoning; a hard multi-step
decision benefits from it. Making the assignment live-editable means the team can react to a new
model release or a cost spike without a deploy.

**How to test it**: re-verify grounding/tap accuracy specifically after any model swap — this is
genuinely model-specific and doesn't automatically carry over.

**Common interview questions**: "What's the difference between this and a true per-request
difficulty classifier?" "How would you test the router itself?" (full answers:
[14_interview_questions_intermediate.md Q8](14_interview_questions_intermediate.md))

**Common production failures**: a routing config change silently degrading a specific call type's
quality with no error thrown at all; a configured model becoming unavailable with no confirmed
fallback.

**Debugging techniques**: check the per-model aggregate dashboard (latency, failure rate, cost) for
a trend before diving into a single task; confirm which model actually answered a specific step via
its per-call debug record.

---

## 3. Tokens, Context Window & Cost Tracking

**Category:** LLM Infra | **Status:** ✅ Used | **QA Priority:** 🟢

**Theory**: Text is billed and processed in tokens, and every model has a maximum context window
(input + output combined) it can hold in one call. Token count is simultaneously a hard technical
ceiling and the direct driver of API cost.

**Where it appears in Airtap**: `omni`'s normalized per-call stats (input/output/cached/reasoning
tokens), used to compute cost, deduct user credit, and trigger context compaction (#24).

**Why Airtap uses it**: a multi-step task's cost is otherwise unbounded; without per-call tracking
there's no way to bill usage, detect a runaway task, or watch model cost/health in aggregate.

**How to test it**: confirm tracked cost matches actual usage (no drift); confirm compaction fires
at the right token threshold.

**Common interview questions**: "Why might a non-English prompt cost more?" "What's the
relationship between reasoning tokens and normal output tokens?" (full answers:
[13_interview_questions_beginner.md Q4](13_interview_questions_beginner.md))

**Common production failures**: a credit/cost figure drifting from actual billed usage; a UTC-
midnight daily-quota reset landing mid-test and looking like an unrelated failure.

**Debugging techniques**: per-call token breakdown in the model debug capture; aggregate per-model
cost dashboards for trend-level drift.

---

## 4. Sampling Controls (Temperature / Top-P)

**Category:** LLM Infra | **Status:** ✅ Used | **QA Priority:** 🟢

**Theory**: At every generation step a model produces a full probability distribution over the next
token; temperature and top-P control how a token actually gets picked from it — low values push
toward deterministic, consistent output, high values toward varied, less predictable output.

**Where it appears in Airtap**: pass-through, per-call-purpose knobs in `omni`'s canonical request;
configured via the Model Registry, not a single global setting.

**Why Airtap uses it**: an agent driving a UI generally wants consistent, reliable decisions; making
this configurable per call type lets different jobs (main loop vs. title generation) be tuned
independently.

**How to test it**: run identical tasks multiple times and track a success *rate*, not a single
pass/fail — this is the direct, hands-on version of testing non-determinism.

**Common interview questions**: "Why does the same prompt sometimes produce different valid
outputs?" "Does temperature 0 guarantee full determinism?" (full answers:
[13_interview_questions_beginner.md Q7](13_interview_questions_beginner.md))

**Common production failures**: N/A as a "failure" per se — the risk is a *test suite* built on
exact-match assertions against inherently variable output, producing false failures.

**Debugging techniques**: compare multiple runs of the same task side by side rather than treating
one run as definitive.

---

## 5. Conversation Roles & Message Structure

**Category:** LLM Infra | **Status:** ✅ Used | **QA Priority:** 🟢

**Theory**: Chat-tuned LLMs expect input organized into roles — system (developer instructions,
privileged), user, and assistant (the model's own prior turns) — rather than one flat text blob,
which is what lets one model be steered into very different behavior via the system role alone.

**Where it appears in Airtap**: `omni`'s canonical roles — `system`, `user`, `assistant`, and a
`tool_result` role tied to a specific prior tool call by ID.

**Why Airtap uses it**: keeps conversation history in one shape regardless of which vendor answers
a given step, which is required for model routing (#2) to work safely, and keeps tool-call
continuity correct across a multi-step task.

**How to test it**: confirm a `tool_result` always ties back to the correct prior tool call; confirm
the system role's rules are actually weighted above conflicting user/on-screen input.

**Common interview questions**: "Why would you cache part of a system prompt but not all of it?"
(full answers: [13_interview_questions_beginner.md Q6](13_interview_questions_beginner.md))

**Common production failures**: a broken tool-result-to-tool-call link (the model reacting to the
wrong action's outcome).

**Debugging techniques**: inspect the exact assembled prompt/message sequence for a step via the
per-call debug capture.

---

## 6. Reasoning Models / Extended Thinking

**Category:** LLM Infra | **Status:** ✅ Used | **QA Priority:** 🟡

**Theory**: Some models spend extra, billable computation deliberating internally before producing a
visible answer, trading latency and cost for better accuracy on hard, multi-step problems — a
configurable "effort" or "thinking budget," not a prompt trick.

**Where it appears in Airtap**: a per-model `reasoningLevel` configured in the Model Registry,
passed directly into the main decision call.

**Why Airtap uses it**: some agent decisions are genuinely hard (ambiguous screens, multi-step
planning around an obstacle) and benefit from a model that reasons before committing — configured
per model rather than blanket-enabled, matching the same cost/capability logic as #2.

**How to test it**: confirm reasoning tokens are visible in cost tracking (they're billed like
output tokens even though invisible to the user); check for expected latency changes when
reasoning is enabled/disabled via a routing change.

**Common interview questions**: "What's the cost trade-off of a reasoning model?" (full answers:
[05_llm_usage.md §6](05_llm_usage.md))

**Common production failures**: reasoning-token cost silently inflating a task's spend without a
corresponding visible symptom.

**Debugging techniques**: the captured reasoning trace itself is the fastest way to see *why* a
reasoning-enabled model made a confusing decision.

---

## 7. Multimodal Vision Input (VLMs)

**Category:** LLM Infra | **Status:** ✅ Used | **QA Priority:** 🟡

**Theory**: A Vision-Language Model accepts images and text together and reasons across both — the
category of model required for a system to "see" a screenshot at all; some frontier models remain
text-only even when strong at other tasks, so multimodality is a separate axis from raw capability.

**Where it appears in Airtap**: every device-perception step — a screenshot is sent as an image
content part in the canonical request; the Model Registry ensures the assigned model actually
supports images.

**Why Airtap uses it**: this is the literal mechanism that lets the product exist — without vision,
the agent can't perceive anything not captured by structured element data alone.

**How to test it**: apps with sparse/absent structured UI data (games, canvas views, WebViews) —
this is where vision has to carry the whole decision.

**Common interview questions**: "How does a model process an image alongside text?" (full answers:
[13_interview_questions_beginner.md Q11](13_interview_questions_beginner.md))

**Common production failures**: a stale (one-step-behind) screenshot being reasoned over — a
deliberate, conditional-refresh trade-off, not automatically a bug; illegible small text after
image compression.

**Debugging techniques**: inspect the exact screenshot used for a specific step's decision via the
per-call debug capture.

---

## 8. Prompt / Context Caching

**Category:** LLM Infra | **Status:** ✅ Used | **QA Priority:** 🟢

**Theory**: If a large prompt prefix is identical across many calls, some providers let you cache
the already-processed version so you don't pay to reprocess it every time — a major cost lever for
any system making many similar sequential calls.

**Where it appears in Airtap**: the system prompt's stable half (persona, playbook, tool
descriptions) is marked for caching; the volatile half (date, memory, routine context) never is.

**Why Airtap uses it**: a task is many sequential steps sharing an identical large prompt prefix —
caching it is a direct, high-leverage saving specific to this workload shape.

**How to test it**: confirm the "stable" half stays byte-identical across users/tasks of the same
receiver type — any per-user leakage into it silently breaks caching.

**Common interview questions**: "How does prompt caching save money?" (full answers:
[14_interview_questions_intermediate.md Q9](14_interview_questions_intermediate.md))

**Common production failures**: a silent cache-efficiency drop with zero correctness symptom to
flag it — a pure, easy-to-miss cost regression.

**Debugging techniques**: aggregate cache-efficiency figures in the per-model dashboard.

---

## 9. Rate Limits, Timeouts & Error Normalization

**Category:** LLM Infra | **Status:** ✅ Used | **QA Priority:** 🟢

**Theory**: Providers enforce rate limits and can time out or become momentarily unavailable — a
production system needs to detect the specific failure type and retry sensibly, neither blindly nor
forever.

**Where it appears in Airtap**: `omni`'s normalized error taxonomy (rate limit, model unavailable,
timeout, output validation), consumed by the agent job's bounded retry handling.

**Why Airtap uses it**: a transient hiccup shouldn't fail a whole multi-step task, but an
unbounded retry is its own risk ("a bug with a budget").

**How to test it**: confirm the retry window matches documentation per error type; specifically
re-test whether a not-yet-warm cloud-phone session is handled the same as other infra errors (a
known, worth-checking edge).

**Common interview questions**: "How should a production system handle rate limits?" (full
answers: [05_llm_usage.md §9](05_llm_usage.md))

**Common production failures**: a persistent failure retrying past its intended window; a known
gap error type not getting the same graceful handling as documented ones.

**Debugging techniques**: task failure reason code plus state timeline shows exactly which error
type ended the task and after how many attempts.

---

# Section B — Agents, Tools & Evaluation

## 10. AI Agent Definition

**Category:** Agents | **Status:** ✅ Used | **QA Priority:** 🟡

**Theory**: The dividing line between a chatbot, an assistant, a workflow, and an agent is autonomy
over the *sequence of steps* — an agent decides its own steps at runtime, acts, checks the result,
and adjusts; nobody wrote that sequence down in advance. Most production "AI agents" are actually
workflows, because workflows are cheaper and easier to test.

**Where it appears in Airtap**: the Agent Orchestrator (`yoda`) — no pre-written flowchart exists
for satisfying an arbitrary request.

**Why Airtap uses it**: the product has to handle any request across any app, which a hand-designed
flowchart-per-task-type can't scale to.

**How to test it**: confirm the agent genuinely re-plans when something unexpected happens, rather
than blindly continuing a rigid assumption.

**Common interview questions**: "How is an agent different from a chatbot or workflow?" (full
answers: [13_interview_questions_beginner.md Q10](13_interview_questions_beginner.md))

**Common production failures**: N/A as its own failure category — see #11 (the loop) and #16
(grounding) for where agent-shaped failures actually concentrate.

**Debugging techniques**: read the reasoning trail to distinguish deliberate adaptation from
accidental drift.

---

## 11. The Agent Loop & ReAct Pattern

**Category:** Agents | **Status:** ✅ Used | **QA Priority:** 🔴

**Theory**: Every agent reduces to one loop — perceive, think, act, observe, repeat. ReAct
(Reason+Act) is the specific pattern of forcing the model to write reasoning down *before* every
action; the written reasoning becomes part of its own context, making the next action more likely to
follow logically, and doubles as a free, human-readable debugging log.

**Where it appears in Airtap**: `yoda`'s per-step cycle; every tool schema requires an
`observe`/`review`/`plan` section before the actual action, enforced at the schema level, not just
requested in prompt text.

**Why Airtap uses it**: schema-level enforcement is stronger than a prompt request that can be
silently skipped under pressure; the reasoning trail is the single most valuable debugging artifact
in the whole product.

**How to test it**: confirm the reasoning is genuinely specific to the current situation, not
boilerplate filler that technically satisfies the schema.

**Common interview questions**: "What is ReAct, and why does writing reasoning down help?" (full
answers: [14_interview_questions_intermediate.md Q1](14_interview_questions_intermediate.md))

**Common production failures**: a reasoning failure (misunderstood the screen) versus a
grounding/execution failure (reasoned correctly, acted imprecisely) — conflating the two wastes
investigation time; a task stuck mid-loop with the job chain never re-enqueuing (self-heals only
after a ~24h sweep).

**Debugging techniques**: state timeline → step trace → full call capture, in that order — read the
reasoning before anything else when the symptom looks like a wrong decision, not a coded error.

---

## 12. Planning

**Category:** Agents | **Status:** ✅ Used | **QA Priority:** 🟡

**Theory**: Decomposing a fuzzy goal into concrete steps, ideally interleaved (decide-act-observe
one step at a time) rather than committed upfront, since an upfront plan is stuck with an invalid
rest-of-plan the moment one step fails.

**Where it appears in Airtap**: the `ReportPlan` tool, required by the playbook before substantive
execution on actionable requests, kept deliberately high-level when a matching skill might override
specific steps.

**Why Airtap uses it**: a visible, required plan is a cheap, gradeable artifact before anything
irreversible happens.

**How to test it**: plan quality is gradeable in isolation — Airtap's own evaluation framework
already does exactly this (cancel shortly after the plan is stated).

**Common interview questions**: "What's the difference between upfront and interleaved planning?"
(full answers: [06_agents_and_tools.md §3](06_agents_and_tools.md))

**Common production failures**: a plan that locks into brittle manual UI steps despite a matching
skill existing that should have been used instead.

**Debugging techniques**: read the stated `ReportPlan` output directly against what actually
happened afterward.

---

## 13. Single-Agent Architecture

**Category:** Agents | **Status:** ✅ Used | **QA Priority:** 🟢

**Theory**: Multi-agent systems (Planner/Executor/Reviewer or similar) add value when a task has
genuinely separable sub-jobs, but are otherwise pure overhead — more latency, more cost, more places
for information to get lost in a handoff. The mature default is single-agent unless there's a
concrete reason to split.

**Where it appears in Airtap**: `yoda` — one loop, one model call per step, no multi-agent
framework dependency anywhere in the codebase.

**Why Airtap uses it**: every step needs the same context (current screen) and the same capability
(decide one action) — there's no natural specialist-role split the way a research-then-write
pipeline has.

**How to test it**: N/A for handoff-specific bugs (they don't exist here); the applicable gap is
the absence of a live, independent reviewer catching a bad decision before it executes.

**Common interview questions**: "When would you use multi-agent over single-agent?" (full answers:
[14_interview_questions_intermediate.md Q12](14_interview_questions_intermediate.md))

**Common production failures**: N/A directly.

**Debugging techniques**: standard single-call reasoning-trail inspection (see #11).

---

## 14. Tool Calling — Declaration

**Category:** Agents | **Status:** ✅ Used | **QA Priority:** 🟡

**Theory**: Describing available tools (name, description, argument schema) to the model so it can
request one instead of only producing prose — the model decides, trusted code executes.

**Where it appears in Airtap**: the Tool Manager (`yodaTools.ts`), Zod-defined schemas, filtered per
receiver type before every single call.

**Why Airtap uses it**: without declared tools, the model can only produce text; per-receiver-type
filtering prevents the model from ever being offered a tool its current device has no way to
execute.

**How to test it**: test tool-list *exclusion* per receiver type as rigorously as inclusion.

**Common interview questions**: "How does an LLM 'decide' to use a tool?" (full answers:
[13_interview_questions_beginner.md Q9](13_interview_questions_beginner.md))

**Common production failures**: a tool leaked to a receiver type that can't execute it.

**Debugging techniques**: compare the offered tool list for a given receiver type against what
actually gets called.

---

## 15. Tool Calling — Execution

**Category:** Agents | **Status:** ✅ Used | **QA Priority:** 🔴

**Theory**: The model only ever *proposes* a tool call; trusted application code is what actually
runs it and returns a result — the entire safety and testability story for tool calling rests on
this split.

**Where it appears in Airtap**: one generic dispatch registry (`AndroidActionRegistry`) handling
every tool uniformly, whether device-touching or not.

**Why Airtap uses it**: uniform dispatch means the orchestrator needs no special-case logic per
tool, and keeps "model proposes, code disposes" enforced in exactly one place.

**How to test it**: three independent failure classes — wrong tool selected, malformed/wrong
arguments, or a tool failure result being ignored/mishandled — test each separately.

**Common interview questions**: "What's the security implication of the model never executing
anything itself?" (full answers: [14_interview_questions_intermediate.md Q2](14_interview_questions_intermediate.md))

**Common production failures**: an unregistered tool call not failing explicitly; a subtly wrong
argument (especially one influenced by untrusted content — see #31) producing a plausible-looking
but incorrect action.

**Debugging techniques**: compare the recorded tool call and its arguments directly against the
resulting device state.

---

## 16. Screen Understanding & Grounding

**Category:** Agents | **Status:** ✅ Used | **QA Priority:** 🔴

**Theory**: Grounding connects a model's decision ("tap login") to a real, exact screen location — a
model can be completely right about *what* to do and only approximately right about *where*, and
approximately right is simply wrong for a coordinate. This is a failure category with no classical
test-automation analogue. Serious systems combine screenshots (vision) with structured element data
(an accessibility tree) rather than relying on either alone.

**Where it appears in Airtap**: confirmed coordinate-based grounding (`Tap` takes `[x, y]`
directly), informed by screenshot **and** a structured "UI dump" together, per the playbook's own
instructions; no Set-of-Marks-style overlay found anywhere.

**Why Airtap uses it**: coordinate output works on anything visible, including apps with poor or
missing accessibility metadata; the UI dump sharpens accuracy without requiring a complete tree.

**How to test it**: track grounding accuracy as its **own** metric — a task can succeed despite a
grounding miss through retries, hiding real fragility if only task success is measured.

**Common interview questions**: "Why is grounding uniquely hard for GUI agents?" (full answers:
[14_interview_questions_intermediate.md Q3](14_interview_questions_intermediate.md))

**Common production failures**: a tap landing on the wrong (often visually adjacent) element;
coordinate misinterpretation after a model swap; layout shifts from an on-screen keyboard.

**Debugging techniques**: compare the exact screenshot at the decision moment against the resulting
tap coordinate and the next step's screenshot to see precisely where it landed versus where it was
intended.

---

## 17. Action Space Design & Automation Layer

**Category:** Agents | **Status:** ✅ Used | **QA Priority:** 🔴

**Theory**: The action space is the bounded set of moves an agent may make — smaller is more
reliable, and an explicit "done" action is required or the agent has no way to know when to stop.
Underneath, a real automation layer (commonly ADB, Accessibility APIs, or dedicated hardware)
translates a decision into an actual device action.

**Where it appears in Airtap**: a deliberately bounded action set (tap/swipe/type/launch/wait/...)
with `RespondToUser` as the "done" equivalent; execution via Android Accessibility Service and/or a
physical BLE-to-USB HID dongle — confirmed **not** ADB.

**Why Airtap uses it**: ADB requires developer mode a real end-user's phone won't have;
Accessibility Service needs no such setup; the HID dongle additionally makes input genuinely
indistinguishable from a human and is the only option at all on iOS.

**How to test it**: physical-hardware failure modes (BLE range, battery, USB seating) have no
software analogue and must be tested on real devices, not reasoned about from logs.

**Common interview questions**: "Why might a product avoid ADB deliberately?" (full answers:
[15_interview_questions_advanced.md Q4](15_interview_questions_advanced.md))

**Common production failures**: OEM battery-optimization killing a backgrounded receiver app; a
dongle out of range or dead; a screen locked mid-action.

**Debugging techniques**: for hardware-layer symptoms, check the physical device/dongle directly —
cloud-side logs alone can't distinguish "asleep" from "dead" from "out of range."

---

## 18. Rule-Based Shortcuts vs. AI-Driven Decisions

**Category:** Agents | **Status:** ✅ Used | **QA Priority:** 🟢

**Theory**: Not every action needs AI-driven visual grounding — when a deterministic mechanism
already exists for a well-defined action, using it is faster, cheaper, and immune to grounding
failure entirely (the same principle as skipping a vector DB for an exact-match ID lookup, applied
to actions instead of data).

**Where it appears in Airtap**: the `android-direct-actions` skill — fires native Android intents
directly for well-defined actions (alarms, calls, SMS, settings) instead of visually navigating to
them; deliberately unavailable on dongle receivers, which have no way to invoke an OS intent
programmatically.

**Why Airtap uses it**: a single deterministic call with no vision and no coordinates either fires
correctly or fails explicitly — it can't "almost" work.

**How to test it**: this is closer to classical API testing (right action string, right parameters)
than visual verification — a genuinely different test approach from the rest of Section B.

**Common interview questions**: "When would you skip the AI-vision path entirely?" (full answers:
[06_agents_and_tools.md §9](06_agents_and_tools.md))

**Common production failures**: this path silently unavailable on a receiver type mishandled by
falling back incorrectly, instead of gracefully using the normal vision-and-tap path.

**Debugging techniques**: confirm which path (direct intent vs. visual navigation) was actually
used for a given action before debugging it as if it were a grounding problem.

---

## 19. Retry Logic & Loop Avoidance

**Category:** Agents | **Status:** ✅ Used | **QA Priority:** 🟡

**Theory**: An agent without a stopping condition is "a bug with a budget" — it can retry a broken
action indefinitely, burning cost overnight. Real systems need max retries, max steps/duration, and
ideally a circuit breaker for repeated identical failures.

**Where it appears in Airtap**: two layers — prompt-level ("compare state, don't repeat a no-
progress action pattern," playbook §6.2) and code-level (bounded retry windows for specific error
types, an overall step cap, a ~24-hour stale-task sweep as a last resort).

**Why Airtap uses it**: the prompt layer handles the common case efficiently; the code layer is the
guaranteed backstop when it doesn't.

**How to test it**: construct deliberately repetitive/dead-end UI flows and confirm the agent
changes strategy — the loop-avoidance instruction is prompt-level only, not code-enforced, making
this a real, valuable place to find genuine AI-quality bugs.

**Common interview questions**: "How do you stop an agent from looping forever?" (full answers:
[06_agents_and_tools.md §10](06_agents_and_tools.md))

**Common production failures**: a genuinely stuck task not self-healing quickly (the safety net is
hours, not minutes).

**Debugging techniques**: task state history shows whether a job simply stopped re-enqueuing with no
error anywhere — the signature of an orphaned background job, distinct from a code-level failure.

---

## 20. Risk-Tiered Action Safety

**Category:** Agents | **Status:** ⚠️ Partial | **QA Priority:** 🔴

**Theory**: Because GUI-agent mistakes are often irreversible (a sent message, a purchase, a
deletion — no "regenerate response" undo), the mature response is a risk tier: safe to fully
automate, gated behind confirmation, or not yet safe to automate at all. This is the highest-value
answer a QA-background candidate can typically give in this space.

**Where it appears in Airtap**: general guardrails (never fabricate a credential; verify state
before acting), a preference for the safer variant of an action when one exists in the
`android-direct-actions` skill specifically, and two general escape hatches
(`RequestClarification`/`RequestTakeover`) — but **no confirmed formal, code-enforced three-tier
gate** exists that automatically forces confirmation for any action resembling a purchase or
deletion.

**Why Airtap (partially) uses it**: the informal, prompt-level version is cheap and present; a
formal gate would need every tool call to carry a risk classification, which wasn't found as
implemented.

**How to test it**: the single highest-blast-radius test category in the whole product — construct
tasks that plausibly approach an irreversible action across several different apps and directly
observe what happens today, rather than assuming protection exists.

**Common interview questions**: "How would you design a risk-tiered safety system for an
action-taking agent?" (full answers: [15_interview_questions_advanced.md Q5](15_interview_questions_advanced.md))

**Common production failures**: an irreversible-feeling action proceeding without confirmation in a
scenario where a reasonable person would expect one — a real, plausible, currently under-guarded
finding, not hypothetical.

**Debugging techniques**: read the reasoning trail immediately preceding a risky action to see
whether risk was considered at all.

---

## 21. Reflection & Self-Correction

**Category:** Agents | **Status:** ⚠️ Partial | **QA Priority:** 🟡

**Theory**: An agent checking its own last action against reality works well against an external,
objective signal (did the screen actually change as expected) and works badly when a model grades
its own subjective judgment with no outside signal — it tends to just agree with itself.

**Where it appears in Airtap**: folded into the same single decision call rather than a separate
critique pass — playbook §6.4 instructs treating visible app state as untrusted until verified; a
code-level heuristic separately detects at least one specific known bad state (a login wall)
independent of the model's own conclusion.

**Why Airtap (partially) uses it**: a fully separate reflection call would double the cost/latency
of every step for a benefit the roadmap itself is skeptical of without an external signal; the
targeted heuristic backstop is cheaper for the one case it covers.

**How to test it**: construct a scenario where self-verification *should* catch a mismatch (wrong
account selected, stale pre-filled field) and confirm whether it actually does — there's no second,
independent check behind the general case.

**Common interview questions**: "What's the risk with an agent that checks its own work?" (full
answers: [06_agents_and_tools.md §12](06_agents_and_tools.md))

**Common production failures**: a state mismatch that single-pass self-verification misses,
compounding into further wrong actions.

**Debugging techniques**: compare what the agent *believed* about the state (from its reasoning) to
what the screenshot actually shows at that moment.

---

## 22. Evaluation & LLM-as-a-Judge

**Category:** Agents | **Status:** ✅ Used | **QA Priority:** 🟡

**Theory**: An eval is a test where the assertion is a judgment call, not an equality check —
LLM-as-a-judge uses a strong model to grade output against a rubric when there's no exact-match
ground truth. Known judge biases: verbosity (favors longer answers), position (favors whichever
option is seen first), and drift (upgrading the judge silently shifts historical scores).

**Where it appears in Airtap**: `cortex/src/eval` — a curated dataset, deterministic checks
(plan-quality, output-content), and a reference-free LLM judge (yes/no questions against the full
trace), run through the real production task engine.

**Why Airtap uses it**: real tasks against a curated dataset, graded by a mix of cheap deterministic
checks and judge questions, is the practical answer to "did a prompt/model change quietly make the
agent worse."

**How to test it**: test the eval framework's *own* blind spots — no confirmed automatic trigger
(the single biggest gap identified across this whole document set), no confirmed judge-bias
mitigation.

**Common interview questions**: "What are LLM-judge failure modes?" "What is Eval Ops?" (full
answers: [14_interview_questions_intermediate.md Q10](14_interview_questions_intermediate.md),
[15_interview_questions_advanced.md Q6](15_interview_questions_advanced.md))

**Common production failures**: a shipped prompt/model regression with no eval run in its history at
all; a judge-model upgrade silently breaking baseline comparability.

**Debugging techniques**: read the judge's cited evidence for a verdict, not just its pass/fail;
check whether an eval run was actually attempted for a suspect change before assuming the framework
itself failed.

---

# Section C — Memory & Context

## 23. Memory Taxonomy

**Category:** Memory | **Status:** ✅ Used | **QA Priority:** 🟡

**Theory**: LLMs are stateless by default; memory is scaffolding built around that. It splits by
duration (short-term, inside the context window vs. long-term, in a separate store) and by kind
(episodic/conversation — raw history; semantic — distilled facts; profile — a stable "who is this"
record; working — a scratchpad for the current task). The hard design problem is curation: what's
worth keeping, and how stale/contradicted facts get handled.

**Where it appears in Airtap**: `umem`, a per-user Firestore-backed store — a profile file (user
facts), a long-term file (semantic, written by a dedicated cheap-model call after every task), daily
short-term files, plus persona/identity files that don't fit the taxonomy at all (agent
self-concept, not memory about the user). Within-task conversation history serves as
working/episodic memory for that task's duration.

**Why Airtap uses it**: without cross-task memory, every task starts as a stranger to the user;
restricting the automatic writer to only two of the files is a deliberate boundary keeping the
user's core profile under direct user control only.

**How to test it**: cross-user isolation first, always — a security property, not a quality one.

**Common interview questions**: "What types of memory does an agent need?" (full answers:
[14_interview_questions_intermediate.md Q5](14_interview_questions_intermediate.md))

**Common production failures**: a stale/contradicted fact continuing to be used (mechanics
unconfirmed — a genuinely open test question); cross-user contamination (severity: data breach).

**Debugging techniques**: memory is plain text — read the actual stored file for the account in
question directly, no special tooling required.

---

## 24. Context Compaction

**Category:** Memory | **Status:** ✅ Used | **QA Priority:** 🟡

**Theory**: Real systems handle an overflowing context window by summarizing older content rather
than either truncating blindly or failing outright — related to "lost in the middle," the effect
where models recall content from a long context's start/end more reliably than its middle.

**Where it appears in Airtap**: `yodaCompaction` — an extra, dedicated summarization LLM call
triggered once a step's input tokens cross a threshold; confirmed as a manual flow for some model
vendors specifically, presumed (not independently confirmed) to rely on native provider handling for
others.

**Why Airtap uses it**: a long task's growing history would otherwise threaten both cost and
model-recall quality; this bounds both reactively.

**How to test it**: force a task long enough to trigger at least one compaction event, then verify
continued coherence for several more steps.

**Common interview questions**: "Why do long-running agents need context compaction?" (full
answers: [13_interview_questions_beginner.md Q5](13_interview_questions_beginner.md))

**Common production failures**: a compaction summary dropping something the task still needed; a
"lost in the middle" recall failure on an instruction buried deep in a long prompt.

**Debugging techniques**: look for the visible "context automatically compacted" marker in the task
thread; check per-call token counts leading up to that point.

---

## 25. Routine-Scoped Memory

**Category:** Memory | **Status:** ✅ Used | **QA Priority:** 🟢

**Theory**: Not a core roadmap taxonomy category, but a natural extension: a recurring scheduled job
benefits from its own persistent memory scope, distinct from both single-run working memory and
general user profile memory, so it can "remember" its own run history specifically.

**Where it appears in Airtap**: a dedicated `executionMemory` field per routine, injected alongside
(not instead of) the user's general `umem` context whenever a task was spawned by a routine.

**Why Airtap uses it**: avoids polluting general user memory with routine run-bookkeeping, and
avoids routines interfering with each other's state.

**How to test it**: confirm isolation between different routines' memory scopes, and whether a
routine actually uses its memory to avoid repeating an action.

**Common interview questions**: N/A as a standalone commonly-asked question — usually folds into
memory taxonomy questions (#23).

**Common production failures**: cross-routine memory leakage; a routine not actually consulting its
own memory before repeating an action.

**Debugging techniques**: read the routine's stored `executionMemory` directly, same technique as
#23.

---

# Section D — Prompt Engineering

## 26. Prompt Anatomy & System Prompt Design

**Category:** Prompting | **Status:** ✅ Used | **QA Priority:** 🟡

**Theory**: A well-formed prompt covers role/persona, instruction, context, input, constraints,
output format, and optionally examples — most "the model is being dumb" complaints trace back to one
of these being missing or vague. The system prompt specifically is the developer's privileged,
persistent channel, weighted above conflicting user input.

**Where it appears in Airtap**: `yodaSystemPrompt` + the playbook markdown files, split into a
stable (cacheable) half and a volatile (per-call) half, with receiver-type-specific playbook
variants (cloud/physical, Android dongle, iOS dongle) — each with its own honest "receiver limits"
section.

**Why Airtap uses it**: the stable/volatile split is a direct cost optimization (#8); per-
receiver-type variants exist because real capability genuinely differs by device type.

**How to test it**: confirm the correct playbook variant loads for the correct receiver type — a
capability claim that doesn't apply to the current device is a real, testable bug.

**Common interview questions**: "What makes a good system prompt?" (full answers:
[13_interview_questions_beginner.md Q8](13_interview_questions_beginner.md))

**Common production failures**: a leaked capability claim on the wrong receiver type; a rule buried
mid-playbook followed less reliably than one near the start/end.

**Debugging techniques**: inspect the exact assembled prompt for a step via the per-call debug
capture.

---

## 27. Chain-of-Thought (Schema-Enforced Reasoning)

**Category:** Prompting | **Status:** ✅ Used | **QA Priority:** 🟢

**Theory**: Asking a model to reason step by step before answering reliably improves multi-step
accuracy — the classic version is a prompt instruction ("let's think step by step"); a stronger
version enforces it structurally, at the output-schema level, so it can't be silently skipped.

**Where it appears in Airtap**: the `observe`/`review`/`plan` fields required by every tool schema
— see #11 for the full loop-level treatment; this entry is the prompt-construction angle
specifically.

**Why Airtap uses it**: schema-level enforcement can't be quietly dropped the way a prompt
instruction can.

**How to test it**: confirm the reasoning fields contain genuine, non-generic content (see #11).

**Common interview questions**: "How would you make chain-of-thought more reliable than just
asking for it?" (full answers: [08_prompt_pipeline.md §3](08_prompt_pipeline.md))

**Common production failures**: see #11.

**Debugging techniques**: see #11.

---

## 28. Structured Output / JSON Mode

**Category:** Prompting | **Status:** ✅ Used | **QA Priority:** 🟡

**Theory**: Forcing a model to return schema-conformant output (not just valid JSON, but output
matching *your* exact schema) so it can feed code directly. Providers implement the underlying
guarantee differently — constrained decoding for some, a tool-calling workaround for others — but
callers shouldn't need to care which.

**Where it appears in Airtap**: every agent decision *is* a tool call, which already is
schema-constrained structured output; some narrow auxiliary calls (title generation, schedule
parsing) plausibly use direct schema-constrained output instead of a tool call, though this wasn't
independently confirmed call-by-call.

**Why Airtap uses it**: free-form prose from the model would be unparseable by the code that has to
act on it.

**How to test it**: schema-validate under adversarial/malformed model output and confirm explicit
failure, not silent coercion; check whether a structured-output bug is vendor-specific (an adapter
gap) or universal (a schema/prompt bug).

**Common interview questions**: "What's the difference between JSON mode and structured output?"
(full answers: [13_interview_questions_beginner.md Q9](13_interview_questions_beginner.md) and
[08_prompt_pipeline.md §4](08_prompt_pipeline.md))

**Common production failures**: a malformed tool call exhausting its one corrective retry and
failing the task.

**Debugging techniques**: the raw model output in the per-call debug capture, before any
post-processing.

---

## 29. Few-Shot vs. Zero-Shot Prompting

**Category:** Prompting | **Status:** ✅ Used | **QA Priority:** 🟢

**Theory**: Zero-shot gives an instruction with no worked examples; few-shot includes several,
useful when a task is niche or the output format is strict and domain-specific. Example quality and
order matter more than raw count, and examples cost tokens on every call.

**Where it appears in Airtap**: the main playbook is almost entirely zero-shot (rule-based
instruction, not examples); the one confirmed few-shot pattern is the `android-direct-actions`
skill's worked intent examples, used specifically because that sub-task has a strict, demonstrable
output format.

**Why Airtap uses it**: the general loop has no fixed input/output pair to demonstrate; the one
skill that does use examples fits exactly the case the theory says few-shot is best for.

**How to test it**: if that skill's output format drifts, check whether its worked examples
themselves have gone stale or unrepresentative first.

**Common interview questions**: "When would you use few-shot over zero-shot?" (full answers:
[08_prompt_pipeline.md §5](08_prompt_pipeline.md))

**Common production failures**: N/A as a distinct production failure category; see #18 for this
skill's own applicable failures.

**Debugging techniques**: compare the skill's example list against its current real-world output
shape.

---

## 30. Prompt Chaining

**Category:** Prompting | **Status:** ✅ Used | **QA Priority:** 🟢

**Theory**: Breaking one big task into a pipeline of smaller, focused prompts, each feeding the
next — more reliable and debuggable than one mega-prompt, at the cost of latency, and vulnerable to
error propagation if nothing validates between steps.

**Where it appears in Airtap**: not the primary architecture (the main loop is a dynamic agent loop,
not a fixed chain), but real chaining patterns exist alongside it — the compaction call (#24) is a
genuinely separate chained call; the playbook enforces a fixed tool sequence
(`LaunchApp → ReportPlan → LoadSkill → execution`) for certain requests; memory/title/follow-on-
suggestion generation are each their own separate, narrow, chained calls.

**Why Airtap uses it**: narrow, well-defined sub-jobs benefit from a small focused prompt the same
way any chaining use case does, without needing the whole task to be a fixed pipeline.

**How to test it**: test each chained auxiliary call in isolation first; for the enforced sequence,
confirm a wrong early step (like the wrong app opened) doesn't silently compound through later
steps.

**Common interview questions**: "Does Airtap use prompt chaining?" (full answers:
[08_prompt_pipeline.md §6](08_prompt_pipeline.md))

**Common production failures**: error propagation from a wrong early step in the enforced sequence.

**Debugging techniques**: unit-test the chained auxiliary calls (title, memory, compaction)
independently of full task execution when one misbehaves.

---

## 31. Prompt Injection (Security)

**Category:** Prompting | **Status:** ✅ Confirmed risk | **QA Priority:** 🔴

**Theory**: An attacker smuggles instructions into a model's input so it ignores the developer's
original instructions — direct (the user types it) or indirect (hidden in content the model merely
reads). There's no clean "escaping" fix, because natural language *is* the instruction format; you
defend in depth. For an action-taking agent specifically, this is the highest-blast-radius category,
since a successful injection can trigger a real, sometimes irreversible action, not just leak text.

**Where it appears in Airtap**: every agent step reads a screenshot of arbitrary, untrusted app/
website content — a textbook indirect-injection surface, confirmed real rather than theoretical.
Existing mitigations: guardrails against leaking internal details, an instruction to treat visible
state as untrusted until verified. **Not confirmed**: any dedicated injection-detection step, or a
formal gate specifically blocking an irreversible action following suspicious content.

**Why this matters for Airtap specifically**: the product's core mechanism (reading arbitrary
screens) *is* the exposure — this isn't an edge case, it's structural.

**How to test it**: construct test pages/app states with visible adversarial instruction text and
confirm the agent doesn't comply; the must-have assertion is that no injected content can trigger an
irreversible action without a confirmation gate — a bar this product doesn't yet have a confirmed,
formal way to guarantee (ties directly to #20).

**Common interview questions**: "How do you mitigate prompt injection in an agent that reads
untrusted visual content?" (full answers: [15_interview_questions_advanced.md Q3](15_interview_questions_advanced.md))

**Common production failures**: internal-detail leakage under adversarial pressure; an injected
instruction influencing a tool call's arguments.

**Debugging techniques**: the reasoning trail after suspected adversarial content shows whether the
model noticed and reasoned about it, or acted without apparent awareness.

---

## 32. Prompt Versioning

**Category:** Prompting | **Status:** ⚠️ Partial | **QA Priority:** 🟡

**Theory**: Treat prompts as versioned, reviewed, tested artifacts — like code — gated on a golden
eval set before shipping, with fast rollback, since a small prompt wording change can measurably
shift behavior and cost across the entire user base.

**Where it appears in Airtap**: prompts are plain git-tracked files, so version control, diffs, and
PR review come for free; **not confirmed**: any automatic gate tying a prompt change to a golden-
eval-set regression run before merge — the Evaluation Framework (#22) that could serve this role
exists but isn't wired to CI or a merge gate.

**Why Airtap (partially) does this**: plain source files are the simplest way to get real version
control; the missing piece is wiring existing infrastructure into the release path, not building
something new.

**How to test it**: treat any playbook/template/skill-file change as a manual regression-testing
trigger until this is automated — a genuinely high-leverage thing to propose fixing.

**Common interview questions**: "How should prompts be treated in a production system?" (full
answers: [08_prompt_pipeline.md §8](08_prompt_pipeline.md))

**Common production failures**: a one-line prompt change shipping with no eval run in its history,
silently regressing behavior for every user of that prompt.

**Debugging techniques**: correlate the timing of a noticed quality regression against the git
history of prompt/template files for that time window.

---

# Section E — Confirmed Not Used

These are real, major concepts from the `AI ROADMAP` — worth knowing cold for an interview — that
are confirmed **absent** from Airtap. Each is genuinely useful to understand *why* it's absent, not
just that it is (see [04_ai_components_mapping.md](04_ai_components_mapping.md) for the full,
original verification of each).

| Concept | Theory (one line) | Why Airtap doesn't use it | What would change this |
|---|---|---|---|
| **RAG** | Retrieve relevant text, then generate an answer grounded in it | Per-user memory is small enough that full-context injection is simpler, cheaper, and has no retrieval-failure mode to debug | Memory size growing large enough to crowd out task context |
| **Vector Databases / Embeddings** | Fast approximate similarity search over meaning-encoded content | No retrieval pipeline exists to need one; under the roadmap's own ~10k-chunk threshold anyway | Same trigger as RAG above |
| **Multi-Agent Frameworks** | Several specialized LLM agents handing off to each other | Every step needs identical context and capability — no natural specialist-role split exists in this task shape | A genuinely separable, high-value role emerging — e.g., a live pre-execution reviewer (ties to #20's gap) |
| **MCP (in-product)** | A shared standard for exposing tools to models across systems | One agent, one small well-known tool set — interoperability benefit has little to attach to (MCP *is* used, but only for engineers' own dev tooling, unrelated to the product) | Needing to expose Airtap's tools to *other* agents, or rapidly integrating many external tool providers |
| **Fine-Tuning / LoRA / QLoRA** | Adjusting a model's weights for a narrow, consistent behavior | Behavior is steered entirely through prompting and model selection; no training infrastructure exists at all | A deep, high-volume behavior change prompting genuinely can't achieve |
| **Distillation** | Training a small model to mimic a large one's behavior | The same practical goal (cheap, fast model for a narrow job) is achieved via model *selection* (#2) instead of training | A need for genuinely on-device inference (see below) |
| **Token Streaming** | Sending output token-by-token as it's generated | The agent needs a complete, valid tool call before it can dispatch a device action — a partially-streamed JSON object isn't actionable | A shift toward chat-style, human-readable-as-it-generates output somewhere in the product |
| **Local / On-Device Inference** | Running the model itself on the device, not a cloud API | All decision-making is 100% cloud-side via `omni` — "on-device" in this product means on-device *action*, not on-device *inference* | Genuine offline requirements, or per-tap latency/cost becoming the dominant constraint |
| **A/B Testing Infrastructure** | Rolling a change to a slice of traffic and comparing outcomes | Confirmed absent by direct search — no experiment/variant/bucket system for prompts or models found | Needing to validate a risky prompt/model change against real traffic before a full rollout |

**Interview framing for this whole section**: the strongest answer isn't listing these as gaps — it's
being able to say precisely *why* each was skipped and *what specific, concrete signal* would change
that judgment. That's system-design thinking, and it's exactly what
[15_interview_questions_advanced.md Q12](15_interview_questions_advanced.md) walks through in full.

---

## Closing: how the whole document set fits together

```text
Phase 1 (architecture)  →  what the system is, how it's built
Phase 2 (AI theory)     →  which AI concepts it uses, and how
Phase 3 (QA strategy)   →  how to test, monitor, and debug it
Phase 4 (interview prep)→  how to talk about all of the above confidently
       ↑
This document — the index tying all four together, concept by concept
```

When in doubt about where to go next: if you need the *system*, go to Phase 1. If you need the
*theory*, go to Phase 2. If you need to *test or debug* something, go to Phase 3. If you need to
*explain* something, go to Phase 4 — and if you just need to know where any single concept lives
across all of that, come back here.
