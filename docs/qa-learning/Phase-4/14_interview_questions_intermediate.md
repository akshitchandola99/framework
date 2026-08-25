# 14 — Interview Questions: Intermediate

*Phase 4 · Document 2 of 3. Assumes [13_interview_questions_beginner.md](13_interview_questions_beginner.md).
Same three-part format per question. This document covers agent architecture in depth: reasoning
patterns, tool-calling mechanics, grounding, memory, retrieval, evaluation, and cost/performance
patterns. [15](15_interview_questions_advanced.md) covers system design and hard QA judgment
calls.*

---

## Q1. What is the ReAct pattern, and how does it apply to agent design?

### Part A — Generic AI Interview Answer
ReAct stands for Reason + Act, and it's the loop underneath nearly every agent framework worth
naming. The idea is simple but powerful: instead of letting a model jump straight to an action, you
force it to write down its reasoning *before* every single action, then look at the result before
reasoning again — a repeating Thought → Action → Observation cycle. The non-obvious part is *why*
this actually helps: the written reasoning becomes part of the model's own context for its next
decision, so having explicitly reasoned "the restaurant is closed, so I need an alternative" makes
the model far more likely to actually act on that conclusion next. It's chain-of-thought prompting
welded directly onto tool calling. It also has a major side benefit for anyone building or
maintaining the system: that reasoning trail is a free, human-readable log of the agent's intent —
when an agent does something wrong, you can read *why* it thought that was the right move, instead
of staring at a black box that just fired an action.

### Part B — How Airtap Implements This
This is Airtap's actual implementation pattern for its entire decision loop, and it's enforced more
strongly than a typical prompt-level request: every tool the agent can call is defined so that its
response format itself requires a structured reasoning section — an observation of the current
state, a review of what that means, and a plan — filled in before the actual chosen action and its
arguments. Because this requirement lives in the response's required structure rather than just
being requested in prompt wording, the model literally cannot produce a valid response without
including it, which is a stronger guarantee than hoping a "please think step by step" instruction
gets followed under pressure. In practice, this means every single step of every task Airtap runs
leaves behind a self-documenting record of what the agent believed it was looking at and why it
chose its next move.

### Part C — QA Perspective
- **What to validate**: the reasoning fields contain genuine, task-specific reasoning tied to the
  actual current screen — not generic, boilerplate text that technically satisfies the schema
  without adding real value.
- **Possible bugs**: a model that "games" the structural requirement with shallow filler reasoning
  while still producing a valid response — this would defeat the purpose while passing all
  structural validation.
- **Logs to inspect**: the observe/review/plan reasoning on every step is the primary artifact for
  understanding any wrong-action investigation — read it first, before anything else.
- **Edge cases to test**: a wrong action where the reasoning was actually correct (pointing at a
  downstream execution/grounding problem) versus one where the reasoning itself was already wrong
  (pointing at a genuine understanding problem) — these are different bug classes needing different
  fixes.
- **Likely follow-up questions**: "Why enforce this at the schema level instead of just asking for
  it in the prompt?" "How would you detect an agent whose reasoning doesn't actually match its
  action?"

---

## Q2. How does tool/function calling actually work end-to-end?

### Part A — Generic AI Interview Answer
The full loop, worth being able to draw: you describe a set of tools to the model (name,
description, argument schema) as part of the request. The model reads the current situation and
decides whether a tool is needed at all; if so, it emits a structured request — not prose — naming
the tool and filling in its arguments as data matching that schema. Your own application code then
actually runs the corresponding real function and gets a genuine result back. That result is fed
back into the model as a new message, and the model reads it and writes the final, human-facing
answer (or decides another tool call is needed, and loops). The security-critical detail worth
stating explicitly: the model never runs anything itself at any point in this chain — it only ever
proposes; your code is what disposes.

### Part B — How Airtap Implements This
This exact loop is the mechanical core of every agent step Airtap runs, dispatched through one
central, generic registry: a lookup keyed by tool name, populated with every available tool's
handler at startup. When the model returns its chosen tool call, this registry looks up the matching
handler and runs it — and this single mechanism handles *every* tool uniformly, whether it's a
device action (which needs to resolve a live connected device first) or something that doesn't
touch a device at all, like a web search or an image-generation call. For device-touching actions
specifically, there's an additional routing decision layered on top: depending on whether the task
targets a cloud-hosted virtual device or a real, physically paired phone, the command travels over
a completely different transport to actually reach and execute on that device — but from the tool
dispatcher's point of view, both look identical: pick a handler, run it, get a result back.

### Part C — QA Perspective
- **What to validate**: three genuinely separate correctness questions for every tool call — was
  the *right* tool chosen, were its *arguments* correct, and was its *result* actually used
  correctly by the next decision (not silently ignored or misread as success).
- **Possible bugs**: an unregistered/unknown tool call should fail loudly and explicitly, never be
  silently swallowed; a tool offered to the model that its current device type has no way to
  actually execute is a filtering bug specifically, not a tool-execution bug.
- **Logs to inspect**: the chosen tool name and its arguments for a step, plus the tool's recorded
  result — compare this directly against the resulting device/screen state to see whether the
  mismatch is at the decision level or the execution level.
- **Edge cases to test**: a tool call with boundary-case arguments (empty, extremely long, unusual
  characters); a tool deliberately made to fail, to confirm the agent notices and adapts rather than
  proceeding as if it had succeeded.
- **Likely follow-up questions**: "What's the risk if a tool's failure result isn't clearly
  distinguishable from a success?" "How would you test argument correctness specifically, separate
  from tool-selection correctness?"

---

## Q3. What is "grounding" in a GUI/computer-use agent, and why is it uniquely hard?

### Part A — Generic AI Interview Answer
Grounding is the step that connects a model's *decision* ("tap the login button") to an actual
pixel or element on a real screen the OS can act on. This is a genuinely distinct problem from
deciding *what* to do, and it's what makes GUI agents categorically harder to get right than a pure
text chatbot: a model can be completely correct about its intent and still get the location wrong —
tap 40 pixels too low and hit "forgot password" instead of "login." That's a failure category with
no equivalent in classical UI test automation, where a selector either resolves or it throws an
explicit error; it can't be "approximately right." Three general approaches exist: coordinate-based
(the model directly estimates x/y — works on literally anything visible, but models are genuinely
bad at precise spatial estimation and it's brittle across different screen sizes); element/tree-based
(the model picks a labeled element and the system computes the exact coordinates — precise, but
blind to anything not properly exposed); and a hybrid called Set-of-Marks, where detected elements
get numbered directly on the screenshot and the model just picks a number, turning a hard spatial
estimation problem into an easy multiple-choice one.

### Part B — How Airtap Implements This
Airtap's grounding is confirmed coordinate-based: the tap action's own definition takes a direct
[x, y] coordinate pair, and a live configuration setting per model controls exactly how those
coordinates should be interpreted (raw device pixels, a normalized 0–1000 scale, or a
preprocessed-vision-specific scale) — meaning the *system*, not the model, handles the final unit
conversion once a coordinate estimate is produced. Rather than relying on vision alone for this
estimate, Airtap's operating instructions explicitly have the model use the current screenshot
**together with** a separate structured description of on-screen elements to choose its coordinates
— a deliberate middle ground that sharpens the raw vision-only guess without requiring every app to
expose a perfect, complete element tree (which many genuinely don't — games, custom-rendered views,
certain web content). No evidence of Set-of-Marks-style numbered-box overlay prompting exists
anywhere in the product; it's coordinate output, informed by both signals together.

### Part C — QA Perspective
- **What to validate**: grounding accuracy as its **own**, separately-tracked metric — "given a
  correct decision, did the tap land on the correct element?" — never buried inside overall task
  success, since a task can succeed despite a grounding miss through retries, hiding real fragility.
- **Possible bugs**: coordinate misinterpretation after a model swap (different models can use
  different coordinate conventions); a tap that's off by a small, consistent margin across many
  screens on one specific device (suggests a resolution/scaling bug, not a per-decision error).
- **Logs to inspect**: the exact screenshot at the moment of the decision, alongside the resulting
  tap coordinate and the following step's screenshot, to see precisely where the tap landed versus
  where it was intended.
- **Edge cases to test**: apps with sparse or missing structured element data (deliberately worth
  testing, since this is where vision has to carry the whole decision); different screen
  sizes/resolutions and states where an on-screen keyboard shifts the layout mid-task.
- **Likely follow-up questions**: "Why not just use Set-of-Marks and remove the coordinate-guessing
  problem entirely?" "How would you build a regression suite specifically for grounding accuracy?"

---

## Q4. What's the difference between screenshot-based and accessibility-tree-based screen understanding?

### Part A — Generic AI Interview Answer
There are two fundamentally different ways an agent can "see" a screen. **Screenshots** give a
vision model a picture — it sees everything a human would see, but this is comparatively slow (image
data is expensive to process), imprecise (the model has to estimate positions), and expensive in
token cost. The **accessibility tree** is structured data the OS already maintains for every UI
element — its text, type, bounds, and whether it's clickable — originally built to make screen
readers work for blind users; an agent can read this directly as cheap, fast, precise text. Its
weakness is the mirror image of vision's strength: it's blind to anything an app doesn't properly
expose — custom-rendered canvases, games, and poorly-built apps often leave the tree empty or
useless, no matter how visually obvious the content is to a human. The honest, correct answer isn't
"pick one" — real, serious mobile agents use both together: the tree as the fast, cheap, precise
primary signal, and vision as the fallback for whatever the tree can't see.

### Part B — How Airtap Implements This
Airtap confirms exactly this hybrid pattern in its own operating instructions: a specific rule
directs the model to use the current screenshot image **together with** a structured "UI dump" to
verify visible state and choose coordinates — not either one alone. This dual signal is fetched as
part of the same device-context request whenever a fresh read of the screen is needed (which is
itself conditional — only refetched when the previous action was one that could have changed the
screen, not on literally every single step, for efficiency). Beyond straightforward perception,
Airtap also has a deliberate opt-out for one narrow slice of tasks: for well-defined system-level
actions like setting an alarm or dialing a number, a dedicated mechanism fires a native OS command
directly, bypassing both the screenshot and the element tree entirely — no perception or grounding
step happens at all for that class of action, which is a real strength when it applies.

### Part C — QA Perspective
- **What to validate**: behavior specifically on apps with poor or absent accessibility metadata —
  this is precisely where the system is most exposed and where real bugs concentrate.
- **Possible bugs**: reasoning from a one-step-stale screenshot after a step that didn't touch the
  device (expected, conditional behavior — confirm it doesn't get misdiagnosed as "the agent didn't
  notice the screen changed"); the structured element description and the screenshot genuinely
  disagreeing about the current state (a rare but real synchronization risk).
- **Logs to inspect**: both signals (screenshot and structured description) as captured for a
  specific step, side by side, to see exactly what information the model actually had available.
- **Edge cases to test**: games, canvas-rendered UIs, and WebViews deliberately, since these are the
  known-weakest points for the structured-description half of the hybrid.
- **Likely follow-up questions**: "What happens on an app that exposes neither useful accessibility
  data nor legible visuals?" "Why fetch fresh screen state conditionally instead of on every step?"

---

## Q5. What types of memory does an AI agent need?

### Part A — Generic AI Interview Answer
By default, an LLM is completely stateless — it remembers nothing between calls; a conversation only
feels continuous because the whole history gets re-sent every turn. "Memory" is the scaffolding
built around that statelessness. The standard taxonomy splits it two ways. By **duration**:
short-term (lives inside the current context window, gone once the conversation ends or the window
fills) versus long-term (persists outside the model, in a separate store, retrieved back in when
relevant). By **kind**: conversation/episodic memory (the raw history of what happened — a diary),
semantic memory (distilled, clean facts extracted from that history, stripped of exactly when/how
they were learned), profile memory (a stable, structured "who is this person" record), and working
memory (a scratchpad for the current task specifically, discarded once it's done). The genuinely
hard design problem isn't storage — it's curation: deciding what's worth promoting to long-term
memory, and how to handle a fact that later becomes stale or contradicted.

### Part B — How Airtap Implements This
Airtap maintains memory at two distinct scopes solved by entirely different mechanisms. Within one
task, conversation history is simply re-sent each step (working/episodic memory), compacted via
summarization once it grows too large. Across a user's entire history with the product, a separate,
persistent per-user store holds several distinct files that map cleanly onto the taxonomy above: one
file of stable facts about the user (profile memory), one file of longer-term distilled facts
(semantic memory, written by a dedicated cheap-model call after every finished task — confirming
that "should I remember this?" really is an LLM decision here, exactly as the general pattern
describes), and daily short-term note files. Two additional files hold the agent's own persona/
self-concept configuration — these are edited directly by the user, not written automatically, and
don't really fit the "memory about the user" taxonomy at all; worth not force-fitting them into it.
The automatic memory-writer call is deliberately restricted — it can update only the long-term-facts
file and today's short-term file, never the user's core profile or the agent's persona files.

### Part C — QA Perspective
- **What to validate**: cross-user isolation, first and always — this is a security property, not a
  quality one. A fact stated in one task should be correctly recalled in a later, unrelated task by
  the *same* user, and never by a different one.
- **Possible bugs**: a stale or contradicted fact continuing to be used after a correction (the
  exact mechanics of how this is resolved weren't independently confirmed, making it a genuinely
  open, valuable thing to test rather than assume works); a memory write that inflates future
  prompts unboundedly over time.
- **Logs to inspect**: the actual stored memory content is plain text and directly readable — the
  simplest, most direct debugging technique in this entire product is just reading the file for the
  account in question.
- **Edge cases to test**: stating a fact and then explicitly contradicting it in a later task; a
  brand-new account with zero memory history; two accounts with very similar stated facts, tested
  concurrently, checking for cross-contamination.
- **Likely follow-up questions**: "Why restrict the automatic memory writer to only two of the
  files?" "How would you test that a 'forget this' request actually removes something, rather than
  just acknowledging it in the reply?"

---

## Q6. What is RAG (Retrieval-Augmented Generation)?

### Part A — Generic AI Interview Answer
RAG's one-sentence version: instead of hoping the model already knows the answer, you go find the
actual answer first and hand it to the model along with the question. The flow: a document
collection gets split into chunks, each chunk is converted into an embedding (a numeric
representation of its meaning) and stored in a searchable index; at query time, the user's question
is embedded the same way, the most similar stored chunks are retrieved, and those chunks are stuffed
directly into the prompt alongside the question, with an instruction to answer only from that
provided material. RAG fixes four real problems at once: a model's knowledge cutoff, no access to
private/internal data, hallucination (grounding the answer in real retrieved text instead of the
model's memorized patterns), and the ability to cite a real source for a claim. The critical
distinction from fine-tuning, and a near-guaranteed interview question: RAG changes what the model
*knows* right now; fine-tuning changes how the model *behaves*. Proposing fine-tuning to fix a
"the model doesn't know our data" problem is one of the most common wrong answers in AI interviews.

### Part B — How Airtap Implements This
Airtap uses **no RAG pipeline anywhere in the product** — this is worth stating directly and
confidently rather than assuming a modern AI product must have one somewhere. There's no embedding
generation, no vector database, and no chunking/retrieval step at any layer, confirmed by directly
searching the codebase for this kind of infrastructure and finding nothing. Airtap's per-user memory
(above) is deliberately implemented as **full-context injection** instead — reading a small, bounded
set of plain-text files directly into every prompt, with no retrieval step involved at all. This is
a legitimate, scale-appropriate design choice, not a gap: retrieval infrastructure earns its
complexity at a scale Airtap's per-user memory simply hasn't reached, and reading everything
directly is simpler, cheaper, and has zero retrieval-specific failure modes to debug (no stale
index, no embedding-model mismatch, no wrong-chunk-retrieved bug) because there's no retrieval
step to have them.

### Part C — QA Perspective
- **What to validate**: since there's no RAG pipeline, don't test for RAG-specific failure modes at
  all — they describe a system Airtap doesn't have, and spending test effort there is wasted effort.
- **Possible bugs**: the actual, applicable risk at Airtap's current scale is context-window
  pressure from memory content simply growing large over time and crowding out room for the task's
  own conversation — the real, forward-looking signal that a retrieval-based approach might
  eventually become worth revisiting.
- **Logs to inspect**: N/A for retrieval specifically; memory content itself is directly readable
  plain text (see Q5).
- **Edge cases to test**: N/A for retrieval; if memory size is ever raised as a product question,
  the edge case to watch for is a very long-tenured account's memory file size and its effect on
  prompt size/cost.
- **Likely follow-up questions**: "At what scale would you recommend introducing RAG here?" "How
  would you know it was time to revisit this design decision?"

---

## Q7. What is a Vector Database, and when do you NOT need one?

### Part A — Generic AI Interview Answer
A vector database is a database whose primary index is built for fast nearest-neighbor search in
high-dimensional space (finding "what's semantically similar to this?"), instead of exact lookups on
a key. It exists because brute-force comparison against millions of stored vectors, one at a time,
is too slow at scale — a vector DB trades a small amount of accuracy for a large amount of speed
using approximate-nearest-neighbor indexing. The stronger, more senior interview answer isn't
reciting the tool list (Pinecone, Weaviate, Milvus, Qdrant, Chroma, FAISS) — it's knowing when you
genuinely don't need one: under roughly ten thousand chunks, a simple brute-force comparison is fast
enough and, being exact rather than approximate, is actually *more* accurate than the fancy option;
a well-tagged small dataset might not need semantic search at all if keyword search already works;
and exact-match lookups (an order ID, a SKU, an error code) belong in a normal database query, never
a similarity search, which might confidently return something that merely *looks* similar and is
completely wrong.

### Part B — How Airtap Implements This
Airtap uses no vector database anywhere — confirmed directly by searching the codebase for this
category of infrastructure. This connects directly to the RAG answer above: without a retrieval
pipeline, there's nothing that would need a vector index in the first place. It's worth being able
to articulate this as a deliberate, sound design judgment rather than simply an absence: Airtap's
memory footprint per user is a small, bounded set of plain-text files — nowhere near the scale where
a vector database, embeddings, and approximate search would earn their operational complexity. This
is a genuinely good example of the same principle the generic answer describes: recognizing you
don't need the more complex tool is itself a stronger signal than knowing how to use it.

### Part C — QA Perspective
- **What to validate**: N/A directly — there's no vector index in this product to validate.
- **Possible bugs**: N/A for vector-search-specific failure modes (stale index, embedding-model
  mismatch, wrong-chunk retrieval) — none of these apply here.
- **Logs to inspect**: N/A.
- **Edge cases to test**: N/A for this specific concept as implemented; the closest applicable test
  is confirming that full-context memory injection doesn't silently degrade as content grows (see
  Q6).
- **Likely follow-up questions**: "If Airtap's memory needs did grow to the point of needing a
  vector DB, what would that migration look like, and what new failure modes would it introduce?"
  "Can you name a case where a company *should* skip a vector DB even at moderate scale?"

---

## Q8. What is Model Routing, and why does it matter for cost and performance?

### Part A — Generic AI Interview Answer
Not every request needs the most expensive, most capable model available. Model routing is the
practice of directing easier requests to a smaller, cheaper, faster model and reserving a flagship
model only for genuinely hard cases — commonly framed as a triage nurse analogy: a paper cut doesn't
need the top surgeon. This is consistently cited as one of the most effective cost-optimization
levers in production AI, with real deployments reporting large cost reductions at roughly equivalent
overall quality. The one real risk worth naming: the router itself can misroute — sending a
genuinely hard question to the cheap model and getting a worse answer — so a routing layer needs its
own evaluation (how often does it route correctly?), not just trust in the downstream models it's
choosing between.

### Part B — How Airtap Implements This
Airtap implements a real, working version of this via a live, configuration-driven model registry —
though it's important to be precise about *what kind* of routing this actually is: it's a fixed,
purpose-based assignment (this receiver type or this call type gets this specific model), not a
dynamic classifier inspecting each individual request's difficulty in real time. Confirmed distinct
model assignments exist for the main decision loop, a lighter model specifically for
hardware-constrained device types, a separate default for routine-triggered tasks, and small,
fast/cheap models for narrow auxiliary jobs like generating a task title, deciding what to remember,
or parsing a schedule description. Because this configuration lives in a live document rather than
hardcoded, which model powers a given purpose can be changed without a full deployment — a real
operational lever, and also a real operational risk if changed carelessly.

### Part C — QA Perspective
- **What to validate**: after any model-routing configuration change, re-verify behavior
  specifically for that purpose — most importantly, coordinate/grounding accuracy, which is
  genuinely model-specific and doesn't automatically carry over from whichever model was previously
  assigned.
- **Possible bugs**: a routing change silently degrading a specific call type's quality without
  throwing any error at all (this is an AI-quality-shaped failure, not a coded one); a model
  becoming unavailable with no confirmed fallback behavior.
- **Logs to inspect**: per-model aggregate dashboards (latency, failure rate, cost) are the fastest
  way to spot a routing regression as a trend, before or alongside any single-task investigation.
- **Edge cases to test**: the exact moment of a live routing config change — does an in-flight task
  behave consistently, or can it straddle two different model configurations awkwardly?
- **Likely follow-up questions**: "What's the difference between this and a true dynamic,
  per-request difficulty classifier?" "How would you test the router itself, separate from testing
  the models it routes to?"

---

## Q9. What is Prompt/Context Caching, and how does it save money?

### Part A — Generic AI Interview Answer
If a large chunk of a prompt — a long system prompt, a big block of retrieved or reference content —
is identical across many consecutive calls, some providers let you cache the already-processed
version of that prefix so you don't pay to reprocess it every single time. This is one of the
biggest, easiest wins in production LLM cost optimization, especially valuable for any system that
makes many similar calls in sequence (an agent working through a multi-step task is a textbook
case). It's genuinely different from a normal application-level response cache: it's not "return the
same answer for the same question," it's "don't re-pay to re-read the same long instructions every
single time."

### Part B — How Airtap Implements This
Airtap's system prompt is deliberately built in two halves specifically to exploit this: a large,
stable half — persona framing, the detailed operating rulebook, the available tool descriptions —
that's marked for provider-side caching because it stays byte-identical across essentially every
step of a task (and across many different users' tasks on the same device type), and a small,
volatile half — current date, location, the user's remembered context — that's rebuilt fresh every
single call and never cached, since it genuinely changes each time. Because a task can run through
many steps, each one a separate LLM call sharing that same large stable prefix, this split is a
direct, high-leverage cost saving specifically for this kind of repeated-agent-loop workload — not
a one-off optimization but something that pays off on every single step of every task.

### Part C — QA Perspective
- **What to validate**: the "stable" half of the prompt genuinely stays identical across different
  users and different tasks of the same device type — this is the actual cache boundary, and
  confirming it holds is confirming the cost optimization is actually working.
- **Possible bugs**: a prompt-template change that accidentally moves per-user or per-task data into
  what's supposed to be the cacheable stable half — this silently breaks caching and spikes cost with
  zero correctness symptom to flag it, meaning it needs to be proactively watched, not discovered
  from a complaint.
- **Logs to inspect**: aggregate per-model cache-efficiency figures in the relevant dashboard are the
  practical way to catch a caching regression before it's noticed any other way.
- **Edge cases to test**: N/A as a functional edge case (this is a cost/performance concern, not a
  correctness one) — the relevant "test" is a proactive regression check on any prompt-template
  change specifically.
- **Likely follow-up questions**: "How would you write an automated check to catch a caching
  regression before it ships?" "Is this guaranteed to work identically across every model vendor
  Airtap uses?"

---

## Q10. What is LLM-as-a-Judge, and what are its known failure modes?

### Part A — Generic AI Interview Answer
When there's no single exact-match ground truth to compare against — which is most of the time for
genuinely open-ended AI output — you hand the output to a strong model and ask *it* to score the
output against a rubric. This is considered the single most important modern evaluation technique,
because it's the practical way to grade quality (helpfulness, correctness, tone) at real scale,
where full human review is too slow and expensive and exact-match assertions simply can't express
"is this a good explanation." Four recognized patterns: reference-free scoring (no gold answer
needed — the most common real case), reference-based scoring (comparing against a known-good
answer), rubric/checklist scoring (grading against explicit, itemized criteria), and pairwise
comparison (which of two outputs is better — useful for A/B-testing a prompt or model change).
Critically, a judge is itself an LLM and has real, documented biases worth naming unprompted:
**verbosity bias** (judges tend to favor longer answers even when a shorter one is better),
**position bias** (in pairwise comparisons, judges favor whichever answer they see first, regardless
of quality), and **judge drift** (upgrading the judge model can silently shift historical scores,
breaking baseline comparability). The correct framing: the judge is a test oracle, and your oracle
can itself be wrong — you have to audit the judge, the same way you'd audit any other test tool.

### Part B — How Airtap Implements This
Airtap has a real, working LLM-as-a-judge implementation as part of its evaluation framework: a
separate model reads a task's full trace and answers a set of specific yes/no questions about it,
with every question required to be true for that check to pass — this is the reference-free scoring
pattern specifically, not pairwise comparison or reference-based scoring. This judge runs as part of
evaluating a curated set of representative test tasks, alongside simpler, cheaper deterministic
checks (did the agent produce a plan at all; does the final response contain or avoid certain
content). No confirmed mitigation exists in this product today for any of the three known judge
biases named above — no order-swapping to cancel position bias, no explicit anti-verbosity
adjustment, no formal process for revalidating baselines after a judge-model upgrade. This is a real,
directly testable gap, not a hypothetical concern.

### Part C — QA Perspective
- **What to validate**: whether a longer, padded-but-wrong answer actually scores better than a
  correct, concise one on a judge-based check — direct, deliberate verbosity-bias testing.
- **Possible bugs**: a judge-model upgrade silently shifting historical pass rates with no
  corresponding product change at all, breaking the ability to compare "before" and "after" fairly.
- **Logs to inspect**: the judge's own cited evidence for a specific verdict (not just its pass/fail
  output) — this is what lets you distinguish "the agent was genuinely wrong" from "the judge graded
  it unfairly," a critical distinction for trusting any given result.
- **Edge cases to test**: a case constructed so the judge's verdict is genuinely close/ambiguous —
  these are exactly the cases most exposed to bias, and worth the most scrutiny.
- **Likely follow-up questions**: "How would you specifically test for position bias if this
  framework ever adds pairwise comparison?" "How often would you recommend auditing judge verdicts
  by hand, and why?"

---

## Q11. What's the difference between Task Success Rate and Trajectory/Step Accuracy in agent evaluation?

### Part A — Generic AI Interview Answer
Scoring a single text answer is one thing; scoring an agent that took ten steps to accomplish
something is genuinely harder, because you care about the *journey*, not just the destination.
**Task Success Rate (TSR)** is the headline, most commonly quoted metric: did the agent complete the
whole task, yes or no. But TSR alone hides real fragility: **step/action accuracy** asks whether each
*individual* action was correct, not just the final state — an agent can reach the right destination
despite several wrong turns. **Trajectory match** asks whether the agent took a *reasonable* path,
not just any path that happened to work — reaching a goal through a chaotic, lucky route is fragile
even when TSR proudly reports "success." **Efficiency** asks how many steps/tool calls were used
versus the optimal path — a wildly over-long solution to a simple task is a real defect even if it
technically worked. The subtle, senior-level point: two agents can both post a 90% TSR, but one gets
there efficiently and reliably every time, while the other flails and gets lucky — step accuracy and
trajectory data are what catch the second one *before* it fails in production on a slightly harder
variant of the same task.

### Part B — How Airtap Implements This
Airtap's evaluation framework has real, working analogues for some of these but not a formally named
version of all of them. A dedicated check type verifies whether the agent produced a sound plan
early on — a pre-execution, plan-quality signal, cheap to run since it doesn't require full task
completion, and closely related to (though not identical to) trajectory-quality thinking. Separate
checks verify the final visible response's content, which functions as a task-level,
TSR-style correctness signal. What was **not** found as a formally named, distinct metric: an
explicit step-level accuracy score, or a trajectory-match score, tracked and reported separately
from overall pass/fail. This is a real, honest gap worth being able to name directly: if trajectory
fragility (right answer, lucky/wrong path) is a specific concern, it isn't something this framework
currently measures on its own — it would need to be added, or checked manually by reading the
reasoning trail case by case.

### Part C — QA Perspective
- **What to validate**: don't treat a passing evaluation run as proof of robust, efficient
  execution — most current cases check plan quality or final output content, not full trajectory
  quality, so a passing run is a narrower guarantee than it might sound like.
- **Possible bugs**: an agent that "passes" by luck on a specific test case, then fails on a
  near-identical variant where the lucky path isn't available — a real risk precisely because
  trajectory isn't currently a tracked metric here.
- **Logs to inspect**: the full step-by-step reasoning and action trail for a passing case, read
  manually, is currently the only way to assess trajectory quality — there's no dashboard for it.
- **Edge cases to test**: deliberately re-run a passing case multiple times and check whether the
  path taken is consistent and sensible each time, or varies wildly while still nominally
  "succeeding."
- **Likely follow-up questions**: "How would you add a trajectory-match metric to an evaluation
  framework that doesn't have one yet?" "Why might two agents with identical TSR actually represent
  very different levels of real reliability?"

---

## Q12. What's the difference between single-agent and multi-agent architectures?

### Part A — Generic AI Interview Answer
A single-agent system is one model, one loop, working through many tools — simple, cheap, and
comparatively easy to debug, but it can get overwhelmed when the tool list grows very long or the
task is genuinely broad. A multi-agent system splits work across several specialized agents (a
common shape: Planner → Executor → Reviewer, or a Researcher/Coder/Reviewer pipeline) that hand off
to each other — this adds real value when a task has genuinely separable sub-jobs, and especially
when an independent Reviewer/Critic agent can catch mistakes the original agent was blind to,
because it comes in fresh with one narrow job. The honest, mature answer worth stating directly:
multi-agent is often over-engineering. It's slower (more LLM calls in sequence), more expensive
(every agent is its own billable tokens), and every handoff between agents is a fresh place for
information to get lost or garbled. The default should be a single, well-prompted agent; reach for
multiple agents only when a task measurably fails because it's too broad for one agent, not because
splitting it sounds more sophisticated.

### Part B — How Airtap Implements This
Airtap is confirmed single-agent: one decision loop, one model call per step, with no separate
planner/executor/reviewer processes running independently — and no dependency on any multi-agent
framework exists in the codebase at all. This lines up with the generic answer's own reasoning: a
mobile GUI-automation step doesn't naturally split into independent specialist roles the way a
research-then-write-then-fact-check pipeline does — every single step needs the exact same context
(what's currently on screen) and the exact same capability (decide one action), which is exactly the
scenario where a single agent is the right default rather under-engineering. That said, Airtap does
have functional echoes of planning and reviewing *within* its single loop: a dedicated tool for
stating a plan before acting, and — separately, only during offline evaluation runs, not on live
production tasks — a judge model reviewing a task's outcome. Neither of these is a live, independent
second agent process participating in real user tasks; there's no in-production reviewer catching a
bad decision *before* it executes, which is a real, worth-naming trade-off of the single-agent
choice.

### Part C — QA Perspective
- **What to validate**: since there's no multi-agent handoff architecture, none of the
  handoff-specific failure modes (lost information between agents, an agent that rubber-stamps
  clearly bad work) apply here — don't spend test effort on them.
- **Possible bugs**: the actual, applicable gap is the absence of a live pre-execution reviewer — a
  bad decision has no independent second check before it becomes a real action, beyond the single
  decision call's own self-verification.
- **Logs to inspect**: N/A for multi-agent-specific signals; general reasoning-trail inspection (see
  Q1) is what's available here instead.
- **Edge cases to test**: N/A for multi-agent handoff scenarios specifically; the relevant test
  angle is confirming single-pass self-verification actually catches a deliberately planted state
  mismatch, since there's no independent backup behind it.
- **Likely follow-up questions**: "If you were going to add a second agent to this product, where
  would it add the most value, and why there specifically?" "What would change about your test
  strategy the day a second, independent agent process was introduced?"

---

## Q13. What is Model Context Protocol (MCP)?

### Part A — Generic AI Interview Answer
Historically, every LLM provider had its own slightly different way of describing tools to a model,
and every tool integration was custom glue code written per model-tool pair. MCP is an emerging open
standard for exposing tools to models in one common way — sometimes described as "USB-C for tool
calling": a tool exposes an MCP interface once, and any MCP-aware agent can discover and use it
without bespoke wiring. It's worth knowing the name specifically because newer agent benchmarks are
starting to mix GUI-style actions and MCP-based tool calls inside the same evaluated task, so an
agent built today may plausibly need to handle both kinds of tool surface.

### Part B — How Airtap Implements This
Airtap does **not** use MCP as its own tool-exposure mechanism — its tools are custom-defined
schemas dispatched through an internal registry (see Q2), not MCP servers. There's a genuinely
interesting nuance worth stating precisely rather than glossing over: MCP configuration files *do*
exist in this codebase, but they configure MCP servers used by **engineers' own development
tooling** — a design-asset server and a framework-devtools server — entirely unrelated to how
Airtap's own agent calls its own tools in production. Conflating "MCP is configured somewhere in
this repo" with "Airtap's product uses MCP" would be a real, checkable mistake — the two are
completely unrelated uses of the same underlying protocol name.

### Part C — QA Perspective
- **What to validate**: N/A directly — since the product doesn't use MCP for its own tool calling,
  there's no MCP-specific product behavior to validate.
- **Possible bugs**: N/A for MCP-specific failure modes in the agent's own tool-calling path.
- **Logs to inspect**: N/A.
- **Edge cases to test**: N/A as currently implemented.
- **Likely follow-up questions**: "If Airtap were to adopt MCP for its own tools, what would change
  architecturally?" "What's the practical benefit of MCP over a custom tool registry, for a product
  that only ever needs to talk to its own tools?" (A strong answer: MCP's main benefit is
  *interoperability* across many different agents/tools — a real product with a fixed, small,
  well-known tool set doesn't necessarily gain much from it, which is a reasonable justification for
  not adopting it here.)

---
**Next:** [15_interview_questions_advanced.md](15_interview_questions_advanced.md) — system design, testing non-determinism, and the hardest QA judgment calls.
