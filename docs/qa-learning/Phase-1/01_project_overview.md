# 01 — Project Overview

*Phase 1 · Document 1 of 4 — start here.*

## What Airtap is

Airtap is a product that lets an AI agent **use a real phone on your behalf**. You (or a
teammate) type a request in plain language — "what was my last Amazon order," "add milk to my
grocery list," "reply to this text for me" — and a cloud-based AI agent looks at the phone's
screen, decides what to tap/type/swipe next, does it, looks again, and keeps going until the
task is done or it needs you.

The distinguishing engineering bet of this product is *how* the agent touches the phone. Instead
of only using software-level automation (which apps can sometimes detect and block), Airtap can
drive a phone with **genuine hardware input** — a small BLE-to-USB accessory called the **HID
dongle** plugs into the target phone and emits real keyboard/mouse/touch signals, the same way a
physical keyboard or mouse would. From the phone's operating system's point of view, a person is
using the device. Android also supports a pure software path (Accessibility Service), and there's
a third option that needs no physical phone at all — a disposable **cloud phone** (a virtual
Android device you watch and interact with live in the browser).

This matters enormously for QA: this is a product where the "device under test" is sometimes a
literal piece of hardware sitting on a desk with a dongle plugged into it, not just an app or a
web page. A meaningful share of what can go wrong here — Bluetooth range, USB contact, firmware
version drift, a screen timing out, an OEM battery optimizer killing a background service — has
no software equivalent and can't be caught by a unit test.

## Who uses it, and how they get in

- **End users** — consumers who've been admitted off a waitlist (accounts start `WAITLISTED` and
must be allow-listed or manually admitted before they can create tasks). They reach Airtap
through:
  - **Pilot**, the web app (`pilot/`) — the primary surface: compose a task, watch it run, pair
  devices, set up recurring **routines**.
  - **Pilot iOS** (`pilot-ios/`, shipped as "PocketPilot.ai") — the mobile counterpart, with an
  extra trick: a user's own iPhone can *become* a controllable receiver device, not just a
  controller (more in [02](02_high_level_architecture.md)).
  - **Telegram** — DM a bot to create/continue/cancel tasks entirely by text.
  - **iMessage / SMS / RCS** — the same idea, via a texting integration called **Linq**.
- **Internal staff** — the same web app also hosts admin-only surfaces behind permissions: a
dashboard of product/LLM-health metrics, an "evals" console for AI-quality regression testing,
and an admission console for managing the waitlist.



## The shape of a task, end to end

At a glance (fully detailed in [03](03_request_lifecycle.md)):

1. A user types a request into Pilot (or Telegram/iMessage) and picks which device should do the
  work — a paired physical phone or an on-demand cloud phone.
2. The backend creates a **Task** and starts a loop: take a screenshot of the current screen,
  send it plus the conversation so far to an LLM, get back one decision (a tool call), execute
   that decision on the device, and repeat.
3. Each device action is dispatched over whichever channel fits the device — a live network call
  for a cloud phone, or a message relayed through the cloud to a paired physical phone.
4. The loop ends when the agent says it's done, asks the user a clarifying question, asks the user
  to take over (e.g., a login/CAPTCHA it can't solve), hits a safety limit, or errors out.
5. The user watches this happen in near-real-time as a chat-like thread with inline screenshots.



## The major components, at a glance

Full detail lives in [02_high_level_architecture.md](02_high_level_architecture.md); this is just
the map so the names stop being a wall of noise.


| Component                  | What it is                            | Why it exists                                                                                                                                         |
| -------------------------- | ------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| **cortex**                 | Node/TypeScript backend ("the brain") | Owns the AI agent loop, the task/user/routine data model, the HTTP API, and talks to every LLM provider and every device channel.                     |
| **pilot**                  | Next.js web app                       | The primary end-user and internal-staff UI.                                                                                                           |
| **pilot-ios**              | Swift iOS app ("PocketPilot.ai")      | Mobile client; can also turn the phone itself into a receiver device.                                                                                 |
| **receiver**               | Android app                           | Runs on the physical Android phone being controlled; executes commands via Accessibility Service or the HID dongle.                                   |
| **receiver-ios**           | iOS app                               | Runs on a physical iPhone dedicated to being controlled; always uses the HID dongle.                                                                  |
| **HID dongle**             | Small BLE↔USB hardware accessory      | Turns commands into genuine keyboard/mouse/touch hardware signals on the host phone.                                                                  |
| **website**                | Next.js marketing site                | Public-facing site (waitlist signup, etc.) — separate app from Pilot.                                                                                 |
| **packages/**              | Shared TypeScript libraries           | Code shared between cortex/pilot/website (e.g. a "rich response" rendering format, routine template data).                                            |
| **task-analysis-producer** | Standalone Node CLI                   | Offline pipeline that labels/analyzes real production tasks after the fact (distinct from automated evals — see [02](02_high_level_architecture.md)). |
| **web-automation**         | Python/Playwright/pytest suite        | The one *automated* end-to-end test project in the repo today; currently thin (UI-shell smoke checks).                                                |
| **agent-skills/airtap**    | A Claude Code "skill"                 | Lets an AI coding agent drive Airtap's own API (create/monitor tasks). Meta-tooling, not part of the product itself.                                  |




## Vocabulary you'll need immediately

A short glossary — enough to read Documents 2 and 3 without stalling. Terms get their full
treatment later; this is just so nothing is opaque on first read.

- **Task** — one user request and everything the agent did to satisfy it: a running record with a
state (queued, executing, waiting-on-you, completed, failed, ...), a message thread, and a
sequence of **steps**.
- **Step** — one iteration of the agent loop: one screenshot/context read, one LLM decision, one
device action.
- **Receiver** — a controllable device registered to a user's account. Four flavors:
`physical` (Android, Accessibility Service), `androidDongle` (Android, HID dongle),
`iosDongle` (iPhone, HID dongle — the only option on iOS), and `cloud`/`cloud_phone` (an
ephemeral virtual Android device, no hardware involved).
Setup is called **pairing** (physical/dongle: QR code + one-time pairing code).
- **Routine** — a task that runs on a recurring schedule (natural language like "every weekday
morning" gets turned into an iCalendar RRULE) instead of being triggered by a user click.
- **Yoda** / **Omni** — internal code names you'll see constantly in later docs: *Yoda* is the
module that runs the agent's decision loop, it is the brain of the AI Agentthe piece of code
that actually decides what to do next on the phone, one step at a time. Part ok Backend code.
Prepares the screenshot + instructions, calls the LLM, takes the LLM's answer, and acts on
it (taps the button, etc.);
*Omni* is the internal layer that lets Yoda talk to seven different LLM vendors
(Anthropic, Google, OpenAI, xAI, Groq, OpenRouter, AWS Bedrock)
through one consistent interface. The translator in between — Yoda hands it a request,
Omni knows how to phrase it correctly for whichever LLM is being used, and hands back the answer
- **Skill** — a bundled instruction playbook (e.g., "how to use Instagram," "how to book a ride")
the agent can load mid-task for domain-specific guidance, distinct from a **tool** (a concrete
action the agent can call, like "tap," "type," or "search the web").
- **Take over / clarification** — two ways a task pauses for a human: the agent can ask a
clarifying question, or it can explicitly hand control to the user (e.g., "please log in
yourself, then I'll continue").
- **Eval** — an on-demand, dataset-driven regression test of *agent quality itself* ("does the
agent still complete this class of task correctly"), run from an internal Pilot screen. Distinct
from `task-analysis-producer`, which analyzes real historical tasks rather than running new
synthetic ones.



## Environments

Config is environment-driven (`CORTEX_*` / `PILOT_*` / `WEBSITE_*` env vars), and the observed
environments are: `local` (a developer's machine), `dev` (1–4), `qa1`, `qa2`, and `prod`. Each
environment is fully isolated — its own Firebase project, its own storage namespace — so accounts,
paired devices, and tasks in `qa1` are invisible to `qa2` or `prod`. When you're told "reproduce
this in QA," confirm *which* QA environment, since there are at least two, and be aware that some
test accounts (waitlist bypass) are allow-listed per environment and won't automatically exist
everywhere.

## What this means for QA, in one paragraph

Airtap's surface area spans a web app, two native mobile apps, an Android accessibility/HID
automation layer, an iOS BLE/HID/ReplayKit automation layer, physical hardware with its own
firmware, a multi-vendor LLM backend making non-deterministic decisions, and several alternate
text-based front doors (Telegram, iMessage). Correctness bugs can live in any layer, and several
of the most consequential failure classes (hardware disconnects, OEM battery-kill behavior,
"did the AI actually do the right thing") are inherently resistant to conventional automated
testing — which is reflected in the repo already containing a large body of detailed manual test
documentation alongside a comparatively thin automated suite. Document 2 maps how these pieces
physically connect; Document 3 walks through exactly what happens, step by step, from the moment
a user hits send to the moment a task completes — including where, concretely, each of these
layers can fail.

---

**Next:** [02_high_level_architecture.md](02_high_level_architecture.md) — how these components connect, what data flows where, and the full failure-surface map.