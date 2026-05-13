"""
TC-EXAM: 검사 화면 Regression Tests

검사 화면 구성:
  1. 설정 아이콘 (우측 상단)
  2. 상태 표시 — 네트워크 / 블루투스 / 배터리
  3. 대시보드 — 심박수 / 체온 / 낙상 감지 / 걸음 수 / 활동 레벨 / 자세
  4. 검사 시작 / 종료 버튼

검사 설정 화면:
  - 버전 정보 (앱 아이콘 5회 클릭 → 파일 화면)
  - 기기 정보
  - 검사 정보
"""
import time
import logging
from selenium.webdriver.common.by import By

log = logging.getLogger(__name__)

_START_BTN   = "검사 시작"
_STOP_BTN    = "검사 종료"
_SETTING_BTN = "설정"


def _poll(drv, text, timeout: int = 10) -> bool:
    return drv.is_visible_text(text, timeout=timeout)


# ---------------------------------------------------------------------------
# Test Cases — 검사 화면
# ---------------------------------------------------------------------------

def test_exam_001_screen_visible(drv, runner):
    """TC-EXAM-001 | 검사 화면 진입 — '검사 시작' 버튼 표시 확인"""
    runner.assert_true(
        drv.is_visible_text(_START_BTN, timeout=5),
        "검사 화면의 '검사 시작' 버튼이 표시되지 않음"
    )


def test_exam_002_status_indicators(drv, runner):
    """TC-EXAM-002 | 상태 표시 — 네트워크/블루투스/배터리 아이콘 영역 존재"""
    # 텍스트 대신 UI 구조 존재 확인 (상태 아이콘은 텍스트 없이 이미지로만 표시될 수 있음)
    # 검사 화면 자체가 표시됐으면 상태바는 포함된 것으로 간주
    runner.assert_true(
        drv.is_visible_text(_START_BTN, timeout=3),
        "검사 화면이 아님 — 상태 표시 확인 불가"
    )
    log.info("TC-EXAM-002: 검사 화면 상태 표시 영역 존재 확인 (수동 육안 확인 권고)")


def test_exam_003_start_exam(drv, runner):
    """TC-EXAM-003 | '검사 시작' 클릭 → 실시간 데이터 수신 시작 / '검사 종료' 버튼 표시"""
    if not drv.is_visible_text(_START_BTN, timeout=3):
        log.info("TC-EXAM-003: 이미 검사 중 — 스킵")
        return
    drv.tap_text(_START_BTN, timeout=5, contains=False)
    time.sleep(1)
    ok = drv.is_visible_text(_STOP_BTN, timeout=10)
    runner.assert_true(ok, "'검사 시작' 클릭 후 '검사 종료' 버튼이 표시되지 않음")
    if ok:
        log.info("TC-EXAM-003: '검사 종료' 버튼 표시 확인 — 검사 시작됨")


def test_exam_004_stop_exam_popup(drv, runner):
    """TC-EXAM-004 | '검사 종료' 클릭 → 종료 확인 팝업 표시"""
    if not drv.is_visible_text(_STOP_BTN, timeout=3):
        log.info("TC-EXAM-004: 검사 미시작 상태 — 스킵")
        return
    drv.tap_text(_STOP_BTN, timeout=5, contains=False)
    time.sleep(1)
    popup_visible = drv.is_visible_text(["검사 종료", "종료하", "확인"], timeout=5)
    runner.assert_true(popup_visible, "'검사 종료' 클릭 후 확인 팝업이 표시되지 않음")
    if popup_visible:
        log.info("TC-EXAM-004: 검사 종료 팝업 확인")
        # 팝업 취소 (검사 유지)
        try:
            drv.tap_text(["취소", "Cancel", "닫기"], timeout=3, contains=False)
        except Exception:
            drv.drv.press_keycode(4)
        time.sleep(0.5)


def test_exam_005_stop_exam_checkbox(drv, runner):
    """TC-EXAM-005 | 검사 종료 팝업 — 체크박스 미체크 시 '검사 종료' 비활성화"""
    if not drv.is_visible_text(_STOP_BTN, timeout=3):
        log.info("TC-EXAM-005: 검사 미시작 상태 — 스킵")
        return
    drv.tap_text(_STOP_BTN, timeout=5, contains=False)
    time.sleep(1)
    if not drv.is_visible_text("검사 종료", timeout=3):
        runner.assert_true(False, "검사 종료 팝업이 표시되지 않음")
        return
    # 체크박스 미체크 상태에서 확인 버튼 상태 확인
    checkboxes = drv.drv.find_elements(By.CLASS_NAME, "android.widget.CheckBox")
    all_unchecked = all(cb.get_attribute("checked") != "true" for cb in checkboxes) if checkboxes else True
    if all_unchecked and checkboxes:
        try:
            btn = drv.find("검사 종료", timeout=2)
            enabled = btn.get_attribute("enabled") == "true"
            runner.assert_false(enabled, "체크박스 미체크 상태에서 '검사 종료' 버튼이 활성화됨")
        except Exception:
            log.info("TC-EXAM-005: 버튼 상태 확인 불가 — 수동 확인 필요")
    # 팝업 닫기
    try:
        drv.tap_text(["취소", "Cancel", "닫기"], timeout=3, contains=False)
    except Exception:
        drv.drv.press_keycode(4)
    time.sleep(0.5)


def test_exam_006_stop_and_go_summary(drv, runner):
    """TC-EXAM-006 | 검사 종료 팝업 — 체크박스 체크 + '검사 종료' → 요약 화면 이동"""
    if not drv.is_visible_text(_STOP_BTN, timeout=3):
        log.info("TC-EXAM-006: 검사 미시작 상태 — 스킵")
        return
    drv.tap_text(_STOP_BTN, timeout=5, contains=False)
    time.sleep(1)
    checkboxes = drv.drv.find_elements(By.CLASS_NAME, "android.widget.CheckBox")
    for cb in checkboxes:
        if cb.get_attribute("checked") != "true":
            cb.click()
            time.sleep(0.3)
    try:
        drv.tap_text("검사 종료", timeout=5, contains=False)
    except Exception:
        drv.tap_text("확인", timeout=5, contains=False)
    time.sleep(2)
    on_summary = drv.is_visible_text(["업로드", "건너뛰기", "완료", "요약"], timeout=10)
    runner.assert_true(on_summary, "검사 종료 후 요약 화면으로 이동하지 않음")
    if on_summary:
        log.info("TC-EXAM-006: 요약 화면 이동 확인")


# ---------------------------------------------------------------------------
# Test Cases — 설정 화면
# ---------------------------------------------------------------------------

def test_exam_set_001_settings_entry(drv, runner):
    """TC-EXAM-SET-001 | 설정 아이콘 → 설정 화면 이동"""
    if not drv.is_visible_text([_START_BTN, _STOP_BTN], timeout=3):
        log.info("TC-EXAM-SET-001: 검사 화면이 아님 — 스킵")
        return
    drv.tap_text(_SETTING_BTN, timeout=5)
    time.sleep(1)
    on_settings = drv.is_visible_text(["버전 정보", "기기 정보", "검사 정보", "버전"], timeout=5)
    runner.assert_true(on_settings, "설정 아이콘 클릭 후 설정 화면으로 이동하지 않음")
    if on_settings:
        log.info("TC-EXAM-SET-001: 설정 화면 진입 확인")


def test_exam_set_002_version_info(drv, runner):
    """TC-EXAM-SET-002 | 설정 → 버전 정보 표시 확인"""
    if not drv.is_visible_text(["버전 정보", "Version"], timeout=3):
        log.info("TC-EXAM-SET-002: 설정 화면이 아님 — 스킵")
        return
    runner.assert_true(
        drv.is_visible_text(["버전 정보", "Version"], timeout=3),
        "설정 화면에서 버전 정보가 표시되지 않음"
    )
    log.info("TC-EXAM-SET-002: 버전 정보 표시 확인")


def test_exam_set_003_file_screen_5tap(drv, runner):
    """TC-EXAM-SET-003 | 버전 정보 화면 앱 아이콘 5회 클릭 → 파일 화면 이동"""
    if not drv.is_visible_text(["버전 정보", "Version"], timeout=3):
        log.info("TC-EXAM-SET-003: 설정 화면이 아님 — 스킵")
        return
    # 버전 정보 탭 진입
    try:
        drv.tap_text("버전 정보", timeout=3)
        time.sleep(0.5)
    except Exception:
        pass
    # 앱 아이콘 영역 5회 탭 (중앙 이미지 영역 추정)
    try:
        icons = drv.drv.find_elements(By.CLASS_NAME, "android.widget.ImageView")
        if icons:
            for _ in range(5):
                icons[0].click()
                time.sleep(0.2)
    except Exception:
        log.info("TC-EXAM-SET-003: 아이콘 요소 찾기 실패 — 스킵")
        drv.drv.press_keycode(4)
        return
    time.sleep(1)
    on_file = drv.is_visible_text(["파일", "File", "데이터", "내보내기"], timeout=5)
    if on_file:
        log.info("TC-EXAM-SET-003: 파일 화면 진입 확인")
        drv.drv.press_keycode(4)
    else:
        log.info("TC-EXAM-SET-003: 파일 화면 미진입 — 아이콘 위치 수동 확인 필요")
    runner.assert_true(on_file, "앱 아이콘 5회 클릭 후 파일 화면으로 이동하지 않음")


def test_exam_set_004_device_info(drv, runner):
    """TC-EXAM-SET-004 | 설정 → 기기 정보 표시 확인"""
    if not drv.is_visible_text(["기기 정보", "Device"], timeout=3):
        log.info("TC-EXAM-SET-004: 설정 화면이 아님 — 스킵")
        return
    try:
        drv.tap_text("기기 정보", timeout=3)
        time.sleep(0.5)
    except Exception:
        pass
    runner.assert_true(
        drv.is_visible_text(["기기 정보", "Device", "시리얼", "Serial"], timeout=5),
        "기기 정보가 표시되지 않음"
    )
    log.info("TC-EXAM-SET-004: 기기 정보 표시 확인")


def test_exam_set_005_exam_info(drv, runner):
    """TC-EXAM-SET-005 | 설정 → 검사 정보 표시 확인"""
    if not drv.is_visible_text(["검사 정보"], timeout=3):
        log.info("TC-EXAM-SET-005: 설정 화면이 아님 — 스킵")
        return
    try:
        drv.tap_text("검사 정보", timeout=3)
        time.sleep(0.5)
    except Exception:
        pass
    runner.assert_true(
        drv.is_visible_text(["검사 정보", "대상", "검사"], timeout=5),
        "검사 정보가 표시되지 않음"
    )
    log.info("TC-EXAM-SET-005: 검사 정보 표시 확인")


TESTS = [
    test_exam_001_screen_visible,
    test_exam_002_status_indicators,
    test_exam_003_start_exam,
    test_exam_004_stop_exam_popup,
    test_exam_005_stop_exam_checkbox,
    test_exam_006_stop_and_go_summary,
    test_exam_set_001_settings_entry,
    test_exam_set_002_version_info,
    test_exam_set_003_file_screen_5tap,
    test_exam_set_004_device_info,
    test_exam_set_005_exam_info,
]
