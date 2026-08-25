import logging
from playwright.sync_api import expect
from pages.base_page import BasePage
from pages.task_page import TaskPage
import pytest
from pathlib import Path

log = logging.getLogger(__name__)

FILE_PATH_IMG_JPG = Path(__file__).resolve().parent / "test_data" / "sample.jpg"
FILE_PATH_PDF = Path(__file__).resolve().parent / "test_data" / "sample.pdf"
FILE_PATH_IMG_PNG = Path(__file__).resolve().parent / "test_data" / "sample.png"
FILR_PATH_XLSX = Path(__file__).resolve().parent / "test_data" / "sample.xlsx"

@pytest.mark.order(8)
def test_task_attachments(page):
    log.info("Starting a new task with attachments")
    bp = BasePage(page)
    bp.create_new_task()

    bp.attach_files([FILE_PATH_IMG_JPG,FILE_PATH_PDF,FILE_PATH_IMG_PNG,FILR_PATH_XLSX])
    bp.enter_task(task="what type of files are these")
    log.info("Waiting for invalid attachment message")
    expect(bp.attachment_invalid_msg).to_be_visible()
    bp.submit_task()

    tp = TaskPage(page)
    log.info("Waiting for task completion")
    expect(tp.task_completed_txt).to_be_visible(timeout=30_000)
    log.info("Task with attachments completed")






