"""
TC-CONN: 검사 화면 중 연결 상태 에러 케이스

ADB로 BT/WiFi/GPS를 제어해 에러 팝업을 유발하고 복구를 검증한다.
WiFi ADB 연결 중이면 WiFi-off 케이스는 자동 스킵.
"""
import subprocess
import time
import logging

log = logging.getLogger(__name__)

_EXAM_TEXT   = "검사 시작"
_RUNNING_TEXT = "검사 종료"


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


def _wifi_is_off(drv) -> bool:
    udid = drv.cfg.get("udid", "")
    cmd = ["adb"] + (["-s", udid] if udid else []) + ["shell", "settings", "get", "global", "wifi_on"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return r.stdout.strip() == "0"
    except Exception:
        return False


def _poll_until(drv, text, appear: bool, timeout: int) -> tuple[bool, float]:
    t0 = time.monotonic()
    for _ in range(timeout * 2):
        time.sleep(0.5)
        visible = drv.is_visible_text(text, timeout=1)
        if appear and visible:
            return True, round(time.monotonic() - t0, 1)
        if not appear and not visible:
            return True, round(time.monotonic() - t0, 1)
    return False, round(time.monotonic() - t0, 1)


def _on_exam_screen(drv) -> bool:
    return drv.is_visible_text([_EXAM_TEXT, _RUNNING_TEXT], timeout=3)


# ---------------------------------------------------------------------------
# Test Cases
# ---------------------------------------------------------------------------

def test_conn_000_exam_active(drv, runner):
    """TC-CONN-000 | 사전 확인: 검사 화면 진입 상태"""
    runner.assert_true(_on_exam_screen(drv), "검사 화면이 아님 — 연결 테스트 실행 불가")


def test_conn_001_bt_off_popup(drv, runner):
    """TC-CONN-001 | BT OFF → 블루투스 에러 팝업 표시 (20s 이내)"""
    if not _on_exam_screen(drv):
        return
    _bt_off(drv)
    try:
        ok, elapsed = _poll_until(drv, ["블루투스", "Bluetooth", "연결이 끊어", "연결 끊김"], appear=True, timeout=20)
        if ok:
            log.info("TC-CONN-001: 블루투스 에러 팝업 %.1fs 후 표시", elapsed)
            try:
                drv.tap_text(["확인", "Ok", "OK", "재시도"], timeout=5, contains=False)
            except Exception:
                pass
        runner.assert_true(ok, f"BT OFF 후 20s 내 블루투스 에러 팝업 미표시")
    finally:
        _bt_on(drv)
        time.sleep(3)


def test_conn_002_bt_recovery(drv, runner):
    """TC-CONN-002 | BT OFF → ON → 검사 화면 복구 (30s 이내)"""
    if not _on_exam_screen(drv):
        return
    _bt_off(drv)
    time.sleep(5)
    _bt_on(drv)
    ok, elapsed = _poll_until(drv, [_EXAM_TEXT, _RUNNING_TEXT], appear=True, timeout=30)
    if ok:
        log.info("TC-CONN-002: BT 재연결 후 검사 화면 복구 %.1fs", elapsed)
    runner.assert_true(ok, f"BT 재활성화 후 30s 내 검사 화면 복구 실패")


def test_conn_003_wifi_off_network_card(drv, runner):
    """TC-CONN-003 | WiFi OFF → OS 수준 wifi_on=0 확인 (네트워크 상태 변화)"""
    if _is_wifi_adb(drv):
        log.info("TC-CONN-003: WiFi ADB 연결 중 — WiFi OFF 스킵")
        return
    if not _on_exam_screen(drv):
        return
    _wifi_off(drv)
    try:
        wifi_off = _wifi_is_off(drv)
        runner.assert_true(wifi_off, "WiFi가 꺼지지 않음 (adb wifi_on still 1)")
        if wifi_off:
            log.info("TC-CONN-003: WiFi OFF 확인 (adb wifi_on=0)")
    finally:
        _wifi_on(drv)
        time.sleep(4)


def test_conn_004_wifi_recovery(drv, runner):
    """TC-CONN-004 | WiFi OFF → ON → wifi_on=1 복구 (15s 이내)"""
    if _is_wifi_adb(drv):
        log.info("TC-CONN-004: WiFi ADB 연결 중 — 스킵")
        return
    _wifi_off(drv)
    time.sleep(2)
    _wifi_on(drv)
    recovered = False
    for _ in range(30):
        time.sleep(0.5)
        if not _wifi_is_off(drv):
            recovered = True
            break
    runner.assert_true(recovered, "WiFi 재활성화 후 15s 내 복구 실패")
    if recovered:
        log.info("TC-CONN-004: WiFi 복구 확인")


TESTS = [
    test_conn_000_exam_active,
    test_conn_001_bt_off_popup,
    test_conn_002_bt_recovery,
    test_conn_003_wifi_off_network_card,
    test_conn_004_wifi_recovery,
]
