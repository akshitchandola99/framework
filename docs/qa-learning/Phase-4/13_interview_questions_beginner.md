# 13 — Interview Questions: Beginner

*Phase 4 · Document 1 of 3. Interview preparation, synthesizing Phase 1 (architecture), Phase 2
(AI theory ↔ implementation), and Phase 3 (QA testing strategy) into question-and-answer form.
Every question is answered in three parts: **Part A** is what any strong candidate should be able
to say, with no Airtap knowledge required. **Part B** is how this concept is concretely implemented
inside Airtap. **Part C** is the QA lens — what to validate, what breaks, where to look, what to
test, and what an interviewer might ask next. This document covers foundational AI/ML/LLM
vocabulary. [14](14_interview_questions_intermediate.md) covers agent architecture in depth;
[15](15_interview_questions_advanced.md) covers system design and hard QA judgment calls.*

---

## Q1. What is AI, Machine Learning, and Deep Learning — how do they relate to each other?

### Part A — Generic AI Interview Answer
Artificial Intelligence is the umbrella goal: building systems that perform tasks normally
requiring human intelligence — reasoning, perception, language, decision-making. Machine Learning
is one *technique* for achieving that goal: systems that learn patterns from data instead of being
explicitly programmed with rules. Deep Learning is a subset of ML that uses multi-layered neural
networks to learn complex patterns automatically from raw data (images, audio, text) rather than
requiring a human to hand-design features first. So the relationship is a nested hierarchy: every
ML system is AI, and every DL system is ML, but not every AI system is ML (a rule-based system —
plain IF/ELSE logic — is AI with zero learning involved). One clean way to say it: "AI is the goal;
ML and DL are means of getting there by learning from data instead of coding behavior by hand."

### Part B — How Airtap Implements This
Airtap sits at the very top of this hierarchy as a **consumer**, not a builder, of these
technologies. It implements no neural network layers, does no training, and runs no machine
learning pipeline of its own — every "intelligent" decision in the product comes from calling a
third-party, already-trained Large Language Model (Anthropic, Google, OpenAI, and others) through
an internal abstraction layer. That said, Airtap is not purely AI-driven everywhere: it deliberately
mixes in real rule-based logic alongside its LLM-driven agent loop — for example, a skill that
fires a native Android intent directly for well-defined actions like setting an alarm, instead of
asking the AI model to visually find and tap through a UI. Recognizing where a product uses
learned/probabilistic behavior versus hand-coded deterministic behavior — and knowing *why* each
was chosen for its specific job — is itself a strong signal in an interview.

### Part C — QA Perspective
- **What to validate**: that Airtap's rule-based shortcuts (deterministic paths) actually produce
  correct, exact results every time, since they should — a rule-based path failing intermittently is
  a real bug, not "AI being AI."
- **Possible bugs**: confusing which parts of the system are deterministic vs. probabilistic leads
  to mis-triaged bugs — filing a "flaky test" bug against a deterministic code path, or expecting
  perfect reproducibility from a genuinely probabilistic one.
- **Logs to inspect**: for a rule-based action, the exact parameters/action fired (this should be
  auditable and exact); for an LLM-driven decision, the reasoning trail behind it (this is
  explanatory, not exact).
- **Edge cases to test**: a request that could plausibly be satisfied by either the rule-based
  shortcut or the general AI-driven path — confirm the system consistently picks the more reliable
  option when one is available.
- **Likely follow-up questions**: "Give an example of something that should never be handled by an
  LLM, and why?" "How would you decide whether a new feature should be rule-based or model-driven?"

---

## Q2. What is Generative AI, and how does Airtap use it?

### Part A — Generic AI Interview Answer
Generative AI refers to models that create new content — text, images, audio, code — based on
patterns learned from existing data, rather than just classifying an input or predicting a number.
The contrast is discriminative vs. generative: a discriminative model answers "what is this?" (is
this email spam?); a generative model answers "create something like this" (write this email).
Modern generative AI for text and reasoning is built on the Transformer architecture, which is what
makes today's LLMs (ChatGPT, Claude, Gemini) possible; image/audio/video generation typically uses
different underlying architectures (diffusion models, GANs).

### Part B — How Airtap Implements This
Generative AI is the foundation of the entire product. Every step of Airtap's agent loop is a
generative decision: the model isn't classifying a fixed label, it's generating a novel, structured
response (reasoning plus a chosen action) conditioned on whatever screen it's currently looking at
— something that's never been seen in exactly that form before. Beyond the core decision loop,
Airtap also uses generative AI directly for content creation: there are dedicated tools for
generating and editing images as part of a task (for example, if a user asks the agent to create an
image), and for other side calls like turning a free-text schedule description into a formal
recurrence rule, or summarizing a long conversation. All of this routes through the same internal
LLM abstraction layer, regardless of which specific generative model is doing the work.

### Part C — QA Perspective
- **What to validate**: generated content (images, summaries, schedule interpretations) actually
  matches what the user asked for — generative output is powerful but has no built-in guarantee of
  correctness the way a lookup or calculation would.
- **Possible bugs**: a generated artifact that's technically well-formed but doesn't match user
  intent (a generated image that's stylistically fine but depicts the wrong subject; a schedule
  interpretation that's a valid recurrence rule but not what the user meant).
- **Logs to inspect**: the full request sent to the generative call (what exactly was asked for) and
  the raw output, to determine if a mismatch is a prompting problem or a genuinely wrong generation.
- **Edge cases to test**: ambiguous or underspecified generation requests, generation requests in a
  non-English language, and requests that push against content-policy boundaries.
- **Likely follow-up questions**: "How is generative AI different from a search engine returning
  existing content?" "What's the risk of an agent using a generative tool mid-task, versus just at
  the end?"

---

## Q3. What is a Large Language Model (LLM), and how does it generate a response?

### Part A — Generic AI Interview Answer
An LLM's entire generation mechanism, at its core, is **next-token prediction**: given all the text
so far, it produces a probability distribution over what the next small chunk of text (a token)
should be, picks one, appends it, and repeats — one token at a time, conditioning each new
prediction on everything generated so far, including its own prior output. This simple, repeated
mechanism is what produces essays, code, structured data, and conversation. It's trained by seeing
massive amounts of text and learning, for every position, what token actually came next — so at
heart it's a supervised-learning-flavored task, even though people don't usually describe it that
way casually. The word-by-word "typing" effect you see in a chat UI isn't a visual trick — the model
genuinely is producing output one token at a time, live.

### Part B — How Airtap Implements This
Airtap calls LLMs through an internal abstraction layer that normalizes every vendor's API behind
one consistent request/response contract, so the rest of the codebase never has to know or care
whether a given call is answered by Anthropic, Google, OpenAI, xAI, Groq, OpenRouter, or AWS
Bedrock. Every agent step is one such call: the model is given the current screen (as an image), a
running history of what's happened so far, and a system prompt describing its job and the tools
available — and it generates a structured decision (reasoning plus exactly one chosen tool call).
Which specific model answers a given call is picked by a live, config-driven model registry, based
on the purpose of the call (the main decision loop, a lighter model for hardware-constrained
devices, a cheap model for generating a task title) — not hardcoded to one model everywhere.

### Part C — QA Perspective
- **What to validate**: that responses are structurally valid (a well-formed, schema-matching tool
  call) on essentially every call, and that behavior is broadly consistent across the different
  models that can be configured to answer the same kind of request.
- **Possible bugs**: a malformed or schema-invalid response from the model (handled with exactly
  one corrective retry before the step fails); a response that's valid but reflects a
  misunderstanding of the current screen.
- **Logs to inspect**: the complete, per-call record of exactly what was sent to the model and
  exactly what it returned — this is the single most useful artifact for understanding "why did the
  model do that."
- **Edge cases to test**: very short and very long tasks, tasks with heavy non-English or
  mixed-language content (token cost differs meaningfully by language), and behavior when the model
  configured for a given purpose changes.
- **Likely follow-up questions**: "Why is the same prompt sometimes answered differently on two
  runs?" "What happens if the model's response doesn't match the expected schema?"

---

## Q4. What is a token, and why does it matter for cost and performance?

### Part A — Generic AI Interview Answer
Before a model can process text, the text is broken into tokens — pieces that can be a whole word,
part of a word, or punctuation, depending on the tokenizer. Most modern tokenizers use a technique
called Byte-Pair Encoding: common chunks (like whole common words) stay as single tokens, while
rare or unusual text gets split into several smaller pieces. As a rough rule of thumb, about 100
tokens is roughly 75 words of English text — though this ratio is worse (more tokens for the same
meaning) for many non-English languages and for code. Tokens matter practically for two reasons:
API pricing is billed per token (input and output separately), and every model has a maximum
context window measured in tokens, so token count is both a cost lever and a hard technical limit.

### Part B — How Airtap Implements This
Airtap doesn't implement tokenization itself — that happens inside whichever vendor model is
answering a call — but it tracks token usage as a first-class concern for every single call: input
tokens, cached input tokens, output tokens, and (for models that support it) reasoning tokens are
all captured and normalized into one consistent format regardless of vendor, and used to compute a
real cost figure for every step. This feeds directly into the product: it's how a user's daily
usage against their credit limit is calculated, and it's tracked per model in internal dashboards to
watch for cost or efficiency regressions. Token count is also the trigger for one of Airtap's more
important mechanisms: once a task's per-call input token count crosses a threshold, the system
automatically summarizes the conversation so far (visible in the task thread as a "context
automatically compacted" message) rather than letting the prompt grow indefinitely.

### Part C — QA Perspective
- **What to validate**: that a task's tracked cost accurately reflects its actual token usage, and
  that the compaction mechanism fires at the expected token threshold, not arbitrarily early or
  late.
- **Possible bugs**: a credit/cost drift (tracked cost doesn't match actual billed usage); a
  compaction event that loses context the task still needed afterward.
- **Logs to inspect**: per-call token breakdown (input/output/cached/reasoning) available for every
  step, plus aggregate per-model cost dashboards to spot trends versus single-task anomalies.
- **Edge cases to test**: tasks in non-English languages or involving a lot of code/structured data
  (both tend to use more tokens per unit of meaning); a task that runs long enough to trigger
  compaction, followed by several more steps, to confirm coherence survives it.
- **Likely follow-up questions**: "Why might a Hindi or Arabic prompt cost more than an equivalent
  English one?" "What's the relationship between reasoning tokens and normal output tokens?"

---

## Q5. What is a context window, and what happens when a conversation gets too long?

### Part A — Generic AI Interview Answer
The context window is the maximum number of tokens (usually input plus output combined) a model can
process in a single call — think of it as a whiteboard of fixed size: you can write a lot on it, but
once it's full, something has to give. A model genuinely cannot see or recall anything outside its
current context window unless it's explicitly re-sent as part of the input; it isn't quietly
"remembering" earlier turns on its own. In practice, systems handle an overflowing context by
summarizing older content, dropping the oldest messages, or retrieving only the specifically
relevant parts instead of sending everything. There's also a well-documented effect called "lost in
the middle" — models tend to recall information from the very start or end of a long context more
reliably than information buried in the middle, which affects how you'd structure a long prompt.

### Part B — How Airtap Implements This
Since a task can run for many steps, each one adding to the conversation, Airtap actively manages
this rather than letting a task simply run until it breaks. When the previous step's input token
count crosses a configured threshold, the system triggers an extra, dedicated LLM call whose only
job is to summarize everything that's happened so far in the task; all later steps then build their
prompt starting from that summary rather than the full original history. This is a genuinely
separate, additional step in the task's execution — it costs its own latency and tokens, and does
no device action, which is worth knowing so a "step that did nothing on screen" isn't mistaken for
a stall. This compaction behavior is confirmed to run for some model vendors specifically; for
others, the assumption is that the vendor's own native context handling is relied on instead,
though that specific mechanism wasn't independently verified.

### Part C — QA Perspective
- **What to validate**: a long task actually triggers the compaction step at roughly the expected
  point, and the agent's behavior stays coherent (doesn't repeat already-completed work, doesn't
  "forget" the original goal) after it happens.
- **Possible bugs**: a compaction summary that drops something the task still needed; a task that
  should have compacted but didn't (running dangerously close to the real context limit); the "lost
  in the middle" effect degrading recall of an instruction placed deep in a long prompt.
- **Logs to inspect**: the visible "context automatically compacted" marker in a task's thread; the
  per-call token counts leading up to that point to confirm the threshold logic.
- **Edge cases to test**: a task specifically engineered to be very long (many follow-ups, a
  multi-app workflow) to force at least one compaction event, then verify continued correct
  behavior for several more steps afterward.
- **Likely follow-up questions**: "What would you test differently for a task that compacts versus
  one that doesn't?" "How would you detect a 'lost in the middle' failure specifically?"

---

## Q6. What are System, User, and Assistant roles in an LLM conversation?

### Part A — Generic AI Interview Answer
Modern chat-tuned LLMs expect input structured into distinct roles rather than one long blob of raw
text. The **system** role carries developer-set instructions — persona, rules, boundaries — usually
invisible to the end user and set once for the whole session. The **user** role is whatever the
actual person types. The **assistant** role is the model's own prior responses, fed back in on
later turns so it has continuity within the context window. This structure is what lets one
underlying model be steered into completely different products just by swapping the system
message — a support bot, a coding assistant, and a creative writing helper can all be the same
model with a different system prompt setting the ground rules.

### Part B — How Airtap Implements This
Airtap's internal LLM abstraction defines a canonical set of message roles that every vendor's
wire format gets translated into and out of: a `system` role (text-only, out-of-band instructions),
a `user` role, an `assistant` role (which can contain reasoning, visible text, and a tool call all
from one logical turn), and a `tool_result` role specifically tied back to whichever prior tool call
it's the result of. Airtap's own system prompt is itself split into two halves assembled together: a
large, stable half (the agent's persona, its detailed rulebook, available tool descriptions) that's
identical across many calls and marked for provider-side caching, and a small, volatile half
(current date, location, the user's remembered context) that's rebuilt fresh on every single call.

### Part C — QA Perspective
- **What to validate**: the system prompt's rules are actually being followed and prioritized over
  conflicting instructions that might appear in user input or on-screen content.
- **Possible bugs**: a `tool_result` incorrectly linked to the wrong prior tool call (the model
  reacting to the wrong action's outcome); per-user or per-task data accidentally leaking into what's
  supposed to be the stable, cacheable system-prompt half (a silent cost regression, not a
  correctness one).
- **Logs to inspect**: the exact assembled prompt sent for a given step (available in the per-call
  debug capture), to confirm the stable/volatile split and role structure are correct.
- **Edge cases to test**: attempts to get the model to treat user input or on-screen content as
  though it had system-level authority (a basic form of prompt injection testing).
- **Likely follow-up questions**: "Why would you cache part of a system prompt but not all of it?"
  "What happens if user input and system instructions conflict?"

---

## Q7. What is Temperature in LLM sampling, and why does it matter for testing?

### Part A — Generic AI Interview Answer
At every generation step, a model produces a full probability distribution over what the next token
could be. Temperature scales that distribution before a token gets picked: low temperature (near 0)
sharpens it so the model almost always picks the single most likely token — consistent, predictable
output, useful for tasks needing reliability like structured extraction or code generation. High
temperature flattens the distribution, giving less-likely tokens a real chance — more varied,
sometimes more creative, occasionally stranger output. At temperature 0, generation is essentially
deterministic: the same input tends to produce the same output. This is the direct, mechanical
source of the "same prompt, different valid answers" behavior that makes testing LLM systems
fundamentally different from testing traditional deterministic software.

### Part B — How Airtap Implements This
Airtap's LLM abstraction layer exposes temperature (and a related setting, top-P) as pass-through,
per-call configuration knobs — a value of "not set" simply lets the provider apply its own default.
These are configured per model/purpose in Airtap's model registry rather than being one global
setting, which allows different call types (the main decision-making loop versus, say, a
lightweight title-generation call) to be tuned independently if needed. The specific values
configured for Airtap's production calls weren't independently verified in this research — that
detail lives in the live configuration data itself — but the mechanism for setting them exists and
works exactly as described generically above.

### Part C — QA Perspective
- **What to validate**: not a single expected output, but a *distribution* of acceptable outcomes —
  does the agent successfully complete a given task across many runs, not just once.
- **Possible bugs**: over-reliance on exact-match assertions anywhere in a test suite covering
  agent decisions is itself a latent bug in the *test*, not the product — it will produce false
  failures on perfectly valid, differently-phrased-or-sequenced correct behavior.
- **Logs to inspect**: nothing specific to temperature itself, but the reasoning trail across
  multiple runs of the same task is the practical way to see this variability directly.
- **Edge cases to test**: run the identical task several times back to back and record the success
  rate and the variety of paths taken, rather than treating any single run as definitive.
- **Likely follow-up questions**: "How would you write a regression test for something the model
  might answer two different, both-correct ways?" "Does lowering temperature to make a test
  reproducible fully guarantee determinism?"

---

## Q8. What is Prompt Engineering, and why is it the "cheapest lever" in AI development?

### Part A — Generic AI Interview Answer
Prompt engineering is the practice of carefully designing what you ask a model, and how, to get
better, more reliable behavior — without changing the model's weights (that's fine-tuning) and
without changing what it knows (that's retrieval/RAG). It's considered the cheapest, fastest lever
available because it requires no retraining and no new infrastructure — just changing text — and can
be iterated on immediately. A well-formed prompt generally covers several components: a role or
persona, a clear instruction, relevant context, the actual input data, any constraints, the desired
output format, and sometimes worked examples. Most "the model is being dumb" complaints trace back
to one of these being missing, vague, or contradictory. The practical rule of thumb when something's
wrong: try prompting first, reach for retrieval if the model is missing *knowledge*, and only
consider fine-tuning for a deep, high-volume behavior change that prompting genuinely can't achieve.

### Part B — How Airtap Implements This
Airtap's entire behavior is shaped almost exclusively through prompt engineering — it uses no
retrieval system and no fine-tuning anywhere in the product. Its main system prompt visibly contains
every one of the components described above: persona framing tailored to the type of device being
controlled, a detailed numbered rulebook covering planning, execution order, and specific
best-practices (how to launch an app, how to recognize it's making no progress, how to handle text
input), explicit constraints (never reveal internal details, never invent a credential), and strict
output-formatting rules (plain, neutral language; a specific markdown syntax for showing shopping
results). Notably, the main rulebook is almost entirely instruction-based rather than
example-based — worked examples appear in only one specific area (a skill for firing native Android
actions directly), used there because that particular sub-task benefits from a strict, demonstrable
output format.

### Part C — QA Perspective
- **What to validate**: the correct persona/rulebook variant is loaded for the correct situation
  (different device types get different rules — a capability claim that doesn't apply to the current
  device type is a real, testable bug).
- **Possible bugs**: a prompt-wording change with an outsized, hard-to-predict effect on behavior
  across many tasks at once — this is a documented, real risk category for this kind of system, not
  a hypothetical one.
- **Logs to inspect**: the exact assembled prompt for a specific step (via per-call debug capture),
  to confirm which rules and context were actually in play when a decision was made.
- **Edge cases to test**: whether a rule buried in the middle of a long instruction set is followed
  as reliably as one placed near the beginning or end (the "lost in the middle" effect, applied to
  instructions specifically, not just retrieved content).
- **Likely follow-up questions**: "How would you regression-test a prompt change before it ships?"
  "Why might a product choose prompting over fine-tuning here specifically?"

---

## Q9. What is Function/Tool Calling, and why can't an LLM act on its own?

### Part A — Generic AI Interview Answer
An LLM, by itself, can only produce text — it cannot browse the web, check a database, send an
email, or click a button. Function (tool) calling gives it a way to ask for that: you describe a set
of available tools (name, description, and an argument schema) to the model, and instead of
answering in prose, it can respond with a structured request to call one of them — for example,
`get_weather(city="Delhi")`. The crucial point, and the entire safety story behind this pattern: the
model does not execute anything itself. It only decides *what* to call and *with what arguments*;
trusted application code is what actually runs the real function and returns a result for the model
to continue from. This is why tool calling is often described as "the model proposes, the code
disposes."

### Part B — How Airtap Implements This
Tool calling is the literal foundation of everything Airtap's agent does — every single decision the
agent makes, including the ones that don't touch a device (searching the web, generating an image),
is expressed as exactly one tool call per step, never plain prose. Available tools include a large
device-operation tool covering tap/swipe/type/launch-app/and more, a browser-automation tool (for
cloud-hosted sessions only), search and content-generation tools, and a small set of control tools
for planning, asking the user a question, or handing off control. Critically, the exact list of
tools offered to the model is filtered per device type before every single call — a device
controlled purely through physical hardware input, for example, is never even shown a
browser-automation tool, since it has no way to execute it. Once the model picks a tool, one
dedicated dispatcher looks it up and runs it — the same generic mechanism whether it's a device
action or an external API call.

### Part C — QA Perspective
- **What to validate**: tool availability is correctly filtered per device/receiver type (test the
  *exclusions*, not just that offered tools work); a chosen tool's arguments are well-formed and
  actually match the current situation.
- **Possible bugs**: three distinct, separately-testable failure classes: the wrong tool gets
  chosen, the right tool gets malformed/subtly-wrong arguments, or a tool's failure result gets
  ignored and the agent proceeds as if it had succeeded.
- **Logs to inspect**: the recorded tool name and arguments for a step, compared directly against
  the resulting device/screen state, to determine which of the three failure classes above actually
  occurred.
- **Edge cases to test**: arguments at their boundaries (empty strings, very long text, unusual
  characters); a tool call to something that doesn't exist or isn't currently available.
- **Likely follow-up questions**: "What's the security implication of the model never executing
  anything itself?" "How would you test that a tool result failure is actually noticed by the
  model, not ignored?"

---

## Q10. What is an AI Agent, and how is it different from a chatbot?

### Part A — Generic AI Interview Answer
Four terms get used loosely and interchangeably, but they're genuinely different: a **chatbot**
answers one turn at a time, text in and text out, deciding nothing about sequence. An **assistant**
might use a tool, but only one you basically asked it to use directly. A **workflow** is an LLM
embedded inside a flowchart a human designed in advance — the LLM handles the language parts of each
fixed step, but the sequence of steps itself never changes. An **agent**, given a goal, decides its
own sequence of steps at runtime, takes real actions, checks the result, and adjusts if something
goes wrong — nobody wrote that specific sequence down in advance. The dividing line is genuinely
just **autonomy over the sequence of steps**, not whether tools are involved (a fixed workflow can
use plenty of tools too). Worth knowing honestly: most production systems marketed as "AI agents"
today are actually workflows, because workflows are cheaper, more predictable, and easier to test.

### Part B — How Airtap Implements This
Airtap is a genuine agent by this definition, not a workflow. Nothing in the product hard-codes the
sequence of screens and taps needed to satisfy an arbitrary natural-language request — a decision
loop figures out, live, one step at a time, what to do next based on what it currently observes on
screen, adjusting when something doesn't go as expected. This has to be true for the product to
work at all: it needs to handle *any* user request across *any* app, which a fixed, hand-designed
flowchart-per-task-type simply couldn't scale to. There is one deliberate, narrow exception worth
knowing precisely: for a small set of very well-defined actions (setting an alarm, dialing a number,
opening a specific settings screen), Airtap skips the AI-driven visual decision entirely and fires a
direct, deterministic system command instead — closer to a workflow shortcut for that narrow slice,
used specifically because it's faster and immune to a whole class of AI-decision failure for
well-defined actions.

### Part C — QA Perspective
- **What to validate**: the agent genuinely adapts its sequence of steps when something unexpected
  happens (an app not being where it's expected, a screen that doesn't match what was anticipated),
  rather than blindly continuing a rigid plan.
- **Possible bugs**: an agent that "succeeds" by taking a lucky, fragile path (every individual step
  worked out by chance, not by sound reasoning) is a real and important bug category — it looks
  identical to a genuinely robust success from the outside.
- **Logs to inspect**: the step-by-step reasoning trail, to distinguish a deliberate, sound
  adaptation from an accidental one.
- **Edge cases to test**: deliberately break something mid-task (an app that isn't where expected, a
  step that fails) and confirm the agent re-plans sensibly rather than continuing on an
  invalidated assumption.
- **Likely follow-up questions**: "Why might a company choose a workflow instead of a full agent for
  a given feature?" "How would you test whether a 'successful' task was actually robust or just
  lucky?"

---

## Q11. What is a Vision-Language Model (multimodal AI)?

### Part A — Generic AI Interview Answer
A Vision-Language Model (VLM) accepts images and text together as input and reasons across both —
"here's a screenshot, where's the login button?" is a task only a multimodal model can do at all; a
text-only model literally cannot process the image, no matter how the question is phrased. At a high
level, an image gets chopped into small patches, each patch becomes a numeric representation similar
in spirit to how a word becomes one, and those image representations get fed into the same
underlying model alongside the text — letting the model's attention mechanism connect what it reads
with what it sees in one unified pass. Not every capable model is multimodal — a model can be
excellent at coding or reasoning while still being entirely text-only, so "which models are
multimodal" is a genuinely separate question from "which models are the strongest overall."

### Part B — How Airtap Implements This
This capability is exactly what makes Airtap's entire product category possible: an agent
controlling a phone by "looking" at it has to be able to see a screenshot at all, which requires a
multimodal-capable model for every device-perception step. Airtap's model registry specifically
ensures the model assigned to a given purpose actually supports image input before it's ever used
this way. Notably, Airtap doesn't rely on vision alone — its own operating instructions explicitly
have the model use the current screenshot together with a separate, structured description of
on-screen elements (what's sometimes called a UI dump) to decide where to tap, rather than
estimating a tap location from the raw image by itself. This hybrid approach exists because raw
vision-only coordinate guessing is known to be imprecise, while a structured description alone is
blind to anything not properly exposed by the app (custom-drawn interfaces, games, certain
web content) — combining both covers each approach's weak spot with the other's strength.

### Part C — QA Perspective
- **What to validate**: the model actually reads and correctly reasons about small or dense
  on-screen text/UI details, not just broad screen layout.
- **Possible bugs**: a stale screenshot being reasoned over (screen state is refetched only under
  certain conditions, not on literally every step, which is a deliberate efficiency trade-off, not
  automatically a defect); poor image quality/compression making small text illegible to the model.
- **Logs to inspect**: the specific screenshot used for a given step's decision (available in the
  per-call debug capture), to check exactly what the model was actually looking at.
- **Edge cases to test**: apps with custom-rendered, non-standard interfaces (games, canvas-based
  views, certain web content) where the structured element description is likely to be sparse or
  empty — these apps put the most weight on vision alone.
- **Likely follow-up questions**: "Why combine vision with structured element data instead of
  relying on just one?" "What happens on a screen an app doesn't expose any structured information
  about?"

---

## Q12. What is Hallucination, and why does it happen?

### Part A — Generic AI Interview Answer
Hallucination is when a model generates output that sounds fluent and confident but is actually
wrong or invented — a fabricated fact, a made-up citation, a function that doesn't exist. It happens
because an LLM is fundamentally a next-token predictor trained to produce plausible-sounding
continuations, not a fact-checked lookup system; if the most statistically plausible-sounding
continuation happens to be made up, the model generates it just as confidently as it would generate
something true, because it has no fully reliable built-in way to signal "I don't know." The main
mitigations are grounding the model in retrieved source material and explicitly telling it that
saying "I don't know" is an acceptable answer, alongside lowering randomness in the response and
catching fabrications with dedicated evaluation before they reach a real user.

### Part B — How Airtap Implements This
Hallucination is a directly relevant, real risk for Airtap given the product takes physical
actions based on its own reasoning — a confidently-wrong belief about what's on screen, or an
invented detail, can turn into an actual, incorrect real-world action, not just a wrong sentence. A
specific, named guardrail exists in Airtap's operating rules addressing one of the most damaging
possible forms of this directly: the agent is explicitly instructed to never invent a username,
phone number, or password under any circumstance, rather than confidently fabricating a plausible
one if it's unsure. More generally, Airtap's operating instructions repeatedly emphasize verifying
current on-screen state against what's actually expected before acting, rather than assuming a
belief about the screen is correct — a direct, if not perfect, mitigation against acting on a
hallucinated understanding of the current state.

### Part C — QA Perspective
- **What to validate**: the agent never fabricates a credential or personal detail under pressure,
  and its final answers are actually grounded in what it observed during the task, not invented.
- **Possible bugs**: a wholly confident final response that doesn't match anything actually seen
  during the task — this produces no error anywhere in the system, since nothing "failed"; the
  output was simply wrong, which makes it a distinctly hard bug category to catch passively.
- **Logs to inspect**: the full reasoning trail across a task, to check whether a wrong final claim
  can actually be traced back to something genuinely observed, or whether it appears from nowhere.
- **Edge cases to test**: tasks where the requested information genuinely isn't available on
  screen — does the agent correctly say so, or does it produce a plausible-sounding guess instead?
- **Likely follow-up questions**: "How would you build an automated check specifically for
  hallucination, given there's no error to catch?" "Why is 'I don't know' considered a correct
  answer worth explicitly testing for?"

---
**Next:** [14_interview_questions_intermediate.md](14_interview_questions_intermediate.md) — agent architecture, tool calling mechanics, grounding, memory, RAG, and evaluation, in depth.
