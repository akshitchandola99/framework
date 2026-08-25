# Track 1 — Python for Automation

*Deep-dive for Track 1 of [00_master_study_plan.md](00_master_study_plan.md). Topics are in
learning order — each one only uses ideas from earlier topics. Read top to bottom.*

## Topic table


| #   | Topic                                                      | Priority | Notes                                                                                |
| --- | ---------------------------------------------------------- | -------- | ------------------------------------------------------------------------------------ |
| 1   | Virtual environments, `pip`, `requirements.txt`            | 🔴 P0    | **First.** You can't write project code without it.                                  |
| 2   | Reading a traceback bottom-up                              | 🔴 P0    | Needed the moment your first code breaks. Highest-ROI debugging skill.               |
| 3   | Collections (`list`, `dict`, `set`, `tuple`, `Counter`...) | 🟠 P1    | Test data and API response handling. Also covers what `[]` / `()` / `{}` mean where. |
| 4   | Exception handling                                         | 🔴 P0    | `try`/`except`/`finally`, custom errors, when *not* to catch.                        |
| 5   | `*args` / `**kwargs`, lambda                               | 🟠 P1    | **Must come before decorators** — decorators are written using them.                 |
| 6   | OOP: classes, objects, `self`, `__init__`, inheritance     | 🔴 P0    | Page Objects and API clients *are* classes.                                          |
| 7   | OOP theory terms                                           | 🟠 P1    | Interview definitions only. Don't over-study.                                        |
| 8   | **Decorators**                                             | 🔴 P0    | Every pytest fixture/marker is a decorator. Write one from scratch.                  |
| 9   | Context managers (`with`)                                  | 🔴 P0    | Guaranteed cleanup. Uses decorators, hence after #8.                                 |
| 10  | Type hints                                                 | 🟠 P1    | Readability + IDE help. Needed before dataclasses.                                   |
| 11  | Dataclasses                                                | 🟠 P1    | Clean test-data models. Needs type hints (#10).                                      |
| 12  | Mutable/immutable, deep vs shallow copy, list vs tuple     | 🟠 P1    | Interview flashcards *and* a real source of test bugs.                               |
| 13  | Generators & iterators                                     | 🟡 P2    | Interview favourite; useful for big files.                                           |
| 14  | Async programming (`async`/`await`)                        | 🟡 P2    | Needed for `httpx` async clients.                                                    |
| 15  | Threading, multiprocessing, GIL                            | 🟢 P3    | **Trivia only.** `pytest-xdist` handles parallel tests for you.                      |


---



# 1. Virtual environments, pip, requirements.txt 🔴



## What it is

A virtual environment is just **a folder that holds its own private copy of Python and its own
packages**. Each project gets its own.

## Why you need it

Say you have two projects:

- Project A needs Playwright version 1.40
- Project B needs Playwright version 1.50

Without virtual environments, both share one global Python. Installing 1.50 for Project B **breaks
Project A**. With virtual environments, each project has its own copy and they never clash.

## How to use it

```bash
# 1. create it (do this once per project)
python -m venv .venv

# 2. activate it (do this every time you open a terminal)
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows

# 3. install things
pip install pytest requests

# 4. save what you installed
pip freeze > requirements.txt

# 5. leave it when done
deactivate
```



## How to tell if it's active

Your terminal prompt changes — it shows the environment name in brackets:

```bash
(.venv) yourname@laptop project %
```

If you don't see `(.venv)`, it is **not** active, and `pip install` will go to the wrong place.

## What requirements.txt is

A plain text file listing every package and its version:

```text
pytest==8.3.2
requests==2.32.3
playwright==1.47.0
```

Someone else (or a CI machine) recreates your exact setup with one command:

```bash
pip install -r requirements.txt
```



## Common mistakes


| Mistake                    | What happens                                                       |
| -------------------------- | ------------------------------------------------------------------ |
| Forgetting to activate     | Packages install globally; your project can't find them            |
| Committing `.venv` to git  | Huge folder, breaks on other machines. Add `.venv` to `.gitignore` |
| Never running `pip freeze` | Nobody else can reproduce your setup                               |


**Airtap:** `web-automation/.venv` already exists — that suite is already set up this way.

## Don't confuse

- `venv` — built into Python. The standard. Use this.
- `conda` — for data science. Heavier.
- `poetry` **/** `uv` — newer tools that do more. Fine, but not needed to start.

---



# 2. Reading a traceback 🔴



## What it is

When Python hits an error it prints a **traceback** — a report of what broke and where.

## The one rule: read it bottom-up

The **last line** tells you *what* went wrong. The lines **above** tell you *where*.

```
Traceback (most recent call last):
  File "test_login.py", line 12, in test_login
    login_page.login("me", "pw")
  File "pages/login_page.py", line 8, in login
    self.page.fill("#user", user)
TimeoutError: Timeout 30000ms exceeded waiting for "#user"
```

Read it like this:

1. **Bottom line:** `TimeoutError` — the element `#user` was never found.
2. **Above it:** it happened in `pages/login_page.py`, line 8.
3. **Above that:** which was called from `test_login.py`, line 12.

So: your test called `login()`, which tried to fill `#user`, which never appeared.

## Anatomy

Each `File ... line ... in ...` block is called a **frame**. It's one function call. They're listed
oldest-first, so:

- **Top frame** = where your code started
- **Bottom frame** = where it actually broke

Most of the time the bottom two lines are all you need.

## Common errors and what they mean


| Error                                 | Plain meaning                 | Typical cause                                         |
| ------------------------------------- | ----------------------------- | ----------------------------------------------------- |
| `NameError`                           | That name doesn't exist       | Typo, or used a variable before creating it           |
| `TypeError`                           | Wrong type of thing           | `"5" + 5`, or wrong number of arguments               |
| `AttributeError`                      | That object has no such thing | `None.something` — usually a function returned `None` |
| `KeyError`                            | Dictionary has no such key    | API response missing a field you expected             |
| `IndexError`                          | List position doesn't exist   | Empty list, or off-by-one                             |
| `ImportError` / `ModuleNotFoundError` | Can't find that package       | Forgot to activate venv, or didn't install it         |
| `AssertionError`                      | Your `assert` failed          | This is a **test failure**, not a code crash          |




## The one to watch for

`AttributeError: 'NoneType' object has no attribute 'x'` is extremely common. It almost always
means **a function returned** `None` **when you expected a real value**. Look at what produced that
object, not where it exploded.

## Why this matters

Most people see a wall of red text, panic, and start guessing. Reading it properly takes ten
seconds and usually tells you the exact line to fix.

---



# 3. Collections 🟠

These are the containers you'll use constantly for test data and API responses.

## The four basics


| Type    | Bracket | Mental model                                          | Ordered?        | Changeable? | Duplicates? |
| ------- | ------- | ----------------------------------------------------- | --------------- | ----------- | ----------- |
| `list`  | `[]`    | A shopping list — things in order, you keep adding    | Yes             | Yes         | Yes         |
| `tuple` | `()`    | A record/row — fixed slots, each slot means something | Yes             | **No**      | Yes         |
| `set`   | `{}`    | A guest list — "is this name on it?", no repeats      | No              | Yes         | **No**      |
| `dict`  | `{}`    | A labelled drawer — look things up by name            | Yes (insertion) | Yes         | Keys unique |


```python
# list — ordered, changeable, allows duplicates
tools = ["Tap", "Swipe", "Tap"]
tools.append("InputText")
print(tools[0])              # "Tap"

# dict — key → value lookup
task = {"id": "abc123", "state": "COMPLETED"}
print(task["state"])         # "COMPLETED"

# set — unique items only, very fast "is it in here?"
seen = {"Tap", "Swipe"}
print("Tap" in seen)         # True

# tuple — like a list, but cannot be changed
point = (100, 250)
```



## When to use which


| Need                                          | Use     |
| --------------------------------------------- | ------- |
| A sequence you'll add to / change             | `list`  |
| Look something up by name/key                 | `dict`  |
| Remove duplicates, or fast "does this exist?" | `set`   |
| A fixed pair/group that shouldn't change      | `tuple` |


As a flowchart:

```
Do items have names/labels?             → dict   {k: v}
Only care "is X in there?" / no dupes?  → set    {a, b}
Fixed shape, fixed meaning per slot?    → tuple  (a, b, c)
Otherwise (growing pile, order matters) → list   [a, b, c]
```



## Which bracket, and why

The same bracket means different things depending on where it sits. This trips up nearly everyone.

### `[]` — "a sequence" *or* "reach inside something"

Two jobs:

```python
text_parts = []           # 1. standing alone → a new list
text_parts[0]             # 2. attached to a name → get item out
```

**The rule:** `[]` **touching a name** is a lookup. `[]` **standing alone** builds a list.

Job 2 works on anything indexable, not just lists:

```python
parts[0]                  # list → by position
payload["modelId"]        # dict → by key
value[:limit]             # string → by slice
```



### `()` — "call it", "group it", or "a tuple"

```python
get_base_url()            # 1. call a function
(a or b) and c            # 2. group an expression for precedence
("taskId", "receiverId")  # 3. a tuple
```

⚠️ **The classic trap:** the **comma** makes a tuple, not the brackets.

```python
("hello")     # just the string "hello" — the brackets did nothing
("hello",)    # a 1-item tuple ← the trailing comma is required
```

Brackets are often optional for tuples. This returns a 3-tuple with no brackets at all:

```python
return index, agent_message, latest_update
```



### `{}` — dict *or* set, decided by what's inside

```python
{}                  # empty DICT (the default — sets lose this fight)
set()               # empty set
{"a": 1}            # has a colon → dict
{"a", "b"}          # no colon → set
```

**One rule:** colon inside = dict, no colon = set, nothing inside = dict.

⚠️ This is why you write `seen = set()` and never `seen = {}` for an empty set.

### Bonus: the bracket picks the comprehension type

Same loop, four different results — only the bracket changes:

```python
[p["text"] for p in parts]              # → list
{p["text"] for p in parts}              # → set (deduplicated)
{p["type"]: p["text"] for p in parts}   # → dict
(p["text"] for p in parts)              # → generator, NOT a tuple (see topic #13)
```

The generator form is worth knowing because `any(...)` and `all(...)` can stop early with it —
they never need the whole collection built.

## Safe dictionary access

This is important for API responses, where a field might be missing:

```python
task = {"id": "abc123"}

task["state"]              # ❌ KeyError — crashes
task.get("state")          # ✅ returns None
task.get("state", "UNKNOWN")   # ✅ returns "UNKNOWN"
```



## Useful loops

```python
# loop over a dict
for key, value in task.items():
    print(key, "=", value)

# loop with position number
for i, tool in enumerate(tools):
    print(i, tool)
```



## Three helpers worth knowing

`Counter` — counts things for you:

```python
from collections import Counter

tools = ["Tap", "Tap", "InputText"]
counts = Counter(tools)
print(counts)                  # Counter({'Tap': 2, 'InputText': 1})
print(counts["Tap"])           # 2
print(counts.most_common(1))   # [('Tap', 2)]
```

`defaultdict` — a dict that creates missing values automatically:

```python
from collections import defaultdict

# without it, you must check first
steps_by_task = defaultdict(list)
steps_by_task["task1"].append("Tap")    # key didn't exist — created automatically
```

`namedtuple` — a tuple with names instead of positions:

```python
from collections import namedtuple

Point = namedtuple("Point", ["x", "y"])
p = Point(100, 250)
print(p.x)      # 100 — clearer than p[0]
```



## Nested data (real API responses)

API responses are usually dicts inside lists inside dicts:

```python
response = {
    "task": {
        "id": "abc123",
        "steps": [
            {"tool": "Tap", "success": True},
            {"tool": "InputText", "success": False},
        ]
    }
}

# get the first step's tool
print(response["task"]["steps"][0]["tool"])     # "Tap"

# get all tool names — this is a "list comprehension"
tools = [s["tool"] for s in response["task"]["steps"]]
print(tools)                                     # ['Tap', 'InputText']

# only the failed ones
failed = [s["tool"] for s in response["task"]["steps"] if not s["success"]]
print(failed)                                    # ['InputText']
```

A **list comprehension** is just a short way of writing a loop that builds a list. Read it as:
*"give me* `s["tool"]` *for each* `s` *in that list."*

**Airtap:** counting which tools a task used across all its steps — `Counter` does it in one line.
Useful for an assertion like "this task should never call `LaunchIntent`."

## All four, in the real airtap codebase

Every example below is actual code in this repo. Open the files alongside this section.

### `list` — an ordered pile you keep growing

`agent-skills/airtap/scripts/airtap_common.py:145` — a message starts with its text part, and an
image is *appended* only if the user passed one:

```python
parts = [{"type": "text", "text": message_text}]
if image_file:
    parts.append({"type": "image", "contentBase64": read_base64_file(image_file)})
```

**Why a list?** Order matters (text before image) and the size isn't known upfront. Same pattern at
`airtap_common.py:472`, where `unseen_agent_messages` is built up inside the polling loop, and at
`web-automation/browser_config.py:20`, where Chrome flags are `["--start-maximized"]` — a list
because Chrome consumes flags in order.

### `tuple` — a fixed-shape record

`airtap_common.py:39` declares the shape once:

```python
AgentUpdate = Tuple[int, Dict[str, Any], str]   # (index, message, text)
```

Every agent update is *always* those three things in that order. Built at `airtap_common.py:482`:

```python
unseen_agent_messages.append((index, agent_message, latest_update))
```

…and unpacked by shape at `airtap_common.py:362`:

```python
return "\n\n".join(text for text, _, _ in extract_text_part_entries(message))
```

That `text, _, _` only works because the shape is guaranteed. `_` means "I don't need this slot."

**Why not a list?** A list says *"0 or more of the same kind of thing."* A tuple says *"exactly
these 3 different things."* The tuple documents the shape and makes accidental mutation impossible.

`airtap_common.py:207` shows the other common use — a hardcoded loop over fixed field names:

```python
for key in ("taskId", "receiverId", "modelId"):
```



### `set` — uniqueness and fast "is it in there?"

`airtap_common.py:26` is a textbook case:

```python
POLL_FINAL_TASK_STATES = {"COMPLETED", "FAILED", "CANCELLED", "STOPPED"}
POLL_WAITING_TASK_STATES = {"WAITING_FOR_USER_INPUT", ...}
POLL_STOP_TASK_STATES = POLL_FINAL_TASK_STATES | POLL_WAITING_TASK_STATES
```

The only thing ever done with it, at `airtap_common.py:507`:

```python
if isinstance(task_state, str) and task_state in POLL_STOP_TASK_STATES:
```

**Two reasons a set wins here:**

1. `x in some_set` is instant regardless of size; `x in some_list` scans every item.
2. That `|` is set **union** — "final states OR waiting states". You get that free with sets; with
  lists you'd concatenate and risk duplicates.

The second set in that file is the deduplication guard at `airtap_common.py:452`:

```python
seen_agent_signatures: Set[str] = set()
...
if message_signature in seen_agent_signatures:
    continue                                  # already shown this update, skip it
seen_agent_signatures.add(message_signature)
```

This is *why* polling doesn't reprint the same agent message every 10 seconds. A set is exactly
right: the contents are never read back, only asked "seen this before?"

### `dict` — look up a value by its name

Almost every API payload in airtap is a dict. `airtap_common.py:287` shows the two big superpowers
— conditionally adding a key, and safe reads:

```python
payload: Dict[str, Any] = {
    "receiverId": receiver_id,
    "userMessage": build_user_message(message_text, image_file),
}
if model_id:
    payload["modelId"] = model_id      # add a key only when there's a value
```

```python
task_state = task_details.get("taskState")   # None if missing — no KeyError
```

`payload["modelId"]` would **crash** if the key were absent; `.get()` returns `None` instead. That
is why all the response-reading code uses `.get()` — the server's JSON shape isn't guaranteed.

Dicts are also how airtap talks to the outside world: `response.json()` hands you a dict,
`json.dumps()` turns one back into text, and `web-automation/browser_config.py:14` builds a dict of
Playwright options that gets spread into the call with `**` (topic #5):

```python
playwright.chromium.launch_persistent_context(**chrome_persistent_launch_options())
```



### The one conversion worth copying

`airtap_common.py:222`:

```python
summary["keys"] = sorted(payload.keys())
```

`payload.keys()` has no reliable order for logging, and JSON has no "set" type at all — so it's
converted to a sorted **list** before being written out.

**The practical rule: use sets and dicts for *working*, convert to lists when you need to *output*.**

## Don't confuse

- `{}` **is an empty dict, not an empty set.** Empty set is `set()`.
- `("x")` **is not a tuple** — it's just the string. You need the trailing comma: `("x",)`.
- `(x for x in y)` **is a generator, not a tuple** — see topic #13.
- **A tuple can be a dict key; a list cannot** — see topic #12.

---



# 4. Exception handling 🔴



## What it is

Catching errors on purpose so your code can react, instead of just crashing.

## The basic shape

```python
try:
    resp = requests.get(url, timeout=5)
except requests.Timeout:
    print("The API was too slow")
```



## All four parts

```python
try:
    resp = requests.get(url, timeout=5)
except requests.Timeout:
    print("too slow")            # runs only if that error happened
except requests.ConnectionError:
    print("could not connect")   # you can catch different errors differently
else:
    print("worked fine")         # runs only if NO error happened
finally:
    session.close()              # ALWAYS runs, error or not
```

- `except` — handle a specific error
- `else` — the happy path
- `finally` — cleanup that must always happen



## Catching specific errors matters

```python
except:                      # ❌ NEVER. Catches everything, including your own typos.
except Exception:            # ⚠️ Very broad. Only at the top level of a program.
except requests.Timeout:     # ✅ Specific. You know exactly what you're handling.
```

**Why bare** `except:` **is bad:** if you make a typo in your test, the bare `except` swallows it. Your
test **passes** when it should have failed. That's the worst possible bug in a test suite.

## Raising your own errors

```python
if not task_id:
    raise ValueError("task_id cannot be empty")
```



## Custom exceptions

Make your own error type so failures read clearly:

```python
class TaskTimeoutError(Exception):
    pass

raise TaskTimeoutError(f"Task {task_id} did not finish in 120 seconds")
```

Now callers can catch *just* that:

```python
try:
    wait_for_task(task_id)
except TaskTimeoutError:
    pytest.fail("task never completed")
```



## Seeing the original error

When you catch an error and raise a different one, keep the original attached:

```python
try:
    resp = requests.get(url)
except requests.Timeout as e:
    raise TaskTimeoutError("API too slow") from e     # 'from e' keeps the original
```

Now the traceback shows both. Without `from e`, you lose the real cause.

## When NOT to catch

**Don't catch an error you can't actually handle.** If your test hits an unexpected error, you
*want* it to crash loudly. A crashed test tells you something is wrong. A silently-caught error
tells you nothing.

**Airtap:** your async polling helper should `raise TaskTimeoutError` with the task ID — not
silently return `None`. A silent `None` turns into a confusing `AttributeError` three lines later,
far away from the real problem.

---



# 5. `*args`, `**kwargs`, lambda 🟠



## First: two kinds of arguments

```python
def login(user, password):
    ...

login("me", "secret")                      # positional — order matters
login(user="me", password="secret")        # keyword — order doesn't matter
```



## Default values

```python
def get_task(task_id, timeout=30):     # timeout is optional
    ...

get_task("abc")            # timeout is 30
get_task("abc", 60)        # timeout is 60
```



## `*args` — collect extra positional arguments

The `*` means "put any extra positional arguments into a **tuple** called `args`."

```python
def show(first, *args):
    print("first:", first)
    print("rest :", args)

show(1, 2, 3)
# first: 1
# rest : (2, 3)
```



## `**kwargs` — collect extra named arguments

The `**` means "put any extra named arguments into a **dict** called `kwargs`."

```python
def call_api(method, **kwargs):
    print("method:", method)
    print("options:", kwargs)

call_api("GET", timeout=5, retries=3)
# method: GET
# options: {'timeout': 5, 'retries': 3}
```



## Both together

```python
def anything(*args, **kwargs):
    print(args)      # tuple of positional
    print(kwargs)    # dict of named

anything(1, 2, timeout=5)
# (1, 2)
# {'timeout': 5}
```

This "accept anything" pattern is exactly what decorators need (topic #8).

## Unpacking — the same symbols, in reverse

Used when **calling** a function, `*` and `*`* spread things out:

```python
numbers = [1, 2, 3]
print(*numbers)          # same as print(1, 2, 3)

options = {"timeout": 5, "retries": 3}
call_api("GET", **options)     # same as call_api("GET", timeout=5, retries=3)
```

So: `*` in a **definition** collects; `*` in a **call** spreads.

## lambda — a tiny unnamed function

These two are the same:

```python
def get_time(task):
    return task["createdAt"]

get_time = lambda task: task["createdAt"]
```

Lambdas are for when you need a one-line function immediately:

```python
tasks.sort(key=lambda t: t["createdAt"])          # sort by creation time
recent = filter(lambda t: t["state"] == "COMPLETED", tasks)
```



## When to use lambda vs def

- **lambda** — one short expression, used once, passed straight into something else
- **def** — anything longer, anything reused, anything that needs a name for readability

If your lambda needs a comment to explain it, use `def` instead.

## Don't confuse

- The names `args` and `kwargs` are just convention. `*a, **kw` works identically.
- `*` is not a pointer (like in C). It only means collect-or-spread.

---



# 6. OOP: classes, objects, `self`, `__init__` 🔴



## Class vs object

- A **class** is a blueprint.
- An **object** is one real thing built from that blueprint.

One class → many objects.

## The simplest class

```python
class LoginPage:
    def __init__(self, page):     # runs automatically when you create an object
        self.page = page          # save it so other methods can use it

    def login(self, user, pwd):
        self.page.fill("#user", user)
        self.page.fill("#pass", pwd)
        self.page.click("#submit")
```

Using it:

```python
lp = LoginPage(page)              # object created → __init__ runs
lp.login("me", "secret")          # call a method on it
```



## What `self` actually is

`self` means **"this particular object."**

When you write `lp.login("me", "secret")`, Python turns it into `LoginPage.login(lp, "me", "secret")` — it passes the object in as the first argument automatically. That first argument is
`self`.

So `self.page` means "the `page` belonging to *this* object."

```python
lp1 = LoginPage(page_one)
lp2 = LoginPage(page_two)
# lp1.page and lp2.page are different — each object has its own
```



## Attributes vs methods

- **Attribute** = data stored on the object (`self.page`)
- **Method** = a function that belongs to the object (`login()`)



## Instance vs class attributes

```python
class ApiClient:
    BASE_URL = "https://qa1.airtap.ai"     # class attribute — shared by ALL objects

    def __init__(self, token):
        self.token = token                  # instance attribute — one per object
```

Use class attributes for constants. Use instance attributes for anything that differs per object.

## Inheritance — reusing another class

```python
class BasePage:
    def __init__(self, page):
        self.page = page

    def screenshot(self, name):
        self.page.screenshot(path=f"{name}.png")


class LoginPage(BasePage):          # LoginPage gets everything BasePage has
    def login(self, user, pwd):
        self.page.fill("#user", user)


lp = LoginPage(page)
lp.login("me", "pw")     # its own method
lp.screenshot("after")   # inherited for free
```



## `super()` — calling the parent's version

If the child needs its own `__init__` but still wants the parent's setup:

```python
class LoginPage(BasePage):
    def __init__(self, page, timeout):
        super().__init__(page)      # run BasePage.__init__ first
        self.timeout = timeout      # then add our own
```



## Overriding — replacing a parent method

```python
class BasePage:
    def load(self):
        print("loading generic page")

class LoginPage(BasePage):
    def load(self):                     # same name = replaces the parent's
        print("loading login page")

LoginPage(page).load()      # "loading login page"
```



## `__str__` — make your objects readable

Very useful when debugging:

```python
class TestUser:
    def __init__(self, email):
        self.email = email

    def __str__(self):
        return f"TestUser({self.email})"

print(TestUser("a@b.com"))     # TestUser(a@b.com)
# without __str__ you'd get: <__main__.TestUser object at 0x104f2b3d0>
```



## Don't confuse

- `self` is **not a keyword**. `def login(banana, user)` technically works. Never do it — every
Python developer expects `self`.
- Methods with double underscores (`__init__`, `__str__`) are called **dunder** methods. Python
calls them for you automatically. You rarely call them directly.

**Airtap:** `web-automation/pages/pilot_app_page.py` is exactly this pattern — a Page Object class.

---



# 7. OOP theory terms 🟠

You need these to **define** in an interview. You don't need to architect around them.


| Term              | Plain meaning                                                      | Tiny example                                                              |
| ----------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------- |
| **Encapsulation** | Keep data and the methods that use it together; hide the internals | `self._token` — the underscore means "internal, don't touch from outside" |
| **Inheritance**   | A child class reuses a parent's code                               | `class LoginPage(BasePage)`                                               |
| **Polymorphism**  | Same method name, different behaviour depending on the class       | `BasePage.load()` overridden in each page class                           |
| **Abstraction**   | Hide complexity behind a simple interface                          | `api.create_task()` hides auth, retries, headers, and JSON parsing        |


**One-line interview answer for polymorphism:** *"Different classes can respond to the same method
call in their own way — so I can call* `.load()` *on any page object without knowing which page it
is."*

---



# 8. Decorators 🔴

**The most important topic in this track.** Every pytest fixture and marker is a decorator.

## Build-up 1: functions are objects

You can put a function in a variable, just like a number:

```python
def greet():
    print("hello")

f = greet        # no brackets — this is the function itself, not its result
f()              # "hello"
```



## Build-up 2: a function can return a function

```python
def make_greeter():
    def inner():
        print("hello")
    return inner            # returns the function, doesn't call it

g = make_greeter()
g()                         # "hello"
```



## Build-up 3: a function can take a function

```python
def run_twice(func):
    func()
    func()

run_twice(greet)     # prints hello twice
```



## Now: a decorator

A decorator is a function that **takes a function, wraps it, and returns the wrapper.**

```python
def log_it(func):
    def wrapper():
        print("start")
        func()
        print("done")
    return wrapper


def greet():
    print("hello")

greet = log_it(greet)     # wrap it
greet()
# start
# hello
# done
```



## The `@` symbol is just shorthand

These two are **exactly the same**:

```python
greet = log_it(greet)
```

```python
@log_it
def greet():
    print("hello")
```

That's it. That's the whole feature. `@log_it` above a function means "pass this function through
`log_it` and use the result instead."

## Making it work for any function

The version above only works for functions with no arguments and no return value. Fix it with
`*args`/`**kwargs` from topic #5:

```python
def log_it(func):
    def wrapper(*args, **kwargs):          # accept anything
        print(f"start {func.__name__}")
        result = func(*args, **kwargs)     # pass everything through
        print("done")
        return result                       # don't forget to return!
    return wrapper


@log_it
def add(a, b):
    return a + b

print(add(2, 3))
# start add
# done
# 5
```

Three things the wrapper must do:

1. Accept `*args, **kwargs`
2. Pass them through to the real function
3. **Return** the real function's result



## `functools.wraps` — keep the original name

Without it, the decorated function forgets its own name:

```python
print(add.__name__)     # "wrapper"  ← confusing in tracebacks!
```

Fix:

```python
import functools

def log_it(func):
    @functools.wraps(func)          # add this line
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

print(add.__name__)     # "add"  ✅
```

Always add `@functools.wraps(func)`. It costs one line and saves confusing debugging later.

## Decorators with arguments

`@pytest.mark.parametrize("x", [1, 2])` takes arguments. That needs **one more layer**:

```python
def repeat(times):                       # layer 1: takes the argument
    def decorator(func):                 # layer 2: takes the function
        def wrapper(*args, **kwargs):    # layer 3: does the work
            for _ in range(times):
                func(*args, **kwargs)
        return wrapper
    return decorator


@repeat(3)
def hello():
    print("hi")

hello()      # prints hi three times
```

Same idea, just wrapped once more. You rarely write these — but you use them constantly.

## Where you'll actually meet them

```python
@pytest.fixture              # decorator
def api_client():
    ...

@pytest.mark.parametrize("value", [1, 2, 3])    # decorator with arguments
def test_something(value):
    ...

@contextmanager              # topic #9 uses one too
def browser_session():
    ...
```



## Don't confuse

- **Decorator vs inheritance** — a decorator wraps a *function*; inheritance extends a *class*.
- A decorator runs **once**, when the function is defined. The wrapper runs every time you call it.

---



# 9. Context managers (`with`) 🔴



## What it is

A `with` block **guarantees cleanup happens** — even if the code inside crashes.

```python
with open("file.txt") as f:
    data = f.read()
# file is closed automatically here, even if read() raised an error
```



## Why it matters

Browsers, API sessions, and database connections must be closed. If your test crashes halfway and
the browser never closes, you leak a process. Do that a hundred times in CI and the machine runs
out of memory.

## The problem it solves

Without `with`:

```python
browser = playwright.chromium.launch()
page = browser.new_page()
page.goto("https://example.com")     # ← if this crashes...
browser.close()                       # ← this never runs. Leaked browser.
```

With `with`, cleanup always runs.

## Writing your own

The easy way uses `@contextmanager` — a decorator (topic #8):

```python
from contextlib import contextmanager

@contextmanager
def browser_session(playwright):
    browser = playwright.chromium.launch()    # setup
    try:
        yield browser                          # hand it over, test runs here
    finally:
        browser.close()                        # cleanup — always runs
```

Using it:

```python
with browser_session(playwright) as browser:
    page = browser.new_page()
    page.goto("https://example.com")
# browser closed automatically
```

**The shape to remember:** everything before `yield` is setup, everything after is cleanup. Wrap
the `yield` in `try/finally` so cleanup runs even on a crash.

If this shape looks familiar — it's exactly how pytest fixtures work.

## Multiple at once

```python
with open("in.txt") as src, open("out.txt", "w") as dst:
    dst.write(src.read())
```



## The class version (know it exists)

You can also make a class with `__enter__` and `__exit__`:

```python
class BrowserSession:
    def __enter__(self):
        self.browser = launch()
        return self.browser

    def __exit__(self, exc_type, exc_value, traceback):
        self.browser.close()
```

`@contextmanager` is simpler and covers almost every case. Use that unless you need object state.

## Don't confuse

`try/finally` does the same job:

```python
browser = launch()
try:
    ...
finally:
    browser.close()
```

`with` is just cleaner and **reusable** — write the cleanup logic once, use it everywhere.

---



# 10. Type hints 🟠



## What it is

Notes about what type a value is supposed to be.

```python
def get_task(task_id: str) -> dict:
    ...
```

Read as: "`task_id` should be a string, and this function returns a dict."

## Common ones

```python
name: str = "abc"
count: int = 5
ratio: float = 1.5
ok: bool = True

tools: list[str] = ["Tap", "Swipe"]           # list of strings
task: dict[str, str] = {"id": "abc"}          # dict, str keys, str values
point: tuple[int, int] = (100, 250)
```



## Optional — "might be None"

```python
from typing import Optional

def find_task(task_id: str) -> Optional[dict]:
    """Returns the task, or None if not found."""
```

Modern shorthand (Python 3.10+):

```python
def find_task(task_id: str) -> dict | None:
```

This is genuinely useful — it warns the reader "check for None before using this."

## The big misconception

**Python does NOT enforce type hints at runtime.** This runs happily, no error:

```python
def get_task(task_id: str) -> dict:
    return {"id": task_id}

get_task(12345)      # hinted as str, given an int — Python does not care
```

They are **documentation and tooling only**. If you want them actually checked, run a separate
tool:

```bash
pip install mypy
mypy your_file.py
```



## Why bother then

1. **Readability** — you instantly know what a function wants
2. **IDE autocomplete** — your editor knows `task` is a dict and suggests `.get()`
3. **Catching mistakes early** — with mypy, before running anything
4. **Required for dataclasses** — topic #11 literally won't work without them

---



# 11. Dataclasses 🟠



## The problem

Writing a simple data-holding class is tediously repetitive:

```python
class TestUser:
    def __init__(self, email, password, admitted=True):
        self.email = email
        self.password = password
        self.admitted = admitted

    def __repr__(self):
        return f"TestUser({self.email}, {self.password}, {self.admitted})"

    def __eq__(self, other):
        return (self.email == other.email
                and self.password == other.password
                and self.admitted == other.admitted)
```

That's a lot of typing to store three values.

## The fix

```python
from dataclasses import dataclass

@dataclass
class TestUser:
    email: str
    password: str
    admitted: bool = True
```

That's it. Same result. Notice it's a decorator (#8) and it needs type hints (#10).

## What you get free

```python
u = TestUser("a@b.com", "pw")

print(u)                    # TestUser(email='a@b.com', password='pw', admitted=True)
print(u.email)              # a@b.com

u2 = TestUser("a@b.com", "pw")
print(u == u2)              # True — compares values, not memory addresses
```

Without `@dataclass`, that last line would print `False` (two different objects).

## Default values

```python
@dataclass
class TaskRequest:
    prompt: str                            # required
    receiver_type: str = "cloud"           # optional
    timeout: int = 120                     # optional
```



## The mutable default trap

This **breaks**:

```python
@dataclass
class Config:
    tags: list = []        # ❌ Python raises an error here
```

Because a list is mutable, and all objects would share the same one. Use `field` instead:

```python
from dataclasses import dataclass, field

@dataclass
class Config:
    tags: list = field(default_factory=list)     # ✅ fresh list per object
```

(Topic #12 explains why sharing a mutable object is dangerous.)

## Don't confuse: dataclass vs Pydantic


|                          | `@dataclass`       | Pydantic                    |
| ------------------------ | ------------------ | --------------------------- |
| Built into Python?       | Yes                | No (`pip install pydantic`) |
| Checks types at runtime? | **No**             | **Yes**                     |
| `TestUser(email=123)`    | Accepted silently  | Raises an error             |
| Best for                 | Internal test data | Validating API responses    |


Rule of thumb: **dataclass for your own data, Pydantic for data from outside** (API responses,
config files).

---



# 12. Mutable, immutable, and copying 🟠



## Mutable vs immutable

- **Mutable** = can be changed after it's made → `list`, `dict`, `set`
- **Immutable** = cannot be changed → `str`, `int`, `tuple`, `bool`

```python
nums = [1, 2]
nums.append(3)         # ✅ lists can change

text = "hello"
text[0] = "H"          # ❌ TypeError — strings cannot change
```



## The trap: assignment is not a copy

```python
a = [1, 2]
b = a              # NOT a copy — b points to the SAME list
b.append(3)
print(a)           # [1, 2, 3]  ← a changed too!
```

Think of it like a shared document link, not a photocopy. Both names point at one object.

## Checking

```python
print(a is b)      # True  — same object in memory
print(a == b)      # True  — same contents
```

`is` asks "is it literally the same object?" `==` asks "do they look the same?"

## Shallow copy — copies the outside only

```python
import copy

data = {"user": {"name": "x"}}
shallow = copy.copy(data)

shallow["user"]["name"] = "y"
print(data)      # {'user': {'name': 'y'}}  ← the inner dict was shared!
```

The outer dict is new. The inner dict is still shared.

## Deep copy — copies everything

```python
deep = copy.deepcopy(data)
deep["user"]["name"] = "z"
print(data)      # unchanged ✅
```



## Simple rule

- Flat data (no nesting) → shallow copy is fine
- Nested data (dicts inside dicts) → use `deepcopy`



## Why QA cares — a real bug

```python
DEFAULT_PAYLOAD = {"prompt": "test", "options": {"timeout": 30}}

def test_one():
    payload = DEFAULT_PAYLOAD              # not a copy!
    payload["options"]["timeout"] = 5      # modifies the shared original
    ...

def test_two():
    payload = DEFAULT_PAYLOAD              # now has timeout=5, not 30
    ...                                     # fails, and looks unrelated
```

Test one passes. Test two fails. Running test two **alone** passes. This is one of the most
confusing bug shapes in test suites.

**The fix:** build fresh data per test (a function or fixture), or `deepcopy` it.

## The mutable default argument gotcha

A classic interview question:

```python
def add_tag(tag, tags=[]):       # ❌ the list is created ONCE, shared forever
    tags.append(tag)
    return tags

print(add_tag("a"))    # ['a']
print(add_tag("b"))    # ['a', 'b']  ← surprise!
```

The correct way:

```python
def add_tag(tag, tags=None):
    if tags is None:
        tags = []                # fresh list each call
    tags.append(tag)
    return tags
```



## list vs tuple


|                    | list                    | tuple                          |
| ------------------ | ----------------------- | ------------------------------ |
| Changeable?        | Yes                     | No                             |
| Syntax             | `[1, 2]`                | `(1, 2)`                       |
| Can be a dict key? | No                      | Yes                            |
| Use for            | Data that grows/changes | Fixed groups, like coordinates |


```python
coords = {(100, 250): "login button"}     # ✅ tuple key works
coords = {[100, 250]: "login button"}     # ❌ TypeError — list can't be a key
```

Only immutable things can be dictionary keys.

---



# 13. Generators & iterators 🟡



## Iterable vs iterator

- **Iterable** = anything you can loop over (`list`, `dict`, `str`, file)
- **Iterator** = the thing that actually hands you items one at a time

```python
nums = [1, 2, 3]        # iterable
it = iter(nums)         # iterator
print(next(it))         # 1
print(next(it))         # 2
```

A `for` loop does this for you automatically.

## Generators — the easy way to make an iterator

Use `yield` instead of `return`:

```python
def count_to(n):
    for i in range(1, n + 1):
        yield i          # hand over one value, remember where we were

for num in count_to(3):
    print(num)           # 1, 2, 3
```



## `return` vs `yield`

- `return` — hands back one value and the function **ends**
- `yield` — hands back one value and the function **pauses**, ready to continue



## Why: memory

```python
# loads the entire 2GB file into memory ❌
def read_all(path):
    with open(path) as f:
        return f.readlines()

# hands over one line at a time ✅
def read_lines(path):
    with open(path) as f:
        for line in f:
            yield line
```

The second one uses almost no memory no matter how big the file is.

## Generator expressions

Like a list comprehension, but with `()` instead of `[]`:

```python
squares_list = [x * x for x in range(1000)]     # builds all 1000 now
squares_gen  = (x * x for x in range(1000))     # builds them as you ask
```



## They're single-use

```python
gen = count_to(3)
print(list(gen))     # [1, 2, 3]
print(list(gen))     # []  ← already used up!
```

A list can be looped many times. A generator, once.

## Interview differentiation

- **Every generator is an iterator.** Not every iterator is a generator.
- A generator is made with `yield` (or a generator expression).
- An iterator is any object with `__iter__` and `__next__`.
- Generators are **lazy** (compute on demand) and **single-use**.

---



# 14. Async programming 🟡



## The problem

Most test time is spent **waiting** — for an API to reply, for a page to load. Normal code waits
and does nothing:

```python
r1 = requests.get(url1)      # wait 1 second doing nothing
r2 = requests.get(url2)      # wait 1 second doing nothing
r3 = requests.get(url3)      # wait 1 second doing nothing
# total: 3 seconds
```



## The fix

Async lets you start all three, then collect the results:

```python
import asyncio, httpx

async def get_one(client, url):
    r = await client.get(url)        # "pause here, let others run"
    return r.json()

async def main():
    async with httpx.AsyncClient() as client:
        results = await asyncio.gather(
            get_one(client, url1),
            get_one(client, url2),
            get_one(client, url3),
        )
    return results

asyncio.run(main())
# total: about 1 second
```



## The three keywords


| Keyword         | Meaning                                                    |
| --------------- | ---------------------------------------------------------- |
| `async def`     | This function can pause and resume                         |
| `await`         | "Pause here, let something else run, come back when ready" |
| `asyncio.run()` | Start the whole async machine (from normal code)           |




## Rules

- You can only use `await` **inside** an `async def` function
- Calling an async function without `await` gives you a coroutine object, not a result:

```python
result = get_one(client, url)          # ❌ a coroutine object, not data
result = await get_one(client, url)    # ✅ actual data
```



## The big misconception

**Async is not threading, and it is not parallel processing.**

- Async = **one** worker, switching between tasks while they wait
- Threading = multiple workers

Think of one waiter serving five tables. While table 1 reads the menu, the waiter serves table 2.
One person, no idle time — but still only one person.

This means:

- ✅ Great for **waiting** work (network, files) — that's where the waiter switches tables
- ❌ Useless for **heavy calculation** — one worker is still one worker



## For testing

`pytest-asyncio` lets you write async tests:

```python
@pytest.mark.asyncio
async def test_get_task():
    async with httpx.AsyncClient() as client:
        r = await client.get("/task/abc")
    assert r.status_code == 200
```

Reach for this only when you genuinely need many concurrent calls. Plain `requests` is simpler and
fine for most API tests.

---



# 15. Threading, multiprocessing, GIL 🟢

**Interview trivia only.** Learn the paragraph. You will not build this yourself.

## The GIL

The **Global Interpreter Lock** means only one thread can run Python code at a time, even on a
multi-core CPU.

## The three options


| Approach            | Good for                 | Real parallelism?                                            |
| ------------------- | ------------------------ | ------------------------------------------------------------ |
| **Threading**       | Waiting on network/files | No (GIL) — but still helps, since waiting threads release it |
| **Multiprocessing** | Heavy calculation        | Yes — separate processes, separate GILs                      |
| **Async**           | Waiting on network/files | No — one thread, switching                                   |




## Interview answer

*"The GIL means only one thread executes Python bytecode at a time, so threading doesn't speed up
CPU-heavy work. It still helps for I/O-bound work because a thread releases the GIL while waiting.
For real CPU parallelism you use multiprocessing, which runs separate processes."*

## The misconception

**"The GIL means Python can't do parallel work"** — false. Multiprocessing gives genuine
parallelism, and threading still helps for I/O-bound work.

## For testing

You use `pytest-xdist`:

```bash
pytest -n 4        # run tests across 4 workers
```

It handles everything. Never hand-roll threads for test parallelism.

---



# Quick-fire differentiation table

Common interview "X vs Y" questions, all in one place.


| Question                              | Answer                                                                              |
| ------------------------------------- | ----------------------------------------------------------------------------------- |
| list vs tuple                         | List is mutable; tuple is immutable and can be a dict key                           |
| Is `{}` a dict or a set?              | **Dict.** Colon inside = dict, no colon = set, empty = dict. Empty set is `set()`   |
| What makes a tuple?                   | The **comma**, not the brackets — `("x")` is a string, `("x",)` is a tuple          |
| list vs set for lookups               | `in` on a set is instant; `in` on a list scans every item                           |
| `[]` after a name vs alone            | Attached = index/key lookup; standing alone = new list                              |
| `is` vs `==`                          | `is` = same object in memory; `==` = same value                                     |
| Shallow vs deep copy                  | Shallow copies the outer object only; deep copies every nested level                |
| `*args` vs `**kwargs`                 | Extra positional → tuple; extra named → dict                                        |
| `*` in definition vs in call          | Definition collects; call spreads                                                   |
| `return` vs `yield`                   | `return` ends the function; `yield` pauses it                                       |
| Generator vs iterator                 | Every generator is an iterator; generators are made with `yield` and are single-use |
| Async vs threading                    | Async = one thread switching while waiting; threading = multiple threads            |
| Threading vs multiprocessing          | Threading for I/O-bound; multiprocessing for CPU-bound (real parallelism)           |
| Dataclass vs Pydantic                 | Dataclass doesn't validate types; Pydantic validates at runtime                     |
| Decorator vs inheritance              | Decorator wraps a function; inheritance extends a class                             |
| `with` vs `try/finally`               | Same guarantee; `with` is cleaner and reusable                                      |
| Are type hints enforced?              | **No** — documentation only, unless you run `mypy`                                  |
| Does the GIL prevent parallelism?     | **No** — multiprocessing is truly parallel; threads still help I/O                  |
| Class vs instance attribute           | Class attribute is shared by all objects; instance attribute is per-object          |
| Bare `except:` vs `except Exception:` | Bare catches *everything* including your own typos — never use it                   |


---



# Practice checklist

Do these **without AI**. If you can't do one, that's the topic to go back to.

**Setup and debugging**

- [ ] Create a venv, install pytest into it, save a `requirements.txt`
- [ ] Read a real traceback out loud, bottom-up, explaining each frame
- [ ] Deliberately cause a `KeyError` and an `AttributeError`, then fix each

**Data and errors**

- [ ] Pull a nested value out of a fake API response dict
- [ ] Use `Counter` to count items in a list
- [ ] Write the same loop four ways — as a list, set, dict, and generator comprehension
- [ ] Open `agent-skills/airtap/scripts/airtap_common.py` and explain why `POLL_STOP_TASK_STATES`
  ```
  is a set and `parts` is a list
  ```
- [ ] Prove `{}` is a dict and not a set with `type({})`
- [ ] Write a custom exception and raise it with a useful message
- [ ] Write a `try/except/finally` where `finally` actually matters

**Functions and classes**

- [ ] Write a function using `*args` and `**kwargs` that prints both
- [ ] Write a class with `__init__`, one method, and a `__str__`
- [ ] Write a child class that overrides a parent method and calls `super()`

**The big two**

- [ ] Write a decorator that prints how long a function took to run
- [ ] Add `functools.wraps` to it and confirm `__name__` is correct
- [ ] Write a `@contextmanager` that prints "open" and "close" around a block
- [ ] Make it still print "close" when the code inside raises an error

**Gotchas**

- [ ] Cause a shallow-copy bug on purpose, then fix it with `deepcopy`
- [ ] Demonstrate the mutable default argument trap, then fix it
- [ ] Write a generator that yields lines from a file, and prove it's single-use

**Optional (P2)**

- [ ] Write an async function that fetches 3 URLs with `asyncio.gather`