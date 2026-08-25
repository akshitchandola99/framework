# 10 — Component Reference

*Phase 2 · Document 7 of 7. Documents 04–09 are concept-first (start from a roadmap idea, find
where it lives) and flow-first (start from a request, trace it through). This document is
**component-first**: start from a file or module you're looking at, and find out which AI-theory
concepts it embodies and where to read more. Use it as the fast lookup; use 05–09 for the actual
explanations.*

This deliberately does not repeat Phase 1's [04_system_components.md](../Phase-1/04_system_components.md),
which already gives every component in the system a full profile (what/why/where/tech/input/output/
next/QA). This document only covers the subset of components that carry real AI-theory weight, and
for each one answers a narrower question: **which roadmap concepts does this file actually
implement?**

---

## A. Entry & Orchestration

| Component | Repo location | Roadmap concepts it embodies | QA one-liner | Deep dive |
|---|---|---|---|---|
| Agent Orchestrator | `cortex/src/yoda/yoda.ts`, `yodaJobs.ts` | Agent loop (perceive/think/act/verify), ReAct, planning, decision-making & retry | The single most important file to understand before testing anything else in this product. | [06 §1–2](06_agents_and_tools.md) |
| `ReportPlan` tool | `cortex/src/yoda/yodaTools.ts` (schema) | Planning (interleaved, not upfront) | Gradeable in isolation — Airtap's own eval already does this. | [06 §3](06_agents_and_tools.md) |
| `android-direct-actions` skill | `cortex/src/skills/definitions/android-direct-actions.md` | The "don't use AI grounding when a deterministic path exists" pattern; also a rare few-shot prompting example | Confirm it's correctly *unavailable* on dongle receivers, not just correctly used when available. | [06 §9](06_agents_and_tools.md), [08 §5](08_prompt_pipeline.md) |

---

## B. Prompt & Context Layer

| Component | Repo location | Roadmap concepts it embodies | QA one-liner | Deep dive |
|---|---|---|---|---|
| `yodaSystemPrompt.mustache` | `cortex/src/templates/` | Prompt anatomy, system prompt design, prompt/context caching (stable half) | Confirm nothing per-user leaks into this file's rendered output — it's the cache boundary. | [08 §1–2](08_prompt_pipeline.md) |
| `yodaSystemPlaybook*.md` (3 variants) | `cortex/src/templates/` | System prompt design, chain-of-thought guardrails, loop-avoidance instructions, guardrails/safety-in-prompt | Cross-check the *correct* variant loads per receiver type — a leaked capability claim on the wrong receiver type is a direct, testable bug. | [06 §10](06_agents_and_tools.md), [08 §2](08_prompt_pipeline.md) |
| `yodaVolatileSystemPrompt.mustache` | `cortex/src/templates/` | Context injection (memory, date, routine context) — the non-cacheable half | Verify this, not the stable half, is where per-task variation actually lives. | [08 §2](08_prompt_pipeline.md) |
| Tool schema envelope (`observe`/`review`/`plan`) | `cortex/src/yoda/yodaTools.ts` | Chain-of-thought, enforced at the schema level (ReAct) | Read this on every "wrong action" investigation before anything else — it's a free debug log. | [06 §2](06_agents_and_tools.md), [08 §3](08_prompt_pipeline.md) |
| Context compaction | `cortex/src/yoda/yodaCompaction.ts` | Context window management, "lost in the middle," prompt chaining (a genuinely separate chained call) | Confirm the visible "compacted" marker appears at the right token threshold, and confirmed only for Google/xAI-routed models — not verified for other vendors. | [05 §3](05_llm_usage.md), [07 §3](07_memory_and_context.md) |
| Conversation history assembly | `cortex/src/yoda/yodaConversationHistory.ts` | Short-term/working memory, canonical message roles | Working memory in this product == the pre-compaction task history, not a separate structure. | [07 §1–2](07_memory_and_context.md) |

---

## C. LLM Layer

| Component | Repo location | Roadmap concepts it embodies | QA one-liner | Deep dive |
|---|---|---|---|---|
| `omni.ts` + vendor adapters | `cortex/src/omni/` | LLM provider abstraction, structured output/tool calling, sampling controls, multimodal input, error normalization | Vendor-specific bugs are real — check `omni`'s own support matrix (in its `AGENTS.md`) before assuming a bug is universal. | [05 §1, 4, 9](05_llm_usage.md) |
| `omniErrors.ts` | `cortex/src/omni/` | Rate limits, timeouts, retry-worthy vs. terminal failures | Confirm the retryable-error list matches what's documented — the "cloud session not ready" gap is a known, testable edge. | [05 §9](05_llm_usage.md) |
| Model Registry | `cortex/src/mreg/` | Model families/types, model routing, cost optimization, distillation-adjacent model selection | A live-editable config — re-verify grounding accuracy after any model swap, not just "does it still respond." | [05 §2](05_llm_usage.md) |
| `reasoningLevel` config | Set in `mreg`, consumed in `yoda.ts` | Reasoning models / extended thinking | Reasoning tokens are billed like output tokens — confirm they're visible in cost dashboards, not hidden. | [05 §6](05_llm_usage.md) |
| Prompt caching (`anthropicCacheControl`) | `cortex/src/yoda/yoda.ts` (usage), `omni` (hint plumbing) | Prompt/context caching | A cache-efficiency regression is a cost bug with no correctness symptom — check `dashGetLlmHealth`, don't wait for a complaint. | [05 §8](05_llm_usage.md) |

---

## D. Tool & Action Layer

| Component | Repo location | Roadmap concepts it embodies | QA one-liner | Deep dive |
|---|---|---|---|---|
| `yodaTools.ts` | `cortex/src/yoda/` | Tool/function calling (declaration side), structured output, MCP-equivalent (custom, not MCP) | Test tool-list *exclusion* per receiver type, not just inclusion. | [06 §5](06_agents_and_tools.md) |
| `AndroidActionRegistry` | `cortex/src/android/androidActions.ts` | Tool/function calling (execution side) — "model proposes, code disposes" | Test tool selection, argument correctness, and result handling as three separate surfaces. | [06 §6](06_agents_and_tools.md) |
| `Tap`/`AndroidOperation` coordinate schema | `cortex/src/yoda/yodaTools.ts` | Grounding (coordinate-based, confirmed — not element-based, not Set-of-Marks) | The single highest-value test category in the whole product — measure grounding accuracy as its own metric. | [06 §7](06_agents_and_tools.md) |
| Skill Registry | `cortex/src/skills/` | On-demand vs. auto-loaded context injection; a form of retrieval-by-exact-match (package name / explicit `LoadSkill` call), not semantic retrieval | Confirm a custom user-owned skill correctly overrides its built-in namesake. | [06 §9](06_agents_and_tools.md) (skills generally referenced throughout) |

---

## E. Device / Automation Layer

| Component | Repo location | Roadmap concepts it embodies | QA one-liner | Deep dive |
|---|---|---|---|---|
| Device Command Router | `cortex/src/android/androidExecuteCommand.ts` | The "action executor" boundary between decision and physical effect | The literal fork point between cloud and physical transport — a bug here misroutes a command entirely. | [09 Stage 9](09_runtime_request_walkthrough.md) |
| Android Controller (on-device) | `receiver/` | Automation layer — confirmed Accessibility Service + HID, not ADB | Physical hardware failure modes (BLE range, dongle battery) have no software equivalent — must be tested on real hardware. | [06 §8](06_agents_and_tools.md) |
| iOS Controller (on-device) | `receiver-ios/` | Same — HID dongle is mandatory on iOS (no Accessibility-Service equivalent) | AssistiveTouch-off is a real, app-detected failure mode — reproduce it directly. | [06 §8](06_agents_and_tools.md), Phase 1 Device Layer |
| Screenshot + UI dump fetch | `android/androidGetInstance.ts`-adjacent flow, receiver apps | Screen understanding (hybrid: vision + accessibility-tree-derived state) | Deliberately test apps with sparse/empty accessibility data — this is where the vision half has to carry the whole decision. | [05 §7](05_llm_usage.md), [06 §7](06_agents_and_tools.md) |

---

## F. Memory Layer

| Component | Repo location | Roadmap concepts it embodies | QA one-liner | Deep dive |
|---|---|---|---|---|
| `umem.ts` / `umemWorkspace.ts` | `cortex/src/umem/` | Long-term/profile/semantic memory, memory curation as an LLM decision | Cross-user isolation is a security test, not a quality test — prioritize it first. | [07 §2](07_memory_and_context.md) |
| `umemTaskMemory.ts` | `cortex/src/umem/` | The "should I store this?" curation decision, implemented as a real, restricted LLM call | Confirm the write boundary holds — this call can write `memory.md`/today's short-term file, and nothing else. | [07 §2](07_memory_and_context.md) |
| Routine `executionMemory` | `cortex/src/rtn/`, injected via `yodaRoutineContext.ts` | A distinct memory scope, routine-specific — not covered by the roadmap's core taxonomy directly, but a natural extension of it | Test isolation between routines' memory, and whether it's actually used to avoid duplicate actions. | [07 §4](07_memory_and_context.md) |
| *(absent)* Vector-based / embedding retrieval | — | The roadmap's own "when you don't need a vector DB" principle, applied deliberately | Don't test for RAG-specific failure modes (stale index, embedding mismatch) — there's no retrieval step to have them. | [07 §5](07_memory_and_context.md) |

---

## G. Evaluation & Quality Layer

| Component | Repo location | Roadmap concepts it embodies | QA one-liner | Deep dive |
|---|---|---|---|---|
| `evalTaskDataset.ts` / `data/evalTaskDataset.v2.json` | `cortex/src/eval/` | Golden dataset construction | ~50+ curated cases — check coverage gaps against real production task categories (`dashGetTaskAnalysis`, Phase 1). | [06 §13](06_agents_and_tools.md) |
| `evalJudge.ts` | `cortex/src/eval/` | LLM-as-a-judge (reference-free scoring pattern) | No confirmed mitigation for verbosity/position/self-preference/drift bias — test for these directly. | [06 §13](06_agents_and_tools.md) |
| `evalTaskRunner.ts` | `cortex/src/eval/` | Agent-specific evals (plan-quality proxy, output-content checks) — runs the **real** task engine | Most current cases check plan quality only, not full task completion — don't over-read a passing run. | [06 §13](06_agents_and_tools.md) |
| Eval trigger (`/evals` in Pilot) | `pilot/app/evals/`, `evalRunStartHandler.ts` | "Eval Ops" — infrastructure present, continuous automation absent | The single most concrete, actionable gap in this entire document set — no CI/schedule trigger found. | [06 §13](06_agents_and_tools.md), [08 §8](08_prompt_pipeline.md) |
| `taskOmniDebug.ts` / `taskYodaTrace.ts` | `cortex/src/task/` | Not a roadmap concept per se, but the practical answer to "how do you debug a non-deterministic system" | Always-on, complete capture of every LLM call — the default first stop for "why did the agent do that." | Phase 1 [04 §30](../Phase-1/04_system_components.md) |

---

## H. Confirmed absent — the fast "don't go looking for this" list

For anyone scanning the codebase expecting to find these, based on common AI-product assumptions —
confirmed not present, with the reasoning in [04_ai_components_mapping.md](04_ai_components_mapping.md):

| You might look for... | You will not find it, because... |
|---|---|
| A vector database client (Pinecone/Weaviate/Chroma/FAISS/pgvector) | No RAG pipeline exists — memory uses full-context injection at a scale where that's the right call. |
| An MCP server implementation for the agent's own tools | Tools are custom Zod schemas dispatched through an internal registry. (MCP *is* present, but only as external dev-tooling config — Figma/Next.js devtools — unrelated to the product.) |
| `adb shell` calls in the automation path | Deliberately avoided — real end-user phones don't have USB debugging on. Accessibility Service + HID dongle instead. |
| LangGraph / CrewAI / AutoGen / any multi-agent framework | The agent loop is fully custom-built and single-agent. |
| A separate "Planner" or "Reviewer" agent process | Planning is one tool call inside the single loop; there's no live, in-production review pass distinct from the main decision. |
| Streaming token-by-token responses from the LLM | Explicitly disabled (`isStreaming: false`) — the agent needs a complete, valid tool call before it can act. |
| On-device / local model inference | All decision-making is cloud-side via `omni`; "on-device" in this product means on-device *action*, not on-device *inference*. |
| Model fine-tuning, LoRA/QLoRA artifacts | No training infrastructure exists anywhere in this repository. |
| A/B testing infrastructure for prompts or models | Not found — grepped and confirmed absent. |
| A formal, code-enforced risk tier for irreversible actions | Not found as a hard gate — present only as prompt-level guardrails and model judgment. Flagged as the most important open gap in [06 §11](06_agents_and_tools.md). |

---

## How to use this whole document set going forward

- **Starting from a roadmap concept?** → [04_ai_components_mapping.md](04_ai_components_mapping.md).
- **Starting from a specific file or component?** → this document.
- **Need the deep explanation of one topic area?** → [05](05_llm_usage.md) (LLM), [06](06_agents_and_tools.md)
  (agent/tools), [07](07_memory_and_context.md) (memory), [08](08_prompt_pipeline.md) (prompts).
- **Need to see it all as one flow?** → [09_runtime_request_walkthrough.md](09_runtime_request_walkthrough.md).
- **Need the general platform architecture underneath all of this (non-AI-specific)?** → Phase 1,
  starting at [01_project_overview.md](../Phase-1/01_project_overview.md).

This closes Phase 2.
