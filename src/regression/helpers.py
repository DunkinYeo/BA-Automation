"""
BioArmour 공통 헬퍼
한국어 / 영어 OS 언어 설정에 따라 앱 언어가 결정됨 — 모든 셀렉터를 리스트로 관리
"""
import time
import logging

log = logging.getLogger(__name__)

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
    else:
        log.info("[setup] Back key → 로그인 화면")
        for _ in range(6):
            if drv.is_visible_text(LOGIN_TITLE, timeout=2):
                break
            drv.drv.press_keycode(4)
            time.sleep(0.8)
        time.sleep(0.5)


def tap_setting_icon(drv):
    """설정 아이콘 탭 (텍스트 없는 아이콘이므로 좌표 사용)."""
    cx, cy = SETTING_ICON_CENTER
    drv.drv.tap([(cx, cy)])
    time.sleep(1.5)


def enter_serial(drv, serial: str):
    """시리얼 번호 입력 (커스텀 6자리 박스 입력).

    React Native 커스텀 컴포넌트라 EditText 없음.
    입력 영역 탭 후 키보드로 입력.
    """
    # 입력 영역 탭 (content-desc="#, #, #, #, #, #")
    try:
        els = drv.drv.find_elements(
            "xpath", '//*[@content-desc="#, #, #, #, #, #"]'
        )
        if els:
            els[0].click()
            time.sleep(0.5)
        else:
            # fallback: 화면 중앙 하단 입력 영역 좌표 탭
            drv.drv.tap([(540, 1383)])
            time.sleep(0.5)
    except Exception:
        drv.drv.tap([(540, 1383)])
        time.sleep(0.5)

    # 키보드로 숫자 입력
    import subprocess
    udid = drv.cfg.get("udid", "")
    cmd = ["adb"] + (["-s", udid] if udid else []) + ["shell", "input", "text", serial]
    subprocess.run(cmd, capture_output=True, timeout=5)
    time.sleep(0.3)


def is_connect_enabled(drv) -> bool:
    """연결하기/Connect 버튼 활성화 여부."""
    for text in CONNECT_BTN:
        try:
            els = drv.drv.find_elements(
                "xpath", f'//*[@content-desc="{text}"]'
            )
            if els:
                return els[0].get_attribute("enabled") == "true"
            # text 속성으로도 확인
            els = drv.drv.find_elements(
                "xpath", f'//*[@text="{text}"]/..'
            )
            if els:
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


def _dismiss_error_popups(drv):
    for btn in OK_BTNS:
        if drv.is_visible_text(btn, timeout=1):
            try:
                drv.tap_text(btn, timeout=2, contains=False)
                time.sleep(0.5)
                return
            except Exception:
                pass


def _check_and_confirm(drv):
    try:
        from selenium.webdriver.common.by import By
        checkboxes = drv.drv.find_elements(By.CLASS_NAME, "android.widget.CheckBox")
        for cb in checkboxes:
            if cb.get_attribute("checked") != "true":
                cb.click()
                time.sleep(0.3)
    except Exception:
        pass
    try:
        drv.tap_text(OK_BTNS, timeout=5, contains=False)
    except Exception:
        pass
