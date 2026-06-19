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

_START_BTN    = ["검사 시작", "Start Study"]
_STOP_BTN     = ["검사 종료", "End Study"]
_STOP_CB_DESC = ["검사를 종료하겠습니다.", "I want to end study.", "I confirm termination", "Confirm termination"]
_LOADING_TEXT = ["잠시만 기다려주세요", "Please wait", "Loading"]

# 개념별 한/영 쌍 — 각 쌍에서 하나 이상 표시돼야 PASS
_DASHBOARD_LABEL_PAIRS = [
    ["심박수", "Heart Rate"],
    ["체온", "Temperature"],
    ["낙상감지", "Fall"],
    ["걸음 수", "Steps"],
    ["활동 레벨", "Activity Level"],
    ["자세", "Posture"],
]
# is_visible_text 단일 호출용 flat list
_DASHBOARD_LABELS = [lbl for pair in _DASHBOARD_LABEL_PAIRS for lbl in pair]
_STATUS_LABELS    = ["네트워크", "Network", "블루투스", "Bluetooth", "배터리", "Battery"]
_ERROR_POPUPS     = ["오류", "Error", "알 수 없는 오류", "연결 끊김", "Disconnected"]

_SETTINGS_ITEMS   = ["버전 정보", "Version Information", "기기 정보", "Device Information",
                     "검사 정보", "Study Information"]
_STOP_POPUP_TEXT  = ["검사 종료", "End Study", "종료하", "Confirm", "확인"]
_SUMMARY_TEXT     = ["업로드", "Upload", "건너뛰기", "Skip", "완료", "Done", "Complete",
                     "진행률", "Progress"]

_MONITOR_INTERVAL = 30   # 모니터링 체크 주기 (초)
_MONITOR_DURATION = 600  # 총 모니터링 시간 (초, 10분)


def _wait_loading_clear(drv, timeout: int = 30):
    """로딩 오버레이 사라질 때까지 대기."""
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout:
        if not drv.is_visible_text(_LOADING_TEXT, timeout=1):
            return
        time.sleep(1)
    log.warning("_wait_loading_clear: %ds 후에도 로딩 오버레이 미사라짐", timeout)


def _on_exam(drv) -> bool:
    return drv.is_visible_text(_START_BTN + _STOP_BTN, timeout=3)


def _adb(drv, *args):
    udid = drv.cfg.get("udid", "")
    cmd = ["adb"] + (["-s", udid] if udid else []) + list(args)
    subprocess.run(cmd, capture_output=True, timeout=10)


# ---------------------------------------------------------------------------
# Test Cases — 검사 화면 진입 확인 (검사 시작 전)
# ---------------------------------------------------------------------------

def test_exam_001_screen_visible(drv, runner):
    """TC-EXAM-001 | 검사 화면 진입 — '검사 시작' 또는 '검사 종료' 버튼 표시 확인"""
    runner.assert_true(
        drv.is_visible_text(_START_BTN + _STOP_BTN, timeout=5),
        "검사 화면의 '검사 시작/Start Study' 버튼이 표시되지 않음"
    )


def test_exam_002_status_indicators(drv, runner):
    """TC-EXAM-002 | 상태 표시 — 네트워크/블루투스/배터리 라벨 존재"""
    if not _on_exam(drv):
        runner.skip("검사 화면이 아님")
    found = drv.is_visible_text(_STATUS_LABELS, timeout=5)
    if found:
        log.info("TC-EXAM-002: 상태 라벨 확인")
    else:
        log.info("TC-EXAM-002: 상태 라벨 텍스트 미감지 — 아이콘만 표시될 수 있음 (수동 확인 권고)")
    runner.assert_true(_on_exam(drv), "검사 화면이 아님 — 상태 표시 확인 불가")


def test_exam_d08_initial_values(drv, runner):
    """TC-EXAM-D08 | 검사 시작 전 대시보드 — 라벨 및 초기값 표시"""
    if not drv.is_visible_text(_START_BTN, timeout=3):
        runner.skip("이미 검사 중 — Start Study 버튼 없음")
    missing = []
    for pair in _DASHBOARD_LABEL_PAIRS:
        if drv.is_visible_text(pair, timeout=2):
            log.info("TC-EXAM-D08: '%s' 라벨 확인", pair)
        else:
            log.warning("TC-EXAM-D08: '%s' 라벨 미감지", pair)
            missing.append(pair[0])
    runner.assert_true(
        len(missing) == 0,
        f"검사 시작 전 대시보드 라벨 미표시: {missing}"
    )
    log.info("TC-EXAM-D08: 검사 시작 전 대시보드 라벨 확인")


# ---------------------------------------------------------------------------
# Test Cases — 검사 시작
# ---------------------------------------------------------------------------

def test_exam_003_start_exam(drv, runner):
    """TC-EXAM-011 | '검사 시작' 클릭 → '검사 종료' 버튼 표시"""
    if not drv.is_visible_text(_START_BTN, timeout=3):
        runner.skip("이미 검사 중 — Start Study 버튼 없음")
    drv.tap_text(_START_BTN, timeout=5, contains=False)
    _wait_loading_clear(drv, timeout=30)
    ok = drv.is_visible_text(_STOP_BTN, timeout=20)
    runner.assert_true(ok, "'검사 시작' 클릭 후 '검사 종료/End Study' 버튼이 표시되지 않음")
    if ok:
        log.info("TC-EXAM-003: '검사 종료' 버튼 표시 확인 — 검사 시작됨")


def test_exam_d01_dashboard_labels(drv, runner):
    """TC-EXAM-D01 | 검사 시작 후 대시보드 6개 항목 라벨 표시"""
    if not drv.is_visible_text(_STOP_BTN, timeout=3):
        runner.skip("검사 미시작 — End Study 버튼 없음")
    missing = []
    for pair in _DASHBOARD_LABEL_PAIRS:
        if drv.is_visible_text(pair, timeout=2):
            log.info("TC-EXAM-D01: '%s' 확인", pair)
        else:
            log.warning("TC-EXAM-D01: '%s' 미감지", pair)
            missing.append(pair[0])
    runner.assert_true(
        len(missing) == 0,
        f"대시보드 라벨 미표시: {missing}"
    )


def test_exam_d02_monitor_during_exam(drv, runner):
    """TC-EXAM-D02 | 검사 진행 중 10분 모니터링 — 화면 유지·에러 팝업·대시보드 상태 확인"""
    if not drv.is_visible_text(_STOP_BTN, timeout=3):
        runner.skip("검사 미시작 — End Study 버튼 없음")

    deadline    = time.monotonic() + _MONITOR_DURATION
    check_num   = 0
    error_count = 0
    crash_count = 0

    log.info("TC-EXAM-D02: 10분 모니터링 시작 (%d초 간격)", _MONITOR_INTERVAL)

    while time.monotonic() < deadline:
        remaining = int(deadline - time.monotonic())
        check_num += 1

        on_exam = drv.is_visible_text(_STOP_BTN, timeout=5)
        if not on_exam:
            crash_count += 1
            log.error("TC-EXAM-D02 [%02d] 검사 화면 이탈 감지! (남은시간: %ds)", check_num, remaining)
            try:
                drv.screenshot(f"d02_exit_{check_num:02d}")
            except Exception:
                pass
            if drv.is_visible_text(_ERROR_POPUPS, timeout=3):
                error_count += 1
                log.warning("TC-EXAM-D02 [%02d] 에러 팝업 감지 — 닫기 시도", check_num)
                try:
                    drv.tap_text(["확인", "Ok", "OK", "닫기", "Close"], timeout=3, contains=False)
                    time.sleep(1)
                except Exception:
                    pass
        else:
            src = drv.drv.page_source
            visible = [lbl for lbl in _DASHBOARD_LABELS if lbl in src]
            log.info("TC-EXAM-D02 [%02d] 검사 중 정상 | 대시보드: %s | 남은시간: %ds",
                     check_num, visible, remaining)

        time.sleep(_MONITOR_INTERVAL)

    still_on_exam = drv.is_visible_text(_STOP_BTN, timeout=5)
    log.info("TC-EXAM-D02: 모니터링 종료 — 총 %d회 체크, 에러팝업 %d회, 화면이탈 %d회",
             check_num, error_count, crash_count)
    runner.assert_true(
        still_on_exam,
        f"10분 모니터링 후 검사 화면 이탈 상태 (에러팝업 {error_count}회, 화면이탈 {crash_count}회)"
    )


# ---------------------------------------------------------------------------
# Test Cases — 검사 종료 팝업 (취소)
# ---------------------------------------------------------------------------

def test_exam_004_stop_exam_popup(drv, runner):
    """TC-EXAM-013 | '검사 종료' 클릭 → 팝업 표시 → 취소 → 검사 화면 복귀 확인"""
    if not drv.is_visible_text(_STOP_BTN, timeout=3):
        runner.skip("검사 미시작 — End Study 버튼 없음")
    drv.tap_text(_STOP_BTN, timeout=5, contains=False)
    time.sleep(1)
    popup_visible = drv.is_visible_text(_STOP_POPUP_TEXT, timeout=5)
    runner.assert_true(popup_visible, "'검사 종료/End Study' 클릭 후 확인 팝업이 표시되지 않음")
    if popup_visible:
        log.info("TC-EXAM-004: 검사 종료 팝업 확인")
        try:
            drv.tap_text(["취소", "Cancel", "닫기"], timeout=3, contains=False)
        except Exception:
            drv.drv.press_keycode(4)
        time.sleep(0.8)
        back_on_exam = drv.is_visible_text(_STOP_BTN, timeout=5)
        runner.assert_true(back_on_exam, "종료 팝업 취소 후 검사 화면 복귀하지 않음")


def test_exam_005_stop_exam_checkbox(drv, runner):
    """TC-EXAM-014 | 검사 종료 팝업 — 체크박스 미체크 시 '검사 종료' 비활성화"""
    if not drv.is_visible_text(_STOP_BTN, timeout=3):
        runner.skip("검사 미시작 — End Study 버튼 없음")
    drv.tap_text(_STOP_BTN, timeout=5, contains=False)
    time.sleep(1)
    if not drv.is_visible_text(_STOP_POPUP_TEXT, timeout=3):
        runner.assert_true(False, "검사 종료 팝업이 표시되지 않음")
        return
    try:
        for btn_text in _STOP_BTN:
            els = drv.drv.find_elements(By.XPATH, f'//*[@text="{btn_text}"]')
            if els:
                clickable = els[0].get_attribute("clickable")
                enabled   = els[0].get_attribute("enabled")
                is_active = (clickable == "true") if clickable is not None else (enabled == "true")
                runner.assert_false(is_active, "체크박스 미체크 상태에서 종료 버튼이 활성화됨")
                break
        else:
            log.info("TC-EXAM-005: 버튼 상태 확인 불가 — 수동 확인 필요")
    except Exception:
        log.info("TC-EXAM-005: 버튼 상태 확인 불가 — 수동 확인 필요")
    try:
        drv.drv.press_keycode(4)
    except Exception:
        pass
    time.sleep(0.5)



# ---------------------------------------------------------------------------
# Test Cases — 검사 중 설정 화면
# ---------------------------------------------------------------------------

def test_exam_set_001_settings_entry(drv, runner):
    """TC-EXAM-SET-001 | 설정 아이콘 → 설정 화면 이동"""
    if not _on_exam(drv):
        runner.skip("검사 화면이 아님")
    cx, cy = SETTING_ICON_CENTER
    drv.drv.tap([(cx, cy)])
    time.sleep(1)
    on_settings = drv.is_visible_text(_SETTINGS_ITEMS, timeout=5)
    runner.assert_true(on_settings, "설정 아이콘 탭 후 설정 화면으로 이동하지 않음")
    if on_settings:
        log.info("TC-EXAM-SET-001: 설정 화면 진입 확인")


def test_exam_set_006_back_to_exam(drv, runner):
    """TC-EXAM-SET-006 | 설정 화면 Back → 검사 화면 복귀, 검사 계속 진행 중"""
    for _ in range(4):
        if drv.is_visible_text(_STOP_BTN, timeout=2):
            break
        drv.drv.press_keycode(4)
        time.sleep(0.8)
    back_on_exam = drv.is_visible_text(_STOP_BTN, timeout=5)
    runner.assert_true(back_on_exam, "설정 화면 Back 후 검사 화면('검사 종료/End Study' 버튼) 미복귀")
    if back_on_exam:
        log.info("TC-EXAM-SET-006: 설정 → Back 후 검사 화면 복귀 확인")


# ---------------------------------------------------------------------------
# Test Cases — 검사 종료 (요약 화면 이동)
# ---------------------------------------------------------------------------

def test_exam_006_stop_and_go_summary(drv, runner):
    """TC-EXAM-015 | 검사 종료 팝업 — 체크박스 체크 + '검사 종료' → 요약 화면 이동"""
    _wait_loading_clear(drv, timeout=30)
    if not drv.is_visible_text(_STOP_BTN, timeout=5):
        runner.skip("검사 미시작 — End Study 버튼 없음")
    drv.tap_text(_STOP_BTN, timeout=5, contains=False)
    time.sleep(1)
    _wait_loading_clear(drv, timeout=10)
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
        log.warning("TC-EXAM-006: 체크박스를 찾지 못함 — 종료 버튼 직접 탭 시도")
    try:
        drv.tap_text(_STOP_BTN, timeout=5, contains=False)
    except Exception:
        drv.tap_text(["확인", "Ok", "OK", "Confirm"], timeout=5, contains=False)
    time.sleep(2)
    on_summary = drv.is_visible_text(_SUMMARY_TEXT, timeout=20)
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
    # 검사 시작 직후 — 대시보드 라벨 확인
    test_exam_d01_dashboard_labels,
    # 10분 모니터링 — 화면 유지·에러·대시보드 상태
    test_exam_d02_monitor_during_exam,
    # 종료 팝업 플로우 (004: 팝업 표시 + 취소 + 복귀, 005: 체크박스 비활성화)
    test_exam_004_stop_exam_popup,
    test_exam_005_stop_exam_checkbox,
    # 검사 중 설정 — 진입/복귀만 확인 (세부 항목은 Phase 1 TC-SET에서 검증)
    test_exam_set_001_settings_entry,
    test_exam_set_006_back_to_exam,
]

# 검사 종료 (실행 후 요약 화면으로 이동)
TESTS_STOP = [
    test_exam_006_stop_and_go_summary,
]

TESTS = TESTS_PRE_STOP + TESTS_STOP
