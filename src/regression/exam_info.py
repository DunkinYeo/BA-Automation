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

_CONFIRM_BTN    = ["확인", "Confirm", "OK"]
_EXAM_TEXT      = ["검사 시작", "Start Study"]
_INFO_SCREEN    = ["검사 정보 확인", "Study Information Confirmation", "대상 ID", "이름"]
_CHECKBOX_DESC  = ["확인했습니다.", "I confirm", "Confirmed", "All information is correct."]


def _wait_for_info_screen(drv, timeout: int = 60) -> bool:
    """INFO 화면 진입 대기 (BLE 연결 시간 포함)."""
    return drv.is_visible_text(_INFO_SCREEN, timeout=timeout)


def _tap_checkbox(drv) -> bool:
    """INFO 화면 체크박스 탭 — content-desc 기반 커스텀 컴포넌트."""
    # 1) content-desc 로 찾기
    for desc in _CHECKBOX_DESC:
        try:
            els = drv.drv.find_elements(By.XPATH, f'//*[@content-desc="{desc}"]')
            if els:
                els[0].click()
                time.sleep(0.4)
                return True
        except Exception:
            pass
    # 2) 표준 CheckBox fallback
    try:
        cbs = drv.drv.find_elements(By.CLASS_NAME, "android.widget.CheckBox")
        if cbs:
            for cb in cbs:
                if cb.get_attribute("checked") != "true":
                    cb.click()
                    time.sleep(0.3)
            return True
    except Exception:
        pass
    return False


def _is_confirm_enabled(drv) -> bool:
    """확인 버튼 활성화 여부 — clickable 속성 기준."""
    for text in _CONFIRM_BTN:
        try:
            els = drv.drv.find_elements(By.XPATH, f'//*[@content-desc="{text}"]')
            if els:
                val = els[0].get_attribute("enabled")
                return val == "true"
            els2 = drv.drv.find_elements(By.XPATH, f'//*[@text="{text}"]')
            if els2:
                val = els2[0].get_attribute("enabled")
                return val == "true"
        except Exception:
            pass
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
    # INFO 화면 최초 진입 시 체크박스는 미체크 상태여야 함
    # clickable/enabled 속성으로 판단 (React Native 앱 특성상 enabled=true일 수 있어 SKIP 허용)
    enabled = _is_confirm_enabled(drv)
    if enabled is None:
        runner.skip("확인 버튼 상태 감지 불가")
    runner.assert_false(enabled, "체크박스 미체크 상태에서 '확인'이 활성화됨")


def test_info_004_checkbox_confirm_flow(drv, runner):
    """TC-INFO-004 | 체크박스 체크 + '확인' 클릭 → 검사 화면 이동"""
    # 체크박스 탭 (content-desc="확인했습니다." 기반)
    checked = _tap_checkbox(drv)
    if not checked:
        log.warning("TC-INFO-004: 체크박스를 찾지 못함 — '확인' 버튼 직접 탭 시도")
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
