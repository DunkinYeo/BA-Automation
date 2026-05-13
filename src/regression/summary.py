"""
TC-SUMMARY: 요약 화면 Regression Tests

검사 종료 후 진입하는 요약 화면:
  - 완료: 데이터 전송 완료 → '완료' 버튼 → 로그인 화면
  - 업로드/건너뛰기: 데이터 누락 시 두 버튼 표시
  - 건너뛰기 팝업: 체크박스 + 건너뛰기 버튼 → 로그인 화면

자동화 가능 케이스:
  SUMMARY-001: 요약 화면 진입 확인
  SUMMARY-002: 완료 or 업로드/건너뛰기 버튼 중 하나 표시
  SUMMARY-003: 완료 → 로그인 이동
  SUMMARY-006: 건너뛰기 팝업 표시
  SUMMARY-007: 건너뛰기 확정 → 로그인 이동

수동 케이스:
  SUMMARY-004/005: 업로드 버튼 (데이터 누락 조건 재현 어려움)
"""
import time
import logging
from selenium.webdriver.common.by import By

log = logging.getLogger(__name__)

_COMPLETE_BTN  = "완료"
_UPLOAD_BTN    = "업로드"
_SKIP_BTN      = "건너뛰기"
_LOGIN_TEXT    = "연결하기"


def _on_summary(drv) -> bool:
    return drv.is_visible_text([_COMPLETE_BTN, _UPLOAD_BTN, _SKIP_BTN], timeout=5)


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_summary_001_screen_visible(drv, runner):
    """TC-SUMMARY-001 | 요약 화면 진입 — '완료' 또는 '업로드'/'건너뛰기' 버튼 표시"""
    runner.assert_true(_on_summary(drv), "요약 화면 버튼이 표시되지 않음 (완료/업로드/건너뛰기 중 하나 필요)")
    if drv.is_visible_text(_COMPLETE_BTN, timeout=2):
        log.info("TC-SUMMARY-001: '완료' 버튼 확인 (데이터 정상 전송)")
    elif drv.is_visible_text(_UPLOAD_BTN, timeout=2):
        log.info("TC-SUMMARY-001: '업로드'/'건너뛰기' 버튼 확인 (데이터 누락)")


def test_summary_002_button_state(drv, runner):
    """TC-SUMMARY-002 | 데이터 상태에 따라 완료 or 업로드/건너뛰기 표시"""
    has_complete = drv.is_visible_text(_COMPLETE_BTN, timeout=3)
    has_upload   = drv.is_visible_text(_UPLOAD_BTN, timeout=3)
    has_skip     = drv.is_visible_text(_SKIP_BTN, timeout=3)
    runner.assert_true(
        has_complete or has_upload or has_skip,
        "요약 화면에서 완료/업로드/건너뛰기 버튼이 모두 미표시"
    )
    log.info(
        "TC-SUMMARY-002: 완료=%s, 업로드=%s, 건너뛰기=%s",
        has_complete, has_upload, has_skip
    )


def test_summary_006_skip_popup(drv, runner):
    """TC-SUMMARY-006 | '건너뛰기' 클릭 → 확인 팝업 표시"""
    if not drv.is_visible_text(_SKIP_BTN, timeout=3):
        log.info("TC-SUMMARY-006: '건너뛰기' 버튼 없음 (완료 상태) — 스킵")
        return
    drv.tap_text(_SKIP_BTN, timeout=5, contains=False)
    time.sleep(1)
    popup_visible = drv.is_visible_text([_SKIP_BTN, "중단", "확인", "체크"], timeout=5)
    runner.assert_true(popup_visible, "'건너뛰기' 클릭 후 확인 팝업이 표시되지 않음")
    if popup_visible:
        log.info("TC-SUMMARY-006: 건너뛰기 팝업 확인")
        # 취소하여 요약 화면 유지 (test_summary_007에서 완료)
        try:
            drv.tap_text(["취소", "Cancel", "닫기"], timeout=3, contains=False)
        except Exception:
            drv.drv.press_keycode(4)
        time.sleep(0.5)


def test_summary_007_skip_confirm(drv, runner):
    """TC-SUMMARY-007 | 건너뛰기 팝업 — 체크박스 체크 + '건너뛰기' → 로그인 화면 이동"""
    if not drv.is_visible_text(_SKIP_BTN, timeout=3):
        log.info("TC-SUMMARY-007: '건너뛰기' 버튼 없음 (완료 상태) — 스킵")
        return
    drv.tap_text(_SKIP_BTN, timeout=5, contains=False)
    time.sleep(1)
    # 팝업에서 체크박스 체크
    checkboxes = drv.drv.find_elements(By.CLASS_NAME, "android.widget.CheckBox")
    for cb in checkboxes:
        if cb.get_attribute("checked") != "true":
            cb.click()
            time.sleep(0.3)
    try:
        drv.tap_text(_SKIP_BTN, timeout=5, contains=False)
    except Exception:
        drv.tap_text("확인", timeout=5, contains=False)
    time.sleep(2)
    on_login = drv.is_visible_text(_LOGIN_TEXT, timeout=10)
    runner.assert_true(on_login, "건너뛰기 확정 후 로그인 화면으로 이동하지 않음")
    if on_login:
        log.info("TC-SUMMARY-007: 로그인 화면 복귀 확인")


def test_summary_003_complete_to_login(drv, runner):
    """TC-SUMMARY-003 | '완료' 버튼 클릭 → 로그인 화면 이동"""
    if not drv.is_visible_text(_COMPLETE_BTN, timeout=3):
        log.info("TC-SUMMARY-003: '완료' 버튼 없음 (데이터 누락 상태) — 스킵")
        return
    drv.tap_text(_COMPLETE_BTN, timeout=5, contains=False)
    time.sleep(2)
    on_login = drv.is_visible_text(_LOGIN_TEXT, timeout=10)
    runner.assert_true(on_login, "'완료' 클릭 후 로그인 화면으로 이동하지 않음")
    if on_login:
        log.info("TC-SUMMARY-003: 로그인 화면 복귀 확인")


TESTS = [
    test_summary_001_screen_visible,
    test_summary_002_button_state,
    test_summary_006_skip_popup,
    test_summary_007_skip_confirm,
    test_summary_003_complete_to_login,
]
