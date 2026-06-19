import dataclasses
import logging
import time
from typing import Callable

log = logging.getLogger(__name__)


class _SkipSignal(Exception):
    pass


@dataclasses.dataclass
class TestResult:
    name: str
    passed: bool
    message: str
    duration_s: float
    skipped: bool = False
    screenshot: str | None = None


class TestRunner:
    def __init__(self, drv, artifacts=None):
        self.drv = drv
        self.artifacts = artifacts
        self.results: list[TestResult] = []

    def assert_true(self, condition: bool, message: str):
        if not condition:
            raise Exception(message)

    def assert_false(self, condition: bool, message: str):
        if condition:
            raise Exception(message)

    def fail(self, message: str):
        raise Exception(message)

    def skip(self, reason: str = ""):
        """TC를 SKIP으로 명시적 처리 — 총 카운트에서 제외."""
        raise _SkipSignal(reason)

    @staticmethod
    def _clean_message(e: Exception) -> str:
        msg = str(e)
        first_line = msg.split('\n')[0].strip()
        if first_line.startswith('Message:'):
            body = first_line[len('Message:'):].strip()
            if not body:
                for line in msg.split('\n'):
                    line = line.strip()
                    if 'NoSuchElement' in line or 'could not be located' in line:
                        return "Element not found on screen"
                    if 'StaleElement' in line or 'stale element' in line.lower():
                        return "Stale element (screen changed)"
                    if 'TimeoutException' in line or 'timeout' in line.lower():
                        return "Timeout waiting for element"
                return "Unexpected Appium error"
            if 'could not be located' in body:
                return "Element not found on screen"
            if 'stale element' in body.lower():
                return "Stale element (screen changed)"
            return body[:80]
        return first_line[:80]

    def run(self, test_fn: Callable) -> TestResult:
        name = (test_fn.__doc__ or test_fn.__name__).strip()
        log.info("[TC] %s", name)
        start = time.monotonic()
        screenshot = None
        try:
            test_fn(self.drv, self)
            duration = time.monotonic() - start
            result = TestResult(name=name, passed=True, message="PASS", duration_s=duration)
            log.info("  PASS (%.1fs)", duration)
        except _SkipSignal as e:
            duration = time.monotonic() - start
            reason = str(e) or "조건 미충족"
            result = TestResult(name=name, passed=True, message=f"SKIP: {reason}",
                                duration_s=duration, skipped=True)
            log.info("  SKIP: %s (%.1fs)", reason, duration)
        except Exception as e:
            duration = time.monotonic() - start
            try:
                screenshot = self.drv.screenshot(f"fail_{test_fn.__name__}")
            except Exception:
                pass
            result = TestResult(
                name=name, passed=False, message=self._clean_message(e),
                duration_s=duration, screenshot=screenshot
            )
            log.warning("  FAIL: %s (%.1fs)", e, duration)
        self.results.append(result)
        return result

    def run_all(self, tests: list[Callable]) -> dict:
        for t in tests:
            self.run(t)
        return self.summary()

    def summary(self) -> dict:
        total    = len(self.results)
        skipped  = sum(1 for r in self.results if r.skipped)
        ran      = total - skipped
        passed   = sum(1 for r in self.results if r.passed and not r.skipped)
        log.info("=" * 50)
        log.info("Regression: %d/%d passed (%d skipped)", passed, ran, skipped)
        for r in self.results:
            if r.skipped:
                icon = "SKIP"
            elif r.passed:
                icon = "PASS"
            else:
                icon = "FAIL"
            log.info("  [%s] %s", icon, r.name)
            if not r.passed and not r.skipped:
                log.info("       -> %s", r.message)
                if r.screenshot:
                    log.info("       screenshot: %s", r.screenshot)
        log.info("=" * 50)
        return {"total": ran, "passed": passed, "skipped": skipped,
                "failed": ran - passed, "results": self.results}
