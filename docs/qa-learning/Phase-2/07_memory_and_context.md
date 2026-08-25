# 07 — Memory and Context

*Phase 2 · Document 4 of 7. Covers Phase 11 of the roadmap (Memory) plus the memory-relevant parts
of Phase 2 (context window). See [04_ai_components_mapping.md](04_ai_components_mapping.md) for the
full checklist. Phase 1's [03_request_lifecycle.md](../Phase-1/03_request_lifecycle.md) already
covers the mechanical step-by-step of compaction and memory writes — this document adds the
theory-to-implementation mapping and QA framing on top of that.*

---

## 1. Why Memory Exists At All

### 1. AI Theory
An LLM is stateless by default — it remembers nothing between calls. A conversation only *feels*
continuous because the whole history is re-sent every turn, and that only works up to the context
window's limit. "Memory" is the scaffolding built around a stateless model to fake continuity —
from simply re-sending history, up to a persistent store that survives well past what any context
window could hold.

### 2. Airtap Implementation
Airtap needs continuity at **two different scopes** that get solved two different ways: within one
task (re-sent conversation history, bounded by compaction — §3 below) and across many unrelated
tasks over time (a persistent per-user store — `umem`, §2 below). Confusing these two is a common
mistake; they're implemented by entirely different code paths for a reason.

### 3. Runtime Workflow
```text
Within a task:  history is just re-sent every step (short-term)
Across tasks:   umem is explicitly read and re-injected into a NEW task's prompt (long-term)
```

### 4. Why Airtap Uses It
Without cross-task memory, every new task would start from zero — the agent would never "know"
anything about a user beyond what's typed in that single request. Without within-task history
management, a long task would eventually exceed the context window outright. Both failure modes are
real and different; both need solving.

### 5. QA Perspective
Keep these two failure classes separate when triaging a "the agent forgot something" report: was
the fact from *earlier in this same task* (a within-task/compaction question, §3) or from a
*previous, separate task* (a `umem`/long-term question, §2)? They point at completely different
code.

### 6. Interview Mapping
- **"Why do LLM-based products need memory at all?"** → Models are stateless; memory is the
  scaffolding that fakes continuity, at whatever scope a product needs it.
- **"What does Airtap use?"** → Two distinct mechanisms: re-sent (and compacted) history within a
  task, and a persistent per-user store across tasks.
- **"Why two mechanisms, not one?"** → They solve genuinely different problems at different
  timescales and have different storage/retrieval needs.
- **"What would you test?"** → Whether a "forgot" bug is actually a within-task or a cross-task
  memory failure — the diagnosis determines which system to investigate.

---

## 2. Long-Term Memory: `umem`

### 1. AI Theory
The standard taxonomy splits memory by *kind*, not just by duration: **conversation/episodic**
memory (the raw history of what was said/done — a diary), **semantic** memory (distilled facts
extracted from that history, stripped of when/how they were learned — "user is vegetarian," not
"user mentioned being vegetarian on Tuesday"), **profile** memory (a stable, structured "who is
this person" record), and **working** memory (a scratchpad for the current task, discarded when it
ends). The hardest design problem isn't storage — it's **curation**: deciding what's worth
promoting to long-term memory, and how to handle facts that become stale or contradicted.

### 2. Airtap Implementation
`cortex/src/umem/` — per-user (scoped by `authUserId`), persisting across **every** task the user
ever runs, not per-task. Confirmed structure (Phase 1 research): four workspace files plus daily
short-term files, stored in Firestore. Mapped onto the roadmap's taxonomy:

| `umem` file | Roadmap category | What it actually holds |
|---|---|---|
| `user.md` | **Profile memory** | Facts about the user — the stable "who is this person" sheet. |
| `memory.md` | **Semantic memory** | Long-term, distilled facts — written by a dedicated cheap-model call after every terminal task, not raw transcripts. |
| `YYYY-MM-DD.md` (daily) | **Short-term memory** (not the same as working memory — see below) | Recent, day-scoped notes; persists longer than a single task but is not treated as permanent long-term fact storage. |
| `soul.md` / `identity.md` | *(orthogonal to the roadmap's taxonomy)* | These aren't memory *about the user* at all — they're the agent's own persona/self-concept configuration, user-editable but not written by the automatic memory-writer call. Worth not force-fitting these into "profile memory"; they're a different thing entirely. |

The within-task conversation history (before compaction) is the closest real match for **working
memory** — a scratchpad for the current task — and also doubles as **conversation/episodic**
memory for that task's own duration.

**On curation**: confirmed that "should I store this?" genuinely is an LLM decision, exactly as the
roadmap describes — on every terminal task state, a dedicated, cheap model call (`umemTaskMemory.ts`,
using a small/fast model) reads the finished task and decides what to write, restricted by a
`MemoryUpdate` tool that can only touch `memory.md` and today's short-term file — it cannot touch
`user.md`, `soul.md`, or `identity.md` (those are edited directly by the user via a separate API,
not by the agent's automatic memory writer). **Not independently confirmed in this research**: the
exact mechanics of how a contradicted/stale fact gets resolved (e.g., "moved from Delhi to
Dehradun") — the tool is named `MemoryUpdate` rather than `MemoryAppend`, suggesting it's capable of
overwriting rather than only appending, but the precise update/conflict-resolution logic wasn't
directly inspected at that level of detail. Stated as unconfirmed rather than assumed.

### 3. Runtime Workflow
```text
READ (start of every task):
  Prompt Builder pulls soul.md + identity.md + user.md + memory.md sections
   ↓
  Injected into the volatile half of the system prompt (see doc 08) — every new task starts
  with this context already available, even if it's the user's very first message that session
   ↓
WRITE (end of every task):
  Task reaches a terminal state (COMPLETED / FAILED / CANCELLED / STOPPED)
   ↓
  A state-change observer fires a background job
   ↓
  A dedicated, cheap model call reads the finished task and decides what's worth keeping
   ↓
  Writes ONLY to memory.md and/or today's short-term file, via a restricted MemoryUpdate tool
```

### 4. Why Airtap Uses It
Without this, every task would be a stranger to the user — no continuity of preferences, no
"remembering" a correction, no cross-task personalization at all, which is the entire point of an
assistant that's supposed to feel like it knows you. Restricting the automatic writer to only two of
the four files is a deliberate safety boundary: the agent can accumulate facts and short-term notes
on its own, but it cannot silently rewrite the user's core identity/persona configuration — that
stays under direct user control.

### 5. QA Perspective
- **Isolation is a security property, not just a quality one** (per the roadmap's own framing):
  test that one user's memory never surfaces for another user. This is the highest-priority test in
  this whole document — a cross-user memory leak is a data breach, not a quality bug.
- **Recall test**: state a durable fact in one task, start a completely unrelated new task, and
  confirm the agent demonstrates awareness of it.
- **Boundary test**: confirm the automatic memory writer genuinely cannot touch `user.md`/
  `soul.md`/`identity.md` — attempt to get a task to "convince" the agent to change its own persona
  via conversation, and confirm it doesn't persist.
- **Staleness test**: state a fact, then state a contradicting fact in a later task, and check
  whether the old one is corrected or both persist inconsistently — this is explicitly unconfirmed
  behavior per this research, so it's a genuinely open, valuable thing to verify rather than assume
  is handled.
- **"Forget that" test**: if there's a user-facing way to ask the agent to forget something,
  confirm it's actually removed from `memory.md`/the short-term file, not just acknowledged in the
  reply text.
- **Timing**: memory writes fire on terminal states only, via a background job — confirm a very
  quickly cancelled task still gets (or correctly doesn't get) a memory write, and that the write
  doesn't block the user-visible task completion.
- **Logs**: the memory-writer's own LLM call is captured like any other (`taskOmniDebug`/Langfuse,
  per [05_llm_usage.md](05_llm_usage.md)) — a wrong memory write can be traced back to exactly what
  it was shown and what it decided to keep.

### 6. Interview Mapping
- **"What kinds of memory does a real agent product need?"** → Episodic/conversation, semantic,
  profile, and working memory — different lifespans, different retrieval needs.
- **"What does Airtap use?"** → `umem`, a per-user Firestore-backed store with four files mapping
  cleanly onto profile/semantic/short-term memory, written selectively by a dedicated LLM call after
  every task, plus within-task history serving as working/episodic memory for that task's duration.
- **"Why was this design chosen?"** → It separates *what the agent can learn on its own*
  (`memory.md`, short-term notes) from *what only the user controls* (persona/identity/profile
  facts) — a deliberate, narrow write boundary rather than letting the agent freely rewrite anything
  about itself or the user.
- **"What would you test?"** → Cross-user isolation first (it's a security property), then recall
  across unrelated tasks, then whether the write boundary actually holds under adversarial
  conversation.

---

## 3. Context Window Management & Compaction

### 1. AI Theory
Every model has a fixed maximum context size. A long-running conversation or task will eventually
threaten it — and even before hitting the hard limit, quality can degrade ("lost in the middle":
models recall information from the start or end of a long context more reliably than the middle).
Real systems handle this by summarizing older content, dropping the oldest turns, or retrieving
only what's relevant instead of keeping everything.

### 2. Airtap Implementation
`cortex/src/yoda/yodaConversationHistory.ts` (assembly) and `yodaCompaction.ts` (compaction).
Compaction is confirmed to trigger a **manual, code-driven summarization flow** — an explicit extra
LLM call, using a dedicated summarization prompt — specifically for **Google- and xAI-routed
models** (`yodaUsesManualCompactionFlow`, per the Phase 1 investigation), triggered when the
*previous* step's input token count crosses a configured threshold (documented default: roughly
75,000 tokens). **Worth stating precisely rather than overclaiming**: for Anthropic- and
OpenAI-family-routed calls, this manual path was not confirmed to be the mechanism in use — the
original research treated this as a reasonable presumption (that those providers' own native
context-handling is relied on instead), not a directly verified fact; `omni`'s own documentation
does show Anthropic-family adapters having fuller native support for "compaction block replay" than
Google/xAI (which need a "text wrapper" workaround), which is at least consistent with that
presumption without fully proving the mechanism. Once compaction fires, later prompt-building starts
from the latest compaction point forward, not from the task's full original history.

### 3. Runtime Workflow
```text
Before building the next step's prompt:
   ↓
Check: did the PREVIOUS step's input token count cross the compaction threshold?
   ↓ yes (confirmed path: Google/xAI-routed models)
Extra LLM call: summarize everything so far
   ↓
Visible in the task thread as "Context automatically compacted"
   ↓
All FUTURE prompt-building starts from this compaction point forward, not the original history
```
This is a genuine **extra step in the task's job chain** — it costs one full additional LLM round
trip and produces a step that does no device work at all, which is expected behavior, not a stall.

### 4. Why Airtap Uses It
A task can run for many steps, each appending to the conversation history; without compaction, a
sufficiently long task would eventually either blow the context window outright or suffer
"lost-in-the-middle" quality degradation well before that. Summarizing and restarting from a
checkpoint keeps both cost and recall quality bounded as a task grows, at the cost of one extra LLM
call when it triggers.

### 5. QA Perspective
- **Verify the visible marker appears at the right point** — run or find a long task and confirm
  "Context automatically compacted" shows up roughly at the documented token threshold, not
  arbitrarily earlier or later.
- **Post-compaction coherence**: confirm the agent doesn't lose track of what it was doing
  immediately after a compaction event — this is the direct, testable version of "did the summary
  preserve what actually mattered."
- **A compacted step is a legitimate explanation for "a step that did nothing visible on the
  device"** — don't misdiagnose this as a stall; check for the compaction marker before assuming a
  step is stuck.
- **Vendor-specific behavior**: since the manual flow is confirmed only for Google/xAI, a task that
  changes which vendor is answering it mid-task (via a model-routing change — see
  [05_llm_usage.md](05_llm_usage.md)) is a genuinely under-verified scenario worth testing
  specifically — does compaction behavior stay consistent across that switch?
- **"Lost in the middle" itself**: no explicit mitigation for this specific effect (e.g.,
  deliberately repositioning critical instructions near the start/end of a long prompt) was
  confirmed beyond compaction shortening the history overall — worth probing directly on a long
  task with a critical fact buried mid-history, both before and after a compaction event.

### 6. Interview Mapping
- **"How do you handle a conversation longer than the context window?"** → Summarize older content
  and continue from the summary, rather than either truncating blindly or hitting a hard failure.
- **"What does Airtap use?"** → A token-threshold-triggered compaction call
  (`yodaCompaction`), confirmed to run as an explicit manual flow for Google/xAI-routed models.
- **"Why was this design chosen?"** → It bounds both cost and context-window risk reactively,
  without needing to pre-guess how long any given task will run.
- **"What would you test?"** → That the threshold fires at the right point, that post-compaction
  behavior stays coherent, and that compaction behaves consistently if the underlying model/vendor
  changes mid-task.

---

## 4. Routine-Scoped Memory

### 1. AI Theory
Not covered as a distinct category in the roadmap's core taxonomy, but a natural extension of it: a
recurring, scheduled job can benefit from its own persistent memory scope — distinct from any single
run's working memory, and distinct from the general user profile — so it can "remember" its own run
history specifically (e.g., "I already sent this reminder yesterday, don't duplicate it").

### 2. Airtap Implementation
Confirmed in Phase 1's research: routines carry an `executionMemory` field, separate from `umem`.
`cortex/src/yoda/yodaRoutineContext.ts` injects a `<routine_context>` block into the volatile system
prompt whenever the current task was spawned by a routine, including this routine-scoped memory —
distinct from, and in addition to, the per-user `umem` context that's also injected for that same
task.

### 3. Runtime Workflow
```text
Scheduled job triggers a routine-spawned task (see doc 09 for the full trigger path)
   ↓
Volatile prompt assembly includes BOTH:
   - the user's general umem context (§2)
   - this routine's own executionMemory (routine-scoped, carried between THIS routine's runs only)
```

### 4. Why Airtap Uses It
A routine runs repeatedly, unattended, and its own run-to-run continuity needs ("did I already do
this today," "what happened last time this ran") are a different scope than either a single task's
working memory (too narrow — wiped every run) or the user's general profile (too broad — not
specific to this one recurring job). A dedicated scope avoids polluting general user memory with
routine-run bookkeeping, and avoids routines interfering with each other's state.

### 5. QA Perspective
- **Scope isolation**: confirm one routine's `executionMemory` doesn't leak into another routine's
  context, even for the same user.
- **Duplicate-run test**: a good practical check is exactly the "did I already send this today"
  scenario — trigger a routine's underlying condition twice in the same window and confirm
  `executionMemory` is actually being used to avoid a duplicate action, if that's the intended
  behavior for that routine.
- Cross-reference with the RRULE/scheduling edge cases already documented in Phase 1's manual test
  suite references — routine memory bugs and scheduling bugs can look similar from the outside
  ("it did the wrong thing on the wrong day") but point at different code.

### 6. Interview Mapping
- **"Would a scheduled/recurring agent need its own memory scope?"** → Yes — run-to-run continuity
  for a specific recurring job is a different need than either single-task working memory or
  general user profile memory.
- **"What does Airtap use?"** → A dedicated `executionMemory` field per routine, injected alongside
  (not instead of) the user's general `umem` context.
- **"Why was this design chosen?"** → Keeps a routine's own operational state from polluting general
  user memory, and keeps separate routines from interfering with each other.
- **"What would you test?"** → Isolation between routines' memory scopes, and whether a routine
  actually uses its memory to avoid repeating an action it already took.

---

## 5. Why Airtap Does NOT Use RAG or a Vector Database for Memory

This is worth its own section rather than a one-line "not used," because it's a genuinely good
design-judgment answer, not just an absence.

### The theory that applies here
The roadmap makes this exact point directly (Phase 5): *"Under ten thousand chunks, brute force is
fast enough and more accurate [than a vector database]"* — and long-term agent memory is explicitly
named (Phase 11) as something that's architecturally "RAG pointed at the agent's own past," **if**
you choose to implement it that way. It's a choice, not a requirement.

### Why full-context injection is the right call here, not a shortcut
`umem`'s entire long-term store per user is a small, bounded set of plain-text files — nowhere near
the corpus size (the roadmap's own cited threshold is roughly 10,000 chunks) where a vector
database, embeddings, and similarity search would earn their complexity. Reading the whole thing
and injecting it directly into the prompt (full-context stuffing) is simpler, has zero additional
infrastructure, is trivially debuggable (you can just read the actual markdown file), and — because
there's no retrieval step — has **no retrieval-failure mode at all**: no risk of the wrong memory
chunk being retrieved, no embedding-model-mismatch bug, no stale-index problem. Airtap's memory
system doesn't have a retrieval step to fail, on purpose, because it doesn't need one at this scale.

### QA Perspective
- **This is a scale-dependent design decision, not a permanent one.** If per-user memory ever grows
  large enough that full-context injection becomes expensive or starts crowding out task-specific
  context, that's the point at which retrieval-based memory would become the right trade-off — worth
  knowing this is a "not yet," not a "never," if memory size is ever raised as a product question.
- **Because there's no retrieval, none of the RAG-specific failure modes apply** (stale index,
  embedding-model mismatch, access-control leakage through a retrieved chunk) — don't test for
  these; they describe a system Airtap doesn't have.
- **What DOES need testing instead**: context-window pressure from memory size — as a user's
  `memory.md` grows, does it start crowding out room for the actual task's own conversation
  history? This is the real, applicable failure mode of a full-context-injection approach at scale,
  and it's the thing to watch as an early warning that retrieval-based memory might eventually be
  warranted.

### Interview Mapping
- **"Why wouldn't you use RAG for an agent's memory?"** → Because RAG earns its complexity at scale;
  under roughly ten thousand chunks, reading everything directly is simpler, cheaper, and has no
  retrieval-failure mode to debug.
- **"What does Airtap actually do instead?"** → Full-context injection of a small, bounded set of
  plain-text memory files, read directly into the prompt every time.
- **"Why was this design chosen?"** → Per-user memory is small enough that the roadmap's own stated
  exception to "always use a vector DB" applies directly — added retrieval infrastructure would be
  complexity without a corresponding benefit at this scale.
- **"What would you test?"** → Whether memory size growth ever starts crowding out task context —
  that's the leading indicator that this design choice would need to be revisited, not a current
  bug to hunt for.

---
**Next:** [08_prompt_pipeline.md](08_prompt_pipeline.md) — how the prompts that carry all of this context are actually built.
