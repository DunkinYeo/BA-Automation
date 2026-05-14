"""
TC-LOGIN: 로그인 화면 Regression Tests

실제 확인된 UI 텍스트 (한/영):
  로그인 타이틀 : 기기 연결하기 / Connect Your Device
  시리얼 힌트  : 6자리 숫자 입력 / Serial Number (6 digits)
  연결 버튼    : 연결하기 / Connect  (content-desc 기준, enabled=false when empty)
  설정 아이콘  : 텍스트 없음 — 좌표 탭 (941~1014, 202~275)

입력 구조:
  - React Native 커스텀 6자리 박스 (EditText 없음)
  - content-desc="#, #, #, #, #, #" ViewGroup 탭 후 adb input text 입력

에러 케이스 (ADB 제어 가능):
  BT OFF / GPS OFF / WiFi OFF → 연결 시도 시 에러 팝업 확인
"""
import subprocess
import time
import logging

log = logging.getLogger(__name__)

from src.regression.helpers import (
    CONNECT_BTN, LOGIN_TITLE, SERIAL_HINT, SETTING_ITEMS,
    tap_setting_icon, enter_serial, is_connect_enabled,
    VERSION_TITLE, DEVICE_TITLE, STUDY_TITLE,
    OK_BTNS,
)


def _adb(drv, *args):
    udid = drv.cfg.get("udid", "")
    cmd = ["adb"] + (["-s", udid] if udid else []) + list(args)
    subprocess.run(cmd, capture_output=True, timeout=10)


def _bt_off(drv): _adb(drv, "shell", "cmd", "bluetooth_manager", "disable")
def _bt_on(drv):  _adb(drv, "shell", "cmd", "bluetooth_manager", "enable")
def _wifi_off(drv): _adb(drv, "shell", "svc", "wifi", "disable")
def _wifi_on(drv):  _adb(drv, "shell", "svc", "wifi", "enable")
def _gps_off(drv):  _adb(drv, "shell", "settings", "put", "secure", "location_mode", "0")
def _gps_on(drv):   _adb(drv, "shell", "settings", "put", "secure", "location_mode", "3")


def _is_wifi_adb(drv) -> bool:
    return ":" in drv.cfg.get("udid", "")


def _back_to_login(drv):
    """에러 TC 후 앱이 로그인 화면이 아닌 경우 Back 키로 복귀."""
    if drv.is_visible_text(LOGIN_TITLE, timeout=2):
        return
    # 서버 에러 팝업(302, 902 등) 먼저 닫기
    for btn in OK_BTNS:
        try:
            drv.tap_text(btn, timeout=1, contains=False)
            time.sleep(0.5)
        except Exception:
            pass
    if drv.is_visible_text(LOGIN_TITLE, timeout=2):
        return
    for _ in range(4):
        drv.drv.press_keycode(4)
        time.sleep(0.8)
        if drv.is_visible_text(LOGIN_TITLE, timeout=2):
            return


def _clear_serial(drv):
    """시리얼 박스 지우기 — 입력 영역 탭 후 DEL 6회, 키보드 닫기."""
    udid = drv.cfg.get("udid", "")
    cmd_base = ["adb"] + (["-s", udid] if udid else [])
    # 입력 영역에 포커스
    try:
        els = drv.drv.find_elements("xpath", '//*[@content-desc="#, #, #, #, #, #"]')
        if els:
            els[0].click()
        else:
            drv.drv.tap([(540, 1340)])
    except Exception:
        drv.drv.tap([(540, 1340)])
    time.sleep(0.3)
    # DEL 6회
    for _ in range(6):
        subprocess.run(cmd_base + ["shell", "input", "keyevent", "67"],
                       capture_output=True, timeout=5)
    time.sleep(0.2)
    # 키보드 닫기
    try:
        drv.drv.hide_keyboard()
    except Exception:
        subprocess.run(cmd_base + ["shell", "input", "keyevent", "111"],
                       capture_output=True, timeout=5)
    time.sleep(0.4)


# ---------------------------------------------------------------------------
# TC-LOGIN-001 ~ 005 | 로그인 화면 기본 UI
# ---------------------------------------------------------------------------

def test_login_001_screen_visible(drv, runner):
    """TC-LOGIN-001 | 앱 실행 → 로그인 화면 표시"""
    runner.assert_true(
        drv.is_visible_text(LOGIN_TITLE, timeout=5),
        "로그인 화면 타이틀(기기 연결하기/Connect Your Device) 미표시"
    )
    runner.assert_true(
        drv.is_visible_text(CONNECT_BTN, timeout=3),
        "연결하기/Connect 버튼 미표시"
    )


def test_login_002_empty_connect_disabled(drv, runner):
    """TC-LOGIN-002 | 시리얼 미입력 → 연결하기 버튼 비활성화"""
    runner.assert_false(
        is_connect_enabled(drv),
        "시리얼 미입력 상태에서 연결하기 버튼이 활성화됨"
    )


def test_login_003_serial_hint_visible(drv, runner):
    """TC-LOGIN-003 | 시리얼 입력 힌트 텍스트 표시 확인"""
    runner.assert_true(
        drv.is_visible_text(SERIAL_HINT, timeout=3),
        "6자리 숫자 입력 / Serial Number (6 digits) 힌트 미표시"
    )


def test_login_004_valid_serial_connect_enabled(drv, runner):
    """TC-LOGIN-004 | 6자리 숫자 입력 → 연결하기 버튼 활성화"""
    device_num = drv.cfg.get("test_device_number", "123456")
    enter_serial(drv, device_num)
    time.sleep(0.5)
    enabled = is_connect_enabled(drv)
    _clear_serial(drv)
    runner.assert_true(enabled, f"'{device_num}' 입력 후 연결하기 버튼 비활성화")


def test_login_005_setting_icon_entry(drv, runner):
    """TC-LOGIN-005 | 설정 아이콘 탭 → 설정 화면 이동"""
    runner.assert_true(drv.is_visible_text(LOGIN_TITLE, timeout=3), "로그인 화면이 아님")
    tap_setting_icon(drv)
    on_setting = drv.is_visible_text(SETTING_ITEMS["version"] + SETTING_ITEMS["device"], timeout=5)
    runner.assert_true(on_setting, "설정 아이콘 탭 후 설정 화면(버전 정보/기기 정보) 미표시")
    # 복귀
    drv.drv.press_keycode(4)
    time.sleep(0.5)


def test_login_006_wrong_serial_error(drv, runner):
    """TC-LOGIN-006 | 잘못된 시리얼 → 연결 → 에러 팝업 표시"""
    enter_serial(drv, "000000")
    time.sleep(0.3)
    runner.assert_true(is_connect_enabled(drv), "6자리 입력 후 연결하기 비활성화")
    drv.tap_text(CONNECT_BTN, timeout=5, contains=False)
    # 에러 팝업 대기 — 실제 앱이 노출하는 텍스트 포함 (902 서버 에러 코드 포함)
    # 실제 확인된 팝업 텍스트: "알 수 없는 오류 (902)" / "알 수 없는 오류가 발생했습니다."
    popup = drv.is_visible_text(
        ["알 수 없는 오류", "알 수 없는", "902",
         "디바이스를 찾을 수 없음", "검사 정보 없음", "연결 실패",
         "Cannot find", "not found", "오류", "Error"],
        timeout=40
    )
    # 팝업 뜰 때 스크린샷 캡처
    try:
        drv.screenshot("login_006_wrong_serial_popup")
    except Exception:
        pass
    # 팝업 텍스트 로그
    import re
    try:
        src = drv.drv.page_source
        texts = [t for t in re.findall(r'text="([^"]+)"', src) if t.strip()]
        log.info(f"TC-LOGIN-006 popup 화면 텍스트: {texts}")
    except Exception:
        pass
    try:
        drv.tap_text(OK_BTNS, timeout=5, contains=False)
    except Exception:
        pass
    time.sleep(1)
    _clear_serial(drv)
    runner.assert_true(popup, "잘못된 시리얼 → 연결 시 에러 팝업 미표시")


# ---------------------------------------------------------------------------
# TC-LOGIN-ERR | 에러 케이스 (ADB 제어)
# ---------------------------------------------------------------------------

def test_login_err_10_bt_off(drv, runner):
    """TC-LOGIN-ERR-10 | BT OFF → 연결하기 → 블루투스 꺼짐 에러 팝업"""
    device_num = drv.cfg.get("test_device_number", "")
    if not device_num:
        log.info("TC-LOGIN-ERR-10: test_device_number 미설정 — 스킵")
        return
    _bt_off(drv)
    time.sleep(2)
    try:
        enter_serial(drv, device_num)
        drv.tap_text(CONNECT_BTN, timeout=5, contains=False)
        popup = drv.is_visible_text(
            ["블루투스", "Bluetooth", "블루투스 기능", "블루투스를 활성화"],
            timeout=15
        )
        try:
            drv.tap_text(OK_BTNS, timeout=5, contains=False)
        except Exception:
            pass
        time.sleep(1)
        _clear_serial(drv)
        if popup:
            log.info("TC-LOGIN-ERR-10: 블루투스 꺼짐 팝업 확인")
        runner.assert_true(popup, "BT OFF 시 블루투스 에러 팝업 미표시")
    finally:
        _bt_on(drv)
        time.sleep(3)
        _back_to_login(drv)


def test_login_err_11_gps_off(drv, runner):
    """TC-LOGIN-ERR-11 | 위치 OFF → 연결하기 → 위치 꺼짐 에러 팝업"""
    device_num = drv.cfg.get("test_device_number", "")
    if not device_num:
        log.info("TC-LOGIN-ERR-11: test_device_number 미설정 — 스킵")
        return
    _gps_off(drv)
    time.sleep(1)
    try:
        enter_serial(drv, device_num)
        drv.tap_text(CONNECT_BTN, timeout=5, contains=False)
        popup = drv.is_visible_text(
            ["위치", "위치 기능", "위치를 활성화", "Location"],
            timeout=15
        )
        try:
            drv.tap_text(OK_BTNS, timeout=5, contains=False)
        except Exception:
            pass
        time.sleep(1)
        _clear_serial(drv)
        if popup:
            log.info("TC-LOGIN-ERR-11: 위치 꺼짐 팝업 확인")
        runner.assert_true(popup, "위치 OFF 시 에러 팝업 미표시")
    finally:
        _gps_on(drv)
        time.sleep(1)
        _back_to_login(drv)


def test_login_err_01_network_off(drv, runner):
    """TC-LOGIN-ERR-01 | WiFi OFF → 연결하기 → 네트워크 에러 팝업"""
    if _is_wifi_adb(drv):
        log.info("TC-LOGIN-ERR-01: WiFi ADB 연결 중 — 스킵")
        return
    device_num = drv.cfg.get("test_device_number", "")
    if not device_num:
        log.info("TC-LOGIN-ERR-01: test_device_number 미설정 — 스킵")
        return
    _wifi_off(drv)
    time.sleep(2)
    try:
        enter_serial(drv, device_num)
        drv.tap_text(CONNECT_BTN, timeout=5, contains=False)
        popup = drv.is_visible_text(
            ["네트워크", "네트워크 연결 안됨", "인터넷", "Network", "network"],
            timeout=15
        )
        try:
            drv.tap_text(OK_BTNS, timeout=5, contains=False)
        except Exception:
            pass
        time.sleep(1)
        _clear_serial(drv)
        if popup:
            log.info("TC-LOGIN-ERR-01: 네트워크 꺼짐 팝업 확인")
        runner.assert_true(popup, "WiFi OFF 시 네트워크 에러 팝업 미표시")
    finally:
        _wifi_on(drv)
        time.sleep(4)
        _back_to_login(drv)


TESTS = [
    test_login_001_screen_visible,
    test_login_002_empty_connect_disabled,
    test_login_003_serial_hint_visible,
    test_login_004_valid_serial_connect_enabled,
    test_login_005_setting_icon_entry,
    test_login_006_wrong_serial_error,
]
