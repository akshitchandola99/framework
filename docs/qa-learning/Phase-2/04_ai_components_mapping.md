# 04 — AI Components Mapping

*Phase 2 · Document 1 of 7. This phase connects AI theory (the `AI ROADMAP` study notes) to
Airtap's actual implementation. Phase 1 ([docs/qa-learning/Phase-1/](../Phase-1/01_project_overview.md))
already covered the general system architecture — read that first if you haven't. This phase
assumes it.*

## What this document is

The `AI ROADMAP` folder is an 18-phase study curriculum (`Complete_AI_Roadmap_v2.md` plus seven
per-phase notes files) covering everything from neural-network basics to production AI systems.
This document goes through **every concept in it**, phase by phase, and gives a verdict:

- **✅ Used** — confirmed in the repository; see the linked document for the full six-part
  treatment (theory, implementation, runtime workflow, why, QA perspective, interview mapping).
- **⚠️ Partial** — some real element of the concept exists, but not the full pattern the roadmap
  describes; the notes explain exactly what's actually there.
- **❌ Not used** — checked directly against the repository (grep, direct file reads, or explicit
  findings from the Phase 1 investigation) and not found. Reasoning is given, not just the verdict.
- **🔧 Background only** — the concept describes something happening *inside* the third-party LLMs
  Airtap calls (Anthropic/Google/OpenAI/etc.), not something Airtap itself implements. Airtap
  depends on it working but has no code for it.

Every verdict here is grounded in the actual codebase — direct greps, direct file reads (prompt
templates, playbook, skill definitions, `omni`'s own `AGENTS.md`), and the deep module research
from Phase 1. Where something couldn't be confirmed either way, that's stated explicitly rather
than guessed.

## How to use this document

This is the index. If a row says ✅ or ⚠️, the linked document has the full breakdown. If a row
says ❌, the reasoning given here **is** the complete answer — there's no deeper document to chase,
because there's no implementation to describe.

---

## Phase 1 — AI Foundations

Almost all of Phase 1 is about how ML/DL models get *built* — training mechanics, neural network
internals. Airtap doesn't build or train any models; it calls hosted LLM APIs (Anthropic, Google,
OpenAI, xAI, Groq, OpenRouter, AWS Bedrock) through its `omni` abstraction. So this entire phase is
almost uniformly **background knowledge Airtap depends on but does not implement.**

| Concept | Status | Notes |
|---|---|---|
| AI / ML / DL hierarchy | 🔧 | Airtap sits at the top of this stack as a *consumer* of Generative AI (LLMs); it implements none of the layers underneath. |
| Rule-based AI | ⚠️ | Airtap is **not** rule-based at its core (the agent's decisions are LLM-driven), but real rule-based logic coexists alongside it — see [06](06_agents_and_tools.md) for the `android-direct-actions` skill, a deliberately deterministic (non-LLM-grounded) shortcut for well-defined actions like setting an alarm. |
| Supervised / Unsupervised / Reinforcement Learning | 🔧 | This is how the underlying vendor models were trained (including RLHF — Phase 14). Airtap does none of this training itself. |
| Train/validation/test split, cross-validation | ❌ | No model training happens in this repository, so there's nothing to split or cross-validate. The closest conceptual cousin — a held-out golden dataset used to check quality before shipping a change — exists for **prompts**, not trained weights; see the Evaluation Layer in [06](06_agents_and_tools.md). |
| Epoch, batch, parameters, learning rate | ❌ | No training infrastructure exists in this repository. |
| Overfitting / underfitting | ❌ | Not applicable — no training. The eval golden-set regression check ([06](06_agents_and_tools.md)) is the nearest real analogue for "did a change quietly make things worse," but it's a prompt/agent-behavior check, not a model-fit check. |
| Neural network internals (neurons, layers, backprop, activation functions) | 🔧 | Entirely inside the vendor models Airtap calls; no code in this repository touches this layer. |
| CNN / RNN / LSTM | 🔧 | Same — architecture history of the models Airtap consumes, not something implemented here. |
| Generative AI | ✅ | This is the category the whole product sits in — every agent decision, and the `GenerateImage`/`EditImage` tools, are generative-AI calls. See [05](05_llm_usage.md). |
| GPUs, training infrastructure | ❌ | Airtap self-hosts no models and runs no training or inference hardware; it is a pure API consumer of hosted LLM providers. |
| AI Lifecycle (train → deploy → monitor → retrain) | ⚠️ | Airtap has no train/retrain step (it doesn't own model weights). It does have a real "monitor" step (Phase 1's Observability documents), and a rough analogue of "deploy → validate" for *prompts* (see prompt versioning in [08](08_prompt_pipeline.md)). |

---

## Phase 2 — Transformers & LLMs

Mixed: the Transformer *internals* are vendor-side background; the LLM *usage* concepts (context
window, sampling, roles, model types) are things Airtap directly configures and depends on. Full
detail in [05_llm_usage.md](05_llm_usage.md).

| Concept | Status | Notes |
|---|---|---|
| Tokens & tokenization (BPE) | 🔧 | Happens inside the vendor's model. Airtap doesn't tokenize text itself, but it **does** track token counts as a first-class cost/stats concern (input, output, cached, reasoning tokens) — see [05](05_llm_usage.md). |
| Embeddings (inside a Transformer) | 🔧 | Internal to the vendor model. Not to be confused with Phase 4's embeddings-as-a-tool, which Airtap does **not** use at all — see Phase 4–6 below. |
| Context window | ✅ | Directly managed — Airtap tracks input token counts per step and triggers context compaction when a threshold is crossed. See [05](05_llm_usage.md) and [07](07_memory_and_context.md). |
| Self-attention, multi-head attention, positional encoding | 🔧 | Purely internal to the vendor model's architecture; nothing in this repository implements or configures these directly. |
| Next-token prediction | 🔧 | The generation mechanism inside every vendor model call; not something Airtap's code touches. |
| Training vs. inference (LLM-specific) | 🔧 | Airtap only ever performs inference (calling a frozen, already-trained model). |
| Hallucinations | ✅ | A real, named risk for an agent that takes physical actions. See the guardrail discussion (`"Never hallucinate username, phone number, passwords"` in the playbook) and the eval/judge mitigation in [06](06_agents_and_tools.md). |
| Temperature, Top-P, Top-K | ⚠️ | `omni`'s canonical request supports `temperature` and `topP` as pass-through inference knobs. No evidence of a `topK` parameter in the canonical contract. See [05](05_llm_usage.md). |
| System / User / Assistant roles | ✅ | Core to `omni`'s canonical message model (`system`, `user`, `assistant`, `tool_result` roles) and to how prompts are assembled. See [05](05_llm_usage.md) and [08](08_prompt_pipeline.md). |
| Context window limits, "lost in the middle" | ⚠️ | Airtap manages context size via compaction (see [07](07_memory_and_context.md)); no direct evidence was found of an explicit mitigation for the "lost in the middle" recall-degradation effect specifically (e.g., deliberately repositioning critical instructions). Stated as not found, not as absent. |
| Fine-tuning | ❌ | No fine-tuning infrastructure exists in this repository. Airtap calls stock hosted models (with internal alias names like `airtap-1.1` that map to a real `vendor/model`, configured in the Model Registry — not a custom-trained model). See [05](05_llm_usage.md). |
| Types of LLMs (base/instruct, dense/MoE, open/closed, standard/reasoning, text/multimodal, general/domain) | ✅ | Airtap's Model Registry selects specific instruct-tuned, multimodal, closed/API-only models per purpose, and does use reasoning-capable models for some configurations (`reasoningLevel` is passed per model). See [05](05_llm_usage.md). |
| Model families (GPT, Claude, Gemini, Llama, Grok, DeepSeek, Mistral, Qwen, Phi, Gemma) | ✅ | Airtap's `omni` layer explicitly routes to Anthropic, Google (Gemini), OpenAI, xAI (Grok), Groq, OpenRouter, and AWS Bedrock (Anthropic-hosted) by vendor prefix. See [05](05_llm_usage.md). |
| Model sizes, VRAM math, quantization (GGUF/AWQ/GPTQ) | ❌ | Airtap never loads model weights itself, so none of this applies — it's exclusively a hosted-API consumer. |
| Remote vs. local models | ✅ (remote only) | Airtap's decision-making is **100% remote/cloud API inference** — there is no on-device model inference anywhere in this repository, despite the product's "on-device intelligence" framing referring to on-device *action* (the phone physically executes taps), not on-device *inference* (the model runs in the cloud backend). See [05](05_llm_usage.md) for the explicit distinction. |

---

## Phase 3 — Prompt Engineering

Heavily used — this is one of Airtap's most concretely implemented theory areas. Full detail in
[08_prompt_pipeline.md](08_prompt_pipeline.md).

| Concept | Status | Notes |
|---|---|---|
| Prompt anatomy (role/instruction/context/input/constraints/format/examples) | ✅ | The system playbook and prompt templates visibly contain all seven components. See [08](08_prompt_pipeline.md). |
| Zero-shot / One-shot / Few-shot | ⚠️ | The playbook is almost entirely **rule-based instruction**, not worked examples — no significant few-shot example blocks were found in the main playbook. One skill file (`android-direct-actions`) **does** include several worked input→output example mappings, closer to a few-shot pattern. See [08](08_prompt_pipeline.md). |
| Chain of Thought (CoT) | ✅ | Every tool call is required to go through an `observe → review → plan` reasoning envelope before acting — a structurally-enforced CoT pattern. See [06](06_agents_and_tools.md) and [08](08_prompt_pipeline.md). |
| Structured Outputs / JSON Mode | ✅ | Every agent decision is a schema-validated tool call (Zod schemas via `omni`'s tool contract) — true schema-constrained structured output, not just "valid JSON." See [08](08_prompt_pipeline.md). |
| Function / Tool Calling | ✅ | The core mechanism of the entire product. See [06](06_agents_and_tools.md). |
| Prompt Chaining | ⚠️ | Airtap's task loop is closer to a single evolving agent loop than a fixed prompt chain, but real chaining-like patterns exist: context compaction is a distinct chained LLM call, and the playbook enforces a fixed tool sequence (`LaunchApp → ReportPlan → LoadSkill → execution`) for certain request types. See [08](08_prompt_pipeline.md). |
| Prompt Injection | ✅ | A confirmed, real risk surface — Airtap's agent reads arbitrary on-screen content (screenshots of any app or website) as part of every decision, which is a textbook **indirect prompt injection** vector. See [08](08_prompt_pipeline.md) for the specific guardrails found and what's not (yet) covered. |
| System Prompt Design | ✅ | `yodaSystemPrompt.mustache` plus the playbook markdown files are a deliberately structured, receiver-type-specific system prompt. See [08](08_prompt_pipeline.md). |
| Prompt Versioning | ⚠️ | Prompts are plain files in `cortex/src/templates/`, so they get git version control, diffs, and PR review "for free" — but no evidence was found of a *formal*, CI-gated golden-set regression check that automatically blocks a prompt change from merging. The infrastructure to build one exists (the Evaluation Layer), but it isn't wired to run automatically. See [06](06_agents_and_tools.md) for the Evaluation Layer's actual trigger model. |
| Prompt engineering vs. RAG vs. fine-tuning ("which lever") | ⚠️ | Airtap's actual choice is visible in its architecture: no RAG, no fine-tuning — behavior is steered almost entirely through prompting (playbooks, skills) plus tool/model selection. See [07](07_memory_and_context.md) for why RAG specifically was skipped. |

---

## Phase 4, 5, 6 — Embeddings, Vector Databases, RAG

**None of this is used anywhere in Airtap.** This is worth stating plainly and completely, since
it's a large fraction of the roadmap and a natural assumption for anyone coming from a
"AI product = RAG" mental model.

| Concept | Status | Notes |
|---|---|---|
| Embeddings as a retrieval tool | ❌ | Grepped for embedding/vector-search terminology across the backend; the only hit was a false positive (`cosine` inside an image-*compression* utility — DCT math, unrelated to cosine similarity). |
| Similarity search (cosine / dot product / Euclidean) | ❌ | No similarity-search code exists anywhere in the repository. |
| Vector databases (Pinecone, Weaviate, Milvus, Qdrant, Chroma, FAISS, pgvector) | ❌ | None appear in any `package.json` in the repository, and no vector-DB client code was found. |
| Chunking strategies | ❌ | No document-chunking pipeline exists. (Context *compaction*, covered in [07](07_memory_and_context.md), is a different concept — summarizing a growing conversation, not splitting a document for retrieval.) |
| Metadata filtering, HNSW/IVF indexing | ❌ | Not applicable — there's no vector index to filter or build. |
| RAG (the full retrieve-then-generate pipeline) | ❌ | Confirmed absent. See [07_memory_and_context.md](07_memory_and_context.md) for the detailed "why not" — Airtap's per-user memory store is small enough that the roadmap's own stated exception ("under ~10,000 chunks, you don't need a vector DB") applies directly. |
| Hybrid search, re-ranking, query rewriting, HyDE | ❌ | All are RAG-retrieval refinements; not applicable with no retrieval pipeline in place. |
| Agentic RAG / multi-hop retrieval | ❌ | Not applicable. The **web search tool** (`WebSearch`, backed by SerpAPI/ScrapingDog) is superficially similar in spirit — the agent decides *whether* to search, like agentic RAG's "decide whether to retrieve" — but it queries the live web via an API, not a private vector-indexed corpus. Worth knowing the distinction rather than conflating the two. See [06](06_agents_and_tools.md). |
| RAG evaluation (RAGAS: faithfulness, answer relevancy, context precision/recall) | ❌ | Not applicable — there's no retrieval pipeline for these metrics to measure. |

---

## Phase 7, 8, 9 — AI Agents, Agentic AI, Multimodal / GUI Agents

**This is the core of the product.** Full detail in [06_agents_and_tools.md](06_agents_and_tools.md)
and [05_llm_usage.md](05_llm_usage.md) (for the vision/multimodal-model side specifically).

| Concept | Status | Notes |
|---|---|---|
| Chatbot vs. Assistant vs. Workflow vs. Agent | ✅ | Airtap is a genuine **agent** by the roadmap's own test (decides its own step sequence, takes real actions) — not a workflow with a human-drawn flowchart. See [06](06_agents_and_tools.md). |
| The core agent loop (perceive → think → act → verify) | ✅ | This is exactly Airtap's per-step cycle. See [06](06_agents_and_tools.md) and [09](09_runtime_request_walkthrough.md). |
| Planning | ✅ | The `ReportPlan` tool, enforced by the playbook before substantive execution. See [06](06_agents_and_tools.md). |
| Reasoning | ✅ | Both the structural observe/review/plan envelope and, for models configured with a `reasoningLevel`, genuine extended-thinking reasoning. See [05](05_llm_usage.md). |
| Memory | ✅ | `umem`. See [07](07_memory_and_context.md). |
| Reflection / self-critique | ⚠️ | No dedicated "reflection pass" (a second LLM call that critiques the first) was found. The closest real analogues are prompt-level self-verification instructions (§6.4 of the playbook: "treat any visible app state as untrusted until verified") and implicit heuristic detection (e.g., recognizing a Google Play login wall from the screenshot) — both are single-pass, not a distinct critique step. See [06](06_agents_and_tools.md). |
| Tool Calling | ✅ | See [06](06_agents_and_tools.md). |
| Decision Making & Retry Logic | ✅ | See [06](06_agents_and_tools.md) for retry-window and stuck-task handling. |
| ReAct pattern | ✅ | The `observe/review/plan` envelope that wraps every tool call **is** Airtap's ReAct implementation. See [06](06_agents_and_tools.md). |
| Single-agent vs. multi-agent | ✅ (single-agent) | Airtap runs one agent, one loop, one model call per step — confirmed **not** multi-agent. See [06](06_agents_and_tools.md). |
| Planner / Executor / Reviewer pattern | ❌ | No separate agent processes exist for these roles. `ReportPlan` (planning) and the Evaluation Layer's `llm_judge` (reviewing, but only in eval runs, not live production traffic) are functionally adjacent but are not a live multi-agent handoff pipeline. |
| Self-correction | ⚠️ | Same finding as Reflection above — present as prompt guidance (loop-avoidance rules), not as a dedicated verify-against-an-external-signal mechanism distinct from the main decision call. |
| Agent frameworks (LangGraph, CrewAI, AutoGen/AG2, OpenAI Agents SDK, AWS Strands) | ❌ | None appear in `cortex/package.json`. Airtap's agent loop (`yoda`) is fully custom-built, not assembled from any of these frameworks. |
| Vision-Language Models (VLMs) | ✅ | Screenshots are sent directly to multimodal models as part of every decision call. See [05](05_llm_usage.md). |
| Screen understanding: screenshots vs. accessibility tree | ✅ (hybrid) | Confirmed hybrid: the playbook explicitly instructs using "the current screenshot image **together with** the UI dump" — both signals inform every tap decision. See [06](06_agents_and_tools.md). |
| OCR, UI element detection | ⚠️ | No standalone OCR or bounding-box UI-element-detection model was found as a distinct step; screen understanding relies on the multimodal LLM's own vision plus the structured "UI dump." |
| Grounding (coordinate-based / element-based / Set-of-Marks) | ✅ (coordinate-based) | Confirmed by the `Tap` tool's own schema (`coordinates: [x, y]`) — Airtap uses coordinate-based grounding, informed by the UI dump, not element-ID selection or numbered-box (Set-of-Marks) annotation. No Set-of-Marks-style overlay was found anywhere in the codebase. See [06](06_agents_and_tools.md). |
| Action space design | ✅ | A deliberately bounded set of device actions (tap, swipe, type, long-press, navigate, launch, wait...) plus an explicit "done" equivalent (`RespondToUser`). See [06](06_agents_and_tools.md). |
| Automation layer (ADB, UI Automator, Appium, XCUITest) | ❌ | Confirmed **not** ADB — every ADB-related string found in the Android receiver's code is a comment describing what the app *deliberately avoids needing* (ADB requires developer/USB-debugging mode, which a real end-user's phone won't have). Airtap uses Android's **Accessibility Service** API and/or the physical **HID dongle** instead — see [06](06_agents_and_tools.md) for exactly why that trade-off was made. |
| The perception-action loop | ✅ | Maps directly onto `yoda`'s step cycle. See [06](06_agents_and_tools.md) and [09](09_runtime_request_walkthrough.md). |
| Third-party GUI-agent products (Anthropic Computer Use, Operator, UI-TARS, Browser Use, CogAgent) | ❌ | Airtap doesn't use any of these — it's a custom, purpose-built agent, not built on top of a named third-party computer-use product. Conceptually closest in spirit to Anthropic's Computer Use category, but independently implemented. |
| Risk-tiering of the action space (safe / gated / not-yet-autonomous) | ⚠️ | Partial, not formalized: the playbook and the `android-direct-actions` skill both instruct the model to seek confirmation before "externally visible or irreversible" actions, and `RequestClarification`/`RequestTakeover` exist as escape hatches — but no formal, code-enforced three-tier classification (e.g., a hard gate that forces confirmation specifically for any purchase/delete/permission-grant action) was found. This is called out explicitly as a real QA-relevant gap in [06](06_agents_and_tools.md). |

---

## Phase 10, 11, 12 — Tool Calling, Memory, Multi-Agent Systems

| Concept | Status | Notes |
|---|---|---|
| Tool calling (full mechanism) | ✅ | See [06](06_agents_and_tools.md) for the Tool Manager / Tool Executor split. |
| MCP (Model Context Protocol) | ❌ (in-product) | Confirmed not used as the product's own tool-exposure mechanism — Airtap's tools are custom Zod schemas dispatched through an internal registry, not MCP servers. **Caveat**: `.mcp.json` files do exist in the repo (root and `pilot/`), but they configure MCP servers used by *engineers' own development tooling* (a Figma design-asset server, a Next.js devtools server) — unrelated to how Airtap's agent calls its own tools. See [06](06_agents_and_tools.md). |
| Short-term vs. long-term memory | ✅ | Maps directly onto `umem`'s daily short-term files vs. its long-term `memory.md`. See [07](07_memory_and_context.md). |
| Conversation / semantic / profile / working memory | ✅ | All four map cleanly onto specific `umem` files and the task-level conversation history. See [07](07_memory_and_context.md) for the exact mapping. |
| Multi-agent systems (any topology) | ❌ | Confirmed single-agent — see Phase 7–9 row above. |
| Orchestrator/Supervisor vs. Collaborative multi-agent | ❌ | Not applicable — no multi-agent system exists. |

---

## Phase 13, 14, 15 — AI Evals, Model Training, AI Infrastructure

| Concept | Status | Notes |
|---|---|---|
| Eval metrics (correctness, groundedness, hallucination, relevance, completeness, safety, instruction-following, tool-use accuracy, latency, cost) | ⚠️ | Airtap's eval reports do capture cost/latency/token stats for every run, and its check types (plan-quality, output-content, LLM-judge questions) cover several of these loosely — but not as a formally named, complete metric suite. See [06](06_agents_and_tools.md). |
| Automated vs. human evals | ⚠️ | Automated (assertion + LLM-judge) evals exist and are the primary mechanism. A lightweight, informal human-eval signal also exists in production: user thumbs-up/down feedback on agent responses (tracked as a product event). No formal structured human-eval program (rubric, inter-rater agreement) was found. |
| LLM-as-a-judge | ✅ | `evalJudge.ts` — a real, working implementation. See [06](06_agents_and_tools.md) for which of the four judge patterns (reference-free/based, rubric, pairwise) it actually uses. |
| Judge failure modes (verbosity bias, position bias, self-preference bias, judge drift) | ❌ (unmitigated) | No evidence was found of explicit mitigation for these known LLM-judge biases (e.g., swapping answer order to cancel position bias). Called out as a real, testable gap in [06](06_agents_and_tools.md). |
| Agent-specific evals (Task Success Rate, step accuracy, trajectory match, efficiency) | ⚠️ | Airtap's `report_plan` check is a pre-execution proxy for plan quality; `final_output_contains`/`llm_judge` checks approximate task-level success (TSR-like). No formally named step-accuracy or trajectory-match metric was found. See [06](06_agents_and_tools.md). |
| Published benchmarks (AndroidWorld, MobileWorld, WebArena, OSWorld, GAIA, Mind2Web) | ❌ | Airtap evaluates against its **own** internal dataset (`evalTaskDataset.v2.json`), not any published external benchmark. |
| Third-party eval tooling (Promptfoo, DeepEval, RAGAS, LangSmith, Braintrust) | ❌ | None found in dependencies. Airtap built its own evaluation module (`cortex/src/eval`) rather than adopting one of these. |
| Golden dataset construction | ✅ | `evalTaskDataset.v2.json`, ~50+ curated cases. See [06](06_agents_and_tools.md). |
| "Eval Ops" (evaluation as a continuous pipeline, not a pre-launch script) | ⚠️ | The infrastructure for this exists, but per the Phase 1 investigation, no CI hook or schedule triggers eval runs automatically — it's run on-demand from an internal Pilot screen. This is the single most direct, named gap versus the roadmap's recommended practice. See [06](06_agents_and_tools.md). |
| Pretraining, instruction tuning, RLHF/DPO | ❌ | Airtap performs none of this — it consumes already-trained, already-aligned hosted models. |
| LoRA / QLoRA (parameter-efficient fine-tuning) | ❌ | No fine-tuning of any kind occurs in this repository. |
| Distillation | ❌ (not literally) | No model-training-based distillation exists. **Conceptually adjacent**: `mreg` assigns lighter, cheaper off-the-shelf models to narrower purposes (dongle-constrained receivers, title generation, display-metadata labels) — achieving a similar practical goal (cheaper, faster models for simpler jobs) through model *selection*, not training a distilled model. See [05](05_llm_usage.md). |
| GPU/CPU, CUDA, inference servers (vLLM, TGI), API gateways | ❌ | Airtap runs no inference hardware or serving software of its own; it is purely a client of hosted provider APIs. |
| Token limits, rate limits | ✅ | `omni` has a normalized error type for rate limiting (`OmniRateLimitError`) with defined retry handling. See [05](05_llm_usage.md). |
| Streaming | ❌ | Confirmed not used for the agent's decision calls: `omni`'s canonical output carries an `isStreaming` field that is hardcoded `false`, and the Anthropic adapter explicitly uses the SDK's *non-streaming* request type. See [05](05_llm_usage.md) for why this is the architecturally correct choice for a tool-calling agent loop. |
| Caching (response caching, prompt/context caching) | ✅ | Anthropic prompt caching is explicitly used for the stable half of the system prompt. General-purpose Redis caching also exists but is an application-level cache, not an LLM-response cache — the distinction matters and is explained in [05](05_llm_usage.md). |
| Reasoning tokens billed like output tokens | ✅ | `omni`'s canonical stats explicitly break out `outputTokensReasoning` as a distinct, tracked figure. See [05](05_llm_usage.md). |
| Model routing (cost optimization) | ✅ | `mreg` — though it's important to be precise about *what kind* of routing: a fixed, config-driven assignment of model-per-purpose, not a live classifier that inspects each request's difficulty. See [05](05_llm_usage.md). |
| Cost optimization (cache → route → shrink model → trim prompt → watch reasoning tokens) | ✅ | Airtap uses caching, model routing/tiering, and lighter models for constrained receivers — a real, multi-lever cost strategy, detailed in [05](05_llm_usage.md). |

---

## Phase 16, 17, 18 — Product Architecture, AI Testing, Production AI

These three phases are less about naming a specific technique and more about *shape* — how the
product is architected, how you'd test it, and how it's run in production. They don't map to a
single "used/not used" checkbox the way earlier phases do; instead, they're woven through every
other document in this phase, and specifically:

| Concept | Where it's addressed |
|---|---|
| Mobile/GUI agent architecture diagram (`User Prompt → LLM Planner → Screen Capture → VLM → Action Decision → Executor → State Change → Verification → Loop`) | [09_runtime_request_walkthrough.md](09_runtime_request_walkthrough.md) maps this diagram directly onto Airtap's real components, step by step. |
| Non-determinism as the default testing mindset | Threaded through every "QA Perspective" section in [05](05_llm_usage.md)–[08](08_prompt_pipeline.md). |
| Grounding failures as a no-classical-QA-analogue failure category | [06_agents_and_tools.md](06_agents_and_tools.md), in the grounding section. |
| Risk-tiered testing for irreversible actions | [06_agents_and_tools.md](06_agents_and_tools.md) — and flagged there as a real, partially-open gap in Airtap today, not a fully solved problem. |
| Monitoring, logging, tracing | Already covered in depth in Phase 1's [04_system_components.md](../Phase-1/04_system_components.md) (Logging, Error Monitoring, Telemetry & Tracing, Task Debug & Trace Capture) — not re-covered here to avoid duplication; [05](05_llm_usage.md) and [06](06_agents_and_tools.md) cross-reference it where an AI-specific concept intersects it. |
| Guardrails, human-in-the-loop | `RequestClarification` / `RequestTakeover` — covered in [06](06_agents_and_tools.md). |
| A/B testing | ❌ Not found. Grepped for A/B-testing infrastructure across the backend and frontend; no experiment/variant/bucket system for prompts or models was found. |
| Versioning, cost tracking, continuous evaluation | Prompt versioning: [08](08_prompt_pipeline.md). Cost tracking: [05](05_llm_usage.md). Continuous evaluation: see the "Eval Ops" row above — infrastructure exists, continuous automatic triggering does not. |

---

## Summary: the honest one-paragraph answer

If asked "does Airtap use RAG / vector databases / fine-tuning / multi-agent systems / MCP /
streaming / third-party agent frameworks?" — the accurate answer for all of them is **no**. If
asked "does Airtap use LLM-driven agentic tool calling, multimodal vision input, structured
output, prompt caching, model routing, memory, context compaction, chain-of-thought-style
reasoning, and LLM-as-judge evaluation?" — the accurate answer for all of them is **yes**, and
the next six documents explain exactly how, where, and how to test each one.

---
**Next:** [05_llm_usage.md](05_llm_usage.md) — how Airtap actually talks to LLMs: providers, models, sampling, tokens, caching, and cost.
