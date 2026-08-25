# Track 3 — API Automation

*Deep-dive for Track 3 of [00_master_study_plan.md](00_master_study_plan.md). Topics are in
learning order. Assumes [Track 1](track_01_python_for_automation.md) (classes, exceptions,
dicts) and [Track 2](track_02_pytest.md) (fixtures, parametrize).*

## What is API testing?

An **API** is how one program talks to another. When you click "Create task" in Pilot, the browser
doesn't do the work — it sends a message to Airtap's backend, and the backend replies.

**API testing means skipping the browser and sending those messages yourself.**

| | UI test | API test |
|---|---|---|
| Speed | Seconds | Milliseconds |
| Stability | Breaks when a button moves | Breaks only when the contract changes |
| What it checks | What the user sees | What the system actually does |
| Setup cost | Browser, waits, locators | An HTTP call |

**Why this track is weighted heaviest:** API tests catch more bugs, run far faster, and break far
less often than UI tests. Most QA engineers over-invest in UI automation because it's visual. Going
deep here is the fastest way to become genuinely useful — and it's what hiring managers ask about.

**Airtap status:** there is **no API test suite yet**. This is a greenfield build, and it's the
highest-value thing you can add.

## Topic table

| # | Topic | Priority | Notes |
|---|---|---|---|
| 1 | HTTP methods, status codes, headers, body | 🔴 P0 | The vocabulary. Understand *why*, not memorised numbers. |
| 2 | `requests` + `Session` | 🔴 P0 | Your main tool. |
| 3 | Auth: API keys, Bearer, JWT | 🔴 P0 | Early — you can't call a real Airtap endpoint without it. |
| 4 | Response validation beyond status code | 🔴 P0 | "It returned 200" is not a test. |
| 5 | JSON Schema validation | 🔴 P0 | "It's JSON" vs "it's the *right* JSON". |
| 6 | Framework structure | 🔴 P0 | Structure before the suite grows. |
| 7 | Negative & edge cases | 🔴 P0 | Where API testing earns its value. |
| 8 | Test data: `Faker`, factories | 🟠 P1 | Stop hardcoding dicts. |
| 9 | API chaining | 🟠 P1 | Output of one call feeds the next. |
| 10 | Retry logic & rate limits | 🟠 P1 | |
| 11 | **Async polling for job APIs** | 🔴 P0 | Critical for Airtap — tasks finish asynchronously. |
| 12 | Mocking | 🟡 P2 | Test your code without the real API. |
| 13 | `httpx` + async | 🟡 P2 | Needs Track 1 #14. |
| 14 | OAuth2 flows | 🟡 P2 | Know it conceptually. |
| 15 | Contract testing | 🟢 P3 | Awareness only. |

---

# 1. HTTP basics 🔴

## The four parts of a request

Every API call has the same four pieces:

```
POST  https://qa1.airtap.ai/cortex/api/task/v1/taskCreate     ← method + URL
Authorization: Bearer at-pat-xxxxx                             ← headers
Content-Type: application/json

{"receiverId": "cloud", "userMessage": {...}}                  ← body
```

## Methods — what you're trying to do

| Method | Meaning | Example |
|---|---|---|
| `GET` | Read something | Get a list of tasks |
| `POST` | Create something | Create a new task |
| `PUT` | Replace something entirely | Replace a whole routine |
| `PATCH` | Update part of something | Change just a routine's time |
| `DELETE` | Remove something | Delete a task |

## ⚠️ Airtap is different — almost everything is POST

Airtap uses `POST` for **reads too**. Real examples:

```
POST /cortex/api/task/v1/taskGetDetails     ← reading, but still POST
POST /cortex/api/task/v1/taskGetList        ← reading, but still POST
POST /cortex/api/task/v1/taskCreate
POST /cortex/api/task/v1/taskCancel
```

The only `GET` endpoints found are the health checks:

```
GET /cortex/api/check/v1/checkHealth
```

**Why it matters for you:** don't assume "read = GET". When writing Airtap tests, check the actual
route. Sending `GET` to `taskGetDetails` will just fail.

## Status codes — what happened

Learn the **families**, not individual numbers:

| Family | Meaning | Plain English |
|---|---|---|
| **2xx** | Success | It worked |
| **3xx** | Redirect | Look somewhere else |
| **4xx** | **Your** fault | You sent something wrong |
| **5xx** | **Server's** fault | Their code broke |

The 4xx/5xx split is the important one. **4xx means fix your request. 5xx means the backend has a
bug.** If a test gets a 500, that's usually a real defect worth raising, not a bad test.

Most-used specifics:

| Code | Meaning |
|---|---|
| 200 | OK |
| 201 | Created |
| 400 | Bad request (malformed/missing fields) |
| 401 | Not authenticated (no/bad token) |
| 403 | Authenticated, but not allowed |
| 404 | Not found |
| 409 | Conflict |
| 413 | Body too large |
| 429 | Too many requests (rate limited) |
| 500 | Server error |

## Airtap's real code mapping

From the docs research, Airtap maps errors like this:

| Situation | HTTP code |
|---|---|
| Validation failed | 400 |
| Unauthorized | 401 |
| Version conflict / general failure | 409 |
| Body over 50MB | 413 |
| Server exception | 500 |

## Query params vs path params vs body

```
/tasks/abc123              ← path param: identifies WHICH thing
/tasks?state=COMPLETED     ← query param: filters/options
{"taskId": "abc123"}       ← body: the data you're sending
```

Airtap mostly uses **the body** — because everything is POST, the IDs go in the JSON body rather
than the URL.

## Headers you'll actually use

| Header | Purpose |
|---|---|
| `Authorization` | Who you are |
| `Content-Type: application/json` | "My body is JSON" |
| `Accept` | "Send me JSON back" |
| `x-airtap-pilot-version` | Airtap-specific — version check on some routes |

---

# 2. `requests` and `Session` 🔴

## Install

```bash
pip install requests
```

## Your first call

```python
import requests

resp = requests.get("https://qa1.airtap.ai/cortex/api/check/v1/checkHealth")

print(resp.status_code)     # 200
print(resp.text)            # raw text
print(resp.json())          # parsed into a Python dict
```

`resp.json()` is the one you'll use most — it turns the JSON reply into a normal Python dict
(Track 1 #3).

## Sending data

```python
resp = requests.post(
    "https://qa1.airtap.ai/cortex/api/task/v1/taskGetDetails",
    json={"taskId": "abc123"},                      # `json=` sets Content-Type for you
    headers={"Authorization": "Bearer at-pat-xxx"},
    timeout=30,
)
```

**Always pass `timeout`.** Without it, a hung server hangs your test forever. There's no default.

## `json=` vs `data=`

```python
requests.post(url, json={"taskId": "abc"})    # ✅ auto-converts to JSON + sets header
requests.post(url, data={"taskId": "abc"})    # ❌ sends form-encoded, not JSON
```

Use `json=` for JSON APIs. This trips people up constantly.

## Session — reuse settings across calls

Without a session, you repeat the auth header on every single call:

```python
requests.post(url1, headers={"Authorization": token}, timeout=30)
requests.post(url2, headers={"Authorization": token}, timeout=30)
requests.post(url3, headers={"Authorization": token}, timeout=30)
```

With a session, you set it once:

```python
session = requests.Session()
session.headers.update({"Authorization": "Bearer at-pat-xxx"})

session.post(url1, json={...})     # header sent automatically
session.post(url2, json={...})     # and here
```

**Two benefits:**
1. Shared headers and cookies — set once
2. **Connection reuse** — the TCP connection stays open, so later calls are measurably faster

This is why your API client class (topic #6) will wrap a `Session`.

## Reading the response

```python
resp.status_code      # 200
resp.json()           # parsed dict
resp.text             # raw string
resp.headers          # response headers
resp.elapsed          # how long it took — useful for latency assertions
resp.ok               # True if status < 400
```

## The `.json()` trap

If the server returns HTML (a crash page, a proxy error), `.json()` raises a confusing error:

```python
try:
    data = resp.json()
except ValueError:
    pytest.fail(f"Expected JSON, got: {resp.text[:200]}")
```

That message tells you what actually came back. Much better than a bare `JSONDecodeError`.

---

# 3. Authentication 🔴

## The three you'll meet

| Type | Looks like | Where |
|---|---|---|
| **API key** | `X-API-Key: abc123` | Simple internal services |
| **Bearer token** | `Authorization: Bearer eyJhbGc...` | Most modern APIs |
| **JWT** | A Bearer token with structure | Very common |

## Bearer — the standard shape

```python
headers = {"Authorization": f"Bearer {token}"}
```

The word `Bearer`, a space, then the token. That's it.

## What a JWT is

A JWT (JSON Web Token) is a Bearer token in three parts separated by dots:

```
eyJhbGciOiJIUzI1NiJ9.eyJ1c2VySWQiOiIxMjMiLCJleHAiOjE3MzB9.abc123signature
     header                      payload                      signature
```

The middle part is **readable** — it's just base64-encoded JSON. You can decode it to see when the
token expires:

```python
import base64, json

payload = token.split(".")[1]
payload += "=" * (-len(payload) % 4)          # fix padding
print(json.loads(base64.b64decode(payload)))  # {'userId': '123', 'exp': 1730...}
```

Useful when debugging "why did my test suddenly get 401?" — check `exp`.

**Note:** JWTs are *signed*, not encrypted. Never assume the contents are secret.

## Airtap: use a Personal Access Token

Airtap supports two credentials:
- A **session token** — what the browser uses after login
- A **Personal Access Token (PAT)** — prefixed `at-pat-`, designed exactly for automation and CI

**Use a PAT.** It's the supported credential for scripted runs and doesn't expire mid-suite the way
a session might.

```python
session.headers.update({"Authorization": f"Bearer {os.environ['AIRTAP_PAT']}"})
```

## Never hardcode secrets

```python
TOKEN = "at-pat-abc123..."                    # ❌ ends up in git forever
TOKEN = os.environ["AIRTAP_PAT"]              # ✅ from the environment
```

Read from environment variables, and add any `.env` file to `.gitignore`.

## Airtap has a second gate

Even with a perfectly valid token, a request can still be rejected. Accounts have an admission
state: `WAITLISTED` / `ADMITTED` / `BANNED`. A brand-new test account is `WAITLISTED` and **cannot
create tasks** until admitted.

**If a fresh test account gets rejected on everything, check admission status before debugging your
auth code.** This is the most common false alarm when setting up a new API suite here.

---

# 4. Response validation beyond status code 🔴

## The mistake

```python
def test_get_task():
    resp = session.post(url, json={"taskId": task_id})
    assert resp.status_code == 200        # ❌ this is not a test
```

A 200 means "the server replied." It doesn't mean the reply was **correct**. An API can return 200
with an empty body, wrong fields, or a null where data should be.

## What to actually check

```python
def test_get_task():
    resp = session.post(url, json={"taskId": task_id})

    assert resp.status_code == 200                    # 1. transport worked
    body = resp.json()
    assert body["status"] == "Success"                # 2. app-level result
    assert body["taskId"] == task_id                  # 3. correct data
    assert body["taskState"] in VALID_STATES          # 4. sensible value
```

## ⚠️ The most important Airtap-specific point

**Airtap replies have their own `status` field inside the body, separate from the HTTP status
code.** Every response follows this shape:

```json
{
  "status": "Success",
  "message": "...",
  "taskId": "abc123"
}
```

The real `status` values (from `at/at.ts`) include:

```
Success, Pending, Failure, Unauthorized,
FailureValidationError, FailureTryAgain, FailureNotFound,
FailureActiveTaskExists, FailureTokenExpired, FailureInvalidToken,
FailureUnderMaintenance, FailureForbidden, ...
```

**This means checking `resp.status_code == 200` alone can miss a failure entirely.** Always check
both:

```python
assert resp.status_code == 200
assert resp.json()["status"] == "Success"
```

Write a helper so you never forget:

```python
def assert_success(resp):
    assert resp.status_code == 200, f"HTTP {resp.status_code}: {resp.text[:200]}"
    body = resp.json()
    assert body["status"] == "Success", f"App status: {body['status']} — {body.get('message')}"
    return body
```

Now every test is one line:

```python
body = assert_success(session.post(url, json={"taskId": task_id}))
```

## Levels of checking

| Level | Checks | Example |
|---|---|---|
| 1 | HTTP code | `status_code == 200` |
| 2 | App status | `body["status"] == "Success"` |
| 3 | Field presence | `"taskId" in body` |
| 4 | Field types | `isinstance(body["taskId"], str)` |
| 5 | Field values | `body["taskId"] == expected_id` |
| 6 | Whole shape | JSON Schema (topic #5) |

## Don't over-assert

```python
assert body["createdAt"] == "2026-08-07T10:32:11.123Z"    # ❌ breaks every run
assert "createdAt" in body                                 # ✅ it exists
```

Assert on things that should be stable. Timestamps, generated IDs, and durations change every run —
check they're *present and sensible*, not exact.

---

# 5. JSON Schema validation 🔴

## The problem

Checking fields one by one gets long fast:

```python
assert "taskId" in body
assert isinstance(body["taskId"], str)
assert "status" in body
assert isinstance(body["status"], str)
assert "createdAt" in body
# ...20 more lines
```

## The fix: describe the shape once

```bash
pip install jsonschema
```

```python
from jsonschema import validate

TASK_SCHEMA = {
    "type": "object",
    "required": ["status", "taskId", "taskState"],
    "properties": {
        "status":    {"type": "string"},
        "taskId":    {"type": "string"},
        "taskState": {"type": "string", "enum": [
            "QUEUED", "WAITING_FOR_EXECUTION", "COMPLETED", "FAILED",
            "CANCELLED", "STOPPED",
            "WAITING_FOR_USER_INPUT", "WAITING_FOR_USER_INTERVENTION",
        ]},
        "stepCount": {"type": "integer", "minimum": 0},
    },
}

def test_task_details_shape():
    body = assert_success(session.post(url, json={"taskId": task_id}))
    validate(instance=body, schema=TASK_SCHEMA)      # one line, whole shape
```

Those task states are the real ones used by Airtap.

## What schema validation catches that manual checks miss

- A field that changed type (`stepCount` became a string)
- A field that disappeared in a backend refactor
- A new state value the backend started returning that your tests don't know about

That last one is genuinely valuable — the `enum` fails loudly if the backend adds a state, instead
of silently passing.

## The alternative: Pydantic

```bash
pip install pydantic
```

```python
from pydantic import BaseModel

class TaskDetails(BaseModel):
    status: str
    taskId: str
    taskState: str
    stepCount: int = 0

def test_task_details():
    body = assert_success(session.post(url, json={"taskId": task_id}))
    task = TaskDetails(**body)          # raises if the shape is wrong
    assert task.taskState == "COMPLETED"
```

**Bonus:** now you get autocomplete — `task.taskState` instead of `body["taskState"]`, and typos
fail immediately.

| | jsonschema | Pydantic |
|---|---|---|
| Style | A dict describing the shape | A Python class |
| Best for | Validating raw API responses | When you also want typed objects to work with |
| Ties back to | — | Track 1 #11 (dataclasses) — same idea, plus validation |

Either is fine. Pick one and be consistent.

---

# 6. Framework structure 🔴

**This is what separates "some scripts" from "a framework"** — and it's what AI-generated code
usually gets wrong. Do this early, before the suite grows.

## The problem

```python
def test_one():
    resp = requests.post(
        "https://qa1.airtap.ai/cortex/api/task/v1/taskGetList",     # repeated URL
        headers={"Authorization": "Bearer at-pat-abc"},              # repeated + hardcoded!
        json={},
        timeout=30,
    )
```

Change environment, and you edit 50 files.

## Target layout

```
api-automation/
├── pytest.ini
├── requirements.txt
├── config/
│   └── settings.py          ← base URLs, tokens (from env vars)
├── api_clients/
│   ├── __init__.py
│   ├── base_client.py       ← session, auth, common request logic
│   └── task_client.py       ← taskCreate, taskGetDetails, ...
├── schemas/
│   └── task_schemas.py
└── tests/
    ├── conftest.py          ← fixtures
    └── test_tasks.py
```

(That's the module vs package idea — `api_clients/` is a package with an `__init__.py`, exactly
like `pages/` in `web-automation/`.)

## Step 1: config from environment

```python
# config/settings.py
import os

ENVIRONMENTS = {
    "qa1": "https://qa1.airtap.ai",
    "qa2": "https://qa2.airtap.ai",
}

ENV = os.getenv("AIRTAP_ENV", "qa1")
BASE_URL = ENVIRONMENTS[ENV]
PAT = os.environ["AIRTAP_PAT"]          # crashes loudly if missing — good
```

Switching environment becomes:

```bash
AIRTAP_ENV=qa2 pytest
```

## Step 2: the base client

```python
# api_clients/base_client.py
import requests
from config.settings import BASE_URL, PAT


class BaseClient:
    def __init__(self, base_url=BASE_URL, token=PAT, timeout=30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        })

    def post(self, endpoint, payload=None):
        url = f"{self.base_url}{endpoint}"
        return self.session.post(url, json=payload or {}, timeout=self.timeout)

    def get(self, endpoint):
        return self.session.get(f"{self.base_url}{endpoint}", timeout=self.timeout)

    def close(self):
        self.session.close()
```

Everything shared lives in one place: base URL, auth, timeout, content type.

## Step 3: one client per API area

```python
# api_clients/task_client.py
from api_clients.base_client import BaseClient


class TaskClient(BaseClient):                  # inheritance — Track 1 #6
    def create(self, user_message, receiver_id="cloud", **extra):
        return self.post("/cortex/api/task/v1/taskCreate", {
            "userMessage": user_message,
            "receiverId": receiver_id,
            **extra,
        })

    def get_details(self, task_id, debug=False):
        return self.post("/cortex/api/task/v1/taskGetDetails",
                         {"taskId": task_id, "debug": debug})

    def get_list(self):
        return self.post("/cortex/api/task/v1/taskGetList", {})

    def cancel(self, task_id):
        return self.post("/cortex/api/task/v1/taskCancel", {"taskId": task_id})
```

Those endpoint paths and field names are the real ones from `taskRoutes.ts` and
`taskCreateHandler.ts`.

## Step 4: expose it as a fixture

```python
# tests/conftest.py
import pytest
from api_clients.task_client import TaskClient


@pytest.fixture(scope="session")
def task_client():
    client = TaskClient()
    yield client
    client.close()                # teardown — Track 2 #3
```

## The payoff

```python
def test_get_task_list(task_client):
    body = assert_success(task_client.get_list())
    assert isinstance(body["tasks"], list)
```

No URLs, no headers, no timeouts in the test. The test says *what* it checks, not *how* to call.

## Don't confuse: client vs Page Object

They're the same idea at different layers:

| | Page Object (Track 4) | API client (here) |
|---|---|---|
| Hides | Locators, clicks | URLs, headers, auth |
| Exposes | `login()`, `create_task()` | `create()`, `get_details()` |
| So tests read as | User actions | API operations |

---

# 7. Negative and edge-case testing 🔴

**This is where API testing earns its value.** Happy-path tests confirm the feature works. Negative
tests find the bugs.

## The categories

| Category | Example |
|---|---|
| **Auth** | No token, invalid token, expired token, wrong user's data |
| **Missing fields** | Required field absent |
| **Wrong types** | String where an integer is expected |
| **Boundaries** | 0, -1, empty string, maximum length |
| **Malformed** | Broken JSON, wrong content type |
| **Business rules** | Actions that should be blocked |

## Auth tests

```python
def test_no_token_is_rejected():
    resp = requests.post(f"{BASE_URL}/cortex/api/task/v1/taskGetList",
                         json={}, timeout=30)
    assert resp.status_code == 401


def test_garbage_token_is_rejected():
    resp = requests.post(
        f"{BASE_URL}/cortex/api/task/v1/taskGetList",
        json={},
        headers={"Authorization": "Bearer not-a-real-token"},
        timeout=30,
    )
    assert resp.status_code == 401
    assert resp.json()["status"] in ("FailureInvalidToken", "Unauthorized")
```

Note it asserts the **specific** app status, not just "it failed." That distinguishes a malformed
token from an expired one — different bugs.

## Missing and wrong fields

Real `taskCreate` requires `userMessage` and `receiverId`:

```python
@pytest.mark.parametrize("payload, description", [
    ({},                                    "completely empty"),
    ({"receiverId": "cloud"},               "missing userMessage"),
    ({"userMessage": {"text": "hi"}},       "missing receiverId"),
])
def test_task_create_rejects_bad_payload(task_client, payload, description):
    resp = task_client.post("/cortex/api/task/v1/taskCreate", payload)
    assert resp.status_code == 400, f"Should reject: {description}"
    assert resp.json()["status"] == "FailureValidationError"
```

Parametrize (Track 2 #5) makes each case its own named test.

## Boundaries

`cancelAfterSteps` is a real optional field with a documented minimum of 1:

```python
@pytest.mark.parametrize("steps", [0, -1, -999])
def test_cancel_after_steps_rejects_below_minimum(task_client, steps):
    resp = task_client.create(
        user_message={"text": "test"},
        cancelAfterSteps=steps,
    )
    assert resp.status_code == 400
```

## Airtap-specific business rules worth testing

| Rule | Expected |
|---|---|
| Create a second task while one is active | Should **queue**, not error (`FailureActiveTaskExists` exists as a status — worth checking which happens) |
| Waitlisted account creates a task | Rejected |
| Request another user's task by ID | Rejected — an access-control test, not just a functional one |
| Body over 50MB | 413 |

That third one matters most: **"can user A read user B's task?"** is a security test. Worth writing
early.

## A quirk to know

From the Phase-1 research: Airtap **silently ignores undeclared extra fields** rather than
rejecting them.

```python
def test_extra_fields_are_ignored(task_client):
    resp = task_client.create(
        user_message={"text": "hi"},
        totallyMadeUpField="nonsense",       # not in the DTO
    )
    assert resp.status_code == 200           # accepted, field dropped
```

This is intentional — but worth a test so you'd notice if it changed.

---

# 8. Test data 🟠

## The problem

```python
def test_one():
    payload = {"userMessage": {"text": "test"}, "receiverId": "cloud"}    # repeated
def test_two():
    payload = {"userMessage": {"text": "test"}, "receiverId": "cloud"}    # repeated
```

Worse — if these share one dict, you hit the mutable-shared-data bug from
[Track 1 #12](track_01_python_for_automation.md).

## Fix 1: a builder function

```python
def make_task_payload(text="test task", receiver="cloud", **overrides):
    payload = {
        "userMessage": {"text": text},
        "receiverId": receiver,
    }
    payload.update(overrides)
    return payload            # a FRESH dict every call
```

```python
make_task_payload()
make_task_payload(text="check the weather")
make_task_payload(receiver="physical", cancelAfterSteps=3)
```

## Fix 2: a fixture factory (Track 2 #7)

```python
@pytest.fixture
def task_payload():
    def _make(text="test task", **overrides):
        return {"userMessage": {"text": text}, "receiverId": "cloud", **overrides}
    return _make


def test_something(task_payload, task_client):
    resp = task_client.post("/cortex/api/task/v1/taskCreate", task_payload("hello"))
```

## `Faker` — realistic random data

```bash
pip install faker
```

```python
from faker import Faker
fake = Faker()

fake.email()          # 'joshua43@example.org'
fake.name()           # 'Amanda Perez'
fake.uuid4()
fake.sentence()
```

**Where it helps:** unique values so tests don't collide.

```python
def make_routine_name():
    return f"qa-test-{fake.uuid4()[:8]}"     # unique every run
```

**Where it doesn't:** don't randomise the thing you're testing. If you're testing schedule parsing,
use the **real 129 RRULE cases** — random text proves nothing.

## Clean up what you create

```python
@pytest.fixture
def created_task(task_client):
    created = []

    def _create(text="test"):
        body = assert_success(task_client.create({"text": text}))
        created.append(body["taskId"])
        return body["taskId"]

    yield _create

    for task_id in created:
        task_client.cancel(task_id)          # runs even if the test failed
```

QA environments are shared. Leaving hundreds of test tasks behind is bad manners and eventually
breaks other people's tests.

---

# 9. API chaining 🟠

## What it is

Using the output of one call as the input to the next — which is what any real workflow looks like.

## Simple example

```python
def test_create_then_read(task_client):
    # 1. create
    create_body = assert_success(task_client.create({"text": "hello"}))
    task_id = create_body["taskId"]              # ← output

    # 2. use that id
    details = assert_success(task_client.get_details(task_id))     # ← input
    assert details["taskId"] == task_id
```

`taskCreate` genuinely returns `{taskId: string}` — that's the real response type.

## Longer chain

```python
def test_task_lifecycle(task_client):
    task_id = assert_success(task_client.create({"text": "hello"}))["taskId"]

    assert_success(task_client.cancel(task_id))

    details = assert_success(task_client.get_details(task_id))
    assert details["taskState"] == "CANCELLED"

    tasks = assert_success(task_client.get_list())["tasks"]
    assert any(t["taskId"] == task_id for t in tasks)
```

## The trap: chained tests that depend on each other

```python
task_id = None                       # ❌ module-level shared state

def test_create():
    global task_id
    task_id = create()["taskId"]

def test_read():                     # breaks if run alone, or in parallel
    get_details(task_id)
```

**Why it's bad:** you can't run `test_read` by itself, order matters, and parallel runs
(`pytest -n 4`) break completely.

**The fix:** each test sets up what it needs, via a fixture:

```python
@pytest.fixture
def existing_task(task_client):
    return assert_success(task_client.create({"text": "test"}))["taskId"]


def test_read(task_client, existing_task):      # self-sufficient
    details = assert_success(task_client.get_details(existing_task))
    assert details["taskId"] == existing_task
```

---

# 10. Retry logic and rate limits 🟠

## Why

Networks blip. Servers restart. A test failing because of a one-off timeout is noise, not a bug.

## Built-in retries for connection problems

```python
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

retry = Retry(
    total=3,
    backoff_factor=1,                          # waits 1s, 2s, 4s
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"],
)
session.mount("https://", HTTPAdapter(max_retries=retry))
```

**Backoff** means waiting longer between attempts, rather than hammering a struggling server.

## Rate limiting (429)

429 means "you're sending too fast." The reply often tells you how long to wait:

```python
if resp.status_code == 429:
    wait = int(resp.headers.get("Retry-After", 5))
    time.sleep(wait)
```

## ⚠️ Retry the transport, not the assertion

```python
# ✅ fine — the network flaked
retry on: connection error, timeout, 502, 503

# ❌ not fine — this hides a real bug
for _ in range(3):
    if resp.json()["status"] == "Success":
        break
```

If a test only passes on the third try, that's information you're throwing away. This is the
"retrying vs root-causing" distinction that Track 5 covers — and it's a senior/junior dividing
line in interviews.

---

# 11. Async polling for job-driven APIs 🔴

**The single most Airtap-relevant topic in this track.** Build this once, reuse it everywhere —
including in your Playwright tests (Track 4).

## The problem

When you create an Airtap task, the API replies **immediately** with a `taskId`. The task hasn't
run yet. The AI agent works through it step by step in the background — that can take seconds or
minutes.

So this test is wrong:

```python
def test_task_completes(task_client):
    task_id = assert_success(task_client.create({"text": "hello"}))["taskId"]
    details = assert_success(task_client.get_details(task_id))
    assert details["taskState"] == "COMPLETED"        # ❌ almost certainly still QUEUED
```

## The wrong fix

```python
time.sleep(60)          # ❌
```

Same problem as the `time.sleep(5)` in Airtap's existing UI suite: too slow when the task is fast,
too short when it's slow, and it hides what you're actually waiting for.

## The right fix: poll until a terminal state

```python
import time

TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED", "STOPPED"}


class TaskTimeoutError(Exception):          # custom exception — Track 1 #4
    pass


def wait_for_task(task_client, task_id, timeout=180, interval=3):
    """Poll until the task reaches a terminal state. Return its final details."""
    deadline = time.time() + timeout

    while time.time() < deadline:
        details = assert_success(task_client.get_details(task_id))
        state = details["taskState"]

        if state in TERMINAL_STATES:
            return details                   # done

        time.sleep(interval)

    raise TaskTimeoutError(
        f"Task {task_id} still in '{state}' after {timeout}s"
    )
```

Using it:

```python
def test_task_completes(task_client):
    task_id = assert_success(task_client.create({"text": "what is 2+2?"}))["taskId"]

    details = wait_for_task(task_client, task_id)

    assert details["taskState"] == "COMPLETED", \
        f"Task ended as {details['taskState']}: {details.get('failureReason')}"
```

## Why each piece matters

| Piece | Why |
|---|---|
| `deadline` | A hard stop — the test can never hang forever |
| `interval` | Don't hammer the API every millisecond |
| `TERMINAL_STATES` as a set | Stop on **any** ending, not just success |
| Custom exception with the task ID | The failure message tells you what to go look at |
| Returns the details | The caller asserts; the helper just waits |

## The most important design point

**Poll for `in TERMINAL_STATES`, not `== "COMPLETED"`.**

If you only wait for `COMPLETED`, a task that `FAILED` in two seconds still makes your test sit
there for the full three minutes before timing out. Waiting for *any* ending gives you a fast, clear
failure.

## Waiting for a specific state

Some tasks legitimately end in "waiting for the user":

```python
def wait_for_state(task_client, task_id, wanted, timeout=180, interval=3):
    deadline = time.time() + timeout
    while time.time() < deadline:
        details = assert_success(task_client.get_details(task_id))
        if details["taskState"] == wanted:
            return details
        if details["taskState"] in TERMINAL_STATES:
            raise AssertionError(f"Ended as {details['taskState']}, wanted {wanted}")
        time.sleep(interval)
    raise TaskTimeoutError(f"Never reached {wanted}")
```

Now you can test `WAITING_FOR_USER_INPUT` — the agent asking a clarifying question.

## Keep runs cheap with `cancelAfterSteps`

`taskCreate` has a real optional field: `cancelAfterSteps` (integer, minimum 1).

```python
task_client.create({"text": "open settings"}, cancelAfterSteps=3)
```

The task stops after three agent steps. **This is genuinely valuable for automation** — real agent
runs cost money (LLM calls) and time. For tests that only need to confirm a task *starts and
progresses*, capping the steps keeps your suite fast and cheap.

## Non-determinism (the Airtap reality)

The same task can take a different path each run, and still be correct. So:

```python
assert details["finalResponse"] == "The answer is 4"     # ❌ brittle wording
assert details["taskState"] == "COMPLETED"               # ✅ state, not wording
assert "4" in details["finalResponse"]                   # ✅ meaning, loosely
```

Assert on **state and structure**, not exact AI-generated text. This is Track 8c territory, and this
polling helper is its foundation.

---

# 12. Mocking 🟡

## What it is

Replacing a real API call with a fake reply, so you can test **your own code** without the network.

## When it's useful

- Testing your error handling — how does your client behave on a 500?
- Testing something hard to trigger for real (rate limits, timeouts)
- Fast unit tests for your framework's own logic

## Example with `responses`

```bash
pip install responses
```

```python
import responses

@responses.activate
def test_client_handles_server_error():
    responses.add(
        responses.POST,
        "https://qa1.airtap.ai/cortex/api/task/v1/taskGetList",
        json={"status": "Failure", "message": "boom"},
        status=500,
    )

    client = TaskClient()
    resp = client.get_list()
    assert resp.status_code == 500        # no real network call happened
```

## The limit

**Mocking tests your code, not their API.** If the backend changes its response shape, your mocked
test still passes — while production breaks.

Use mocks for your framework's internals. Use real calls for actual API testing.

---

# 13. `httpx` and async 🟡

Needs [Track 1 #14](track_01_python_for_automation.md).

## When to bother

When you need many calls at once. Sequentially, 20 calls at 1 second each takes 20 seconds.
Concurrently, about 1.

```bash
pip install httpx pytest-asyncio
```

```python
import httpx, asyncio, pytest


@pytest.mark.asyncio
async def test_many_tasks_in_parallel():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30) as client:
        client.headers["Authorization"] = f"Bearer {PAT}"

        responses = await asyncio.gather(*[
            client.post("/cortex/api/task/v1/taskGetDetails", json={"taskId": tid})
            for tid in task_ids
        ])

    for r in responses:
        assert r.status_code == 200
```

`httpx` has almost the same API as `requests`, so switching is easy.

**Don't reach for this by default.** Plain `requests` is simpler and fine for most API tests. Use
async when you have a genuine "many calls at once" need.

---

# 14. OAuth2 🟡

## The idea

OAuth2 is how "Sign in with Google" works. Instead of giving an app your password, you approve it
with the provider, and the app gets a token.

## The common flow

```
1. App sends you to Google
2. You log in and approve
3. Google redirects back with a short code
4. App swaps that code for an access token
5. App uses the token as a Bearer header
```

## Why it's only P2

**Step 2 requires a human in a browser.** That's deliberate — it's a security feature. Most teams
don't fully automate OAuth login. They either:
- Use a service account / API token instead (what Airtap's PAT does), or
- Log in once manually and reuse the saved session (what `web-automation`'s persistent Chrome
  profile does today)

**For Airtap:** use the PAT. Don't try to automate Google Sign-In.

---

# 15. Contract testing 🟢

**Awareness only.**

## The idea

In a microservice system, service A calls service B. Contract testing writes down the agreed shape
of that call, and both sides test against it — so B can't change its response without B's own tests
failing first.

Pact is the best-known tool.

## Why it's low priority for you

It matters most in organisations with many services and many teams. At SDET-2/3 level it's rarely
required unless a job description names it explicitly.

**What you should be able to say:** *"Contract testing catches integration breakage at build time
instead of in staging, by making both sides test against a shared agreed schema."* That's enough.

Your JSON Schema validation (topic #5) is already a lightweight version of the same instinct.

---

# Putting it together: a complete test file

```python
# tests/test_task_lifecycle.py
import pytest
from helpers import assert_success, wait_for_task


@pytest.mark.smoke
def test_health_check_is_up(task_client):
    resp = task_client.get("/cortex/api/check/v1/checkHealth")
    assert resp.status_code == 200


@pytest.mark.smoke
def test_task_list_requires_auth():
    import requests
    from config.settings import BASE_URL
    resp = requests.post(f"{BASE_URL}/cortex/api/task/v1/taskGetList",
                         json={}, timeout=30)
    assert resp.status_code == 401


def test_create_and_complete_task(task_client):
    body = assert_success(task_client.create(
        user_message={"text": "what is 2 plus 2?"},
        cancelAfterSteps=5,                          # keep it cheap
    ))
    task_id = body["taskId"]

    details = wait_for_task(task_client, task_id, timeout=180)

    assert details["taskState"] in ("COMPLETED", "STOPPED")
    assert details["taskId"] == task_id


@pytest.mark.parametrize("payload, why", [
    ({},                              "empty body"),
    ({"receiverId": "cloud"},         "no userMessage"),
    ({"userMessage": {"text": "x"}},  "no receiverId"),
])
def test_create_rejects_invalid_payload(task_client, payload, why):
    resp = task_client.post("/cortex/api/task/v1/taskCreate", payload)
    assert resp.status_code == 400, f"should reject: {why}"
    assert resp.json()["status"] == "FailureValidationError"
```

Every piece here comes from an earlier topic: fixtures and markers and parametrize (Track 2), the
client (#6), `assert_success` (#4), negative cases (#7), and polling (#11).

---

# Quick-fire differentiation table

| Question | Answer |
|---|---|
| `json=` vs `data=` | `json=` sends JSON and sets the header; `data=` sends form-encoded |
| `requests.post()` vs `Session.post()` | Session reuses the connection and shares headers |
| 4xx vs 5xx | 4xx = your request is wrong; 5xx = their server broke |
| HTTP status vs Airtap's `status` field | Two separate things — **always check both** |
| jsonschema vs Pydantic | Schema validates a dict; Pydantic gives you a typed object too |
| Path param vs query param vs body | Which thing / filters and options / the data being sent |
| Mocking vs real API calls | Mocks test *your* code; real calls test *their* API |
| Retrying transport vs retrying assertions | Transport retry is fine; assertion retry hides bugs |
| Polling vs `sleep` | Polling stops as soon as it's ready and fails clearly on timeout |
| Wait for `COMPLETED` vs any terminal state | Any terminal state — otherwise a fast failure waits the full timeout |
| API client vs Page Object | Same pattern, different layer: hides URLs vs hides locators |

---

# Practice checklist

Build this against **qa1 or qa2**, never production, using a PAT.

**Setup**
- [ ] Create `api-automation/` with the folder layout from #6
- [ ] Put `BASE_URL` and the PAT in env vars, not code
- [ ] Get a PAT issued for a test account and confirm it's `ADMITTED`

**First calls (doc 02, Milestone 1)**
- [ ] Call `checkHealth` and assert 200
- [ ] Call `taskGetList` with no auth and assert 401
- [ ] Call `taskGetList` with your PAT and assert `status == "Success"`

**Validation**
- [ ] Write `assert_success()` and use it everywhere
- [ ] Write a JSON schema for the task-details response and validate against it
- [ ] Include the real task states in an `enum` so an unknown state fails

**Structure (Milestone 2)**
- [ ] Build `BaseClient` with a `Session` and auth
- [ ] Build `TaskClient` with `create`, `get_details`, `get_list`, `cancel`
- [ ] Expose it as a session-scoped fixture

**Negative (Milestone 5)**
- [ ] Parametrized invalid-payload tests for `taskCreate`
- [ ] Invalid token, missing token
- [ ] Try reading another account's task and confirm it's rejected

**The big one (Milestone 4)**
- [ ] Write `wait_for_task()` with a timeout and a custom exception
- [ ] Create a task with `cancelAfterSteps=3` and poll to completion
- [ ] Make it fail on purpose (bad task ID) and confirm the error message is useful

**Reuse the existing manual suite (Milestone 3)**
- [ ] Convert 10 rows of `manual-custom-routine-rrule-ai-test-cases.md` into a parametrized test
- [ ] Then convert the invalid-prompt rows using `pytest.raises`
