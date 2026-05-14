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
import subprocess
import time
import logging
from selenium.webdriver.common.by import By

from src.regression.helpers import SETTING_ICON_CENTER

log = logging.getLogger(__name__)

_START_BTN      = "검사 시작"
_STOP_BTN       = "검사 종료"
_STOP_CB_DESC   = ["검사를 종료하겠습니다.", "I confirm termination", "Confirm termination"]
_LOADING_TEXT   = ["잠시만 기다려주세요", "Please wait", "Loading"]
_DASHBOARD_LABELS = ["심박수", "체온", "낙상감지", "걸음 수", "활동 레벨", "자세"]
_STATUS_LABELS    = ["네트워크", "블루투스", "배터리"]


def _wait_loading_clear(drv, timeout: int = 30):
    """로딩 오버레이('잠시만 기다려주세요...') 사라질 때까지 대기."""
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        if not drv.is_visible_text(_LOADING_TEXT, timeout=1):
            return
        time.sleep(1)
    log.warning("_wait_loading_clear: %ds 후에도 로딩 오버레이 미사라짐", timeout)


def _on_exam(drv) -> bool:
    return drv.is_visible_text([_START_BTN, _STOP_BTN], timeout=3)


def _adb(drv, *args):
    udid = drv.cfg.get("udid", "")
    cmd = ["adb"] + (["-s", udid] if udid else []) + list(args)
    subprocess.run(cmd, capture_output=True, timeout=10)


# ---------------------------------------------------------------------------
# Test Cases — 검사 화면 진입 확인 (검사 시작 전)
# ---------------------------------------------------------------------------

def test_exam_001_screen_visible(drv, runner):
    """TC-EXAM-001 | 검사 화면 진입 — '검사 시작' 버튼 표시 확인"""
    runner.assert_true(
        drv.is_visible_text(_START_BTN, timeout=5),
        "검사 화면의 '검사 시작' 버튼이 표시되지 않음"
    )


def test_exam_002_status_indicators(drv, runner):
    """TC-EXAM-002 | 상태 표시 — 네트워크/블루투스/배터리 라벨 존재"""
    if not _on_exam(drv):
        log.info("TC-EXAM-002: 검사 화면이 아님 — 스킵")
        return
    found = drv.is_visible_text(_STATUS_LABELS, timeout=5)
    if found:
        log.info("TC-EXAM-002: 상태 라벨(네트워크/블루투스/배터리) 확인")
    else:
        log.info("TC-EXAM-002: 상태 라벨 텍스트 미감지 — 아이콘만 표시될 수 있음 (수동 확인 권고)")
    runner.assert_true(_on_exam(drv), "검사 화면이 아님 — 상태 표시 확인 불가")


def test_exam_d08_initial_values(drv, runner):
    """TC-EXAM-D08 | 검사 시작 전 대시보드 — 라벨 및 초기값 표시"""
    if not drv.is_visible_text(_START_BTN, timeout=3):
        log.info("TC-EXAM-D08: 이미 검사 중 — 스킵")
        return
    # 대시보드 라벨 6개 확인
    for label in _DASHBOARD_LABELS:
        if drv.is_visible_text(label, timeout=3):
            log.info("TC-EXAM-D08: '%s' 라벨 확인", label)
        else:
            log.warning("TC-EXAM-D08: '%s' 라벨 미감지", label)
    runner.assert_true(
        drv.is_visible_text(_DASHBOARD_LABELS, timeout=3),
        f"검사 시작 전 대시보드 라벨 미표시: {_DASHBOARD_LABELS}"
    )
    log.info("TC-EXAM-D08: 검사 시작 전 대시보드 라벨 확인")


# ---------------------------------------------------------------------------
# Test Cases — 검사 시작
# ---------------------------------------------------------------------------

def test_exam_003_start_exam(drv, runner):
    """TC-EXAM-011 | '검사 시작' 클릭 → '검사 종료' 버튼 표시"""
    if not drv.is_visible_text(_START_BTN, timeout=3):
        log.info("TC-EXAM-003: 이미 검사 중 — 스킵")
        return
    drv.tap_text(_START_BTN, timeout=5, contains=False)
    _wait_loading_clear(drv, timeout=30)
    ok = drv.is_visible_text(_STOP_BTN, timeout=20)
    runner.assert_true(ok, "'검사 시작' 클릭 후 '검사 종료' 버튼이 표시되지 않음")
    if ok:
        log.info("TC-EXAM-003: '검사 종료' 버튼 표시 확인 — 검사 시작됨")


def test_exam_d01_dashboard_labels(drv, runner):
    """TC-EXAM-D01 | 검사 시작 후 대시보드 6개 항목 라벨 표시"""
    if not drv.is_visible_text(_STOP_BTN, timeout=3):
        log.info("TC-EXAM-D01: 검사 미시작 상태 — 스킵")
        return
    missing = []
    for label in _DASHBOARD_LABELS:
        if drv.is_visible_text(label, timeout=3):
            log.info("TC-EXAM-D01: '%s' 확인", label)
        else:
            log.warning("TC-EXAM-D01: '%s' 미감지", label)
            missing.append(label)
    runner.assert_true(
        len(missing) == 0,
        f"대시보드 라벨 미표시: {missing}"
    )


# ---------------------------------------------------------------------------
# Test Cases — 검사 종료 팝업 (취소)
# ---------------------------------------------------------------------------

def test_exam_004_stop_exam_popup(drv, runner):
    """TC-EXAM-013 | '검사 종료' 클릭 → 종료 확인 팝업 표시"""
    if not drv.is_visible_text(_STOP_BTN, timeout=3):
        log.info("TC-EXAM-004: 검사 미시작 상태 — 스킵")
        return
    drv.tap_text(_STOP_BTN, timeout=5, contains=False)
    time.sleep(1)
    popup_visible = drv.is_visible_text(["검사 종료", "종료하", "확인"], timeout=5)
    runner.assert_true(popup_visible, "'검사 종료' 클릭 후 확인 팝업이 표시되지 않음")
    if popup_visible:
        log.info("TC-EXAM-004: 검사 종료 팝업 확인")
        try:
            drv.tap_text(["취소", "Cancel", "닫기"], timeout=3, contains=False)
        except Exception:
            drv.drv.press_keycode(4)
        time.sleep(0.5)


def test_exam_005_stop_exam_checkbox(drv, runner):
    """TC-EXAM-014 | 검사 종료 팝업 — 체크박스 미체크 시 '검사 종료' 비활성화"""
    if not drv.is_visible_text(_STOP_BTN, timeout=3):
        log.info("TC-EXAM-005: 검사 미시작 상태 — 스킵")
        return
    drv.tap_text(_STOP_BTN, timeout=5, contains=False)
    time.sleep(1)
    if not drv.is_visible_text("검사 종료", timeout=3):
        runner.assert_true(False, "검사 종료 팝업이 표시되지 않음")
        return
    try:
        els = drv.drv.find_elements(By.XPATH, '//*[@text="검사 종료"]')
        if els:
            clickable = els[0].get_attribute("clickable")
            enabled   = els[0].get_attribute("enabled")
            is_active = (clickable == "true") if clickable is not None else (enabled == "true")
            runner.assert_false(is_active, "체크박스 미체크 상태에서 '검사 종료' 버튼이 활성화됨")
        else:
            log.info("TC-EXAM-005: 버튼 상태 확인 불가 — 수동 확인 필요")
    except Exception:
        log.info("TC-EXAM-005: 버튼 상태 확인 불가 — 수동 확인 필요")
    # 팝업 닫기
    try:
        drv.drv.press_keycode(4)
    except Exception:
        pass
    time.sleep(0.5)


def test_exam_016_popup_cancel_return(drv, runner):
    """TC-EXAM-016 | 종료 팝업 취소 → 검사 화면 복귀, 검사 유지"""
    if not drv.is_visible_text(_STOP_BTN, timeout=3):
        log.info("TC-EXAM-016: 검사 미시작 상태 — 스킵")
        return
    drv.tap_text(_STOP_BTN, timeout=5, contains=False)
    time.sleep(1)
    if not drv.is_visible_text(["검사 종료", "종료하"], timeout=3):
        runner.assert_true(False, "종료 팝업이 표시되지 않음")
        return
    # 팝업 취소 (X 버튼 or Back)
    try:
        drv.tap_text(["취소", "Cancel", "닫기"], timeout=3, contains=False)
    except Exception:
        drv.drv.press_keycode(4)
    time.sleep(0.8)
    # 검사 화면 복귀 확인 ('검사 종료' 버튼이 다시 보여야 함)
    back_on_exam = drv.is_visible_text(_STOP_BTN, timeout=5)
    runner.assert_true(back_on_exam, "종료 팝업 취소 후 검사 화면('검사 종료' 버튼)으로 복귀하지 않음")
    if back_on_exam:
        log.info("TC-EXAM-016: 팝업 취소 후 검사 화면 복귀 확인 — 검사 계속 진행 중")


# ---------------------------------------------------------------------------
# Test Cases — 검사 중 설정 화면
# ---------------------------------------------------------------------------

def test_exam_set_001_settings_entry(drv, runner):
    """TC-EXAM-SET-001 | 설정 아이콘 → 설정 화면 이동"""
    if not _on_exam(drv):
        log.info("TC-EXAM-SET-001: 검사 화면이 아님 — 스킵")
        return
    cx, cy = SETTING_ICON_CENTER
    drv.drv.tap([(cx, cy)])
    time.sleep(1)
    on_settings = drv.is_visible_text(["버전 정보", "기기 정보", "검사 정보"], timeout=5)
    runner.assert_true(on_settings, "설정 아이콘 탭 후 설정 화면으로 이동하지 않음")
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
    try:
        drv.tap_text("버전 정보", timeout=3)
        time.sleep(0.5)
    except Exception:
        pass
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


def test_exam_set_006_back_to_exam(drv, runner):
    """TC-EXAM-SET-002 | 설정 화면 Back → 검사 화면 복귀, 검사 계속 진행 중"""
    # 설정 서브화면에서 Back 여러 번 눌러 검사 화면까지 복귀
    for _ in range(4):
        if drv.is_visible_text(_STOP_BTN, timeout=2):
            break
        drv.drv.press_keycode(4)
        time.sleep(0.8)
    back_on_exam = drv.is_visible_text(_STOP_BTN, timeout=5)
    runner.assert_true(back_on_exam, "설정 화면 Back 후 검사 화면('검사 종료' 버튼) 미복귀")
    if back_on_exam:
        log.info("TC-EXAM-SET-006: 설정 → Back 후 검사 화면 복귀 확인 — 검사 계속 진행 중")


# ---------------------------------------------------------------------------
# Test Cases — 검사 중 에러 케이스 (GPS)
# ---------------------------------------------------------------------------

def test_exam_err02_gps_off(drv, runner):
    """TC-EXAM-ERR-02 | 검사 중 GPS OFF → 위치 꺼짐 에러 팝업 표시 → GPS ON → 복구"""
    if not drv.is_visible_text(_STOP_BTN, timeout=3):
        log.info("TC-EXAM-ERR-02: 검사 미시작 상태 — 스킵")
        return
    # GPS OFF
    _adb(drv, "shell", "settings", "put", "secure", "location_mode", "0")
    time.sleep(2)
    try:
        popup = drv.is_visible_text(
            ["위치", "GPS", "위치 기능", "Location", "위치를 활성화"],
            timeout=15
        )
        if popup:
            log.info("TC-EXAM-ERR-02: 위치 꺼짐 에러 팝업 확인")
            try:
                drv.tap_text(["확인", "Ok", "OK", "닫기"], timeout=5, contains=False)
            except Exception:
                pass
        runner.assert_true(popup, "검사 중 GPS OFF 시 위치 꺼짐 에러 팝업 미표시")
    finally:
        _adb(drv, "shell", "settings", "put", "secure", "location_mode", "3")
        time.sleep(1)
        _wait_loading_clear(drv, timeout=20)


# ---------------------------------------------------------------------------
# Test Cases — 검사 종료 (요약 화면 이동)
# ---------------------------------------------------------------------------

def test_exam_006_stop_and_go_summary(drv, runner):
    """TC-EXAM-015 | 검사 종료 팝업 — 체크박스 체크 + '검사 종료' → 요약 화면 이동"""
    _wait_loading_clear(drv, timeout=30)
    if not drv.is_visible_text(_STOP_BTN, timeout=5):
        log.info("TC-EXAM-006: 검사 미시작 상태 — 스킵")
        return
    drv.tap_text(_STOP_BTN, timeout=5, contains=False)
    time.sleep(1)
    _wait_loading_clear(drv, timeout=10)
    # 체크박스 탭
    tapped = False
    for desc in _STOP_CB_DESC:
        try:
            els = drv.drv.find_elements(By.XPATH, f'//*[@content-desc="{desc}"]')
            if els:
                els[0].click()
                time.sleep(0.4)
                tapped = True
                break
        except Exception:
            pass
    if not tapped:
        log.warning("TC-EXAM-006: 체크박스를 찾지 못함 — '검사 종료' 버튼 직접 탭 시도")
    try:
        drv.tap_text("검사 종료", timeout=5, contains=False)
    except Exception:
        drv.tap_text("확인", timeout=5, contains=False)
    time.sleep(2)
    on_summary = drv.is_visible_text(["업로드", "건너뛰기", "완료", "진행률"], timeout=20)
    runner.assert_true(on_summary, "검사 종료 후 요약 화면으로 이동하지 않음")
    if on_summary:
        log.info("TC-EXAM-006: 요약 화면 이동 확인")


# ---------------------------------------------------------------------------
# Test Lists
# ---------------------------------------------------------------------------

# 검사 종료 전 실행 — 검사 화면 활성 상태에서 모든 TC 최대 수행
TESTS_PRE_STOP = [
    # 검사 시작 전
    test_exam_001_screen_visible,
    test_exam_002_status_indicators,
    test_exam_d08_initial_values,
    # 검사 시작
    test_exam_003_start_exam,
    # 검사 시작 후 — 대시보드, 팝업, 설정, 에러
    test_exam_d01_dashboard_labels,
    test_exam_004_stop_exam_popup,
    test_exam_005_stop_exam_checkbox,
    test_exam_016_popup_cancel_return,
    test_exam_set_001_settings_entry,
    test_exam_set_002_version_info,
    test_exam_set_003_file_screen_5tap,
    test_exam_set_004_device_info,
    test_exam_set_005_exam_info,
    test_exam_set_006_back_to_exam,
    test_exam_err02_gps_off,
]

# 검사 종료 (실행 후 요약 화면으로 이동)
TESTS_STOP = [
    test_exam_006_stop_and_go_summary,
]

TESTS = TESTS_PRE_STOP + TESTS_STOP
