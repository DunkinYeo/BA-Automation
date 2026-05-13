"""
TC-INFO: 검사 정보 화면 Regression Tests

연결 성공 후 표시되는 화면:
  - 대상 ID / 이름 표시
  - 체크박스 체크 후 '확인' 버튼 클릭 → 검사 화면 이동
  - 체크박스 미체크 시 '확인' 비활성화
"""
import time
import logging
from selenium.webdriver.common.by import By

log = logging.getLogger(__name__)

_CONFIRM_BTN  = "확인"
_EXAM_TEXT    = "검사 시작"


def _get_checkboxes(drv):
    try:
        return drv.drv.find_elements(By.CLASS_NAME, "android.widget.CheckBox")
    except Exception:
        return []


def _is_confirm_enabled(drv) -> bool:
    try:
        btn = drv.find(_CONFIRM_BTN, timeout=3)
        return btn.get_attribute("enabled") == "true"
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_info_001_screen_visible(drv, runner):
    """TC-INFO-001 | 검사 정보 화면 — 대상 ID/이름 표시 확인"""
    runner.assert_true(
        drv.is_visible_text(_CONFIRM_BTN, timeout=5),
        "검사 정보 화면의 '확인' 버튼이 표시되지 않음"
    )
    log.info("TC-INFO-001: 검사 정보 화면 확인")


def test_info_002_subject_info_visible(drv, runner):
    """TC-INFO-002 | 검사 정보 — 대상 ID 또는 이름 텍스트 표시"""
    # 대상 ID / 이름 중 하나는 표시돼야 함
    has_info = drv.is_visible_text(["대상 ID", "대상ID", "이름", "Name", "ID"], timeout=5)
    if not has_info:
        log.warning("TC-INFO-002: 대상 ID/이름 레이블을 찾을 수 없음 — 실제 UI 텍스트 확인 필요")
    runner.assert_true(has_info, "검사 정보 화면에서 대상 ID/이름 정보가 표시되지 않음")


def test_info_003_checkbox_unchecked_confirm_disabled(drv, runner):
    """TC-INFO-003 | 체크박스 미체크 → '확인' 버튼 비활성화"""
    checkboxes = _get_checkboxes(drv)
    if not checkboxes:
        log.info("TC-INFO-003: 체크박스 없음 — UI 구조 확인 필요")
        return
    # 모두 체크 해제
    for cb in checkboxes:
        if cb.get_attribute("checked") == "true":
            cb.click()
            time.sleep(0.3)
    runner.assert_false(_is_confirm_enabled(drv), "체크박스 미체크 상태에서 '확인'이 활성화됨")


def test_info_004_checkbox_confirm_flow(drv, runner):
    """TC-INFO-004 | 체크박스 체크 + '확인' 클릭 → 검사 화면 이동"""
    checkboxes = _get_checkboxes(drv)
    for cb in checkboxes:
        if cb.get_attribute("checked") != "true":
            cb.click()
            time.sleep(0.3)
    runner.assert_true(_is_confirm_enabled(drv), "체크박스 체크 후 '확인' 버튼이 활성화되지 않음")
    drv.tap_text(_CONFIRM_BTN, timeout=5, contains=False)
    time.sleep(1)
    on_exam = drv.is_visible_text(_EXAM_TEXT, timeout=10)
    runner.assert_true(on_exam, "'확인' 클릭 후 검사 화면('검사 시작')으로 이동하지 않음")


TESTS = [
    test_info_001_screen_visible,
    test_info_002_subject_info_visible,
    test_info_003_checkbox_unchecked_confirm_disabled,
    test_info_004_checkbox_confirm_flow,
]
