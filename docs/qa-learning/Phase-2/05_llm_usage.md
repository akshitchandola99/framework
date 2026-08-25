# 05 — LLM Usage

*Phase 2 · Document 2 of 7. Covers every Phase-2/Phase-15-style "how does Airtap actually talk to
an LLM" concept from the roadmap: providers, models, tokens, sampling, reasoning, vision input,
caching, and cost. See [04_ai_components_mapping.md](04_ai_components_mapping.md) for the full
concept checklist this document expands on.*

Every concept below follows the same six-part pattern: theory, implementation, where it activates
in a live request, why it exists, how to QA it, and an interview-style mapping.

---

## 1. The LLM Provider Abstraction Layer

### 1. AI Theory
An "LLM provider" is whichever company hosts and serves a model over an API — Anthropic, Google,
OpenAI, and so on. Each one has its own request format, response shape, and quirks. A product that
might call more than one needs an abstraction layer so the rest of the codebase can say "generate
a response" without caring which vendor answers.

### 2. Airtap Implementation
`cortex/src/omni/` — internally called "Omni." Owns one canonical request/response contract
(`omni.ts`) and a set of per-vendor adapter files: `omniAnthropic.ts` (Anthropic direct + Bedrock),
`omniGemini.ts` (Google), `omniResponses.ts` (a shared adapter for OpenAI, OpenRouter, xAI, and
Groq — these four all expose an OpenAI-Responses-compatible API surface), and
`omniChatCompletions.ts` (a reference Chat Completions path). Supporting files: `omniErrors.ts`
(normalized error taxonomy), `omniSchemaValidation.ts` (tool/structured-output validation),
`omniSerialization.ts`, `omniTracing.ts` / `omniLangfuseSetup.ts` (tracing, see Phase 1's
Telemetry component). Libraries: `@anthropic-ai/sdk`, `@anthropic-ai/bedrock-sdk`, `@google/genai`,
plus a shared HTTP client for the OpenAI-Responses-family vendors. Routing is by a `vendor/model`
string (e.g. `anthropic/claude-...`) — the `vendor` prefix is looked up in a fixed dispatch table;
the vendor is **never** inferred from the model name itself.

### 3. Runtime Workflow
```text
Agent Orchestrator (yoda)
   ↓  assembles prompt + tool schemas + model choice
omniGenerate()
   ↓  routes by vendor prefix
Vendor adapter (omniAnthropic / omniGemini / omniResponses / omniChatCompletions)
   ↓  translates canonical request → vendor wire format
Vendor HTTP API (Anthropic / Google / OpenAI / xAI / Groq / OpenRouter / Bedrock)
   ↓  vendor response
Vendor adapter
   ↓  translates vendor response → canonical OmniOutput (reasoning/text/tool_use + stats)
Agent Orchestrator (yoda) resumes with a normalized result
```
This layer activates on **every single LLM call anywhere in the system** — not just the main agent
step, but memory generation, title generation, RRULE parsing, eval judging, and follow-on
suggestions all pass through it too.

### 4. Why Airtap Uses It
Airtap genuinely needs multiple vendors — different models are assigned to different jobs by cost
and capability (see §2 below), and the product needs to be able to add, swap, or fail over a vendor
without rewriting every caller. Without this layer, every one of those call sites (roughly a dozen,
per the Phase 1 module research) would need its own vendor-specific request-building and
response-parsing code, and a single provider's outage or API change would require auditing the
whole codebase instead of one adapter file.

### 5. QA Perspective
- **Vendor-specific bugs are real and expected, not automatically suspicious.** The support matrix
  in `omni`'s own `AGENTS.md` documents genuine per-vendor gaps (e.g., parallel-tool-call
  suppression isn't fully enforced on Google; some vendors only support text-only tool results). If
  a behavior differs specifically "when the task used model X but not model Y," check that matrix
  before assuming it's an application bug.
- **Debugging tool**: every call's exact vendor request and vendor response are captured, always,
  in Phase 1's Task Debug & Trace Capture component (`taskOmniDebug`) — this is the fastest way to
  confirm whether a wrong decision came from a bad prompt, a vendor quirk, or a parsing bug in the
  adapter.
- **Failure normalization**: confirm that a genuinely different underlying vendor error (rate
  limit vs. timeout vs. malformed output) actually surfaces as the correct normalized `Omni*Error`
  type, since downstream retry behavior (§9) branches on it.
- **Logs to check**: `taskOmniDebug` (per-call, complete), Langfuse trace for the task (per-call,
  opt-in — Phase 1's Telemetry component), `dashGetLlmHealth` for aggregate per-model latency/cost/
  failure-rate trends.

### 6. Interview Mapping
- **"What is an LLM provider abstraction?"** → A layer that normalizes different vendors' APIs
  behind one contract so callers don't need vendor-specific code.
- **"What does Airtap use for it?"** → `omni`, a custom-built internal module — not a third-party
  SDK like LangChain's model abstraction.
- **"Why was this design chosen?"** → Airtap genuinely routes different jobs to different vendors
  for cost/capability reasons, and needs every call site (agent steps, memory, evals, etc.) to work
  identically regardless of which vendor is behind a given model.
- **"What would you test?"** → Cross-vendor behavior parity for the same task (does the same
  prompt produce comparably correct tool calls on Claude vs. Gemini vs. GPT?), and that every
  vendor-specific error correctly normalizes to the right `Omni*Error` type so retry logic behaves
  consistently.

---

## 2. Model Families, Types & Selection

### 1. AI Theory
"Model family" tells you who built a model (GPT/OpenAI, Claude/Anthropic, Gemini/Google...).
Separately, any model can be described along independent axes: base vs. instruct-tuned, dense vs.
Mixture-of-Experts, open-weight vs. closed/API-only, standard vs. reasoning, text-only vs.
multimodal, general vs. domain-specific. A real product picks specific models along these axes for
specific jobs, not "the best model for everything."

### 2. Airtap Implementation
`cortex/src/mreg/` (`mreg.ts`, `mregGetModelHandler.ts`) is the Model Registry. Each configured
model entry (`MregModelInfo`) carries the `vendor/model` FQN, a coordinate system it expects for
tap targets (`androidCoordinateMode`: device pixels, normalized 0–1000, or preprocessed vision
pixels), pricing, and inference config (including `reasoningLevel`, §6). This config lives in the
**live** Firestore document `ConfSubEnv` (Phase 1's config model) — editable without a redeploy.
Confirmed vendor families in active use: Anthropic (Claude, direct and via Bedrock), Google
(Gemini), OpenAI, xAI (Grok), Groq, and OpenRouter. All are instruct/chat-tuned, closed/API-only
models — Airtap uses **no** open-weight, self-hosted models. Multiple purposes get distinct default
models: the main agent loop, a lighter model specifically for iOS/Android dongle receivers, a
routine-triggered default, and small auxiliary models for title generation, memory generation, and
routine-schedule parsing (a fast/cheap model), plus a different model again for UI-facing
step-summary generation.

### 3. Runtime Workflow
```text
Task/step about to call the LLM
   ↓  "what model powers this purpose, for this receiver type?"
Model Registry (mreg) — looks up live ConfSubEnv config
   ↓  returns modelFqn + androidCoordinateMode + pricing + inference config
Agent Orchestrator / LLM Provider Layer (omni)
   ↓  uses that exact model + config for this call
```
This activates at the **start** of essentially every LLM call in the system — before the prompt is
even sent, something has to decide which model answers it.

### 4. Why Airtap Uses It
A single "always use the best model" policy would be both slow and expensive for calls that don't
need frontier reasoning — a UI status label doesn't need the same model as a hard multi-step
planning decision. Splitting model choice by purpose is a direct, deliberate cost/capability
trade-off, and making it a **live config** (not hardcoded) means the team can shift models — say,
in response to a new model release or a cost spike — without shipping a code change.

### 5. QA Perspective
- **Coordinate accuracy is model-specific, not universal.** `androidCoordinateMode` varies per
  model entry — swapping the model behind a receiver type can change how tap coordinates are
  interpreted. Re-verify tap/swipe accuracy specifically after any model-routing config change,
  not just "does it still respond."
- **Live-config risk**: because this is hot-editable, a mid-day model swap in production is a real,
  reachable event — not just a deploy-time concern. Worth confirming who can make this change and
  whether it's audited.
- **Logs/dashboards**: `dashGetLlmHealth` (Phase 1) is the aggregate view — per-model latency, p95,
  failure rate, stop-reason breakdown, and cost; a bad model swap should be visible there quickly.
- **Edge case**: verify the fallback/behavior when a configured model becomes genuinely unavailable
  (deprecated, vendor outage) — is there a fallback model, or does the task simply fail?

### 6. Interview Mapping
- **"What's the difference between model family and model type?"** → Family = vendor (Claude vs.
  GPT). Type = independent axes (reasoning vs. standard, multimodal vs. text-only, etc.) that apply
  regardless of vendor.
- **"What does Airtap use for model selection?"** → `mreg`, a live-config-driven registry, not a
  dynamic per-request classifier — it's "the right fixed model for this purpose," not "route this
  specific request based on how hard it looks."
- **"Why was this design chosen?"** → Cost and latency vary enormously by task type; a
  config-driven, purpose-based assignment gets most of the benefit of routing without needing a
  live difficulty classifier.
- **"What would you test?"** → Grounding/tap accuracy after any model swap, and that the live
  config change actually propagates to every running backend instance without a restart.

---

## 3. Tokens, Context Window & Cost Tracking

### 1. AI Theory
Text is billed and processed in tokens, not characters or words. Every model has a maximum context
window — the total tokens (input + output) it can hold in one call — and since pricing is
per-token, tracking token counts is both a technical necessity (don't exceed the window) and a
direct cost-control concern.

### 2. Airtap Implementation
`omni`'s canonical stats (defined in `omni.ts`, normalized per vendor by each adapter) capture:
request latency, total input tokens, cached input tokens, cache-created input tokens, output
tokens, reasoning output tokens (a breakdown *within* output tokens, not additional to it), and
`costUsd` — computed centrally from these normalized stats plus `mreg`'s pricing config, so
individual adapters never invent cost math themselves. Every step's stats are persisted alongside
the step content in one Firestore transaction that also deducts the user's credit balance (Phase 1
finding). Context-window pressure specifically is what triggers context compaction (see
[07_memory_and_context.md](07_memory_and_context.md)) — the previous step's input token count is
checked against a configured threshold before building the next prompt.

### 3. Runtime Workflow
```text
LLM call returns
   ↓
Vendor adapter extracts raw usage figures from the vendor response
   ↓
Omni normalizes them into canonical stats (input/output/cached/reasoning tokens)
   ↓
Cost calculated centrally (stats × mreg pricing)
   ↓
Persisted with the step + credit deducted (one Firestore transaction)
   ↓
Visible in: task cost totals, dashGetLlmHealth, eval run reports, taskOmniDebug
```

### 4. Why Airtap Uses It
A task can run for many steps, each with its own LLM call(s) — cost is genuinely unbounded per
task without tracking (the same concern the roadmap raises about agents generally). Without
per-call token accounting, Airtap couldn't bill usage against a daily credit limit, couldn't detect
a runaway task early, and couldn't build the cost/latency dashboards the team actually uses to
watch model health.

### 5. QA Perspective
- **Credit-deduction accuracy**: confirm the credit charged for a task matches its actual tracked
  token cost — a drift here is a billing bug, not just a display bug.
- **Compaction threshold**: verify a long task actually triggers compaction at the expected input
  token count, and that a compacted task doesn't silently lose critical earlier context.
- **UTC daily-quota edge case** (cross-reference with Phase 1): a test spanning UTC midnight can see
  the daily spend limit reset mid-run — a legitimate source of confusing "why did behavior change
  mid-test" reports.
- **Logs**: `taskGetModelDebug`/`taskOmniDebug` for per-call token breakdowns; eval run reports for
  aggregate cost/latency per run (confirmed to include this in Phase 1's eval research).

### 6. Interview Mapping
- **"What is a context window?"** → The fixed maximum tokens (in + out) a model can process in one
  call.
- **"What does Airtap use to manage it?"** → Per-call token stats tracked through `omni`, plus a
  compaction mechanism (`yodaCompaction`) that summarizes history once input tokens cross a
  threshold.
- **"Why was this design chosen?"** → A multi-step agent task can't predict its own length in
  advance; tracking tokens per call and compacting reactively is simpler and more robust than
  trying to pre-budget an unknown number of steps.
- **"What would you test?"** → Cost/credit accounting correctness, and that compaction preserves
  enough context for the task to continue coherently.

---

## 4. Sampling Controls (Temperature, Top-P)

### 1. AI Theory
At each generation step, a model produces a full probability distribution over its vocabulary.
Temperature and top-p control how a token actually gets picked from that distribution — low
temperature is close to deterministic ("always pick the most likely token"); high temperature
allows more variety. This is the direct, hands-on source of LLM non-determinism.

### 2. Airtap Implementation
`omni`'s canonical request supports `temperature` and `topP` as provider-neutral, pass-through
inference hints (confirmed directly in `omni`'s own `AGENTS.md`); a `null` value means "omit and
let the provider apply its own default." No `topK` parameter is present in the canonical contract.
**What was not directly confirmed in this research**: the specific temperature/top-p values
actually configured for Airtap's production agent-loop calls versus its auxiliary calls (title
generation, memory generation, etc.) — that lives in the live `mreg`/`ConfSubEnv` model config data
itself, which wasn't inspected at that level of detail. This is stated explicitly rather than
guessed; check the current `ConfSubEnv` document for the live values.

### 3. Runtime Workflow
```text
Model Registry (mreg) resolves inference config for this call's purpose
   ↓  (may include temperature / topP, or null = provider default)
LLM Provider Layer (omni) passes these through to the vendor adapter
   ↓
Vendor applies them during token sampling
```

### 4. Why Airtap Uses It
An agent choosing UI actions generally needs reliable, repeatable decisions rather than creative
variety — the same screen and the same instruction should usually produce the same kind of
decision. Exposing these as configurable, per-call-purpose knobs (rather than one global setting)
lets different call types (the main decision loop vs. a title-generation call, which might
reasonably want more lexical variety) be tuned independently.

### 5. QA Perspective
- **This is the direct, hands-on source of the "same prompt, different valid outputs" problem**
  the roadmap calls out — exact-match assertions on agent decisions are structurally unreliable.
  Test for a *distribution* of acceptable behavior (does the agent complete the task correctly
  across N runs?), not a single expected trace — this is exactly the approach Airtap's own eval
  framework takes (checks rather than exact string matches; see
  [06_agents_and_tools.md](06_agents_and_tools.md)).
- **Regression testing tip**: if reproducibility matters for a specific investigation, check
  whether the relevant call's configured sampling is low/near-zero — that's the lever, if it's
  exposed for that call type.
- **Don't assume determinism even at low temperature** — some infrastructure-level randomness can
  remain even then, per general LLM behavior; a single non-reproduction isn't proof a bug doesn't
  exist.

### 6. Interview Mapping
- **"What does temperature control?"** → How sharply the model's next-token distribution is
  narrowed before sampling — low = consistent, high = varied.
- **"What does Airtap use it for?"** → A per-call, config-driven knob in `omni`'s canonical
  request; exact production values weren't directly confirmed in this investigation and should be
  checked in the live model config.
- **"Why would an agent product care about this?"** → An agent's actions have real consequences;
  favoring consistency over creativity is generally the right default for a UI-driving decision.
- **"What would you test?"** → Run identical tasks multiple times and measure success *rate*, not
  a single pass/fail — the standard mitigation for LLM non-determinism in testing.

---

## 5. Conversation Roles & Canonical Message Structure

### 1. AI Theory
Chat-tuned LLMs expect input organized into roles: a system message (developer instructions,
usually invisible to the end user), user messages, and the model's own prior assistant messages fed
back in so it has conversational continuity within the context window.

### 2. Airtap Implementation
`omni`'s canonical runtime message roles (directly from `omni`'s `AGENTS.md`): `system` (an
out-of-band, text-only instruction channel — not part of normal history replay),
`user` (caller input), `assistant` (the only model-output role — one assistant message may contain
ordered `reasoning`, `text`, and `tool_use` parts from a single logical turn), and `tool_result`
(the result of exactly one prior tool call, tied back to it by `tool_use_id`). Each vendor adapter
translates these canonical roles into that vendor's actual wire format (which may differ
significantly — e.g., Anthropic's separate top-level `system` parameter vs. a `system`-role message
in an OpenAI-style array).

### 3. Runtime Workflow
```text
Agent Orchestrator (yoda) assembles:
  system role   → stable (cacheable) + volatile prompt halves (see doc 08)
  user role     → the user's request / queued follow-up messages
  assistant role → prior steps' reasoning + tool calls
  tool_result role → results of prior device/tool actions
   ↓
LLM Provider Layer (omni) → vendor-specific wire translation → vendor API
```

### 4. Why Airtap Uses It
This is what makes model routing (§2) safe: because history is stored in one canonical shape
regardless of which vendor answered a given step, a task can (in principle) be served by different
vendors across its lifetime without the calling code needing to know or care about each vendor's
particular wire format. It's also what lets tool-call continuity work correctly — a `tool_result`
message is explicitly linked to the `tool_use` that produced it, so multi-step tool-using
conversations replay correctly.

### 5. QA Perspective
- **Tool-result linkage**: verify a `tool_result` always correctly ties back to the right prior
  `tool_use_id` — a broken link here would show up as the model reacting to the wrong tool's
  result, a confusing and hard-to-spot class of bug.
- **Reasoning continuity is vendor-scoped, not universal**: `omni`'s own docs are explicit that
  reasoning/thinking continuity artifacts from one vendor must never be replayed into a different
  vendor — a reasoning-continuity bug would be most likely to appear right after a model-routing
  change mid-investigation, not in steady-state use.
- **System prompt privilege**: confirm the system role's instructions are actually being weighted
  above conflicting user input (ties to prompt injection testing — see
  [08_prompt_pipeline.md](08_prompt_pipeline.md)).

### 6. Interview Mapping
- **"Why do LLM APIs use roles instead of one text blob?"** → It lets one model be steered
  differently per product/session via the system role, while keeping user and model turns
  distinguishable for context and safety.
- **"What does Airtap use?"** → A canonical four-role model (`system`/`user`/`assistant`/
  `tool_result`) in `omni`, translated per-vendor by each adapter.
- **"Why was this design chosen?"** → It decouples conversation history from any one vendor's wire
  format, which is required for `mreg`'s per-purpose model routing to work safely.
- **"What would you test?"** → Tool-result-to-tool-call linkage integrity, and that reasoning
  continuity tokens are never replayed across an incompatible vendor.

---

## 6. Reasoning Models / Extended Thinking

### 1. AI Theory
Some models spend extra, billable "reasoning" computation deliberating internally before producing
a visible answer — trading latency and cost for better accuracy on hard, multi-step problems.
Whether and how much a model reasons is usually a configurable "effort" or "thinking budget," not
an on/off prompt trick.

### 2. Airtap Implementation
Confirmed directly in `cortex/src/yoda/yoda.ts`: the main generation call explicitly passes
`reasoningLevel: modelInfo.omniInferenceConfig.reasoningLevel` — a value sourced from the Model
Registry's per-model config. Per `omni`'s `AGENTS.md`, this is treated as an opaque, provider-facing
hint string (not a normalized cross-vendor enum): `null` means "no explicit level, let the provider
default apply"; Anthropic specifically treats `'enabled'`/`'adaptive'` as thinking modes, while
other non-null Anthropic values are passed through as a top-level effort setting. Reasoning output,
when returned, is a distinct canonical output part and its token count is tracked separately
(`outputTokensReasoning`) inside — not in addition to — the overall output-token count.

### 3. Runtime Workflow
```text
Model Registry (mreg) resolves this model's configured reasoningLevel
   ↓
Agent Orchestrator (yoda) includes it in the omniGenerate() call
   ↓
Vendor adapter maps it to that provider's actual mechanism
   (Anthropic thinking config / OpenAI-family summary+include fields / Gemini includeThoughts / etc.)
   ↓
Canonical output may include a `reasoning` part alongside `text` and `tool_use`
   ↓
Reasoning tokens tracked in stats; reasoning content available in taskOmniDebug/Langfuse traces
```

### 4. Why Airtap Uses It
Some agent decisions are genuinely hard — an ambiguous screen state, a multi-step plan that needs
to account for an obstacle, distinguishing which of several similar-looking UI elements is correct.
A model that reasons before committing is more likely to get these right, at the cost of extra
latency and (billable) tokens — which is exactly why this is a **per-model, config-driven** choice
rather than a blanket setting: it's another instance of the same cost/capability trade-off that
drives `mreg`'s whole design.

### 5. QA Perspective
- **Cost visibility**: reasoning tokens are billed like output tokens even though the user never
  sees them directly — confirm they show up distinctly in cost tracking/dashboards rather than
  being invisible in a cost investigation.
- **Latency trade-off**: a model swap that turns reasoning on (or increases its level) is a
  legitimate, expected source of a latency regression — check `reasoningLevel` config before
  treating a latency change as a bug.
- **Debugging value**: when a task made a confusing decision on a reasoning-enabled model, the
  captured reasoning trace (via `taskOmniDebug` or Langfuse) is the most direct way to see *why* —
  read it before assuming the decision logic itself is broken.
- **Vendor-specific behavior**: reasoning continuity/replay is explicitly vendor-scoped (§5) —
  worth retesting after any change to which vendor handles a reasoning-enabled model.

### 6. Interview Mapping
- **"What's a reasoning model?"** → One that spends extra inference-time compute deliberating
  before answering, trading cost/latency for accuracy on hard problems.
- **"What does Airtap use it for?"** → A per-model `reasoningLevel` config, passed through
  `omni` into whichever vendor's actual thinking mechanism, used for models configured to warrant
  it.
- **"Why was this design chosen?"** → Not every agent step needs deep reasoning; making it a
  per-model, per-purpose config keeps the cost/latency trade-off deliberate rather than blanket.
- **"What would you test?"** → That reasoning tokens are visible in cost tracking, and that a
  reasoning-enabled model measurably improves outcomes on genuinely hard, ambiguous screen states
  versus a non-reasoning configuration.

---

## 7. Multimodal Vision Input

### 1. AI Theory
A multimodal (vision-language) model accepts images and text together and reasons across both — a
screenshot gets chopped into patches, each becomes an embedding, and the model's attention
mechanism lets text tokens and image content inform each other in the same pass. This is the
category of model required for a system to "look at" a screen at all.

### 2. Airtap Implementation
Screenshots captured from the device (Phase 1's device layer — `GetAndroidState`/
`device/screenshot` commands) are included as image content parts in the canonical message sent
through `omni`, which defines `image` as one of its canonical multimodal input part types (alongside
text, audio, video, and file). `mreg` ensures the model assigned to a given purpose actually
supports image input. Per the playbook (`yodaSystemPlaybook.md` §6.3), the screenshot is used
**together with** a textual "UI dump" (structured element/state data) — not vision alone — to
verify visible state and choose tap coordinates. This confirms the hybrid screen-understanding
pattern: vision for what's actually rendered, structured state data for precision, both feeding the
same decision.

### 3. Runtime Workflow
```text
Device action completes (or task starts)
   ↓
Fresh device context fetched: screenshot + UI dump (conditionally, per doc 03's finding —
   not on every step, only when the previous action touched the device)
   ↓
Screenshot becomes an image content part; UI dump becomes text content
   ↓
Both included in the next LLM call via omni (model confirmed multimodal-capable by mreg)
   ↓
Model reasons over image + text together → produces the next tool call, including tap coordinates
```

### 4. Why Airtap Uses It
Without vision, the agent would be blind to anything the structured UI dump doesn't capture well —
custom-rendered views, canvas/game surfaces, images, and generally any app that doesn't expose
clean accessibility metadata. Relying on the UI dump alone would make Airtap blind to a large slice
of real apps; relying on vision alone would be slower, more expensive (image tokens), and less
precise for exact element bounds. Using both together — exactly the roadmap's own recommended
hybrid pattern for mobile/GUI agents — covers each approach's blind spot with the other's strength.

### 5. QA Perspective
- **Screenshot freshness**: because the fetch is conditional (not every step), a decision can be
  made from a screenshot that's one step stale — confirmed in Document 3 of Phase 1. This is a
  legitimate, designed trade-off, not automatically a bug, but worth checking first when an agent
  seems to "not notice" a screen change.
- **Custom-rendered UI is the hardest test surface**: games, canvas views, and WebViews are where
  the UI dump is likely to be sparse or empty, making vision the *only* real signal — deliberately
  test against apps like this.
- **Image quality/cost trade-offs**: the Android receiver downscales and JPEG-compresses
  screenshots (Phase 1 finding — quality 25) — verify small text/icons remain legible enough for
  the model to read reliably at that compression level, especially on high-density displays.
- **Multimodal calls cost and latency more** than text-only ones (image tokens are expensive) —
  worth tracking as its own cost line in a latency/cost investigation.

### 6. Interview Mapping
- **"What's a VLM, and why does a GUI agent need one?"** → A model that reasons over images and
  text together; without it, the agent can't "see" a screenshot at all.
- **"What does Airtap use for screen understanding?"** → A hybrid: a multimodal model's vision over
  the screenshot, combined with a structured UI dump, feeding the same decision.
- **"Why was this design chosen?"** → Vision alone is imprecise and expensive; the UI dump alone is
  blind to custom-rendered content — using both covers each one's weak spot.
- **"What would you test?"** → Behavior on apps with little-to-no accessibility metadata (games,
  canvas UIs), and whether image compression settings degrade decision accuracy on small text.

---

## 8. Prompt / Context Caching

### 1. AI Theory
If a large chunk of a prompt (a long system prompt, a big retrieved context) is identical across
many calls, some providers let you cache the processed version of that prefix so you don't pay to
reprocess it every time — a direct, significant cost lever for any system that makes many similar
calls in a row.

### 2. Airtap Implementation
Confirmed in `cortex/src/yoda/yoda.ts`'s prompt-assembly logic: the system prompt is deliberately
split into a **stable half** (persona framing, coordinate instructions, the playbook, the skills
index) marked with `anthropicCacheControl: true`, and a **volatile half** (routine context, memory,
current date/location) that is never cached, since it changes every call. `omni`'s canonical
contract treats cache flags as hints/supplemental stats, not correctness behavior — unsupported
adapters may simply ignore them, and cache-related token counters (`cachedInputTokens`,
`cacheCreatedInputTokens`) are tracked normally in the shared stats layer regardless of vendor.

### 3. Runtime Workflow
```text
Prompt Builder assembles: [stable system prompt (cache-marked)] + [volatile system prompt] + [history]
   ↓
Sent via omni to the vendor
   ↓
Vendor (if it supports prompt caching, e.g. Anthropic) reuses cached KV-state for the
   stable prefix on this and later calls within the cache window
   ↓
Cache hit/miss reflected in normalized stats (cachedInputTokens vs. fresh input tokens)
```
This activates on **every single agent step** — the stable prompt half is identical across an
entire task's steps (and across different users' tasks on the same receiver type), which is exactly
what makes it cacheable.

### 4. Why Airtap Uses It
A task is a chain of many sequential LLM calls, and the large, persona/playbook/skills-index half
of the prompt is identical across essentially all of them. Without caching, every single step would
re-pay (in both latency and cost) to reprocess that same large prefix from scratch — for a product
whose core cost driver is "many LLM calls per task," this is one of the most direct, high-leverage
savings available, exactly matching the roadmap's own framing of caching as "where real money is
saved."

### 5. QA Perspective
- **Regression risk**: a prompt-template change that accidentally moves per-user or per-task data
  into what's supposed to be the stable, cacheable half would silently break caching (and spike
  cost) without producing any obviously wrong output — a good deliberate regression test: confirm
  the stable prompt text is byte-identical across different users/tasks of the same receiver type.
- **Cache efficiency is a tracked metric**: `dashGetLlmHealth` (Phase 1) includes cache efficiency
  as a dashboard figure — a good place to spot a caching regression in production.
- **Vendor-specific**: caching is explicitly not guaranteed across every vendor — don't expect
  identical cache-hit behavior when a model-routing change moves a call to a different vendor.

### 6. Interview Mapping
- **"What is prompt caching?"** → Reusing a provider's already-processed representation of an
  identical prompt prefix, instead of reprocessing it on every call.
- **"What does Airtap use it for?"** → Its system prompt is split into a cache-marked stable half
  and an uncached volatile half, reused across every step of a task.
- **"Why was this design chosen?"** → A task is many sequential calls sharing an identical large
  prompt prefix — caching that prefix is a direct, high-leverage cost and latency saving.
- **"What would you test?"** → That the stable prompt half stays byte-identical across
  calls/users/tasks (a regression would silently break caching), and that cache-efficiency metrics
  are actually visible in the LLM-health dashboard.

---

## 9. Rate Limits, Timeouts & Error Normalization

### 1. AI Theory
Providers enforce rate limits (HTTP 429) and can time out or become momentarily unavailable. A
production system needs to detect these specific failure types and retry sensibly — not treat
every failure identically, and not retry forever.

### 2. Airtap Implementation
`omni`'s error taxonomy (`omniErrors.ts`) normalizes vendor-specific failures into typed errors,
including `OmniRateLimitError`, `OmniModelUnavailableError`, `OmniTimeoutError`, and
`OmniOutputValidationError` (confirmed in Phase 1's agent-loop research). These normalized types are
what `yodaJobs.ts`'s `yodaHandleRunTaskError` inspects to decide whether a failed step gets a
bounded automatic retry or fails the task outright.

### 3. Runtime Workflow
```text
Vendor call fails (429 / timeout / 5xx / malformed output)
   ↓
Vendor adapter classifies the raw error
   ↓
Normalized into a typed Omni*Error
   ↓
yodaHandleRunTaskError checks: is this error type on the retryable list?
   ↓
Yes → bounded retry window (e.g., roughly one retry for most Omni-layer errors)
No  → task marked FAILED with a specific reason code
```

### 4. Why Airtap Uses It
A transient rate limit or momentary provider hiccup shouldn't fail an entire multi-step user task —
but retrying indefinitely on a genuinely broken call is exactly the "bug with a budget" the roadmap
warns about for agents generally. Typed, bounded retry policy is the middle ground: resilient to
real transients, bounded against runaway cost/time.

### 5. QA Perspective
- **Test the retry boundary directly**: confirm rate-limit/timeout errors actually get retried
  within the documented window, and that a genuinely persistent failure still terminates instead of
  looping.
- **Known gap worth re-testing**: per the Phase 1 investigation, a "cloud session not ready" error
  was *not* found on the explicit retryable list the way other infrastructure errors are — starting
  a cloud-phone task the instant the phone is requested (before its session is warm) is a concrete,
  reproducible way to check this boundary case specifically.
- **Logs**: the task's failure reason code plus `taskStateTimeline` (Phase 1) show exactly which
  error type ended the task and after how many attempts.

### 6. Interview Mapping
- **"How should a production system handle LLM rate limits?"** → Detect the specific failure type
  and retry with a bounded window — not blindly, not forever.
- **"What does Airtap use?"** → A normalized `Omni*Error` taxonomy plus a bounded retry policy in
  the agent job's error handler.
- **"Why was this design chosen?"** → Distinguishes recoverable transients from real failures
  without risking an unbounded retry loop burning cost on a task that will never succeed.
- **"What would you test?"** → The exact retry-window boundaries per error type, and specifically
  whether known-gap error types (like a not-yet-ready cloud session) are handled as gracefully as
  the documented ones.

---

## What Airtap deliberately does not use here

Two closely related "LLM usage" concepts are confirmed **not** in use, worth stating plainly since
they're easy to assume by default (full reasoning already given in
[04_ai_components_mapping.md](04_ai_components_mapping.md)):

- **Streaming.** `omni`'s canonical output carries an `isStreaming` field that is hardcoded
  `false`, and the Anthropic adapter explicitly uses the SDK's non-streaming request type. This is
  architecturally sensible for a tool-calling agent loop: the system needs a **complete, validated
  tool call** before it can dispatch a device action — there's no meaningful way to "half-execute" a
  tap from a partially-streamed JSON object the way a chat UI can display partially-streamed prose.
- **Local / on-device model inference.** Despite the product's "on-device intelligence" framing,
  every LLM decision happens via a cloud API call through `omni` — there is no local or on-device
  model inference anywhere in this repository. The "on-device" part of the product is the *action*
  (the phone itself physically executing a tap via Accessibility Service or the HID dongle) and the
  *screenshot capture*, not the decision-making, which is 100% remote. This distinction is worth
  keeping precise, since it's a natural and common point of confusion.

---
**Next:** [06_agents_and_tools.md](06_agents_and_tools.md) — the agent loop itself: planning, tool calling, grounding, and evaluation.
