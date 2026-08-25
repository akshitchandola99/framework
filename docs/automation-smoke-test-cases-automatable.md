# Airtap Smoke Suite — Automatable Cases

The 107 of 122 cases that can be automated. The 15 hardware / real-device cases are excluded entirely — see `automation-smoke-test-cases.md` for those and for the gap analysis.

- **Automate now (no blocker):** 77
- **Automate after enablers:** 30
- **Total:** 107

| Lane | Cases | What it is |
|---|---|---|
| 1 · Pre-flight | 5 | Pure API, runs in seconds, gates everything else |
| 2 · Fast smoke | 67 | UI + API, no wall-clock dependency, target under 15 min |
| 3 · Nightly | 5 | Time-bound; cannot fit a daily smoke window |

Priority within *automate now*: **P0 41** · P1 31 · P2 5

## Automate now

### Lane 1 · Pre-flight — 5 cases

| ID | Test Case | Scenario | Pri | Act | Assert | Effort | Automation Notes |
|---|---|---|---|---|---|---|---|
| `AUTH-10` | Cortex API rejects unauthenticated calls *(new)* | Authentication and App Bootstrap | P0 | API | API | S | GAP: the suite is 100% UI-observed. This is the cheapest, fastest release gate available and should run first in the lane. |
| `AUTH-11` | Deployed build and health are verified before the suite runs *(new)* | Authentication and App Bootstrap | P0 | API | API | S | GAP: the suite runs 'every day after release' but never asserts WHICH build is deployed. Today a green run could be against yesterday's build. This must gate the whole lane. |
| `LINQ-19` | Webhook with an invalid signature is rejected *(new)* | Linq (iMessage / RCS) | P0 | API | API | S | GAP: this is a publicly reachable unauthenticated endpoint with no negative coverage in the suite. Highest security value per line of code in this whole plan. |
| `SET-13` | PAT authenticates API calls and a deleted PAT stops working *(new)* | Help and Settings | P0 | API | API | S | GAP: the existing PAT case stops at the UI. Whether the token actually authenticates, and whether revocation takes effect, is the part that matters. |
| `PAIR-11` | Receiver version meets the minimum supported by this release *(new)* | Receiver apk-Pilot pairing | P1 | API | API | S | GAP: the repo treats the receiver RPC contract as versioned and mandates version bumps, yet the daily smoke never checks compatibility. This is a pure API assertion and belongs in the pre-flight block with AUTH-11. |

### Lane 2 · Fast smoke — 67 cases

| ID | Test Case | Scenario | Pri | Act | Assert | Effort | Automation Notes |
|---|---|---|---|---|---|---|---|
| `AUTH-01` | Existing user sign in via EMAIL (google) | Authentication and App Bootstrap | P0 | UI | UI | M | Google blocks scripted OAuth. Sign in once, persist storage_state, and reuse it as the session fixture for every other UI test; refresh it in a nightly bootstrap job. Needs E7. |
| `AUTH-05` | Session restores after reload | Authentication and App Bootstrap | P0 | UI | UI | S | Ideal first test of the new suite. Fast, deterministic, no external dependency. |
| `AUTH-06` | User can log out | Authentication and App Bootstrap | P0 | UI | UI | S | Assert the redirect AND that a direct navigation to a protected route afterwards is refused. |
| `AUTH-07` | Protected route while signed out redirects to login *(new)* | Authentication and App Bootstrap | P0 | UI | UI | S | GAP: the suite only implies this inside the logout case. Route guarding deserves its own parametrised test. |
| `CP-01` | Cloudphone auto-opens on login | Cloud Phone and Remote View | P0 | UI | UI | M | Assert the stream via RTCPeerConnection.getStats() (framesDecoded increasing) rather than the presence of a <video> element. 'Video is visible' passes on a black frame. |
| `CP-03` | Cloudphone opens and streams | Cloud Phone and Remote View | P0 | UI | UI | M | Same getStats() assertion as CP-01. |
| `LINQ-13` | Task link opens Pilot without sign-in | Linq (iMessage / RCS) | P0 | UI | UI | M | Fully automatable once a valid link exists: open it in a clean context with no storage state. Also assert the link cannot be reused to reach unrelated tasks. |
| `MOB-04` | Core app surfaces render correctly on a mobile viewport *(new)* | Mobile Browser | P0 | UI | UI | M | GAP: mobile coverage today is Cloudphone-only. The rest of the app has no mobile smoke at all, despite mobile browser being a listed supported surface. |
| `MOB-05` | Task can be submitted and completed on mobile browser *(new)* | Mobile Browser | P0 | UI | UI + API | M | GAP: the primary user action is never exercised on mobile. |
| `PAIR-01` | Pairing entry points are visible | Receiver apk-Pilot pairing | P0 | UI | UI | S | Clipboard assertion needs clipboard-read permission granted on the context. |
| `PAIR-02` | Autopilot APK download | Receiver apk-Pilot pairing | P0 | UI | UI + API | S | The APK URL endpoint is unauthenticated, so assert it resolves with HTTP 200 and an APK content type at API level, then assert the UI download event separately. Do not download the full binary on every run. |
| `PAIR-04` | Connected devices list opens | Receiver apk-Pilot pairing | P0 | UI | UI | S |  |
| `RTN-01` | Create routine via Routines page UI | Routines | P0 | UI | UI + API | M | Verify the persisted routine record, not only the list row. |
| `RTN-02` | Create routine via chat | Routines | P0 | UI | UI + API | M | Chat parsing is LLM-driven. Assert the resulting schedule fields via API; do not assert the assistant's wording. |
| `RTN-03` | Set time / frequency | Routines | P0 | UI | UI | S | Parametrise across daily / weekly / monthly. |
| `RTN-06` | Disable routine | Routines | P0 | UI | UI | S |  |
| `RTN-07` | Re-enable routine | Routines | P0 | UI | UI | S | Assert the recomputed next-run time, which is where re-enable usually breaks. |
| `RTN-09` | Run Now execution | Routines | P0 | UI | UI + API | M | The fast proxy for RTN-08; it exercises the same execution path without the wait. |
| `RTN-12` | Delete routine | Routines | P0 | UI | UI + API | S | Also the teardown primitive every routine test needs; build it first. |
| `RTN-14` | Edit title / prompt only | Routines | P0 | UI | UI + API | S | Assert the total routine count is unchanged; that is what catches the duplicate bug. |
| `SET-01` | Support ticket can be submitted | Help and Settings | P0 | UI | UI + API | S | Automate the submission and the API acknowledgement. The email half moves to SET-03. |
| `SET-04` | Location update works | Help and Settings | P0 | UI | UI | S | Fully deterministic: grant geolocation on the context and set fixed coordinates, then assert the resolved location text. |
| `SET-05` | Personal access token lifecycle | Help and Settings | P0 | UI | UI + API | M | Build this early: the token it creates is the bootstrap credential for the entire API layer of the new suite. |
| `SET-07` | Skills lifecycle: create, edit, toggle, delete, export *(new)* | Help and Settings | P0 | UI | UI + API | M | MAJOR GAP: Skills is a shipped surface with a full CRUD backend module and zero coverage in the smoke suite. It should be a P0 block, not an afterthought. |
| `SHARE-01` | Recent task search works | Task Search and Share | P0 | UI | UI | S | Seed the searched task in the same run so the assertion does not depend on account history. |
| `SHARE-02` | Task can be shared | Task Search and Share | P0 | UI | UI | M | Open the copied URL in a brand-new browser context with no storage state. That is the only way to actually prove 'without login'. |
| `TASK-01` | Task runs on Cloudphone | Task Creation and Execution | P0 | UI | UI + API | M | Core end-to-end. Submit via UI, poll terminal state via API rather than watching the DOM; assert both HTTP 200 and body status == Success. |
| `TASK-02` | Task with image upload runs | Task Creation and Execution | P0 | UI | UI | M | set_input_files with a committed fixture image. Keep the fixture in the repo, never a machine-local path. |
| `TASK-03` | Follow-up works after task completion | Task Creation and Execution | P0 | UI | UI + API | M | Assert the follow-up shares the parent task id; do not just count message bubbles. |
| `TASK-04` | Model switch works | Task Creation and Execution | P0 | UI | UI + API | M | The 'uses the selected model' half is only provable via the API/task record. UI-only assertion is not enough. |
| `TASK-06` | Active task can be stopped | Task Creation and Execution | P0 | UI | UI + API | M | Confirm the backend state actually left EXECUTING; a UI badge alone can lie. |
| `TASK-08` | Task does not stall in WAITING_FOR_EXECUTION / WAITING_FOR_ANDROID_INSTANCE / EXECUTING beyond SLA *(rewritten)* | Task Creation and Execution | P0 | API | API | S | DEFECT IN SOURCE: row 16 of smoke.xlsx has no pre-req and no expected result, so it can neither pass nor fail. Rewritten here as a bounded-time state assertion. Per-state SLA values must be agreed with backend before coding. |
| `TASK-09` | Latest task shows in Recent | Task Creation and Execution | P0 | UI | UI + API | S |  |
| `TASK-10` | Task can be deleted from Recent | Task Creation and Execution | P0 | UI | UI + API | S | Verify deletion server-side too, so a UI-only list refresh cannot mask a failed delete. |
| `TASK-11` | Empty or whitespace-only prompt cannot be submitted *(new)* | Task Creation and Execution | P0 | UI | UI | S | GAP: no input-validation case exists. Cheap and catches composer regressions immediately. |
| `TASK-14` | Direct task URL opens the correct task *(new)* | Task Creation and Execution | P0 | UI | UI | S | GAP: deep-link routing is untested despite being how Linq intervention links land users in the app. |
| `AUTH-08` | Invalidated session forces re-authentication *(new)* | Authentication and App Bootstrap | P1 | UI + API | UI + API | S | GAP: no negative auth case exists anywhere in the suite. |
| `CP-02` | Cloudphone stays closed after user closes it | Cloud Phone and Remote View | P1 | UI | UI | S | Also assert the preference survives a reload. |
| `CP-04` | Cloudphone input works | Cloud Phone and Remote View | P1 | UI | UI | L | Assert the EFFECT, not the gesture: drive a known on-device action and verify the resulting device state. Verifying only that a click dispatched proves nothing. |
| `CP-06` | Cloudphone mute / unmute | Cloud Phone and Remote View | P1 | UI | UI | M | Assert the media element's muted/volume state and the audio track, not only the icon. 'Audio plays' is only provable via track state in a headless run. |
| `CP-09` | Cloudphone recovers from a stream interruption *(new)* | Cloud Phone and Remote View | P1 | UI | UI | M | GAP: no resiliency case anywhere in the suite. Playwright can simulate offline/online on the context, so this is cheap to automate. |
| `LINQ-03` | Connected status on Pilot | Linq (iMessage / RCS) | P1 | UI | UI + API | S | Fully automatable today against a pre-linked test account. |
| `MOB-01` | Cloudphone tap / input / navigation works | Mobile Browser | P1 | UI | UI | M | Playwright device descriptors with touch enabled. Note in the report that this is emulation, not a real device, so it will not catch true mobile-browser defects. |
| `MOB-03` | Cloudphone mute / unmute on mobile | Mobile Browser | P1 | UI | UI | S |  |
| `PAIR-05` | Device switching works before task submission | Receiver apk-Pilot pairing | P1 | UI | UI + API | M | Needs E6 (a second seeded device). Assert the executing device from the task record, not the picker label. |
| `PAIR-08` | Expired or invalid activation code is rejected *(new)* | Receiver apk-Pilot pairing | P1 | API | API | M | GAP: pairing is only tested on the happy path. |
| `PAIR-09` | Device can be unpaired and default falls back *(new)* | Receiver apk-Pilot pairing | P1 | UI | UI + API | M | GAP: the suite pairs devices but never removes one, so the cleanup path is untested and test accounts accumulate stale devices. |
| `PAIR-10` | Offline receiver is shown offline and is not selectable *(new)* | Receiver apk-Pilot pairing | P1 | UI | UI + API | M | GAP: no device-availability case exists. |
| `RTN-04` | Switch model on routine | Routines | P1 | UI | UI + API | M |  |
| `RTN-05` | Switch device on routine | Routines | P1 | UI | UI + API | M | Needs E6 for a non-Cloudphone target. |
| `RTN-10` | Routine history opens as task | Routines | P1 | UI | UI | S |  |
| `RTN-11` | Pre-defined routine setup | Routines | P1 | UI | UI + API | M | Template content changes; select by position or a stable template id, not by title text. |
| `RTN-15` | Custom schedule AI parse | Routines | P1 | UI | UI + API | M | Assert the generated recurrence rule and next-run timestamp via API. Asserting the human-readable label will flake as the model's phrasing drifts. |
| `RTN-18` | Routine run against an offline device behaves predictably *(new)* | Routines | P1 | UI | UI + API | M | GAP: the offline-device path is untested for routines. |
| `RTN-19` | Unparseable custom schedule is rejected clearly *(new)* | Routines | P1 | UI | UI + API | S | GAP: the AI parse case only covers a clean input. A silently persisted bad schedule is worse than a rejection. |
| `RTN-20` | Routine list survives reload and re-login *(new)* | Routines | P1 | UI | UI | S |  |
| `SET-06` | Short term & long term memory is generated | Help and Settings | P1 | UI | UI + API | M | Memory content is model-generated. Assert that entries exist, that an edit persists and that a delete removes it; never assert the text. |
| `SET-09` | Personalise settings persist *(new)* | Help and Settings | P1 | UI | UI | S | GAP: Personalise is a settings section with no coverage. |
| `SET-12` | Location permission denied is handled gracefully *(new)* | Help and Settings | P1 | UI | UI | S | GAP: only the granted path is covered. |
| `SHARE-03` | Invalid or revoked share link does not expose data *(new)* | Task Search and Share | P1 | UI | UI + API | M | GAP: sharing is tested positively only. This is the security-relevant half of a public, unauthenticated surface. |
| `SHARE-04` | Share page does not leak another account's task *(new)* | Task Search and Share | P1 | API | API | M | GAP: no cross-tenant isolation check exists in the suite. |
| `TASK-12` | Oversized or unsupported attachment is rejected clearly *(new)* | Task Creation and Execution | P1 | UI | UI + API | M | GAP: backend enforces a 50 MB body cap; nothing in the suite exercises the limit or the error surface. |
| `TASK-13` | Failed task shows a failed state with an actionable error *(new)* | Task Creation and Execution | P1 | UI | UI + API | M | GAP: the suite covers completion and stop but never the FAILED state. The failure path is what users actually hit on a bad release. |
| `CP-10` | Maintenance and terminal-state views render *(new)* | Cloud Phone and Remote View | P2 | UI | UI | M | GAP: these views are shipped components with no coverage. They are exactly what users see on a bad day. |
| `CP-11` | Remote view pane survives expand, collapse and resize *(new)* | Cloud Phone and Remote View | P2 | UI | UI | S |  |
| `SET-10` | Dark mode toggle applies and persists *(new)* | Help and Settings | P2 | UI | UI | S | GAP: cheap, and theme regressions are common and highly visible. |
| `TASK-15` | Second task on a busy device is queued or blocked with clear UI *(new)* | Task Creation and Execution | P2 | UI | UI + API | M | GAP: concurrency behaviour is referenced in the routine Run Now case but never tested directly. |

### Lane 3 · Nightly — 5 cases

| ID | Test Case | Scenario | Pri | Act | Assert | Effort | Automation Notes |
|---|---|---|---|---|---|---|---|
| `RTN-17` | Routine fires at the correct instant across timezones *(new)* | Routines | P0 | API | API | M | GAP: scheduling is the core of this feature and timezone correctness is never asserted. This is the single highest-value missing routine case. |
| `CP-08` | Cloudphone data is preserved | Cloud Phone and Remote View | P1 | UI | UI | L | Write a deterministic marker on the device (a file or an app state) and assert it after re-login instead of eyeballing the screen. |
| `RTN-08` | Scheduled execution at set time | Routines | P1 | API | API | L | Schedule ~3 minutes out and poll the task list by API. Time-bound: put this in the nightly lane, not the fast smoke lane. |
| `RTN-13` | Disabled routine does not auto-run | Routines | P1 | API | API | L | Time-bound negative test. Nightly lane. |
| `TASK-16` | Task list paging loads older tasks *(new)* | Task Creation and Execution | P2 | UI | UI | M | GAP: search is tested, listing at scale is not. |

## Automate after enablers

### Blocked · E1 — 1 cases

| ID | Test Case | Scenario | Pri | Act | Assert | Effort | Automation Notes |
|---|---|---|---|---|---|---|---|
| `AUTH-02` | Existing user sign in via MOBILE-NUMBER (IN / US / CN) | Authentication and App Bootstrap | P0 | UI | UI + API | M | BLOCKED on E1. No deterministic OTP today, so this P0 login path cannot run daily. Parametrise over the 3 country codes once a fixed test OTP exists. |

### Blocked · E1+E2 — 1 cases

| ID | Test Case | Scenario | Pri | Act | Assert | Effort | Automation Notes |
|---|---|---|---|---|---|---|---|
| `AUTH-04` | New user onboarding via MOBILE-NUMBER (IN / US / CN) | Authentication and App Bootstrap | P1 | UI | UI + API | L | BLOCKED on E1 and E2. |

### Blocked · E2 — 2 cases

| ID | Test Case | Scenario | Pri | Act | Assert | Effort | Automation Notes |
|---|---|---|---|---|---|---|---|
| `AUTH-03` | New user onboarding via EMAIL (google) | Authentication and App Bootstrap | P1 | UI | UI + API | L | BLOCKED on E2. Needs a fresh account per run plus teardown, otherwise it is a one-shot test that can never repeat. |
| `AUTH-09` | Waitlisted and banned account states render correctly *(new)* | Authentication and App Bootstrap | P1 | UI | UI + API | M | GAP: /waitlist and /banned are shipped routes with zero smoke coverage. Depends on E2 to hold accounts in those states. |

### Blocked · E2+E4 — 1 cases

| ID | Test Case | Scenario | Pri | Act | Assert | Effort | Automation Notes |
|---|---|---|---|---|---|---|---|
| `LINQ-01` | New account creation via DM | Linq (iMessage / RCS) | P0 | API | API | M | Needs E4 (webhook signing secret) plus E2 for teardown of the created account. |

### Blocked · E3 — 2 cases

| ID | Test Case | Scenario | Pri | Act | Assert | Effort | Automation Notes |
|---|---|---|---|---|---|---|---|
| `RTN-16` | Routine email notification | Routines | P1 | UI | Email | M | BLOCKED on E3. No mailbox automation exists. |
| `SET-03` | Support ticket email verification | Help and Settings | P1 | UI | Email | M | BLOCKED on E3. |

### Blocked · E4 — 14 cases

| ID | Test Case | Scenario | Pri | Act | Assert | Effort | Automation Notes |
|---|---|---|---|---|---|---|---|
| `LINQ-02` | Connect Messages from Pilot | Linq (iMessage / RCS) | P0 | UI + API | UI + API | M | Pilot half is automatable now; the inbound /link half needs E4. |
| `LINQ-05` | Task first message starts the task | Linq (iMessage / RCS) | P0 | API | API | M | Needs E4. |
| `LINQ-06` | Follow-up continues same task | Linq (iMessage / RCS) | P0 | API | API | M | Needs E4. Assert on task id, which is exact and non-flaky. |
| `LINQ-07` | /stop cancels an active task | Linq (iMessage / RCS) | P0 | API | API | S | Needs E4. |
| `LINQ-08` | /new creates a new task | Linq (iMessage / RCS) | P0 | API | API | S | Needs E4. |
| `LINQ-09` | Task completion message is received | Linq (iMessage / RCS) | P0 | API | API | M | Needs E4 plus a way to read outbound messages (provider sandbox or outbound store). |
| `LINQ-04` | Greeting response on first message | Linq (iMessage / RCS) | P1 | API | API | S | Needs E4. The 'no task is created' half is a clean API assertion. |
| `LINQ-10` | Attachments with text are allowed | Linq (iMessage / RCS) | P1 | API | API | M | Needs E4. Parametrise over the three file types. |
| `LINQ-11` | Group chats are not allowed | Linq (iMessage / RCS) | P1 | API | API | M | Needs E4 with a group-shaped webhook payload. |
| `LINQ-14` | Message queuing while task is executing | Linq (iMessage / RCS) | P1 | API | API | M | Needs E4. |
| `LINQ-15` | Location task asks for location via Messages | Linq (iMessage / RCS) | P1 | UI + API | UI + API | M | Needs E4; the Pilot half is automatable now. |
| `LINQ-18` | Unknown or unlinked sender is handled, never silently dropped *(new)* | Linq (iMessage / RCS) | P1 | API | API | M | GAP: only linked and fresh senders are covered. Needs E4. |
| `LINQ-20` | Duplicate webhook delivery is idempotent *(new)* | Linq (iMessage / RCS) | P1 | API | API | M | GAP: providers retry deliveries. Needs E4. |
| `LINQ-21` | Disconnect Messages from Pilot unlinks the sender *(new)* | Linq (iMessage / RCS) | P1 | UI + API | UI + API | M | GAP: connect is covered, disconnect is not. Pilot half is automatable now; the inbound half needs E4. |

### Blocked · E4+E8 — 1 cases

| ID | Test Case | Scenario | Pri | Act | Assert | Effort | Automation Notes |
|---|---|---|---|---|---|---|---|
| `LINQ-12` | Waiting for user intervention sends task link | Linq (iMessage / RCS) | P1 | API | API | M | Needs E4 and E8. |

### Blocked · E5 — 1 cases

| ID | Test Case | Scenario | Pri | Act | Assert | Effort | Automation Notes |
|---|---|---|---|---|---|---|---|
| `CP-07` | Cloudphone idle timeout | Cloud Phone and Remote View | P2 | UI | UI | L | A 15-minute wall-clock wait cannot sit in a daily smoke lane. Move to the nightly lane, or get a configurable idle timeout in QA (E5). |

### Blocked · E8 — 1 cases

| ID | Test Case | Scenario | Pri | Act | Assert | Effort | Automation Notes |
|---|---|---|---|---|---|---|---|
| `TASK-07` | Waiting-for-user-input state is actionable | Task Creation and Execution | P1 | UI | UI + API | L | BLOCKED on E8. Without a fixture prompt that reliably parks a task in WAITING_FOR_USER_INPUT this will flake daily. |

### Blocked · E10 — 1 cases

| ID | Test Case | Scenario | Pri | Act | Assert | Effort | Automation Notes |
|---|---|---|---|---|---|---|---|
| `SET-08` | Telegram connect, connected status and disconnect *(new)* | Help and Settings | P1 | UI + API | UI + API | M | GAP: Settings ships a Telegram panel and the backend has a Telegram module, but the smoke suite only covers iMessage/RCS. The Telegram Bot API makes the messaging half far more automatable than Linq. Needs E10. |

### Partial · split the case — 5 cases

| ID | Test Case | Scenario | Pri | Act | Assert | Effort | Automation Notes |
|---|---|---|---|---|---|---|---|
| `HID-09` | Clear error when dongle is disconnected | HID Dongle | P0 | UI + API | UI + API | M | The Pilot-side error surface is automatable by driving the receiver into a disconnected state through the API. Only the physical half needs the lab. |
| `SET-02` | Support ticket image and screenshot | Help and Settings | P1 | UI | UI | L | Image attach is trivial. In-app screenshot capture uses screen capture, which needs a Chromium auto-select flag and is brittle; split the case so the attach half can be automated now. |
| `CP-05` | Cloudphone copy / paste | Cloud Phone and Remote View | P2 | UI | UI | L | Needs clipboard-read and clipboard-write permissions. The copy-out direction is the hard half and may stay manual. |
| `SET-11` | Browser push notification for task completion *(new)* | Help and Settings | P2 | UI | UI | L | GAP: push messaging is bootstrapped in the app shell and untested. Push delivery assertions in headless Chromium are brittle. |
| `TASK-05` | Microphone input creates composer text | Task Creation and Execution | P2 | UI | UI | L | Feasible with Chromium fake-media flags and a committed WAV fixture. STT output is non-deterministic, so assert a non-empty transcript and successful submit, never exact wording. |

`Partial · split the case` means only part of the case is automatable — split it into an automated half and a manual half rather than leaving the whole thing manual.

## Enablers

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

