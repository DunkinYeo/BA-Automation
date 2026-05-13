import logging
import subprocess
import time

log = logging.getLogger(__name__)

from appium import webdriver
from appium.options.android.uiautomator2.base import UiAutomator2Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, WebDriverException, InvalidSessionIdException

from src.retry import retry
from src.artifacts import ArtifactManager
from src.reporter import RunReporter


class AndroidDriver:
    def __init__(self, a_cfg: dict, selectors: dict, artifacts: ArtifactManager, reporter: RunReporter):
        self.cfg = a_cfg
        self.sel = selectors
        self.artifacts = artifacts
        self.reporter = reporter
        self._last_adb_reconnect_at: float = 0.0
        self.drv = self._connect()

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def _build_options(self) -> UiAutomator2Options:
        opts = UiAutomator2Options()
        opts.platform_name = "Android"
        opts.automation_name = "UiAutomator2"
        opts.device_name = self.cfg.get("device_name", "Android")
        opts.no_reset = bool(self.cfg.get("no_reset", True))
        opts.new_command_timeout = int(self.cfg.get("new_command_timeout", 3600))
        udid = self.cfg.get("udid", "")
        if udid:
            opts.udid = udid
        if self.cfg.get("app_package"):
            opts.app_package = self.cfg["app_package"]
        if self.cfg.get("app_activity"):
            opts.app_activity = self.cfg["app_activity"]
        return opts

    def _connect(self) -> webdriver.Remote:
        server = self.cfg.get("appium_server_url", "http://127.0.0.1:4723")
        self.reporter.log_event("appium_connect", {"server": server})
        return webdriver.Remote(server, options=self._build_options())

    def _ensure_adb_connected(self) -> None:
        udid = self.cfg.get("udid", "")
        wifi_addr = None
        if udid and ":" in udid and not udid.startswith("/"):
            wifi_addr = udid
        if not wifi_addr:
            return
        now = time.monotonic()
        if now - self._last_adb_reconnect_at < 30:
            return
        self._last_adb_reconnect_at = now
        try:
            self.reporter.log_event("adb_reconnect_attempt", {"addr": wifi_addr})
            result = subprocess.run(["adb", "connect", wifi_addr], capture_output=True, text=True, timeout=10)
            output = result.stdout.strip()
            self.reporter.log_event("adb_reconnect_result", {"addr": wifi_addr, "output": output})
            if "connected" in output.lower() and "already" not in output.lower():
                time.sleep(2)
        except Exception as e:
            self.reporter.log_event("adb_reconnect_failed", {"addr": wifi_addr, "error": str(e)})

    def reconnect(self):
        logging.warning("[SESSION] recreating driver")
        self.reporter.log_event("session_recreating", {})
        self._last_adb_reconnect_at = 0.0
        self._ensure_adb_connected()
        try:
            self.drv.quit()
        except Exception:
            pass
        self.drv = self._connect()
        try:
            self.bring_to_foreground()
        except Exception:
            pass
        logging.info("[SESSION] recovery success")
        self.reporter.log_event("session_recovery_success", {})

    def is_session_alive(self) -> bool:
        try:
            _ = self.drv.current_activity
            return True
        except Exception:
            return False

    def ensure_session(self):
        if not self.is_session_alive():
            logging.warning("[SESSION] driver lost — session not alive")
            self.reporter.log_event("session_lost", {"reason": "session_not_alive"})
            self.reconnect()

    def close(self):
        try:
            self.drv.quit()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def get_device_info(self) -> dict:
        try:
            caps = self.drv.capabilities
            return {
                "model":           caps.get("deviceModel", caps.get("device", "")),
                "manufacturer":    caps.get("deviceManufacturer", ""),
                "android_version": caps.get("platformVersion", ""),
                "udid":            self.cfg.get("udid", ""),
            }
        except Exception:
            return {"udid": self.cfg.get("udid", "")}

    def wait_idle(self, seconds: float):
        time.sleep(seconds)

    def is_visible_text(self, text: str | list, timeout: int = 5) -> bool:
        texts = [text] if isinstance(text, str) else text
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                src = self.drv.page_source
                for t in texts:
                    if t in src:
                        return True
            except Exception:
                pass
            time.sleep(0.4)
        return False

    def find(self, text: str, timeout: int = 5):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                els = self.drv.find_elements(By.XPATH, f'//*[@text="{text}"]')
                if els:
                    return els[0]
                els = self.drv.find_elements(By.XPATH, f'//*[contains(@text, "{text}")]')
                if els:
                    return els[0]
            except Exception:
                pass
            time.sleep(0.4)
        raise TimeoutException(f"Element with text '{text}' not found within {timeout}s")

    def tap_text(self, text: str | list, timeout: int = 5, contains: bool = True):
        texts = [text] if isinstance(text, str) else text
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            for t in texts:
                try:
                    if contains:
                        els = self.drv.find_elements(By.XPATH, f'//*[contains(@text, "{t}")]')
                    else:
                        els = self.drv.find_elements(By.XPATH, f'//*[@text="{t}"]')
                    if els:
                        els[0].click()
                        return
                except Exception:
                    pass
            time.sleep(0.4)
        raise TimeoutException(f"Could not tap text {texts!r} within {timeout}s")

    def screenshot(self, name: str) -> str:
        return self.artifacts.screenshot(self.drv, name)

    def bring_to_foreground(self):
        pkg = self.cfg.get("app_package")
        if not pkg:
            return
        try:
            self.drv.activate_app(pkg)
        except Exception:
            act = self.cfg.get("app_activity")
            if act:
                try:
                    self.drv.start_activity(pkg, act)
                except Exception:
                    pass
