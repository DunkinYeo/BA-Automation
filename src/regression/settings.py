"""
TC-SET: 설정 화면 Regression Tests

실제 확인된 UI 텍스트 (한/영):
  설정 타이틀      : 설정 / Setting
  버전 정보        : 버전 정보 / Version Information
  기기 정보        : 기기 정보 / Device Information
  검사 정보        : 검사 정보 / Study Information

버전 정보 화면:
  타이틀          : 버전 정보 / Version Information
  현재 버전 라벨  : 현재 버전 / Current Version
  앱 아이콘 5회   → 파일 정보 / File Information

기기 정보 화면:
  기기 종류 / Device Type
  기기 번호 / Serial Number
  펌웨어 버전 / FW Version
  소프트웨어 버전 / SW Version

검사 정보 화면:
  검사 ID / Study ID
  대상 ID / ID
  이름 / Name
  시작 시간 / Start Time
"""
import time
import logging

log = logging.getLogger(__name__)

from src.regression.helpers import (
    tap_setting_icon, LOGIN_TITLE,
    SETTING_ITEMS, VERSION_TITLE, CURRENT_VER, FILE_TITLE,
    DEVICE_TITLE, DEVICE_FIELDS,
    STUDY_TITLE, STUDY_FIELDS,
)

# 앱 아이콘 좌표 (Pixel 7 기준, bounds [409,1061][671,1324])
_APP_ICON_CENTER = (540, 1192)


def _on_setting(drv) -> bool:
    """설정 메인 화면 — 3개 항목이 모두 보여야 메인으로 판정."""
    src = drv.drv.page_source
    return all(
        any(t in src for t in texts)
        for texts in SETTING_ITEMS.values()
    )


def _ensure_setting(drv):
    """설정 메인 화면으로 이동. 현재 서브화면이면 Back으로 올라온다."""
    for _ in range(3):
        if _on_setting(drv):
            return True
        drv.drv.press_keycode(4)
        time.sleep(0.8)
    tap_setting_icon(drv)
    time.sleep(1)
    return _on_setting(drv)


def _go_setting(drv):
    tap_setting_icon(drv)
    time.sleep(1)
    return _on_setting(drv)


# ---------------------------------------------------------------------------
# Test Cases — 설정 메인 화면
# ---------------------------------------------------------------------------

def test_set_002_menu_items(drv, runner):
    """TC-SET-002 | 설정 화면 진입 + 버전 정보 / 기기 정보 / 검사 정보 메뉴 표시"""
    if not _on_setting(drv):
        runner.assert_true(drv.is_visible_text(LOGIN_TITLE, timeout=3), "로그인 화면이 아님")
        ok = _go_setting(drv)
        runner.assert_true(ok, "설정 아이콘 탭 후 설정 화면 미이동")
    for key, texts in SETTING_ITEMS.items():
        runner.assert_true(
            drv.is_visible_text(texts, timeout=3),
            f"설정 항목 미표시: {texts}"
        )
    log.info("TC-SET-002: 설정 3개 항목 모두 확인")


# ---------------------------------------------------------------------------
# Test Cases — 버전 정보
# ---------------------------------------------------------------------------

def test_set_003_version_info(drv, runner):
    """TC-SET-003 | 버전 정보 탭 → 버전 정보 화면 이동, 현재 버전 표시"""
    _ensure_setting(drv)
    drv.tap_text(SETTING_ITEMS["version"], timeout=5)
    time.sleep(1)
    runner.assert_true(
        drv.is_visible_text(VERSION_TITLE, timeout=3),
        "버전 정보 / Version Information 타이틀 미표시"
    )
    runner.assert_true(
        drv.is_visible_text(CURRENT_VER, timeout=3),
        "현재 버전 / Current Version 라벨 미표시"
    )
    log.info("TC-SET-003: 버전 정보 화면 확인")
    drv.drv.press_keycode(4)
    time.sleep(0.8)


def test_set_004_file_screen_5tap(drv, runner):
    """TC-SET-004 | 버전 정보 화면 앱 아이콘 5회 탭 → 파일 정보 화면 이동"""
    _ensure_setting(drv)
    drv.tap_text(SETTING_ITEMS["version"], timeout=5)
    time.sleep(1)
    cx, cy = _APP_ICON_CENTER
    for _ in range(5):
        drv.drv.tap([(cx, cy)])
        time.sleep(0.3)
    time.sleep(1)
    ok = drv.is_visible_text(FILE_TITLE, timeout=5)
    if ok:
        log.info("TC-SET-004: 파일 정보 화면 진입 확인")
    runner.assert_true(ok, "앱 아이콘 5회 탭 후 파일 정보/File Information 화면 미이동")
    # 버전 정보로 Back → 설정 메인으로 Back
    drv.drv.press_keycode(4)
    time.sleep(0.5)
    drv.drv.press_keycode(4)
    time.sleep(0.8)


# ---------------------------------------------------------------------------
# Test Cases — 기기 정보
# ---------------------------------------------------------------------------

def test_set_005_device_info(drv, runner):
    """TC-SET-005 | 기기 정보 탭 → 기기 정보 화면, 4개 필드 표시"""
    _ensure_setting(drv)
    drv.tap_text(SETTING_ITEMS["device"], timeout=5)
    time.sleep(1)
    runner.assert_true(
        drv.is_visible_text(DEVICE_TITLE, timeout=3),
        "기기 정보 / Device Information 타이틀 미표시"
    )
    for key, texts in DEVICE_FIELDS.items():
        runner.assert_true(
            drv.is_visible_text(texts, timeout=3),
            f"기기 정보 필드 미표시: {texts}"
        )
    log.info("TC-SET-005: 기기 정보 4개 필드 확인 (기기 종류/기기 번호/펌웨어 버전/소프트웨어 버전)")
    drv.drv.press_keycode(4)
    time.sleep(0.8)


# ---------------------------------------------------------------------------
# Test Cases — 검사 정보
# ---------------------------------------------------------------------------

def test_set_006_study_info(drv, runner):
    """TC-SET-006 | 검사 정보 탭 → 검사 정보 화면, 4개 필드 표시"""
    _ensure_setting(drv)
    drv.tap_text(SETTING_ITEMS["study"], timeout=5)
    time.sleep(1)
    runner.assert_true(
        drv.is_visible_text(STUDY_TITLE, timeout=3),
        "검사 정보 / Study Information 타이틀 미표시"
    )
    for key, texts in STUDY_FIELDS.items():
        runner.assert_true(
            drv.is_visible_text(texts, timeout=3),
            f"검사 정보 필드 미표시: {texts}"
        )
    log.info("TC-SET-006: 검사 정보 4개 필드 확인 (검사 ID/대상 ID/이름/시작 시간)")


def test_set_007_back_to_login(drv, runner):
    """TC-SET-007 | 설정 화면 Back → 로그인 화면 복귀"""
    _ensure_setting(drv)
    drv.drv.press_keycode(4)
    time.sleep(1)
    runner.assert_true(
        drv.is_visible_text(LOGIN_TITLE, timeout=5),
        "설정 화면 Back 후 로그인 화면 미복귀"
    )
    log.info("TC-SET-007: 로그인 화면 복귀 확인")


TESTS = [
    test_set_002_menu_items,
    test_set_003_version_info,
    test_set_004_file_screen_5tap,
    test_set_005_device_info,
    test_set_006_study_info,
    test_set_007_back_to_login,
]
