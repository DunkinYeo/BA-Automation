"""
BioArmour 공통 헬퍼
한국어 / 영어 OS 언어 설정에 따라 앱 언어가 결정됨 — 모든 셀렉터를 리스트로 관리
"""
import subprocess
import time
import logging

log = logging.getLogger(__name__)


def _grant_location_permissions(drv):
    """OS 위치 권한 팝업이 뜨지 않도록 ADB로 미리 부여한다."""
    pkg = drv.cfg.get("app_package", "")
    if not pkg:
        return
    udid = drv.cfg.get("udid", "")
    base = ["adb"] + (["-s", udid] if udid else [])
    for perm in [
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_COARSE_LOCATION",
    ]:
        try:
            subprocess.run(base + ["shell", "pm", "grant", pkg, perm],
                           capture_output=True, timeout=10)
        except Exception:
            pass

# ── 한/영 셀렉터 상수 ────────────────────────────────────────────────────────
CONNECT_BTN    = ["연결하기", "Connect"]
LOGIN_TITLE    = ["기기 연결하기", "Connect Your Device"]
SERIAL_HINT    = ["6자리 숫자 입력", "Serial Number (6 digits)"]

SETTING_ITEMS  = {
    "version": ["버전 정보", "Version Information"],
    "device":  ["기기 정보", "Device Information"],
    "study":   ["검사 정보", "Study Information"],
}

VERSION_TITLE  = ["버전 정보", "Version Information"]
CURRENT_VER    = ["현재 버전", "Current Version"]
FILE_TITLE     = ["파일 정보", "File Information"]

DEVICE_TITLE   = ["기기 정보", "Device Information"]
DEVICE_FIELDS  = {
    "type":   ["기기 종류", "Device Type"],
    "serial": ["기기 번호", "Serial Number"],
    "fw":     ["펌웨어 버전", "FW Version"],
    "sw":     ["소프트웨어 버전", "SW Version"],
}

STUDY_TITLE    = ["검사 정보", "Study Information"]
STUDY_FIELDS   = {
    "study_id": ["검사 ID", "Study ID"],
    "id":       ["대상 ID", "ID"],
    "name":     ["이름", "Name"],
    "start":    ["시작 시간", "Start Time"],
}

# 검사 화면 (디바이스 연결 필요 — 현재 확인 불가)
EXAM_START     = ["검사 시작", "Start Study"]
EXAM_STOP      = ["검사 종료", "End Study"]
EXAM_CONFIRM   = ["검사 정보 확인", "Study Information"]

# 요약 화면
SUMMARY_DONE   = ["완료", "Done", "Complete"]
SUMMARY_UPLOAD = ["업로드", "Upload"]
SUMMARY_SKIP   = ["건너뛰기", "Skip"]

# 공통 버튼
OK_BTNS        = ["확인", "Ok", "OK"]
CANCEL_BTNS    = ["취소", "Cancel"]
ALLOW_BTNS     = ["허용", "Allow", "동의"]

# 설정 아이콘 좌표 (Pixel 7 1080x2400 기준) — 텍스트 없는 아이콘이라 좌표 사용
SETTING_ICON_BOUNDS = (941, 202, 1014, 275)   # [x1,y1][x2,y2]
SETTING_ICON_CENTER = (977, 238)


def reset_to_login(drv, hard: bool = True):
    """로그인 화면(연결하기)으로 돌아간다."""
    pkg = drv.cfg.get("app_package")
    if hard:
        log.info("[setup] App restart → 로그인 화면")
        _grant_location_permissions(drv)
        try:
            drv.drv.terminate_app(pkg)
        except Exception:
            pass
        time.sleep(1)
        try:
            drv.drv.activate_app(pkg)
        except Exception:
            act = drv.cfg.get("app_activity")
            if act:
                drv.drv.start_activity(pkg, act)
        time.sleep(2)
        # 앱이 활성 검사 세션을 유지하는 경우 로그인 화면이 아닌 검사 화면으로 복귀할 수 있음
        if not drv.is_visible_text(LOGIN_TITLE, timeout=3):
            log.info("[setup] 검사 화면 감지 — 강제 종료 후 로그인 복귀 시도")
            _force_end_exam_to_login(drv)
    else:
        log.info("[setup] Back key → 로그인 화면")
        for _ in range(6):
            if drv.is_visible_text(LOGIN_TITLE, timeout=2):
                break
            drv.drv.press_keycode(4)
            time.sleep(0.8)
        time.sleep(0.5)


def _force_end_exam_to_login(drv):
    """활성 검사/요약 세션에서 로그인 화면으로 강제 복귀."""
    from selenium.webdriver.common.by import By
    _STOP_BTN_TEXT = "검사 종료"
    _STOP_CB_DESCS = ["검사를 종료하겠습니다.", "I confirm termination"]
    _SUMMARY_TEXTS = ["진행률", "데이터 업로드", "시작 시간", "종료 시간"]
    _SKIP_BTNS     = ["건너뛰기", "Skip"]
    _DONE_BTNS     = ["완료", "Done", "Complete"]
    _EXAM_CONFIRM  = ["검사 정보 확인", "Study Information Confirmation"]

    # 0) 검사 정보 확인 화면인 경우 — Back 키로 로그인 복귀
    if drv.is_visible_text(_EXAM_CONFIRM, timeout=3):
        log.info("[setup] 검사 정보 확인 화면 감지 — Back 키로 로그인 복귀")
        for _ in range(3):
            drv.drv.press_keycode(4)
            time.sleep(1)
            if drv.is_visible_text(LOGIN_TITLE, timeout=2):
                return

    # 1) 요약 화면인 경우 — 업로드 버튼/완료 버튼 탭으로 바로 로그인 복귀
    if drv.is_visible_text(_SUMMARY_TEXTS, timeout=3):
        log.info("[setup] 요약 화면 감지 — 완료/건너뛰기 탭으로 로그인 복귀")
        for btn in [_DONE_BTNS, _SKIP_BTNS]:
            if drv.is_visible_text(LOGIN_TITLE, timeout=2):
                return
            try:
                drv.tap_text(btn, timeout=5, contains=False)
                time.sleep(2)
            except Exception:
                pass
        if drv.is_visible_text(LOGIN_TITLE, timeout=3):
            return

    # 2) 검사 화면인 경우 — 검사 종료 팝업 → 체크박스 → 확인
    try:
        drv.tap_text(_STOP_BTN_TEXT, timeout=5, contains=False)
        time.sleep(1)
    except Exception:
        pass

    for desc in _STOP_CB_DESCS:
        try:
            els = drv.drv.find_elements(By.XPATH, f'//*[@content-desc="{desc}"]')
            if els:
                els[0].click()
                time.sleep(0.4)
                break
        except Exception:
            pass

    try:
        drv.tap_text(_STOP_BTN_TEXT, timeout=5, contains=False)
        time.sleep(2)
    except Exception:
        pass

    # 3) 요약 화면에서 완료/건너뛰기
    for btn in [_DONE_BTNS, _SKIP_BTNS]:
        if drv.is_visible_text(LOGIN_TITLE, timeout=2):
            return
        try:
            drv.tap_text(btn, timeout=5, contains=False)
            time.sleep(2)
        except Exception:
            pass

    # 4) Back 키 강제 복귀
    for _ in range(5):
        if drv.is_visible_text(LOGIN_TITLE, timeout=2):
            return
        drv.drv.press_keycode(4)
        time.sleep(0.8)
    log.warning("[setup] 로그인 화면 복귀 실패 — 수동 확인 필요")


def tap_setting_icon(drv):
    """설정 아이콘 탭 (텍스트 없는 아이콘이므로 좌표 사용)."""
    cx, cy = SETTING_ICON_CENTER
    drv.drv.tap([(cx, cy)])
    time.sleep(1.5)


def enter_serial(drv, serial: str):
    """시리얼 번호 입력 후 키보드 닫기."""
    import subprocess
    udid = drv.cfg.get("udid", "")

    # 입력 영역 탭 (content-desc="#, #, #, #, #, #")
    try:
        els = drv.drv.find_elements(
            "xpath", '//*[@content-desc="#, #, #, #, #, #"]'
        )
        if els:
            els[0].click()
        else:
            drv.drv.tap([(540, 1340)])
    except Exception:
        drv.drv.tap([(540, 1340)])
    time.sleep(0.5)

    # 숫자 입력
    cmd = ["adb"] + (["-s", udid] if udid else []) + ["shell", "input", "text", serial]
    subprocess.run(cmd, capture_output=True, timeout=5)
    time.sleep(0.4)

    # 키보드 닫기 — 버튼이 키보드에 가려지지 않도록
    try:
        drv.drv.hide_keyboard()
    except Exception:
        cmd_back = ["adb"] + (["-s", udid] if udid else []) + ["shell", "input", "keyevent", "111"]
        subprocess.run(cmd_back, capture_output=True, timeout=5)
    time.sleep(0.5)


def is_connect_enabled(drv) -> bool:
    """연결하기/Connect 버튼 활성화 여부.
    React Native 앱은 enabled 속성이 항상 true일 수 있으므로 clickable 우선 확인."""
    for text in CONNECT_BTN:
        try:
            els = drv.drv.find_elements(
                "xpath", f'//*[@content-desc="{text}"]'
            )
            if els:
                # clickable 먼저 확인 (React Native 버튼 비활성화 시 clickable=false)
                clickable = els[0].get_attribute("clickable")
                if clickable is not None:
                    return clickable == "true"
                return els[0].get_attribute("enabled") == "true"
            # text 속성으로도 확인
            els = drv.drv.find_elements(
                "xpath", f'//*[@text="{text}"]/..'
            )
            if els:
                clickable = els[0].get_attribute("clickable")
                if clickable is not None:
                    return clickable == "true"
                return els[0].get_attribute("enabled") == "true"
        except Exception:
            pass
    return False


def go_to_exam_screen(drv, wait_ble: int = 60):
    """로그인 → (검사 정보 화면) → 검사 화면까지 자동 진입."""
    try:
        pkg = drv.cfg.get("app_package")
        if pkg:
            drv.drv.activate_app(pkg)
            time.sleep(1.5)
    except Exception:
        pass

    if drv.is_visible_text(EXAM_START + EXAM_STOP, timeout=3):
        log.info("[go_to_exam_screen] Already on exam screen")
        return

    serial = drv.cfg.get("test_device_number", "")
    if serial and drv.is_visible_text(LOGIN_TITLE, timeout=3):
        enter_serial(drv, serial)
        time.sleep(0.3)
        drv.tap_text(CONNECT_BTN, timeout=5, contains=False)

    deadline = time.monotonic() + wait_ble
    while time.monotonic() < deadline:
        if drv.is_visible_text(EXAM_START + EXAM_STOP, timeout=1):
            log.info("[go_to_exam_screen] 검사 화면 도달")
            return
        if drv.is_visible_text(EXAM_CONFIRM, timeout=1):
            _check_and_confirm(drv)
            time.sleep(1)
            continue
        _dismiss_error_popups(drv)
        time.sleep(1)

    raise Exception(f"검사 화면 진입 실패 ({wait_ble}s 초과)")


_OS_PERMISSION_BTNS = [
    "앱 사용 중에만 허용", "While using the app", "Allow only while using the app",
    "이번만 허용", "Only this time",
    "허용", "Allow", "동의",
]


def _dismiss_os_permission_dialog(drv) -> bool:
    """Android OS 위치/권한 다이얼로그를 탭해서 닫는다. 닫으면 True."""
    for btn in _OS_PERMISSION_BTNS:
        if drv.is_visible_text(btn, timeout=1):
            try:
                drv.tap_text(btn, timeout=2, contains=False)
                time.sleep(0.5)
                return True
            except Exception:
                pass
    return False


def _dismiss_error_popups(drv):
    if _dismiss_os_permission_dialog(drv):
        return
    for btn in OK_BTNS:
        if drv.is_visible_text(btn, timeout=1):
            try:
                drv.tap_text(btn, timeout=2, contains=False)
                time.sleep(0.5)
                return
            except Exception:
                pass


def _check_and_confirm(drv):
    # content-desc="확인했습니다." 기반 체크박스 탭 (React Native 커스텀 컴포넌트)
    _CHECKBOX_DESC = ["확인했습니다.", "I confirm", "Confirmed"]
    tapped = False
    try:
        from selenium.webdriver.common.by import By
        for desc in _CHECKBOX_DESC:
            els = drv.drv.find_elements(By.XPATH, f'//*[@content-desc="{desc}"]')
            if els:
                els[0].click()
                time.sleep(0.4)
                tapped = True
                break
    except Exception:
        pass
    if not tapped:
        # fallback: 표준 CheckBox
        try:
            from selenium.webdriver.common.by import By
            cbs = drv.drv.find_elements(By.CLASS_NAME, "android.widget.CheckBox")
            for cb in cbs:
                if cb.get_attribute("checked") != "true":
                    cb.click()
                    time.sleep(0.3)
        except Exception:
            pass
    try:
        drv.tap_text(OK_BTNS, timeout=5, contains=False)
    except Exception:
        pass
