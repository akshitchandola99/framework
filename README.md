# Testing Framework Structure

```text
airtap-pw-suite/
├── pytest.ini
├── requirements.txt
├── .env.example
├── conftest.py                      # ROOT: browser/context, base_url, env config, storage_state loader
│
├── config/
│   └── settings.py                  # base URLs, timeouts, env-driven config
│
├── test_data/                       # committed test files (never machine-local paths)
│   ├── sample.jpg
│   ├── sample.png
│   ├── sample.pdf
│   └── sample.xlsx
│
├── pages/                           # Page Object Model — one class per screen
│   ├── base_page.py
│   ├── login_page.py
│   ├── cloudphone_page.py
│   ├── task_composer_page.py
│   ├── recent_tasks_page.py
│   ├── routines_page.py
│   ├── pairing_page.py
│   ├── settings_page.py
│   └── linq_page.py
│
└── tests/
    ├── auth/
    │   ├── conftest.py              # unauthenticated context fixture (for login/logout flows)
    │   └── test_auth.py             # AUTH-01 (google login → storage_state), AUTH-05, AUTH-06, AUTH-07, AUTH-08
    │
    ├── cloudphone/
    │   ├── conftest.py              # authed context + cloudphone-open fixture (shared by all CP-* tests)
    │   ├── test_stream.py           # CP-01, CP-03  (getStats() assertions)
    │   ├── test_lifecycle.py        # CP-02 (stays closed + persists)
    │   ├── test_input.py            # CP-04 (effect-based assertion)
    │   ├── test_audio.py            # CP-06 (mute/unmute)
    │   └── test_resiliency.py       # CP-09 (offline/online simulation)
    │
    ├── tasks/
    │   ├── conftest.py              # authed session + task cleanup/teardown fixture
    │   ├── test_task_execution.py   # TASK-01 (Cloudphone run, API poll)
    │   ├── test_task_image.py       # TASK-02 (set_input_files)
    │   ├── test_task_followup.py    # TASK-03
    │   ├── test_task_model_switch.py# TASK-04
    │   ├── test_task_stop.py        # TASK-06
    │   ├── test_task_recent.py      # TASK-09, TASK-10
    │   ├── test_task_validation.py  # TASK-11 (empty/whitespace prompt)
    │   └── test_task_deeplink.py    # TASK-14
    │
    ├── routines/
    │   ├── conftest.py              # routine teardown fixture (built on RTN-12 delete)
    │   ├── test_routine_create.py   # RTN-01, RTN-02
    │   ├── test_routine_schedule.py # RTN-03 (parametrised daily/weekly/monthly), RTN-15
    │   ├── test_routine_toggle.py   # RTN-06, RTN-07
    │   ├── test_routine_run_now.py  # RTN-09
    │   ├── test_routine_edit.py     # RTN-14, RTN-12 (delete)
    │   ├── test_routine_device_model.py # RTN-04, RTN-05
    │   ├── test_routine_history.py  # RTN-10, RTN-11
    │   └── test_routine_persistence.py # RTN-20
    │
    ├── pairing/
    │   ├── conftest.py              # paired-device fixture
    │   ├── test_pairing_entry.py    # PAIR-01
    │   ├── test_apk_download.py     # PAIR-02
    │   ├── test_device_list.py      # PAIR-04
    │   └── test_device_switch.py    # PAIR-05
    │
    ├── settings/
    │   ├── conftest.py              # authed settings-page fixture
    │   ├── test_support_ticket.py   # SET-01
    │   ├── test_location.py         # SET-04, SET-12
    │   ├── test_pat_lifecycle.py    # SET-05
    │   ├── test_skills.py           # SET-07 (CRUD)
    │   ├── test_memory.py           # SET-06
    │   └── test_personalise.py      # SET-09
    │
    ├── search_share/
    │   ├── conftest.py              # seeded-task fixture
    │   ├── test_search.py           # SHARE-01
    │   └── test_share.py            # SHARE-02 (fresh context, no storage_state)
    │
    ├── linq/
    │   ├── conftest.py
    │   ├── test_task_link.py        # LINQ-13 (clean context)
    │   └── test_connected_status.py # LINQ-03
    │
    └── mobile/
        ├── conftest.py              # mobile device-descriptor context fixture
        ├── test_mobile_render.py    # MOB-04
        ├── test_mobile_task.py      # MOB-05
        ├── test_mobile_input.py     # MOB-01
        └── test_mobile_audio.py     # MOB-03
```


# Logging Mechanism
```
Using Python's <logging> <module> generate the logs,
and pytest's built-in <logging> <plugin> capture/display them.

- Each module gets its own logger via <logging.getLogger(__name__)> — no manual handler/formatter setup required anywhere.

- pytest's logging plugin automatically captures log records per test, attaches them to failure output, and can stream to console + write to a file, all via config in <pytest.ini> — zero extra code.

- Scales cleanly as pages/ and more tests/ are filled in later: any new module just grabs a logger and logs, no wiring needed.
```