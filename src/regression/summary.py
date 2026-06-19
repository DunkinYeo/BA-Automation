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

_COMPLETE_BTN = ["완료", "Done", "Complete"]
_UPLOAD_BTN   = ["업로드", "Upload"]
_SKIP_BTN     = ["건너뛰기", "Skip"]
_LOGIN_TEXT   = ["연결하기", "Connect", "Connect Your Device", "기기 연결하기"]

_SUMMARY_INDICATORS = ["진행률", "Progress", "시작 시간", "Start Time",
                       "종료 시간", "End Time", "검사 정보", "Study Information"]

_SKIP_CB_DESCS = ["건너뛰겠습니다.", "I want to skip upload.", "I confirm skip"]
_ALL_SUMMARY   = _SUMMARY_INDICATORS + _COMPLETE_BTN + _UPLOAD_BTN + _SKIP_BTN


def _on_summary(drv) -> bool:
    return drv.is_visible_text(_ALL_SUMMARY, timeout=5)


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

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
        runner.skip("Skip 버튼 없음 — 데이터 정상 업로드 완료 상태")
    drv.tap_text(_SKIP_BTN, timeout=5, contains=False)
    time.sleep(1)
    popup_visible = drv.is_visible_text(_SKIP_BTN + ["중단", "확인", "체크", "Confirm", "Cancel"], timeout=5)
    runner.assert_true(popup_visible, "'건너뛰기/Skip' 클릭 후 확인 팝업이 표시되지 않음")
    if popup_visible:
        log.info("TC-SUMMARY-006: 건너뛰기 팝업 확인")
        try:
            drv.tap_text(["취소", "Cancel", "닫기"], timeout=3, contains=False)
        except Exception:
            drv.drv.press_keycode(4)
        time.sleep(0.5)


def test_summary_007_skip_confirm(drv, runner):
    """TC-SUMMARY-007 | 건너뛰기 팝업 — 체크박스 체크 + '건너뛰기' → 로그인 화면 이동"""
    if not drv.is_visible_text(_SKIP_BTN, timeout=3):
        runner.skip("Skip 버튼 없음 — 데이터 정상 업로드 완료 상태")
    drv.tap_text(_SKIP_BTN, timeout=5, contains=False)
    time.sleep(1)
    import re
    try:
        src = drv.drv.page_source
        texts = [t for t in re.findall(r'(?:text|content-desc)="([^"]+)"', src) if t.strip()]
        log.info("TC-SUMMARY-007 팝업 텍스트: %s", texts)
    except Exception:
        pass
    try:
        drv.screenshot("summary_007_skip_popup")
    except Exception:
        pass
    tapped = False
    for desc in _SKIP_CB_DESCS:
        try:
            els = drv.drv.find_elements(By.XPATH, f'//*[@content-desc="{desc}"]')
            if els:
                els[0].click()
                time.sleep(0.3)
                tapped = True
                break
        except Exception:
            pass
    if not tapped:
        try:
            checkboxes = drv.drv.find_elements(By.CLASS_NAME, "android.widget.CheckBox")
            for cb in checkboxes:
                if cb.get_attribute("checked") != "true":
                    cb.click()
                    time.sleep(0.3)
        except Exception:
            pass
    # 건너뛰기 팝업 확인 버튼: "Yes, Skip" (실제 앱 텍스트)
    confirmed = False
    for btn in ["Yes, Skip"]:
        try:
            els = drv.drv.find_elements(By.XPATH, f'//*[@content-desc="{btn}"]')
            if els:
                els[-1].click()
                confirmed = True
                break
        except Exception:
            pass
    if not confirmed:
        try:
            drv.tap_text(["Yes, Skip", "건너뛰기", "Skip", "확인", "OK"], timeout=5, contains=False)
        except Exception:
            pass
    time.sleep(2)
    on_login = drv.is_visible_text(_LOGIN_TEXT, timeout=10)
    runner.assert_true(on_login, "건너뛰기 확정 후 로그인 화면으로 이동하지 않음")
    if on_login:
        log.info("TC-SUMMARY-007: 로그인 화면 복귀 확인")


def test_summary_003_complete_to_login(drv, runner):
    """TC-SUMMARY-003 | '완료' 버튼 클릭 → 로그인 화면 이동"""
    if not drv.is_visible_text(_COMPLETE_BTN, timeout=3):
        runner.skip("Done 버튼 없음 — 데이터 미완료, Upload/Skip 버튼 상태")
    drv.tap_text(_COMPLETE_BTN, timeout=5, contains=False)
    time.sleep(2)
    on_login = drv.is_visible_text(_LOGIN_TEXT, timeout=10)
    runner.assert_true(on_login, "'완료/Done' 클릭 후 로그인 화면으로 이동하지 않음")
    if on_login:
        log.info("TC-SUMMARY-003: 로그인 화면 복귀 확인")


TESTS = [
    test_summary_002_button_state,
    test_summary_006_skip_popup,
    test_summary_007_skip_confirm,
    test_summary_003_complete_to_login,
]
