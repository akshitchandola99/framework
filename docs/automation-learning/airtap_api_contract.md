# Airtap API Contract

*A working reference for the Cortex HTTP API, written for QA and test automation.*

## Status of this document

Airtap has **no OpenAPI spec, no Swagger, and no API reference doc**. The API "contract" today
lives in three separate places in code:

| What | Where |
|---|---|
| Endpoint paths + auth rules | `cortex/src/<module>/<module>Routes.ts` |
| Request shapes | `class-validator` DTOs inside each handler |
| Response shapes | `pilot/lib/{tasks,receivers,routines,models}/types.ts` |

There is also `pilot/lib/api-contract.ts` — but that's a **runtime validation helper library**, not
a document. It gives the frontend functions like `requireNonEmptyString()` and produces errors
like `Task response contract mismatch at tasks[0].id: expected non-empty string.`

**This document fills that gap.** Build it out as you write your API test suite — you have to work
out these shapes anyway.

**Confidence markers used below:**

| Marker | Meaning |
|---|---|
| ✅ **Verified** | Read directly from source code |
| ⚠️ **Partial** | Endpoint confirmed; request/response fields not fully checked |
| ❓ **TBD** | Needs verification — fill in as you test |

---

# 1. Conventions

| | |
|---|---|
| **Base URL** | `https://qa1.airtap.ai` · also `qa2`, `dev1-4`, `prod` |
| **Route shape** | `/cortex/api/<module>/v1/<moduleAction>` |
| **Method** | **POST for everything**, including reads. Only exception found: `checkHealth` (GET) |
| **Content type** | `application/json` |
| **Max body size** | 50 MB → `413` if exceeded |

## ⚠️ Two conventions that will surprise you

**1. Reads use POST.** `taskGetDetails` and `taskGetList` are both POST. Don't assume "read = GET".

**2. Route domain ≠ module name** for two modules:

| Module | Route domain |
|---|---|
| `rcvr` | `/cortex/api/**receiver**/v1/...` |
| `rtn` | `/cortex/api/**routine**/v1/...` |

All others match (`task` → `/task`, `check` → `/check`).

## CORS

The backend has an explicit origin allow-list. Requests from an unlisted origin fail **in the
browser**, not server-side. Irrelevant for Python tests; relevant when debugging Pilot.

---

# 2. Response envelope ✅ Verified

Every response carries an app-level `status` **inside the body**, separate from the HTTP status
code.

```json
{
  "status": "Success",
  "message": "...",
  "taskId": "abc123"
}
```

Source: `AtSuccessResponse<T> = { status, message } & T` in `cortex/src/at/at.ts`.

## ⚠️ The single most important testing rule

**Always check both.** HTTP `200` with `"status": "Failure"` is possible.

```python
assert resp.status_code == 200
assert resp.json()["status"] == "Success"
```

## Status values ✅ Verified

From the `AtStatus` enum. The ones you'll actually meet:

| Value | Meaning | Typical HTTP |
|---|---|---|
| `Success` | Worked | 200 |
| `Pending` / `Processing` | Accepted, still working | 200 |
| `Failure` | Generic failure | 409 |
| `FailureValidationError` | Bad or missing fields | 400 |
| `Unauthorized` / `FailureUnauthorized` | Not authenticated | 401 |
| `FailureInvalidToken` | Token malformed | 401 |
| `FailureTokenExpired` | Token expired | 401 |
| `FailureForbidden` | Valid token, wrong scope | 403 |
| `FailureNotFound` | No such resource | 404 |
| `FailureNoResource` | Resource unavailable | 409 |
| `FailureAlreadyExists` | Duplicate | 409 |
| `FailureActiveTaskExists` | User already has an active task | 409 |
| `FailureInvalidParameter` | Bad parameter value | 400 |
| `FailureInvalidState` | Wrong state for this action | 409 |
| `FailureTryAgain` | Transient — retry | 409 |
| `FailureUnderMaintenance` | Backend in maintenance | 409 |
| `FailureMaxBodySizeExceeded` | Body too large | 413 |

*(The full enum has ~40 values, many for cloud-phone/orch flows you won't hit in API tests.)*

## HTTP error mapping ✅ Verified

| Condition | HTTP |
|---|---|
| Validation error | 400 |
| Unauthorized | 401 |
| Server exception | 500 |
| Body too large | 413 |
| Everything else | 409 |

---

# 3. Authentication ✅ Verified

## Header

```
Authorization: Bearer at-pat-xxxxxxxxxxxx
```

## Token type

Airtap PATs are **opaque tokens sent as Bearer credentials — not JWTs**.

| | |
|---|---|
| Format | `at-pat-` prefix + random string (nanoid) |
| Contents | Nothing — you cannot decode it |
| Stored as | SHA-256 hash (the raw token is shown once, at creation) |
| Revocation | Instant — delete the record |

Source: `cortex/src/user/userPersonalAccessToken.ts`

**Implication for tests:** a 401 means the server's lookup failed (revoked / wrong environment /
typo), **not** a signature or expiry problem. You can't decode it to inspect expiry.

## Second gate: account admission

A valid token is not enough. Accounts carry a state: `WAITLISTED` / `ADMITTED` / `BANNED`. A new
account is `WAITLISTED` and **cannot create tasks**.

> **If a fresh test account is rejected on everything, check admission status before debugging your
> auth code.** This is the most common false alarm when setting up an API suite.

## Version header

Some routes check `x-airtap-pilot-version` and reject mismatches with `FailurePilotVersionConflict`.
Mostly affects stale browser tabs after a deploy.

---

# 4. Endpoints — `check` ✅ Verified

## `GET /cortex/api/check/v1/checkHealth`

**Auth:** none. **Use this as your suite's first smoke test.**

```json
{ "status": "Success" }
```

## `GET /cortex/api/check/v1/checkResourceUsage`

**Auth:** required. ⚠️ Response shape ❓ TBD.

---

# 5. Endpoints — `task` ✅ Paths verified

All at `/cortex/api/task/v1/...`, all **POST**, all **auth required**.

| Endpoint | Purpose |
|---|---|
| `taskCreate` | Create a task |
| `taskGetDetails` | Read one task |
| `taskGetList` | List tasks |
| `taskCancel` | Cancel a running task |
| `taskDelete` | Delete a task |
| `taskAddUserMessage` | Send a message (resumes a waiting task) |
| `taskQueueUserMessage` | Queue a message while the task is running |
| `taskGetModelDebug` | Raw LLM call data (needs `debug:access`) |
| `taskCreateShare` | Create a share link |
| `taskGetShare` | Read a shared task |
| `taskExtractFromAudio` | Transcribe audio into a task prompt |

---

## `POST /cortex/api/task/v1/taskCreate` ✅ Verified

Creates a task and returns immediately. **The task has not run yet** — see §9 on polling.

### Request

| Field | Type | Required | Rules |
|---|---|---|---|
| `userMessage` | object | ✅ | The user's request (nested object) |
| `receiverId` | string | ✅ | `"cloud"` or a paired device ID |
| `modelId` | string | — | Defaults to the configured model |
| `cancelAfterSteps` | integer | — | **Minimum 1.** Stops the task after N agent steps |
| `timeZone` | string | — | IANA zone, validated (e.g. `Asia/Kolkata`) |

```json
{
  "userMessage": { "text": "what is 2 plus 2?" },
  "receiverId": "cloud",
  "cancelAfterSteps": 5
}
```

> 💡 **`cancelAfterSteps` is your cost-control lever.** Every task run costs real LLM money and
> minutes. For tests that only need to confirm a task *starts and progresses*, cap the steps.

### Response — 200 ✅ Verified

```json
{
  "status": "Success",
  "message": "...",
  "taskId": "abc123"
}
```

| Field | Type | Always? |
|---|---|---|
| `status` | string | ✅ |
| `message` | string | ✅ |
| `taskId` | string | ✅ on success |

### Errors

| Condition | HTTP | `status` |
|---|---|---|
| Missing `userMessage` or `receiverId` | 400 | `FailureValidationError` |
| `cancelAfterSteps` < 1 | 400 | `FailureValidationError` |
| Invalid `timeZone` | 400 | `FailureValidationError` |
| No / invalid token | 401 | `Unauthorized` |
| Waitlisted account | 403 | ❓ TBD |
| Unknown `receiverId` | ❓ | ❓ TBD |

### Behaviours worth knowing

- **Undeclared extra fields are silently dropped**, not rejected.
- A second task while one is active is expected to **queue**, not fail. (`FailureActiveTaskExists`
  exists in the enum — worth confirming which actually happens. ❓)
- `modelId` requires `debug:access` permission for debug-only models.

---

## `POST /cortex/api/task/v1/taskGetDetails` ✅ Request verified

### Request

| Field | Type | Required | Notes |
|---|---|---|---|
| `taskId` | string | ✅ | |
| `debug` | boolean | — | Silently ignored without `debug:access` |

### Response — 200 ⚠️ Partial

Confirmed present via `pilot/lib/tasks/types.ts` (`TaskSummary`):

| Field | Type | Notes |
|---|---|---|
| `status` | string | Envelope |
| `id` / `taskId` | string | ❓ confirm which key the API returns |
| `state` | enum | See §8 |
| `title` | string | |
| `createdAt` | date | Nullable |
| `updatedAt` | date | Nullable |
| `routineId` | string | Null unless spawned by a routine |
| `stopReason` | string | Nullable |
| `userTextParts` | string[] | |

Full message/step content: ❓ TBD — read `taskGetDetailsCore.ts` or capture a live response.

### Errors

| Condition | HTTP | `status` |
|---|---|---|
| Missing `taskId` | 400 | `FailureValidationError` |
| Unknown `taskId` | ❓ | `FailureNotFound` |
| **Another user's task** | ❓ | `FailureForbidden` (unless `task:view-any`) |

> 🔒 That last row is a **security test**, not a functional one. Write it early.

---

## `POST /cortex/api/task/v1/taskGetList` ⚠️ Partial

### Response ⚠️

From `TaskListResult` in `pilot/lib/tasks/types.ts`:

| Field | Type |
|---|---|
| `activeTaskId` | string \| null |
| `tasks` | array of `TaskSummary` |

Request filters/pagination: ❓ TBD.

---

## `POST /cortex/api/task/v1/taskCancel` ⚠️ Partial

Request: `{ "taskId": "abc123" }` ❓ confirm.
Expected effect: task reaches `CANCELLED`.

Worth testing at **each** state — cancelling a queued task vs. a running one vs. an already-finished
one may behave differently (`FailureInvalidState`).

---

# 6. Endpoints — `receiver` ✅ Paths + auth verified

At `/cortex/api/**receiver**/v1/...` — note the domain differs from the module name.

| Endpoint | Auth | Purpose |
|---|---|---|
| `rcvrGetList` | ✅ Required | List paired devices |
| `rcvrGetPairingCode` | ✅ Required | Generate a pairing code |
| `rcvrAddReceiver` | ❌ **None** | Device redeems a pairing code |
| `rcvrGetLatestApkUrl` | ❌ **None** | Android APK download URL |
| `rcvrCreateTicket` | ❌ **None** | Support ticket from a device |
| `rcvrStartWebrtc` | ✅ Required | Cloud phone video — SDP offer |
| `rcvrSetAnswerSdp` | ✅ Required | Cloud phone video — SDP answer |

> 🔒 **Three unauthenticated endpoints.** Good abuse/rate-limit test targets — and
> `rcvrGetLatestApkUrl` is a useful second smoke test since it needs no auth.

Request/response shapes: ❓ TBD.

---

# 7. Endpoints — `routine` ✅ Paths verified

At `/cortex/api/**routine**/v1/...`, all POST.

| Endpoint | Purpose |
|---|---|
| `rtnCreate` | Create a routine |
| `rtnGetList` | List routines |
| `rtnUpdate` | Update a routine |
| `rtnDelete` | Delete a routine |
| `rtnRunNow` | Trigger immediately |
| **`rtnGenerateRRule`** | **Natural language → RRULE** |
| `rtnGetMemory` / `rtnUpdateMemory` / `rtnDeleteMemory` | Routine-scoped memory |

## `rtnGenerateRRule` — your highest-value first test target

Converts free text into an iCalendar recurrence rule.

```
"Every weekday at 8:30 AM"
   → RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=8;BYMINUTE=30
```

**`pilot/manual-custom-routine-rrule-ai-test-cases.md` already contains 129 rows** of prompts and
expected RRULEs, plus an invalid-prompts section. That file is a ready-made parametrized test suite.

Request/response shape: ❓ TBD — confirm the field names before writing the suite.

---

# 8. Enums

## `taskState` ✅ Verified

| State | Terminal? | Meaning |
|---|---|---|
| `QUEUED` | No | Waiting behind another active task |
| `WAITING_FOR_EXECUTION` | No | Ready, waiting for a worker |
| `WAITING_FOR_USER_INPUT` | No | Agent asked a clarifying question |
| `WAITING_FOR_USER_INTERVENTION` | No | Agent needs the user to act (e.g. a login wall) |
| `COMPLETED` | ✅ | Finished successfully |
| `FAILED` | ✅ | Ended with an error |
| `CANCELLED` | ✅ | Cancelled by the user |
| `STOPPED` | ✅ | Hit a limit (e.g. `cancelAfterSteps`) |

```python
TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED", "STOPPED"}
```

## `receiverType` ✅ Verified

| Value | Meaning |
|---|---|
| `cloud` | Ephemeral cloud Android VM — **use this for automation** |
| `physical` | Android via Accessibility Service |
| `androidDongle` | Android via HID dongle |
| `iosDongle` | iPhone via HID dongle |

## Permissions seen ✅ Verified

`debug:access` · `task:view-any` · `admin:view` · `dashboard:view` · `eval:access` ·
`cloud:keepalive` · `user:delete`

---

# 9. Async behaviour — critical for tests

`taskCreate` returns immediately. The agent then works through the task in the background, one step
at a time — seconds to minutes.

```
taskCreate  →  200 { taskId }        (task has NOT run)
                    ↓
              QUEUED / WAITING_FOR_EXECUTION
                    ↓  (agent loop, N steps)
              COMPLETED / FAILED / CANCELLED / STOPPED
```

**So this is wrong:**

```python
task_id = create()["taskId"]
assert get_details(task_id)["taskState"] == "COMPLETED"   # ❌ still QUEUED
```

**Poll instead** — and poll for *any* terminal state, not just `COMPLETED`:

```python
def wait_for_task(client, task_id, timeout=180, interval=3):
    deadline = time.time() + timeout
    while time.time() < deadline:
        details = client.get_details(task_id).json()
        if details["taskState"] in TERMINAL_STATES:
            return details
        time.sleep(interval)
    raise TaskTimeoutError(f"{task_id} still {details['taskState']} after {timeout}s")
```

Waiting only for `COMPLETED` means a task that **fails in 2 seconds** still burns the full 3-minute
timeout before your test reports anything.

---

# 10. What contract testing is, and what to test here

## The distinction

Contract testing checks the API's **shape** — not whether the feature works.

| | Question it answers |
|---|---|
| **Functional test** | "Did creating a task actually create a task?" |
| **Contract test** | "Did the response return `taskId` as a string, `taskState` as a known enum value, and reject a missing `receiverId` with a 400?" |

You're testing the **agreement between frontend and backend**. A silent backend change — a renamed
field, a new enum value, a type change from int to string — fails a test instead of breaking Pilot
in production.

## Why this matters for Airtap specifically

There is no OpenAPI spec. The frontend simply **trusts the backend's shape at runtime** —
`pilot/lib/api-contract.ts` throws when a response is wrong, but only once a real user hits it.

**Contract tests move that failure from production to CI.**

## What to test, mapped to this document

| # | Test | Section |
|---|---|---|
| 1 | **Both statuses** — HTTP 200 *and* body `status == "Success"` | §2 |
| 2 | **Required response fields exist** — `taskCreate` always returns `taskId` as a string | §5 |
| 3 | **Enum is closed** — `taskState` is one of the 8 known values | §8 |
| 4 | **Types don't drift** — `routineId` is string-or-null, `createdAt` parses as a date | §5, §10 |
| 5 | **Missing required fields rejected** — no `userMessage` → 400 + `FailureValidationError` | §5 |
| 6 | **Boundaries rejected** — `cancelAfterSteps: 0` → 400 (minimum is 1) | §5 |
| 7 | **No auth → 401** on every authenticated endpoint | §3 |
| 8 | **Extra fields ignored, not rejected** — confirm this documented behaviour stays true | §5 |

## The highest-value one

**#3 — the closed enum.** If the backend adds a new `taskState`, a JSON Schema with a fixed `enum`
list fails loudly. Without it, your tests keep passing while Pilot renders a blank status to real
users.

That single check is the clearest argument for turning this document into schemas — which is
exactly what the next section does.

---

# 11. Making this executable

A document drifts. A schema fails a test. Convert each response table into a JSON Schema:

```python
# schemas/task_schemas.py
TASK_DETAILS_SCHEMA = {
    "type": "object",
    "required": ["status", "taskState"],
    "properties": {
        "status":    {"type": "string"},
        "taskState": {"type": "string", "enum": [
            "QUEUED", "WAITING_FOR_EXECUTION",
            "WAITING_FOR_USER_INPUT", "WAITING_FOR_USER_INTERVENTION",
            "COMPLETED", "FAILED", "CANCELLED", "STOPPED",
        ]},
        "title":     {"type": "string"},
        "routineId": {"type": ["string", "null"]},
    },
}
```

```python
from jsonschema import validate

def test_task_details_shape(task_client, existing_task):
    body = assert_success(task_client.get_details(existing_task))
    validate(instance=body, schema=TASK_DETAILS_SCHEMA)
```

**The `enum` is the valuable part.** If the backend adds a new task state, this test fails loudly
instead of silently passing — which is exactly the contract-drift protection this document exists
to give you.

---

# 12. Verification checklist

Fill these in as you build the suite. Each ❓ above becomes a ✅ here.

**Task domain**
- [ ] Capture a real `taskGetDetails` response and document every field
- [ ] Confirm the ID key name (`id` vs `taskId`)
- [ ] Confirm `taskGetList` request options (filters? pagination?)
- [ ] Confirm what happens on a second concurrent task — queue or `FailureActiveTaskExists`?
- [ ] Confirm `taskCancel` behaviour from each state
- [ ] Confirm the exact HTTP code + status for another user's task

**Receiver domain**
- [ ] Document `rcvrGetList` response
- [ ] Document `rcvrGetPairingCode` request/response
- [ ] Rate-limit test the three unauthenticated endpoints

**Routine domain**
- [ ] Document `rtnGenerateRRule` request/response — then convert the 129 manual cases
- [ ] Document `rtnCreate` required fields

**Cross-cutting**
- [ ] Confirm the waitlisted-account rejection code
- [ ] Confirm behaviour at the 50 MB body limit
- [ ] Write a JSON schema for every documented response

---

# 13. Keeping this alive

| Practice | Why |
|---|---|
| Store it **next to the tests** (e.g. `api-automation/API_CONTRACT.md`) | It rots if it lives away from the code that uses it |
| Update it in the **same PR** as a test change | Never a separate "docs" task |
| Back every response with a **JSON schema** | The doc becomes executable |
| Note the **date + branch** you verified against | Confidence decays; readers should know how old it is |

**Last verified:** against `kepler-v1.7.25_at-1512`, reading `taskRoutes.ts`,
`taskCreateHandler.ts`, `taskGetDetailsHandler.ts`, `rcvrRoutes.ts`, `rtnRoutes.ts`, `at/at.ts`,
`userPersonalAccessToken.ts`, and `pilot/lib/tasks/types.ts`.
