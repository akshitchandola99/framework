from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
PROFILE_DIR = ROOT_DIR / "chrome-profile"
TEST_DATA_DIR = ROOT_DIR / "tests" / "tasks" / "test_data"

APP_URL = "https://airtap.ai/app"
TASK_URL_PATTERN = r"https://airtap.ai/app/t\?taskId=task-.*"

DEFAULT_TIMEOUT = 15_000
LONG_TIMEOUT = 30_000
FOLLOWUP_TIMEOUT = 60_000

SAMPLE_JPG = TEST_DATA_DIR / "sample.jpg"
SAMPLE_PNG = TEST_DATA_DIR / "sample.png"
SAMPLE_PDF = TEST_DATA_DIR / "sample.pdf"
SAMPLE_XLSX = TEST_DATA_DIR / "sample.xlsx"
