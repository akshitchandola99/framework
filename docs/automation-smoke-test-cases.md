# Airtap Smoke Suite — Automation Plan

Companion to `automation-smoke-test-cases.xlsx`. Both are generated from the same source, so they cannot drift.

**Source:** `smoke.xlsx` — 85 test-case rows across 9 scenarios.

## What this document is

The daily post-release smoke suite, reviewed case by case and marked for automation, plus the cases that should exist but do not. Every row carries an explicit automate / partial / no decision, the layer it belongs at, and the blocker if there is one.

## Headline numbers

| | Count |
|---|---|
| Cases in the new plan | **122** |
| Carried over from smoke.xlsx | 83 |
| Rewritten because the source row was not testable | 1 |
| Dropped because the source row was blank | 1 |
| **New cases added to close gaps** | **38** |

| Automation decision | Count | Share |
|---|---|---|
| Yes | 77 | 63% |
| Partial | 30 | 25% |
| No | 15 | 12% |
| **Automatable (Yes + Partial)** | **107** | **88%** |

| Priority | Total | Automatable |
|---|---|---|
| P0 | 55 | 50 |
| P1 | 57 | 48 |
| P2 | 10 | 9 |

| Assert layer (what gates the release) | Cases |
|---|---|
| UI + API | 42 |
| UI | 39 |
| API | 24 |
| Device | 15 |
| Email | 2 |

| Scenario | Total | Automatable | Not automatable |
|---|---|---|---|
| Authentication and App Bootstrap | 11 | 11 | 0 |
| Task Creation and Execution | 16 | 16 | 0 |
| Receiver apk-Pilot pairing | 11 | 8 | 3 |
| Cloud Phone and Remote View | 11 | 11 | 0 |
| Task Search and Share | 4 | 4 | 0 |
| Routines | 20 | 20 | 0 |
| Help and Settings | 13 | 13 | 0 |
| Mobile Browser | 5 | 4 | 1 |
| Linq (iMessage / RCS) | 20 | 19 | 1 |
| HID Dongle | 11 | 1 | 10 |

## What the current smoke suite lacks

### F-01 · Blocker — Two rows in smoke.xlsx are not testable

Of the 85 case rows, row 16 (task stuck in WAITING_FOR_EXECUTION / WAITING_FOR_ANDROID_INSTANCE / EXECUTING) has an empty Pre-Req and an empty Expected Result, and row 77 is entirely blank.

**Action:** Neither row can pass or fail, so both are dead weight in a suite that gates every release. Row 16 rewritten as TASK-08 with a bounded-time SLA assertion; row 77 dropped.

### F-02 · Blocker — The suite never verifies which build it is testing

The suite runs daily after release but has no case that reads the deployed Pilot / Cortex version or a health check.

**Action:** A green run today does not prove the new release is even deployed. Added as AUTH-11, which must gate the whole lane.

### F-03 · Blocker — No API-layer coverage at all

All 85 existing rows are UI-observed. Cortex exposes a full POST API with Bearer PAT auth and an envelope where HTTP 200 can still carry status: Failure.

**Action:** A UI-only suite cannot see a 200/Failure response and is slow and flaky where an API assertion would be exact. The new suite should assert state via API and drive intent via UI. Added AUTH-10, SET-13, TASK-08, PAIR-11.

### F-04 · Coverage — Whole shipped surfaces have zero coverage

Skills (a full CRUD surface with its own backend module), Telegram connection, Personalise, dark mode, browser push notifications, and the waitlist / banned account states.

**Action:** Regressions in these ship undetected. Added SET-07, SET-08, SET-09, SET-10, SET-11, AUTH-09.

### F-05 · Coverage — Strong happy-path bias

Almost all 85 existing rows assert success. Missing: failed task state, invalid share link, expired activation code, invalid webhook signature, denied permissions, offline device, empty prompt, oversized attachment, unparseable schedule.

**Action:** Bad releases usually break the error path, not the happy path. Added TASK-11, TASK-12, TASK-13, PAIR-08, PAIR-10, SHARE-03, RTN-18, RTN-19, SET-12, LINQ-19.

### F-06 · Coverage — No timezone or scheduling-correctness case

Routines are the product's scheduling feature, yet nothing asserts that a routine fires at the correct UTC instant for the user's timezone or across DST.

**Action:** The classic and highest-impact scheduler bug is untested. Added RTN-17 at P0.

### F-07 · Coverage — No security or isolation cases

The public share page, the unauthenticated Linq webhook and the unauthenticated receiver endpoints have no negative coverage, and nothing checks cross-account isolation.

**Action:** Added SHARE-03, SHARE-04, LINQ-19, AUTH-10.

### F-08 · Reliability — Several cases assert on non-deterministic model output

Custom schedule label, memory content, and the voice transcript are all LLM-generated. Asserting their text will fail as phrasing drifts.

**Action:** Rewrite each to assert persisted structure (recurrence rule, next-run timestamp, entry exists, transcript non-empty) instead of wording. Applies to RTN-15, RTN-02, SET-06, TASK-05.

### F-09 · Reliability — Assertions are too shallow for a streaming product

'Video is visible' passes on a frozen black frame; 'audio plays when unmuted' cannot be seen from the DOM; 'tap works' is asserted at the gesture, not the effect.

**Action:** Use RTCPeerConnection.getStats() for frames decoded, media track state for audio, and an observable on-device effect for input. Applies to CP-01, CP-03, CP-04, CP-06.

### F-10 · Runtime — Time-bound cases cannot live in a daily smoke lane

The ~15 minute Cloudphone idle timeout, the scheduled-run wait, and the disabled-routine-does-not-run negative all block on wall-clock time.

**Action:** Split the suite into a fast smoke lane and a nightly lane, or expose a configurable idle timeout in QA. Applies to CP-07, RTN-08, RTN-13.

### F-11 · Scope — 15 cases are physically unautomatable and should be scoped out

15 cases - 10 HID dongle, 3 receiver-pairing cases needing a real Android, RCS delivery, and the mobile soft keyboard - require physical hardware or real devices.

**Action:** Report these separately so automation coverage percentages are honest, and give them their own hardware-lab lane rather than pretending Playwright will get there.

### F-12 · Infrastructure — No test-data lifecycle

New-user onboarding, waitlist and banned cases all need accounts in specific states, and nothing exists to create, reset or delete them.

**Action:** Without this the onboarding cases are one-shot and test accounts accumulate stale devices, routines and tasks. Tracked as enabler E2.

### F-13 · Maintainability — Existing tests select on visible copy

The current suite matches Try it, Cloud Phone and Airtap 1.0 by text and regex.

**Action:** Every copy change or new model name breaks the suite. The fresh suite should require stable test ids on core controls (enabler E7) before it grows past a handful of tests.

### F-14 · Coverage — Mobile coverage is Cloudphone-only

The three mobile cases all test Cloudphone. Login, home, composer, Recent, Routines and Settings have no mobile smoke.

**Action:** Added MOB-04 and MOB-05.

### F-15 · Coverage — Deep-link routing is untested

Linq sends users into Pilot via task and location links, but nothing verifies that a direct task URL opens the right task.

**Action:** Added TASK-14; complements LINQ-13.

## Enablers we need before parts of this can be automated

| ID | Enabler | Unblocks | Priority |
|---|---|---|---|
| **E1** | Fixed OTP for whitelisted QA test numbers, or an API to read the last OTP | AUTH-02, AUTH-04 | High |
| **E2** | Test-user provisioning and teardown API (create admitted / waitlisted / banned, delete) | AUTH-03, AUTH-04, AUTH-09, LINQ-01, and isolation for the whole suite | High |
| **E3** | Mailbox automation (Mailosaur, Gmail API, or a QA catch-all inbox) | RTN-16, SET-01, SET-03 | Medium |
| **E4** | Linq webhook signing secret for QA, plus a way to read outbound messages | The 16-case Linq block | High |
| **E5** | Configurable Cloudphone idle timeout in QA | CP-07 | Low |
| **E6** | An always-on Android emulator or device running the receiver APK, seeded as a second device | PAIR-03, PAIR-05, PAIR-06, RTN-05 | Medium |
| **E7** | Stable test ids on core controls | Every UI case | High |
| **E8** | A fixture prompt that reliably parks a task in WAITING_FOR_USER_INPUT | TASK-07, LINQ-12 | Medium |
| **E9** | Real-device browser cloud | MOB-02 | Low |
| **E10** | A QA Telegram test bot and chat credentials | SET-08 | Low |

- **E1** — Without it, mobile sign-in for IN / US / CN, a P0 login path, can never run automated.
- **E2** — Also the fix for test accounts silting up with stale devices, routines and tasks.
- **E3** — Three cases assert on email and none can be automated without it.
- **E4** — The webhook is unauthenticated and signature-verified, so inbound can be simulated at API level. This single enabler converts most of the Linq block from manual to automatable.
- **E5** — Turns a 15-minute wall-clock test into a fast one.
- **E6** — Also unlocks device-switching and non-Cloudphone routine execution.
- **E7** — The current suite selects on visible copy and will break on wording changes. Agree this with frontend before the new suite grows.
- **E8** — Otherwise both cases flake.
- **E9** — Emulated Chromium has no soft keyboard, so this case cannot be proven without real devices.
- **E10** — Telegram exposes a public Bot API, so once credentials exist the messaging half is far easier to automate than Linq.

## Recommended lanes

The suite should not run as one flat block. Split it:

1. **Pre-flight (API, seconds).** AUTH-10, AUTH-11, PAIR-11, LINQ-19, SET-13. If the wrong build is deployed or auth is broken, fail here and skip the rest.
2. **Fast smoke (UI + API, target under 15 min).** All P0 UI cases with no wall-clock dependency.
3. **Nightly (time-bound).** CP-07 idle timeout, RTN-08 scheduled execution, RTN-13 disabled-routine negative, RTN-17 timezone / DST.
4. **Hardware lab (manual today).** The 10 HID dongle cases, PAIR-03 / PAIR-06 / PAIR-07, LINQ-16 RCS, MOB-02 soft keyboard.

## Build order

1. `SET-05` PAT lifecycle — it produces the credential the whole API layer depends on.
2. Pre-flight API block (AUTH-10, AUTH-11).
3. Auth session fixture from `AUTH-01` storage state, then AUTH-05 / AUTH-06 / AUTH-07.
4. `TASK-01` end-to-end, then the rest of the task block — plus `RTN-12` and `TASK-10` early, since delete is the teardown primitive everything else needs.
5. Routines, Settings, Skills (`SET-07`), Share.
6. Cloudphone streaming assertions, which are the highest-effort UI work.
7. Linq, once E4 lands.

## Full case list

### Authentication and App Bootstrap — 11/11 automatable

| ID | Test Case | Origin | Automate | Pri | Act | Assert | Effort | Notes / Blockers |
|---|---|---|---|---|---|---|---|---|
| `AUTH-01` | Existing user sign in via EMAIL (google) | Existing | Yes | P0 | UI | UI | M | Google blocks scripted OAuth. Sign in once, persist storage_state, and reuse it as the session fixture for every other UI test; refresh it in a nightly bootstrap job. Needs E7. |
| `AUTH-02` | Existing user sign in via MOBILE-NUMBER (IN / US / CN) | Existing | Partial | P0 | UI | UI + API | M | BLOCKED on E1. No deterministic OTP today, so this P0 login path cannot run daily. Parametrise over the 3 country codes once a fixed test OTP exists. |
| `AUTH-03` | New user onboarding via EMAIL (google) | Existing | Partial | P1 | UI | UI + API | L | BLOCKED on E2. Needs a fresh account per run plus teardown, otherwise it is a one-shot test that can never repeat. |
| `AUTH-04` | New user onboarding via MOBILE-NUMBER (IN / US / CN) | Existing | Partial | P1 | UI | UI + API | L | BLOCKED on E1 and E2. |
| `AUTH-05` | Session restores after reload | Existing | Yes | P0 | UI | UI | S | Ideal first test of the new suite. Fast, deterministic, no external dependency. |
| `AUTH-06` | User can log out | Existing | Yes | P0 | UI | UI | S | Assert the redirect AND that a direct navigation to a protected route afterwards is refused. |
| `AUTH-07` | Protected route while signed out redirects to login | **NEW** | Yes | P0 | UI | UI | S | GAP: the suite only implies this inside the logout case. Route guarding deserves its own parametrised test. |
| `AUTH-08` | Invalidated session forces re-authentication | **NEW** | Yes | P1 | UI + API | UI + API | S | GAP: no negative auth case exists anywhere in the suite. |
| `AUTH-09` | Waitlisted and banned account states render correctly | **NEW** | Partial | P1 | UI | UI + API | M | GAP: /waitlist and /banned are shipped routes with zero smoke coverage. Depends on E2 to hold accounts in those states. |
| `AUTH-10` | Cortex API rejects unauthenticated calls | **NEW** | Yes | P0 | API | API | S | GAP: the suite is 100% UI-observed. This is the cheapest, fastest release gate available and should run first in the lane. |
| `AUTH-11` | Deployed build and health are verified before the suite runs | **NEW** | Yes | P0 | API | API | S | GAP: the suite runs 'every day after release' but never asserts WHICH build is deployed. Today a green run could be against yesterday's build. This must gate the whole lane. |

### Task Creation and Execution — 16/16 automatable

| ID | Test Case | Origin | Automate | Pri | Act | Assert | Effort | Notes / Blockers |
|---|---|---|---|---|---|---|---|---|
| `TASK-01` | Task runs on Cloudphone | Existing | Yes | P0 | UI | UI + API | M | Core end-to-end. Submit via UI, poll terminal state via API rather than watching the DOM; assert both HTTP 200 and body status == Success. |
| `TASK-02` | Task with image upload runs | Existing | Yes | P0 | UI | UI | M | set_input_files with a committed fixture image. Keep the fixture in the repo, never a machine-local path. |
| `TASK-03` | Follow-up works after task completion | Existing | Yes | P0 | UI | UI + API | M | Assert the follow-up shares the parent task id; do not just count message bubbles. |
| `TASK-04` | Model switch works | Existing | Yes | P0 | UI | UI + API | M | The 'uses the selected model' half is only provable via the API/task record. UI-only assertion is not enough. |
| `TASK-05` | Microphone input creates composer text | Existing | Partial | P2 | UI | UI | L | Feasible with Chromium fake-media flags and a committed WAV fixture. STT output is non-deterministic, so assert a non-empty transcript and successful submit, never exact wording. |
| `TASK-06` | Active task can be stopped | Existing | Yes | P0 | UI | UI + API | M | Confirm the backend state actually left EXECUTING; a UI badge alone can lie. |
| `TASK-07` | Waiting-for-user-input state is actionable | Existing | Partial | P1 | UI | UI + API | L | BLOCKED on E8. Without a fixture prompt that reliably parks a task in WAITING_FOR_USER_INPUT this will flake daily. |
| `TASK-08` | Task does not stall in WAITING_FOR_EXECUTION / WAITING_FOR_ANDROID_INSTANCE / EXECUTING beyond SLA | **Rewritten** | Yes | P0 | API | API | S | DEFECT IN SOURCE: row 16 of smoke.xlsx has no pre-req and no expected result, so it can neither pass nor fail. Rewritten here as a bounded-time state assertion. Per-state SLA values must be agreed with backend before coding. |
| `TASK-09` | Latest task shows in Recent | Existing | Yes | P0 | UI | UI + API | S |  |
| `TASK-10` | Task can be deleted from Recent | Existing | Yes | P0 | UI | UI + API | S | Verify deletion server-side too, so a UI-only list refresh cannot mask a failed delete. |
| `TASK-11` | Empty or whitespace-only prompt cannot be submitted | **NEW** | Yes | P0 | UI | UI | S | GAP: no input-validation case exists. Cheap and catches composer regressions immediately. |
| `TASK-12` | Oversized or unsupported attachment is rejected clearly | **NEW** | Yes | P1 | UI | UI + API | M | GAP: backend enforces a 50 MB body cap; nothing in the suite exercises the limit or the error surface. |
| `TASK-13` | Failed task shows a failed state with an actionable error | **NEW** | Yes | P1 | UI | UI + API | M | GAP: the suite covers completion and stop but never the FAILED state. The failure path is what users actually hit on a bad release. |
| `TASK-14` | Direct task URL opens the correct task | **NEW** | Yes | P0 | UI | UI | S | GAP: deep-link routing is untested despite being how Linq intervention links land users in the app. |
| `TASK-15` | Second task on a busy device is queued or blocked with clear UI | **NEW** | Yes | P2 | UI | UI + API | M | GAP: concurrency behaviour is referenced in the routine Run Now case but never tested directly. |
| `TASK-16` | Task list paging loads older tasks | **NEW** | Yes | P2 | UI | UI | M | GAP: search is tested, listing at scale is not. |

### Receiver apk-Pilot pairing — 8/11 automatable

| ID | Test Case | Origin | Automate | Pri | Act | Assert | Effort | Notes / Blockers |
|---|---|---|---|---|---|---|---|---|
| `PAIR-01` | Pairing entry points are visible | Existing | Yes | P0 | UI | UI | S | Clipboard assertion needs clipboard-read permission granted on the context. |
| `PAIR-02` | Autopilot APK download | Existing | Yes | P0 | UI | UI + API | S | The APK URL endpoint is unauthenticated, so assert it resolves with HTTP 200 and an APK content type at API level, then assert the UI download event separately. Do not download the full binary on every run. |
| `PAIR-03` | Pairing via Autopilot app | Existing | No | P0 | Device | Device | L | Out of Playwright's reach. Automatable later with an always-on Android emulator running the receiver APK, driven by adb/Appium (E6). Keep manual for the daily smoke. |
| `PAIR-04` | Connected devices list opens | Existing | Yes | P0 | UI | UI | S |  |
| `PAIR-05` | Device switching works before task submission | Existing | Yes | P1 | UI | UI + API | M | Needs E6 (a second seeded device). Assert the executing device from the task record, not the picker label. |
| `PAIR-06` | Android Autopilot task run | Existing | No | P0 | Device | Device | L | Same constraint as PAIR-03. The Pilot-side state display can be asserted once E6 exists. |
| `PAIR-07` | Autopilot notifications | Existing | No | P2 | Device | Device | M | Native Android app preference. Manual, or Appium in the device lab lane. |
| `PAIR-08` | Expired or invalid activation code is rejected | **NEW** | Yes | P1 | API | API | M | GAP: pairing is only tested on the happy path. |
| `PAIR-09` | Device can be unpaired and default falls back | **NEW** | Yes | P1 | UI | UI + API | M | GAP: the suite pairs devices but never removes one, so the cleanup path is untested and test accounts accumulate stale devices. |
| `PAIR-10` | Offline receiver is shown offline and is not selectable | **NEW** | Yes | P1 | UI | UI + API | M | GAP: no device-availability case exists. |
| `PAIR-11` | Receiver version meets the minimum supported by this release | **NEW** | Yes | P1 | API | API | S | GAP: the repo treats the receiver RPC contract as versioned and mandates version bumps, yet the daily smoke never checks compatibility. This is a pure API assertion and belongs in the pre-flight block with AUTH-11. |

### Cloud Phone and Remote View — 11/11 automatable

| ID | Test Case | Origin | Automate | Pri | Act | Assert | Effort | Notes / Blockers |
|---|---|---|---|---|---|---|---|---|
| `CP-01` | Cloudphone auto-opens on login | Existing | Yes | P0 | UI | UI | M | Assert the stream via RTCPeerConnection.getStats() (framesDecoded increasing) rather than the presence of a <video> element. 'Video is visible' passes on a black frame. |
| `CP-02` | Cloudphone stays closed after user closes it | Existing | Yes | P1 | UI | UI | S | Also assert the preference survives a reload. |
| `CP-03` | Cloudphone opens and streams | Existing | Yes | P0 | UI | UI | M | Same getStats() assertion as CP-01. |
| `CP-04` | Cloudphone input works | Existing | Yes | P1 | UI | UI | L | Assert the EFFECT, not the gesture: drive a known on-device action and verify the resulting device state. Verifying only that a click dispatched proves nothing. |
| `CP-05` | Cloudphone copy / paste | Existing | Partial | P2 | UI | UI | L | Needs clipboard-read and clipboard-write permissions. The copy-out direction is the hard half and may stay manual. |
| `CP-06` | Cloudphone mute / unmute | Existing | Yes | P1 | UI | UI | M | Assert the media element's muted/volume state and the audio track, not only the icon. 'Audio plays' is only provable via track state in a headless run. |
| `CP-07` | Cloudphone idle timeout | Existing | Partial | P2 | UI | UI | L | A 15-minute wall-clock wait cannot sit in a daily smoke lane. Move to the nightly lane, or get a configurable idle timeout in QA (E5). |
| `CP-08` | Cloudphone data is preserved | Existing | Yes | P1 | UI | UI | L | Write a deterministic marker on the device (a file or an app state) and assert it after re-login instead of eyeballing the screen. |
| `CP-09` | Cloudphone recovers from a stream interruption | **NEW** | Yes | P1 | UI | UI | M | GAP: no resiliency case anywhere in the suite. Playwright can simulate offline/online on the context, so this is cheap to automate. |
| `CP-10` | Maintenance and terminal-state views render | **NEW** | Yes | P2 | UI | UI | M | GAP: these views are shipped components with no coverage. They are exactly what users see on a bad day. |
| `CP-11` | Remote view pane survives expand, collapse and resize | **NEW** | Yes | P2 | UI | UI | S |  |

### Task Search and Share — 4/4 automatable

| ID | Test Case | Origin | Automate | Pri | Act | Assert | Effort | Notes / Blockers |
|---|---|---|---|---|---|---|---|---|
| `SHARE-01` | Recent task search works | Existing | Yes | P0 | UI | UI | S | Seed the searched task in the same run so the assertion does not depend on account history. |
| `SHARE-02` | Task can be shared | Existing | Yes | P0 | UI | UI | M | Open the copied URL in a brand-new browser context with no storage state. That is the only way to actually prove 'without login'. |
| `SHARE-03` | Invalid or revoked share link does not expose data | **NEW** | Yes | P1 | UI | UI + API | M | GAP: sharing is tested positively only. This is the security-relevant half of a public, unauthenticated surface. |
| `SHARE-04` | Share page does not leak another account's task | **NEW** | Yes | P1 | API | API | M | GAP: no cross-tenant isolation check exists in the suite. |

### Routines — 20/20 automatable

| ID | Test Case | Origin | Automate | Pri | Act | Assert | Effort | Notes / Blockers |
|---|---|---|---|---|---|---|---|---|
| `RTN-01` | Create routine via Routines page UI | Existing | Yes | P0 | UI | UI + API | M | Verify the persisted routine record, not only the list row. |
| `RTN-02` | Create routine via chat | Existing | Yes | P0 | UI | UI + API | M | Chat parsing is LLM-driven. Assert the resulting schedule fields via API; do not assert the assistant's wording. |
| `RTN-03` | Set time / frequency | Existing | Yes | P0 | UI | UI | S | Parametrise across daily / weekly / monthly. |
| `RTN-04` | Switch model on routine | Existing | Yes | P1 | UI | UI + API | M |  |
| `RTN-05` | Switch device on routine | Existing | Yes | P1 | UI | UI + API | M | Needs E6 for a non-Cloudphone target. |
| `RTN-06` | Disable routine | Existing | Yes | P0 | UI | UI | S |  |
| `RTN-07` | Re-enable routine | Existing | Yes | P0 | UI | UI | S | Assert the recomputed next-run time, which is where re-enable usually breaks. |
| `RTN-08` | Scheduled execution at set time | Existing | Yes | P1 | API | API | L | Schedule ~3 minutes out and poll the task list by API. Time-bound: put this in the nightly lane, not the fast smoke lane. |
| `RTN-09` | Run Now execution | Existing | Yes | P0 | UI | UI + API | M | The fast proxy for RTN-08; it exercises the same execution path without the wait. |
| `RTN-10` | Routine history opens as task | Existing | Yes | P1 | UI | UI | S |  |
| `RTN-11` | Pre-defined routine setup | Existing | Yes | P1 | UI | UI + API | M | Template content changes; select by position or a stable template id, not by title text. |
| `RTN-12` | Delete routine | Existing | Yes | P0 | UI | UI + API | S | Also the teardown primitive every routine test needs; build it first. |
| `RTN-13` | Disabled routine does not auto-run | Existing | Yes | P1 | API | API | L | Time-bound negative test. Nightly lane. |
| `RTN-14` | Edit title / prompt only | Existing | Yes | P0 | UI | UI + API | S | Assert the total routine count is unchanged; that is what catches the duplicate bug. |
| `RTN-15` | Custom schedule AI parse | Existing | Yes | P1 | UI | UI + API | M | Assert the generated recurrence rule and next-run timestamp via API. Asserting the human-readable label will flake as the model's phrasing drifts. |
| `RTN-16` | Routine email notification | Existing | Partial | P1 | UI | Email | M | BLOCKED on E3. No mailbox automation exists. |
| `RTN-17` | Routine fires at the correct instant across timezones | **NEW** | Yes | P0 | API | API | M | GAP: scheduling is the core of this feature and timezone correctness is never asserted. This is the single highest-value missing routine case. |
| `RTN-18` | Routine run against an offline device behaves predictably | **NEW** | Yes | P1 | UI | UI + API | M | GAP: the offline-device path is untested for routines. |
| `RTN-19` | Unparseable custom schedule is rejected clearly | **NEW** | Yes | P1 | UI | UI + API | S | GAP: the AI parse case only covers a clean input. A silently persisted bad schedule is worse than a rejection. |
| `RTN-20` | Routine list survives reload and re-login | **NEW** | Yes | P1 | UI | UI | S |  |

### Help and Settings — 13/13 automatable

| ID | Test Case | Origin | Automate | Pri | Act | Assert | Effort | Notes / Blockers |
|---|---|---|---|---|---|---|---|---|
| `SET-01` | Support ticket can be submitted | Existing | Yes | P0 | UI | UI + API | S | Automate the submission and the API acknowledgement. The email half moves to SET-03. |
| `SET-02` | Support ticket image and screenshot | Existing | Partial | P1 | UI | UI | L | Image attach is trivial. In-app screenshot capture uses screen capture, which needs a Chromium auto-select flag and is brittle; split the case so the attach half can be automated now. |
| `SET-03` | Support ticket email verification | Existing | Partial | P1 | UI | Email | M | BLOCKED on E3. |
| `SET-04` | Location update works | Existing | Yes | P0 | UI | UI | S | Fully deterministic: grant geolocation on the context and set fixed coordinates, then assert the resolved location text. |
| `SET-05` | Personal access token lifecycle | Existing | Yes | P0 | UI | UI + API | M | Build this early: the token it creates is the bootstrap credential for the entire API layer of the new suite. |
| `SET-06` | Short term & long term memory is generated | Existing | Yes | P1 | UI | UI + API | M | Memory content is model-generated. Assert that entries exist, that an edit persists and that a delete removes it; never assert the text. |
| `SET-07` | Skills lifecycle: create, edit, toggle, delete, export | **NEW** | Yes | P0 | UI | UI + API | M | MAJOR GAP: Skills is a shipped surface with a full CRUD backend module and zero coverage in the smoke suite. It should be a P0 block, not an afterthought. |
| `SET-08` | Telegram connect, connected status and disconnect | **NEW** | Partial | P1 | UI + API | UI + API | M | GAP: Settings ships a Telegram panel and the backend has a Telegram module, but the smoke suite only covers iMessage/RCS. The Telegram Bot API makes the messaging half far more automatable than Linq. Needs E10. |
| `SET-09` | Personalise settings persist | **NEW** | Yes | P1 | UI | UI | S | GAP: Personalise is a settings section with no coverage. |
| `SET-10` | Dark mode toggle applies and persists | **NEW** | Yes | P2 | UI | UI | S | GAP: cheap, and theme regressions are common and highly visible. |
| `SET-11` | Browser push notification for task completion | **NEW** | Partial | P2 | UI | UI | L | GAP: push messaging is bootstrapped in the app shell and untested. Push delivery assertions in headless Chromium are brittle. |
| `SET-12` | Location permission denied is handled gracefully | **NEW** | Yes | P1 | UI | UI | S | GAP: only the granted path is covered. |
| `SET-13` | PAT authenticates API calls and a deleted PAT stops working | **NEW** | Yes | P0 | API | API | S | GAP: the existing PAT case stops at the UI. Whether the token actually authenticates, and whether revocation takes effect, is the part that matters. |

### Mobile Browser — 4/5 automatable

| ID | Test Case | Origin | Automate | Pri | Act | Assert | Effort | Notes / Blockers |
|---|---|---|---|---|---|---|---|---|
| `MOB-01` | Cloudphone tap / input / navigation works | Existing | Yes | P1 | UI | UI | M | Playwright device descriptors with touch enabled. Note in the report that this is emulation, not a real device, so it will not catch true mobile-browser defects. |
| `MOB-02` | Cloudphone soft keyboard opens on mobile | Existing | No | P1 | Device | Device | M | Emulated Chromium has no soft keyboard, so this cannot be proven in Playwright. Needs a real-device cloud (E9) or stays manual. |
| `MOB-03` | Cloudphone mute / unmute on mobile | Existing | Yes | P1 | UI | UI | S |  |
| `MOB-04` | Core app surfaces render correctly on a mobile viewport | **NEW** | Yes | P0 | UI | UI | M | GAP: mobile coverage today is Cloudphone-only. The rest of the app has no mobile smoke at all, despite mobile browser being a listed supported surface. |
| `MOB-05` | Task can be submitted and completed on mobile browser | **NEW** | Yes | P0 | UI | UI + API | M | GAP: the primary user action is never exercised on mobile. |

### Linq (iMessage / RCS) — 19/20 automatable

| ID | Test Case | Origin | Automate | Pri | Act | Assert | Effort | Notes / Blockers |
|---|---|---|---|---|---|---|---|---|
| `LINQ-01` | New account creation via DM | Existing | Partial | P0 | API | API | M | Needs E4 (webhook signing secret) plus E2 for teardown of the created account. |
| `LINQ-02` | Connect Messages from Pilot | Existing | Partial | P0 | UI + API | UI + API | M | Pilot half is automatable now; the inbound /link half needs E4. |
| `LINQ-03` | Connected status on Pilot | Existing | Yes | P1 | UI | UI + API | S | Fully automatable today against a pre-linked test account. |
| `LINQ-04` | Greeting response on first message | Existing | Partial | P1 | API | API | S | Needs E4. The 'no task is created' half is a clean API assertion. |
| `LINQ-05` | Task first message starts the task | Existing | Partial | P0 | API | API | M | Needs E4. |
| `LINQ-06` | Follow-up continues same task | Existing | Partial | P0 | API | API | M | Needs E4. Assert on task id, which is exact and non-flaky. |
| `LINQ-07` | /stop cancels an active task | Existing | Partial | P0 | API | API | S | Needs E4. |
| `LINQ-08` | /new creates a new task | Existing | Partial | P0 | API | API | S | Needs E4. |
| `LINQ-09` | Task completion message is received | Existing | Partial | P0 | API | API | M | Needs E4 plus a way to read outbound messages (provider sandbox or outbound store). |
| `LINQ-10` | Attachments with text are allowed | Existing | Partial | P1 | API | API | M | Needs E4. Parametrise over the three file types. |
| `LINQ-11` | Group chats are not allowed | Existing | Partial | P1 | API | API | M | Needs E4 with a group-shaped webhook payload. |
| `LINQ-12` | Waiting for user intervention sends task link | Existing | Partial | P1 | API | API | M | Needs E4 and E8. |
| `LINQ-13` | Task link opens Pilot without sign-in | Existing | Yes | P0 | UI | UI | M | Fully automatable once a valid link exists: open it in a clean context with no storage state. Also assert the link cannot be reused to reach unrelated tasks. |
| `LINQ-14` | Message queuing while task is executing | Existing | Partial | P1 | API | API | M | Needs E4. |
| `LINQ-15` | Location task asks for location via Messages | Existing | Partial | P1 | UI + API | UI + API | M | Needs E4; the Pilot half is automatable now. |
| `LINQ-16` | Task works on RCS | Existing | No | P1 | Device | Device | L | True RCS delivery needs a real Android handset and carrier. Only the backend half is simulatable; keep the delivery check manual. |
| `LINQ-18` | Unknown or unlinked sender is handled, never silently dropped | **NEW** | Partial | P1 | API | API | M | GAP: only linked and fresh senders are covered. Needs E4. |
| `LINQ-19` | Webhook with an invalid signature is rejected | **NEW** | Yes | P0 | API | API | S | GAP: this is a publicly reachable unauthenticated endpoint with no negative coverage in the suite. Highest security value per line of code in this whole plan. |
| `LINQ-20` | Duplicate webhook delivery is idempotent | **NEW** | Partial | P1 | API | API | M | GAP: providers retry deliveries. Needs E4. |
| `LINQ-21` | Disconnect Messages from Pilot unlinks the sender | **NEW** | Partial | P1 | UI + API | UI + API | M | GAP: connect is covered, disconnect is not. Pilot half is automatable now; the inbound half needs E4. |

### HID Dongle — 1/11 automatable

| ID | Test Case | Origin | Automate | Pri | Act | Assert | Effort | Notes / Blockers |
|---|---|---|---|---|---|---|---|---|
| `HID-01` | Dongle pairs and shows connected | Existing | No | P0 | Device | Device | M | Physical hardware. Keep manual; long-term home is a hardware lab lane, not Playwright. |
| `HID-02` | Task runs on Android with dongle | Existing | No | P0 | Device | Device | L | Physical hardware. The Pilot-side submission half can be automated; the on-device verification cannot. |
| `HID-03` | Task runs on iOS with dongle | Existing | No | P0 | Device | Device | L | Physical hardware. |
| `HID-04` | Tap works through dongle | Existing | No | P1 | Device | Device | M | Physical hardware. |
| `HID-05` | Swipe works through dongle | Existing | No | P1 | Device | Device | M | Physical hardware. |
| `HID-06` | Text typing works through dongle | Existing | No | P1 | Device | Device | M | Physical hardware. |
| `HID-07` | Long press works through dongle | Existing | No | P1 | Device | Device | M | Physical hardware. |
| `HID-08` | Dongle auto-reconnects after power cycle | Existing | No | P1 | Device | Device | M | Physical hardware; power cycling needs a switchable USB hub to ever be automated. |
| `HID-09` | Clear error when dongle is disconnected | Existing | Partial | P0 | UI + API | UI + API | M | The Pilot-side error surface is automatable by driving the receiver into a disconnected state through the API. Only the physical half needs the lab. |
| `HID-10` | iOS AssistiveTouch and broadcast required | Existing | No | P1 | Device | Device | M | Physical iOS device and system settings. |
| `HID-11` | Dongle firmware and receiver version are compatible with this release | **NEW** | No | P1 | Device | Device | S | GAP: no version compatibility gate for the hardware path. |

## Dropped from the source suite

- **smoke.xlsx row 77** (Linq block) — entirely blank: no test case, no pre-req, no expected result. Not carried over.

